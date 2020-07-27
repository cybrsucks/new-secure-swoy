from flask import Flask, render_template, redirect, url_for, request, Response
from wtforms import ValidationError
from Forms import *
from werkzeug.utils import secure_filename
import sqlite3
import re
from flask_jwt import jwt
import datetime
from functools import wraps
import xmltodict
import defusedxml.ElementTree
import xml.etree.ElementTree
import hashlib
import time
import logging
from werkzeug.serving import WSGIRequestHandler, _log


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


class MyRequestHandler(WSGIRequestHandler):
    # Just like WSGIRequestHandler, but without "- -"
    # def log(self, type, message, *args):
    #     _log(type, '%s [%s] %s\n' % (self.address_string(),
    #                                  self.log_date_time_string(),
    #                                  message % args))

    # Just like WSGIRequestHandler, but without "code"
    def log_request(self, code='-', size='-'):
        self.log('info', '"%s" %s', self.requestline, size)


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

    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM user WHERE admin = 1")
        admin = cursor.fetchall()
        noOfAdmin = len(admin)

        cursor.execute(f"SELECT * FROM user WHERE admin = 0")
        user = cursor.fetchall()
        noOfUser = len(user)

        cursor.execute(f"SELECT * FROM delivery_order WHERE delivered = 0")
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

    try:
        toppingsNo = len(productData["products"]["toppings"]["topping"])
        drinkNo = len(productData["products"]["drinks"]["drink"])
    except:
        error = "Warning: Error retrieving product data"

    return render_template("admin_dashboard.html", admin_title="Dashboard", user_account=user_account,
                           noOfAdmin=noOfAdmin, noOfUser=noOfUser, toppingsNo=toppingsNo, drinkNo=drinkNo,
                           noOfOrder=noOfOrder, error=error)


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
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
    id = drink_id
    user_id = request.args["id"]
    et = defusedxml.ElementTree.parse("static/products.xml")
    for drinkTag in list(et.getroot()[0].getchildren()):
        if id == drinkTag.attrib["id"]:
            et.getroot()[0].remove(drinkTag)
            et.write("static/products.xml")
    return redirect(url_for("admin_menu_drinks", id=user_id))


@app.route("/admin/menu_toppings")
@token_required
def admin_menu_toppings():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
def admin_menu_toppings_modify(topping_id):
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
def admin_menu_toppings_add():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
        # with sqlite3.connect("swoy.db") as conn:
        #     cursor = conn.cursor()
        #     cursor.execute(f"INSERT INTO drinks(name, price, thumbnail) "
        #                    f"VALUES('{name}', '{price}', '{filename}')")
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
def admin_menu_toppings_delete(topping_id):
    # with sqlite3.connect("swoy.db") as conn:
    #     cursor = conn.cursor()
    #     cursor.execute(f"DELETE FROM drinks WHERE drink_id='{drink_id}'")
    id = topping_id
    user_id = request.args["id"]
    et = defusedxml.ElementTree.parse("static/products.xml")
    for toppingTag in list(et.getroot()[1].getchildren()):
        if id == toppingTag.attrib["id"]:
            et.getroot()[1].remove(toppingTag)
            et.write("static/products.xml")

    return redirect(url_for("admin_menu_toppings", id=user_id))


@app.route("/admin/orders")
@token_required
def admin_orders():
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
        cursor.execute("SELECT * FROM delivery_order")
        result = cursor.fetchall()
        order_list = []
        for order in result:
            cursor.execute(f"SELECT username FROM user WHERE user_id='{order[1]}'")
            username = cursor.fetchone()[0]
            order_list.append([order[0], username, order[2], order[3], order[4], order[5], order[6]])
        order_list.reverse()

    return render_template("admin_orders.html", admin_title="Delivery Orders", order_list=order_list,
                           user_account=user_account)


@app.route("/admin/orders/clear")  # API
def clear_admin_orders():
    order_id = request.args["order_id"]
    user_id = request.args["id"]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE delivery_order SET delivered = 1 WHERE order_id = '{order_id}'")
        conn.commit()
    return redirect(url_for("admin_orders", id=user_id))


