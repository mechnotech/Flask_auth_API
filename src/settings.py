import os
from datetime import timedelta

from pydantic import BaseSettings


class AuthSettings(BaseSettings):
    db_name: str = os.getenv('DB_NAME', 'auth')
    pg_user: str = os.getenv('POSTGRES_USER', 'auth')
    pg_pass: str = os.getenv('POSTGRES_PASSWORD', 'auth')
    db_host: str = os.getenv('POSTGRES_HOST', '127.0.0.1')
    db_port: int = int(os.getenv('DB_PORT', 5433))
    redis_host: str = os.getenv('REDIS_HOST', '127.0.0.1')
    redis_port: int = int(os.getenv('REDIS_PORT', 6363))
    auth_port: int = int(os.getenv('AUTH_PORT', 5000))


config = AuthSettings()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = (
    f'postgresql://{config.pg_user}:' f'{config.pg_pass}@{config.db_host}:{config.db_port}/{config.db_name}'
)
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('ACCESS_EXPIRES_HOURS', 1)))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('REFRESH_EXPIRES_DAYS', 1)))
ADMIN_ROLES = ['admin', 'moderator']
PRIVILEGED_USERS_ROLES = ['subscriber', 'bonus', 'trial']
JWT_SECRET_KEY = os.getenv('SECRET_KEY', 'Eww3ssefw2931dfsd')
SALT = os.getenv('SALT', '8784dg4rgw44fe73sdf7r72s7')
SWAGGER = {'title': 'OA3 Callbacks', 'openapi': '3.0.2', 'specs_route': '/swagger/'}
DEFAULT_ADMIN_PASS = os.getenv('DEFAULT_ADMIN_PASS', 'password')
AUTH_NAME = os.getenv('AUTH_NAME', 'auth_api')

OAUTH_PROVIDERS = {
    'yandex': {
        'client_id': os.getenv('YANDEX_CLIENT_ID', '392d5a358be14596896095f4e7c57e38'),
        'client_secret': os.getenv('YANDEX_CLIENT_SECRET', '8330cb24871c4700978f1c6a8a71fe84'),
        'request_code_url': 'https://oauth.yandex.ru/authorize?response_type=code&client_id=',
        'get_access_token_url': 'https://oauth.yandex.ru/token',
        'get_user_info_url': 'https://login.yandex.ru/info?format=json',
    },
    'vk': {
        'client_id': os.getenv('VK_CLIENT_ID', '8049716'),
        'client_secret': os.getenv('VK_CLIENT_SECRET', 'ErcbpNBtXw90Q9cHNiMG'),
        'request_code_url': 'https://oauth.vk.com/authorize?display=page&scope=+4194304&client_id=',
        'get_access_token_url': 'https://oauth.vk.com/access_token',
        'get_user_info_url': 'https://api.vk.com/method/account.getProfileInfo?v=5.123',
    },
}
