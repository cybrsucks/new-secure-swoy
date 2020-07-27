from wtforms import StringField, PasswordField, validators, Form, DateField, DecimalField, SelectField, IntegerField
from wtforms.validators import InputRequired, Email, Length, NumberRange
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed


class LoginForm(FlaskForm):
    email = StringField('Email Address:', [validators.DataRequired()])
    password = PasswordField('Password:', [validators.DataRequired()])


class RegistrationForm(FlaskForm):
    username = StringField('Username:', [validators.DataRequired()])
    email = StringField('Email Address:', [validators.DataRequired()])
    password = PasswordField('New Password:', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
    ])
    confirm = PasswordField('Repeat Password:', [validators.DataRequired()])
    security_qns = SelectField('Security Question:',
                               choices=[('What is the name of your first pet?', 'What is the name of your first pet?'),
                                        ('What is the name of your favourite teacher?',
                                         'What is the name of your favourite teacher?'),
                                        ('What is your favourite pet?', 'What is your favourite pet?'),
                                        ('What is your hobby?', 'What is your hobby?'),
                                        ('What is a place that you would like to visit?',
                                         'What is a place that you would like to visit?'),
                                        ('What is the first country you visited?',
                                         'What is the first country you visited?'),
                                        ('What is the name of your favourite place to visit?',
                                         'What is the name of your favourite place to visit?')])

    security_ans = StringField("Answer:", [validators.DataRequired()])


class CheckoutForm(FlaskForm):
    address = StringField('Address:', [validators.data_required()])
    delivery_date = DateField('Expiry Date:', [validators.data_required()])
    delivery_time = SelectField('Delivery Time:', [validators.data_required()], choices=[
        ("12pm", "12pm"),
        ("1pm", "1pm"),
        ("2pm", "2pm"),
        ("3pm", "3pm"),
        ("4pm", "4pm"),
        ("5pm", "5pm"),
        ("6pm", "6pm")])
    creditNo = StringField('Credit Card Number:', [validators.data_required(), validators.NumberRange(min=1000000000000000, max=9999999999999999)])
    ccv = StringField('CCV:', [validators.data_required(), validators.NumberRange(min=100, max=999)])
    expireDate = DateField('Expiry Date:', [validators.data_required()])


class DeliveryForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(max=99)])
    address = StringField('Address:', [validators.data_required()])
    email = StringField('Email Address:', [validators.data_required(), validators.Length(min=6, max=35)])
    contactNo = StringField('Contact Number:', [validators.data_required(), validators.length(min=8, max=8)])


class ModifyDrinkForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=3, max=50,
                                                                                       message="Field must be between $3.00 to $50.00")],
                         places=2)
    thumbnail = FileField('Thumbnail:', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])


class AddDrinkForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=3, max=50,
                                                                                       message="Field must be between $3.00 to $50.00")],
                         places=2, default=5)
    thumbnail = FileField('Thumbnail:', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])


class ModifyToppingForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=0.1, max=10,
                                                                                       message="Field must be between $3.00 to $50.00")],
                         places=2)
    thumbnail = FileField('Thumbnail:', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])


class AddToppingForm(FlaskForm):
    name = StringField('Name:', [validators.data_required(), validators.length(min=3)])
    price = DecimalField('Price:', [validators.data_required(), validators.NumberRange(min=0.1, max=10,
                                                                                       message="Field must be between $3.00 to $50.00")],
                         places=2, default=0.5)
    thumbnail = FileField('Thumbnail:', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])


class ForgotPasswordEmailForm(FlaskForm):
    email = StringField('Email Address:', [validators.data_required()])


class ForgotPasswordSecurityAnswerForm(FlaskForm):
    security_ans = StringField('Answer:', [validators.data_required()])


class UpdatePasswordForm(FlaskForm):
    new_pwd = PasswordField('New Password:',
                          [validators.data_required(), validators.EqualTo('confirm_new_pwd', message='Passwords must match')])
    confirm_new_pwd = PasswordField('Confirm New Password:', [validators.data_required()])


class ChangeLoggedInUserUsernameForm(FlaskForm):
    new_username = StringField('Username:', [validators.DataRequired()])


class ChangeLoggedInUserPasswordForm(FlaskForm):
    current_pwd = PasswordField('Current Password:', [validators.data_required()])
    new_pwd = PasswordField('New Password:',
                          [validators.data_required(), validators.EqualTo('confirm_new_pwd', message='Passwords must match')])
    confirm_new_pwd = PasswordField('Confirm New Password:', [validators.data_required()])

class OTPForm(FlaskForm):
    otp = IntegerField('OTP: ', [validators.data_required()])

