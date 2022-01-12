import json
from http import HTTPStatus
import requests as rq
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from settings import OAUTH_PROVIDERS
from utils.models import LoginSet, OAuthProviderSet
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
    show_error
)

oauth = Blueprint('OAuth', __name__)


@oauth.route('login/', methods=['POST'])
def login():
    user = post_load(obj=LoginSet)
    db_user = is_user_exists(user.login)
    if not db_user:
        return jsonify({'msg': 'Такой пользователь не существует!'}), HTTPStatus.NOT_FOUND
    if not is_password_correct(hashed_password=db_user.password, password_to_check=user.password):
        return jsonify({'msg': 'Пароль неверный!'}), HTTPStatus.UNAUTHORIZED
    access_token, refresh_token = get_user_tokens(db_user)
    do_checkout(db_user, info=str(request.user_agent), refresh_token=refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


def provider_get_tokens(provider):
    if provider.oauth_provider not in OAUTH_PROVIDERS.keys():
        return show_error('Такой провайдер OAuth не поддерживается!', HTTPStatus.UNPROCESSABLE_ENTITY)
    prov_sets = OAUTH_PROVIDERS[provider.oauth_provider]
    provider.client_id = prov_sets.get('client_id')
    provider.client_secret = prov_sets.get('client_secret')
    if not provider.request_code:
        return show_error(f'{prov_sets.get("request_code_url")}{provider.client_id}', HTTPStatus.TEMPORARY_REDIRECT)

    payload = {
        'grant_type': 'authorization_code',
        'code': provider.request_code,
        'client_id': provider.client_id,
        'client_secret': provider.client_secret
    }
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    res = rq.post(url=prov_sets.get('get_access_token_url'), data=payload, headers=headers)
    if res.status_code != 200:
        return show_error(json.loads(res.content), res.status_code)
    try:
        content = json.loads(res.content)
    except Exception as e:
        return show_error(f'Ошибка провайдера {e}', res.status_code)
    return content


@oauth.route('registration/', methods=['POST'])
def registration():
    provider = post_load(obj=OAuthProviderSet)
    tokens = provider_get_tokens(provider)
    provider.access_token = tokens.get('access_token')
    provider.refresh_token = tokens.get('refresh_token')


    candidate = 'some payload from provider'
    user = is_user_exists(candidate, check_email=True)
    if user:
        return jsonify({'msg': 'Пользователь с таким login или email уже создан!'}), HTTPStatus.CONFLICT
    access_token, refresh_token = get_user_tokens(candidate)
    register_user_data(refresh_token, candidate)
    return {'msg': f'Пользователь {candidate.login} создан'}, HTTPStatus.CREATED