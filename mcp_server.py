"""
Simple MCP Server for Voice AI Agent
Provides Google services integration (Gmail, Calendar, etc.) on port 8080
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Google Services Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailRequest(BaseModel):
    to: str
    subject: Optional[str] = None
    body: Optional[str] = None
    action: str = "compose"  # compose, send, read

class CalendarRequest(BaseModel):
    action: str  # create, list, update, delete
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    description: Optional[str] = None

@app.post("/email")
async def handle_email(request: EmailRequest):
    """
    Handle email operations via Gmail API
    """
    try:
        logger.info(f"📧 Email request: {request.action} to {request.to}")
        
        # Mock email handling
        if request.action == "compose":
            return JSONResponse({
                "status": "success",
                "action": "email_composed",
                "to": request.to,
                "subject": request.subject or "No Subject",
                "message": f"Email draft created for {request.to}",
                "mock": True
            })
        elif request.action == "send":
            return JSONResponse({
                "status": "success", 
                "action": "email_sent",
                "to": request.to,
                "message": f"Email sent to {request.to}",
                "mock": True
            })
        else:
            return JSONResponse({
                "status": "success",
                "action": "email_opened",
                "message": "Gmail opened",
                "mock": True
            })
            
    except Exception as e:
        logger.error(f"Email handling error: {e}")
        raise HTTPException(status_code=500, detail=f"Email operation failed: {str(e)}")

@app.post("/calendar")
async def handle_calendar(request: CalendarRequest):
    """
    Handle calendar operations via Google Calendar API
    """
    try:
        logger.info(f"📅 Calendar request: {request.action}")
        
        # Mock calendar handling
        if request.action == "create":
            return JSONResponse({
                "status": "success",
                "action": "event_created", 
                "title": request.title or "New Event",
                "date": request.date or "today",
                "time": request.time or "now",
                "message": f"Calendar event '{request.title}' created",
                "mock": True
            })
        elif request.action == "list":
            return JSONResponse({
                "status": "success",
                "action": "events_listed",
                "events": [
                    {"title": "Meeting with John", "time": "2pm"},
                    {"title": "Doctor appointment", "time": "4pm"}
                ],
                "message": "Calendar events retrieved",
                "mock": True
            })
        else:
            return JSONResponse({
                "status": "success",
                "action": "calendar_opened",
                "message": "Google Calendar opened",
                "mock": True
            })
            
    except Exception as e:
        logger.error(f"Calendar handling error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar operation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "port": 8080,
        "services": ["gmail", "calendar", "contacts"],
        "google_auth": "mock_mode"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP Google Services Server",
        "status": "running", 
        "endpoints": {
            "email": "/email (POST)",
            "calendar": "/calendar (POST)",
            "health": "/health (GET)"
        }
    }

if __name__ == "__main__":
    logger.info("🔗 Starting MCP Server on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
