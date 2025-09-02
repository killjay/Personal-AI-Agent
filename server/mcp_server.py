#!/usr/bin/env python3
"""
Unified MCP Server for Voice AI Agent
Combines Gmail, Calendar, People, and YouTube APIs with Google OAuth2 authentication
No mock data - Real Google services only
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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

app = FastAPI(
    title="MCP Server - Gmail, Calendar, Contacts & YouTube", 
    description="Unified Google services for Voice AI Agent with real authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google OAuth2 Configuration
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar'
]

PEOPLE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/contacts.other.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email'
]

YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.upload'
]

DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

DOCS_SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/documents.readonly'
]

ALL_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES + PEOPLE_SCOPES + YOUTUBE_SCOPES + DRIVE_SCOPES + DOCS_SCOPES

CLIENT_SECRETS = {
    "web": {
        "client_id": "943563522589-6pi60ibpqehlns0lgshugn79mssknv19.apps.googleusercontent.com",
        "project_id": "june-470413",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost:8080/auth/callback"]
    }
}

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'mcp_token.json')

class GoogleServiceManager:
    """Manages Google API services with unified authentication"""
    
    def __init__(self):
        self._credentials = None
        self._gmail_service = None
        self._calendar_service = None
        self._people_service = None
        self._youtube_service = None
        self._drive_service = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load and refresh credentials if available"""
        if os.path.exists(TOKEN_FILE):
            try:
                logger.info(f"Loading credentials from {TOKEN_FILE}")
                with open(TOKEN_FILE, 'r') as token_file:
                    creds_data = json.load(token_file)
                    self._credentials = Credentials.from_authorized_user_info(creds_data, ALL_SCOPES)
                
                logger.info("Credentials loaded successfully")
                
                # Refresh if expired
                if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                    logger.info("Credentials expired, refreshing...")
                    self._credentials.refresh(GoogleRequest())
                    self._save_credentials()
                    logger.info("Credentials refreshed and saved")
                elif self._credentials and self._credentials.valid:
                    logger.info("Credentials are valid and ready to use")
                    
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                self._credentials = None
        else:
            logger.info(f"No token file found at {TOKEN_FILE}")
    
    def _save_credentials(self):
        """Save credentials to file"""
        if self._credentials:
            try:
                with open(TOKEN_FILE, 'w') as token_file:
                    json.dump({
                        'token': self._credentials.token,
                        'refresh_token': self._credentials.refresh_token,
                        'token_uri': self._credentials.token_uri,
                        'client_id': self._credentials.client_id,
                        'client_secret': self._credentials.client_secret,
                        'scopes': self._credentials.scopes
                    }, token_file)
            except Exception as e:
                logger.error(f"Error saving credentials: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        try:
            if not self._credentials:
                logger.debug("No credentials found")
                return False
                
            # Check if credentials are valid
            if self._credentials.valid:
                logger.debug("Credentials are valid")
                return True
                
            # Try to refresh if expired but have refresh token
            if self._credentials.expired and self._credentials.refresh_token:
                logger.info("Credentials expired, attempting refresh...")
                try:
                    self._credentials.refresh(GoogleRequest())
                    self._save_credentials()
                    logger.info("Credentials refreshed successfully")
                    return True
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh credentials: {refresh_error}")
                    return False
            
            logger.warning("Credentials exist but are invalid and cannot be refreshed")
            return False
            
        except Exception as e:
            logger.error(f"Error checking credential validity: {e}")
            return False
    
    def get_gmail_service(self):
        """Get Gmail service instance"""
        if not self.is_authenticated():
            return None
        
        if not self._gmail_service:
            try:
                self._gmail_service = build('gmail', 'v1', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building Gmail service: {e}")
                return None
        
        return self._gmail_service
    
    def get_calendar_service(self):
        """Get Calendar service instance"""
        if not self.is_authenticated():
            return None
        
        if not self._calendar_service:
            try:
                self._calendar_service = build('calendar', 'v3', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building Calendar service: {e}")
                return None
        
        return self._calendar_service
    
    def get_people_service(self):
        """Get People API service instance"""
        if not self.is_authenticated():
            return None
        
        if not self._people_service:
            try:
                self._people_service = build('people', 'v1', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building People service: {e}")
                return None
        
        return self._people_service
    
    def get_youtube_service(self):
        """Get YouTube Data API service instance"""
        if not self.is_authenticated():
            return None
        
        if not self._youtube_service:
            try:
                self._youtube_service = build('youtube', 'v3', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building YouTube service: {e}")
                return None
        
        return self._youtube_service
    
    def get_drive_service(self):
        """Get Google Drive API service instance"""
        if not self.is_authenticated():
            return None
        
        if not self._drive_service:
            try:
                self._drive_service = build('drive', 'v3', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building Drive service: {e}")
                return None
        
        return self._drive_service
    
    def get_docs_service(self):
        """Get Google Docs API service instance"""
        if not self.is_authenticated():
            return None
        
        if not hasattr(self, '_docs_service'):
            self._docs_service = None
            
        if not self._docs_service:
            try:
                self._docs_service = build('docs', 'v1', credentials=self._credentials)
            except Exception as e:
                logger.error(f"Error building Docs service: {e}")
                return None
        
        return self._docs_service
    
    def get_credentials(self):
        """Get current credentials"""
        return self._credentials
    
    def set_credentials(self, credentials):
        """Set new credentials"""
        self._credentials = credentials
        self._gmail_service = None
        self._calendar_service = None
        self._people_service = None
        self._youtube_service = None
        self._save_credentials()

# Global service manager
service_manager = GoogleServiceManager()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check with authentication status"""
    return {
        "status": "MCP Server is running",
        "services": ["gmail", "calendar", "contacts", "youtube"],
        "port": 8080,
        "authenticated": service_manager.is_authenticated(),
        "version": "1.0.0"
    }

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth2 login for all services"""
    try:
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=ALL_SCOPES,
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        logger.info(f"Initiating OAuth flow: {authorization_url}")
        return {
            "auth_url": authorization_url,
            "message": "Visit the auth_url to complete authentication",
            "services": ["Gmail", "Calendar", "Contacts", "YouTube"],
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
        
        # Create flow with flexible scope handling
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=ALL_SCOPES,
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        # Fetch token and accept whatever scopes Google granted
        flow.fetch_token(code=code)
        
        # Set credentials regardless of scope differences
        service_manager.set_credentials(flow.credentials)
        
        # Get the actual granted scopes
        granted_scopes = flow.credentials.scopes if flow.credentials.scopes else ["Unknown"]
        
        logger.info(f"Authentication successful! Granted scopes: {granted_scopes}")
        
        # Determine which services are authenticated based on granted scopes
        authenticated_services = []
        if any("gmail" in scope for scope in granted_scopes):
            authenticated_services.append("Gmail")
        if any("calendar" in scope for scope in granted_scopes):
            authenticated_services.append("Calendar")
        if any("contacts" in scope for scope in granted_scopes):
            authenticated_services.append("Contacts")
        if any("youtube" in scope for scope in granted_scopes):
            authenticated_services.append("YouTube")
        
        return {
            "status": "success",
            "message": "Authentication completed successfully!",
            "authenticated": True,
            "services": authenticated_services
        }
        
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Callback error: {str(e)}")

@app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    try:
        authenticated = service_manager.is_authenticated()
        
        # Determine which services are authenticated based on available scopes
        authenticated_services = []
        if authenticated:
            try:
                credentials = service_manager.get_credentials()
                if credentials and hasattr(credentials, 'scopes') and credentials.scopes:
                    if any("gmail" in scope for scope in credentials.scopes):
                        authenticated_services.append("gmail")
                    if any("calendar" in scope for scope in credentials.scopes):
                        authenticated_services.append("calendar")
                    if any("contacts" in scope for scope in credentials.scopes):
                        authenticated_services.append("contacts")
                    if any("youtube" in scope for scope in credentials.scopes):
                        authenticated_services.append("youtube")
            except Exception as e:
                logger.error(f"Error checking credentials scopes: {e}")
                # Fallback: try to detect services based on successful API calls
                if service_manager.get_gmail_service():
                    authenticated_services.append("gmail")
                if service_manager.get_calendar_service():
                    authenticated_services.append("calendar")  
                if service_manager.get_people_service():
                    authenticated_services.append("contacts")
                if service_manager.get_youtube_service():
                    authenticated_services.append("youtube")
        
        return {
            "authenticated": authenticated,
            "services": authenticated_services,
            "auth_url": "http://localhost:8080/auth/login" if not authenticated else None,
            "token_file_exists": os.path.exists(TOKEN_FILE),
            "scopes": ALL_SCOPES if authenticated else []
        }
    except Exception as e:
        logger.error(f"Error in auth_status: {e}")
        raise HTTPException(status_code=500, detail=f"Auth status error: {str(e)}")

# ============================================================================
# GMAIL ENDPOINTS
# ============================================================================

@app.get("/gmail/recent")
async def get_recent_emails(count: int = 10):
    """Get recent emails from Gmail"""
    try:
        gmail_service = service_manager.get_gmail_service()
        if not gmail_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get message list
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=count,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            message = gmail_service.users().messages().get(
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
        return {"emails": emails, "count": len(emails), "service": "gmail"}
        
    except Exception as e:
        logger.error(f"Error fetching recent emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@app.get("/gmail/unread")
async def get_unread_emails():
    """Get unread emails from Gmail"""
    try:
        gmail_service = service_manager.get_gmail_service()
        if not gmail_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get unread messages
        results = gmail_service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD']
        ).execute()
        
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages[:10]:  # Limit to 10 for performance
            message = gmail_service.users().messages().get(
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
        return {"emails": emails, "count": len(emails), "service": "gmail"}
        
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch unread emails: {str(e)}")

# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================

@app.get("/calendar/today")
async def get_today_events():
    """Get today's calendar events"""
    try:
        calendar_service = service_manager.get_calendar_service()
        if not calendar_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Format for API
        time_min = today.isoformat() + 'Z'
        time_max = tomorrow.isoformat() + 'Z'
        
        # Get events
        events_result = calendar_service.events().list(
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
        return {
            "events": calendar_events, 
            "count": len(calendar_events), 
            "date": today.strftime("%Y-%m-%d"),
            "service": "calendar"
        }
        
    except Exception as e:
        logger.error(f"Error fetching today's events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/calendar/upcoming")
async def get_upcoming_events(days: int = 7):
    """Get upcoming events for the next N days"""
    try:
        calendar_service = service_manager.get_calendar_service()
        if not calendar_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get date range
        now = datetime.now()
        future = now + timedelta(days=days)
        
        # Format for API
        time_min = now.isoformat() + 'Z'
        time_max = future.isoformat() + 'Z'
        
        # Get events
        events_result = calendar_service.events().list(
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
        return {
            "events": calendar_events, 
            "count": len(calendar_events), 
            "days": days,
            "service": "calendar"
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/calendar/list")
async def get_calendars():
    """Get list of user's calendars"""
    try:
        calendar_service = service_manager.get_calendar_service()
        if not calendar_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get calendar list
        calendar_list = calendar_service.calendarList().list().execute()
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
        return {"calendars": calendars, "count": len(calendars), "service": "calendar"}
        
    except Exception as e:
        logger.error(f"Error fetching calendars: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendars: {str(e)}")

@app.post("/calendar/create_event")
async def create_calendar_event(request: Request):
    """Create a new calendar event"""
    try:
        calendar_service = service_manager.get_calendar_service()
        if not calendar_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Parse request body
        event_data = await request.json()
        
        # Required fields
        title = event_data.get('title', 'Meeting')
        start_time = event_data.get('start_time')  # ISO format or datetime string
        end_time = event_data.get('end_time')
        
        # Optional fields
        description = event_data.get('description', '')
        location = event_data.get('location', '')
        attendees = event_data.get('attendees', [])  # List of email addresses
        calendar_id = event_data.get('calendar_id', 'primary')
        
        if not start_time or not end_time:
            raise HTTPException(status_code=400, detail="start_time and end_time are required")
        
        # Format event for Google Calendar API
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Chicago',  # Central Time for US Central timezone
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Chicago',  # Central Time for US Central timezone
            },
        }
        
        # Add location if provided
        if location:
            event['location'] = location
        
        # Add attendees if provided
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Create the event
        created_event = calendar_service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'  # Send email invites to attendees
        ).execute()
        
        logger.info(f"Created calendar event: {title} at {start_time}")
        
        return {
            "success": True,
            "event_id": created_event['id'],
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "attendees": attendees,
            "calendar_link": created_event.get('htmlLink', ''),
            "service": "calendar"
        }
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

# ============================================================================
# PEOPLE API ENDPOINTS
# ============================================================================

@app.get("/contacts/all")
async def get_all_contacts():
    """Get all contacts from Google Contacts"""
    try:
        people_service = service_manager.get_people_service()
        if not people_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get connections (contacts)
        results = people_service.people().connections().list(
            resourceName='people/me',
            personFields='names,emailAddresses,phoneNumbers,organizations,addresses,birthdays'
        ).execute()
        
        connections = results.get('connections', [])
        contacts = []
        
        for person in connections:
            contact_data = {
                "resource_name": person.get('resourceName', ''),
                "names": [],
                "emails": [],
                "phones": [],
                "organizations": [],
                "addresses": [],
                "birthdays": []
            }
            
            # Extract names
            if 'names' in person:
                for name in person['names']:
                    contact_data["names"].append({
                        "display_name": name.get('displayName', ''),
                        "given_name": name.get('givenName', ''),
                        "family_name": name.get('familyName', ''),
                        "middle_name": name.get('middleName', '')
                    })
            
            # Extract email addresses
            if 'emailAddresses' in person:
                for email in person['emailAddresses']:
                    contact_data["emails"].append({
                        "value": email.get('value', ''),
                        "type": email.get('type', ''),
                        "display_name": email.get('displayName', '')
                    })
            
            # Extract phone numbers
            if 'phoneNumbers' in person:
                for phone in person['phoneNumbers']:
                    contact_data["phones"].append({
                        "value": phone.get('value', ''),
                        "type": phone.get('type', ''),
                        "canonical_form": phone.get('canonicalForm', '')
                    })
            
            # Extract organizations
            if 'organizations' in person:
                for org in person['organizations']:
                    contact_data["organizations"].append({
                        "name": org.get('name', ''),
                        "title": org.get('title', ''),
                        "department": org.get('department', '')
                    })
            
            # Extract addresses
            if 'addresses' in person:
                for address in person['addresses']:
                    contact_data["addresses"].append({
                        "formatted_value": address.get('formattedValue', ''),
                        "type": address.get('type', ''),
                        "street_address": address.get('streetAddress', ''),
                        "city": address.get('city', ''),
                        "region": address.get('region', ''),
                        "postal_code": address.get('postalCode', ''),
                        "country": address.get('country', '')
                    })
            
            # Extract birthdays
            if 'birthdays' in person:
                for birthday in person['birthdays']:
                    if 'date' in birthday:
                        date_info = birthday['date']
                        contact_data["birthdays"].append({
                            "year": date_info.get('year', ''),
                            "month": date_info.get('month', ''),
                            "day": date_info.get('day', '')
                        })
            
            contacts.append(contact_data)
        
        logger.info(f"Retrieved {len(contacts)} contacts")
        return {
            "contacts": contacts,
            "count": len(contacts),
            "service": "people"
        }
        
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch contacts: {str(e)}")

@app.get("/contacts/search")
async def search_contacts(query: str):
    """Search contacts by name or email"""
    try:
        people_service = service_manager.get_people_service()
        if not people_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get all connections first, then filter
        results = people_service.people().connections().list(
            resourceName='people/me',
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()
        
        connections = results.get('connections', [])
        matching_contacts = []
        query_lower = query.lower()
        
        for person in connections:
            match_found = False
            
            # Check names
            if 'names' in person:
                for name in person['names']:
                    display_name = name.get('displayName', '').lower()
                    given_name = name.get('givenName', '').lower()
                    family_name = name.get('familyName', '').lower()
                    
                    if (query_lower in display_name or 
                        query_lower in given_name or 
                        query_lower in family_name):
                        match_found = True
                        break
            
            # Check emails
            if not match_found and 'emailAddresses' in person:
                for email in person['emailAddresses']:
                    email_value = email.get('value', '').lower()
                    if query_lower in email_value:
                        match_found = True
                        break
            
            if match_found:
                contact_data = {
                    "resource_name": person.get('resourceName', ''),
                    "names": person.get('names', []),
                    "emails": person.get('emailAddresses', []),
                    "phones": person.get('phoneNumbers', [])
                }
                matching_contacts.append(contact_data)
        
        logger.info(f"Found {len(matching_contacts)} contacts matching '{query}'")
        return {
            "contacts": matching_contacts,
            "count": len(matching_contacts),
            "query": query,
            "service": "people"
        }
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search contacts: {str(e)}")

@app.get("/profile/me")
async def get_my_profile():
    """Get authenticated user's profile information"""
    try:
        people_service = service_manager.get_people_service()
        if not people_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get user profile
        profile = people_service.people().get(
            resourceName='people/me',
            personFields='names,emailAddresses,phoneNumbers,addresses,organizations,birthdays,genders'
        ).execute()
        
        profile_data = {
            "resource_name": profile.get('resourceName', ''),
            "names": profile.get('names', []),
            "emails": profile.get('emailAddresses', []),
            "phones": profile.get('phoneNumbers', []),
            "addresses": profile.get('addresses', []),
            "organizations": profile.get('organizations', []),
            "birthdays": profile.get('birthdays', []),
            "genders": profile.get('genders', [])
        }
        
        logger.info("Retrieved user profile")
        return {
            "profile": profile_data,
            "service": "people"
        }
        
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@app.get("/contacts/find")
async def find_contact_by_name(name: str):
    """Find a specific contact by name (for meeting scheduling)"""
    try:
        people_service = service_manager.get_people_service()
        if not people_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get all connections and find best match
        results = people_service.people().connections().list(
            resourceName='people/me',
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()
        
        connections = results.get('connections', [])
        name_lower = name.lower()
        best_matches = []
        
        for person in connections:
            if 'names' in person:
                for person_name in person['names']:
                    display_name = person_name.get('displayName', '').lower()
                    given_name = person_name.get('givenName', '').lower()
                    family_name = person_name.get('familyName', '').lower()
                    
                    # Exact match gets highest priority
                    if name_lower == display_name or name_lower == given_name or name_lower == family_name:
                        contact_data = {
                            "resource_name": person.get('resourceName', ''),
                            "display_name": person_name.get('displayName', ''),
                            "given_name": person_name.get('givenName', ''),
                            "family_name": person_name.get('familyName', ''),
                            "emails": person.get('emailAddresses', []),
                            "phones": person.get('phoneNumbers', []),
                            "match_type": "exact"
                        }
                        best_matches.insert(0, contact_data)  # Add to front for exact matches
                    # Partial match
                    elif (name_lower in display_name or name_lower in given_name or name_lower in family_name):
                        contact_data = {
                            "resource_name": person.get('resourceName', ''),
                            "display_name": person_name.get('displayName', ''),
                            "given_name": person_name.get('givenName', ''),
                            "family_name": person_name.get('familyName', ''),
                            "emails": person.get('emailAddresses', []),
                            "phones": person.get('phoneNumbers', []),
                            "match_type": "partial"
                        }
                        best_matches.append(contact_data)
        
        # Remove duplicates and limit results
        unique_matches = []
        seen_names = set()
        for match in best_matches:
            name_key = match.get('display_name', '').lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_matches.append(match)
        
        logger.info(f"Found {len(unique_matches)} contacts matching '{name}'")
        return {
            "contacts": unique_matches[:5],  # Return top 5 matches
            "count": len(unique_matches),
            "query": name,
            "service": "people"
        }
        
    except Exception as e:
        logger.error(f"Error finding contact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find contact: {str(e)}")

@app.get("/contacts/emails")
async def get_contact_emails():
    """Get all contact emails for easy access"""
    try:
        people_service = service_manager.get_people_service()
        if not people_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get connections with email addresses
        results = people_service.people().connections().list(
            resourceName='people/me',
            personFields='names,emailAddresses'
        ).execute()
        
        connections = results.get('connections', [])
        email_contacts = []
        
        for person in connections:
            if 'emailAddresses' in person and person['emailAddresses']:
                for email in person['emailAddresses']:
                    email_data = {
                        "name": "",
                        "email": email.get('value', ''),
                        "type": email.get('type', ''),
                        "resource_name": person.get('resourceName', '')
                    }
                    
                    # Get the person's name
                    if 'names' in person:
                        for name in person['names']:
                            if name.get('metadata', {}).get('primary', False):
                                email_data['name'] = name.get('displayName', '')
                                break
                        if not email_data['name'] and person['names']:
                            email_data['name'] = person['names'][0].get('displayName', '')
                    
                    email_contacts.append(email_data)
        
        logger.info(f"Retrieved {len(email_contacts)} email contacts")
        return {
            "email_contacts": email_contacts,
            "count": len(email_contacts),
            "service": "people"
        }
        
    except Exception as e:
        logger.error(f"Error fetching email contacts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email contacts: {str(e)}")

# ============================================================================
# YOUTUBE DATA API ENDPOINTS
# ============================================================================

@app.get("/youtube/channel")
async def get_my_channel():
    """Get authenticated user's YouTube channel information"""
    try:
        youtube_service = service_manager.get_youtube_service()
        if not youtube_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get user's channel
        channels_response = youtube_service.channels().list(
            part='snippet,statistics,contentDetails',
            mine=True
        ).execute()
        
        channels = channels_response.get('items', [])
        
        if not channels:
            return {
                "error": "No YouTube channel found for authenticated user",
                "channels": [],
                "service": "youtube"
            }
        
        channel_data = []
        for channel in channels:
            snippet = channel.get('snippet', {})
            statistics = channel.get('statistics', {})
            content_details = channel.get('contentDetails', {})
            
            channel_info = {
                "id": channel.get('id', ''),
                "title": snippet.get('title', ''),
                "description": snippet.get('description', ''),
                "custom_url": snippet.get('customUrl', ''),
                "published_at": snippet.get('publishedAt', ''),
                "thumbnail_url": snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                "subscriber_count": statistics.get('subscriberCount', '0'),
                "video_count": statistics.get('videoCount', '0'),
                "view_count": statistics.get('viewCount', '0'),
                "uploads_playlist_id": content_details.get('relatedPlaylists', {}).get('uploads', '')
            }
            channel_data.append(channel_info)
        
        logger.info(f"Retrieved {len(channel_data)} YouTube channels")
        return {
            "channels": channel_data,
            "count": len(channel_data),
            "service": "youtube"
        }
        
    except Exception as e:
        logger.error(f"Error fetching YouTube channel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube channel: {str(e)}")

@app.get("/youtube/videos")
async def get_my_videos(max_results: int = 10):
    """Get authenticated user's recent YouTube videos"""
    try:
        youtube_service = service_manager.get_youtube_service()
        if not youtube_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # First get the uploads playlist ID
        channels_response = youtube_service.channels().list(
            part='contentDetails',
            mine=True
        ).execute()
        
        channels = channels_response.get('items', [])
        if not channels:
            return {
                "error": "No YouTube channel found",
                "videos": [],
                "service": "youtube"
            }
        
        uploads_playlist_id = channels[0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        playlist_response = youtube_service.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        videos = []
        for item in playlist_response.get('items', []):
            snippet = item.get('snippet', {})
            video_id = snippet.get('resourceId', {}).get('videoId', '')
            
            video_info = {
                "video_id": video_id,
                "title": snippet.get('title', ''),
                "description": snippet.get('description', ''),
                "published_at": snippet.get('publishedAt', ''),
                "thumbnail_url": snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                "channel_title": snippet.get('channelTitle', ''),
                "watch_url": f"https://www.youtube.com/watch?v={video_id}"
            }
            videos.append(video_info)
        
        logger.info(f"Retrieved {len(videos)} YouTube videos")
        return {
            "videos": videos,
            "count": len(videos),
            "max_results": max_results,
            "service": "youtube"
        }
        
    except Exception as e:
        logger.error(f"Error fetching YouTube videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube videos: {str(e)}")

@app.get("/youtube/search")
async def search_youtube(q: str, max_results: int = 10):
    """Search YouTube videos"""
    try:
        logger.info(f"YouTube search request: q='{q}', max_results={max_results}")
        
        youtube_service = service_manager.get_youtube_service()
        if not youtube_service:
            raise HTTPException(status_code=401, detail="YouTube service not authenticated")
        
        # Search for videos
        search_response = youtube_service.search().list(
            q=q,
            part='id,snippet',
            maxResults=max_results,
            type='video'
        ).execute()
        
        videos = []
        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                video_info = {
                    'video_id': search_result['id']['videoId'],
                    'title': search_result['snippet']['title'],
                    'channel': search_result['snippet']['channelTitle'],
                    'description': search_result['snippet']['description'],
                    'published_at': search_result['snippet']['publishedAt'],
                    'thumbnail': search_result['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'url': f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
                }
                videos.append(video_info)
        
        logger.info(f"Found {len(videos)} videos for query: {q}")
        
        return {
            "status": "success",
            "query": q,
            "total_results": len(videos),
            "videos": videos
        }
        
    except Exception as e:
        logger.error(f"Error in YouTube search: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"YouTube search failed: {str(e)}")

@app.get("/youtube/playlists")
async def get_my_playlists(max_results: int = 25):
    """Get authenticated user's YouTube playlists"""
    try:
        youtube_service = service_manager.get_youtube_service()
        if not youtube_service:
            return {
                "error": "Not authenticated",
                "auth_required": True,
                "auth_url": "http://localhost:8080/auth/login"
            }
        
        # Get user's playlists
        playlists_response = youtube_service.playlists().list(
            part='snippet,contentDetails',
            mine=True,
            maxResults=max_results
        ).execute()
        
        playlists = []
        for item in playlists_response.get('items', []):
            snippet = item.get('snippet', {})
            content_details = item.get('contentDetails', {})
            
            playlist_info = {
                "playlist_id": item.get('id', ''),
                "title": snippet.get('title', ''),
                "description": snippet.get('description', ''),
                "published_at": snippet.get('publishedAt', ''),
                "thumbnail_url": snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                "item_count": content_details.get('itemCount', 0),
                "privacy_status": snippet.get('localized', {}).get('title', ''),
                "url": f"https://www.youtube.com/playlist?list={item.get('id', '')}"
            }
            playlists.append(playlist_info)
        
        logger.info(f"Retrieved {len(playlists)} YouTube playlists")
        return {
            "playlists": playlists,
            "count": len(playlists),
            "max_results": max_results,
            "service": "youtube"
        }
        
    except Exception as e:
        logger.error(f"Error fetching YouTube playlists: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube playlists: {str(e)}")

# ============================================================================
# NOTES & LISTS API (Google Drive-based)
# ============================================================================

@app.get("/notes/all")
async def get_all_notes():
    """Get all June notes stored in Google Drive"""
    if not service_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    
    try:
        drive_service = service_manager.get_drive_service()
        if not drive_service:
            raise HTTPException(status_code=503, detail="Drive service not available")
        
        # Search for June notes folder or create it
        folder_query = "name='June Notes' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_result = drive_service.files().list(q=folder_query).execute()
        
        if not folder_result.get('files'):
            # Create June Notes folder
            folder_metadata = {
                'name': 'June Notes',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
        else:
            folder_id = folder_result.get('files')[0].get('id')
        
        # Get all notes in the folder
        notes_query = f"parents in '{folder_id}' and trashed=false"
        notes_result = drive_service.files().list(
            q=notes_query,
            fields="files(id,name,createdTime,modifiedTime,mimeType)"
        ).execute()
        
        notes_list = []
        for file in notes_result.get('files', []):
            note_info = {
                "id": file.get('id'),
                "title": file.get('name', 'Untitled'),
                "created_time": file.get('createdTime', ''),
                "updated_time": file.get('modifiedTime', ''),
                "type": "shopping_list" if "Shopping" in file.get('name', '') else "note"
            }
            notes_list.append(note_info)
        
        logger.info(f"Retrieved {len(notes_list)} June notes from Drive")
        return {
            "notes": notes_list,
            "count": len(notes_list),
            "folder_id": folder_id,
            "service": "drive"
        }
        
    except Exception as e:
        logger.error(f"Error fetching notes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch notes: {str(e)}")

@app.post("/notes/create")
async def create_note(request: dict):
    """Create a new note in Google Drive (for meeting minutes/notes)"""
    if not service_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    
    try:
        drive_service = service_manager.get_drive_service()
        if not drive_service:
            raise HTTPException(status_code=503, detail="Drive service not available")
        
        title = request.get('title', 'Meeting Notes')
        content = request.get('content', '')
        
        # Ensure June Notes folder exists
        folder_query = "name='June Notes' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_result = drive_service.files().list(q=folder_query).execute()
        
        if not folder_result.get('files'):
            folder_metadata = {
                'name': 'June Notes',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
        else:
            folder_id = folder_result.get('files')[0].get('id')
        
        # Create the note as a Google Doc
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        note_content = f"""# {title}
Created: {timestamp}
Created by: June AI Assistant

{content}
"""
        
        # Create Google Doc
        doc_metadata = {
            'name': title,
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.document'
        }
        
        # Create empty doc first
        doc = drive_service.files().create(body=doc_metadata).execute()
        doc_id = doc.get('id')
        
        # Update content using Google Docs API with proper formatting
        from googleapiclient.discovery import build
        docs_service = build('docs', 'v1', credentials=service_manager.get_credentials())
        
        # Convert markdown-like content to Google Docs formatting
        formatted_requests = []
        
        # Insert the base content first
        formatted_requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': note_content
            }
        })
        
        # Apply formatting based on content structure
        lines = note_content.split('\n')
        current_index = 1
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            # Format headers (lines starting with #)
            if line.startswith('# '):
                formatted_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(line)
                        },
                        'textStyle': {
                            'fontSize': {'magnitude': 24, 'unit': 'PT'},
                            'bold': True
                        },
                        'fields': 'fontSize,bold'
                    }
                })
            elif line.startswith('## '):
                formatted_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(line)
                        },
                        'textStyle': {
                            'fontSize': {'magnitude': 16, 'unit': 'PT'},
                            'bold': True
                        },
                        'fields': 'fontSize,bold'
                    }
                })
            elif line.startswith('**') and line.endswith('**'):
                # Bold text
                formatted_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(line)
                        },
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
            elif line.startswith('• ') or line.startswith('- '):
                # Bullet points - apply list formatting
                formatted_requests.append({
                    'createParagraphBullets': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(line)
                        },
                        'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                    }
                })
            
            current_index += line_length
        
        # Execute all formatting requests
        if formatted_requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': formatted_requests}
            ).execute()
        
        logger.info(f"Created note: {title}")
        return {
            "success": True,
            "note_id": doc_id,
            "title": title,
            "content": content,
            "message": f"Note '{title}' created successfully in Google Drive",
            "service": "drive"
        }
        
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")

@app.post("/lists/create")
async def create_shopping_list(request: dict):
    """Create or update a shopping list in Google Drive"""
    if not service_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    
    try:
        drive_service = service_manager.get_drive_service()
        if not drive_service:
            raise HTTPException(status_code=503, detail="Drive service not available")
        
        title = request.get('title', 'Shopping List')
        items = request.get('items', [])
        append_to_existing = request.get('append', True)
        
        # Ensure June Notes folder exists
        folder_query = "name='June Notes' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_result = drive_service.files().list(q=folder_query).execute()
        
        if not folder_result.get('files'):
            folder_metadata = {
                'name': 'June Notes',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
        else:
            folder_id = folder_result.get('files')[0].get('id')
        
        # Try to find existing shopping list
        existing_list = None
        if append_to_existing:
            list_query = f"name='{title}' and parents in '{folder_id}' and trashed=false"
            list_result = drive_service.files().list(q=list_query).execute()
            
            if list_result.get('files'):
                existing_list = list_result.get('files')[0]
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if existing_list and append_to_existing:
            # Append to existing list
            doc_id = existing_list.get('id')
            
            # Get current content
            from googleapiclient.discovery import build
            docs_service = build('docs', 'v1', credentials=service_manager.get_credentials())
            
            doc = docs_service.documents().get(documentId=doc_id).execute()
            
            # Get the document's end index (total character count)
            end_index = doc.get('body', {}).get('content', [])[-1].get('endIndex', 1) - 1
            
            # Add new items
            new_items_text = "\n" + "\n".join([f"□ {item}" for item in items])
            new_items_text += f"\n\nUpdated: {timestamp}\n"
            
            requests_body = [
                {
                    'insertText': {
                        'location': {'index': end_index},
                        'text': new_items_text
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests_body}
            ).execute()
            
            logger.info(f"Added {len(items)} items to existing shopping list")
            return {
                "success": True,
                "note_id": doc_id,
                "title": title,
                "action": "appended",
                "items_added": items,
                "message": f"Added {len(items)} items to '{title}'",
                "service": "drive"
            }
        else:
            # Create new list
            list_content = f"""# {title}
Created: {timestamp}
Created by: June AI Assistant

"""
            for item in items:
                list_content += f"□ {item}\n"
            
            # Create Google Doc
            doc_metadata = {
                'name': title,
                'parents': [folder_id],
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            doc = drive_service.files().create(body=doc_metadata).execute()
            doc_id = doc.get('id')
            
            # Update content
            from googleapiclient.discovery import build
            docs_service = build('docs', 'v1', credentials=service_manager.get_credentials())
            
            requests_body = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': list_content
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests_body}
            ).execute()
            
            logger.info(f"Created new shopping list: {title}")
            return {
                "success": True,
                "note_id": doc_id,
                "title": title,
                "action": "created",
                "items": items,
                "total_items": len(items),
                "message": f"Created '{title}' with {len(items)} items",
                "service": "drive"
            }
        
    except Exception as e:
        logger.error(f"Error creating/updating shopping list: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create/update shopping list: {str(e)}")

@app.get("/notes/search")
async def search_notes(query: str = ""):
    """Search June notes in Google Drive"""
    if not service_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    
    try:
        drive_service = service_manager.get_drive_service()
        if not drive_service:
            raise HTTPException(status_code=503, detail="Drive service not available")
        
        # Find June Notes folder
        folder_query = "name='June Notes' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_result = drive_service.files().list(q=folder_query).execute()
        
        if not folder_result.get('files'):
            return {
                "notes": [],
                "count": 0,
                "query": query,
                "service": "drive"
            }
        
        folder_id = folder_result.get('files')[0].get('id')
        
        # Search notes with query
        search_query = f"parents in '{folder_id}' and trashed=false"
        if query:
            search_query += f" and fullText contains '{query}'"
        
        notes_result = drive_service.files().list(
            q=search_query,
            fields="files(id,name,createdTime,modifiedTime,mimeType)"
        ).execute()
        
        notes_list = []
        for file in notes_result.get('files', []):
            note_info = {
                "id": file.get('id'),
                "title": file.get('name', 'Untitled'),
                "created_time": file.get('createdTime', ''),
                "updated_time": file.get('modifiedTime', ''),
                "type": "shopping_list" if "Shopping" in file.get('name', '') else "note"
            }
            notes_list.append(note_info)
        
        logger.info(f"Found {len(notes_list)} notes matching '{query}'")
        return {
            "notes": notes_list,
            "count": len(notes_list),
            "query": query,
            "service": "drive"
        }
        
    except Exception as e:
        logger.error(f"Error searching notes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {str(e)}")

# ============================================================================
# UNIFIED ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with service overview"""
    authenticated = service_manager.is_authenticated()
    auth_status = "✅ Authenticated" if authenticated else "❌ Not Authenticated"
    
    return {
        "message": "MCP Server - Unified Gmail, Calendar, Contacts & YouTube for Voice AI Agent",
        "version": "1.0.0",
        "authentication": auth_status,
        "services": {
            "gmail": {
                "endpoints": ["/gmail/recent", "/gmail/unread"],
                "authenticated": authenticated
            },
            "calendar": {
                "endpoints": ["/calendar/today", "/calendar/upcoming", "/calendar/list"],
                "authenticated": authenticated
            },
            "contacts": {
                "endpoints": ["/contacts/all", "/contacts/search", "/profile/me"],
                "authenticated": authenticated
            },
            "youtube": {
                "endpoints": ["/youtube/channel", "/youtube/videos", "/youtube/search", "/youtube/playlists"],
                "authenticated": authenticated
            },
            "notes": {
                "endpoints": ["/notes/all", "/notes/create", "/lists/create", "/notes/search"],
                "authenticated": authenticated
            }
        },
        "auth_endpoints": {
            "login": "/auth/login",
            "status": "/auth/status",
            "callback": "/auth/callback"
        }
    }

@app.get("/status")
async def service_status():
    """Comprehensive service status"""
    authenticated = service_manager.is_authenticated()
    
    status = {
        "server": "MCP Server",
        "port": 8080,
        "authenticated": authenticated,
        "services": {
            "gmail": {
                "available": service_manager.get_gmail_service() is not None,
                "endpoints": 2
            },
            "calendar": {
                "available": service_manager.get_calendar_service() is not None,
                "endpoints": 3
            },
            "contacts": {
                "available": service_manager.get_people_service() is not None,
                "endpoints": 5
            },
            "youtube": {
                "available": service_manager.get_youtube_service() is not None,
                "endpoints": 4
            },
            "drive": {
                "available": service_manager.get_drive_service() is not None,
                "endpoints": 4
            },
            "docs": {
                "available": service_manager.get_docs_service() is not None,
                "endpoints": 4
            }
        },
        "total_endpoints": 25,
        "auth_required": not authenticated
    }
    
    return status

# ============================================================================
# UNIFIED ENDPOINTS
# ============================================================================

@app.get("/notes")
async def get_notes():
    """Get all notes - unified endpoint"""
    return await get_all_notes()

@app.post("/notes")
async def create_note_unified(request: dict):
    """Create a note - unified endpoint"""
    return await create_note(request)

@app.get("/lists")
async def get_lists():
    """Get all shopping lists - unified endpoint"""
    # Filter for shopping lists specifically
    all_notes = await get_all_notes()
    shopping_lists = [note for note in all_notes["notes"] if note["type"] == "shopping_list"]
    return {
        "lists": shopping_lists,
        "count": len(shopping_lists),
        "service": "drive"
    }

@app.post("/lists")
async def create_list_unified(request: dict):
    """Create a shopping list - unified endpoint"""
    return await create_shopping_list(request)

@app.get("/search")
async def search_unified(query: str = ""):
    """Search notes and lists - unified endpoint"""
    return await search_notes(query)

if __name__ == "__main__":
    logger.info("🚀 Starting MCP Server (Gmail + Calendar + Contacts + YouTube + Drive) on http://0.0.0.0:8080")
    logger.info("🔐 Google OAuth2 authentication enabled for all services")
    logger.info("📧 Gmail endpoints: /gmail/recent, /gmail/unread")
    logger.info("📅 Calendar endpoints: /calendar/today, /calendar/upcoming, /calendar/list, /calendar/create_event")
    logger.info("👥 Contacts endpoints: /contacts/all, /contacts/search, /contacts/find, /contacts/emails, /profile/me")
    logger.info("🎥 YouTube endpoints: /youtube/channel, /youtube/videos, /youtube/search, /youtube/playlists")
    logger.info("📝 Drive endpoints: /notes/all, /notes/create, /lists/create, /notes/search")
    logger.info("🔑 Visit http://localhost:8080/auth/login to authenticate")
    logger.info("❌ NO MOCK DATA - Real Google services only!")
    uvicorn.run(app, host="0.0.0.0", port=8080)
