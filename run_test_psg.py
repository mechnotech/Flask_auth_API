from app import app
from db import db, init_db
from db_models import User, Profile

# Подготоваливаем контекст и создаём таблицы
init_db(app)
app.app_context().push()
db.create_all()

# Insert-запросы
admin = User(login='admin', password='password', email='mc@ya.ru')
db.session.add(admin)
db.session.commit()

# Select-запросы
User.query.all()
user = User.query.filter_by(login='admin').first()
profile = Profile(user_id=user.id)
db.session.add(profile)
db.session.commit()