import os
import whisper
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import requests
import tempfile
import logging
import json
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = "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"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

app = FastAPI()

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

        # Check if model is loaded
        if model is None:
            return JSONResponse({"action": "error", "message": "Whisper model not available"}, status_code=500)

        # Try to transcribe with error handling
        try:
            # Use Whisper's built-in audio loading - force English language
            result = model.transcribe(audio_path, fp16=False, language="en")
            text = result["text"].strip()
            logger.info(f"Transcribed text: '{text}'")
        except Exception as e:
            logger.error(f"Primary transcription failed: {e}")
            # Try alternative approach - load audio as numpy array
            try:
                import librosa
                logger.info("Trying librosa fallback...")
                # Load audio file using librosa (which doesn't require FFmpeg for some formats)
                audio_data, sr = librosa.load(audio_path, sr=16000)
                logger.info(f"Librosa loaded audio successfully: {len(audio_data)} samples at {sr}Hz")
                result = model.transcribe(audio_data)
                text = result["text"].strip()
                logger.info(f"Transcribed text (librosa method): '{text}'")
            except Exception as e2:
                logger.error(f"Librosa transcription also failed: {e2}")
                # Try one more approach - convert the file extension and try again
                try:
                    # Sometimes the issue is just the file extension
                    import shutil
                    new_path = audio_path.replace('.wav', '.3gp')
                    shutil.copy2(audio_path, new_path)
                    logger.info(f"Trying with .3gp extension: {new_path}")
                    result = model.transcribe(new_path, fp16=False)
                    text = result["text"].strip()
                    logger.info(f"Transcribed text (.3gp method): '{text}'")
                    os.unlink(new_path)  # cleanup
                except Exception as e3:
                    logger.error(f"All transcription methods failed: {e3}")
                    # Cleanup temp file
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                    return JSONResponse({"action": "error", "message": f"Voice transcription failed - audio format may not be supported. Install FFmpeg for better compatibility."}, status_code=500)

        # Cleanup temp file
        try:
            os.unlink(audio_path)
        except:
            pass

        # If no text was transcribed
        if not text:
            return JSONResponse({"action": "error", "message": "No speech detected"})

        # Send to Claude for intent parsing
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        prompt = f'''You are an AI assistant for a phone. The user said: "{text}".
Reply with a JSON object describing the action to perform. Use these exact action types:

For phone calls with contact names:
{{"action": "call", "contact": "contact_name"}}

For phone calls with numbers:
{{"action": "call", "contact": "phone_number"}}

For SMS:
{{"action": "send_sms", "contact": "contact_name_or_number", "message": "message_text"}}

For opening apps - use the most common/simple name:
{{"action": "open_app", "app": "calendar"}} for calendar/schedule apps
{{"action": "open_app", "app": "camera"}} for camera/photo apps
{{"action": "open_app", "app": "contacts"}} for contacts/phonebook
{{"action": "open_app", "app": "messages"}} for messaging/SMS apps
{{"action": "open_app", "app": "phone"}} for phone/dialer apps
{{"action": "open_app", "app": "gmail"}} for Gmail specifically
{{"action": "open_app", "app": "email"}} for any email app
{{"action": "open_app", "app": "whatsapp"}} for WhatsApp
{{"action": "open_app", "app": "facebook"}} for Facebook
{{"action": "open_app", "app": "instagram"}} for Instagram
{{"action": "open_app", "app": "youtube"}} for YouTube
{{"action": "open_app", "app": "chrome"}} for Chrome browser
{{"action": "open_app", "app": "browser"}} for any web browser
{{"action": "open_app", "app": "maps"}} for Maps/navigation
{{"action": "open_app", "app": "music"}} for music apps
{{"action": "open_app", "app": "photos"}} for photo gallery
{{"action": "open_app", "app": "settings"}} for device settings
{{"action": "open_app", "app": "calculator"}} for calculator
{{"action": "open_app", "app": "clock"}} for clock/timer/alarm
{{"action": "open_app", "app": "weather"}} for weather apps
{{"action": "open_app", "app": "spotify"}} for Spotify
{{"action": "open_app", "app": "netflix"}} for Netflix
{{"action": "open_app", "app": "amazon"}} for Amazon
{{"action": "open_app", "app": "uber"}} for Uber
{{"action": "open_app", "app": "twitter"}} for Twitter
{{"action": "open_app", "app": "linkedin"}} for LinkedIn
{{"action": "open_app", "app": "telegram"}} for Telegram
{{"action": "open_app", "app": "snapchat"}} for Snapchat
{{"action": "open_app", "app": "tiktok"}} for TikTok
{{"action": "open_app", "app": "discord"}} for Discord
{{"action": "open_app", "app": "zoom"}} for Zoom
{{"action": "open_app", "app": "skype"}} for Skype

For any other app, use the simplest common name (e.g., "slack", "dropbox", "drive", etc.)

For errors:
{{"action": "error", "message": "Could not understand"}}

Examples:
- "call mom" -> {{"action": "call", "contact": "mom"}}
- "dial 123456789" -> {{"action": "call", "contact": "123456789"}}
- "open gmail" -> {{"action": "open_app", "app": "gmail"}}
- "launch facebook" -> {{"action": "open_app", "app": "facebook"}}
- "start camera" -> {{"action": "open_app", "app": "camera"}}

Only reply with the JSON object, no other text.'''

        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 256,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(CLAUDE_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            action_json = response.json()["content"][0]["text"]
            logger.info(f"Claude response: {action_json}")
            
            # Parse the JSON string from Claude and return as proper JSON
            try:
                parsed_action = json.loads(action_json)
                return JSONResponse(content=parsed_action)
            except json.JSONDecodeError:
                # If Claude didn't return valid JSON, create error response
                return JSONResponse({"action": "error", "message": "AI returned invalid response format"})
                
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return JSONResponse({"action": "error", "message": f"AI processing failed: {str(e)}"}, status_code=500)

    except Exception as e:
        logger.error(f"General error: {e}")
        return JSONResponse({"action": "error", "message": f"Server error: {str(e)}"}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "Server is running", "whisper_loaded": model is not None}

# To run: uvicorn server:app --host 0.0.0.0 --port 5005

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:5005")
    uvicorn.run(app, host="0.0.0.0", port=5005)
