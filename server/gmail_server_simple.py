#!/usr/bin/env python3
"""
Simple Gmail API Server for Voice AI Agent
Uses FastAPI for consistency with other servers
"""

import os
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gmail API Server", description="Gmail integration for Voice AI Agent")

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
    return {"status": "Gmail Server is running", "service": "gmail", "port": 5000}

@app.get("/emails/recent")
async def get_recent_emails():
    """Get recent emails"""
    try:
        # Mock data for now - replace with actual Gmail API integration
        mock_emails = [
            {
                "id": "email_001",
                "subject": "Welcome to Voice AI Agent",
                "sender": "noreply@example.com",
                "snippet": "Thank you for setting up your Voice AI Agent...",
                "timestamp": datetime.now().isoformat(),
                "unread": True
            },
            {
                "id": "email_002", 
                "subject": "System Update Available",
                "sender": "updates@voiceai.com",
                "snippet": "A new system update is available for download...",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "unread": False
            }
        ]
        
        logger.info(f"Retrieved {len(mock_emails)} recent emails")
        return {"emails": mock_emails, "count": len(mock_emails)}
        
    except Exception as e:
        logger.error(f"Error fetching recent emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@app.get("/emails/unread")
async def get_unread_emails():
    """Get unread emails"""
    try:
        mock_unread = [
            {
                "id": "email_001",
                "subject": "Welcome to Voice AI Agent", 
                "sender": "noreply@example.com",
                "snippet": "Thank you for setting up your Voice AI Agent...",
                "timestamp": datetime.now().isoformat(),
                "unread": True
            }
        ]
        
        logger.info(f"Retrieved {len(mock_unread)} unread emails")
        return {"emails": mock_unread, "count": len(mock_unread)}
        
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch unread emails: {str(e)}")

@app.post("/emails/send")
async def send_email(email_data: dict):
    """Send an email"""
    try:
        # Mock sending email
        logger.info(f"Sending email to: {email_data.get('to', 'unknown')}")
        
        return {
            "status": "sent",
            "message_id": f"sent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Gmail Server for Voice AI Agent", "version": "1.0.0"}

if __name__ == "__main__":
    logger.info("Starting Gmail Server on http://0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
