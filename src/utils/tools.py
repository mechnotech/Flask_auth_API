import hmac
import json
from http import HTTPStatus
from functools import wraps
from typing import Tuple, Union, Optional, Any

from flask import make_response, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jti,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from orjson import orjson
from pydantic import ValidationError
from werkzeug.exceptions import abort

from db_models.models import User, Profile, JwtRefresh, Login, Role, SocialAccount
from dbs.db import db, cache
from settings import JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES, ADMIN_ROLES, SALT
from utils.models import UserSet, ProfileSet, LogSet, RoleSet


def show_error(text: Optional[Any], http_code: int):
    return abort(make_response(jsonify({'msg': text}), http_code))


def sign(password: str) -> str:
    sig = hmac.new(key=SALT.encode('utf-8'), msg=password.encode('utf-8'), digestmod='sha256')
    return sig.hexdigest()


def get_user_tokens(user) -> Tuple[str, str]:
    access_token = create_access_token(identity=user.login)
    refresh_token = create_refresh_token(identity=user.login)
    return access_token, refresh_token


def get_user_by_id(user_id):
    return User.query.filter_by(id=user_id).first()


def is_user_exists(user: Union[UserSet, str], check_email=None) -> Optional[User]:
    User.query.all()
    if check_email:
        return (
            User.query.filter_by(login=user.login).one_or_none() or User.query.filter_by(email=user.email).one_or_none()
        )
    return User.query.filter_by(login=user).one_or_none()


def is_password_correct(hashed_password: str, password_to_check: str):
    return hashed_password == sign(password_to_check)


def is_token_revoked(jwt_id: str):
    return cache.get(jwt_id)


def get_key_to_cache(login: str, url: str) -> str:
    return f'{login}-{url}'


