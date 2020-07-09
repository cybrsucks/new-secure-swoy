import smtplib
import pyotp
import time
import datetime

base32secret = 'S3K3TPI5MYA2M67V'
# print('Secret:', base32secret)

totp = pyotp.TOTP(base32secret)
email_otp = totp.now()
# print('OTP code:', email_otp)
time.sleep(30)
# print('OTP code:', totp.now())


fromaddr = 'swoybubbletea@gmail.com'
toaddrs = 'swoybubbletea@gmail.com'
subject = "SWOY Bubble Tea"
body = "Hello! Your OTP: " + str(email_otp)
msg = f'Subject: {subject}\n\n{body}'
username = 'swoybubbletea@gmail.com'
password = 'SWOYB0b4T3A'
server = smtplib.SMTP('smtp.gmail.com:587')
server.starttls()
server.login(username, password)
server.sendmail(fromaddr, toaddrs, msg)
print("OTP sent to your email inbox.")
server.quit()

otp_not_finalised = True
while otp_not_finalised:
    resend = input("Resend?")
    if resend.upper() == "Y":
        email_otp = totp.now()
        time.sleep(30)
        fromaddr = 'swoybubbletea@gmail.com'
        toaddrs = 'swoybubbletea@gmail.com'
        # send to recipient change the above address
        subject = "SWOY Bubble Tea"
        body = "Hello! Your OTP: " + str(email_otp)
        msg = f'Subject: {subject}\n\n{body}'
        username = 'swoybubbletea@gmail.com'
        password = 'SWOYB0b4T3A'
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddrs, msg)
        print("OTP sent to your email inbox.")
        server.quit()
    else:
        break

check = input("Email OTP: ")
if check == email_otp:
    print("Success!")
    otp_not_finalised = False



