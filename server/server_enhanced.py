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
GPTOSS_API_URL = "https://api.gptoss.com/v1/messages"

# Voice Configuration - June uses Sarah (female_1) voice
JUNE_VOICE = "female_1"  # Sarah - Female US English voice

# Initialize global location variable
user_location = None

app = FastAPI()

def create_speak_response(message: str, voice: str = JUNE_VOICE):
    """Create a standardized speak response with June's voice"""
    return JSONResponse({
        "action": "speak",
        "message": message,
        "voice": voice,
        "voice_name": "Sarah"  # Human-readable name for female_1
    })

def create_notification_response(message: str, notification_type: str = "success"):
    """Create a floating notification response instead of voice"""
    return JSONResponse({
        "action": "notification",
        "message": message,
        "type": notification_type,  # success, error, info, warning
        "duration": 3000  # 3 seconds
    })

async def get_location_and_pricing(items_list: list, user_location_data: dict = None):
    """Get user location and fetch pricing for shopping items"""
    try:
        # Use global location or provided location
        global user_location
        location_data = user_location_data or user_location
        
        # If no location provided, try to get approximate location
        if not location_data:
            location_data = {
                "city": "Default City",
                "country": "US",
                "latitude": 0.0,
                "longitude": 0.0
            }
        
    # Use Gptoss to estimate pricing based on location and current market prices
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        pricing_prompt = f"""You are a grocery pricing expert. Based on the location {location_data.get('city', 'US')} and current market prices, estimate realistic prices for these grocery items: {', '.join(items_list)}

Please provide a JSON response with estimated prices in USD. Include:
- item_name: price in dollars (as number)
- estimated_store: nearby store chain
- total_estimated: sum of all prices

Format your response as valid JSON only:
{{
  "items": [
    {{"name": "item1", "price": 2.99, "store": "Walmart"}},
    {{"name": "item2", "price": 4.50, "store": "Walmart"}}
  ],
  "location": "{location_data.get('city', 'Unknown')}",
  "total_estimated": 7.49,
  "currency": "USD",
  "estimated_store": "Walmart"
}}"""

        pricing_data = {
            "model": "gptoss-20b-20240307",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": pricing_prompt}]
        }
        
    pricing_response = requests.post(GPTOSS_API_URL, headers=headers, json=pricing_data, timeout=30)
        
        if pricing_response.status_code == 200:
            pricing_result = pricing_response.json()
            pricing_text = pricing_result["content"][0]["text"].strip()
            
            try:
                pricing_info = json.loads(pricing_text)
                return pricing_info
            except json.JSONDecodeError:
                logger.error(f"Failed to parse pricing JSON: {pricing_text}")
                return None
        else:
            logger.error(f"Pricing API error: {pricing_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting location and pricing: {e}")
        return None

# Load model with error handling
try:
    model = whisper.load_model("small")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None

@app.post("/location")
async def update_location(location_data: dict):
    """Update user location for pricing and store recommendations"""
    try:
        global user_location
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        city = location_data.get("city", "Unknown")
        country = location_data.get("country", "US")
        
        # Store location globally (in production, you'd use a database)
        user_location = {
            "latitude": latitude,
            "longitude": longitude,
            "city": city,
            "country": country,
            "updated": datetime.now().isoformat()
        }
        
        logger.info(f"Location updated: {city}, {country}")
        return JSONResponse({
            "success": True,
            "message": f"Location updated to {city}, {country}",
            "location": user_location
        })
        
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        return JSONResponse({
            "success": False,
            "message": "Failed to update location"
        }, status_code=500)

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

        logger.info(f"Transcribed text: '{text}'")

        # Route to appropriate handler based on content
        text_lower = text.lower()
        
        # Check for meeting/calendar related queries
        if any(word in text_lower for word in ["meeting", "schedule", "calendar", "appointment", "book"]):
            return await handle_meeting_scheduling(text)
        # Check for note-taking requests  
        elif any(word in text_lower for word in ["note", "remember", "write down", "jot down"]):
            return await handle_notes_request(text)
        # Check for shopping list requests
        elif any(word in text_lower for word in ["shopping", "grocery", "buy", "purchase", "list", "add to"]):
            return await handle_shopping_list_request(text)
        # Check for Gmail/Calendar queries
        elif any(word in text_lower for word in ["email", "gmail", "calendar", "events", "today", "tomorrow"]):
            return await handle_gmail_calendar_query(text)
        # Check for YouTube queries
        elif any(word in text_lower for word in ["youtube", "video", "channel", "subscribe", "watch"]):
            return await handle_youtube_query(text)
        else:
            # General conversation/command processing
            return await handle_general_query(text)

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return JSONResponse({"action": "error", "message": f"Failed to process voice: {str(e)}"}, status_code=500)

