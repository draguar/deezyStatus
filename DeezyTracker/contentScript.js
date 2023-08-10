const SLACK_APP_URL = "https://deezy-status.vercel.app"; 
// Store the last sent emoji and status_text
let lastEmoji = '';
let lastStatusText = '';

function isFavorite(){
	const trackActions = document.querySelector(".track-actions");
	if (trackActions) {
		const addToFavButton = trackActions.querySelector("svg[data-testid='HeartIcon']");
		const removeFromFavButton = trackActions.querySelector("svg[data-testid='HeartFillIcon']");
		if (addToFavButton) {
		  console.log('Not favorite');
		  return false;
		} else if (removeFromFavButton) {
		  console.log('Currently favorite');
		  return true;
		}
    } else {
		console.log('no trackActions');
	}
	throw new Error('Cannot detect if favorite or not');
}

function sendSlackStatus(emoji, status_text) {
	console.log(emoji+ " "+ status_text);
	
	// Check if the current emoji and status_text are the same as the last sent ones
    if (emoji === lastEmoji && status_text === lastStatusText) {
        console.log('Data is the same as the previous request. Skipping Slack API call.');
        return;
    }

	chrome.storage.sync.get('slackToken', function (data) {
		// Create a data object with the parameters to send
		const slack_post_data = {
		  emoji: emoji,
		  status_text: status_text,
		  user_token: data.slackToken
		};
		// Create the request options
	    const requestOptions = {
		  method: 'POST',
		  headers: {
		    'Content-Type': 'application/json',
		  },
		  body: JSON.stringify(slack_post_data),
	    };
		
		// Update the last sent emoji and status_text
		lastEmoji = emoji;
		lastStatusText = status_text;
		// Send the POST request using fetch()
		console.log("posting" + JSON.stringify(slack_post_data) + " to "+ `${SLACK_APP_URL}/slackstatus`);
	    fetch(`${SLACK_APP_URL}/slackstatus`, requestOptions)
		  .then((response) => {
		    if (!response.ok) {
			  throw new Error('Network response was not ok');
		    }
		    // Handle the successful response if needed
		    console.log('Status update sent successfully');

		  })
		  .catch((error) => {
		    // Handle any errors that occurred during the fetch
		    console.error('Error sending status update:', error.message);
		  });
	});
}


// Helper function to log the current track information
function logCurrentTrack() {
  const trackContainer = document.querySelector('.track-container');
  if (trackContainer) {
    const marqueeContent = trackContainer.querySelector('.marquee-content');
    if (marqueeContent) {
      const trackInfo = marqueeContent.textContent.trim();
      const [track, artist] = trackInfo.split(' · ');
      console.log('Current Track:', track);
      console.log('Artist:', artist);
	  
	  const playButton = document.querySelector('.svg-icon-group-btn > svg[data-testid="PlayIcon"]');
	  const pauseButton = document.querySelector('.svg-icon-group-btn > svg[data-testid="PauseIcon"]');

	  if (playButton) {
        console.log('Status: Paused');
		sendSlackStatus("", "");
      } else if (pauseButton) {
		const favorite_status = isFavorite();
		const emoji = favorite_status ? ":heart:" : ":musical_note:"; 
		let status_text = "listening to" + (favorite_status?" favorite: ":": ") + track + " - " + artist
		 if (status_text.length > 100) {
			//Remove parenthesis if there are any
			status_text = status_text.replace(/\([^)]*\)/g, '');
		 }
 		sendSlackStatus(emoji, status_text);
      } else {
        console.log('Status: Unknown');
      }
    } else {
		console.log('no marquee content');
	}
  } else {
	  console.log('no track container');
  }
}

function setupMutationObserver() {
  // Set up a mutation observer to detect DOM changes
  const playerBottom = document.querySelector('.player-bottom');
  if (playerBottom) {
    const observer = new MutationObserver(() => {
      // Call getCurrentTrack whenever a DOM change is observed in player-bottom
      logCurrentTrack();
    });

    const observerConfig = { childList: true, subtree: true };
    observer.observe(playerBottom, observerConfig);
	console.log("observer set up");
	logCurrentTrack();
  } else {
	  console.log('no player');
	   setTimeout(() => {
		setupMutationObserver();
	  }, 5000); 
	  console.log("timeout set up");
  }
}
  
setupMutationObserver();
window.addEventListener("beforeunload", function () {
	sendSlackStatus("","");
});

