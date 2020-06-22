from flask import Flask, request, render_template, redirect


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("base.html")


if __name__ == "__main__":
    app.run(debug=True)
