import os
import whisper
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import requests
import tempfile
import logging
import json
import numpy as np
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = "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"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Claude Model Configuration - Three-Tier AI System (All using Haiku for cost efficiency)
CLAUDE_HAIKU = "claude-3-haiku-20240307"      # Router AI - Fast query analysis
CLAUDE_SONNET = "claude-3-haiku-20240307"     # Productivity AI - Fast business task handling (using Haiku)
CLAUDE_OPUS = "claude-3-haiku-20240307"       # Content AI - Fast personal assistance (using Haiku)

# Voice Configuration - June uses Sarah (female_1) voice
JUNE_VOICE = "female_1"  # Sarah - Female US English voice

def route_to_ai_specialist(user_query: str) -> str:
    """Router AI: Decision model that determines which specialized AI should handle the query"""
    try:
        logger.info(f"🎯 ROUTER AI DECISION MODEL analyzing: '{user_query}'")
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        router_prompt = f"""You are the ROUTER AI - the decision model for June Voice Assistant. 

TASK: Analyze this user query and decide which specialized AI should handle it: "{user_query}"

AVAILABLE SPECIALISTS:

🏢 PRODUCTIVITY AI (Sonnet Model) - Business & Communication Tasks:
- Gmail, email operations (sending, checking, composing)
- Phone calls and dialing (calling contacts, dialing numbers)
- Calendar meetings and scheduling (appointments, meetings, events)
- Document creation (resumes, letters, proposals, reports)
- Professional business tasks requiring high accuracy

📝 CONTENT AI (Opus Model) - Personal & Creative Tasks:
- Notes and reminders (taking notes, remembering things)
- Shopping/grocery lists (adding items, managing lists)
- Creative writing and personal content
- General conversation and questions
- Personal organization tasks

DECISION RULES:
- Email/Gmail queries → "productivity"
- Calling/dialing queries → "productivity" 
- Calendar/meeting queries → "productivity"
- Document creation → "productivity"
- Notes/reminders → "content"
- Shopping lists → "content"
- General questions → "content"
- Creative tasks → "content"

Respond with JSON only:
{{
  "specialist": "productivity|content",
  "reasoning": "Brief explanation of why this specialist was chosen",
  "confidence": 0.95,
  "detected_intent": "brief description of what user wants"
}}"""

        router_data = {
            "model": CLAUDE_HAIKU,  # Fast routing decisions
            "max_tokens": 300,
            "messages": [{"role": "user", "content": router_prompt}]
        }
        
        logger.info("🤖 Sending query to Router AI decision model...")
        router_response = requests.post(CLAUDE_API_URL, headers=headers, json=router_data, timeout=30)
        
        if router_response.status_code == 200:
            router_result = router_response.json()
            extracted_text = router_result["content"][0]["text"].strip()
            
            try:
                routing_data = json.loads(extracted_text)
                specialist = routing_data.get("specialist", "content")
                reasoning = routing_data.get("reasoning", "Default routing")
                confidence = routing_data.get("confidence", 0.8)
                detected_intent = routing_data.get("detected_intent", "Unknown")
                
                logger.info(f"🎯 ROUTER AI DECISION:")
                logger.info(f"   → Specialist: {specialist.upper()} AI")
                logger.info(f"   → Confidence: {confidence}")
                logger.info(f"   → Intent: {detected_intent}")
                logger.info(f"   → Reasoning: {reasoning}")
                
                return specialist
                
            except json.JSONDecodeError:
                logger.error(f"Router AI JSON decode error: {extracted_text}")
                logger.info("🎯 ROUTER AI: Defaulting to CONTENT AI")
                return "content"  # Default fallback
        else:
            logger.error(f"Router AI error: {router_response.status_code}")
            logger.info("🎯 ROUTER AI: Defaulting to CONTENT AI")
            return "content"  # Default fallback
            
    except Exception as e:
        logger.error(f"Router AI error: {e}")
        logger.info("🎯 ROUTER AI: Defaulting to CONTENT AI")
        return "content"  # Default fallback

def get_claude_model_for_specialist(specialist: str) -> str:
    """Get the appropriate Claude model for the chosen AI specialist"""
    if specialist == "productivity":
        logger.info("🏢 Using PRODUCTIVITY AI (Haiku) for business tasks")
        return CLAUDE_HAIKU
    elif specialist == "content":
        logger.info("📝 Using CONTENT AI (Haiku) for personal/creative tasks")
        return CLAUDE_HAIKU
    else:
        logger.info("📝 Using CONTENT AI (Haiku) as default")
        return CLAUDE_HAIKU

app = FastAPI()

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

def create_notification_response(message: str, notification_type: str = "success"):
    """Create a notification response"""
    return {
        "action": "notification",
        "message": message,
        "type": notification_type
    }

def create_action_response(action: str, message: str, data: dict = None):
    """Create an action response"""
    return {
        "action": action,
        "message": message,
        "data": data or {}
    }

def create_calendar_response(action_type: str, event_data: dict = None):
    """Create a response for calendar actions"""
    if action_type == "open":
        message = "Opening calendar..."
        return create_action_response("open_calendar", message)
    elif action_type == "create_event":
        message = f"Creating calendar event: {event_data.get('summary', 'New Event')}"
        return create_action_response("create_calendar_event", message, event_data)
    else:
        message = "Showing calendar information..."
        return create_action_response("show_calendar", message, event_data)

