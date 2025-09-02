"""
June Voice AI - Clean Simple Implementation
Matches GitHub repository patterns for Android app compatibility
"""

import os
import json
import base64
import tempfile
import logging
import requests
import aiohttp
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
JUNE_VOICE = "female_1"
MCP_SERVER_URL = "http://localhost:8080"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple response creators (GitHub style)
def create_speak_response(message: str, voice: str = JUNE_VOICE):
    """Create a simple speak response like GitHub implementation"""
    return {
        "action": "speak",
        "message": message,
        "voice": voice
    }

def create_call_response(phone_number: str, contact_name: str = None):
    """Create a simple call response like GitHub implementation"""
    if contact_name:
        message = f"Calling {contact_name}"
    else:
        message = f"Calling {phone_number}"
    
    return {
        "action": "call",
        "message": message,
        "phone_number": phone_number,
        "contact_name": contact_name
    }

def create_email_response(email_address: str, subject: str = None, contact_name: str = None):
    """Create a simple email response like GitHub implementation"""
    message = f"Opening email to {contact_name or email_address}"
    return {
        "action": "email",
        "message": message,
        "email_address": email_address,
        "subject": subject,
        "contact_name": contact_name
    }

def create_calendar_response(action_type: str, data: dict = None):
    """Create a simple calendar response like GitHub implementation"""
    if action_type == "open":
        return {
            "action": "calendar",
            "message": "Opening calendar",
            "calendar_action": "open"
        }
    elif action_type == "create_event":
        return {
            "action": "calendar",
            "message": "Creating calendar event",
            "calendar_action": "create",
            "event_data": data or {}
        }
    else:
        return {
            "action": "calendar", 
            "message": "Opening calendar",
            "calendar_action": "open"
        }

# Simple intent classification
def classify_intent(text: str):
    """Simple intent classification like GitHub"""
    text_lower = text.lower()
    
    # Call/Dial patterns
    if any(word in text_lower for word in ["call", "dial", "phone"]):
        return "call"
    
    # Email patterns  
    if any(word in text_lower for word in ["email", "compose", "send email"]):
        return "email"
        
    # Calendar patterns
    if any(word in text_lower for word in ["schedule", "meeting", "appointment", "calendar"]):
        return "calendar"
        
    # SMS patterns
    if any(word in text_lower for word in ["text", "sms", "message"]):
        return "sms"
    
    # Notes patterns (including document drafting like resumes)
    if any(word in text_lower for word in ["note", "notes", "reminder", "write down", "remember", "jot down", "draft", "resume", "document", "write", "create document"]):
        return "notes"
    
    # List patterns
    if any(word in text_lower for word in ["list", "shopping", "todo", "grocery", "checklist", "add to list", "shop", "buy", "purchase", "store", "market"]):
        return "list"
    
    return "general"

# Handler functions (simple GitHub style)
async def handle_calling_request(user_query: str):
    """Simple calling like GitHub implementation"""
    logger.info(f"Processing calling request: {user_query}")
    
    # Extract phone number or contact name
    words = user_query.split()
    for word in words:
        if word.isdigit() or any(c.isdigit() for c in word):
            # Found a number - direct dial
            phone_number = ''.join(c for c in word if c.isdigit() or c in '-+()' )
            return create_call_response(phone_number)
    
    # No number found - assume contact name
    # Extract name after "call" or "dial"
    text_lower = user_query.lower()
    if "call " in text_lower:
        name = user_query.lower().split("call ", 1)[1].strip()
        return create_call_response("", name)
    elif "dial " in text_lower:
        name = user_query.lower().split("dial ", 1)[1].strip() 
        return create_call_response("", name)
    
    return create_speak_response("Who would you like to call?")

