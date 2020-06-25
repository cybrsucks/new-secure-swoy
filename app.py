from flask import Flask, render_template, redirect, url_for
from Forms import LoginForm, RegistrationForm, CheckoutForm


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


@app.route("/home", methods=['GET', 'POST'])
def home():
    test_list = [
        {"name": "Green Tea", "image": "raymond.jpg"},
        {"name": "Milk Tea", "image": "raymond.jpg"},
        {"name": "Green Tea", "image": "bayek.jpg"},
        {"name": "Milk Tea", "image": "raymond.jpg"},
        {"name": "Green Tea", "image": "bayek.jpg"},
        {"name": "Milk Tea", "image": "raymond.jpg"}
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
    return render_template("signup.html", form=form)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    return render_template("checkout.html")


@app.route("/delivery")
def delivery():
    return render_template("delivery.html")


if __name__ == "__main__":
    app.run(debug=True)
