# Google OAuth Resources Directory

This directory contains Google OAuth credentials for calendar access.

## Required Files:

- `client_secret.json` - Download this from your Google Cloud Console project
  - Go to https://console.cloud.google.com/
  - Create/select a project
  - Enable the Google Calendar API
  - Create OAuth 2.0 credentials for a desktop application
  - Download the JSON file and rename it to `client_secret.json`
  - Place it in this directory

## Note:

The `client_secret.json` file is ignored by git for security reasons and must be obtained separately for each installation.

See `docs/google_calendar_apikey_instructions.md` for detailed setup instructions.
