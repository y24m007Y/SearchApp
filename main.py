from flask import Flask, Blueprint
import views


app = Flask(__name__)
app.secret_key = 'your_secret_key'
print("main.py")
app.register_blueprint(views.bp)


if __name__ == "__main__":
    app.run(debug=False)
