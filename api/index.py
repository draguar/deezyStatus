
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
KV_URL=os.environ.get("KV_URL")
KV_REST_API_URL=os.environ.get("KV_REST_API_URL")
KV_REST_API_TOKEN=os.environ.get("KV_REST_API_TOKEN")
KV_REST_API_READ_ONLY_TOKEN=os.environ.get("KV_REST_API_READ_ONLY_TOKEN")
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

def store_user_id_token_pair(user_id, user_token):
    # Construct the URL to the KV store
    kv_store_url = f"{KV_REST_API_URL}/set/{user_id}/{user_token}"

    # Set up the headers with the API token
    headers = {
        "Authorization": f"Bearer {KV_REST_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # Make the POST request to store the data in the KV store
    response = requests.post(kv_store_url, headers=headers)

    if response.status_code == 200:
        app.logger.info("User ID and token pair stored successfully.")
    else:
        app.logger.error("Error storing user ID and token pair: " + str(response.status_code))
        app.logger.error(response.text)
        
    # same in opposite direction
    # Construct the URL to the KV store
    kv_opposite_url = f"{KV_REST_API_URL}/set/{user_token}/{user_id}"
    # Make the POST request to store the data in the KV store
    response = requests.post(kv_opposite_url, headers=headers)

    if response.status_code == 200:
        app.logger.info("User token and ID pair stored successfully.")
    else:
        app.logger.error("Error storing user ID and token pair: " + str(response.status_code))
        app.logger.error(response.text)
        
        
        
def get_user_token_or_user_id(user_key):

    # Construct the URL to the KV store with the user ID as the key
    kv_store_url = f"{KV_REST_API_URL}/get/{user_key}"

    # Set up the headers with the read-only token
    headers = {
        "Authorization": f"Bearer {KV_REST_API_READ_ONLY_TOKEN}",
    }

    # Make the GET request to retrieve the data from the KV store
    response = requests.get(kv_store_url, headers=headers)

    if response.status_code == 200:
        # Parse the response JSON to get the user token
        app.logger.info(response.text)
        user_value = response.json().get('result')
        
        return user_value
    else:
        app.logger.error("Error retrieving user value:" + str(response.status_code))
        app.logger.error(response.text)
        return None
        
# def get_user_id_by_user_token(user_token):

    # # Construct the URL to the KV store
    # kv_store_url = f"{KV_REST_API_URL}/v1/namespaces/{KV_URL}/values"

    # # Set up the headers with the read-only token
    # headers = {
        # "Authorization": f"Bearer {KV_REST_API_READ_ONLY_TOKEN}",
    # }

    # # Make the GET request to retrieve all data from the KV store
    # response = requests.get(kv_store_url, headers=headers)

    # if response.status_code == 200:
        # # Parse the response JSON to get all the keys and values in the KV store
        # kv_data = response.json().get('data', [])

        # # Loop through the data to find the user ID associated with the provided user token
        # for item in kv_data:
            # if item['value'] == user_token:
                # user_id = item['key']
                # return user_id

        # # If user token not found in the KV store, return None
        # return None
    # else:
        # app.logger.error("Error retrieving data from KV store:" + str(response.status_code))
        # app.logger.error(response.text)
        # return None        
        

# def create_database():
    # conn = sqlite3.connect('slack_tokens.db')
    # cursor = conn.cursor()
    # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS users (
            # user_id TEXT PRIMARY KEY,
            # token TEXT NOT NULL
        # )
    # ''')
    # conn.commit()
    # conn.close()

# def get_user_token(user_id):
    # # Retrieve the user token from the database based on the token
    # conn = sqlite3.connect('slack_tokens.db')
    # cursor = conn.cursor()
    # cursor.execute('SELECT token FROM users WHERE user_id = ?', (user_id,))
    # result = cursor.fetchone()
    # conn.close()

    # if result:
        # user_token = result[0]
        # return user_token
    # else:
        # return False
        
# def get_user_id(user_token):
    # # Retrieve the user token from the database based on the token
    # conn = sqlite3.connect('slack_tokens.db')
    # cursor = conn.cursor()
    # cursor.execute('SELECT user_id FROM users WHERE token = ?', (user_token,))
    # result = cursor.fetchone()
    # conn.close()

    # if result:
        # user_id = result[0]
        # return user_id
    # else:
        # return False

@app.route('/slackstatus', methods=['POST'])
def parse_slack_status_update_request():
    # Retrieve data from the JSON request body
    data = request.get_json()
    app.logger.info(str(data))
    if "emoji" not in data or "status_text" not in data or "user_token" not in data:
        app.logger.error("Missing required data")
        return jsonify({"error": "Missing required data"}), 400
    emoji = data.get("emoji")
    status_text = data.get("status_text")
    user_token = data.get("user_token")
    # get user ID from token
    slack_id=get_user_token_or_user_id(user_token)
    if slack_id is None:
        app.logger.error("Failed to decrypt user ID")
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
    except slack_sdk.errors.SlackApiError as e:
        print(f"Error updating Slack status: {e}")

@app.route('/')
def hello_world():
    app.logger.info("Request received at /")
    # try:
        # create_database()
        # app.logger.info("database created")
    # except Exception as e:
        # app.logger.error(e)
    # conn = sqlite3.connect('slack_tokens.db')
    
    # Construct the URL to the KV store
    kv_store_url = f"{KV_REST_API_URL}/keys/*"

    # Set up the headers with the read-only token
    headers = {
        "Authorization": f"Bearer {KV_REST_API_READ_ONLY_TOKEN}",
    }
    app.logger.info("Send request at " + kv_store_url)


    # Make the GET request to retrieve all data from the KV store
    response = requests.get(kv_store_url, headers=headers)
    app.logger.info(response.text)

    if response.status_code == 200:
        # Parse the response JSON to get all the keys and values in the KV store
        kv_data = response.json().get('data', [])
        return str(kv_data)
    return "response status: "+str(response.status_code)



@slack_app.event("app_home_opened")
def handle_app_home_opened(event, client, logger):
    user_id = event["user"]
    update_home_view (user_id, event)

@app.route('/redis')
def redis_test():
    get_user_token_or_user_id("test")
    return "ok"


@app.route('/slack/events', methods=['POST'])
def slack_events():
    if "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})
    else:
        slack_request_handler.handle(request)
    return ""

def update_home_view (user_id, event=None):
    user_token=get_user_token_or_user_id(user_id)
    if user_token is None:
        app.logger.info("generate a new user token for user : " + str(user_id))
        cipher = Fernet(ENCRYPTION_KEY)
        encrypted_user_id = cipher.encrypt(user_id.encode())
        user_token = encrypted_user_id.decode()
        # Store the user ID and token in the database
        # conn = sqlite3.connect('slack_tokens.db')
        # cursor = conn.cursor()
        # cursor.execute('INSERT INTO users (user_id, user_token) VALUES (?, ?)', (user_id, user_token))
        # conn.commit()
        # conn.close()
        store_user_id_token_pair(user_id, user_token)
    
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


