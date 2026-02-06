# Feature: Re-design Config Screen

The config screen is currently a modal that opens up when the user clicks on the gear icon in the top right corner of the screen. It is a simple modal form with 2 tabs, one for music and one for SubSonic. 
The re-design will be a full screen view with tabs across the top of the screen. The gear icon in the top right corner will remain and still open the config screen. Each tab in the config screen will be a sub-section of editable configuration options.

The tabs will be:
- Music
- SubSonic

The Music tab will have the following sub-sections:
- Music Library Path

The SubSonic tab will have the following sub-sections:
- SubSonic Server URL
- SubSonic Username
- SubSonic Password

The functionality of the tabs in the config screen will remain the same, but the UI will be re-designed to be more user friendly.

## UI

- The gear icon in the top right corner of the search screen will remain and still open the config screen.
- The config screen will be a full screen view with tabs centered across the top of the screen.
- Each tab in the config screen will be a sub-section of editable configuration options.
- When a tab is selected, the content of the tab should be displayed below the tabs. The tab colour should change to indicate which tab is currently selected.
- The config screen will have a save button in the top right corner that will save the configuration options to the config.json file.
- The config screen will have a back button in the top right corner that will close the config screen without saving the configuration options.
- This new UI layout still need to be responsive as it is now. 
- The UI should be as simple as possible and easy to use.
- The UI should be as modern as possible and use the same colour scheme as the rest of the app.

## Coding Standards

- All new code needs to be accompanied by unit tests.
- The code should be easy to read and understand.
- For Python code, use PEP 8 style guidelines and doc strings for all functions and classes.
- For JavaScript code, use ESLint to enforce code style and use TypeScript for type safety.
- Run all unit tests for Python and JavaScript code before submitting a pull request.