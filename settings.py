import os
from datetime import timedelta

from pydantic import BaseSettings


class AuthSettings(BaseSettings):
    db_name: str = os.getenv('DB_NAME', 'auth')
    pg_user: str = os.getenv('POSTGRES_USER', 'auth')
    pg_pass: str = os.getenv('POSTGRES_PASSWORD', 'auth')
    db_host: str = os.getenv('DB_HOST', '127.0.0.1')
    db_port: int = int(os.getenv('DB_PORT', 5433))
    redis_host: str = os.getenv('REDIS_HOST', '127.0.0.1')
    redis_port: int = int(os.getenv('REDIS_PORT', 6363))
    auth_port: int = int(os.getenv('AUTH_PORT', 5000))


config = AuthSettings()
ACCESS_EXPIRES = timedelta(hours=int(os.getenv('ACCESS_EXPIRES_HOURS', 1)))
REFRESH_EXPIRES = timedelta(days=int(os.getenv('REFRESH_EXPIRES_DAYS', 1)))
ADMIN_ROLES = ['admin', 'moderator']
PRIVILEGED_USERS_ROLES = ['subscriber', 'bonus', 'trial']
SECRET_KEY = os.getenv('SECRET_KEY', 'Eww3ssefw2931dfsd')
SALT = os.getenv('SALT', '8784dg4rgw44fe73sdf7r72s7')