# Load model with error handling
try:
    model = whisper.load_model("small")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None

@app.post("/voice")
async def process_voice(file: UploadFile = File(...)):
    try:
        # Save uploaded file with proper extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            audio_path = temp_file.name

        logger.info(f"Audio file saved: {audio_path}, size: {len(content)} bytes")

        if model is None:
            return JSONResponse({"action": "error", "message": "Whisper model not available"}, status_code=500)

        # Transcribe audio with better error handling
        try:
            audio = whisper.load_audio(audio_path)
            
            # Add padding if audio is too short
            if len(audio) < 16000:  # Less than 1 second at 16kHz
                audio = np.pad(audio, (0, 16000 - len(audio)), mode='constant')
            
            # Use the loaded model for transcription
            result = model.transcribe(audio, fp16=False)
            text = result["text"].strip()
            
        except Exception as audio_error:
            logger.error(f"Audio processing error: {audio_error}")
            try:
                # Fallback: try loading without whisper preprocessing
                result = model.transcribe(audio_path, fp16=False)
                text = result["text"].strip()
            except Exception as fallback_error:
                logger.error(f"Fallback transcription failed: {fallback_error}")
                # Clean up temp file
                try:
                    os.unlink(audio_path)
                except:
                    pass
                return JSONResponse({"action": "error", "message": f"Voice transcription failed - audio format may not be supported. Install FFmpeg for better compatibility."}, status_code=500)

        # Clean up temp file
        try:
            os.unlink(audio_path)
        except:
            pass

        if not text:
            return JSONResponse({"action": "error", "message": "No speech detected"})

        logger.info(f"🎤 Voice transcribed: '{text}'")

        # 🎯 THREE-TIER AI ROUTING SYSTEM
        # Step 1: Router AI (Decision Model) determines which specialist should handle the query
        logger.info("🤖 Router AI: Analyzing voice query to determine specialist...")
        specialist = route_to_ai_specialist(text)
        
        if specialist == "productivity":
            # 🏢 PRODUCTIVITY AI handles business/professional tasks
            logger.info("🏢 Routing to PRODUCTIVITY AI for business tasks")
            return await handle_productivity_tasks(text)
        else:
            # 📝 CONTENT AI handles personal/creative tasks
            logger.info("📝 Routing to CONTENT AI for personal tasks")
            return await handle_content_tasks(text)

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return JSONResponse({"action": "error", "message": f"Failed to process voice: {str(e)}"}, status_code=500)

