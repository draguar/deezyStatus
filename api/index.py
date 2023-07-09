from flask import Flask

deezer_app = Flask(__name__)

@deezer_app.route('/')
def home():
    return 'Hello, World!'

@deezer_app.route('/about')
def about():
    return 'About'
