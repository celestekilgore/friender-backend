import boto3
import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from functools import wraps
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
import jwt
from jwt.exceptions import DecodeError
from pyzipcode import ZipCodeDatabase

from forms import LoginForm, RegisterForm, RelationshipForm
from models import db, connect_db, User, Relationship
import uuid

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

client = boto3.client(
    's3',
    aws_access_key_id=os.environ['ACCESS_KEY'],
    aws_secret_access_key=os.environ['SECRET_ACCESS_KEY']
)

zcdb = ZipCodeDatabase()

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

    form = RegisterForm(data=request.form, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form.errors}), 400)

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
            "friend_radius": user.friend_radius,
            "hobbies": user.hobbies,
            "interests": user.interests,
            "image": user.image
        }
    })


# Image

def add_image(image):
    """Add image"""

    file_type = image.content_type.split("/")[0]

    if file_type != "image":
        return (jsonify({"errors": ["Invalid image"]}), 400)

    filename = str(uuid.uuid4())
    BUCKET_NAME = os.environ['BUCKET_NAME']

    client.upload_fileobj(
        image,
        BUCKET_NAME,
        filename,
        ExtraArgs={'ACL': 'public-read', 'ContentType':  image.content_type})

    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"


@app.get("/users/<string:username>/get-potential-friend")
@token_required
def get_potential_friend(current_user, username):
    """Get User"""

    zip_codes = [z.zip for z in zcdb.get_zipcodes_around_radius(
        current_user.zip_code, current_user.friend_radius)]

    users = User.query.filter(and_(
        User.zip_code.in_(zip_codes),
        User.username != username,
    )).all()

    user = None

    for target_user in users:
        we_exist_on_theirs = [
            r for r in target_user.relationships if r.target_user_id == current_user.id
        ]

        target_relationship = we_exist_on_theirs[0] if len(
            we_exist_on_theirs) > 0 else None

        they_exist_on_ours = [
            r for r in current_user.relationships if r.target_user_id == target_user.id
        ]

        # no relationship exists
        if not we_exist_on_theirs and not they_exist_on_ours:
            user = target_user
            break

        # they are awaiting your response
        if target_relationship and target_relationship.status == "pending":
            user = target_user
            break

    if not user:
        return jsonify({"message": "No users in your radius."})

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
    form = RelationshipForm(data=request.json, meta={"csrf": False})

    if not form.validate():
        return (jsonify({"errors": form.errors}), 400)

    # target_user = User.query.get(form.target_user_id.data)
    target_user = User.query.filter_by(username=username).first()

    we_exist_on_theirs = [
        r for r in target_user.relationships if r.target_user_id == current_user.id
    ]
    target_relationship = we_exist_on_theirs[0] if len(
        we_exist_on_theirs) > 0 else None

    they_exist_on_ours = [
        r for r in current_user.relationships if r.target_user_id == target_user.id
    ]
    owner_relationship = they_exist_on_ours[0] if len(
        they_exist_on_ours) > 0 else None

    if target_relationship and owner_relationship:
        if target_relationship.status == "friends" and owner_relationship.status == "friends":
            return (jsonify({"errors": ["Already friends."]}), 400)

        if target_relationship.status == "not-friends" and owner_relationship.status == "not-friends":
            return (jsonify({"errors": ["Already not friends."]}), 400)

    if form.response.data and not target_relationship and not owner_relationship:
        status = "pending"

    elif form.response.data and target_relationship.status == "pending":
        status = "friends"

    if not form.response.data:
        status = "not-friends"

    if target_relationship:
        target_relationship.status = status
    elif status == "not-friends":
        new_relationship = Relationship(
            owner_user_id=target_user.id,
            target_user_id=current_user.id,
            status=status
        )
        db.session.add(new_relationship)

    if owner_relationship:
        owner_relationship.status = status
    else:
        new_relationship = Relationship(
            owner_user_id=current_user.id,
            target_user_id=target_user.id,
            status=status
        )
        db.session.add(new_relationship)

    db.session.commit()

    return jsonify({"message": "Relationship successfully updated."})