# 🏢 PRODUCTIVITY AI SPECIALIST - Handles business and professional tasks
async def handle_productivity_tasks(user_query: str):
    """Productivity AI: Handle business tasks like email, calls, calendar, documents"""
    try:
        logger.info(f"🏢 PRODUCTIVITY AI processing: {user_query}")
        
        # Use Sonnet model for precise business task classification
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        productivity_prompt = f"""You are the PRODUCTIVITY AI specialist for June Voice Assistant. Analyze this business/professional query: "{user_query}"

PRODUCTIVITY TASKS YOU HANDLE:
1. "calling" - Phone calls and dialing
2. "gmail" - Email operations
3. "calendar" - Meeting scheduling and calendar
4. "documents" - Document creation (resumes, letters, proposals)
5. "texting" - Text messages and SMS

Classify the task and extract relevant information.

Respond with JSON only:
{{
  "task_type": "calling|gmail|calendar|documents|texting",
  "confidence": 0.95
}}"""

        productivity_data = {
            "model": get_claude_model_for_specialist("productivity"),
            "max_tokens": 150,
            "messages": [{"role": "user", "content": productivity_prompt}]
        }
        
        response = requests.post(CLAUDE_API_URL, headers=headers, json=productivity_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            extracted_text = result["content"][0]["text"].strip()
            
            try:
                task_data = json.loads(extracted_text)
                task_type = task_data.get("task_type", "gmail")
                
                # Route to specific productivity handler
                if task_type == "calling":
                    return await handle_calling_request(user_query)
                elif task_type == "gmail":
                    return await handle_gmail_query(user_query)
                elif task_type == "calendar":
                    return await handle_meeting_scheduling(user_query)
                elif task_type == "documents":
                    return await handle_document_creation(user_query)
                elif task_type == "texting":
                    return await handle_text_message_request(user_query)
                else:
                    return await handle_gmail_query(user_query)  # Default
                    
            except json.JSONDecodeError:
                return await handle_gmail_query(user_query)  # Default fallback
        else:
            return await handle_gmail_query(user_query)  # Default fallback
            
    except Exception as e:
        logger.error(f"Productivity AI error: {e}")
        return await handle_gmail_query(user_query)  # Default fallback

# 📝 CONTENT AI SPECIALIST - Handles personal and creative tasks
async def handle_content_tasks(user_query: str):
    """Content AI: Handle personal tasks like notes, lists, creative content"""
    try:
        logger.info(f"📝 CONTENT AI processing: {user_query}")
        
        # Use Opus model for creative and personal task classification
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        content_prompt = f"""You are the CONTENT AI specialist for June Voice Assistant. Analyze this personal/creative query: "{user_query}"

CONTENT TASKS YOU HANDLE:
1. "notes" - Taking notes and reminders
2. "shopping" - Shopping and grocery lists
3. "youtube" - YouTube-related tasks
4. "general" - General conversation and questions

Classify the task and extract relevant information.

Respond with JSON only:
{{
  "task_type": "notes|shopping|youtube|general",
  "confidence": 0.95
}}"""

        content_data = {
            "model": get_claude_model_for_specialist("content"),
            "max_tokens": 150,
            "messages": [{"role": "user", "content": content_prompt}]
        }
        
        response = requests.post(CLAUDE_API_URL, headers=headers, json=content_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            extracted_text = result["content"][0]["text"].strip()
            
            try:
                task_data = json.loads(extracted_text)
                task_type = task_data.get("task_type", "general")
                
                # Route to specific content handler
                if task_type == "notes":
                    return await handle_notes_request(user_query)
                elif task_type == "shopping":
                    return await handle_shopping_list_request(user_query)
                elif task_type == "youtube":
                    return await handle_youtube_query(user_query)
                else:
                    return await handle_general_query(user_query)
                    
            except json.JSONDecodeError:
                return await handle_general_query(user_query)  # Default fallback
        else:
            return await handle_general_query(user_query)  # Default fallback
            
    except Exception as e:
        logger.error(f"Content AI error: {e}")
        return await handle_general_query(user_query)  # Default fallback

async def handle_shopping_list_request(user_query: str):
    """Handle shopping list requests"""
    try:
        logger.info(f"Processing shopping list request: {user_query}")
        
        # Check if MCP server is available
        try:
            mcp_status = requests.get("http://localhost:8080/auth/status", timeout=3)
            if mcp_status.status_code == 200:
                status_data = mcp_status.json()
                if not status_data.get("authenticated", False):
                    return create_speak_response("I need to authenticate with Google first to access your shopping lists. Please visit localhost:8080/auth/login to set up Drive access.")
            else:
                return create_speak_response("Drive service is not available right now. Please make sure the MCP server is running.")
        except requests.exceptions.RequestException:
            return create_speak_response("Drive service is not running. I need access to Google Drive to manage your shopping list.")
        
        # Use Claude to extract shopping items
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_prompt = f"""You are June, an AI assistant that can manage shopping lists. The user said: "{user_query}"

Extract the shopping items from this request. Determine:
1. items: Array of items to add to the shopping list
2. list_name: Name of the list (default to "Shopping List")

Examples:
"Add milk and bread to my shopping list" → {{"items": ["milk", "bread"], "list_name": "Shopping List"}}

Return only valid JSON, no other text."""

        claude_data = {
            "model": get_claude_model_for_specialist("content"),
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": claude_prompt
                }
            ]
        }

        logger.info("Sending request to Claude API for shopping list extraction")
        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
        
        if claude_response.status_code == 200:
            claude_result = claude_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            logger.info(f"Claude extracted shopping info: {extracted_text}")
            
            try:
                shopping_info = json.loads(extracted_text)
                items = shopping_info.get("items", [])
                list_name = shopping_info.get("list_name", "Shopping List")
                
                if not items:
                    return create_notification_response("❌ No items specified for shopping list", "warning")
                
                # Create/update shopping list through MCP server (Drive API)
                list_data = {
                    "title": list_name,
                    "items": items,
                    "append": True  # Add to existing list if it exists
                }
                
                # Create the shopping list
                mcp_response = requests.post("http://localhost:8080/lists/create", 
                                           json=list_data, timeout=10)
                
                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    action = result.get("action", "updated")
                    
                    # Create basic notification
                    items_text = ", ".join(items)
                    if action == "created":
                        message = f"✅ Created new {list_name} with {len(items)} items: {items_text}"
                    else:
                        message = f"✅ Added {len(items)} items to {list_name}: {items_text}"
                    
                    return create_notification_response(message)
                else:
                    logger.error(f"MCP server error: {mcp_response.status_code} - {mcp_response.text}")
                    return create_notification_response("❌ Failed to add items to shopping list", "error")
                    
            except json.JSONDecodeError:
                logger.error(f"JSON decode error: {extracted_text}")
                return create_notification_response("❌ Could not understand shopping items", "error")
        else:
            logger.error(f"Claude API error: {claude_response.status_code}")
            return create_speak_response("Sorry, I had trouble processing your shopping list request. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in shopping list handler: {e}")
        return create_speak_response("Sorry, I encountered an error while processing your shopping list. Please try again.")

