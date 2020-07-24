import re



def validate():
    passwd = 'JacobEvans'
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pat = re.compile(reg)
    mat = re.search(pat, passwd)
    if mat:
        print("Password is valid.")
    else:
        print("Password invalid !!")

validate()
