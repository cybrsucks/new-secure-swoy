import smtplib
import pyotp
base32secret = 'S3K3TPI5MYA2M67V'
totp = pyotp.TOTP(base32secret)
# timeout = time.time() + 60*3


def send_otp(send_to_email):
    email_otp = totp.now()
    fromaddr = 'swoybubbletea@gmail.com'
    toaddrs = send_to_email
    subject = "SWOY Bubble Tea - This is your OTP!"
    body = "Hello " + str(toaddrs) + "! \nYour OTP: " + str(email_otp)
    msg = f'Subject: {subject}\n\n{body}'
    username = 'swoybubbletea@gmail.com'
    password = 'SWOYB0b4T3A'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
    return email_otp