# Add placeholder functions for other handlers
async def handle_document_creation(user_query: str):
    """Handle document creation requests like 'draft a resume'"""
    try:
        logger.info(f"Processing document creation request: {user_query}")
        
        # Use Claude to understand what document to create
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_prompt = f"""You are June, an AI assistant that creates professional documents. The user said: "{user_query}"

Create a well-formatted document based on their request. For resumes, use this structure with proper formatting:

# [Full Name]
**Contact Information**
Phone: [phone] | Email: [email] | LinkedIn: [linkedin]
Location: [city, state]

## Professional Summary
[2-3 lines describing experience and key strengths]

## Core Competencies
• [Skill 1] • [Skill 2] • [Skill 3]
• [Skill 4] • [Skill 5] • [Skill 6]

## Professional Experience

**[Job Title]** | [Company Name] | [Location]
[Start Date] - [End Date]
• [Achievement with quantifiable results]
• [Key responsibility and impact]
• [Notable accomplishment]

**[Previous Job Title]** | [Previous Company] | [Location]
[Start Date] - [End Date]
• [Achievement with quantifiable results]
• [Key responsibility and impact]
• [Notable accomplishment]

## Education
**[Degree]** in [Field] | [University] | [Year]
• [Relevant coursework, honors, or activities]

## Technical Skills
• **Software:** [List relevant software/tools]
• **Programming:** [If applicable]
• **Certifications:** [Any professional certifications]

## Projects & Achievements
• [Notable project or achievement]
• [Another significant accomplishment]

---

Respond ONLY with a JSON object:
{{
  "document_type": "resume|cover_letter|business_proposal|report|letter",
  "title": "[Document Title]",
  "content": "[Complete formatted document content using the structure above]"
}}

Make it professional, properly formatted with clear sections, bullet points, and use realistic placeholder information that can be customized."""

        claude_data = {
            "model": get_claude_model_for_specialist("productivity"),
            "max_tokens": 1500,
            "messages": [
                {
                    "role": "user",
                    "content": claude_prompt
                }
            ]
        }
        
        logger.info("Sending request to Claude API for document creation")
        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
        
        if claude_response.status_code == 200:
            claude_result = claude_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            logger.info(f"Claude extracted document info: {extracted_text}")
            
            try:
                document_info = json.loads(extracted_text)
                doc_type = document_info.get("document_type", "document")
                title = document_info.get("title", "New Document")
                content = document_info.get("content", "Document content")
                
                # Create document through MCP server (Drive API)
                doc_data = {
                    "title": title,
                    "content": content
                }
                
                # Create the document
                mcp_response = requests.post("http://localhost:8080/notes/create", 
                                           json=doc_data, timeout=10)
                
                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    message = f"✅ Created {doc_type}: {title}"
                    return create_notification_response(message)
                else:
                    logger.error(f"MCP server error: {mcp_response.status_code} - {mcp_response.text}")
                    return create_notification_response("❌ Failed to create document", "error")
                    
            except json.JSONDecodeError:
                logger.error(f"JSON decode error: {extracted_text}")
                return create_notification_response("❌ Could not understand document request", "error")
        else:
            logger.error(f"Claude API error: {claude_response.status_code}")
            return create_speak_response("Sorry, I had trouble processing your document request. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in document creation handler: {e}")
        return create_speak_response("Sorry, I encountered an error while creating the document. Please try again.")

# Add handler functions
async def handle_calling_request(user_query: str):
    """Handle calling/dialing requests"""
    try:
        logger.info(f"Processing calling request: {user_query}")
        
        # Use Claude to extract contact information
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_prompt = f"""You are June, an AI assistant that can help with calling contacts. The user said: "{user_query}"

Extract the contact name or phone number they want to call. PRIORITIZE phone numbers over names.

CRITICAL RULES:
1. If the user mentions ANY digits or numbers, treat it as a phone number, NOT a contact name
2. If the user says "dial" + numbers, it's ALWAYS a direct phone number
3. If the user says "call" + only numbers, it's ALSO a direct phone number
4. Even short numbers like "200" should be treated as phone numbers, not contact names

Examples:
- "Call John" → contact_name: "John", phone_number: null
- "Call Sarah Smith" → contact_name: "Sarah Smith", phone_number: null
- "Dial mom" → contact_name: "mom", phone_number: null
- "Phone Dr. Johnson" → contact_name: "Dr. Johnson", phone_number: null
- "Call 555-1234" → contact_name: null, phone_number: "555-1234"
- "Dial 200" → contact_name: null, phone_number: "200"
- "Phone 123" → contact_name: null, phone_number: "123"
- "dial 26181258" → contact_name: null, phone_number: "26181258"
- "call 9876543210" → contact_name: null, phone_number: "9876543210"
- "call 200" → contact_name: null, phone_number: "200"

If you see numbers/digits in the request, ALWAYS set phone_number and set contact_name to null.

Respond with JSON only:
{{
  "action": "call",
  "contact_name": null,
  "phone_number": "extracted_number"
}}"""

        claude_data = {
            "model": get_claude_model_for_specialist("productivity"),
            "max_tokens": 300,
            "messages": [{"role": "user", "content": claude_prompt}]
        }
        
        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
        
        if claude_response.status_code == 200:
            claude_result = claude_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            
            try:
                call_info = json.loads(extracted_text)
                contact_name = call_info.get("contact_name")
                phone_number = call_info.get("phone_number")
                
                # PRIORITIZE phone numbers first - if a phone number is extracted, use it directly
                if phone_number:
                    logger.info(f"Dialing number directly: {phone_number}")
                    return create_call_response(phone_number)
                
                # Only search for contacts if no phone number was found
                elif contact_name:
                    logger.info(f"Searching for contact: {contact_name}")
                    # Search for contact by name
                    mcp_response = requests.get(f"http://localhost:8080/contacts/find?name={contact_name}", timeout=10)
                    
                    if mcp_response.status_code == 200:
                        result = mcp_response.json()
                        contacts = result.get("contacts", [])
                        
                        if contacts:
                            # Log all found contacts for debugging
                            logger.info(f"Found {len(contacts)} contacts for '{contact_name}'")
                            for i, contact in enumerate(contacts):
                                names = contact.get("names", [])
                                if names:
                                    display_name = names[0].get("displayName", "Unknown")
                                    logger.info(f"Contact {i}: {display_name}")
                            
                            # Use the first contact found
                            contact = contacts[0]
                            phone_numbers = contact.get("phoneNumbers", [])
                            name = contact.get("names", [{}])[0].get("displayName", contact_name)
                            
                            if phone_numbers:
                                phone = phone_numbers[0].get("value", "")
                                logger.info(f"Calling {name} at {phone}")
                                return create_call_response(phone, name)
                            else:
                                return create_speak_response(f"I found {name} in your contacts, but no phone number is available.")
                        else:
                            return create_speak_response(f"I couldn't find a contact named {contact_name}. Would you like me to dial it as a number instead?")
                    else:
                        return create_speak_response("I'm having trouble accessing your contacts right now. Could you please tell me the phone number directly?")
                        
                else:
                    return create_speak_response("I need either a contact name or phone number to make a call. Could you please specify?")
                    
            except json.JSONDecodeError:
                return create_speak_response("I couldn't understand who you want to call. Please try again.")
        else:
            return create_speak_response("Sorry, I had trouble processing your calling request.")
            
    except Exception as e:
        logger.error(f"Error in calling handler: {e}")
        return create_speak_response("Sorry, I encountered an error while processing the call request.")

