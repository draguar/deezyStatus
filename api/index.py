
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, request, jsonify



deezer_app = Flask(__name__)

@deezer_app.route('/')
def hello_world():
    return "hey"







