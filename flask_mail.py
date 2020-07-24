import smtplib
fromaddr = 'swoybubbletea@gmail.com'
toaddrs = 'swoybubbletea@gmail.com'
subject = "SWOY Bubble Tea"
body = "Hello! Your OTP:"
msg = f'Subject: {subject}\n\n{body}'
username = 'swoybubbletea@gmail.com'
password = 'SWOYB0b4T3A'
server = smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg)
server.quit()






















# from flask_mail import Mail, Message
# from flask import Flask
#
# app = Flask(__name__)
#
# mail = Mail(app)
#
# app.config.from_object(__name__)
# app.config.from_envvar('MINITWIT_SETTINGS', silent=True)
# app.config.update(
#     DEBUG=True,
#     # Flask-Mail Configuration
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT=587,
#     MAIL_USE_TLS=True,
#     MAIL_USE_SSL=False,
#     MAIL_USERNAME='swoybubbletea@gmail.com',
#     MAIL_PASSWORD='SWOYB0b4T3A',
#     DEFAULT_MAIL_SENDER='gmailuser@gmail.com')
#
# # setup Mail
# mail = Mail(app)
#
#
# @app.route('/testmail')
# def mail_it():
#     """handles our message notification"""
#     msg = Message("Hello",
#                   sender=("Gmail User", "swoybubbletea@gmail.com"), recipients=["swoybubbletea@gmail.com"])
#     msg.body = "Test!"
#     mail.send(msg)
#     return "I sent an email!"
#
#
# mail_it()
