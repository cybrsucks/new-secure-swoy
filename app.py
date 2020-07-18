from flask import Flask, render_template, redirect, url_for, request, Response
from wtforms import ValidationError

from Forms import *
from werkzeug.utils import secure_filename
import sqlite3
import re
from flask_jwt import jwt
import datetime
from functools import wraps

# class User:
#     def __init__(self, id, email, password):
#         self.id = id
#         self.email = email
#         self.password = password
#
# users = []
# users.append(User(id=1, email="abc@example.com", password="password"))
# users.append(User(id=2, email="qwerty@mymail.com", password="secret"))


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            print("token is missing")
            return redirect(url_for('login'))

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            print("token is accepted")

        except:
            print("Token expired")
            return redirect(url_for('home'))

        return f(*args, **kwargs)

    return decorated


app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretkey"


@app.route("/admin")
@token_required
def admin_dashboard():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None
    return render_template("admin_dashboard.html", admin_title="Dashboard", user_account=user_account)


@app.route("/admin/otp")
def authenticate_otp():
    form = OTPForm()
    return render_template("admin_authentication.html", admin_title="Your Account", form=form)


@app.route("/admin/<user_id>")
@token_required
def admin_own_account(user_id):
    return render_template("admin_own_account.html", admin_title="Your Account")


@app.route("/admin/menu_drinks")
@token_required
def admin_menu_drinks():
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drinks")
        drinks = cursor.fetchall()
    drink_list = []
    for drink in drinks:
        drink_list.append({"id": drink[0], "name": drink[1], "price": drink[2], "image": drink[3]})

    return render_template("admin_menu_drinks.html", admin_title="Menu Items - Drinks", drink_list=drink_list)


@app.route("/admin/menu_drinks/<drink_id>", methods=["GET", "POST"])
@token_required
def admin_menu_drinks_modify(drink_id):
    form = ModifyDrinkForm()
    if request.method == "GET":
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM drinks WHERE drink_id = '{drink_id}'")
            drink = cursor.fetchone()
        form.name.data = drink[1]
        form.price.data = drink[2]

    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            if filename:
                cursor.execute(f"UPDATE drinks SET name = '{name}', price = '{price}', thumbnail = '{filename}'"
                               f"WHERE drink_id = {drink_id}")
            else:
                cursor.execute(f"UPDATE drinks SET name = '{name}', price = '{price}'"
                               f"WHERE drink_id = {drink_id}")
            conn.commit()
        if filename:
            form.thumbnail.data.save("static/" + filename)

    return render_template("admin_menu_drinks_modify.html", admin_title=f"Menu Items - Modify Drinks - {form.name.data}", form=form, drink_id=drink_id)


@app.route("/admin/menu_drinks/add_drink", methods=["GET", "POST"])
@token_required
def admin_menu_drinks_add():
    form = AddDrinkForm()
    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        filename = secure_filename(form.thumbnail.data.filename)
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO drinks(name, price, thumbnail) "
                           f"VALUES('{name}', '{price}', '{filename}')")
        form.thumbnail.data.save("static/" + filename)
    return render_template("admin_menu_drinks_add.html", admin_title=f"Menu Items - Add Drink", form=form)


@app.route("/admin/menu_drinks/delete/<drink_id>", methods=["POST"])  # API
@token_required
def admin_menu_drinks_delete(drink_id):
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM drinks WHERE drink_id='{drink_id}'")
    return redirect(url_for("admin_menu_drinks"))


@app.route("/admin/menu_toppings")
@token_required
def admin_menu_toppings():
    return render_template("admin_menu_toppings.html", admin_title="Menu Items - Toppings")


@app.route("/admin/orders")
@token_required
def admin_orders():
    return render_template("admin_orders.html", admin_title="Delivery Orders")


@app.route("/admin/feedbacks")
@token_required
def admin_feedbacks():
    return render_template("admin_feedbacks.html", admin_title="Customer Feedbacks")


@app.route("/admin/user_accounts")
@token_required
def admin_user_accounts():
    return render_template("admin_user_accounts.html", admin_title="User Accounts")


@app.route("/admin/admin_accounts")
@token_required
def admin_admin_accounts():
    return render_template("admin_admin_accounts.html", admin_title="Admin Accounts")


