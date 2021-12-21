##  Auth API

### Для запуска в Dev нужно:
#### Создать окружение
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### Запустить контейнеры с Redis и Postgres
`docker-compose -f dev-compose.yaml up -d`

#### Применить миграции alembic
`alembic upgrade head`

#### При первом запуске (создать первичного пользователя (admin, password) и назначить ему админскую роль)
`python create_admin.py`

#### Запуск приложения:
`python pywsgi.py`

Описание работы этого API доступно после запуска будет доступно по адресу http://localhost:5000/swagger/

Тесты (без тестов, только коллекции) для Postman в папке project_description для Auth API и для Fast API

Там же yaml схема Auth API.

####

## Для запуска в Product
`docker-compose -up -d`

Приложение будет доступно по адресу http://localhost:8500


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

#### alembic

самая засадная технология этого проекта. Очень неочевидно устанавливается и весьма неочевидно пробрасывается meta контент
к его env.py
Итого. Если проект плоский, flask не выделен изначально в поддиректорию src (например)
в alembic.ini нужно указать параметр `prepend_sys_path = .` (а в иных случаях `prepend_sys_path = src`) Иначе относительный импорт будет корректен для Pycharm но при вызове
 alembic его не увидит. Попытка же решить проблему через манипуляции с PATH решит проблему миграций, но
приведет к слому настроек Pycharm, восстановить которые я смог только сбросом в "заводские" настройки :(

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

```
ab -k -c 50 -n 20000 -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MDA4OTg5OSwianRpIjoiMTk4ZGNlYzItZTg2Yi00NmE2LTg5N2YtYTM5NTMxMDkwNzZmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImFkbWluIiwibmJmIjoxNjQwMDg5ODk5LCJleHAiOjE2NDAwOTM0OTl9.AENg0kQCWlwYqAvB1-bzV_viv3EgUqPbvRWtCVNAvOQ" localhost:8500/api/v1/users/me/
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
Server Port:            85

Document Path:          /api/v1/users/me/
Document Length:        87 bytes

Concurrency Level:      50
Time taken for tests:   56.268 seconds
Complete requests:      20000
Failed requests:        9306
   (Connect: 0, Receive: 0, Length: 9306, Exceptions: 0)
Non-2xx responses:      9306
Keep-Alive requests:    19823
Total transferred:      5237475 bytes
HTML transferred:       2289054 bytes
Requests per second:    355.44 [#/sec] (mean)
Time per request:       140.669 [ms] (mean)
Time per request:       2.813 [ms] (mean, across all concurrent requests)
Transfer rate:          90.90 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       4
Processing:     0  140 177.9    120    1592
Waiting:        0  140 177.9    120    1592
Total:          0  140 177.9    120    1592

Percentage of the requests served within a certain time (ms)
  50%    120
  66%    161
  75%    225
  80%    264
  90%    372
  95%    499
  98%    641
  99%    747
 100%   1592 (longest request)

```


