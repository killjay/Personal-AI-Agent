"""
Simple TTS Server for Voice AI Agent
Provides text-to-speech synthesis service on port 5002
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TTS Speech Synthesis Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "female_1"
    speed: float = 1.0

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text
    Returns audio data or mock response
    """
    try:
        logger.info(f"🔊 TTS Request: '{request.text}' with voice '{request.voice}'")
        
        # Mock TTS response for now
        # In a real implementation, this would generate actual audio
        return JSONResponse({
            "status": "success",
            "message": "TTS synthesis completed",
            "text": request.text,
            "voice": request.voice,
            "audio_url": f"/audio/mock_{hash(request.text)}.wav",
            "mock": True
        })
        
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tts-server",
        "port": 5002,
        "available_voices": ["female_1", "male_1", "female_2"],
        "capabilities": ["text-to-speech", "voice-selection"]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TTS Speech Synthesis Server", 
        "status": "running",
        "endpoints": {
            "synthesize": "/synthesize (POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    logger.info("🔊 Starting TTS Server on http://0.0.0.0:5002")
    uvicorn.run(app, host="0.0.0.0", port=5002)
