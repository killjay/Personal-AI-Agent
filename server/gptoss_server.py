#!/usr/bin/env python3
"""
GPT-OSS Server for Voice AI Agent
Handles AI intent processing using GPT-OSS open models from Hugging Face
"""

import os
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from groq import Groq

# Using official Groq client for GPT-OSS 20B

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-OSS Server", description="AI Intent Processing using GPT-OSS open models from Hugging Face")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Groq API Configuration
GROQ_API_KEY = "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"
MODEL_NAME = "openai/gpt-oss-20b"  # Official GPT-OSS 20B model on Groq

# Initialize Groq client
try:
    logger.info(f"Initializing Groq client with model: {MODEL_NAME}")
    
    # Set API key as environment variable for Groq client
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    client = Groq()
    
    # Test API connection with GPT-OSS 20B
    test_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Hello"}],
        max_completion_tokens=10,
        temperature=0.7
    )
    
    logger.info("✅ Successfully connected to Groq API with GPT-OSS 20B!")
    groq_available = True
    
except Exception as e:
    logger.error(f"❌ Failed to connect to Groq API: {e}")
    groq_available = False

class ProcessTextRequest(BaseModel):
    text: str
    context: dict = {}

class IntentRequest(BaseModel):
    user_input: str
    conversation_history: list = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_status = "groq-api" if groq_available else "mock-mode"
    return {
        "status": "GPT-OSS Server is running",
        "service": "gpt-oss",
        "model": model_status,
        "model_name": MODEL_NAME if groq_available else "none"
    }

@app.post("/gpt-oss/process-text")
async def process_text(request: ProcessTextRequest):
    """Process text input with GPT-OSS AI via Groq API"""
    try:
        if not groq_available:
            # Return mock response if Groq API not available
            return {
                "status": "success",
                "response": f"I understand you said: {request.text}",
                "intent": "general_query",
                "confidence": 0.8,
                "mock": True
            }
        
        # Use Groq client for real AI processing with GPT-OSS 20B
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Provide clear, concise responses."},
                {"role": "user", "content": request.text}
            ],
            max_completion_tokens=150,
            temperature=0.7,
            reasoning_effort="medium"
        )
        
        ai_response = completion.choices[0].message.content.strip()
        
        logger.info(f"GPT-OSS 20B processed: '{request.text}' -> '{ai_response[:100]}...'")
        return {
            "status": "success",
            "response": ai_response,
            "intent": "processed",
            "confidence": 0.95,
            "mock": False
        }
            
    except Exception as e:
        logger.error(f"GPT-OSS processing failed: {e}")
        return {
            "status": "success",
            "response": f"I understand you said: {request.text}",
            "intent": "fallback",
            "confidence": 0.5,
            "error": str(e),
            "mock": True
        }

@app.post("/gpt-oss/analyze-intent")
async def analyze_intent(request: IntentRequest):
    """Analyze user intent from input"""
    try:
        user_input = request.user_input.lower()
        
        # Simple intent classification
        intent_mapping = {
            "call": ["call", "phone", "dial", "ring"],
            "email": ["email", "mail", "send message", "compose"],
            "calendar": ["calendar", "schedule", "appointment", "meeting", "remind"],
            "app": ["open", "launch", "start app", "run"],
            "weather": ["weather", "temperature", "forecast", "rain"],
            "time": ["time", "clock", "what time"],
            "music": ["music", "song", "play", "spotify"],
            "search": ["search", "google", "find", "look up"]
        }
        
        detected_intent = "general"
        confidence = 0.7
        
        for intent, keywords in intent_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                detected_intent = intent
                confidence = 0.9
                break
        
        # Extract entities
        entities = {}
        if "call" in user_input:
            # Extract phone number or contact name
            words = user_input.split()
            for i, word in enumerate(words):
                if word in ["call", "phone", "dial"]:
                    if i + 1 < len(words):
                        entities["contact"] = words[i + 1]
                    break
        
        return {
            "intent": detected_intent,
            "confidence": confidence,
            "entities": entities,
            "original_text": request.user_input,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze intent: {str(e)}")

@app.post("/gpt-oss/generate-response")
async def generate_response(request: ProcessTextRequest):
    """Generate conversational response using Groq GPT-OSS"""
    try:
        if not groq_available:
            # Mock conversational responses
            responses = [
                f"I understand you're asking about: {request.text}",
                f"That's interesting! You mentioned: {request.text}",
                f"Let me help you with: {request.text}",
                f"I can assist with that. You said: {request.text}"
            ]
            import random
            response = random.choice(responses)
        else:
            # Use Groq client for conversational response
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant named June. Be conversational and helpful."},
                    {"role": "user", "content": request.text}
                ],
                max_completion_tokens=128,
                temperature=0.7,
                reasoning_effort="medium"
            )
            response = completion.choices[0].message.content.strip()
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "conversation_id": "default"
        }
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "response": "I'm here to help! Could you please rephrase that?",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/gpt-oss/status")
async def get_gpt_oss_status():
    """Get GPT-OSS service status"""
    model_status = "groq-api" if groq_available else "mock-mode"
    return {
        "service": "gpt-oss",
        "model": model_status,
        "model_name": MODEL_NAME if groq_available else "none",
        "status": "ready"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "GPT-OSS Server for Voice AI Agent", "version": "1.0.0"}

if __name__ == "__main__":
    logger.info("Starting GPT-OSS Server on http://0.0.0.0:5003")
    uvicorn.run(app, host="0.0.0.0", port=5003)