async def handle_shopping_list_request(user_query: str):
    """Handle shopping list requests with pricing and bill of quantities"""
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
        
    # Use Gptoss to extract shopping items
        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
    gptoss_prompt = f"""You are June, an AI assistant that can manage shopping lists. The user said: "{user_query}"

Extract the shopping items from this request. Determine:
1. items: Array of items to add to the shopping list
2. list_name: Name of the list (default to "Shopping List")

Examples:
"Add milk and bread to my shopping list" → {{"items": ["milk", "bread"], "list_name": "Shopping List"}}

Return only valid JSON, no other text."""

    gptoss_data = {
            "model": "gptoss-20b-20240307",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": gptoss_prompt
                }
            ]
        }

    logger.info("Sending request to Gptoss API for shopping list extraction")
    gptoss_response = requests.post(GPTOSS_API_URL, headers=headers, json=gptoss_data, timeout=30)
        
        if gptoss_response.status_code == 200:
            gptoss_result = gptoss_response.json()
            extracted_text = claude_result["content"][0]["text"].strip()
            logger.info(f"Claude extracted shopping info: {extracted_text}")
            
            try:
                shopping_info = json.loads(extracted_text)
                items = shopping_info.get("items", [])
                list_name = shopping_info.get("list_name", "Shopping List")
                
                if not items:
                    return create_notification_response("❌ No items specified for shopping list", "warning")
                
                # Get pricing information for the items
                logger.info("Getting pricing information for shopping items...")
                pricing_info = await get_location_and_pricing(items)
                
                # Create/update shopping list through MCP server (Drive API)
                list_data = {
                    "title": list_name,
                    "items": items,
                    "append": True  # Add to existing list if it exists
                }
                
                # If we have pricing info, create enhanced list
                if pricing_info:
                    enhanced_list_data = {
                        "title": f"{list_name} - Bill of Quantities",
                        "items": items,
                        "pricing_info": pricing_info,
                        "bill_of_quantities": True,
                        "append": True
                    }
                    
                    # Create both regular list and bill of quantities
                    mcp_response = requests.post("http://localhost:8080/lists/create", 
                                               json=list_data, timeout=10)
                    
                    mcp_bill_response = requests.post("http://localhost:8080/lists/create", 
                                                   json=enhanced_list_data, timeout=10)
                    
                    if mcp_response.status_code == 200 and mcp_bill_response.status_code == 200:
                        result = mcp_response.json()
                        action = result.get("action", "updated")
                        
                        # Create enhanced notification with pricing
                        total_cost = pricing_info.get("total_estimated", 0)
                        store = pricing_info.get("estimated_store", "Local store")
                        location = pricing_info.get("location", "your area")
                        
                        # Create bill summary
                        bill_details = []
                        for item_info in pricing_info.get("items", []):
                            item_name = item_info.get("name", "")
                            item_price = item_info.get("price", 0)
                            bill_details.append(f"{item_name}: ${item_price:.2f}")
                        
                        bill_text = " | ".join(bill_details)
                        
                        if action == "created":
                            message = f"✅ {list_name} created with Bill of Quantities | {bill_text} | Total: ${total_cost:.2f} at {store}"
                        else:
                            message = f"✅ {list_name} updated with pricing | {bill_text} | Total: ${total_cost:.2f} at {store}"
                        
                        return create_notification_response(message)
                    else:
                        logger.error(f"MCP server error creating lists")
                        return create_notification_response("❌ Failed to create shopping list with pricing", "error")
                        
                else:
                    # Fallback to basic list without pricing
                    mcp_response = requests.post("http://localhost:8080/lists/create", 
                                               json=list_data, timeout=10)
                    
                    if mcp_response.status_code == 200:
                        result = mcp_response.json()
                        action = result.get("action", "updated")
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
async def handle_meeting_scheduling(user_query: str):
    return create_speak_response("Meeting scheduling feature will be available soon.")

async def handle_notes_request(user_query: str):
    return create_speak_response("Notes feature will be available soon.")

async def handle_gmail_calendar_query(user_query: str):
    return create_speak_response("Gmail and calendar features will be available soon.")

async def handle_youtube_query(user_query: str):
    return create_speak_response("YouTube features will be available soon.")

async def handle_general_query(user_query: str):
    return create_speak_response("General conversation features will be available soon.")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)
