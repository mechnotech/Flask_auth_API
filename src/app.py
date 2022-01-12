from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager

from dbs.db import init_db
from settings import config
from views.auth.auth import auth
from views.oauth.oauth import oauth
from views.role.role import role
from views.users.users import users

app = Flask(__name__)
app.config.from_pyfile('settings.py', silent=True)
init_db(app)
app.app_context().push()

swagger = Swagger(app, template_file='project_description/openapi.yaml')
jwt = JWTManager(app)
app.register_blueprint(auth, url_prefix='/api/v1/auth')
app.register_blueprint(users, url_prefix='/api/v1/users')
app.register_blueprint(role, url_prefix='/api/v1/role')
app.register_blueprint(oauth, url_prefix='/api/v1/oauth')


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.auth_port,
    )
