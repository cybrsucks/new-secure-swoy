from flask import Flask, render_template, redirect, url_for, request, flash
from Forms import LoginForm, RegistrationForm, CheckoutForm, DeliveryForm
import sqlite3


# class User:
#     def __init__(self, id, email, password):
#         self.id = id
#         self.email = email
#         self.password = password
#
# users = []
# users.append(User(id=1, email="abc@example.com", password="password"))
# users.append(User(id=2, email="qwerty@mymail.com", password="secret"))

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"
with sqlite3.connect("swoy.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS user(
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        admin INTEGER NOT NULL)""")
    # Uncomment to insert admin and test account if db is deleted
    # cursor.execute("INSERT INTO user(username, email,password, admin) "
    #                "VALUES('Super Admin', 'superadmin@swoy.com', 'swoyadmin', True)")
    # cursor.execute("INSERT INTO user(username, email,password, admin) "
    #                "VALUES('John Doe', 'johndoe@gmail.com', '12345678', False)")
    cursor.execute("SELECT * FROM user")
    print(cursor.fetchall())
    conn.commit()


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    test_list = [

        {"name": "Chocolate", "image": "Chocolate Boba.jpeg"},
        {"name": "Earl Grey", "image": "Earl Grey Boba.jpeg"},
        {"name": "Green Tea", "image": "Green Tea Boba.jpg"},
        {"name": "Mango", "image": "Mango Boba.jpg"},
        {"name": "Passionfruit", "image": "Passionfruit Boba.jpg"},
        {"name": "Strawberry", "image": "Strawberry Boba.jpeg"},
    ]

    # if request == 'POST' and form.validate on :
    #     session.pop('user_id', None)
    #
    #     email = request.form['email']
    #     password = request.form['password']
    #
    #     user = [x for x in users if x.email == email][0]
    #     if user and user.password == password:
    #         session['user_id'] = user.id
    #         return redirect(url_for("admin_base"))
    #
    #     return redirect(url_for("home"))
    return render_template("home.html", test_list=test_list)


@app.route("/admin")
def admin_home():
    return render_template("admin_base.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            username = form.username.data
            email = form.email.data
            password = form.password.data
            admin = 0
            command = f"INSERT INTO user(username, email, password, admin) " \
                      f"VALUES ('{username}', '{email}', '{password}', '{admin}')"
            cursor.execute(command)
            updated = cursor.execute("SELECT * FROM user").fetchall()
            print(f"Updated database : {updated}")
            conn.commit()

    return render_template("signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            email = form.email.data
            password = form.password.data
            command = f"SELECT * FROM user WHERE email='{email}' and password='{password}'"
            account_match = cursor.execute(command).fetchone()
            print(f"Account: {account_match}")
            if account_match:
                if account_match[4]:
                    return redirect(url_for("admin_home"))
                else:
                    return redirect(url_for("home"))
            else:
                return render_template("login.html", form=form, error=True)

    return render_template("login.html", form=form)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = CheckoutForm()
    return render_template("checkout.html", form=form)


@app.route("/delivery")
def delivery():
    form = DeliveryForm()
    return render_template("delivery.html", form=form)


@app.route("/product")
def product():
    return render_template("product.html")


if __name__ == "__main__":
    app.run(debug=True)
