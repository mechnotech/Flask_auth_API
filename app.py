from flask import Flask
from flask import request
from flask.views import MethodView
from flask_jwt_extended import (
    JWTManager,
)

from dbs.db import init_db
from settings import SECRET_KEY, config
from utils.models import LoginSet, RoleUser
from utils.tools import *

app = Flask(__name__)
init_db(app)
app.app_context().push()
db.create_all()

app.config['JWT_SECRET_KEY'] = SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = REFRESH_EXPIRES
jwt = JWTManager(app)


@app.route("/api/v1/login", methods=["POST"])
def login():
    user = post_load(obj=LoginSet, request=request)
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
    candidate = post_load(obj=UserSet, request=request)
    user = is_user_exists(candidate, check_email=True)
    if user:
        return jsonify({"msg": 'Пользователь с таким login или email уже создан!'}), 409
    access_token, refresh_token = get_user_tokens(candidate)
    register_user_data(refresh_token, candidate)
    return {'msg': f'Пользователь {candidate.login} создан'}, 201


@app.route("/api/v1/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user, jwt_id = user_sets()
    to_cache_expired(jwt_id=jwt_id)
    access_token, refresh_token = get_user_tokens(user)
    update_jwt_db(user, refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/api/v1/logout", methods=["GET"])
@jwt_required()
def logout():
    user, jwt_id = user_sets()
    do_checkout(user, info=str(request.user_agent), status='logout', jwt_id=jwt_id)
    return {'logout_as': user.login}


@app.route("/api/v1/users/history", methods=["GET"])
@jwt_required()
def logins():
    user, jwt_id = user_sets()
    logins_list = get_logins(user)
    return {'msg': logins_list}


@app.route("/api/v1/role/admit", methods=["POST"])
@admin_required()
def role_admit():
    role_for_user = post_load(obj=RoleUser, request=request)
    admit_role(role_for_user)
    return {'msg': f'Роль {role_for_user.role} назначена пользователю {role_for_user.user}'}, 201


@app.route('/api/v1/role/<string:role>/<string:username>', methods=['DELETE'])
@admin_required()
def revoke_role(role, username):
    role_revoke(role, username)
    return {'msg': f'Роль {role} удалена у пользователя {username}'}


class CabinetAPI(MethodView):
    @jwt_required()
    def get(self):
        user, _ = user_sets()
        profile = get_profile(user)
        return {'msg': profile}

    @jwt_required()
    def post(self):
        user, _ = user_sets()
        profile = post_load(obj=ProfileSet, request=request)
        update_profile(profile, user)
        return jsonify({'msg': 'Профиль обновлен'})


class RoleAPI(MethodView):
    @admin_required()
    def get(self):
        roles = roles_list()
        return {'roles': roles}

    @admin_required()
    def post(self):
        user, _ = user_sets()
        role_name = post_load(obj=RoleSet, request=request)
        set_role(role_name.role)
        return {'created_role': role_name.role}


class RoleChangeAPI(MethodView):
    @admin_required()
    def patch(self, role):
        role_new = post_load(obj=RoleSet, request=request)
        update_role(role, role_new)
        return {'msg': 'Роль обновлена'}

    @admin_required()
    def delete(self, role):
        delete_role(role)
        return {'msg': 'Роль удалена'}


app.add_url_rule(
    '/api/v1/users/me',
    view_func=CabinetAPI.as_view(name='Profile'),
    methods=['GET', 'POST']
)
app.add_url_rule(
    '/api/v1/role/<string:role>',
    view_func=RoleChangeAPI.as_view(name='RoleChange'),
    methods=['PATCH', 'DELETE']
)
app.add_url_rule(
    '/api/v1/role',
    view_func=RoleAPI.as_view(name='Role'),
    methods=['GET', 'POST']
)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.auth_port,
    )