async def handle_gmail_query(user_query: str):
    """Enhanced Gmail handling with MCP server integration"""
    logger.info(f"Processing Gmail query: {user_query}")
    
    text_lower = user_query.lower()
    
    # Check if user wants email summary or specific email actions
    if any(word in text_lower for word in ["summarize", "summary", "check email", "read email"]):
        try:
            # Try to get email summary from MCP server
            logger.info("Requesting email summary from MCP server")
            mcp_response = requests.get(
                "http://localhost:8080/gmail/recent",
                timeout=10
            )
            
            if mcp_response.status_code == 200:
                result = mcp_response.json()
                logger.info(f"MCP email response: {result}")
                
                emails = result.get("emails", [])
                if emails:
                    email_count = len(emails)
                    if email_count == 1:
                        return create_speak_response(f"You have {email_count} recent email. The latest is from {emails[0].get('sender', 'unknown')} with subject '{emails[0].get('subject', 'no subject')}'")
                    else:
                        return create_speak_response(f"You have {email_count} recent emails. The latest is from {emails[0].get('sender', 'unknown')} with subject '{emails[0].get('subject', 'no subject')}'")
                else:
                    return create_speak_response("No recent emails found.")
            else:
                logger.error(f"MCP server error: {mcp_response.status_code}")
                return create_speak_response("Gmail service returned an error.")
                
        except requests.RequestException as e:
            logger.error(f"MCP server connection error: {e}")
            return create_speak_response("Cannot connect to Gmail service. Make sure MCP server is running.")
    
    # Check if user wants to send an email
    elif any(word in text_lower for word in ["send email", "email", "compose", "write to"]):
        return create_email_response("", None, None)
    
    # Default to opening Gmail
    return {
        "action": "open_app",
        "message": "Opening Gmail",
        "app_name": "gmail"
    }

async def extract_meeting_details(user_query: str):
    """Extract meeting details from natural language using AI parsing"""
    import re
    from datetime import datetime, timedelta
    
    query_lower = user_query.lower()
    
    # Extract title/purpose
    title = "Meeting"
    if "meeting" in query_lower:
        title = "Meeting"
    elif "appointment" in query_lower:
        title = "Appointment"
    elif "call" in query_lower:
        title = "Call"
    
    # Extract attendee names
    attendee = ""
    attendee_emails = []
    
    # Look for names after "with"
    with_match = re.search(r'with\s+([a-zA-Z\s]+?)(?:\s+for|\s+at|\s+tomorrow|\s*$)', query_lower)
    if with_match:
        attendee = with_match.group(1).strip().title()
        title = f"Meeting with {attendee}"
    
    # Extract duration
    duration_minutes = 30  # default
    duration_match = re.search(r'(\d+)\s*minutes?', query_lower)
    if duration_match:
        duration_minutes = int(duration_match.group(1))
    elif re.search(r'(\d+)\s*hours?', query_lower):
        hour_match = re.search(r'(\d+)\s*hours?', query_lower)
        duration_minutes = int(hour_match.group(1)) * 60
    
    # Extract time
    now = datetime.now()
    
    # Check for "tomorrow"
    if "tomorrow" in query_lower:
        base_date = now + timedelta(days=1)
    else:
        base_date = now
    
    # Extract time (2 p.m., 2pm, 14:00, etc.)
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)', query_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3).lower()
        
        # Convert to 24-hour format
        if 'p' in period and hour != 12:
            hour += 12
        elif 'a' in period and hour == 12:
            hour = 0
            
        start_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Default to next hour if no time specified
        start_time = base_date.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Format times for Google Calendar API (ISO format)
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()
    
    # Create readable time for speech
    readable_time = start_time.strftime("%A at %I:%M %p")
    if start_time.date() == (now + timedelta(days=1)).date():
        readable_time = f"tomorrow at {start_time.strftime('%I:%M %p')}"
    elif start_time.date() == now.date():
        readable_time = f"today at {start_time.strftime('%I:%M %p')}"
    
    return {
        "title": title,
        "start_time": start_iso,
        "end_time": end_iso,
        "attendee": attendee,
        "attendees": attendee_emails,
        "duration_minutes": duration_minutes,
        "readable_time": readable_time,
        "description": f"Scheduled via voice command: {user_query}"
    }

async def call_mcp_calendar_create(meeting_details: dict):
    """Call MCP server to create calendar event"""
    
    try:
        # Prepare payload for MCP server
        payload = {
            "title": meeting_details["title"],
            "start_time": meeting_details["start_time"],
            "end_time": meeting_details["end_time"],
            "description": meeting_details["description"],
            "attendees": meeting_details["attendees"]
        }
        
        # Add location if attendee is specified
        if meeting_details.get("attendee"):
            payload["location"] = f"Meeting with {meeting_details['attendee']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8080/calendar/create_event",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"MCP calendar response: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP calendar error {response.status}: {error_text}")
                    return {"success": False, "detail": f"HTTP {response.status}: {error_text}"}
                    
    except Exception as e:
        logger.error(f"Error calling MCP calendar service: {e}")
        return {"success": False, "detail": str(e)}

