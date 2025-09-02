#!/usr/bin/env python3
"""
Simple test server to verify voice configuration
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Voice Configuration - June uses Sarah (female_1) voice
JUNE_VOICE = "female_1"  # Sarah - Female US English voice

app = FastAPI()

def create_speak_response(message: str, voice: str = JUNE_VOICE):
    """Create a standardized speak response with June's voice"""
    return JSONResponse({
        "action": "speak",
        "message": message,
        "voice": voice,
        "voice_name": "Sarah"  # Human-readable name for female_1
    })

@app.get("/")
async def root():
    return {"message": "June Voice Test Server", "voice": JUNE_VOICE}

@app.get("/voice/config")
async def get_voice_config():
    """Get current voice configuration for June"""
    return {
        "current_voice": JUNE_VOICE,
        "voice_name": "Sarah",
        "language": "en-US",
        "gender": "female",
        "description": "Female US English voice"
    }

@app.post("/voice/test")
async def test_voice():
    """Test June's voice with a sample message"""
    return create_speak_response("Hi! I'm June, your AI assistant. I'm using Sarah's voice - a female US English voice. How can I help you today?")

if __name__ == "__main__":
    print("🎤 Starting June Voice Test Server...")
    uvicorn.run(app, host="0.0.0.0", port=5006)
