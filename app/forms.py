from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    # Member Profile
    username = StringField("Username *", validators=[
        DataRequired(), Length(min=5, max=10, message="5-10 characters required")
    ], description="5 – 10 alphabetic, numeric characters or full stop")
    
    email = StringField("Email *", validators=[
        DataRequired(), Email(message="Please enter a valid email address.")
    ])
    
    password = PasswordField("Password *", validators=[
        DataRequired(), Length(min=6, max=10, message="6-10 characters required")
    ], description="Create your password for this internet ticketing system (6 - 10 alphabetic or numeric characters)")
    
    password2 = PasswordField("Confirm Password *", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match")
    ])

    # Basic Information
    given_name = StringField("Given Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    gender = RadioField("Gender", choices=[("Male", "Male"), ("Female", "Female")])
    day = SelectField("Day of Birth", choices=[(str(i), str(i)) for i in range(1, 32)])
    month = SelectField("Month of Birth", choices=[
        ("1", "January"), ("2", "February"), ("3", "March"),
        ("4", "April"), ("5", "May"), ("6", "June"),
        ("7", "July"), ("8", "August"), ("9", "September"),
        ("10", "October"), ("11", "November"), ("12", "December")
    ])
    year = SelectField("Year of Birth", choices=[(str(y), str(y)) for y in range(1950, 2026)])

    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[
                              DataRequired(), EqualTo('password')])
    submit = SubmitField("Request Password Reset")

