"""
Simple Whisper Server for Voice AI Agent
Provides speech-to-text transcription service on port 5004
"""

import os
import logging
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Try to import whisper with error handling
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available - using mock responses")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Speech Recognition Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global whisper model
model = None

def load_whisper_model():
    """Load Whisper model with error handling"""
    global model
    if not WHISPER_AVAILABLE:
        logger.warning("Whisper not installed - transcription will return mock responses")
        return False
        
    try:
        model = whisper.load_model("base")
        logger.info("✅ Whisper model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load Whisper model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize Whisper model on startup"""
    load_whisper_model()

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text
    Accepts audio file uploads and returns transcribed text
    """
    temp_file_path = None
    
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            logger.warning(f"Invalid content type: {audio.content_type}")
            # Don't reject - some clients might not set proper content type
        
        # Read audio data
        audio_data = await audio.read()
        logger.info(f"Received audio file: {audio.filename}, size: {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        logger.info(f"Audio saved to: {temp_file_path}")
        
        # Transcribe with Whisper
        if model is not None and WHISPER_AVAILABLE:
            try:
                result = model.transcribe(temp_file_path, language="en")
                transcription = result["text"].strip()
                logger.info(f"🎤 Transcribed: '{transcription}'")
                
                return JSONResponse({
                    "text": transcription,
                    "status": "success",
                    "language": "en"
                })
                
            except Exception as whisper_error:
                logger.error(f"Whisper transcription error: {whisper_error}")
                # Fall through to mock response
        
        # Mock response if Whisper not available
        logger.warning("Using mock transcription - Whisper not available")
        return JSONResponse({
            "text": "test voice command",
            "status": "mock",
            "message": "Whisper not available - using mock response"
        })
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info("Temporary file cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up temp file: {cleanup_error}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "whisper-server",
        "port": 5004,
        "whisper_available": WHISPER_AVAILABLE,
        "model_loaded": model is not None
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Whisper Speech Recognition Server",
        "status": "running",
        "endpoints": {
            "transcribe": "/transcribe (POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    logger.info("🎤 Starting Whisper Server on http://0.0.0.0:5004")
    uvicorn.run(app, host="0.0.0.0", port=5004)
