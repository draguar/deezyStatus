
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


DEEZER_CLIENT_ID = os.environ.get("DEEZER_CLIENT_ID")
DEEZER_CLIENT_SECRET = os.environ.get("DEEZER_CLIENT_SECRET")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
PROJECT_URI  = os.environ.get("PROJECT_URI")
CRONJOB_API_KEY = os.environ.get("CRONJOB_API_KEY")
CRONJOB_ID = os.environ.get("CRONJOB_ID")
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

@app.route('/cronjob')
def fetch_current_track():
    return_value = ""
    if len(deezer_access_tokens) == 0:
        update_conjob(enabled=False)
        return "no user connected, stopped cronjob"
    for slack_id, deezer_token in deezer_access_tokens.items():
        try:
            response = requests.get(DEEZER_API_BASE_URL + "?access_token=" + deezer_token)
            response_data = response.json()
            if "data" in response_data:
                current_track = response_data["data"][0]
                seconds_ago = (datetime.now() - datetime.fromtimestamp(current_track['timestamp'])).seconds
                # if track was started more than 5 minutes ago, we reset default status, otherwise we update it
                if seconds_ago > 5*60:
                    update_slack_status("","",slack_id)
                    return_value += "user " + slack_id + " isn't listening to deezer since : " + seconds_ago +"s \n"
                else:
                    status_text = f"listening to: {current_track['title']} - {current_track['artist']['name']}"
                    update_slack_status(":musical_note:" , status_text, slack_id)
                    return_value += "user " + slack_id +" "+ status_text +"\n"


        except requests.exceptions.RequestException as e:
            print(f"Error getting track information: {e}")
            return "Error getting track information."
    return return_value
    
@app.route('/stopcronjob')
def stop_cronjob():
    return update_conjob(False)
    
@app.route('/startcronjob')
def start_cronjob():
    return update_conjob(True)

    
def update_conjob(enabled):
    url = f"{CRONJOB_API_BASE_URL}/jobs/{CRONJOB_ID}"
    headers = {
        "Authorization": f"Bearer {CRONJOB_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"job": {"enabled": enabled}}
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        return "updated cronjob"
    else : 
        return "error updating cronjob"
    
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
    headers = {
        'Authorization': 'Bearer '+ CRONJOB_API_KEY
    }
    result = requests.get(CRONJOB_API_BASE_URL + '/jobs', headers=headers)
    return result.json()

@app.route("/deezyRedirect")
def callback():
    # Retrieve the authorization code from the query parameters
    
    authorization_code = request.args.get("code")
    state_uuid=request.args.get("state")
    app.logger.info(f"got deezer redirect with uuid: {state_uuid}. dict is {str(uuid_to_slackID)}")

    user_id = uuid_to_slackID[uuid.UUID(state_uuid)]

    # Exchange the authorization code for an access token
    response = requests.get(
        "https://connect.deezer.com/oauth/access_token.php",
        params={
            "app_id": DEEZER_CLIENT_ID,
            "secret": DEEZER_CLIENT_SECRET,
            "code": authorization_code,
            "output": "json"
        }
    )
    # Extract the access token from the response
    data = response.json()
    access_token = data.get("access_token")
    deezer_access_tokens[user_id] = access_token
    update_home_view (user_id)

    return """<html>
            <body>
                <h1>Authorization Successful</h1>
                <p>You can close this tab now.</p>
            </body>
            </html>"""

@app.route('/test')
def hello():
    return "hello"


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
    slackId_to_uuid = {v: k for k, v in uuid_to_slackID.items()}
    if user_id in slackId_to_uuid:
        state_uuid=slackId_to_uuid[user_id]
    else:
        state_uuid=uuid.uuid1()
        uuid_to_slackID[state_uuid]=user_id  
    app.logger.info("making deezer request with uuid: %s correspondinf to user_id %s same as %s",state_uuid, uuid_to_slackID[state_uuid], user_id)
    app.logger.info("troll")
    authorization_url = f"https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_CLIENT_ID}&perms=listening_history,offline_access&redirect_uri={PROJECT_URI}deezyRedirect&state={state_uuid}"
    if user_id in deezer_access_tokens:
        app.logger.info("User already associated with a deezer acces_token")
        message_text = "Deezer is connected"
        button_text = "Connect to another Deezer account"
    else:
        app.logger.info("User not associated with a deezer acces_token")
        message_text = "Welcome to DeezyStatus ;). To start syncing your status with the tracks you listen to on Deezer, click on 'Connect to Deezer' below."
        button_text = "Connect to Deezer"
    view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_text
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": button_text
                            },
                            "url": authorization_url
                        }
                    ]
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


