#!/usr/bin/env python3
"""
Authenticated Gmail API Server for Voice AI Agent
Uses Google OAuth2 for real Gmail integration
"""

import os
import json
import logging
import pickle
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gmail API Server (Authenticated)", description="Real Gmail integration for Voice AI Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google OAuth2 Configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

CLIENT_SECRETS = {
    "web": {
        "client_id": "943563522589-6pi60ibpqehlns0lgshugn79mssknv19.apps.googleusercontent.com",
        "project_id": "june-470413",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost:5000/auth/callback"]
    }
}

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'gmail_token.json')

def get_gmail_service():
    """Get authenticated Gmail service"""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            creds_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            # Save refreshed credentials
            with open(TOKEN_FILE, 'w') as token_file:
                json.dump(creds.to_json(), token_file)
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            creds = None
    
    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)
    else:
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint with auth status"""
    service = get_gmail_service()
    auth_status = "authenticated" if service else "not_authenticated"
    
    return {
        "status": "Gmail Server is running", 
        "service": "gmail", 
        "port": 5000,
        "authentication": auth_status
    }

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth2 login"""
    try:
        # Create OAuth2 flow
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=SCOPES,
            redirect_uri="http://localhost:5000/auth/callback"
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        logger.info(f"Redirecting to authorization URL: {authorization_url}")
        return {
            "auth_url": authorization_url,
            "message": "Visit the auth_url to complete authentication",
            "redirect": True
        }
        
    except Exception as e:
        logger.error(f"Error initiating login: {e}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle OAuth2 callback"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"Auth error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        # Exchange code for token
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=SCOPES,
            redirect_uri="http://localhost:5000/auth/callback"
        )
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save credentials
        with open(TOKEN_FILE, 'w') as token_file:
            json.dump({
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }, token_file)
        
        logger.info("Authentication successful, credentials saved")
        
        return {
            "status": "success",
            "message": "Gmail authentication completed successfully!",
            "authenticated": True
        }
        
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Callback error: {str(e)}")

@app.get("/emails/recent")
async def get_recent_emails(count: int = 10):
    """Get recent emails from Gmail"""
    try:
        service = get_gmail_service()
        if not service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:5000/auth/login"
            }
        
        # Get message list
        results = service.users().messages().list(
            userId='me',
            maxResults=count,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            
            email_data = {
                "id": message['id'],
                "thread_id": message['threadId'],
                "subject": next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                "sender": next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                "date": next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                "snippet": message.get('snippet', ''),
                "unread": 'UNREAD' in message.get('labelIds', [])
            }
            emails.append(email_data)
        
        logger.info(f"Retrieved {len(emails)} recent emails")
        return {"emails": emails, "count": len(emails), "authenticated": True}
        
    except Exception as e:
        logger.error(f"Error fetching recent emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@app.get("/emails/unread")
async def get_unread_emails():
    """Get unread emails from Gmail"""
    try:
        service = get_gmail_service()
        if not service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:5000/auth/login"
            }
        
        # Get unread messages
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD']
        ).execute()
        
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages[:10]:  # Limit to 10 for performance
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            
            email_data = {
                "id": message['id'],
                "subject": next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                "sender": next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                "date": next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                "snippet": message.get('snippet', ''),
                "unread": True
            }
            emails.append(email_data)
        
        logger.info(f"Retrieved {len(emails)} unread emails")
        return {"emails": emails, "count": len(emails), "authenticated": True}
        
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch unread emails: {str(e)}")

@app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    service = get_gmail_service()
    authenticated = service is not None
    
    return {
        "authenticated": authenticated,
        "service": "gmail",
        "auth_url": "http://localhost:5000/auth/login" if not authenticated else None,
        "token_file_exists": os.path.exists(TOKEN_FILE)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    service = get_gmail_service()
    auth_status = "✅ Authenticated" if service else "❌ Not Authenticated"
    
    return {
        "message": "Authenticated Gmail Server for Voice AI Agent", 
        "version": "2.0.0",
        "authentication": auth_status,
        "endpoints": {
            "health": "/health",
            "login": "/auth/login", 
            "status": "/auth/status",
            "recent_emails": "/emails/recent",
            "unread_emails": "/emails/unread"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Authenticated Gmail Server on http://0.0.0.0:5000")
    logger.info("🔐 Google OAuth2 authentication enabled")
    logger.info("📧 Visit http://localhost:5000/auth/login to authenticate")
    uvicorn.run(app, host="0.0.0.0", port=5000)
