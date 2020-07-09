import pyotp
import time

# base32secret = 'S3K3TPI5MYA2M67V'
# print('Secret:', base32secret)
#
# totp = pyotp.TOTP(base32secret)
# print('OTP code:', totp.now())
# time.sleep(30)
# print('OTP code:', totp.now())

import time
timeout = time.time() + 60*5   # 5 minutes from now
while True:
    test = 0
    if test == 5 or time.time() > timeout:
        break
    test = test - 1
