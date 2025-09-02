#!/usr/bin/env python3
"""Test script to debug authentication issues"""

import os
import json
import logging
from google.oauth2.credentials import Credentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN_FILE = 'mcp_token.json'

def test_auth():
    print("Testing authentication...")
    
    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        print(f"✅ Token file exists: {TOKEN_FILE}")
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Token file loaded successfully")
                print(f"🔑 Scopes: {data.get('scopes', [])}")
                
                # Try to create credentials
                creds = Credentials.from_authorized_user_info(data)
                print(f"✅ Credentials created successfully")
                print(f"🔒 Valid: {creds.valid}")
                print(f"🔄 Expired: {creds.expired}")
                print(f"🔑 Has refresh token: {creds.refresh_token is not None}")
                
        except Exception as e:
            print(f"❌ Error loading token: {e}")
    else:
        print(f"❌ No token file found: {TOKEN_FILE}")

if __name__ == "__main__":
    test_auth()
