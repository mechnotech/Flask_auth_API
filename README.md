##  Auth API

### Для запуска нужно:
#### Создать окружение
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### Запустить контейнеры с Redis и Postgres
`docker-compose -f dev-compose.yaml up -d`

#### При первом запуске (создать первичного пользователя (admin, password) и назначить ему админскую роль)
`python create_admin.py`

#### Запуск приложения:
`python pywsgi.py`

Описание работы этого API доступно после запуска будет доступно по адресу http://localhost:5000/swagger/

Тесты (без тестов, только коллекции) для Postman в папке project_description для Auth API и для Fast API

Там же yaml схема Auth API.

####

Схема тестирования:

https://github.com/mechnotech/api_tests                                         
Запускаем группу контейнеров Fast API (тесты не все сработают в ok на этот раз, но заполнят ES данными)

https://github.com/mechnotech/Flask_auth_API
Запускаем этот проект (Auth API)

Пробуем получить от Fast API  эндпоинт film detail (localhost:8000/api/v1/film/5044be46-fafc-4f98-8577-5da9892b1cb9) обычным пользователем без Bearer JWT

Пробуем получить от Fast API  эндпоинт film detail пользователем с Bearer JWT (от admin Auth API)
     
Что произошло?

Fast API - выступает MitM агентом пробрасывая заголовок Authorization от request user к Auth API. Получает его (user) набор ролей.

В итоге общим у API должны быть только понятия о ролях (списках ADMIN_ROLES, PRIVILEGED_USERS_ROLES и т.п.) что позволяет тонко определять доступ к контенту на стороне Fast API.


