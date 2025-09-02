#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Server for Voice AI Agent
Provides text-to-speech conversion endpoints
"""

import os
import json
import logging
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TTS Server", description="Text-to-Speech service for Voice AI Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "TTS Server is running", "service": "tts"}

@app.post("/tts/synthesize")
async def synthesize_speech(request_data: dict):
    """Convert text to speech"""
    try:
        if "text" not in request_data:
            raise HTTPException(status_code=400, detail="Missing 'text' field")
        
        text = request_data["text"]
        voice = request_data.get("voice", "female_1")  # Default to Sarah (female_1)
        speed = request_data.get("speed", 1.0)
        
        logger.info(f"Synthesizing speech for text: '{text[:50]}...' with voice: {voice} (Sarah)")
        
        # Mock implementation - in real scenario would use TTS engine
        # For now, return a mock response
        return {
            "status": "synthesized",
            "text": text,
            "voice": voice,
            "speed": speed,
            "duration_seconds": len(text) * 0.1,  # Mock duration
            "audio_url": f"/tts/audio/mock_audio_{hash(text) % 1000}.wav"
        }
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to synthesize speech: {str(e)}")

@app.get("/tts/voices")
async def get_available_voices():
    """Get available TTS voices"""
    try:
        # Mock voice options
        voices = [
            {"id": "female_1", "name": "Sarah", "language": "en-US", "gender": "female"},
            {"id": "male_1", "name": "John", "language": "en-US", "gender": "male"},
            {"id": "female_2", "name": "Emma", "language": "en-GB", "gender": "female"},
            {"id": "male_2", "name": "James", "language": "en-GB", "gender": "male"}
        ]
        
        return {"voices": voices, "count": len(voices)}
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")

@app.post("/tts/quick-speak")
async def quick_speak(request_data: dict):
    """Quick text-to-speech for short phrases"""
    try:
        if "text" not in request_data:
            raise HTTPException(status_code=400, detail="Missing 'text' field")
        
        text = request_data["text"]
        
        if len(text) > 200:
            raise HTTPException(status_code=400, detail="Text too long for quick speak (max 200 characters)")
        
        logger.info(f"Quick speak: '{text}'")
        
        # Mock implementation
        return {
            "status": "speaking",
            "text": text,
            "estimated_duration": len(text) * 0.08  # Mock duration
        }
    except Exception as e:
        logger.error(f"Error in quick speak: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to quick speak: {str(e)}")

@app.get("/tts/audio/{audio_id}")
async def get_audio_file(audio_id: str):
    """Get synthesized audio file"""
    try:
        # Mock implementation - would return actual audio file
        logger.info(f"Requested audio file: {audio_id}")
        
        # In real implementation, would return FileResponse with actual audio
        return {"message": f"Audio file {audio_id} would be served here", "status": "mock"}
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve audio: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TTS Server for Voice AI Agent", "version": "1.0.0"}

if __name__ == "__main__":
    logger.info("Starting TTS Server on http://0.0.0.0:5002")
    uvicorn.run(app, host="0.0.0.0", port=5002)
