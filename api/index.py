
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, request, jsonify
import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
import logging


deezer_app = Flask(__name__)

@deezer_app.route('/')
def hello_world():
    logging.info("Request received at /")
    return "hey"







