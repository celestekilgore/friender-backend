from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Length, NumberRange


class LoginForm(FlaskForm):
    """Form for logging in a user."""

    username = StringField(
        "Username",
        validators=[InputRequired()],
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired()],
    )


class RegisterForm(FlaskForm):
    """Form for registering new user."""

    username = StringField(
        "Username",
        validators=[InputRequired(), Length(min=2, max=30)],
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(min=6, max=100)],
    )

    zip_code = StringField(
        "Zip Code",
        validators=[InputRequired(), Length(min=2, max=10)],
    )

    friend_radius = IntegerField(
        "Friend Radius",
        validators=[InputRequired(), NumberRange(min=1, max=9999)],
    )