from wtforms import StringField, PasswordField, validators, Form, DateField, DecimalField
from wtforms.validators import InputRequired, Email, Length, NumberRange
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed


class LoginForm(FlaskForm):
    email = StringField('Email Address:', [validators.DataRequired(), validators.Length(min=6, max=35)])
    password = PasswordField('Password:', [validators.DataRequired(), validators.Length(min=8)])


class RegistrationForm(FlaskForm):
    username = StringField('Username:', [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = StringField('Email Address:', [validators.DataRequired(), validators.Length(min=6, max=35)])
    password = PasswordField('New Password:', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(min=8)
    ])
    confirm = PasswordField('Repeat Password:', [validators.DataRequired()])


class CheckoutForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(max=99)])
    address = StringField('Address:', [validators.data_required()])
    creditNo = StringField('Credit Card Number:', [validators.data_required(), validators.length(min=16, max=16)])
    ccv = StringField('CCV:', [validators.data_required(), validators.length(min=3, max=3)])
    expireDate = DateField('Expiry Date:', [validators.data_required()])


class DeliveryForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(max=99)])
    address = StringField('Address:', [validators.data_required()])
    email = StringField('Email Address:', [validators.data_required(), validators.Length(min=6, max=35)])
    contactNo = StringField('Contact Number:', [validators.data_required(), validators.length(min=8, max=8)])


class ModifyDrinkForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=3, max=50, message="Field must be between $3.00 to $50.00")], places=2)
    thumbnail = FileField('Thumbnail:', [FileAllowed(['jpg', 'jpeg', 'png'], 'Images Only!')])


class AddDrinkForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=3, max=50, message="Field must be between $3.00 to $50.00")], places=2, default=5)
    thumbnail = FileField('Thumbnail:', [FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images Only!')])
