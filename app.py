from flask import Flask, render_template, redirect, url_for, request
from Forms import *
from werkzeug.utils import secure_filename
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


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
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
    return render_template("home.html", drink_list=drink_list)


@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", admin_title="Dashboard")


@app.route("/admin/<user_id>")
def admin_own_account(user_id):
    return render_template("admin_own_account.html", admin_title="Your Account")


@app.route("/admin/menu_drinks")
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
def admin_menu_drinks_delete(drink_id):
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM drinks WHERE drink_id='{drink_id}'")
    return redirect(url_for("admin_menu_drinks"))


@app.route("/admin/menu_toppings")
def admin_menu_toppings():
    return render_template("admin_menu_toppings.html", admin_title="Menu Items - Toppings")


@app.route("/admin/orders")
def admin_orders():
    return render_template("admin_orders.html", admin_title="Delivery Orders")


@app.route("/admin/feedbacks")
def admin_feedbacks():
    return render_template("admin_feedbacks.html", admin_title="Customer Feedbacks")


@app.route("/admin/user_accounts")
def admin_user_accounts():
    return render_template("admin_user_accounts.html", admin_title="User Accounts")


@app.route("/admin/admin_accounts")
def admin_admin_accounts():
    return render_template("admin_admin_accounts.html", admin_title="Admin Accounts")


@app.route("/admin/logs")
def admin_logs():
    return render_template("admin_logs.html", admin_title="History Logs")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            username = form.username.data
            email = form.email.data
            password = form.password.data
            security_qns = form.security_qns.data
            security_ans = form.security_ans.data
            admin = 0
            command = f"SELECT * FROM user WHERE email='{email}'"
            account_match = cursor.execute(command).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                return "error"
            else:
                command = f"INSERT INTO user(username, email, password, security_qns, security_ans, admin) " \
                          f"VALUES ('{username}', '{email}', '{password}', '{security_qns}', '{security_ans}' '{admin}')"
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
                    return redirect(url_for("admin_dashboard"))
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


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordEmailForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        return redirect(url_for('security_question', email=email))
    return render_template("forgot_password_EMAIL.html", form=form)


@app.route("/forgot_password/<email>", methods=["GET", "POST"])
def security_question(email):
    form = ForgotPasswordSecurityAnswerForm()
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE email = '{email}'")
        user_account = cursor.fetchone()
    security_qn = user_account[4]
    if request.method == "POST" and form.validate_on_submit():
        given_ans = form.security_ans.data
        if given_ans == user_account[5]:
            return redirect(url_for('forgot_password_change', email=email))
    return render_template("forgot_password.html", form=form, security_qn=security_qn, email=email)


@app.route("/forgot_password/<email>/change", methods=["GET", "POST"])
def forgot_password_change(email):
    return "Hello"


if __name__ == "__main__":
    app.run(debug=True)