async def handle_meeting_scheduling(user_query: str):
    """AI-powered calendar handling with Google Calendar integration"""
    logger.info(f"Calendar processing: {user_query}")
    
    # Check if this is a scheduling request
    if any(keyword in user_query.lower() for keyword in ["schedule", "meeting", "appointment", "book", "create"]):
        try:
            # Extract meeting details from natural language
            meeting_details = await extract_meeting_details(user_query)
            
            # Call MCP server to create the calendar event
            mcp_response = await call_mcp_calendar_create(meeting_details)
            
            if mcp_response.get("success"):
                logger.info(f"✅ Calendar event created successfully: {meeting_details.get('title')}")
                return {
                    "action": "calendar",
                    "message": f"Meeting scheduled: {meeting_details.get('title')} at {meeting_details.get('start_time')}",
                    "calendar_action": "create_success",
                    "event_data": mcp_response,
                    "speak": f"I've scheduled your meeting with {meeting_details.get('attendee', '')} for {meeting_details.get('readable_time', 'the requested time')}."
                }
            else:
                logger.error(f"❌ Failed to create calendar event: {mcp_response}")
                return {
                    "action": "calendar", 
                    "message": "Failed to create calendar event",
                    "calendar_action": "create_failed",
                    "error": mcp_response.get("detail", "Unknown error"),
                    "speak": "Sorry, I couldn't create the calendar event. Please try again."
                }
                
        except Exception as e:
            logger.error(f"Error in calendar processing: {e}")
            return {
                "action": "calendar",
                "message": "Error processing calendar request",
                "calendar_action": "error",
                "speak": "Sorry, I had trouble processing your calendar request."
            }
    
    # Default to opening calendar
    return create_calendar_response("open")

async def handle_text_message_request(user_query: str):
    """Simple SMS handling like GitHub implementation"""
    logger.info(f"Processing SMS request: {user_query}")
    
    return {
        "action": "text",
        "message": "Opening messages",
        "recipient": "",
        "text_content": ""
    }

