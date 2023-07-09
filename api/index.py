
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, redirect, request, jsonify
import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
import logging

# Get the root logger
logger = logging.getLogger()

DEEZER_CLIENT_ID = os.environ.get("DEEZER_CLIENT_ID")
DEEZER_CLIENT_SECRET = os.environ.get("DEEZER_CLIENT_SECRET")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
PROJECT_URI  = os.environ.get("PROJECT_URI")
deezer_access_tokens = {}

# Initializes your app with your bot token and signing secret
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))


slack_request_handler = SlackRequestHandler(app=slack_app)

deezer_app = Flask(__name__)

@deezer_app.route('/')
def hello_world():
    return "hey"

@deezer_app.route("/deezyRedirect")
def callback():
    # Retrieve the authorization code from the query parameters
    authorization_code = request.args.get("code")
    user_id = request.args.get("slack_id")

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

@deezer_app.route('/test')
def hello():
    return "hello"


@slack_app.event("app_home_opened")
def handle_app_home_opened(event, client, logger):
    user_id = event["user"]
    update_home_view (user_id, event)




@deezer_app.route('/slack/events', methods=['POST'])
def slack_events():
    if "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})
    else:
        slack_request_handler.handle(request)
    return ""

def update_home_view (user_id, event=None):
    authorization_url = f"https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_CLIENT_ID}&perms=listening_history,offline_access&redirect_uri={PROJECT_URI}/deezyRedirect?slack_id={user_id}"
    if user_id in deezer_access_tokens:
        logger.info("User already associated with a deezer acces_token")
        message_text = "Deezer is connected"
        button_text = "Connect to another Deezer account"
    else:
        logger.info("User already associated with a deezer acces_token")
        message_text = "Welcome to DeezyStatus. To start syncing your status with the tracks you listen to on Deezer, click on 'Connect to Deezer' below."
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
        if event is None:
            # Get the current app home view ID
            event = slack_client.views_open(
                trigger_id="dummy_trigger_id",
                view={"type": "home"}
            )

        if "view" in event:
            # Update the existing view on the Home tab
            logger.info("Updating the existing view on the Home tab")
            response = slack_client.views_update(
                user_id=user_id,
                view_id=event["view"]["id"],
                view=view
            )
        else:
            # Publish the initial view on the Home tab
            logger.info("Publishing the view on the Home tab")
            response = slack_client.views_publish(
                user_id=user_id,
                view=view
            )
        if response["ok"]:
            logger.info("Successfully published the app home view")
        else:
            logger.error("Failed to publish the app home view")
    except Exception as e:
        logger.error(f"Error publishing the app home view: {str(e)}")


# Start your Bolt app using Socket Mode
if __name__ == "__main__":
    # Start the SocketModeHandler in the main thread
    handler = SocketModeHandler(slack_app, app_token=os.environ.get("SLACK_APP_TOKEN"))
    handler.start()






