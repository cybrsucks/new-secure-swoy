from flask import Flask, render_template, redirect, url_for
from Forms import LoginForm, RegistrationForm, CheckoutForm, DeliveryForm


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
    print(form.email.data, form.password.data, form.username.data)
    return render_template("signup.html", form=form)


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
