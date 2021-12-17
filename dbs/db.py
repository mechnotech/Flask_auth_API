from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from settings import config

db = SQLAlchemy()
cache = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)


def init_db(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://{config.pg_user}:{config.pg_pass}@{config.db_host}:{config.db_port}/{config.db_name}'
    )
    db.init_app(app)
