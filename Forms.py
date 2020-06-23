from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message="Invalid email"), Length(max=50)])
    password = PasswordField('password', validators=[InputRequired, Length(min=8, max=99)])
