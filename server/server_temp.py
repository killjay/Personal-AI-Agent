import os
import whisper
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import requests
import tempfile
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = "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"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

app = FastAPI()

# Load model with error handling
try:
    model = whisper.load_model("base")
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

        # For now, let's return a mock response to test the connection
        # This bypasses the FFmpeg issue temporarily
        text = "test command"
        logger.info(f"Mock transcribed text: {text}")

        # Cleanup temp file
        try:
            os.unlink(audio_path)
        except:
            pass

        # Send mock response for testing
        mock_response = {"action": "error", "message": "Voice processing working - FFmpeg setup needed for full functionality"}
        return JSONResponse(content=mock_response)

        # TODO: Uncomment below when FFmpeg is properly installed
        """
        # Transcribe with error handling
        try:
            result = model.transcribe(audio_path)
            text = result["text"].strip()
            logger.info(f"Transcribed text: {text}")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            # Cleanup temp file
            try:
                os.unlink(audio_path)
            except:
                pass
            return JSONResponse({"action": "error", "message": f"Transcription failed: {str(e)}"}, status_code=500)

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
Reply with a JSON object describing the action to perform, e.g.:
{{"action": "call", "contact": "mom"}}
or
{{"action": "open_app", "app": "WhatsApp"}}
or
{{"action": "send_sms", "contact": "John", "message": "hello"}}
or
{{"action": "error", "message": "Could not understand"}}
Only reply with the JSON object.'''

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
            return JSONResponse(content=action_json)
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return JSONResponse({"action": "error", "message": f"AI processing failed: {str(e)}"}, status_code=500)
        """

    except Exception as e:
        logger.error(f"General error: {e}")
        return JSONResponse({"action": "error", "message": f"Server error: {str(e)}"}, status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "Server is running", "whisper_loaded": model is not None}

# To run: uvicorn server:app --host 0.0.0.0 --port 5005
