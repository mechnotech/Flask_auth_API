import hmac
from typing import Tuple, Union

from flask_jwt_extended import create_access_token, create_refresh_token

from db_models.models import User, SALT, Profile, JwtRefresh
from dbs.db import db
from utils.models import UserSet, LoginSet


def sign(password: str) -> str:
    sig = hmac.new(key=SALT.encode('utf-8'), msg=password.encode('utf-8'), digestmod='sha256')
    return sig.hexdigest()


def get_user_tokens(user: LoginSet, role='user') -> Tuple[str, str]:
    access_token = create_access_token(identity=user.login, additional_claims={'role': role})
    refresh_token = create_refresh_token(identity=user.login)
    return access_token, refresh_token


def is_user_exists(user: Union[UserSet, LoginSet], check_email=None):
    User.query.all()
    if check_email:
        return (
                User.query.filter_by(login=user.login).one_or_none()
                or
                User.query.filter_by(email=user.email).one_or_none()
        )
    return User.query.filter_by(login=user.login).one_or_none()


def is_password_correct(user: LoginSet):
    User.query.all()
    checked_user = User.query.filter_by(login=user.login).first()
    checked_pass = checked_user.password
    return checked_pass == sign(user.password)


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