async def handle_notes_request(user_query: str):
    """Handle notes creation requests including document drafting"""
    logger.info(f"Processing notes request: {user_query}")
    
    try:
        # Extract note content from the query
        text_lower = user_query.lower()
        
        # Check if this is a document drafting request (like resume)
        is_document_draft = any(word in text_lower for word in ["draft", "resume", "document", "create document"])
        
        # Find the note content after trigger words
        trigger_words = ["note", "notes", "reminder", "write down", "remember", "jot down", "draft", "create"]
        note_content = user_query
        
        for trigger in trigger_words:
            if trigger in text_lower:
                # Try to find content after the trigger word
                parts = user_query.lower().split(trigger, 1)
                if len(parts) > 1:
                    # Clean up the content
                    note_content = parts[1].strip()
                    # Remove common prefixes
                    for prefix in ["a", "an", "the", "that", "to", "this", ":"]:
                        if note_content.startswith(prefix):
                            note_content = note_content[len(prefix):].strip()
                    break
        
        # Special handling for resume drafting
        if is_document_draft and "resume" in text_lower:
            note_content = """RESUME DRAFT

[Your Name]
[Your Address]
[Your Phone Number]
[Your Email]

OBJECTIVE
[Brief statement about your career goals and what you bring to the role]

EXPERIENCE
[Company Name] - [Job Title] ([Start Date] - [End Date])
• [Achievement or responsibility]
• [Achievement or responsibility]
• [Achievement or responsibility]

EDUCATION
[University/School Name]
[Degree] in [Field of Study] ([Graduation Year])

SKILLS
• [Skill 1]
• [Skill 2]
• [Skill 3]

ACHIEVEMENTS
• [Notable achievement]
• [Notable achievement]

---
Note: Please fill in the bracketed sections with your specific information."""
            title = f"Resume Draft - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        else:
            if not note_content or note_content == user_query:
                # Fallback to extracting meaningful content
                words = user_query.split()
                if len(words) > 2:
                    note_content = " ".join(words[2:])  # Skip first two words usually trigger
                else:
                    note_content = user_query
            title = f"Voice Note - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create note via MCP server
        mcp_data = {
            "title": title,
            "content": note_content
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{MCP_SERVER_URL}/notes/create", json=mcp_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "resume" in text_lower:
                        speak_message = "I've created a resume draft template for you in your notes. You can fill in your specific details."
                    else:
                        speak_message = f"I've created a note: {note_content}"
                    
                    return {
                        "action": "notes",
                        "message": f"Created {'resume draft' if 'resume' in text_lower else 'note'}: {note_content[:50]}...",
                        "note_id": result.get("id", ""),
                        "speak": speak_message
                    }
                else:
                    logger.error(f"MCP server error: {response.status}")
                    return {
                        "action": "notes",
                        "message": "Error creating note",
                        "speak": "Sorry, I had trouble creating your note."
                    }
                    
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return {
            "action": "notes", 
            "message": "Error creating note",
            "speak": "Sorry, I had trouble creating your note."
        }

async def handle_list_request(user_query: str):
    """Handle shopping list and todo list requests"""
    logger.info(f"Processing list request: {user_query}")
    
    try:
        # Extract list items from the query
        text_lower = user_query.lower()
        
        # Determine list type
        list_type = "Shopping List"
        if any(word in text_lower for word in ["todo", "task", "checklist"]):
            list_type = "Todo List"
        elif any(word in text_lower for word in ["shopping", "grocery", "buy"]):
            list_type = "Shopping List"
        
        # Extract items
        items = []
        
        # Look for items - handle different sentence structures
        items = []
        list_content = ""
        
        # Pattern 1: "Add X, Y, Z to [shopping/grocery] list"
        if "to" in text_lower and any(word in text_lower for word in ["shopping list", "grocery list", "todo list", "list"]):
            # Find items between "add" and "to"
            if text_lower.startswith("add "):
                parts = text_lower.split(" to ", 1)
                if len(parts) > 1:
                    # Get everything after "add " and before " to"
                    list_content = parts[0][4:].strip()  # Remove "add " prefix
        
        # Pattern 2: "Shopping/grocery list: X, Y, Z" or "Add to list: X, Y, Z"
        elif ":" in user_query:
            parts = user_query.split(":", 1)
            if len(parts) > 1:
                list_content = parts[1].strip()
        
        # Pattern 3: Look for items after trigger words
        if not list_content:
            trigger_words = ["add to list", "shopping list", "grocery list", "todo list", "checklist", "shopping", "grocery", "purchase", "store", "market", "buy", "shop", "add", "list"]
            
            for trigger in trigger_words:
                if trigger in text_lower:
                    parts = user_query.lower().split(trigger, 1)
                    if len(parts) > 1:
                        list_content = parts[1].strip()
                        # Remove common prefixes and words
                        for prefix in ["of", "for", ":", "-", "to", "the", "my", "some"]:
                            if list_content.startswith(prefix + " "):
                                list_content = list_content[len(prefix):].strip()
                        break
        
        # Parse items (handle multiple separators in sequence)
        if list_content:
            # First, normalize the text - replace multiple separators with commas
            normalized_content = list_content
            # Replace " and " with ", " 
            normalized_content = normalized_content.replace(" and ", ", ")
            # Replace " & " with ", "
            normalized_content = normalized_content.replace(" & ", ", ")
            # Replace "; " with ", "
            normalized_content = normalized_content.replace(";", ",")
            
            # Now split by comma
            raw_items = normalized_content.split(",")
            
            # Clean up items
            items = [item.strip() for item in raw_items if item.strip()]
        
        if not items:
            items = ["Item from voice note"]
        
        # Create list via MCP server
        mcp_data = {
            "title": f"{list_type} - {datetime.now().strftime('%Y-%m-%d')}",
            "items": items,
            "append": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{MCP_SERVER_URL}/lists/create", json=mcp_data) as response:
                if response.status == 200:
                    result = await response.json()
                    items_text = ", ".join(items)
                    return {
                        "action": "list",
                        "message": f"Added to {list_type.lower()}: {items_text}",
                        "list_id": result.get("id", ""),
                        "items": items,
                        "speak": f"I've added {items_text} to your {list_type.lower()}"
                    }
                else:
                    logger.error(f"MCP server error: {response.status}")
                    return {
                        "action": "list",
                        "message": "Error creating list",
                        "speak": "Sorry, I had trouble creating your list."
                    }
                    
    except Exception as e:
        logger.error(f"Error creating list: {e}")
        return {
            "action": "list",
            "message": "Error creating list", 
            "speak": "Sorry, I had trouble creating your list."
        }

# Main processing function
async def process_query(text: str):
    """Process user query - simple routing like GitHub"""
    intent = classify_intent(text)
    
    logger.info(f"Classified intent: {intent}")
    
    if intent == "call":
        return await handle_calling_request(text)
    elif intent == "email":
        return await handle_gmail_query(text)
    elif intent == "calendar":
        return await handle_meeting_scheduling(text)
    elif intent == "sms":
        return await handle_text_message_request(text)
    elif intent == "notes":
        return await handle_notes_request(text)
    elif intent == "list":
        return await handle_list_request(text)
    else:
        # General response
        return create_speak_response("I'm here to help with calls, emails, calendar, messages, notes, and lists.")

# Main endpoints
@app.post("/query")
async def process_query_endpoint(request: dict):
    """Simple text query endpoint for testing"""
    try:
        text = request.get("text", "")
        logger.info(f"📝 Text query: {text}")
        result = await process_query(text)
        return result
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        return {"error": str(e), "action": "speak", "message": "Sorry, there was an error processing your request."}

@app.post("/voice")
async def process_voice(request: Request):
    """Main voice processing endpoint with flexible multipart/form-data support"""
    try:
        audio_data = None
        
        # Check if this is a multipart request
        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            # Handle multipart form-data request (from Android app)
            form = await request.form()
            logger.info(f"Received multipart form with fields: {list(form.keys())}")
            
            # Try different possible field names for the audio
            audio_file = None
            for field_name in ["audio", "file", "voice", "sound", "recording"]:
                if field_name in form:
                    audio_file = form[field_name]
                    logger.info(f"Found audio in field: {field_name}")
                    break
            
            if audio_file and hasattr(audio_file, 'read'):
                audio_data = await audio_file.read()
                logger.info(f"Multipart audio size: {len(audio_data)} bytes")
            else:
                logger.error(f"No valid audio file found. Form fields: {list(form.keys())}")
                return create_speak_response("No audio file received.")
        else:
            # Handle JSON request with base64 encoded audio (fallback)
            try:
                data = await request.json()
                audio_data = base64.b64decode(data["audio"])
                logger.info(f"JSON audio size: {len(audio_data)} bytes")
            except Exception as json_error:
                logger.error(f"Failed to parse JSON: {json_error}")
                return create_speak_response("Invalid audio format.")
        
        if not audio_data:
            return create_speak_response("No audio data received.")
        
        # Save audio to temporary file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_audio.write(audio_data)
        temp_audio.close()
        logger.info(f"Audio file saved: {temp_audio.name}, size: {len(audio_data)} bytes")
        
        try:
            # Transcribe with Whisper
            with open(temp_audio.name, "rb") as audio_file:
                whisper_response = requests.post(
                    "http://localhost:5004/transcribe",
                    files={"audio": ("audio.wav", audio_file, "audio/wav")},
                    timeout=30
                )
            
            if whisper_response.status_code == 200:
                transcription = whisper_response.json()["text"]
                logger.info(f"🎤 Voice transcribed: '{transcription}'")
                
                # Process query
                result = await process_query(transcription)
                return result
            else:
                logger.error(f"Whisper service error: {whisper_response.status_code}")
                return create_speak_response("Speech recognition service unavailable.")
            
        except requests.RequestException as e:
            logger.error(f"Error connecting to Whisper service: {e}")
            return create_speak_response("Speech recognition service unavailable.")
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return create_speak_response("Sorry, I couldn't process your request.")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_audio.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in voice endpoint: {e}")
        return create_speak_response("Sorry, there was an error.")

@app.get("/")
async def root():
    return {"message": "June Voice AI - Simple Implementation"}

@app.post("/voice_json")
async def process_voice_json(request: Request):
    """Voice processing endpoint for JSON requests with base64 audio"""
    try:
        data = await request.json()
        audio_data = base64.b64decode(data["audio"])
        logger.info(f"JSON audio size: {len(audio_data)} bytes")
        
        # Save audio to temporary file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_audio.write(audio_data)
        temp_audio.close()
        logger.info(f"Audio file saved: {temp_audio.name}, size: {len(audio_data)} bytes")
        
        try:
            # Transcribe with Whisper
            with open(temp_audio.name, "rb") as audio_file:
                whisper_response = requests.post(
                    "http://localhost:5004/transcribe",
                    files={"audio": ("audio.wav", audio_file, "audio/wav")},
                    timeout=30
                )
            
            if whisper_response.status_code == 200:
                transcription = whisper_response.json()["text"]
                logger.info(f"🎤 Voice transcribed: '{transcription}'")
                
                # Process query
                result = await process_query(transcription)
                return result
            else:
                logger.error(f"Whisper service error: {whisper_response.status_code}")
                return create_speak_response("Speech recognition service unavailable.")
            
        except requests.RequestException as e:
            logger.error(f"Error connecting to Whisper service: {e}")
            return create_speak_response("Speech recognition service unavailable.")
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return create_speak_response("Sorry, I couldn't process your request.")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_audio.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in voice_json endpoint: {e}")
        return create_speak_response("Sorry, there was an error.")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting June Voice AI - Simple Implementation on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)