@app.route("/admin/orders_details")
def admin_order_details():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None

    order_id = request.args["order_id"]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM delivery_order WHERE order_id = '{order_id}'")
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
    return render_template("admin_feedbacks.html", admin_title="Customer Feedbacks")


@app.route("/admin/user_accounts")
@token_required
def admin_user_accounts():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None

    users = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE admin = 0")
        users = cursor.fetchall()

    userList = []
    for user in users:
        userList.append({"id": user[0], "username": user[1], "email": user[2]})

    return render_template("admin_user_accounts.html", admin_title="User Accounts", userList=userList,
                           user_account=user_account)


@app.route("/admin/admin_accounts", methods=["GET", "POST"])
@token_required
def admin_admin_accounts():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None

    users = None
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM user WHERE admin = 1")
        users = cursor.fetchall()

    userList = []
    for user in users:
        userList.append({"id": user[0], "username": user[1], "email": user[2]})

    return render_template("admin_admin_accounts.html", admin_title="Admin Accounts", userList=userList,
                           user_account=user_account)


@app.route("/admin/admin_accounts_delete", methods=["GET", "POST"])  # API
def admin_account_delete():
    userId = request.args["id"]
    id = request.args["user_id"]
    with sqlite3.connect("swoy.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM user WHERE user_id='{userId}'")
    localtime = time.asctime(time.localtime(time.time()))
    log_return = "Account deleted at [" + str(localtime) + "]."
    logging.info(log_return)

    return redirect(url_for("admin_admin_accounts", id=id))


@app.route("/admin/add_admin_account", methods=["GET", "POST"])
def add_admin_account():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
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
            security_qns = form.security_qns.data
            security_ans = form.security_ans.data
            admin = 1
            command = f"SELECT * FROM user WHERE email='{email}'"
            account_match = cursor.execute(command).fetchone()
            # print(f"Account: {account_match}")
            if account_match:
                error = "Email already exists"
            else:
                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                command = f"INSERT INTO user(username, email, password, security_qns, security_ans, admin) " \
                          f"VALUES ('{username}', '{email}', '{passwordDigest}', '{security_qns}', '{security_ans}', '{admin}')"
                cursor.execute(command)
                updated = cursor.execute("SELECT * FROM user").fetchall()
                print(f"Updated database : {updated}")
                conn.commit()
                return render_template("admin_add_admin_account.html", admin_title="Add Admin Account", form=form,
                                       user_account=user_account)
    return render_template("admin_add_admin_account.html", admin_title="Add Admin Account", form=form,
                           user_account=user_account)


