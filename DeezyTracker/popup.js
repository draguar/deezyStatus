function updateTokenParagraph() {
	  // Get the current Slack token from Chrome storage
	  chrome.storage.sync.get('slackToken', function (data) {
		const currentToken = data.slackToken;
		const tokenParagraph = document.getElementById('currentToken');
		
		if (currentToken) {
		  tokenParagraph.textContent = 'Currently identified with DeezyStatus through token: '+ currentToken;
		} else {
		  tokenParagraph.textContent = 'No DeezyStatus token registered.';
		}
	  });
	}
	
document.addEventListener('DOMContentLoaded', function () {
  // Update the paragraph on popup load
  updateTokenParagraph();
  
  document.getElementById("saveTokenButton").addEventListener("click", function () {
      const slackToken = document.getElementById("slackTokenInput").value.trim();
      chrome.storage.sync.set({ slackToken: slackToken }, function () {
        console.log("Slack user token saved:", slackToken);
		updateTokenParagraph();
      });
    });
});
  
 