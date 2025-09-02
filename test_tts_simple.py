#!/usr/bin/env python3
"""
Simple TTS test for Android app
Creates a server that always returns a "speak" action for testing
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/voice")
async def test_tts_response(file: UploadFile = File(...)):
    """Always return a speak action for TTS testing"""
    return JSONResponse({
        "action": "speak",
        "message": "Hello! This is a test message to verify that text-to-speech is working correctly on your Android device. If you can hear this, TTS is working perfectly!"
    })

@app.get("/health")
async def health():
    return {"status": "TTS Test Server Running"}

if __name__ == "__main__":
    print("🔊 TTS Test Server starting on port 5007...")
    print("📱 Change Android app server URL to: http://192.168.1.120:5007/voice")
    print("🎤 Record any audio and it will respond with TTS test message")
    uvicorn.run(app, host="0.0.0.0", port=5007)
