# Feature Name: Remove Environment Variables Feature

## Description

Remove the environment variables feature from the vibe-dj application.
The only way to configure the application is now through the config.json file.

## Behaviour

Remove the functionality that reads config variables from environment variables to configure the server. Remove the 
associated tests as well.

## Implementation

Be sure all the unit tests for the UI and Python code are passing after removing the environment variables feature.