async def handle_text_message_request(user_query: str):
    """Handle text messaging requests with proper contact lookup"""
    try:
        logger.info(f"Processing text message request: {user_query}")
        
        # Use Claude to extract recipient and message information
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_prompt = f"""You are June, an AI assistant for text messaging. The user said: "{user_query}"

Extract the recipient name/number and message content they want to send.

Respond with JSON:
{{
  "action": "text",
  "recipient_name": "extracted contact name or null",
  "phone_number": "extracted phone number or null",
  "message_content": "extracted message content or null"
}}

Examples:
- "text mom that I'll be late" -> {{"action": "text", "recipient_name": "mom", "phone_number": null, "message_content": "I'll be late"}}
- "send text to 555-1234 saying hello" -> {{"action": "text", "recipient_name": null, "phone_number": "555-1234", "message_content": "hello"}}
- "message john I'm running behind" -> {{"action": "text", "recipient_name": "john", "phone_number": null, "message_content": "I'm running behind"}}"""

        claude_data = {
            "model": get_claude_model_for_specialist("productivity"),
            "max_tokens": 300,
            "messages": [{"role": "user", "content": claude_prompt}]
        }
        
        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
        
        if claude_response.status_code == 200:
            claude_result = claude_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            
            try:
                text_info = json.loads(extracted_text)
                recipient_name = text_info.get("recipient_name")
                phone_number = text_info.get("phone_number")
                message_content = text_info.get("message_content", "")
                
                if not message_content:
                    return create_speak_response("What message would you like me to send?")
                
                # If phone number is provided, use it directly
                if phone_number:
                    return create_text_response(phone_number, message_content)
                
                # If recipient name is provided, look up contact
                elif recipient_name:
                    try:
                        mcp_response = requests.get(f"http://localhost:8080/contacts/find?name={recipient_name}", timeout=10)
                        
                        if mcp_response.status_code == 200:
                            result = mcp_response.json()
                            contacts = result.get("contacts", [])
                            
                            if contacts:
                                contact_info = contacts[0]
                                phone_numbers = contact_info.get("phoneNumbers", [])
                                name = contact_info.get("names", [{}])[0].get("displayName", recipient_name)
                                
                                if phone_numbers:
                                    phone = phone_numbers[0].get("value", "")
                                    return create_text_response(phone, message_content, name)
                                else:
                                    return create_speak_response(f"I found {name} in your contacts, but no phone number is available for texting.")
                            else:
                                return create_speak_response(f"I couldn't find a contact named {recipient_name}. Could you provide their phone number?")
                        else:
                            return create_speak_response("I'm having trouble accessing your contacts right now. Could you provide the phone number?")
                    
                    except Exception as mcp_error:
                        logger.error(f"MCP contact lookup failed: {mcp_error}")
                        return create_speak_response("I'm having trouble looking up that contact. Could you provide their phone number?")
                        
                else:
                    return create_speak_response("Who would you like me to send the text message to?")
                    
            except json.JSONDecodeError:
                logger.error("Failed to parse Claude response for texting")
                return create_speak_response("I couldn't understand your text message request. Please try again.")
        
        else:
            logger.error(f"Claude API error for texting: {claude_response.status_code}")
            return create_speak_response("Sorry, I'm having trouble processing your text message request.")
            
    except Exception as e:
        logger.error(f"Error in text message handler: {e}")
        return create_speak_response("Sorry, I encountered an error while processing your text message request.")

