#!/usr/bin/env python3
"""
Authenticated Calendar API Server for Voice AI Agent
Uses Google OAuth2 for real Calendar integration
"""

import os
import json
import logging
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

app = FastAPI(title="Calendar API Server (Authenticated)", description="Real Google Calendar integration for Voice AI Agent")

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
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar'
]

CLIENT_SECRETS = {
    "web": {
        "client_id": "943563522589-6pi60ibpqehlns0lgshugn79mssknv19.apps.googleusercontent.com",
        "project_id": "june-470413",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost:5001/auth/callback"]
    }
}

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'calendar_token.json')

def get_calendar_service():
    """Get authenticated Calendar service"""
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
        return build('calendar', 'v3', credentials=creds)
    else:
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint with auth status"""
    service = get_calendar_service()
    auth_status = "authenticated" if service else "not_authenticated"
    
    return {
        "status": "Calendar Server is running", 
        "service": "calendar", 
        "port": 5001,
        "authentication": auth_status
    }

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth2 login for Calendar"""
    try:
        # Create OAuth2 flow
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=SCOPES,
            redirect_uri="http://localhost:5001/auth/callback"
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
            redirect_uri="http://localhost:5001/auth/callback"
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
        
        logger.info("Calendar authentication successful, credentials saved")
        
        return {
            "status": "success",
            "message": "Calendar authentication completed successfully!",
            "authenticated": True
        }
        
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Callback error: {str(e)}")

@app.get("/events/today")
async def get_today_events():
    """Get today's calendar events"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:5001/auth/login"
            }
        
        # Get today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Format for API
        time_min = today.isoformat() + 'Z'
        time_max = tomorrow.isoformat() + 'Z'
        
        # Get events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_data = {
                "id": event['id'],
                "title": event.get('summary', 'No Title'),
                "description": event.get('description', ''),
                "start": start,
                "end": end,
                "location": event.get('location', ''),
                "attendees": [attendee.get('email') for attendee in event.get('attendees', [])],
                "all_day": 'date' in event['start']
            }
            calendar_events.append(event_data)
        
        logger.info(f"Retrieved {len(calendar_events)} events for today")
        return {"events": calendar_events, "count": len(calendar_events), "date": today.strftime("%Y-%m-%d"), "authenticated": True}
        
    except Exception as e:
        logger.error(f"Error fetching today's events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/events/upcoming")
async def get_upcoming_events(days: int = 7):
    """Get upcoming events for the next N days"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:5001/auth/login"
            }
        
        # Get date range
        now = datetime.now()
        future = now + timedelta(days=days)
        
        # Format for API
        time_min = now.isoformat() + 'Z'
        time_max = future.isoformat() + 'Z'
        
        # Get events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_data = {
                "id": event['id'],
                "title": event.get('summary', 'No Title'),
                "description": event.get('description', ''),
                "start": start,
                "end": end,
                "location": event.get('location', ''),
                "attendees": [attendee.get('email') for attendee in event.get('attendees', [])],
                "all_day": 'date' in event['start']
            }
            calendar_events.append(event_data)
        
        logger.info(f"Retrieved {len(calendar_events)} upcoming events for next {days} days")
        return {"events": calendar_events, "count": len(calendar_events), "days": days, "authenticated": True}
        
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/calendars")
async def get_calendars():
    """Get list of user's calendars"""
    try:
        service = get_calendar_service()
        if not service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:5001/auth/login"
            }
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = []
        
        for calendar in calendar_list.get('items', []):
            cal_data = {
                "id": calendar['id'],
                "name": calendar.get('summary', 'Unknown'),
                "description": calendar.get('description', ''),
                "primary": calendar.get('primary', False),
                "access_role": calendar.get('accessRole', 'reader'),
                "selected": calendar.get('selected', False)
            }
            calendars.append(cal_data)
        
        logger.info(f"Retrieved {len(calendars)} calendars")
        return {"calendars": calendars, "count": len(calendars), "authenticated": True}
        
    except Exception as e:
        logger.error(f"Error fetching calendars: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendars: {str(e)}")

@app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    service = get_calendar_service()
    authenticated = service is not None
    
    return {
        "authenticated": authenticated,
        "service": "calendar",
        "auth_url": "http://localhost:5001/auth/login" if not authenticated else None,
        "token_file_exists": os.path.exists(TOKEN_FILE)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    service = get_calendar_service()
    auth_status = "✅ Authenticated" if service else "❌ Not Authenticated"
    
    return {
        "message": "Authenticated Calendar Server for Voice AI Agent", 
        "version": "2.0.0",
        "authentication": auth_status,
        "endpoints": {
            "health": "/health",
            "login": "/auth/login", 
            "status": "/auth/status",
            "today_events": "/events/today",
            "upcoming_events": "/events/upcoming",
            "calendars": "/calendars"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Authenticated Calendar Server on http://0.0.0.0:5001")
    logger.info("📅 Google OAuth2 authentication enabled")
    logger.info("🔐 Visit http://localhost:5001/auth/login to authenticate")
    uvicorn.run(app, host="0.0.0.0", port=5001)
