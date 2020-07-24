import pyotp
import time

# base32secret = 'S3K3TPI5MYA2M67V'
# print('Secret:', base32secret)
#
# totp = pyotp.TOTP(base32secret)
# print('OTP code:', totp.now())
# time.sleep(30)
# print('OTP code:', totp.now())

# import time
# timeout = time.time() + 60*5   # 5 minutes from now
# while True:
#     test = 0
#     if test == 5 or time.time() > timeout:
#         break
#     test = test - 1

import smtplib
import pyotp
import time
import datetime

base32secret = 'S3K3TPI5MYA2M67V'
# print('Secret:', base32secret)

totp = pyotp.TOTP(base32secret)
# email_otp = totp.now()
# # print('OTP code:', email_otp)
# time.sleep(30)
# # print('OTP code:', totp.now())

timeout = time.time() + 60*3   # 1 minutes from now


def send_otp():
    email_otp = totp.now()

    fromaddr = 'swoybubbletea@gmail.com'
    toaddrs = 'swoybubbletea@gmail.com'
    subject = "SWOY Bubble Tea - This is your OTP!"
    body = "Hello " + str(toaddrs) + "! \nYour OTP: " + str(email_otp)
    msg = f'Subject: {subject}\n\n{body}'
    username = 'swoybubbletea@gmail.com'
    password = 'SWOYB0b4T3A'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg)
    print("OTP sent to your email inbox.")
    server.quit()
    print(email_otp)
    return email_otp


email_otp = send_otp()
check = input("Email OTP: ")
if time.time() > timeout or check != email_otp:
    print("OTP INVALID OR EXPIRED")
    exit()
elif check == email_otp and time.time() < timeout:
    print("Success!")



