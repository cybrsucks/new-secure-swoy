from flask import Flask, render_template, redirect, url_for, request, Response
from Forms import *
from werkzeug.utils import secure_filename
import sqlite3
import xmltodict
import xml.etree.ElementTree


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


@app.route("/admin")
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


@app.route("/admin/<user_id>")
def admin_own_account(user_id):
    return render_template("admin_own_account.html", admin_title="Your Account")


@app.route("/admin/menu_drinks")
def admin_menu_drinks():
    # with sqlite3.connect("swoy.db") as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT * FROM drinks")
    #     drinks = cursor.fetchall()

    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = productData["products"]["drinks"]

    drink_list = []
    for drink in drinks:
        for i in drinks[drink]:
            drink_list.append({"id": i["@id"], "name": i["description"], "price": i["price"], "image": i["thumbnail"]})

    return render_template("admin_menu_drinks.html", admin_title="Menu Items - Drinks", drink_list=drink_list)


@app.route("/admin/menu_drinks/<drink_id>", methods=["GET", "POST"])
def admin_menu_drinks_modify(drink_id):
    form = ModifyDrinkForm()
    if request.method == "GET":
        # with sqlite3.connect("swoy.db") as conn:
        #     cursor = conn.cursor()
        #     cursor.execute(f"SELECT * FROM drinks WHERE drink_id = '{drink_id}'")
        #     drink = cursor.fetchone()
        productData = xmltodict.parse(open("static/products.xml", "r").read())
        drinks = productData["products"]["drinks"]
        for drink in drinks:
            for i in drinks[drink]:
                if i["@id"] == drink_id:
                    form.name.data = i["description"]
                    form.price.data = float(i["price"])
        #
        # return render_template("admin_menu_drinks_modify.html", admin_title=f"Menu Items - Modify Drinks - {name}" ,form=form, drink_id=drink_id)

    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None
        # with sqlite3.connect("swoy.db") as conn:
        #     cursor = conn.cursor()
        #     if filename:
        #         cursor.execute(f"UPDATE drinks SET name = '{name}', price = '{price}', thumbnail = '{filename}'"
        #                        f"WHERE drink_id = {drink_id}")
        #     else:
        #         cursor.execute(f"UPDATE drinks SET name = '{name}', price = '{price}'"
        #                        f"WHERE drink_id = {drink_id}")
        #     conn.commit()
        # if filename:
        #     form.thumbnail.data.save("static/" + filename)

        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        id = int(drink_id)
        et = xml.etree.ElementTree.parse("static/products.xml")
        drinkTag = et.getroot()[0].getchildren()[id-1]
        for element in list(drinkTag):
            if element.tag == "thumbnail":
                if filename != None:
                    drinkTag.remove(element)
            else:
                drinkTag.remove(element)

        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "price")
        priceTag.text = str(price)
        if filename != None:
            thumbnailTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "thumbnail")
            thumbnailTag.text = filename
        et.write("static/products.xml")

    return render_template("admin_menu_drinks_modify.html", admin_title=f"Menu Items - Modify Drinks - {form.name.data}", form=form, drink_id=drink_id)


@app.route("/admin/menu_drinks/add_drink", methods=["GET", "POST"])
def admin_menu_drinks_add():
    form = AddDrinkForm()
    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None
        # with sqlite3.connect("swoy.db") as conn:
        #     cursor = conn.cursor()
        #     cursor.execute(f"INSERT INTO drinks(name, price, thumbnail) "
        #                    f"VALUES('{name}', '{price}', '{filename}')")
        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        et = xml.etree.ElementTree.parse("static/products.xml")
        newTag = xml.etree.ElementTree.SubElement(et.getroot()[0], 'drink')
        id = len(et.findall("*/drink"))
        newTag.attrib["id"] = str(id)
        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "price")
        priceTag.text = str(price)
        thumbnailTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id-1], "thumbnail")
        thumbnailTag.text = filename
        et.write("static/products.xml")
    return render_template("admin_menu_drinks_add.html", admin_title=f"Menu Items - Add Drink", form=form)


@app.route("/admin/menu_drinks/delete/<drink_id>", methods=["POST"])  # API
def admin_menu_drinks_delete(drink_id):
    # with sqlite3.connect("swoy.db") as conn:
    #     cursor = conn.cursor()
    #     cursor.execute(f"DELETE FROM drinks WHERE drink_id='{drink_id}'")
    id = drink_id
    et = xml.etree.ElementTree.parse("static/products.xml")
    for drinkTag in list(et.getroot()[0].getchildren()):
        if id == drinkTag.attrib["id"]:
            et.getroot()[0].remove(drinkTag)
            et.write("static/products.xml")

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
    # if not search:
    #     with sqlite3.connect("swoy.db") as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT * FROM drinks")
    #         drinks = cursor.fetchall()
    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = productData["products"]["drinks"]

    drink_list = []
    for drink in drinks:
        for i in drinks[drink]:
            drink_list.append({"id": i["@id"], "name": i["description"], "price": i["price"], "image": i["thumbnail"]})

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
                error = "Email already exists"
            else:
                command = f"INSERT INTO user(username, email, password, security_qns, security_ans, admin) " \
                          f"VALUES ('{username}', '{email}', '{password}', '{security_qns}', '{security_ans}', '{admin}')"
                cursor.execute(command)
                updated = cursor.execute("SELECT * FROM user").fetchall()
                print(f"Updated database : {updated}")
                conn.commit()
                return render_template("login.html", form=LoginForm())

    return render_template("signup.html", form=form, error=error)


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
                        return redirect(url_for("admin_dashboard", id=account_match[0]))
                    else:
                        return redirect(url_for("home", id=account_match[0]))
                else:
                    error = "Password is incorrect."
            else:
                error = "Email does not exist."

    return render_template("login.html", form=form, error=error)


@app.route("/product/<drink_name>")
def product(drink_name):
    comment_list = []
    drink = None
    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = productData["products"]["drinks"]

    for drinkTag in drinks:
        for i in drinks[drinkTag]:
            if i["description"] == drink_name:
                drink = (int(i["@id"]), i["description"], float(i["price"]), i["thumbnail"])

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
        # drink = cursor.fetchone()

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


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = CheckoutForm()
    return render_template("checkout.html", form=form)


@app.route("/delivery")
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


@app.route("/profile", methods=["GET", "POST"])
def view_profile():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            username = user_account[1]
            email = user_account[2]
    except:
        user_account = None

    username_form = ChangeLoggedInUserUsernameForm()
    password_form = ChangeLoggedInUserPasswordForm()
    if request.method == "POST" and username_form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            new_username = username_form.new_username.data
            cursor.execute(f"UPDATE user SET username = '{new_username}' WHERE user_id = '{user_id}'")
            conn.commit()
        return redirect(url_for('home'))
    elif request.method == "POST" and password_form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            current_password_from_db = cursor.execute(f"SELECT password WHERE user_id = '{user_id}")
            if current_password_from_db != password_form.current_pwd.data:
                print("The current password was incorrect. Your password cannot be changed ta this time.")

            new_password = password_form.new_pwd.data
            cursor.execute(f"UPDATE user SET username = '{new_password}' WHERE id = '{user_id}")
            conn.commit()
        return redirect(url_for('home'))

    return render_template("profile.html", username_form=username_form, password_form=password_form, id=user_id, user_account=user_account, username=username, email=email)


@app.route("/pw")
def pw():
    with open("default.md", "r") as v:
        return Response(v.read(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)

