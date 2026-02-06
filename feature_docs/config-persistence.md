# Feature Name: Config Persistence

## Description

This new feature will allow users to save their configuration changes to the config.json file.
Right now users have a UI to edit the following settings:
- Music Library Path
- SubSonic Server URL
- SubSonic Username
- SubSonic Password

These settings are only persisted in the React state and are not saved to the config.json file. With this feature, the settings will be saved to the config.json file.

## Behaviour
- Currently on startup the config.json file is read and the settings are loaded into the React state. 

- On each config screen, add a save button that will save the settings to the config.json file.

- The save button should be disabled if the settings have not changed since the last save. It should be enabled if the settings have changed since the last save.

- When clicked, the save button should save the settings to the config.json file. While saving, the button should show a loading spinner. Once complete, the button should show a checkmark for a 2 second duration.

## Implementation
- Continue to use the tailwindcss framework for styling.
- Use the same colour scheme as the rest of the app.
- Use the same font as the rest of the app.
- The UI still needs to be responsive as it is now.
- Take your time and make sure the UI is as good as it can be as well as the code around it.

## Testing
- Create unit tests for the backend and frontend for this feature and run them to make sure the code is working as expected. If there are any issues, fix them.