@app.route("/admin/logs")
@token_required
def admin_logs():
    return render_template("admin_logs.html", admin_title="History Logs")


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None
    try:
        search = request.args["search"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM drinks WHERE "
                           f"name = '{search}' OR name LIKE '{search}%' OR name LIKE '%{search}' OR name LIKE '%{search}%'")
            drinks = cursor.fetchall()
    except:
        search = None
    if not search:
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drinks")
            drinks = cursor.fetchall()
    drink_list = []
    for drink in drinks:
        drink_list.append({"id": drink[0], "name": drink[1], "price": drink[2], "image": drink[3]})

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
    return render_template("home.html", drink_list=drink_list, user_account=user_account, search=search)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    error = None
    error_password = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            username = form.username.data
            email = form.email.data
            password = form.password.data

            if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", password):
                error_password = "Your password must be at least 8 characters, contain at least 1 symbol (@, $, !, %, *, #, ?, &), at least 1 uppercase and at least 1 lowercase"
                return render_template("signup.html", form=form, error=error, error_password=error_password)
            else:
                error_password = None

            security_qns = form.security_qns.data
            security_ans = form.security_ans.data
            admin = 0
            command = f"SELECT * FROM user WHERE email='{email}'"
            account_match = cursor.execute(command).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                error = "Email already exists"
            else:
                command = f"INSERT INTO user(username, email, password, security_qns, security_ans, admin) " \
                          f"VALUES ('{username}', '{email}', '{password}', '{security_qns}', '{security_ans}', '{admin}')"
                cursor.execute(command)
                updated = cursor.execute("SELECT * FROM user").fetchall()
                print(f"Updated database : {updated}")
                conn.commit()
                return render_template("login.html", form=LoginForm())

    return render_template("signup.html", form=form, error=error, error_password=error_password)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            email = form.email.data
            password = form.password.data
            cursor.execute(f"SELECT * FROM user WHERE email='{email}'")
            account_match = cursor.fetchone()
            if account_match:
                command = f"SELECT * FROM user WHERE email='{email}' and password='{password}'"
                account_match = cursor.execute(command).fetchone()
                print(f"Account: {account_match}")
                if account_match:
                    if account_match[6]:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() +
                                            datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        return redirect(url_for("admin_dashboard", id=account_match[0], token=token.decode('utf-8')))
                    else:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() +
                                            datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        return redirect(url_for("home", id=account_match[0], token=token.decode('utf-8')))
                else:
                    error = "Password is incorrect."
            else:
                error = "Email does not exist."

    return render_template("login.html", form=form, error=error)


@app.route("/product/<drink_name>")
def product(drink_name):
    comment_list = []
    drink = None
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM drinks WHERE name = '{drink_name}'")
        drink = cursor.fetchone()
        if drink:
            cursor.execute(f"SELECT * FROM comments WHERE drink_id = '{drink[0]}'")
            comments = cursor.fetchall()
            comment_list = []
            for comment in comments:
                cursor.execute(f"SELECT username FROM user WHERE user_id = '{comment[2]}'")
                author = cursor.fetchone()[0]
                comment_list.append({"content": comment[1], "author": author})
        else:
            return redirect(url_for("home"))
    return render_template("product.html", drink=drink, comment_list=comment_list, user_account=user_account)


@app.route("/product/update_drink_comments", methods=["GET", "POST"])  # API
@token_required
def update_comment():
    try:
        drink_id = request.args["drink_id"]
        user_id = request.args["user_id"]
        content = request.form["content"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO comments(content, user_id, drink_id) "
                           f"VALUES ('{content}', '{user_id}', '{drink_id}')")
            cursor.execute(f"SELECT name FROM drinks WHERE drink_id = '{drink_id}'")
            drink_name = cursor.fetchone()[0]
            conn.commit()
        return redirect(url_for("product", id=user_id, drink_name=drink_name, _anchor="comments"))
    except:
        return redirect(url_for("home"))


@app.route("/checkout", methods=["GET", "POST"])
@token_required
def checkout():
    form = CheckoutForm()
    return render_template("checkout.html", form=form)


@app.route("/delivery")
@token_required
def delivery():
    form = DeliveryForm()
    return render_template("delivery.html", form=form)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordEmailForm()
    error = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            email = form.email.data
            cursor = conn.cursor()
            command = f"SELECT * FROM user WHERE email='{email}'"
            account_match = cursor.execute(command).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                return redirect(url_for('security_question', email=email))
            else:
                error = "Email does not exist"

    return render_template("forgot_password_EMAIL.html", form=form, error=error)


@app.route("/forgot_password/<email>", methods=["GET", "POST"])
def security_question(email):
    form = ForgotPasswordSecurityAnswerForm()
    error = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE email = '{email}'")
        user_account = cursor.fetchone()
    security_qn = user_account[4]
    if request.method == "POST" and form.validate_on_submit():
        given_ans = form.security_ans.data
        if given_ans.lower() == user_account[5].lower():
            return redirect(url_for('forgot_password_change', email=email))
        else:
            error = "Wrong answer given."
    return render_template("forgot_password.html", form=form, security_qn=security_qn, email=email, error=error)


@app.route("/forgot_password/<email>/change", methods=["GET", "POST"])
def forgot_password_change(email):
    form = UpdatePasswordForm()
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            new_password = form.new_pwd.data
            cursor.execute(f"UPDATE user SET password = '{new_password}' WHERE email = '{email}'")
            conn.commit()
        return redirect(url_for('home'))

    return render_template("update_password.html", form=form, email=email)


@app.route("/pw")
def pw():
    with open("default.md", "r") as v:
        return Response(v.read(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)
