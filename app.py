from forms import LoginForm, RegisterForm, RelationshipForm
from models import db, connect_db, User, Relationship
from api import add_image, get_zip_codes_around_radius, form_errors_to_list
import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
import jwt
from jwt.exceptions import DecodeError

load_dotenv()


app = Flask(__name__)

CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

connect_db(app)


def token_required(f):
    """Decorator for protecting routes."""

    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        # ensure the jwt-token is passed with the headers
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:  # throw error if no token provided
            return (jsonify({"message": "Unauthorized"}), 401)

        try:
            # decode the token to obtain user public_id
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=['HS256'])

        except DecodeError:
            return (jsonify({"message": "Unauthorized"}), 401)

        current_user = User.query.filter_by(username=data['username']).first()
        if current_user is None:
            return (jsonify({"message": "Unauthorized"}), 401)

        # Return the user information attached to the token
        return f(current_user, *args, **kwargs)

    return decorator


@app.post("/login")
def login():
    """Authenticates username and password and returns JWT token."""

    form = LoginForm(data=request.json, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form_errors_to_list(form.errors)}), 400)

    token = User.authenticate(
        form.username.data,
        form.password.data,
    )

    if not token:
        return (jsonify({"errors": ["Invalid username/password."]}), 400)

    return jsonify({"token": token})


@app.post("/register")
def register():
    """Validates register data, creates new user, and returns JWT token."""

    form = RegisterForm(data=request.form, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form_errors_to_list(form.errors)}), 400)

    image_url = add_image(form.image.data) if form.image.data else None

    try:
        token = User.signup(
            form.username.data,
            form.password.data,
            form.zip_code.data,
            form.friend_radius.data,
            form.hobbies.data,
            form.interests.data,
            image_url
        )
        db.session.commit()

    except IntegrityError:
        return (jsonify({"errors": ["Username already taken."]}), 400)

    return jsonify({"token": token})


@app.get("/users/<string:username>")
@token_required
def get_user(current_user, username):
    """Takes username and returns user."""

    user = User.query.filter_by(username=username).first()

    if not user:
        return (jsonify({"errors": ["User not found."]}), 400)

    return jsonify({
        "user": {
            "username": user.username,
            "zip_code": user.zip_code,
            "friend_radius": user.friend_radius,
            "hobbies": user.hobbies,
            "interests": user.interests,
            "image": user.image
        }
    })


@app.get("/users/<string:username>/get-potential-friend")
@token_required
def get_potential_friend(current_user, username):
    """Returns potential friend user within friend radius."""

    zip_codes = get_zip_codes_around_radius(
        current_user.zip_code,
        current_user.friend_radius
    )

    user = User.query.outerjoin(
        Relationship,
        or_(
            (Relationship.owner_id == User.id) & (
                Relationship.target_id == current_user.id),
            (Relationship.owner_id == current_user.id) & (
                Relationship.target_id == User.id),
        )
    ).filter(
        User.id != current_user.id,
        User.zip_code.in_(zip_codes),
        or_(
            Relationship.status.is_(None),
            and_(
                Relationship.owner_id != current_user.id,
                Relationship.status == 'pending',
            ),
        )
    ).first()

    if not user:
        return jsonify({"user": None})

    return jsonify({
        "user": {
            "username": user.username,
            "zip_code": user.zip_code,
            "friend_radius": user.friend_radius,
            "hobbies": user.hobbies,
            "interests": user.interests,
            "image": user.image
        }
    })


@app.post("/users/<string:username>/establish-relationship")
@token_required
def establish_relationship(current_user, username):
    """
    Takes username and establishes relationship with current user based on
    current user response.
    """

    form = RelationshipForm(data=request.json, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form_errors_to_list(form.errors)}), 400)

    target_user = User.query.filter_by(username=username).first()
    relationship = Relationship.query.get((target_user.id, current_user.id))
    status = "friends" if form.response.data else "not-friends"

    if relationship:
        relationship.status = status
    else:
        status = status if status == "not-friends" else "pending"

        new_relationship = Relationship(
            owner_id=current_user.id,
            target_id=target_user.id,
            status=status
        )
        db.session.add(new_relationship)

    db.session.commit()

    return jsonify({"status": status})


@app.get("/users/<string:username>/get-friends")
@token_required
def get_friends(current_user, username):
    """Takes username and returns list of friends."""

    target_user = User.query.filter_by(username=username).first()

    friends = User.query.join(
        Relationship,
        or_(
            (Relationship.owner_id == User.id) & (
                Relationship.target_id == target_user.id),
            (Relationship.owner_id == target_user.id) & (
                Relationship.target_id == User.id),
        )
    ).filter(
        Relationship.status == "friends"
    ).all()

    friends = [{"username": f.username, "image": f.image} for f in friends]

    return jsonify({"friends": friends})
