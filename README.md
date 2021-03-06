##  OAuth API
#### Дополнения текущего спринта:

Добавлены эндпоинты OAuth:
http://localhost:5000/swagger/

или

http://localhost:8500/swager/ (при запуске docker-compose up --build)

Логика работы:

1) Пользователь создает аккаунт с помощью OAuth провайдеров (на данный момент поддерживаются yandex и vk), если пользователя не существует полученными от провайдера OAuth логином или email
создает логин и пароль, который показывает один раз после регистрации. Т.о. можно зайти как через обычный Auth так и OAuth login
2) Пользователь осуществляет логин с помощью OAuth, если был зарегистрирован через OAuth.
3) Пользователь может удалить связь аккаунта и OAuth

Добавлено кэширование кеширование в самом **Nginx** к эндпоинту /users/me/
результат - ~30К запросов в секунду.

Остальные эндпоинты закрыты ограничением **Nginx** на 100 запросов в секунду с IP

##  Auth API

### Для запуска в Dev нужно:
#### Создать окружение
```
git clone git@github.com:mechnotech/Flask_auth_API.git
cd Flask_auth_API
python -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt
```
#### Запустить контейнеры с Redis и Postgres
`docker-compose -f dev-compose.yaml up -d`

#### Применить миграции alembic
`alembic upgrade head`

#### При первом запуске (создать первичного пользователя (admin, password) и назначить ему админскую роль)
`python src/create_admin.py`
Выдаст jwt токены

#### Запуск приложения:
`python src/pywsgi.py`

Описание работы этого API доступно после запуска будет доступно по адресу http://localhost:5000/swagger/

Тесты (без тестов, только коллекции) для Postman в папке project_description для Auth API и для Fast API

Там же yaml схема Auth API.

####

## Для запуска в Product
```
git clone git@github.com:mechnotech/Flask_auth_API.git
cd Flask_auth_API
cp .env.example .env
docker-compose -up -d
```

`docker logs auth_api` - для просмотра выданных JWT токенов в консоли

Приложение будет доступно по адресу http://localhost:8500

Документированное API http://localhost:5000/swagger/


### Схема тестирования:

https://github.com/mechnotech/async_api_1                                         
Запускаем группу контейнеров Fast API 

сначала `docker-compose -f dev-compose up --build`
Затем `main.py`

https://github.com/mechnotech/Flask_auth_API
Запускаем этот проект (Auth API)
через `docker-compose up -d`

Оба API смотрят на хост систему Auth API порт **8500**, Fast API (**8000**)

Пробуем получить от Fast API  эндпоинт film detail (localhost:8000/api/v1/film/5044be46-fafc-4f98-8577-5da9892b1cb9) обычным пользователем без Bearer JWT

Пробуем получить от Fast API  эндпоинт film detail пользователем с Bearer JWT (от admin Auth API)
     
Что произошло?

Fast API - выступает MitM агентом пробрасывая заголовок Authorization от request user к Auth API. Получает его (user) набор ролей.

В итоге общим у API должны быть только понятия о ролях (списках ADMIN_ROLES, PRIVILEGED_USERS_ROLES и т.п.) что позволяет тонко определять доступ к контенту на стороне Fast API.

### PS

Думаю стоит собрать все спринты в один docker-compose, хотя разрабатывать по узлам мне легче.

#### oinb

Отличный форматтер код-стиля **oinb** позволяет везде где возможно заменить забытые "" на '' и не только это:

```
pip install oitnb
# найти и заменить
oitnb -l 120 .
# или только проверить
oitnb -l 120 --check .
```

#### alembic

самая засадная технология этого проекта. Очень неочевидно устанавливается и весьма неочевидно пробрасывается meta контент
к его env.py
Итого. Если проект плоский, flask не выделен изначально в поддиректорию src (например)
в alembic.ini нужно указать параметр `prepend_sys_path = .` (а в иных случаях `prepend_sys_path = src`) Иначе относительный импорт будет корректен для Pycharm но при вызове
 alembic его не увидит. Попытка же решить проблему через манипуляции с PATH решит проблему миграций, но
приведет к слому настроек Pycharm, восстановить которые я смог только сбросом в "заводские" настройки :(

Примеры команд:

`alembic revision --autogenerate -m "Added Some table"` - сделать миграцию
`alembic upgrade head` - применить миграцию



#### Действительно ли этот flask работает асинхронно с gevent?

создаем пару эндпоинтов с time.sleep(30)
Запускаем в консоли htop
F4 - flask
Дергаем эндпоинты браузером и смотрим как в консоли появляются клоны flask
C gevent такого не происходит.

#### Какую нагрузку действительно держит это приложение?

355 запросов в секунду от 50 авторизованных пользователей. 
При параллельном тестировании в Postman максимальная просадка 1.5 сек, в среднем 
200-300 мс под таким ddos`ом.
Срабатывают ограничения Nginx на число коннектов к эндпоинту.

После некоторых оптимизаций удалось добиться 850 запросов в сек к бэкенду, и похоже, что это потолок.

Применив кеширование в самом **Nginx** результат выше на порядки - 35К в секунду.


```
ab -k -c 50 -n 20000 -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MjI0MTc4MywianRpIjoiYmQxYThmMTYtNzRhMS00NDc5LTlkODItZDNiMmZlNGM4ZDkzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6Im1lY2hub3RlY2giLCJuYmYiOjE2NDIyNDE3ODMsImV4cCI6MTY0MjI0NTM4M30.RHX8S7jTf-h0pV6p8cf7Cakr-_A7QaP8E_lh_Ob0OGE" localhost:8500/api/v1/users/me/
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 2000 requests
Completed 4000 requests
Completed 6000 requests
Completed 8000 requests
Completed 10000 requests
Completed 12000 requests
Completed 14000 requests
Completed 16000 requests
Completed 18000 requests
Completed 20000 requests
Finished 20000 requests


Server Software:        nginx
Server Hostname:        localhost
Server Port:            8500

Document Path:          /api/v1/users/me/
Document Length:        80 bytes

Concurrency Level:      50
Time taken for tests:   0.572 seconds
Complete requests:      20000
Failed requests:        0
Keep-Alive requests:    19829
Total transferred:      4939149 bytes
HTML transferred:       1600000 bytes
Requests per second:    34942.07 [#/sec] (mean)
Time per request:       1.431 [ms] (mean)
Time per request:       0.029 [ms] (mean, across all concurrent requests)
Transfer rate:          8426.96 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       3
Processing:     0    1   3.5      1      93
Waiting:        0    1   3.5      1      92
Total:          0    1   3.6      1      93

Percentage of the requests served within a certain time (ms)
  50%      1
  66%      1
  75%      1
  80%      1
  90%      1
  95%      2
  98%      2
  99%      2
 100%     93 (longest request)
```


