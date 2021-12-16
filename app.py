from flask import Flask, abort, make_response
from flask import jsonify
from flask import request
from flask.views import MethodView
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from pydantic.error_wrappers import ValidationError

from dbs.db import db, init_db
from settings import ACCESS_EXPIRES, REFRESH_EXPIRES
from utils.models import UserSet, LoginSet, ProfileSet
from utils.tools import (
    is_user_exists,
    get_user_tokens,
    is_password_correct,
    register_user_data,
    to_cache_expired,
    is_token_revoked,
    update_jwt_db,
    do_checkout, get_profile, update_profile,
)

app = Flask(__name__)
init_db(app)
app.app_context().push()
db.create_all()

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'Eww3ssefw2931dfsd'  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = REFRESH_EXPIRES
jwt = JWTManager(app)


@app.route("/api/v1/login", methods=["POST"])
def login():
    if not request.json:
        return jsonify({"msg": 'Пустой запрос'}), 400
    try:
        user = LoginSet(**request.json)
    except ValidationError as e:
        return jsonify({"msg": e.errors()}), 400
    db_user = is_user_exists(user.login)
    if not db_user:
        return jsonify({"msg": 'Такой пользователь не существует!'}), 404
    if not is_password_correct(hashed_password=db_user.password, password_to_check=user.password):
        return jsonify({"msg": 'Пароль неверный!'}), 403
    access_token, refresh_token = get_user_tokens(db_user)
    do_checkout(db_user, info=str(request.user_agent), refresh_token=refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/api/v1/registration", methods=["POST"])
def registration():
    if not request.json:
        return jsonify({"msg": 'Пустой запрос'}), 400
    try:
        user = UserSet(**request.json)
    except ValidationError as e:
        return jsonify({"msg": e.errors()}), 400
    if is_user_exists(user, check_email=True):
        return jsonify({"msg": 'Пользователь с таким login или email уже создан!'}), 409
    access_token, refresh_token = get_user_tokens(user.login)
    register_user_data(refresh_token, user)
    return jsonify(access_token=access_token, refresh_token=refresh_token), 201


def user_sets():
    user_login = get_jwt_identity()
    body = get_jwt()
    role = body.get('role')
    jwt_id = body.get('jti')
    if is_token_revoked(jwt_id):
        return abort(make_response(jsonify({"msg": 'Refresh-token был отозван'}), 401))
    user = is_user_exists(user_login)
    if not user:
        return abort(make_response(jsonify({"msg": 'Такой пользователь не существует!'}), 404))
    return user, role, jwt_id


@app.route("/api/v1/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user, role, jwt_id = user_sets()
    to_cache_expired(jwt_id=jwt_id)
    if not role:
        role = 'user'
    access_token, refresh_token = get_user_tokens(user, role=role)
    update_jwt_db(user, refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/api/v1/logout", methods=["GET"])
@jwt_required()
def logout():
    user, _, jwt_id = user_sets()
    do_checkout(user, info=str(request.user_agent), status='logout', jwt_id=jwt_id)
    return jsonify(logout_as=user.login), 200


class CabinetAPI(MethodView):
    @jwt_required()
    def get(self):
        user, _, jwt_id = user_sets()
        profile = get_profile(user)
        return profile.json()

    @jwt_required()
    def post(self):
        user, role, jwt_id = user_sets()
        if not request.json:
            return jsonify({"msg": 'Пустой запрос'}), 400
        try:
            profile = ProfileSet(**request.json)
        except ValidationError as e:
            return jsonify({"msg": e.errors()}), 400
        update_profile(profile, user)
        return jsonify({'msg': 'Профиль обновлен'})


app.add_url_rule('/api/v1/users/me', view_func=CabinetAPI.as_view(name='Profile'), methods=['GET', 'POST'])


@app.route("/api/v1/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user, _, jwt_id = user_sets()
    if is_token_revoked(jwt_id):
        return jsonify({"msg": 'Refresh-token был отозван'}), 401
    return jsonify(logged_in_as=current_user.login), 200


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
    )
