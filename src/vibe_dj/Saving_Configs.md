# Saving Configs

This feature allows the users to save the updates made in the config UI to the config file. 
Right now the config values for the "Music" tab and "SubSonic Server" tab in the config UI are saved for the session and are not perssisted anywhere.

If the config values for the "Music" tab and "SubSonic Server" tab in the config UI are changed, and those values were initially loaded from a config file, then the config file should be updated with the new values.

If the config values for the "Music" tab and "SubSonic Server" tab in the config UI are changed, and those values were not initially loaded from a config file, then they are only stored for the session as is the behavior now.

## UI

To allow the user to save the config values, add a "Save" button to the config UI. This button should be placed at the bottom of the config UI. When clicked, the config values should be saved to the config file or to the session variable. 

The "Save" button should be disabled by default and only enabled when the config values have been changed. Upon a successful save, a small check mark should be displayed next to the button for 2 seconds. The button should be disabled again.

## Implementation

- Continue to use the tailwindcss framework for styling.
- Use the same colour scheme as the rest of the app.
- Use the same font as the rest of the app.
- The UI still needs to be responsive as it is now.
- Take your time and make sure the UI is as good as it can be as well as the code around it.
- Create unit tests as needed and run them to make sure the code is working as expected. If there are any issues, fix them.
