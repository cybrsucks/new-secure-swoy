from flask import Flask, request, render_template, redirect


app = Flask(__name__)


@app.route("/")
def home():
    test_list = [
        {"name": "Green Tea", "image": "bayek.jpg"},
        {"name": "Puck you", "image": "puck you.png"},
        {"name": "Green Tea", "image": "bayek.jpg"},
        {"name": "Puck you", "image": "puck you.png"},
        {"name": "Green Tea", "image": "bayek.jpg"},
        {"name": "Puck you", "image": "puck you.png"}
    ]

    return render_template("home.html", test_list=test_list)


if __name__ == "__main__":
    app.run(debug=True)
