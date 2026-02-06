# Feature name: config settings

## Description

This new feature will allow users to edit the configuration fro Vibe-DJ from within the app.

On the main search screen add a gear icon or any icon you think represents "App Configuration". Click on it brings you to the config screen.

Across the top is a set of tabs. The tabs are "Music" and "SubSonic". They will be centered across the top and will have subtle highlighting to indicate which one is selected. The subtle highlighting has to match the current colour scheme.


### Music Tab
The "Music" tab will have a input field for the music library path. If the server was started with this defined as an ENV variable or in a config.json file, then populate this field with either one of those values. 

Below this music library field is a button labelled "Index Music Library". It's disabled by default but cnce the music field is populated, it is enabled. 

When the button is enabled, clicking it forces a check that the library path is accessible and actually exists. It will then start the indexing process by calling the "/index" request API endpoint. The music library path will be passed as a parameter to the API endpoint.

While the index process is running it will show some basic progress information. This will be accomplished by polling the "/status" endpoint every 5 seconds.

Once the index process is complete, the "Index Music Library" button will be disabled and a message will be displayed indicating that the index is complete. The message will be displayed in a toast notification at the bottom of the screen.

### SubSonic Tab
The "SubSonic" tab will have a input field for the SubSonic server URL. If the server was started with this defined as an ENV variable or in a config.json file, then populate this field with either one of those values. 

Below this will be 2 input fields for the SubSonic username and password. If the server was started with this defined as an ENV variable or in a config.json file, then populate this field with either one of those values. 

Below this will be a button labelled "Test SubSonic Connection". It's disabled by default but cnce the SubSonic URL, username, and password are populated, it is enabled. 

These 3 fields will be passed as parameters to the code that syncs the playlist to the SubSonic server.

## Implementation
- Continue to use the tailwindcss framework for styling.
- Use the same colour scheme as the rest of the app.
- Use the same font as the rest of the app.
- The UI still needs to be responsive as it is now.
- Take your time and make sure the UI is as good as it can be as well as the code around it.
- Create unit tests as needed and run them to make sure the code is working as expected. If there are any issues, fix them.

