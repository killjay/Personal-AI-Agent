#!/usr/bin/env python3
"""
Whisper Server for Voice AI Agent  
Provides speech-to-text conversion using OpenAI Whisper
"""

import os
import json
import logging
import tempfile
import whisper
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Server", description="Speech-to-Text service using OpenAI Whisper")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
try:
    model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "Whisper Server is running", 
        "service": "whisper",
        "model_loaded": model is not None
    }

@app.post("/whisper/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio file to text"""
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Whisper model not loaded")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            audio_path = temp_file.name

        logger.info(f"Transcribing audio file: {file.filename}, size: {len(content)} bytes")

        # Transcribe with Whisper
        result = model.transcribe(audio_path, fp16=False)
        text = result["text"].strip()
        
        # Clean up temp file
        os.unlink(audio_path)
        
        logger.info(f"Transcription result: '{text}'")
        
        return {
            "status": "success",
            "text": text,
            "language": result.get("language", "unknown"),
            "confidence": 0.95  # Mock confidence score
        }
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        # Clean up temp file if it exists
        try:
            if 'audio_path' in locals():
                os.unlink(audio_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio_simple(audio: UploadFile = File(...)):
    """Simple transcribe endpoint for compatibility (main server expects this endpoint)"""
    return await transcribe_audio(audio)

@app.post("/whisper/transcribe-streaming")
async def transcribe_streaming(file: UploadFile = File(...)):
    """Transcribe audio with streaming/real-time processing"""
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Whisper model not loaded")
        
        # For now, use same logic as regular transcribe
        # In real implementation, this would handle streaming
        return await transcribe_audio(file)
        
    except Exception as e:
        logger.error(f"Error in streaming transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stream transcribe: {str(e)}")

@app.get("/whisper/models")
async def get_available_models():
    """Get available Whisper models"""
    try:
        models = [
            {"name": "tiny", "size": "~39 MB", "accuracy": "low", "speed": "fast"},
            {"name": "base", "size": "~74 MB", "accuracy": "medium", "speed": "medium"},
            {"name": "small", "size": "~244 MB", "accuracy": "good", "speed": "medium"},
            {"name": "medium", "size": "~769 MB", "accuracy": "better", "speed": "slow"},
            {"name": "large", "size": "~1550 MB", "accuracy": "best", "speed": "slowest"}
        ]
        
        current_model = "base" if model is not None else None
        
        return {
            "available_models": models,
            "current_model": current_model,
            "model_loaded": model is not None
        }
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Whisper Server for Voice AI Agent", "version": "1.0.0"}

if __name__ == "__main__":
    logger.info("Starting Whisper Server on http://0.0.0.0:5004")
    uvicorn.run(app, host="0.0.0.0", port=5004)
