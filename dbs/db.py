from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis

db = SQLAlchemy()
cache = redis.Redis(host='localhost', port=6363, db=0)


def init_db(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://auth:auth@localhost:5433/auth'
    db.init_app(app)
