import hmac
from typing import Tuple, Union, Optional

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from db_models.models import User, SALT, Profile, JwtRefresh, Login
from dbs.db import db, cache
from settings import ACCESS_EXPIRES, REFRESH_EXPIRES, ADMIN_ROLES
from utils.models import UserSet, ProfileSet


def sign(password: str) -> str:
    sig = hmac.new(key=SALT.encode('utf-8'), msg=password.encode('utf-8'), digestmod='sha256')
    return sig.hexdigest()


def get_user_tokens(user, role='user') -> Tuple[str, str]:
    access_token = create_access_token(identity=user.login, additional_claims={'role': role})
    refresh_token = create_refresh_token(identity=user.login, additional_claims={'role': role})
    return access_token, refresh_token


def is_user_exists(user: Union[UserSet, str], check_email=None) -> Optional[User]:
    User.query.all()
    if check_email:
        return (
                User.query.filter_by(login=user.login).one_or_none()
                or
                User.query.filter_by(email=user.email).one_or_none()
        )
    return User.query.filter_by(login=user).one_or_none()


def is_password_correct(hashed_password: str, password_to_check: str):
    return hashed_password == sign(password_to_check)


def is_token_revoked(jwt_id: str):
    return cache.get(jwt_id)


def to_cache_expired(jwt_id: str, token_type='refresh'):
    """
    Храним в Кэше только подписи от JWT как ключи, так-как они уникальны,
    Значением же будет 1, так короче и вернет True при последующем запросе их кэша
    :param jwt_id: Подпись JWT токена
    :param token_type: Тип токена assess или refresh
    :return:
    """
    if token_type == 'refresh':
        ttl = int(REFRESH_EXPIRES.total_seconds())
    else:
        ttl = int(ACCESS_EXPIRES.total_seconds())
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
    return ProfileSet(first_name=profile.first_name, last_name=profile.last_name, role=profile.role, bio=profile.bio)


def update_profile(profile: ProfileSet, user: User):
    Profile.query.all()
    db_profile = Profile.query.filter_by(user_id=user.id).first()
    db_profile.first_name = profile.first_name
    db_profile.last_name = profile.last_name
    db_profile.bio = profile.bio
    db.session.add(db_profile)
    db.session.commit()


def register_user_data(refresh_token, user: UserSet):
    new_user = User(
        login=user.login,
        password=sign(user.password),
        email=user.email
    )
    db.session.add(new_user)
    db.session.commit()
    User.query.all()
    db_user = User.query.filter_by(login=user.login).first()
    profile = Profile(user_id=db_user.id)
    jwt_token = JwtRefresh(user_id=db_user.id, refresh_token=refresh_token)
    db.session.add(profile)
    db.session.add(jwt_token)
    db.session.commit()