def to_cache_expired(jwt_id: str, token_type='refresh'):
    """
    Храним в Кэше только подписи от JWT как ключи, так-как они уникальны,
    Значением же будет 1, так короче и вернет True при последующем запросе их кэша
    :param jwt_id: Подпись JWT токена
    :param token_type: Тип токена assess или refresh
    :return:
    """
    if token_type == 'refresh':
        ttl = int(JWT_REFRESH_TOKEN_EXPIRES.total_seconds())
    else:
        ttl = int(JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
    cache.setex(jwt_id, ttl, 1)


def update_jwt_db(user, refresh_token: str):
    JwtRefresh.query.all()
    jwt_record = JwtRefresh.query.filter_by(user_id=user.id).first()
    jwt_record.refresh_token = refresh_token
    db.session.add(jwt_record)
    db.session.commit()


def do_checkout(user, info: str, status='login', jwt_id=Optional[str], refresh_token=Optional[str]):
    JwtRefresh.query.all()
    jwt_record = JwtRefresh.query.filter_by(user_id=user.id).first()
    if status == 'logout':
        refresh_jwt_id = get_jti(jwt_record.refresh_token)
        to_cache_expired(jwt_id=jwt_id, token_type='access')
        to_cache_expired(jwt_id=refresh_jwt_id)
    if status == 'login':
        jwt_record.refresh_token = refresh_token
        db.session.add(jwt_record)
    login = Login(user_id=user.id, info=info, status=status)
    db.session.add(login)
    db.session.commit()


def get_profile(user):
    Profile.query.all()
    profile = Profile.query.filter_by(user_id=user.id).first()
    return orjson.loads(
        ProfileSet(
            first_name=profile.first_name,
            last_name=profile.last_name,
            role=[str(x) for x in profile.role],
            bio=profile.bio,
        ).json()
    )


def update_profile(profile: ProfileSet, user: User):
    Profile.query.all()
    db_profile = Profile.query.filter_by(user_id=user.id).first()
    db_profile.first_name = profile.first_name
    db_profile.last_name = profile.last_name
    db_profile.bio = profile.bio
    db.session.add(db_profile)
    db.session.commit()
    url = request.base_url
    key = get_key_to_cache(user.login, url)
    cache.delete(key)


def is_social_exist(social_id, social_name):
    return SocialAccount.query.filter_by(social_id=str(social_id), social_name=social_name).one_or_none()


def create_social(social_id, social_name, user_id):
    new_account = SocialAccount(social_id=social_id, social_name=social_name, user_id=user_id)
    db.session.add(new_account)
    db.session.commit()


def remove_user_social(user: User, social: str, complete=False):
    if complete:
        records = SocialAccount.query.filter_by(user_id=user.id).all()
    else:
        records = SocialAccount.query.filter_by(user_id=user.id, social_name=social).all()
    if records:
        for record in records:
            db.session.delete(record)
        db.session.commit()
        return

    return show_error('Пользователь не связан с такой службой OAuth', HTTPStatus.NOT_FOUND)


def register_user_data(refresh_token, user: UserSet):
    new_user = User(login=user.login, password=sign(user.password), email=user.email)
    db.session.add(new_user)
    db.session.commit()
    User.query.all()
    db_user = User.query.filter_by(login=user.login).first()
    profile = Profile(user_id=db_user.id)
    jwt_token = JwtRefresh(user_id=db_user.id, refresh_token=refresh_token)
    db.session.add(profile)
    db.session.add(jwt_token)
    db.session.commit()


def get_logins(user):
    Login.query.all()
    logins = Login.query.filter_by(user_id=user.id).all()
    result = [orjson.loads(LogSet(created_at=x.created_at, info=x.info, status=x.status).json()) for x in logins]
    return result


def _get_role(role_name: str, check_exist=False, check_missing=False):
    """
    Получение роли по её названию из базы
    :param role_name: Название роли, например user
    :param check_exist: Проверить и поднять ошибку если роль уже существует
    :param check_missing: Проверить и поднять ошибку если роль не существует
    :return: Роль
    """
    Role.query.all()
    role = Role.query.filter_by(role=role_name).one_or_none()
    if check_missing and not role:
        show_error(f'Такой роли: {role_name} нет', HTTPStatus.NOT_FOUND)
    if check_exist and role:
        show_error('Роль с таким названием уже существует!', HTTPStatus.BAD_REQUEST)
    return role


def set_role(role_name: str):
    _get_role(role_name, check_exist=True)
    role = Role(role=role_name)
    db.session.add(role)
    db.session.commit()


def update_role(role: str, role_new: RoleSet):
    db_role = _get_role(role, check_missing=True)
    _get_role(role_new.role, check_exist=True)
    db_role.role = role_new.role
    db.session.add(db_role)
    db.session.commit()


def delete_role(role_name):
    db_role = _get_role(role_name, check_missing=True)
    db.session.delete(db_role)
    db.session.commit()


def roles_list():
    roles = Role.query.all()
    return [x.role for x in roles]


def _get_role_user_details(role_name: str, username: str) -> Tuple[Role, User]:
    Role.query.all()
    role = Role.query.filter_by(role=role_name).one_or_none()
    User.query.all()
    user = User.query.filter_by(login=username).one_or_none()
    return role, user


def admit_role(user_role):
    role, user = _get_role_user_details(role_name=user_role.role, username=user_role.user)
    if role and user:
        Profile.query.all()
        profile = Profile.query.filter_by(user_id=user.id).first()
        profile.add_role(role=role)
        db.session.commit()
        return
    return show_error('Нет такой роли или пользователя', HTTPStatus.NOT_FOUND)


def role_revoke(role_name, username):
    role, user = _get_role_user_details(role_name, username)
    if role and user:
        Profile.query.all()
        profile = Profile.query.filter_by(user_id=user.id).first()
        if role in profile.role:
            profile.role.remove(role)
            db.session.commit()
            return
        return show_error(f'Такой роли: {role_name} нет у пользователя: {username}', HTTPStatus.NOT_FOUND)
    return show_error('Нет такой роли или пользователя', HTTPStatus.NOT_FOUND)


def user_sets():
    user_login = get_jwt_identity()
    body = get_jwt()
    jwt_id = body.get('jti')
    if is_token_revoked(jwt_id):
        return show_error('token был отозван', HTTPStatus.UNAUTHORIZED)
    user = is_user_exists(user_login)
    if not user:
        return show_error('Такой пользователь не существует!', HTTPStatus.NOT_FOUND)
    return user, jwt_id


def post_load(obj):
    if not request.json:
        return abort(make_response(jsonify({'msg': 'Пустой запрос'}), HTTPStatus.BAD_REQUEST))
    try:
        entity = obj(**request.json)
    except ValidationError as e:
        return show_error(e.errors(), HTTPStatus.BAD_REQUEST)
    return entity


def admin_required():
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user, jwt_id = user_sets()
            profile = get_profile(user)
            if not set(profile['role']) & set(ADMIN_ROLES):
                return jsonify({'msg': 'Требуются административные права'}), HTTPStatus.FORBIDDEN
            return f(*args, **kwargs)

        return wrapper

    return decorator


def cache_it(ttl=JWT_ACCESS_TOKEN_EXPIRES):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user, jwt_id = user_sets()
            url = request.base_url
            key = get_key_to_cache(user.login, url)
            value = cache.get(key)
            if not value:
                value = f(*args, **kwargs)
            else:
                cache.setex(key, ttl, value)
                return json.loads(value)
            cache.setex(key, ttl, json.dumps(value))
            return value

        return wrapper

    return decorator
