from app import app
from dbs.db import db, init_db
# Запустить один раз после инсталляции!
# Подготавливаем контекст и создаём таблицы
from utils.models import UserSet, RoleUser
from utils.tools import sign, set_role, get_user_tokens, register_user_data, admit_role

init_db(app)
app.app_context().push()
db.create_all()

# Создать админа
admin = UserSet(login='admin', password=sign('password'), email='mc@ya.ru')
access_token, refresh_token = get_user_tokens(admin)
register_user_data(refresh_token, admin)

# Создать роли админа и пользователя
set_role('admin')
set_role('user')

# Назначить админу админскую :) и пользовательскую роли.
admit_role(RoleUser(role='admin', user='admin'))
admit_role(RoleUser(role='user', user='admin'))

print('Пользователь admin создан')
print('Ему назначены роли admin и user')
print('Access Token:', access_token)
print('Refresh Token', refresh_token)
print('OpenAPI: localhost:5000/swagger/')
