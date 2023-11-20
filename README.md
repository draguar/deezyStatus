# DeezyStatus - Sync Your Slack Status with Deezer

<img src="https://avatars.slack-edge.com/2023-08-01/5681931981089_dc2b11a4ed20fd33ef7c_512.png" alt="DeezyStatus Logo" width="100">

[DeezyStatus](https://deezy-status.vercel.app/) is a slack app that lets users automatically synchronize their Slack status with the track they're listening to on Deezer!

## Installation

If you wish to use DeezyStatus, you can find installation and set up instructions on [DeezyStatus official page](https://deezy-status.vercel.app/).
   
## How it Works

DeezyStatus is dependant on the firefox addon [DeezyTracker](https://addons.mozilla.org/en-US/firefox/addon/deezytracker/), which code you will find in `DeezyTracker` directory.

DeezyTracker contains a content script checking for what the user is listening to on Deezer, and sending the information to DeezyStatus Slack app.

The code for the slack app is available in the `api` directory. After the insallation OAuth2 workflow, the app gives the user a token to submit in DeezyTracker in order to identify them. When DeezyTracker sends currently listened track information, DeezyStatus updates the user status. 

## License

DeezyStatus - Sync Your Slack Status with Deezer
    Copyright (C) 2023  Guillaume Vanel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Feedback

DeezyStatus is an in-progress app, and we'd love to hear from you! If you have any feedback, suggestions, or issues, feel free to reach out or open an issue in this repository.

## Contributing

We welcome contributions! If you'd like to contribute to DeezyStatus, please fork this repository and create a pull request.