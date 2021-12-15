from datetime import timedelta
from pydantic.error_wrappers import ValidationError
from flask import Flask
from flask import jsonify
from flask import request
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from dbs.db import db, cache, init_db
from db_models.models import User, Profile
from utils.models import UserSet, LoginSet
from utils.tools import is_user_exists, get_user_tokens, is_password_correct, register_user_data

ACCESS_EXPIRES = timedelta(hours=1)
REFRESH_EXPIRES = timedelta(days=1)
app = Flask(__name__)
init_db(app)
app.app_context().push()
db.create_all()

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'Eww3ssefw2931dfsd'  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = ACCESS_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = REFRESH_EXPIRES
jwt = JWTManager(app)


# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@app.route("/login", methods=["POST"])
def login():
    try:
        user = LoginSet(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    if not is_user_exists(user):
        return jsonify({"error": 'Такой пользователь не существует!'}), 404
    if not is_password_correct(user):
        return jsonify({"error": 'Пароль неверный!'}), 403
    access_token, refresh_token = get_user_tokens(user)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


@app.route("/registration", methods=["POST"])
def registration():
    try:
        user = UserSet(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    if is_user_exists(user, check_email=True):
        return jsonify({"error": 'Пользователь с таким login или email уже создан!'}), 409
    access_token, refresh_token = get_user_tokens(user)
    register_user_data(refresh_token, user)
    return jsonify(access_token=access_token, refresh_token=refresh_token)


# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
    )
