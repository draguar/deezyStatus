const SLACK_APP_URL = "https://deezy-status.vercel.app"; 

function sendSlackStatus(emoji, status_text) {
	console.log(emoji+ " "+ status_text);
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
        console.log('Status: Playing');
		sendSlackStatus(":musical_note:", "listening to: "+ track + " - " + artist);
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

