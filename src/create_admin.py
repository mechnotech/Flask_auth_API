# Запустить один раз после инсталляции
# и выполнения миграции: alembic upgrade head !
from app import app
from dbs.db import init_db

from settings import DEFAULT_ADMIN_PASS
from utils.models import UserSet, RoleUser
from utils.tools import set_role, get_user_tokens, register_user_data, admit_role, is_user_exists


def is_admin_exists():
    # Проверить, не создан ли уже админ?
    admin = is_user_exists('admin')
    if not admin:
        return False

    return True


def create():
    # Создать админа
    admin = UserSet(login='admin', password=DEFAULT_ADMIN_PASS, email='mc@ya.ru')
    access_token, refresh_token = get_user_tokens(admin)
    register_user_data(refresh_token, admin)

    # Создать роли админа, пользователя и еще
    set_role('admin')
    set_role('user')
    set_role('subscriber')

    # Назначить админу админскую :) и пользовательскую роли.
    admit_role(RoleUser(role='admin', user='admin'))
    admit_role(RoleUser(role='user', user='admin'))

    print('Пользователь admin создан (пароль был взят из env, дефолтный: password)')
    print('Ему назначены роли admin и user')
    print('Access Token:', access_token)
    print('Refresh Token', refresh_token)
    print('OpenAPI: localhost:5000/swagger/')


if __name__ == '__main__':
    init_db(app)
    app.app_context().push()
    if not is_user_exists('admin'):
        create()
    else:
        print('Пользователь admin уже существует (пароль в env, дефолтный: password)')
