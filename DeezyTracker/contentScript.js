const SLACK_APP_URL = "https://deezy-status.vercel.app"; 
// Store the last sent emoji and status_text
let lastEmoji = '';
let lastStatusText = '';

function isFavorite(){
	const addToFavButton = document.querySelector('#page_player>div>div>div>div>[data-testid="add_to_favorite_button_off"]');
	const removeFromFavButton = document.querySelector('#page_player>div>div>div>div>[data-testid="add_to_favorite_button_on"]');
	if (addToFavButton) {
	  console.log('Not favorite');
	  return false;
	} else if (removeFromFavButton) {
	  console.log('Currently favorite');
	  return true;
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
  //Look for track title and artist name
  const title_tag = document.querySelector('[data-testid="item_title"]>a');
  if(title_tag){
	track_title=title_tag.innerHTML;
  } else {
	console.log('no track title');
  }
  const artist_tag = document.querySelector('[data-testid="item_subtitle"]>a');
  if(artist_tag){
	track_artist=artist_tag.innerHTML;
  } else {
	console.log('no track artist');
  }
  // Check status playing/paused
  const playButton = document.querySelector('#page_player [data-testid="play_button_play"]');
  const pauseButton = document.querySelector('#page_player [data-testid="play_button_pause"]');
  if (playButton) {
	console.log('Status: Paused');
	sendSlackStatus("", "");
  } else if (pauseButton) {
	const favorite_status = isFavorite();
	const emoji = favorite_status ? ":heart:" : ":musical_note:"; 
	let status_text = "listening to" + (favorite_status?" favorite: ":": ") + track_title + " - " + track_artist
	 if (status_text.length > 100) {
		//Remove parenthesis if there are any
		status_text = status_text.replace(/\([^)]*\)/g, '');
	 }
	sendSlackStatus(emoji, status_text);
  } else {
	console.log('Status: Unknown');
  }
}

function setupMutationObserver() {
  // Set up a mutation observer to detect DOM changes
  const playerBottom = document.querySelector('#page_player');
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

