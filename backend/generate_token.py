#!/usr/bin/env python3
"""
Helper script to generate a token.json file for user OAuth2 authentication with Google Drive.
This is preferred for personal Google accounts to bypass the 0 GB storage quota limit of Service Accounts.

Requirements:
    pip install google-auth-oauthlib google-api-python-client

Usage:
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Select/create your project.
    3. Go to "APIs & Services" -> "Credentials".
    4. Click "+ CREATE CREDENTIALS" -> "OAuth client ID".
    5. Select Application type: "Desktop app", name it, and click "Create".
    6. Download the JSON file of the created client ID, rename it to 'credentials.json', and place it in the same directory as this script.
    7. Run this script: python generate_token.py
    8. Follow the authentication flow in your browser.
    9. Copy the contents of the generated 'token.json' and add it as a GitHub Secret named `GOOGLE_DRIVE_TOKEN_JSON`.
"""

import os
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: 'google-auth-oauthlib' is required to run this script.")
    print("Please install it by running:")
    print("    pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json"
OUTPUT_TOKEN_FILE = "token.json"

def main():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: '{CREDENTIALS_FILE}' not found in the current directory.")
        print("Please download your OAuth client ID JSON from Google Cloud Console,")
        print(f"rename it to '{CREDENTIALS_FILE}', place it here, and run the script again.")
        sys.exit(1)

    print("Starting authentication flow. A browser window should open...")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(OUTPUT_TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
            
        print("\nSuccess!")
        print(f"Your token has been saved to '{OUTPUT_TOKEN_FILE}'.")
        print("\nTo deploy this token to your production server via GitHub Actions:")
        print("1. Open the generated 'token.json' file and copy its entire text contents.")
        print("2. Go to your GitHub repository -> Settings -> Secrets and variables -> Actions.")
        print("3. Add a new repository secret named: GOOGLE_DRIVE_TOKEN_JSON")
        print("4. Paste the copied text contents and save.")
    except Exception as e:
        print(f"\nAn error occurred during authentication: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
