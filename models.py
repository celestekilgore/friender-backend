from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import jwt
from flask import current_app

bcrypt = Bcrypt()
db = SQLAlchemy()

DEFAULT_USER_IMAGE = "https://t4.ftcdn.net/jpg/02/15/84/43/240_F_215844325_ttX9YiIIyeaR7Ne6EaLLjMAmy4GvPC69.jpg"


class Relationship(db.Model):
    """Relationship in the system."""

    __tablename__ = 'relationships'

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    target_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
    )


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.String(100),
        nullable=False,
    )

    zip_code = db.Column(
        db.String(10),
        nullable=False,
    )

    friend_radius = db.Column(
        db.Integer,
        nullable=False,
    )

    hobbies = db.Column(
        db.Text,
        nullable=False
    )

    interests = db.Column(
        db.Text,
        nullable=False
    )

    image = db.Column(
        db.String(500),
        nullable=False,
        default=DEFAULT_USER_IMAGE
    )

    relationships = db.relationship(
        "Relationship",
        secondary="relationships",
        primaryjoin=(Relationship.owner_id == id),
        secondaryjoin=(Relationship.target_id == id),
        backref="user"
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}>"

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns jwt token.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(username=username).one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                payload = {"username": user.username}

                token = jwt.encode(
                    payload,
                    current_app.config.get('SECRET_KEY'),
                    algorithm='HS256'
                )

                return token

        return False

    @classmethod
    def signup(cls, username, password, zip_code, friend_radius, hobbies, interests, image):
        """Sign up user.

        Hashes password and adds user to session.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
            zip_code=zip_code,
            friend_radius=friend_radius,
            hobbies=hobbies,
            interests=interests,
            image=image
        )

        db.session.add(user)

        payload = {"username": user.username}

        token = jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

        return token


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    app.app_context().push()
    db.app = app
    db.init_app(app)
