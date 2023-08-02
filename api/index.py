
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, request, jsonify
import os
import requests, json
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
import logging
import sys
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from flask_cors import CORS
import sqlite3




DEEZER_CLIENT_ID = os.environ.get("DEEZER_CLIENT_ID")
DEEZER_CLIENT_SECRET = os.environ.get("DEEZER_CLIENT_SECRET")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
PROJECT_URI  = os.environ.get("PROJECT_URI")
CRONJOB_API_KEY = os.environ.get("CRONJOB_API_KEY")
CRONJOB_ID = os.environ.get("CRONJOB_ID")
ENCRYPTION_KEY=os.environ.get("ENCRYPTION_KEY")
DEEZER_API_BASE_URL = "https://api.deezer.com/user/me/history"
CRONJOB_API_BASE_URL = 'https://api.cron-job.org'

deezer_access_tokens = {}
uuid_to_slackID={}

# Initializes your app with your bot token and signing secret
slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True
)
slack_client = WebClient(SLACK_BOT_TOKEN)
slack_request_handler = SlackRequestHandler(app=slack_app)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app, resources={r"/slackstatus": {"origins": "https://www.deezer.com"}})

def create_database():
    conn = sqlite3.connect('slack_tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_user_token(user_id):
    # Retrieve the user token from the database based on the token
    conn = sqlite3.connect('slack_tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        user_token = result[0]
        return user_token
    else:
        return False
        
def get_user_id(user_token):
    # Retrieve the user token from the database based on the token
    conn = sqlite3.connect('slack_tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE token = ?', (user_token,))
    result = cursor.fetchone()
    conn.close()

    if result:
        user_id = result[0]
        return user_id
    else:
        return False

@app.route('/slackstatus', methods=['POST'])
def parse_slack_status_update_request():
    # Retrieve data from the JSON request body
    data = request.get_json()
    emoji = data.get("emoji")
    status_text = data.get("status_text")
    user_token = data.get("user_token")

    if not all([emoji, status_text, user_token]):
        return jsonify({"error": "Missing required data"}), 400
        
    # get user ID from token
    slack_id=get_user_id(user_token)
    if not slack_id:
        return jsonify({"error": "Failed to decrypt user ID"}), 400
    update_slack_status(emoji, status_text, slack_id)
    # Return the response (make sure to include the CORS header in the response)
    response_data = {
        'message': 'Status update sent successfully',
        # Add any other data you want to return to the client
    }

    return jsonify(response_data)
    
def update_slack_status(emoji, status_text, slack_id):   
    slack_client = WebClient(token=SLACK_USER_TOKEN)
    try:
        response = slack_client.users_profile_set(
            user=slack_id,
            profile={
                "status_text": status_text,
                "status_emoji": emoji
            }
        )
        if response["ok"]:
            print(f"Slack status updated for user {slack_id}.")
        else:
            print(f"Failed to update Slack status for user {slack_id}.")
    except SlackApiError as e:
        print(f"Error updating Slack status: {e}")

@app.route('/')
def hello_world():
    app.logger.info("Request received at /")
    try:
        create_database()
    except Exception as e:
        app.logger.error(e)
    conn = sqlite3.connect('slack_tokens.db')
    return str(conn)



@slack_app.event("app_home_opened")
def handle_app_home_opened(event, client, logger):
    user_id = event["user"]
    update_home_view (user_id, event)

@app.route('/slack/events', methods=['POST'])
def slack_events():
    if "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})
    else:
        slack_request_handler.handle(request)
    return ""

def update_home_view (user_id, event=None):
    user_token=get_user_token(user_id)
    if not user_token:
        app.logger.info("generate a new user token for user : " + str(user_id))
        cipher = Fernet(ENCRYPTION_KEY)
        encrypted_user_id = cipher.encrypt(user_id.encode())
        user_token = encrypted_user_id.decode()
        # Store the user ID and token in the database
        conn = sqlite3.connect('slack_tokens.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (user_id, user_token) VALUES (?, ?)', (user_id, user_token))
        conn.commit()
        conn.close()
    
    view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "To use DeezyStatus, install chrome app DeezyTracker. Once you set DeezyTracker up and play music in Deezer, it will send current track information to DeezyStatus in order to update you slack status.\n\nTo set up DeezyTracker, please copy paste your following user token: "+ user_token
                    }
                }
            ]
        }
    try:
        # Publish the initial view on the Home tab
        app.logger.info("Publishing the view on the Home tab")
        response = slack_client.views_publish(
            user_id=user_id,
            view=view
        )
        if response["ok"]:
            app.logger.info("Successfully published the app home view")
        else:
            app.logger.error("Failed to publish the app home view")
    except Exception as e:
        app.logger.error(f"Error publishing the app home view: {str(e)}")


