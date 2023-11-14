import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from functools import wraps
from sqlalchemy.exc import IntegrityError
import jwt
from jwt.exceptions import DecodeError

from forms import LoginForm, RegisterForm
from models import db, connect_db, User

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

connect_db(app)


# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        # ensure the jwt-token is passed with the headers
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:  # throw error if no token provided
            return (jsonify({"message": "A valid token is missing!"}), 401)

        try:
            # decode the token to obtain user public_id
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except DecodeError:
            return (jsonify({"message": "Unauthorized"}), 401)

        user = User.query.filter_by(username=data['username']).first()
        if user is None:
            return (jsonify({"message": "Unauthorized"}), 401)

        # Return the user information attached to the token
        return f(user, *args, **kwargs)

    return decorator

# Login


@app.post("/login")
def login():
    """Login"""

    form = LoginForm(data=request.json, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form.errors}), 400)

    token = User.authenticate(
        form.username.data,
        form.password.data,
    )

    if not token:
        return (jsonify({"errors": ["Invalid username/password."]}), 400)

    return jsonify({"token": token})


# Register


@app.post("/register")
def register():
    """Register"""

    form = RegisterForm(data=request.json, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form.errors}), 400)

    try:
        token = User.signup(
            form.username.data,
            form.password.data,
            form.zip_code.data,
            form.friend_radius.data
        )
        db.session.commit()

    except IntegrityError:
        return (jsonify({"errors": ["Username already taken."]}), 400)

    return jsonify({"token": token})


# User

@app.get("/users/<string:username>")
@token_required
def get_user(current_user, username):
    """Get User"""

    user = User.query.filter_by(username=username).first()

    if not user:
        return (jsonify({"errors": ["User not found."]}), 400)

    return jsonify({
        "user": {
            "username": user.username,
            "zip_code": user.zip_code,
            "friend_radius": user.friend_radius
        }
    })
