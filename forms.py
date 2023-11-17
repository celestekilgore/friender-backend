from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField, FileField, BooleanField
from wtforms.validators import InputRequired, Length, NumberRange, Optional, ValidationError, AnyOf
from flask_wtf.file import FileAllowed
from api import is_valid_zip_code


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

    def validate_zip_code(self, field):
        """Takes zip code field and raises error if invalid."""

        if field.data:
            if not is_valid_zip_code(field.data):
                raise ValidationError("Invalid")

    friend_radius = IntegerField(
        "Friend Radius",
        validators=[InputRequired(), NumberRange(min=1, max=9999)],
    )

    hobbies = TextAreaField(
        "Hobbies",
        validators=[InputRequired(), Length(min=2, max=500)]
    )

    interests = TextAreaField(
        "Interests",
        validators=[InputRequired(), Length(min=2, max=500)]
    )

    image = FileField(
        "Image",
        validators=[Optional(), FileAllowed(['png', 'gif', 'jpg', 'jpeg'])]
    )


class RelationshipForm(FlaskForm):
    """Form for establishing relationship."""

    response = BooleanField(
        "Response",
        validators=[AnyOf([True, False])],
    )
