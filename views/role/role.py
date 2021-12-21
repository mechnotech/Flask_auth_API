from http import HTTPStatus

from flask import Blueprint, request
from flask.views import MethodView

from utils.models import RoleUser, RoleSet
from utils.tools import (
    user_sets,
    post_load,
    admin_required,
    admit_role,
    role_revoke,
    roles_list,
    set_role,
    update_role,
    delete_role,
)

role = Blueprint('role', __name__)


@role.route("admit/", methods=["POST"])
@admin_required()
def role_admit():
    role_for_user = post_load(obj=RoleUser, request=request)
    admit_role(role_for_user)
    return {'msg': f'Роль {role_for_user.role} назначена пользователю {role_for_user.user}'}, HTTPStatus.CREATED


@role.route('<string:role_name>/<string:username>/', methods=['DELETE'])
@admin_required()
def revoke_role(role_name, username):
    role_revoke(role_name, username)
    return {'msg': f'Роль {role_name} удалена у пользователя {username}'}


class RoleAPI(MethodView):
    @admin_required()
    def get(self):
        roles = roles_list()
        return {'roles': roles}

    @admin_required()
    def post(self):
        user, _ = user_sets()
        role_obj = post_load(obj=RoleSet, request=request)
        set_role(role_obj.role)
        return {'created_role': role_obj.role}


class RoleChangeAPI(MethodView):
    @admin_required()
    def patch(self, role_name):
        role_new = post_load(obj=RoleSet, request=request)
        update_role(role_name, role_new)
        return {'msg': 'Роль обновлена'}

    @admin_required()
    def delete(self, role_name):
        delete_role(role_name)
        return {'msg': 'Роль удалена'}


role.add_url_rule(
    '<string:role_name>/',
    view_func=RoleChangeAPI.as_view(name='RoleChange'),
    methods=['PATCH', 'DELETE']
)
role.add_url_rule(
    '/',
    view_func=RoleAPI.as_view(name='Role'),
    methods=['GET', 'POST']
)