@app.route("/admin/logs")
@token_required
def admin_logs():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
    except:
        user_account = None

    with open("werkzeug.txt") as f:
        logs = f.read().split("\n")[:-1]
        logs.reverse()
    return render_template("admin_logs.html", admin_title="History Logs", user_account=user_account, logs=logs)


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                command = f"INSERT INTO user(username, email, password, security_qns, security_ans, admin) " \
                          f"VALUES ('{username}', '{email}', '{passwordDigest}', '{security_qns}', '{security_ans}', '{admin}')"
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

            localtime = time.asctime(time.localtime(time.time()))
            log_return = "(" + str(account_match[1]) + ") -- login attempt at [" + str(localtime) + "]"
            logging.info(log_return)

            if account_match:
                passwordDigest = (hashlib.sha256(password.encode("utf-8"))).hexdigest()
                command = f"SELECT * FROM user WHERE email='{email}' and password='{passwordDigest}'"
                account_match = cursor.execute(command).fetchone()
                # print(f"Account: {account_match}")
                if account_match:
                    if account_match[6]:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        log_return = "Admin (" + str(account_match[1]) + ") successfully logged in at " + str(localtime)
                        logging.info(log_return)
                        return redirect(url_for("admin_dashboard", id=account_match[0], token=token.decode('utf-8')))
                    else:
                        token = jwt.encode({' user': account_match[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'])
                        log_return = "Customer (" + str(account_match[1]) + ") logged in at " + str(localtime)
                        logging.info(log_return)
                        return redirect(url_for("home", id=account_match[0], token=token.decode('utf-8')))
                else:
                    # Change to ambiguous message
                    error = "Password is incorrect."
            else:
                # Change to ambiguous message
                error = "Email does not exist."
    return render_template("login.html", form=form, error=error)


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
                    cursor.execute(f"SELECT * FROM comments WHERE drink_id = '{drink[0]}'")
                    comments = cursor.fetchall()
                    comment_list = []
                    for comment in comments:
                        cursor.execute(f"SELECT username FROM user WHERE user_id = '{comment[2]}'")
                        author = cursor.fetchone()[0]
                        comment_list.append({"content": comment[1], "author": author})

    for toppingTag in toppings:
        for i in toppings[toppingTag]:
            price = float(i['price'])
            formatted_price = f"{price:.2f}"
            topping_list.append((int(i["@id"]), i["description"], formatted_price, i["thumbnail"]))

    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
        user_id = request.args["user_id"]
        content = request.form["content"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO comments(content, user_id, drink_id) "
                           f"VALUES ('{content}', '{user_id}', '{drink_id}')")
            conn.commit()

        productData = xmltodict.parse(open("static/products.xml", "r").read())
        drinks = productData["products"]["drinks"]
        for drink in drinks:
            for i in drinks[drink]:
                if i["@id"] == drink_id:
                    drink_name = i["description"]

        return redirect(url_for("product", id=user_id, drink_name=drink_name, _anchor="comments"))
    except:
        return redirect(url_for("home"))


@app.route("/cart")
def cart():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
        cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
            cursor.execute(f"INSERT INTO cart VALUES ('{user_id}', '{cart_items}')")

    return render_template("cart.html", user_account=user_account, cart_item_count=cart_item_count,
                           cart_items=cart_items, total_price=total_price)


@app.route("/cart/add", methods=["GET", "POST"])  # API
def add_cart_item():
    try:
        drink_id = int(request.args["drink_id"])
        user_id = int(request.args["user_id"])
        toppings = [int(s) for s in request.form.getlist("toppings")]
        sugar = int(request.form["sugar"])
        quantity = int(request.form["quantity"])
        item_details = [drink_id, toppings, sugar, quantity]

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
            cart_items = cursor.fetchone()
            if cart_items:
                cart_items = eval(cart_items[0])
                cart_items.append(item_details)
                cursor.execute(f"UPDATE cart SET cart_items = '{cart_items}' WHERE user_id = '{user_id}'")
            else:
                cart_items = [item_details]
                cursor.execute(f"INSERT INTO cart VALUES ('{user_id}', '{cart_items}')")
            conn.commit()

        return redirect(url_for("home", id=user_id))
    except:
        return redirect(url_for("home"))


@app.route("/cart/remove", methods=["GET", "POST"])  # API
def remove_cart_item():
    try:
        user_id = int(request.args["user_id"])
        index_to_remove = int(request.args["item_num"]) - 1
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
            cart_items = cursor.fetchone()[0]
            cart_items = eval(cart_items)
            del cart_items[index_to_remove]
            cursor.execute(f"UPDATE cart SET cart_items = '{cart_items}' WHERE user_id = '{user_id}'")
            conn.commit()
        return redirect(url_for("cart", id=user_id))
    except:
        return redirect(url_for("home"))


@app.route("/checkout", methods=["GET", "POST"])
@token_required
def checkout():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
        cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
            cursor.execute(f"INSERT INTO cart VALUES ('{user_id}', '{cart_items}')")

    return render_template("checkout.html", form=form, user_account=user_account, cart_item_count=cart_item_count,
                           cart_items=cart_items, total_price=total_price)


@app.route("/checkout/add_order", methods=["GET", "POST"])
def add_order():
    try:
        user_id = request.args["id"]
        address = request.form["address"]
        delivery_date = request.form["delivery_date"]
        delivery_time = request.form["delivery_time"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
            cart_items = cursor.fetchone()[0]
            cursor.execute(f"INSERT INTO delivery_order(user_id, address, delivery_date, delivery_time, order_items)"
                           f"VALUES('{user_id}', '{address}', '{delivery_date}', '{delivery_time}', '{cart_items}')")
            cursor.execute(f"UPDATE cart SET cart_items = '[]' WHERE user_id = '{user_id}'")
            conn.commit()
        return redirect(url_for("home", id=user_id))
    except:
        return redirect(url_for("home"))
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
            localtime = time.asctime(time.localtime(time.time()))
            log_return = "(" + str(user_account[1]) + ") attempted to change password [FORGOT PASSWORD] at [" + str(
                localtime) + "]."
            logging.info(log_return)
            return redirect(url_for('forgot_password_change', email=email))
        else:
            # Change to ambiguous message
            error = "Wrong answer given."
    return render_template("forgot_password.html", form=form, security_qn=security_qn, email=email, error=error)


@app.route("/forgot_password/<email>/change", methods=["GET", "POST"])
def forgot_password_change(email):
    form = UpdatePasswordForm()
    if request.method == "POST" and form.validate_on_submit():
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE email = '{email}'")
            user_account = cursor.fetchone()

        localtime = time.asctime(time.localtime(time.time()))
        log_return = "(" + str(user_account[1]) + ") successfully changed password [FORGOT PASSWORD] at [" + str(
            localtime) + "]."
        logging.info(log_return)

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            new_password = form.new_pwd.data
            passwordDigest = (hashlib.sha256(new_password.encode("utf-8"))).hexdigest()
            cursor.execute(f"UPDATE user SET password = '{passwordDigest}' WHERE email = '{email}'")
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
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
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
def change_username():
    try:
        user_id = request.args["id"]
        new_username = request.form["new_username"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE user SET username = '{new_username}' WHERE user_id = '{user_id}'")
            conn.commit()
        return redirect(url_for("view_profile", id=user_id))
    except:
        return redirect(url_for("home"))


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    try:
        user_id = request.args["id"]
        current_pwd = request.form["current_pwd"]
        new_password = request.form["new_pwd"]
        confirm_password = request.form["confirm_new_pwd"]
        currentPasswordDigest = (hashlib.sha256(current_pwd.encode("utf-8"))).hexdigest()
        newPasswordDigest = (hashlib.sha256(new_password.encode("utf-8"))).hexdigest()

        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()

        localtime = time.asctime(time.localtime(time.time()))

        if new_password != confirm_password:
            return redirect(url_for("view_profile", id=user_id, password_error=1))
        else:
            with sqlite3.connect("swoy.db") as conn:
                cursor = conn.cursor()
                current_password_from_db = cursor.execute(f"SELECT password FROM user WHERE user_id = '{user_id}'")
                if current_password_from_db.fetchone()[0] != currentPasswordDigest:
                    log_return = "(" + str(
                        user_account[1]) + ") attempted to change password [EXISTING PASSWORD] at [" + str(
                        localtime) + "]."
                    logging.info(log_return)
                    return redirect(url_for("view_profile", id=user_id, password_error=1))

                else:
                    log_return = "(" + str(
                        user_account[1]) + ") successfully changed password [EXISTING PASSWORD] at [" + str(
                        localtime) + "]."
                    logging.info(log_return)

                cursor.execute(f"UPDATE user SET password = '{newPasswordDigest}' WHERE user_id = '{user_id}'")
                conn.commit()
            return redirect(url_for("view_profile", id=user_id))
    except:
        return redirect(url_for("home"))


@app.route("/order_history", methods=["GET", "POST"])
def order_history():
    try:
        user_id = request.args["id"]
        with sqlite3.connect("swoy.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE user_id = '{user_id}'")
            user_account = cursor.fetchone()
            cursor.execute(f"SELECT cart_items FROM cart WHERE user_id = '{user_id}'")
            cart_items = cursor.fetchone()
            if cart_items:
                cart_item_count = len(eval(cart_items[0]))
            else:
                cart_item_count = 0
    except:
        user_account = None
        cart_item_count = 0
    return render_template("order_history.html", user_account=user_account, cart_item_count=cart_item_count)


@app.route("/pw")
def pw():
    with open("default.md", "r") as v:
        return Response(v.read(), mimetype="text/plain")


if __name__ == "__main__":
    logging.basicConfig(filename='werkzeug.txt', level=logging.INFO)
    # all logs with INFO level and above is logged https://docs.python.org/3/howto/logging.html#when-to-use-logging

    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.WARNING)
    # werkzeug logs such as GET and POST from websites will no longer be logged
    # instead, the only log that is recorded is when debugger is active (WARNING) level

    app.run(debug=True, request_handler=MyRequestHandler)
    # app.run(debug=False, request_handler=MyRequestHandler)
