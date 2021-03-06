import json
import time
from http import HTTPStatus

import requests as rq
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from settings import OAUTH_PROVIDERS
from utils.models import OAuthProviderSet, UserSet, ProfileSet
from utils.tools import (
    post_load,
    is_user_exists,
    get_user_tokens,
    do_checkout,
    register_user_data,
    show_error,
    sign,
    update_profile,
    create_social,
    is_social_exist,
    get_user_by_id,
    user_sets,
    remove_user_social,
)

oauth = Blueprint('OAuth', __name__)


def generate_password(user_raw):
    return sign(f'{user_raw["email"]}+{user_raw["login"]}+{time.time()}')[1:8]


def check_request(result):
    if result.status_code != 200:
        return show_error(json.loads(result.content), result.status_code)
    try:
        content = json.loads(result.content)
    except Exception as e:
        return show_error(f'Ошибка декодирования {e}', result.status_code)
    return content


def provider_get_tokens(provider: OAuthProviderSet):
    """
    Получение authorization токена по без call_back url (режим устройства)
    1) Возвращает ссылку к провайдеру, для получения разрешения на доступ к ресурсам пользователя
    2) Обменивает код доступа, на access token
    """
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
        'client_secret': provider.client_secret,
    }

    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    res = rq.post(url=prov_sets.get('get_access_token_url'), data=payload, headers=headers)
    return check_request(res)


class GetUserinfoFromOAuth:
    def __init__(self, provider: OAuthProviderSet):
        self.provider = provider
        self.tokens = provider_get_tokens(provider)
        self.provider.access_token = self.tokens.get('access_token')
        self.provider.refresh_token = self.tokens.get('refresh_token')
        self.select = {'vk': self.vk, 'yandex': self.yandex}

    def vk(self):
        email = self.tokens.get('email')
        social_id = self.tokens.get('user_id')
        candidate_raw = {'login': f'vk_{social_id}', 'email': email}
        candidate_raw['password'] = generate_password(candidate_raw)
        profile_raw = {'first_name': None, 'last_name': None, 'social_id': social_id}
        return candidate_raw, profile_raw

    def yandex(self):
        headers = {'Authorization': f'Bearer {self.provider.access_token}'}
        prov_sets = OAUTH_PROVIDERS['yandex']
        res = rq.get(url=prov_sets['get_user_info_url'], headers=headers)
        content = check_request(res)
        candidate_raw = {'login': content.get('login'), 'email': content.get('default_email')}
        candidate_raw['password'] = generate_password(candidate_raw)
        profile_raw = {
            'first_name': content.get('first_name'),
            'last_name': content.get('last_name'),
            'social_id': content.get('id'),
        }
        return candidate_raw, profile_raw


@oauth.route('login/', methods=['POST'])
def login():
    provider = post_load(obj=OAuthProviderSet)
    info = GetUserinfoFromOAuth(provider)
    candidate_raw, profile_raw = info.select[provider.oauth_provider]()
    social = is_social_exist(social_id=profile_raw['social_id'], social_name=provider.oauth_provider)
    if not social:
        return jsonify({'msg': 'Пользователь не зарегистрирован!'}), HTTPStatus.NOT_FOUND

    db_user = get_user_by_id(user_id=social.user_id)
    access_token, refresh_token = get_user_tokens(db_user)
    do_checkout(db_user, info=str(request.user_agent), refresh_token=refresh_token)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@oauth.route('registration/', methods=['POST'])
def registration():
    provider = post_load(obj=OAuthProviderSet)
    info = GetUserinfoFromOAuth(provider)
    candidate_raw, profile_raw = info.select[provider.oauth_provider]()
    candidate = UserSet(**candidate_raw)

    user = is_user_exists(candidate, check_email=True)
    if user:
        return jsonify({'msg': 'Пользователь с таким login или email уже создан!'}), HTTPStatus.CONFLICT
    social = is_social_exist(social_id=profile_raw['social_id'], social_name=provider.oauth_provider)
    if social:
        return jsonify({'msg': 'Пользователь уже зарегистрирован через этого OAuth провайдера!'}), HTTPStatus.CONFLICT

    access_token, refresh_token = get_user_tokens(candidate)
    register_user_data(refresh_token, candidate)

    profile = ProfileSet(**profile_raw)
    user = is_user_exists(candidate, check_email=True)
    create_social(social_id=profile_raw['social_id'], social_name=provider.oauth_provider, user_id=user.id)
    update_profile(profile, user)
    return (
        {
            'msg': f'Вы зарегистрировались через OAuth ({provider.oauth_provider})! Ваш логин:'
            f' {candidate.login}, ваш пароль: {candidate.password}'
        },
        HTTPStatus.CREATED,
    )


@oauth.route('remove/<string:social>', methods=['DELETE'])
@jwt_required()
def remove(social):
    """
    Открепить связь социальной сети и аккаунта пользователя
    'vk', 'yandex' или другие зарегистрированные провайдеры в OAUTH_PROVIDERS
    'all' - отключение всех провайдеров.
    """

    user, _ = user_sets()

    if social == 'all':
        remove_user_social(user=user, social=social, complete=True)
        return {'msg': f'Все OAuth Login удалены для пользователя {user.login}'}

    if social not in OAUTH_PROVIDERS.keys():
        return show_error('Такой провайдер OAuth не поддерживается!', HTTPStatus.UNPROCESSABLE_ENTITY)
    remove_user_social(user=user, social=social)
    return {'msg': f'Логин через {social} удален для пользователя {user.login}'}
