from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from sqlalchemy import MetaData

from settings import config

convention = {
    'all_column_names': lambda constraint, table: '_'.join([column.name for column in constraint.columns.values()]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': ('fk__%(table_name)s__%(all_column_names)s__' '%(referred_table_name)s'),
    'pk': 'pk__%(table_name)s',
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)
cache = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)


def init_db(app: Flask):
    db.init_app(app)
