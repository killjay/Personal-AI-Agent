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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
JUNE_VOICE = "female_1"

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
    """Simple Gmail handling like GitHub implementation"""
    logger.info(f"Processing Gmail query: {user_query}")
    
    text_lower = user_query.lower()
    
    # Check if user wants to send an email
    if any(word in text_lower for word in ["send email", "email", "compose", "write to"]):
        return create_email_response("", None, None)
    
    # Default to opening Gmail
    return {
        "action": "open_app",
        "message": "Opening Gmail",
        "app_name": "gmail"
    }

async def handle_meeting_scheduling(user_query: str):
    """Simple calendar handling like GitHub implementation"""
    logger.info(f"Calendar processing: {user_query}")
    
    # Simple calendar handling
    if any(keyword in user_query.lower() for keyword in ["schedule", "meeting", "appointment", "book", "create"]):
        # Extract basic info for Android app
        event_data = {}
        if "tomorrow" in user_query.lower():
            event_data["time"] = "tomorrow"
        elif any(time in user_query.lower() for time in ["am", "pm", ":"]):
            event_data["time"] = "today"
        
        return create_calendar_response("create_event", event_data)
    
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
    else:
        # General response
        return create_speak_response("I'm here to help with calls, emails, calendar, and messages.")

# Main endpoints
@app.post("/voice")
async def process_voice(request: Request):
    """Main voice processing endpoint"""
    try:
        data = await request.json()
        audio_data = base64.b64decode(data["audio"])
        
        # Save audio to temporary file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_audio.write(audio_data)
        temp_audio.close()
        logger.info(f"Audio file saved: {temp_audio.name}, size: {len(audio_data)} bytes")
        
        try:
            # Transcribe with Whisper
            whisper_response = requests.post(
                "http://localhost:5004/transcribe",
                files={"audio": ("audio.wav", open(temp_audio.name, "rb"), "audio/wav")}
            )
            transcription = whisper_response.json()["text"]
            logger.info(f"🎤 Voice transcribed: '{transcription}'")
            
            # Process query
            result = await process_query(transcription)
            
            return result
            
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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting June Voice AI - Simple Implementation on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)