def create_text_response(phone_number: str, message_content: str, contact_name: str = None):
    """Create a response that instructs the phone to send a text message"""
    if contact_name:
        speak_message = f"Sending text to {contact_name}: {message_content}"
    else:
        speak_message = f"Sending text to {phone_number}: {message_content}"
    
    return create_action_response("text", speak_message, {
        "phone_number": phone_number,
        "contact_name": contact_name,
        "message_content": message_content
    })

async def handle_gmail_query(user_query: str):
    """Simple Gmail handling like GitHub implementation"""
    logger.info(f"Processing Gmail query: {user_query}")
    
    text_lower = user_query.lower()
    
    # Check if user wants to send an email
    if any(word in text_lower for word in ["send email", "email", "compose", "write to"]):
        # Simple email response for Android app
        return create_email_response("", None, None)
    
    # Default to opening Gmail
    return {
        "action": "open_app",
        "message": "Opening Gmail",
        "app_name": "gmail"
    }

# Main endpoints for voice processing
@app.post("/voice")
async def process_voice(request: Request):
    """Main voice processing endpoint"""
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
        
        # Process with three-tier AI system
        result = await route_to_specialist_ai(transcription)
        
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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)

EMAILS TO SUMMARIZE:
{json.dumps(emails_for_summary, indent=2)}

Provide a concise summary that mentions:
- Key senders and important subjects
- Main themes or topics
- Any urgent or important items
- Keep it under 100 words and natural

