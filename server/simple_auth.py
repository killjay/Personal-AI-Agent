#!/usr/bin/env python3
"""
Simplified Google OAuth2 Authentication Helper
For development and testing purposes
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send', 
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar'
]

def authenticate():
    """Simplified authentication for development"""
    creds = None
    token_file = 'token.json'
    
    # Load existing credentials
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid credentials, run auth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use the client secrets file you already have
            flow = InstalledAppFlow.from_client_secrets_file(
                '../client_secret_943563522589-6pi60ibpqehlns0lgshugn79mssknv19.apps.googleusercontent.com.json',
                SCOPES
            )
            creds = flow.run_local_server(port=8080)
        
        # Save credentials for next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    print("✅ Authentication successful!")
    return creds

if __name__ == "__main__":
    print("🔐 Starting simplified Google OAuth authentication...")
    print("📋 This will open your browser for authentication")
    print("🌐 Make sure to configure your Google Cloud Console first!")
    
    try:
        creds = authenticate()
        print(f"✅ Success! Token saved to token.json")
        print(f"🔑 You can now use this token in your MCP server")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Make sure your OAuth consent screen is configured properly")
