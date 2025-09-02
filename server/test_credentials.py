#!/usr/bin/env python3
"""
Test script to check credential validity and refresh
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Same scopes as the main server
ALL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar',
    'openid',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/contacts.other.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.upload'
]

TOKEN_FILE = 'mcp_token.json'

def test_credentials():
    print("🔍 Testing credential validity...")
    
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Token file not found: {TOKEN_FILE}")
        return
    
    try:
        # Load credentials
        print(f"📁 Loading credentials from {TOKEN_FILE}")
        with open(TOKEN_FILE, 'r') as token_file:
            creds_data = json.load(token_file)
        
        print("📋 Token file contents:")
        print(f"  - Has token: {'token' in creds_data}")
        print(f"  - Has refresh_token: {'refresh_token' in creds_data}")
        print(f"  - Has scopes: {'scopes' in creds_data}")
        
        # Create credentials object
        credentials = Credentials.from_authorized_user_info(creds_data, ALL_SCOPES)
        
        print(f"🔐 Credentials status:")
        print(f"  - Valid: {credentials.valid}")
        print(f"  - Expired: {credentials.expired}")
        print(f"  - Has refresh token: {bool(credentials.refresh_token)}")
        
        if credentials.expired and credentials.refresh_token:
            print("🔄 Attempting to refresh credentials...")
            try:
                credentials.refresh(Request())
                print("✅ Credentials refreshed successfully!")
                print(f"  - Valid after refresh: {credentials.valid}")
                
                # Save refreshed credentials
                refreshed_data = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                
                with open(TOKEN_FILE, 'w') as token_file:
                    json.dump(refreshed_data, token_file)
                print("💾 Saved refreshed credentials")
                
            except Exception as refresh_error:
                print(f"❌ Failed to refresh: {refresh_error}")
        
        elif credentials.valid:
            print("✅ Credentials are already valid!")
        else:
            print("❌ Credentials are invalid and cannot be refreshed")
        
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")

if __name__ == "__main__":
    test_credentials()
