from datetime import timedelta

from flask import Blueprint, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required

from utils.models import ProfileSet
from utils.tools import user_sets, get_logins, get_profile, post_load, update_profile, cache_it

users = Blueprint('users', __name__)


@users.route('history/', methods=['GET'])
@cache_it(ttl=timedelta(minutes=1))
@jwt_required()
def history():
    user, jwt_id = user_sets()
    logins_list = get_logins(user)
    return {'msg': logins_list}


class CabinetAPI(MethodView):
    @jwt_required()
    def get(self):
        user, _ = user_sets()
        profile = get_profile(user)
        return {'msg': profile}

    @jwt_required()
    def patch(self):
        user, _ = user_sets()
        profile = post_load(obj=ProfileSet)
        update_profile(profile, user)
        return jsonify({'msg': 'Профиль обновлен'})


users.add_url_rule('me/', view_func=CabinetAPI.as_view(name='Profile'), methods=['GET', 'PATCH'])
