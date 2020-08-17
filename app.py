from flask import Flask, render_template, redirect, url_for, request, Response, session
from werkzeug.serving import WSGIRequestHandler, _log
from werkzeug.utils import secure_filename
from wtforms import ValidationError
from functools import wraps
from flask_jwt import jwt
from Forms import *
import defusedxml.ElementTree
import xml.etree.ElementTree
import datetime
import xmltodict
import sqlite3
import hashlib
import logging
import PyOTP
import time
import re


email_otp = None
timeout = None
forgot_pw_email = None
incorrect_password_tries = 0


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        #token = request.args.get('token')

        token = session["token"]
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


# class MyRequestHandler(WSGIRequestHandler):
#     # Just like WSGIRequestHandler, but without "- -"
#     # def log(self, type, message, *args):
#     #     _log(type, '%s [%s] %s\n' % (self.address_string(),
#     #                                  self.log_date_time_string(),
#     #                                  message % args))
#
#     # Just like WSGIRequestHandler, but without "code"
#     def log_request(self, code='-', size='-'):
#         self.log('info', '"%s" %s', self.requestline, size)

formatter = logging.Formatter('%(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


@app.route("/admin", methods=["GET", "POST"])
@token_required
def admin_dashboard():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user WHERE admin = 1")
        admin = cursor.fetchall()
        noOfAdmin = len(admin)

        cursor.execute("SELECT * FROM user WHERE admin = 0")
        user = cursor.fetchall()
        noOfUser = len(user)

        cursor.execute("SELECT * FROM delivery_order WHERE delivered = 0")
        order = cursor.fetchall()
        noOfOrder = len(order)

    productData = None
    toppingsNo = 0
    drinkNo = 0
    error = ""
    try:
        productData = xmltodict.parse(open("static/products.xml", "r").read())
    except:
        error = "Warning: Error retrieving product data"
        admin_logger.error("[" + str(localtime) + "] Products are not being properly displayed on the website.")


    try:
        toppingsNo = len(productData["products"]["toppings"]["topping"])
        drinkNo = len(productData["products"]["drinks"]["drink"])
    except:
        error = "Warning: Error retrieving product data"

    return render_template("admin_dashboard.html", admin_title="Dashboard", user_account=user_account,
                           noOfAdmin=noOfAdmin, noOfUser=noOfUser, toppingsNo=toppingsNo, drinkNo=drinkNo,
                           noOfOrder=noOfOrder, error=error)


@app.route("/admin/otp", methods=["GET", "POST"])
@token_required
def authenticate_otp():
    global email_otp
    global timeout
    if session["unauthenticated_user"][4] != 1:
        session["user"] = session["unauthenticated_user"]
        session["unauthenticated_user"] = None
        return redirect(url_for("home"))
    try:
        user_id = session["unauthenticated_user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = OTPForm()

    if request.method == "GET":
        email_otp = PyOTP.send_otp(user_account[2])
        timeout = time.time() + 60 * 3  # current_time + 3 minutes
        localtime = time.asctime(time.localtime(time.time()))
        # log_return = "[" + str(localtime) + "] An OTP request has been sent to admin inbox"
        # logging.info(log_return)
        admin_logger.info("[" + str(localtime) + "] An OTP request has been sent to admin inbox")

    if request.method == "POST" and form.validate_on_submit():
        email = user_account[2]
        check = str(form.otp.data)

        if time.time() > timeout or check != email_otp:
            print("OTP INVALID OR EXPIRED")
        elif check == email_otp and time.time() < timeout:
            print("Success!")

            session["user"] = session["unauthenticated_user"]
            session["unauthenticated_user"] = None
            email_otp = None
            timeout = None
            localtime = time.asctime(time.localtime(time.time()))
            # log_return = "[" + str(localtime) + "] Admin " + user_account[1] + " has been logged in successfully"
            # logging.info(log_return)
            admin_logger.info("[" + str(localtime) + "] Admin " + user_account[1] + " has been logged in successfully")

            return redirect(url_for('admin_dashboard'))

    return render_template("admin_OTP_authentication.html", form=form)


@app.route("/admin/<user_id>")
@token_required
def admin_own_account(user_id):
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    return render_template("admin_own_account.html", admin_title="Your Account")


@app.route("/admin/menu_drinks")
@token_required
def admin_menu_drinks():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = None
    try:
        drinks = productData["products"]["drinks"]
    except:
        return render_template("admin_menu_drinks.html", admin_title="Menu Items - Drinks", drink_list=[],
                                user_account=user_account, error="Warning: Error retrieving products")
    drink_list = []
    for drink in drinks:
        for i in drinks[drink]:
            price = float(i['price'])
            formatted_price = f"{price:.2f}"
            drink_list.append(
                {"id": i["@id"], "name": i["description"], "price": formatted_price, "image": i["thumbnail"]})

    return render_template("admin_menu_drinks.html", admin_title="Menu Items - Drinks", drink_list=drink_list,
                           user_account=user_account, error="")


@app.route("/admin/menu_drinks/<drink_id>", methods=["GET", "POST"])
@token_required
def admin_menu_drinks_modify(drink_id):
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = ModifyDrinkForm()
    if request.method == "GET":
        productData = xmltodict.parse(open("static/products.xml", "r").read())
        drinks = productData["products"]["drinks"]
        for drink in drinks:
            for i in drinks[drink]:
                if i["@id"] == drink_id:
                    form.name.data = i["description"]
                    form.price.data = float(i["price"])

    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None
        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        id = int(drink_id)
        et = defusedxml.ElementTree.parse("static/products.xml")
        drinkTag = et.getroot()[0].getchildren()[id - 1]
        for element in list(drinkTag):
            if element.tag == "thumbnail":
                if filename != None:
                    drinkTag.remove(element)
            else:
                drinkTag.remove(element)

        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id - 1], "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id - 1], "price")
        priceTag.text = str(price)
        if filename != None:
            thumbnailTag = xml.etree.ElementTree.SubElement(et.getroot()[0][id - 1], "thumbnail")
            thumbnailTag.text = filename
        et.write("static/products.xml")

    return render_template("admin_menu_drinks_modify.html",
                           admin_title=f"Menu Items - Modify Drinks - {form.name.data}", form=form, drink_id=drink_id,
                           user_account=user_account)


@app.route("/admin/menu_drinks/add_drink", methods=["GET", "POST"])
@token_required
def admin_menu_drinks_add():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = AddDrinkForm()
    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None
        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        et = defusedxml.ElementTree.parse("static/products.xml")
        last = list(et.getroot()[0].getchildren())[-1]
        id = int(last.attrib["id"]) + 1
        newTag = xml.etree.ElementTree.SubElement(et.getroot()[0], 'drink')
        newTag.attrib["id"] = str(id)
        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(newTag, "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(newTag, "price")
        priceTag.text = str(price)
        thumbnailTag = xml.etree.ElementTree.SubElement(newTag, "thumbnail")
        thumbnailTag.text = filename
        et.write("static/products.xml")
    return render_template("admin_menu_drinks_add.html", admin_title=f"Menu Items - Add Drink", form=form,
                           user_account=user_account)


@app.route("/admin/menu_drinks/delete/<drink_id>", methods=["POST"])  # API
@token_required
def admin_menu_drinks_delete(drink_id):
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    id = drink_id
    user_id = session["user"][0]
    et = defusedxml.ElementTree.parse("static/products.xml")
    for drinkTag in list(et.getroot()[0].getchildren()):
        if id == drinkTag.attrib["id"]:
            et.getroot()[0].remove(drinkTag)
            et.write("static/products.xml")
    return redirect(url_for("admin_menu_drinks"))


@app.route("/admin/menu_toppings")
@token_required
def admin_menu_toppings():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    productData = xmltodict.parse(open("static/products.xml", "r").read())

    toppings = None
    try:
        toppings = productData["products"]["toppings"]
    except:
        return render_template("admin_menu_toppings.html", admin_title="Menu Items - Toppings",
                               topping_list=[],
                               user_account=user_account, error="Warning: Error retrieving products")

    topping_list = []
    for topping in toppings:
        for i in toppings[topping]:
            topping_list.append(
                {"id": i["@id"], "name": i["description"], "price": i["price"], "image": i["thumbnail"]})

    return render_template("admin_menu_toppings.html", admin_title="Menu Items - Toppings", topping_list=topping_list,
                           user_account=user_account, error="")


@app.route("/admin/menu_toppings/<topping_id>", methods=["GET", "POST"])
@token_required
def admin_menu_toppings_modify(topping_id):
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = ModifyToppingForm()
    if request.method == "GET":
        productData = xmltodict.parse(open("static/products.xml", "r").read())
        toppings = productData["products"]["toppings"]
        for topping in toppings:
            for i in toppings[topping]:
                if i["@id"] == topping_id:
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

        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        id = int(topping_id)
        et = defusedxml.ElementTree.parse("static/products.xml")
        toppingTag = et.getroot()[1].getchildren()[id - 1]
        for element in list(toppingTag):
            if element.tag == "thumbnail":
                if filename != None:
                    toppingTag.remove(element)
            else:
                toppingTag.remove(element)

        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(et.getroot()[1][id - 1], "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(et.getroot()[1][id - 1], "price")
        priceTag.text = str(price)
        if filename != None:
            thumbnailTag = xml.etree.ElementTree.SubElement(et.getroot()[1][id - 1], "thumbnail")
            thumbnailTag.text = filename
        et.write("static/products.xml")

    return render_template("admin_menu_toppings_modify.html",
                           admin_title=f"Menu Items - Modify Toppings - {form.name.data}", form=form,
                           topping_id=topping_id, user_account=user_account)


@app.route("/admin/menu_toppings/add_topping", methods=["GET", "POST"])
@token_required
def admin_menu_toppings_add():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = AddToppingForm()
    if request.method == "POST" and form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        try:
            filename = secure_filename(form.thumbnail.data.filename)
        except:
            filename = None

        if filename != None:
            form.thumbnail.data.save("static/" + filename)

        et = defusedxml.ElementTree.parse("static/products.xml")
        last = list(et.getroot()[1].getchildren())[-1]
        id = int(last.attrib["id"]) + 1
        newTag = xml.etree.ElementTree.SubElement(et.getroot()[1], 'topping')
        newTag.attrib["id"] = str(id)
        et.write("static/products.xml")
        descriptionTag = xml.etree.ElementTree.SubElement(newTag, "description")
        descriptionTag.text = name
        priceTag = xml.etree.ElementTree.SubElement(newTag, "price")
        priceTag.text = str(price)
        thumbnailTag = xml.etree.ElementTree.SubElement(newTag, "thumbnail")
        thumbnailTag.text = filename
        et.write("static/products.xml")
    return render_template("admin_menu_toppings_add.html", admin_title=f"Menu Items - Add Topping", form=form,
                           user_account=user_account)


@app.route("/admin/menu_toppings/delete/<topping_id>", methods=["POST"])  # API
@token_required
def admin_menu_toppings_delete(topping_id):
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    id = topping_id
    user_id = session["user"][0]
    et = defusedxml.ElementTree.parse("static/products.xml")
    for toppingTag in list(et.getroot()[1].getchildren()):
        if id == toppingTag.attrib["id"]:
            et.getroot()[1].remove(toppingTag)
            et.write("static/products.xml")

    return redirect(url_for("admin_menu_toppings"))


@app.route("/admin/orders")
@token_required
def admin_orders():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM delivery_order")
        result = cursor.fetchall()
        order_list = []
        for order in result:
            cursor.execute("SELECT username FROM user WHERE user_id = ?", (order[1],))
            username = cursor.fetchone()[0]
            order_list.append([order[0], username, order[2], order[3], order[4], order[5], order[6]])
        order_list.reverse()

    return render_template("admin_orders.html", admin_title="Delivery Orders", order_list=order_list,
                           user_account=user_account)


@app.route("/admin/orders/clear")  # API
@token_required
def clear_admin_orders():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    order_id = request.args["order_id"]
    user_id = session["user"][0]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE delivery_order SET delivered = 1 WHERE order_id = ?", (order_id,))
        conn.commit()
    return redirect(url_for("admin_orders"))


@app.route("/admin/orders_details")
@token_required
def admin_order_details():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    order_id = request.args["order_id"]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM delivery_order WHERE order_id = ?", (order_id,))
        result = cursor.fetchone()

        order_items = []
        total_price = 0
        for item in eval(result[5]):
            formatted_item = []

            productData = xmltodict.parse(open("static/products.xml", "r").read())
            drinks = None
            toppings = None
            try:
                drinks = productData["products"]["drinks"]
                toppings = productData["products"]["toppings"]
            except:
                return render_template("admin_order_details.html", admin_title="Order details", order_items=order_items,
                                       total_price=total_price, order_id=order_id, user_account=user_account, error="Warning: Error retrieving products")
            for drink in drinks:
                for i in drinks[drink]:
                    if i["@id"] == str(item[0]):
                        formatted_item.append(i["description"])
                        price = float(i["price"])

            topping_list = []
            for topping in toppings:
                for i in toppings[topping]:
                    if i["@id"] in [str(s) for s in item[1]]:
                        topping_list.append(i["description"])
                        price += float(i["price"])
            formatted_item.append(topping_list)

            formatted_item.append(item[2])
            formatted_item.append(item[3])

            price *= item[3]
            total_price += price
            formatted_item.append(f"{price:.2f}")
            order_items.append(formatted_item)

        total_price = f"{total_price:.2f}"

    return render_template("admin_order_details.html", admin_title="Order details", order_items=order_items,
                           total_price=total_price, order_id=order_id, user_account=user_account)


@app.route("/admin/feedbacks")
@token_required
def admin_feedbacks():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    return render_template("admin_feedbacks.html", admin_title="Customer Feedbacks")


@app.route("/admin/user_accounts")
@token_required
def admin_user_accounts():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    users = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE admin = 0")
        users = cursor.fetchall()

    userList = []
    for user in users:
        userList.append({"id": user[0], "username": user[1], "email": user[2]})

    return render_template("admin_user_accounts.html", admin_title="User Accounts", userList=userList,
                           user_account=user_account)


@app.route("/admin/admin_accounts", methods=["GET", "POST"])
@token_required
def admin_admin_accounts():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    users = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE admin = 1")
        users = cursor.fetchall()

    userList = []
    for user in users:
        userList.append({"id": user[0], "username": user[1], "email": user[2]})

    return render_template("admin_admin_accounts.html", admin_title="Admin Accounts", userList=userList,
                           user_account=user_account)


@app.route("/admin/admin_accounts_delete", methods=["GET", "POST"])  # API
@token_required
def admin_account_delete():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    userId = request.args["id"]
    id = session["user"][0]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE user_id= ?", (userId,))
        account_deleted = cursor.fetchone()
        cursor.execute("DELETE FROM user WHERE user_id = ?", (userId,))

    localtime = time.asctime(time.localtime(time.time()))
    # log_return = "[" + str(localtime) + "] " + session["user"][1] + " has deleted admin account " + account_deleted[1]
    # logging.warning(log_return)
    admin_logger.info("[" + str(localtime) + "] " + session["user"][1] + " has deleted admin account " + "[" + account_deleted[1] + "]")

    return redirect(url_for("admin_admin_accounts"))


@app.route("/admin/add_admin_account", methods=["GET", "POST"])
@token_required
def add_admin_account():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    form = RegistrationForm()
    error = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            username = form.username.data
            email = form.email.data
            password = form.password.data

            error_present = True
            while error_present:
                if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", password):
                    error_password = "Your password must be at least 8 characters, contain at least 1 symbol (@, $, !, %, *, #, ?, &), at least 1 uppercase and at least 1 lowercase"
                    while error_password:
                        return render_template("admin_add_admin_account.html", form=form, error=error,error_password=error_password, admin_title="Add Admin Account", user_account=user_account)
                else:
                    error_password = False
                    break

            admin = 1
            account_match = cursor.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                error = "Email already exists"
            else:
                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                cursor.execute(f"INSERT INTO user(username, email, password, admin, locked) "
                               f"VALUES (?, ?, ?, ?, ?)", (username, email, passwordDigest, admin, 0))
                updated = cursor.execute("SELECT * FROM user").fetchall()
                conn.commit()

                localtime = time.asctime(time.localtime(time.time()))
                # log_return = "[" + str(localtime) + "] " + user_account[1] + " created an admin account " + "[" + username + "] "
                # logging.warning(log_return)
                admin_logger.warning("[" + str(localtime) + "] " + user_account[1] + " created an admin account " + "[" + username + "] ")

                users = None
                with sqlite3.connect("swoy.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM user WHERE admin = 1")
                    users = cursor.fetchall()

                userList = []
                for user in users:
                    userList.append({"id": user[0], "username": user[1], "email": user[2]})

                return render_template("admin_admin_accounts.html", admin_title="Admin Accounts", userList=userList, user_account=user_account)
    return render_template("admin_add_admin_account.html", admin_title="Add Admin Account", form=form, user_account=user_account, error=error)


@app.route("/admin/admin_logs")
@token_required
def admin_logs():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    with open("admin_logs.log") as f:
        logs = f.read().split("\n")[:-1]
        logs.reverse()
    return render_template("admin_logs.html", admin_title="History Logs", user_account=user_account, logs=logs)

@app.route("/admin/user_logs")
@token_required
def user_logs():
    if session["user"][4] != 1:
        return redirect(url_for("error_404"))
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    with open("user_logs.log") as f:
        logs = f.read().split("\n")[:-1]
        logs.reverse()
    return render_template("user_logs.html", admin_title="History Logs", user_account=user_account, logs=logs)


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    global forgot_pw_email
    forgot_pw_email = None
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0


    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = None
    try:
        drinks = productData["products"]["drinks"]
    except:
        return render_template("home.html", drink_list=[], user_account=user_account, search=None,
                               cart_item_count=cart_item_count, error="Warning: Error retrieving products")

    drink_list = []
    for drink in drinks:
        for i in drinks[drink]:
            price = float(i['price'])
            formatted_price = f"{price:.2f}"
            drink_list.append(
                {"id": i["@id"], "name": i["description"], "price": formatted_price, "image": i["thumbnail"]})

    try:
        search = request.args["search"]
        filtered_drink_list = []
        for drink in drink_list:
            if search.lower() in drink["name"].lower():
                filtered_drink_list.append(drink)
        drink_list = filtered_drink_list
    except:
        search = None

    return render_template("home.html", drink_list=drink_list, user_account=user_account, search=search,
                           cart_item_count=cart_item_count)


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
            locked = 0

            if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", password):
                error_password = "Your password must be at least 8 characters, contain at least 1 symbol (@, $, !, %, *, #, ?, &), at least 1 uppercase and at least 1 lowercase"
                return render_template("signup.html", form=form, error=error, error_password=error_password)
            else:
                error_password = None
            admin = 0
            account_match = cursor.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                error = "Email already exists"
            else:
                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                cursor.execute("INSERT INTO user(username, email, password, admin, locked) "
                               "VALUES (?, ?, ?, ?, ?)", (username, email, passwordDigest, admin, locked))
                updated = cursor.execute("SELECT * FROM user").fetchall()
                print(f"Updated database : {updated}")
                conn.commit()

                localtime = time.asctime(time.localtime(time.time()))
                # log_return = "[" + str(localtime) + "] New Acount created for " + user_account[1] + " with user_id " + user_account[0]
                # logging.info(log_return)
                admin_logger.info("[" + str(localtime) + "] New Acount created for " + updated[1] + " with user_id " + updated[0])

                return render_template("login.html", form=LoginForm())
    return render_template("signup.html", form=form, error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    global forgot_pw_email
    global incorrect_password_tries
    forgot_pw_email = None
    form = LoginForm()
    error = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            email = form.email.data
            password = form.password.data
            cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
            account_match = cursor.fetchone()
            locked = account_match[5]
            username = account_match[1]

            if account_match:
                localtime = time.asctime(time.localtime(time.time()))
                # log_return = "[" + str(localtime) + "] " + str(account_match[1]) + " attempted login"
                # logging.info(log_return)
                user_logger.info("[" + str(localtime) + "] " + str(account_match[1]) + " attempted login")

                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                # print(passwordDigest)
                account_match = cursor.execute("SELECT * FROM user WHERE email = ? and password = ?", (email, passwordDigest)).fetchone()
                # print(f"Account: {account_match}")
                if account_match:
                    if account_match[4]:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        # log_return = "[" + str(localtime) + "] Admin (" + str(account_match[1]) + ") is required to enter OTP"
                        # logging.info(log_return)
                        admin_logger.info("[" + str(localtime) + "] Admin (" + str(account_match[1]) + ") is required to enter OTP")
                        session["token"] = token
                        session["unauthenticated_user"] = account_match
                        session['user'] = None
                        return redirect(url_for("authenticate_otp"))
                    else:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        # log_return = "[" + str(localtime) + "] Customer (" + str(account_match[1]) + ") successfully logged in"
                        # logging.info(log_return)
                        user_logger.info("[" + str(localtime) + "] Customer (" + str(account_match[1]) + ") successfully logged in")
                        session["token"] = token
                        session["user"] = account_match
                        return redirect(url_for("home"))
                else:
                    # error = "Password is incorrect."
                    if incorrect_password_tries < 4 and locked == 0:
                        incorrect_password_tries += 1
                        error = "Incorrect email or password"
                    else:
                        if incorrect_password_tries >= 4:
                            cursor.execute("UPDATE user SET locked = 1 WHERE email = ?", (email, ))
                            conn.commit()
                        error = "Exceeded incorrect password attempts. Please contact website adminstrator."
                        # log_return = "[" + str(localtime) + "] Customer (" + str(username) + ") has exceeded the password attempt limits and has been locked."
                        # logging.info(log_return)
                        user_logger.info("[" + str(localtime) + "] Customer (" + str(username) + ") has exceeded the password attempt limits and has been locked.")
            else:
                error = "Incorrect email or password"
                # error = "Email does not exist."
    return render_template("login.html", form=form, error=error)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session["token"] = None
    session["user"] = None
    return redirect(url_for("home"))


@app.route("/product/<drink_name>")
def product(drink_name):
    comment_list = []
    drink = None
    productData = xmltodict.parse(open("static/products.xml", "r").read())
    drinks = productData["products"]["drinks"]
    toppings = productData["products"]["toppings"]
    topping_list = []

    for drinkTag in drinks:
        for i in drinks[drinkTag]:
            if i["description"] == drink_name:
                drink = (int(i["@id"]), i["description"], float(i["price"]), i["thumbnail"])

                with sqlite3.connect("swoy.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM comments WHERE drink_id = ?", (drink[0],))
                    comments = cursor.fetchall()
                    comment_list = []
                    for comment in comments:
                        cursor.execute("SELECT username FROM user WHERE user_id = ?", (comment[2],))
                        author = cursor.fetchone()[0]
                        comment_list.append({"content": comment[1], "author": author})

    for toppingTag in toppings:
        for i in toppings[toppingTag]:
            price = float(i['price'])
            formatted_price = f"{price:.2f}"
            topping_list.append((int(i["@id"]), i["description"], formatted_price, i["thumbnail"]))

    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0
    return render_template("product.html", drink=drink, comment_list=comment_list, topping_list=topping_list,
                           user_account=user_account, cart_item_count=cart_item_count)


@app.route("/product/update_drink_comments", methods=["GET", "POST"])  # API
@token_required
def update_comment():
    try:
        drink_id = request.args["drink_id"]
        user_id = session["user"][0]
        content = request.form["content"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO comments(content, user_id, drink_id) VALUES (?, ?, ?)", (content, user_id, drink_id))
            conn.commit()

        productData = xmltodict.parse(open("static/products.xml", "r").read())
        drinks = productData["products"]["drinks"]
        for drink in drinks:
            for i in drinks[drink]:
                if i["@id"] == drink_id:
                    drink_name = i["description"]

        return redirect(url_for("product", drink_name=drink_name, _anchor="comments"))
    except:
        return redirect(url_for("home"))


@app.route("/cart")
@token_required
def cart():
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0

    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchone()
        if cart_items:
            cart_items = eval(cart_items[0])  # [[0]: drink_id, [1]: [topping_id], [2]: sugar_level, [3]: quantity]
            formatted_cart_items = []
            total_price = 0
            for item in cart_items:
                formatted_item = []

                productData = xmltodict.parse(open("static/products.xml", "r").read())
                drinks = productData["products"]["drinks"]
                for drink in drinks:
                    for i in drinks[drink]:
                        if i["@id"] == str(item[0]):
                            formatted_item.append(i["description"])
                            price = float(i["price"])

                topping_list = []
                toppings = productData["products"]["toppings"]
                for topping in toppings:
                    for i in toppings[topping]:
                        if i["@id"] in [str(s) for s in item[1]]:
                            topping_list.append(i["description"])
                            price += float(i["price"])
                formatted_item.append(topping_list)

                formatted_item.append(item[2])
                formatted_item.append(item[3])

                price *= item[3]
                total_price += price
                formatted_item.append(f"{price:.2f}")
                formatted_cart_items.append(formatted_item)

            total_price = f"{total_price:.2f}"
            cart_items = formatted_cart_items

        else:
            cart_items = []
            total_price = 0
            cursor.execute("INSERT INTO cart VALUES (?, ?)", (user_id, str(cart_items)))

    return render_template("cart.html", user_account=user_account, cart_item_count=cart_item_count,
                           cart_items=cart_items, total_price=total_price)


@app.route("/cart/add", methods=["GET", "POST"])  # API
@token_required
def add_cart_item():
    try:
        drink_id = int(request.args["drink_id"])
        user_id = int(session["user"][0])
        toppings = [int(s) for s in request.form.getlist("toppings")]
        sugar = int(request.form["sugar"])
        quantity = int(request.form["quantity"])
        item_details = [drink_id, toppings, sugar, quantity]

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            print(cart_items)
            if cart_items:
                cart_items = eval(cart_items[0])
                cart_items.append(item_details)
                cursor.execute("UPDATE cart SET cart_items = ? WHERE user_id = ?", (str(cart_items), user_id))
            else:
                cart_items = [item_details]
                cursor.execute("INSERT INTO cart VALUES (?, ?)", (user_id, str(cart_items)))
            conn.commit()

        return redirect(url_for("home"))
    except:
        return redirect(url_for("home"))


@app.route("/cart/remove", methods=["GET", "POST"])  # API
@token_required
def remove_cart_item():
    try:
        user_id = int(session["user"][0])
        index_to_remove = int(request.args["item_num"]) - 1
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()[0]
            cart_items = eval(cart_items)
            del cart_items[index_to_remove]
            cursor.execute("UPDATE cart SET cart_items = ? WHERE user_id = ?", (str(cart_items), user_id))
            conn.commit()
        return redirect(url_for("cart"))
    except:
        return redirect(url_for("home"))


@app.route("/checkout", methods=["GET", "POST"])
@token_required
def checkout():
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0
    form = CheckoutForm()

    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
        cart_items = cursor.fetchone()
        if cart_items:
            cart_items = eval(cart_items[0])  # [[0]: drink_id, [1]: [topping_id], [2]: sugar_level, [3]: quantity]
            formatted_cart_items = []
            total_price = 0
            for item in cart_items:
                formatted_item = []

                productData = xmltodict.parse(open("static/products.xml", "r").read())
                drinks = productData["products"]["drinks"]
                for drink in drinks:
                    for i in drinks[drink]:
                        if i["@id"] == str(item[0]):
                            formatted_item.append(i["description"])
                            price = float(i["price"])

                topping_list = []
                toppings = productData["products"]["toppings"]
                for topping in toppings:
                    for i in toppings[topping]:
                        if i["@id"] in [str(s) for s in item[1]]:
                            topping_list.append(i["description"])
                            price += float(i["price"])
                formatted_item.append(topping_list)

                formatted_item.append(item[2])
                formatted_item.append(item[3])

                price *= item[3]
                total_price += price
                formatted_item.append(f"{price:.2f}")
                formatted_cart_items.append(formatted_item)

            total_price = f"{total_price:.2f}"
            cart_items = formatted_cart_items

        else:
            cart_items = []
            total_price = 0
            cursor.execute("INSERT INTO cart VALUES (?, ?)", (user_id, str(cart_items)))

    return render_template("checkout.html", form=form, user_account=user_account, cart_item_count=cart_item_count,
                           cart_items=cart_items, total_price=total_price)


@app.route("/checkout/add_order", methods=["GET", "POST"])
@token_required
def add_order():
    try:
        user_id = session["user"][0]
        address = request.form["address"]
        delivery_date = request.form["delivery_date"]
        delivery_time = request.form["delivery_time"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()[0]
            cursor.execute("INSERT INTO delivery_order(user_id, address, delivery_date, delivery_time, order_items) "
                           "VALUES(?, ?, ?, ?, ?)", (user_id, address, delivery_date, delivery_time, str(cart_items)))
            cursor.execute("UPDATE cart SET cart_items = '[]' WHERE user_id = ?", (user_id,))
            conn.commit()
        return redirect(url_for("home"))
    except:
        return redirect(url_for("home"))
    return render_template("checkout.html", form=form)


@app.route("/delivery")
@token_required
def delivery():
    form = DeliveryForm()
    return render_template("delivery.html", form=form)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password_email_form():
    global forgot_pw_email
    form = ForgotPasswordEmailForm()
    error = None
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            forgot_pw_email = form.email.data
            cursor = conn.cursor()
            account_match = cursor.execute("SELECT * FROM user WHERE email = ?", (forgot_pw_email,)).fetchone()
            if account_match:
                # print("here")
                return redirect(url_for('forgot_pwd_otp'))
            else:
                error = "Email does not exist"
    return render_template("forgot_password(1).html", form=form, error=error)


@app.route("/forgot_password/otp", methods=["GET", "POST"])
def forgot_pwd_otp():
    global email_otp
    global timeout

    form = OTPForm()

    if not forgot_pw_email:
        return redirect(url_for("home"))

    try:
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE email = ?", (forgot_pw_email,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    if request.method == "GET":
        email_otp = PyOTP.send_otp(forgot_pw_email)
        timeout = time.time() + 60 * 3  # current_time + 3 minutes
        localtime = time.asctime(time.localtime(time.time()))
        # log_return = "[" + str(localtime) + "] OTP verification needed to change password for " + user_account[1] + " [FORGOT PASSWORD]"
        # logging.info(log_return)
        user_logger.info("[" + str(localtime) + "] OTP verification needed to change password for " + user_account[1] + " [FORGOT PASSWORD]")

    if request.method == "POST" and form.validate_on_submit():
        check = str(form.otp.data)

        if time.time() > timeout or check != email_otp:
            print("OTP INVALID OR EXPIRED")
        elif check == email_otp and time.time() < timeout:
            print("Success!")
            email_otp = None
            timeout = None

            return redirect(url_for('forgot_password_change'))

    return render_template("forgot_password(2).html", form=form)


@app.route("/forgot_password/change", methods=["GET", "POST"])
def forgot_password_change():
    global forgot_pw_email
    if not forgot_pw_email:
        return redirect(url_for("home"))

    form = UpdatePasswordForm()
    error = None

    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE email = ?", (forgot_pw_email,))
            user_account = cursor.fetchone()

        localtime = time.asctime(time.localtime(time.time()))
        # log_return = "[" + str(localtime) + "] " + str(user_account[1]) + " attempted to change password [EXISTING PASSWORD]"
        # logging.info(log_return)
        user_logger.info("[" + str(localtime) + "] " + str(user_account[1]) + " attempted to change password [EXISTING PASSWORD]")

        new_password = form.new_pwd.data
        error_present = True

        while error_present:
            if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", new_password):
                error_password = "Your password must be at least 8 characters, contain at least 1 symbol (@, $, !, %, *, #, ?, &), at least 1 uppercase and at least 1 lowercase"
                while error_password:
                    return render_template("forgot_password(3).html", form=form, error=error, error_password=error_password)
            else:
                error_password = False
                break

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            passwordDigest = (hashlib.sha256(new_password.encode("utf-8"))).hexdigest()
            cursor.execute("UPDATE user SET password = ? WHERE email = ?", (passwordDigest, forgot_pw_email))
            conn.commit()

        forgot_pw_email = None
        return redirect(url_for('login'))

    return render_template("forgot_password(3).html", form=form)


@app.route("/profile", methods=["GET", "POST"])
@token_required
def view_profile():
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
            username = user_account[1]
            email = user_account[2]
    except:
        user_account = None
        cart_item_count = 0

    try:
        password_error = request.args["password_error"]
    except:
        password_error = None

    username_form = ChangeLoggedInUserUsernameForm()
    password_form = ChangeLoggedInUserPasswordForm()
    return render_template("profile.html", username_form=username_form, password_error=password_error,
                           password_form=password_form, user_account=user_account, cart_item_count=cart_item_count)


@app.route("/change_username", methods=["GET", "POST"])
@token_required
def change_username():
    try:
        user_id = session["user"][0]
        new_username = request.form["new_username"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET username = ? WHERE user_id = ?", (new_username, user_id))
            conn.commit()
        return redirect(url_for("view_profile"))
    except:
        return redirect(url_for("home"))


@app.route("/change_password", methods=["GET", "POST"])
@token_required
def change_password():
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
    except:
        user_account = None

    try:
        current_pwd = request.form["current_pwd"]
        new_password = request.form["new_pwd"]

        error_present = True
        while error_present:
            if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", new_password):
                error_password = "Your password must be at least 8 characters, contain at least 1 symbol (@, $, !, %, *, #, ?, &), at least 1 uppercase and at least 1 lowercase"
                while error_password:
                    return render_template("profile.html", username_form=username_form, password_error=password_error,
                           password_form=password_form, user_account=user_account, cart_item_count=cart_item_count)
            else:
                error_password = False
                break

        confirm_password = request.form["confirm_new_pwd"]
        currentPasswordDigest = (hashlib.sha256(current_pwd.encode("utf-8"))).hexdigest()
        newPasswordDigest = (hashlib.sha256(new_password.encode("utf-8"))).hexdigest()

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()

        localtime = time.asctime(time.localtime(time.time()))

        if new_password != confirm_password:
            return redirect(url_for("view_profile", password_error=1))
        else:
            with sqlite3.connect("swoy.db") as conn:
                cursor = conn.cursor()
                current_password_from_db = cursor.execute("SELECT password FROM user WHERE user_id = ?", (user_id,))
                if current_password_from_db.fetchone()[0] != currentPasswordDigest:
                    # log_return = "[" + str(localtime) + "] "+ str(user_account[1]) + ") attempted to change password [EXISTING PASSWORD]"
                    # logging.info(log_return)
                    user_logger.info("[" + str(localtime) + "] "+ str(user_account[1]) + ") attempted to change password [EXISTING PASSWORD]")
                    return redirect(url_for("view_profile", password_error=1))

                else:
                    # log_return = "[" + str(localtime) + "] " + str(user_account[1]) + ") successfully changed password [EXISTING PASSWORD]"
                    # logging.info(log_return)
                    user_logger.info("[" + str(localtime) + "] " + str(user_account[1]) + ") successfully changed password [EXISTING PASSWORD]")

                cursor.execute("UPDATE user SET password = ? WHERE user_id = ?", (newPasswordDigest, user_id))
                conn.commit()
            return redirect(url_for("view_profile"))
    except:
        return redirect(url_for("home"))


@app.route("/order_history", methods=["GET", "POST"])
@token_required
def order_history():
    try:
        user_id = session["user"][0]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            user_account = cursor.fetchone()
            cursor.execute("SELECT cart_items FROM cart WHERE user_id = ?", (user_id,))
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0
    return render_template("order_history.html", user_account=user_account, cart_item_count=cart_item_count)


@app.errorhandler(404)
@app.route("/404")
def error_page(e):
    return render_template("error_404.html"), 404


@app.route("/er404")
def error_404():
    return render_template("error_404.html")


if __name__ == "__main__":
    user_logger = setup_logger('user_logs', 'user_logs.log')
    admin_logger = setup_logger('admin_logs', 'admin_logs.log')
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)

    # logging.basicConfig(filename='werkzeug.txt', level=logging.INFO)
    # # all logs with INFO level and above is logged https://docs.python.org/3/howto/logging.html#when-to-use-logging
    # logger = logging.getLogger('werkzeug')
    # logger.setLevel(logging.WARNING)
    # werkzeug logs such as GET and POST from websites will no longer be logged
    # instead, the only log that is recorded is when debugger is active (WARNING) level
    # logging.basicConfig(filename='admin_logs_only.txt', level=logging.INFO)
    # logger_admin = logging.getLogger('werkzeug')
    # logger_admin.setLevel(logging.WARNING)

    app.run(debug=True)



