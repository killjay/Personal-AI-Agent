#!/usr/bin/env python3
"""
Test script to simulate server response for TTS debugging
"""

import json
import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.post("/voice")
async def test_voice_response():
    """Test endpoint that returns a speak action"""
    response = {
        "action": "speak",
        "message": "Hello! This is a test message to verify that text-to-speech is working correctly on your Android device."
    }
    print(f"Sending TTS test response: {response}")
    return JSONResponse(response)

@app.get("/health")
async def health():
    return {"status": "TTS Test Server Running"}

if __name__ == "__main__":
    print("🔊 Starting TTS Test Server on port 5006...")
    print("📱 Android app can test TTS by connecting to: http://192.168.1.120:5006/voice")
    print("📋 Expected response format:")
    print(json.dumps({
        "action": "speak",
        "message": "Test message for TTS"
    }, indent=2))
    
    uvicorn.run(app, host="0.0.0.0", port=5006)
