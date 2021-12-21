from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from utils.models import LoginSet, UserSet
from utils.tools import (
    post_load,
    is_user_exists,
    is_password_correct,
    get_user_tokens,
    do_checkout,
    register_user_data,
    user_sets,
    to_cache_expired,
    update_jwt_db,
)

auth = Blueprint('auth', __name__)


@auth.route("login/", methods=["POST"])
def login():
    user = post_load(obj=LoginSet, request=request)
    db_user = is_user_exists(user.login)
    if not db_user:
        return jsonify({"msg": 'Такой пользователь не существует!'}), HTTPStatus.NOT_FOUND
    if not is_password_correct(hashed_password=db_user.password, password_to_check=user.password):
        return jsonify({"msg": 'Пароль неверный!'}), HTTPStatus.UNAUTHORIZED
    access_token, refresh_token = get_user_tokens(db_user)
    do_checkout(db_user, info=str(request.user_agent), refresh_token=refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@auth.route("registration/", methods=["POST"])
def registration():
    candidate = post_load(obj=UserSet, request=request)
    user = is_user_exists(candidate, check_email=True)
    if user:
        return jsonify({"msg": 'Пользователь с таким login или email уже создан!'}), HTTPStatus.CONFLICT
    access_token, refresh_token = get_user_tokens(candidate)
    register_user_data(refresh_token, candidate)
    return {'msg': f'Пользователь {candidate.login} создан'}, HTTPStatus.CREATED


@auth.route("refresh/", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user, jwt_id = user_sets()
    to_cache_expired(jwt_id=jwt_id)
    access_token, refresh_token = get_user_tokens(user)
    update_jwt_db(user, refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@auth.route("logout/", methods=["GET"])
@jwt_required()
def logout():
    user, jwt_id = user_sets()
    do_checkout(user, info=str(request.user_agent), status='logout', jwt_id=jwt_id)
    return {'logout_as': user.login}