Format as a friendly voice response."""

                    claude_data = {
                        "model": get_claude_model_for_specialist("productivity"),
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": summary_prompt}]
                    }
                    
                    try:
                        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
                        
                        if claude_response.status_code == 200:
                            claude_result = claude_response.json()
                            summary_text = claude_result["content"][0]["text"].strip()
                            return create_speak_response(f"Here's your email summary: {summary_text}")
                        else:
                            logger.error(f"Claude API error: {claude_response.status_code}")
                            # Fallback to simple list
                            email_summaries = []
                            for email in emails[:3]:
                                sender = email.get("sender", "Unknown")
                                subject = email.get("subject", "No subject")
                                email_summaries.append(f"{sender}: {subject}")
                            
                            email_text = ". ".join(email_summaries)
                            return create_speak_response(f"You have {len(emails)} emails. {email_text}")
                            
                    except Exception as summary_error:
                        logger.error(f"Email summarization error: {summary_error}")
                        # Fallback to simple list
                        email_summaries = []
                        for email in emails[:3]:
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No subject")
                            email_summaries.append(f"{sender}: {subject}")
                        
                        email_text = ". ".join(email_summaries)
                        return create_speak_response(f"You have {len(emails)} emails. {email_text}")
                else:
                    # Just count and list emails without summarization
                    if len(emails) == 0:
                        return create_speak_response("You have no emails.")
                    elif len(emails) == 1:
                        email = emails[0]
                        sender = email.get("sender", "Unknown")
                        subject = email.get("subject", "No subject")
                        return create_speak_response(f"You have 1 email from {sender} about {subject}")
                    else:
                        # List first few emails
                        email_summaries = []
                        for email in emails[:3]:
                            sender = email.get("sender", "Unknown").split('<')[0].strip()  # Clean sender name
                            subject = email.get("subject", "No subject")
                            email_summaries.append(f"{sender}: {subject}")
                        
                        email_text = ". ".join(email_summaries)
                        remaining = len(emails) - 3
                        if remaining > 0:
                            return create_speak_response(f"You have {len(emails)} emails. Here are the recent ones: {email_text}. And {remaining} more.")
                        else:
                            return create_speak_response(f"You have {len(emails)} emails: {email_text}")
            else:
                return create_speak_response("You have no emails in your inbox.")
        else:
            logger.error(f"MCP server error: {mcp_response.status_code}")
            return create_speak_response("Sorry, I'm having trouble accessing your emails right now.")
            
    except Exception as e:
        logger.error(f"Error in Gmail handler: {e}")
        return create_speak_response("Sorry, I encountered an error while processing your email request.")

async def handle_meeting_scheduling(user_query: str):
    """Simple calendar handling like GitHub implementation"""
    logger.info(f"Calendar AI processing: {user_query}")
    
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

async def handle_schedule_meeting(details: dict, original_query: str):
    """Handle meeting scheduling with intelligent defaults and confirmation"""
    try:
        title = details.get("title", "New Meeting")
        duration = details.get("duration_minutes", 30)
        date = details.get("date", "today")
        time = details.get("time", "")
        attendees = details.get("attendees", [])
        description = details.get("description", "")
        
        logger.info(f"� Scheduling meeting: {title}")
        
        # If no specific time, suggest next available slot
        if not time:
            # Get today's events to suggest a time
            try:
                mcp_response = requests.get("http://localhost:8080/calendar/today", timeout=10)
                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    if result.get("auth_required"):
                        auth_url = result.get("auth_url", "http://localhost:8080/auth/login")
                        return create_speak_response(f"Please authenticate your calendar first. Visit {auth_url} to sign in.")
                    
                    # Suggest next available time slot
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    suggested_time = now.replace(minute=0, second=0) + timedelta(hours=1)
                    time = suggested_time.strftime("%I:%M %p")
            except Exception:
                time = "2:00 PM"  # Default fallback
        
        # Create the meeting via MCP server
        try:
            meeting_data = {
                "title": title,
                "date": date,
                "time": time,
                "duration_minutes": duration,
                "attendees": attendees,
                "description": description or f"Meeting scheduled via June AI: {original_query}"
            }
            
            logger.info(f"� Creating meeting with data: {meeting_data}")
            
            # Use MCP server to create the event
            mcp_response = requests.post(
                "http://localhost:8080/calendar/create_event", 
                json=meeting_data, 
                timeout=15
            )
            
            if mcp_response.status_code == 200:
                result = mcp_response.json()
                
                if result.get("auth_required"):
                    auth_url = result.get("auth_url", "http://localhost:8080/auth/login")
                    return create_speak_response(f"Please authenticate your calendar first. Visit {auth_url} to sign in.")
                
                if result.get("success"):
                    # Build confirmation message
                    attendee_text = ""
                    if attendees:
                        if len(attendees) == 1:
                            attendee_text = f" with {attendees[0]}"
                        else:
                            attendee_text = f" with {', '.join(attendees[:-1])} and {attendees[-1]}"
                    
                    duration_text = f" for {duration} minutes" if duration != 30 else ""
                    date_text = f" on {date}" if date != "today" else " for today"
                    
                    return create_speak_response(
                        f"Perfect! I've scheduled '{title}'{attendee_text} at {time}{date_text}{duration_text}. "
                        "The meeting has been added to your calendar."
                    )
                else:
                    error_msg = result.get("error", "Unknown error")
                    return create_speak_response(f"I couldn't schedule the meeting. {error_msg}")
            
            else:
                return create_speak_response("I'm having trouble accessing your calendar to schedule the meeting. Please try again later.")
                
        except Exception as create_error:
            logger.error(f"Error creating meeting: {create_error}")
            return create_speak_response("I encountered an error while scheduling your meeting. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in schedule meeting: {e}")
        return create_speak_response("Sorry, I couldn't schedule your meeting right now.")

async def handle_view_calendar(details: dict, original_query: str):
    """Handle calendar viewing requests with intelligent responses"""
    try:
        view_scope = details.get("view_scope", "today")
        
        logger.info(f"📅 Viewing calendar: {view_scope}")
        
        # Determine which endpoint to call
        if view_scope == "today":
            endpoint = "http://localhost:8080/calendar/today"
        elif view_scope == "upcoming":
            endpoint = "http://localhost:8080/calendar/upcoming"
        elif view_scope == "tomorrow":
            endpoint = "http://localhost:8080/calendar/upcoming"  # We'll filter for tomorrow
        else:
            endpoint = "http://localhost:8080/calendar/today"  # Default
        
        try:
            mcp_response = requests.get(endpoint, timeout=10)
        except Exception as mcp_error:
            logger.error(f"MCP server request failed: {mcp_error}")
            return create_speak_response("Sorry, I cannot access your calendar right now. Please check if your calendar is connected.")
        
        logger.info(f"📅 Calendar server response status: {mcp_response.status_code}")
        
        if mcp_response.status_code == 200:
            result = mcp_response.json()
            
            # Check if authentication is required
            if result.get("auth_required"):
                auth_url = result.get("auth_url", "http://localhost:8080/auth/login")
                return create_speak_response(f"Please authenticate your calendar first. Visit {auth_url} to sign in.")
            
            events = result.get("events", [])
            
            # Filter for tomorrow if needed
            if view_scope == "tomorrow":
                from datetime import datetime, timedelta
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow_date = tomorrow.strftime("%Y-%m-%d")
                events = [e for e in events if tomorrow_date in e.get("start", {}).get("dateTime", "")]
            
            logger.info(f"📅 Found {len(events)} calendar events")
            
            if events:
                return format_events_response(events, view_scope)
            else:
                if view_scope == "today":
                    return create_speak_response("You have no events scheduled for today. Your calendar is clear!")
                elif view_scope == "tomorrow":
                    return create_speak_response("You have no events scheduled for tomorrow. Your day is free!")
                else:
                    return create_speak_response("You have no upcoming events.")
        
        else:
            logger.error(f"Calendar server error: {mcp_response.status_code}")
            return create_speak_response("Sorry, I'm having trouble accessing your calendar right now.")
            
    except Exception as e:
        logger.error(f"Error in view calendar: {e}")
        return create_speak_response("Sorry, I encountered an error while checking your calendar.")

async def handle_check_availability(details: dict, original_query: str):
    """Check calendar availability for scheduling"""
    try:
        # For now, redirect to view calendar to show current schedule
        return await handle_view_calendar({"view_scope": "today"}, original_query)
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return create_speak_response("Sorry, I couldn't check your availability right now.")

def format_events_response(events: list, view_scope: str) -> dict:
    """Format calendar events into a natural voice response"""
    try:
        if len(events) == 1:
            event = events[0]
            title = event.get("summary", "Untitled event")
            start_time = event.get("start", {}).get("dateTime", "")
            
            if start_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%I:%M %p")
                    
                    if view_scope == "today":
                        return create_speak_response(f"You have one event today: {title} at {time_str}")
                    elif view_scope == "tomorrow":
                        return create_speak_response(f"You have one event tomorrow: {title} at {time_str}")
                    else:
                        return create_speak_response(f"Your next event is: {title} at {time_str}")
                except Exception:
                    return create_speak_response(f"You have one event: {title}")
            else:
                return create_speak_response(f"You have one event: {title}")
        
        elif len(events) <= 3:
            # List all events for small number
            event_summaries = []
            for event in events:
                title = event.get("summary", "Untitled event")
                start_time = event.get("start", {}).get("dateTime", "")
                if start_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        time_str = dt.strftime("%I:%M %p")
                        event_summaries.append(f"{title} at {time_str}")
                    except Exception:
                        event_summaries.append(title)
                else:
                    event_summaries.append(title)
            
            events_text = ". ".join(event_summaries)
            scope_text = view_scope if view_scope != "upcoming" else ""
            return create_speak_response(f"You have {len(events)} events {scope_text}: {events_text}")
        
        else:
            # Summarize for many events
            first_few = []
            for event in events[:3]:
                title = event.get("summary", "Untitled event")
                start_time = event.get("start", {}).get("dateTime", "")
                if start_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        time_str = dt.strftime("%I:%M %p")
                        first_few.append(f"{title} at {time_str}")
                    except Exception:
                        first_few.append(title)
                else:
                    first_few.append(title)
            
            events_text = ", ".join(first_few)
            remaining = len(events) - 3
            scope_text = view_scope if view_scope != "upcoming" else ""
            return create_speak_response(
                f"You have {len(events)} events {scope_text}. The first few are: {events_text}, and {remaining} more."
            )
            
    except Exception as e:
        logger.error(f"Error formatting events: {e}")
        return create_speak_response(f"You have {len(events)} events in your calendar.")

async def handle_notes_request(user_query: str):
    """Handle note-taking requests"""
    try:
        logger.info(f"Processing notes request: {user_query}")
        
        # Use Claude to extract note content
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_prompt = f"""You are June, an AI assistant that can create notes. The user said: "{user_query}"

