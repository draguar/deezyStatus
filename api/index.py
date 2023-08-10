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
from flask_cors import CORS

# Environment variables
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET")
PROJECT_URI  = os.environ.get("PROJECT_URI")
KV_URL=os.environ.get("KV_URL")
KV_REST_API_URL=os.environ.get("KV_REST_API_URL")
KV_REST_API_TOKEN=os.environ.get("KV_REST_API_TOKEN")
KV_REST_API_READ_ONLY_TOKEN=os.environ.get("KV_REST_API_READ_ONLY_TOKEN")

# Initializes Flask app and slack app
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app, resources={r"/slackstatus": {"origins": "https://www.deezer.com"}})

slack_app = App(
    logger=app.logger,
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True
)
slack_request_handler = SlackRequestHandler(app=slack_app)

# --------------------------------------------------------
# Slack app installation OAuth workflow
# --------------------------------------------------------
@app.route('/slackoauth')
def slack_oauth():
    code = request.args.get('code')
    # Prepare the client credentials for HTTP Basic authentication
    credentials = f"{SLACK_CLIENT_ID}:{SLACK_CLIENT_SECRET}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()
    # Exchange the code for an access token using Basic authentication
    response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        headers={"Authorization": f"Basic {base64_credentials}"},
        data={"code": code}
    )
    if response.status_code == 200:
        data = response.json()
        user_id = data["authed_user"]["id"]
        user_token = data["authed_user"]["access_token"]
        bot_token = data["access_token"]
        # Store user information
        user_info = {"id": user_id, "user_token": user_token, "bot_token":bot_token, "uuid":str(uuid.uuid4())}
        store_user_info(user_info)
        # Redirect the user to a thank you page or their profile, etc.
        return "Authentification successful, you can close this tab and return to slack"
    else:
        # Handle the error case
        return "Authentification failed"
        
# --------------------------------------------------------
# KV store manipulation
# --------------------------------------------------------
def store_user_info(user_info):
    # Construct the URL to the KV store
    kv_store_url = f"{KV_REST_API_URL}/set/{user_info['id']}"
    # Set up the headers with the API token
    headers = {
        "Authorization": f"Bearer {KV_REST_API_TOKEN}",
        "Content-Type": "application/json",
    }
    # Make the POST request to store the data in the KV store
    response = requests.post(kv_store_url, headers=headers, json=user_info)
    if response.status_code == 200:
        app.logger.info("User ID and user info stored successfully.")
    else:
        app.logger.error("Error storing user info: " + str(user_info))
        app.logger.error(response.text) 
    # same with uuid as key
    # Construct the URL to the KV store
    kv_opposite_url = f"{KV_REST_API_URL}/set/{user_info['uuid']}"
    # Make the POST request to store the data in the KV store
    response = requests.post(kv_opposite_url, headers=headers, json=user_info))
    if response.status_code == 200:
        app.logger.info("User uuid and user info stored successfully.")
    else:
        app.logger.error("Error storing user info: " + str(user_info))
        app.logger.error(response.text)
    update_home_view(user_info['id'],user_info)
             
def get_user_info(id_or_uuid):
    # Construct the URL to the KV store with the user ID as the key
    kv_store_url = f"{KV_REST_API_URL}/get/{id_or_uuid}"
    # Set up the headers with the read-only token
    headers = {
        "Authorization": f"Bearer {KV_REST_API_READ_ONLY_TOKEN}",
    }
    # Make the GET request to retrieve the data from the KV store
    response = requests.get(kv_store_url, headers=headers)
    if response.status_code == 200:
        # Parse the response JSON to get the user token
        app.logger.info(response.text)
        user_info = response.json().get('result')
        return user_info
    else:
        app.logger.error("Error retrieving user value: status" + str(response.status_code))
        app.logger.error(response.text)
        return None

# --------------------------------------------------------
# Slack event management
# --------------------------------------------------------
@app.route('/slack/events', methods=['POST'])
def slack_events():
    if "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})
    else:
        slack_request_handler.handle(request)
    return ""
# --------------------------------------------------------
# Slack app Home tab
# --------------------------------------------------------
@slack_app.event("app_home_opened")
def handle_app_home_opened(event, client, logger):
    user_id = event["user"]
    update_home_view (user_id)

def update_home_view (user_id, user_info=None):
    if user_info is None:
        user_info = get_user_info(user_id)
    if user_info is None:
        # The user has not completed the OAuth workflow
        app.logger.info("Un-authentified user : " + str(user_id))
        view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "To start using DeezyStatus, please click on the button below\n\n[![Add to slack](https://platform.slack-edge.com/img/add_to_slack.png)](https://slack.com/oauth/v2/authorize?client_id=442927849974.5669273267394&scope=users.profile:read&user_scope=users.profile:write)"
                        }
                    }
                ]
            }
        slack_client = slack_app.client    
    else:
        # The user is OAuth-identified
        app.logger.info("authentified user : " + str(user_id))
        view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "To use DeezyStatus, install firefox add-on [DeezyTracker](https://addons.mozilla.org/en-US/firefox/addon/deezytracker/). Once you set DeezyTracker up and play music in Deezer, it will send current track information to DeezyStatus in order to update you slack status.\n\nTo set up DeezyTracker, please copy paste your following user token: "+ user_info["uuid"]
                    }
                }
            ]
        }
        slack_client = WebClient(token = user_info["bot_token"])
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
            app.logger.error("Failed to publish the app home view : "+response.text)
    except Exception as e:
        app.logger.error(f"Error publishing the app home view: {str(e)}")

# --------------------------------------------------------
# Slack status update
# --------------------------------------------------------
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
    slack_info=get_user_info(user_token)
    if slack_info is None:
        app.logger.error("Failed to retrieve user info")
        return jsonify({"error": "Failed to retrieve user info"}), 400
    update_slack_status(emoji, status_text, slack_info)
    # Return the response
    response_data = {
        'message': 'Status update sent successfully',
    }
    return jsonify(response_data)
    
def update_slack_status(emoji, status_text, slack_info):   
    slack_client = WebClient(token=slack_info["user_token"])
    try:
        response = slack_client.users_profile_set(
            user=slack_info["id"],
            profile={
                "status_text": status_text,
                "status_emoji": emoji
            }
        )
        if response["ok"]:
            print(f"Slack status updated for user {slack_info['id']}.")
        else:
            print(f"Failed to update Slack status for user {slack_info['id']}.")
    except slack_sdk.errors.SlackApiError as e:
        print(f"Error updating Slack status: {e}")

@app.route('/')
def hello_world():
    return "This is DeezyStatus"