Extract what they want to note down and create a proper title.

Respond with JSON:
{{
  "title": "Note title",
  "content": "Note content"
}}"""

        claude_data = {
            "model": get_claude_model_for_specialist("content"),
            "max_tokens": 500,
            "messages": [{"role": "user", "content": claude_prompt}]
        }
        
        claude_response = requests.post(CLAUDE_API_URL, headers=headers, json=claude_data, timeout=30)
        
        if claude_response.status_code == 200:
            claude_result = claude_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            
            try:
                note_info = json.loads(extracted_text)
                title = note_info.get("title", "Quick Note")
                content = note_info.get("content", user_query)
                
                # Create note through MCP server
                note_data = {"title": title, "content": content}
                mcp_response = requests.post("http://localhost:8080/notes/create", json=note_data, timeout=10)
                
                if mcp_response.status_code == 200:
                    message = f"📝 Created note: {title}"
                    return create_notification_response(message)
                else:
                    return create_notification_response("❌ Failed to create note", "error")
                    
            except json.JSONDecodeError:
                return create_notification_response("❌ Could not understand note request", "error")
        else:
            return create_speak_response("Sorry, I had trouble processing your note request.")
            
    except Exception as e:
        logger.error(f"Error in notes handler: {e}")
        return create_speak_response("Sorry, I encountered an error while creating the note.")

async def handle_youtube_query(user_query: str):
    return create_speak_response("YouTube features will be available soon.")

async def handle_general_query(user_query: str):
    return create_speak_response("General conversation features will be available soon.")

# 🎯 MAIN TEXT PROCESSING ENDPOINT - Entry point for June app queries
@app.post("/process")
async def process_text_query(request: dict):
    """
    Main endpoint for processing text queries from June app.
    Implements three-tier AI routing system:
    1. Router AI (Haiku) - Determines specialist
    2. Productivity AI (Sonnet) - Business tasks
    3. Content AI (Opus) - Personal tasks
    """
    try:
        # Extract text from request
        user_text = request.get("text", "").strip()
        if not user_text:
            return JSONResponse({"action": "error", "message": "No text provided"}, status_code=400)
        
        logger.info(f"📱 June app query received: '{user_text}'")
        
        # 🎯 STEP 1: ROUTER AI - Decision model determines which specialist to use
        logger.info("🤖 Router AI: Analyzing query to determine specialist...")
        specialist = route_to_ai_specialist(user_text)
        
        # 🎯 STEP 2: ROUTE TO APPROPRIATE SPECIALIST
        if specialist == "productivity":
            logger.info("🏢 Routing to PRODUCTIVITY AI for business tasks")
            return await handle_productivity_tasks(user_text)
        else:
            logger.info("📝 Routing to CONTENT AI for personal tasks")
            return await handle_content_tasks(user_text)
        
    except Exception as e:
        logger.error(f"Text processing error: {e}")
        return JSONResponse({"action": "error", "message": f"Failed to process query: {str(e)}"}, status_code=500)

@app.get("/status")
async def get_status():
    """Health check endpoint"""
    return {"status": "running", "message": "June Voice AI Server - Three-Tier AI System Active"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)
