#!/usr/bin/env python3
"""
Simple Calendar API Server for Voice AI Agent  
Uses FastAPI for calendar management
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

app = FastAPI(title="Calendar API Server", description="Calendar integration for Voice AI Agent")

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
    return {"status": "Calendar Server is running", "service": "calendar", "port": 5001}

@app.get("/calendar/upcoming")
async def get_upcoming_events():
    """Get upcoming calendar events"""
    try:
        # Mock calendar events
        now = datetime.now()
        mock_events = [
            {
                "id": "event_001",
                "title": "Voice AI Agent Demo",
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=3)).isoformat(),
                "description": "Demonstration of voice AI capabilities",
                "location": "Virtual Meeting"
            },
            {
                "id": "event_002", 
                "title": "Team Standup",
                "start_time": (now + timedelta(days=1, hours=9)).isoformat(),
                "end_time": (now + timedelta(days=1, hours=9, minutes=30)).isoformat(),
                "description": "Daily team synchronization",
                "location": "Conference Room A"
            }
        ]
        
        logger.info(f"Retrieved {len(mock_events)} upcoming events")
        return {"events": mock_events, "count": len(mock_events)}
        
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.get("/calendar/today")
async def get_today_events():
    """Get today's calendar events"""
    try:
        # Mock today's events
        now = datetime.now()
        today_events = [
            {
                "id": "event_today_001",
                "title": "Voice AI Development",
                "start_time": (now.replace(hour=14, minute=0)).isoformat(),
                "end_time": (now.replace(hour=16, minute=0)).isoformat(),
                "description": "Continue development on voice AI features",
                "location": "Development Lab"
            }
        ]
        
        logger.info(f"Retrieved {len(today_events)} events for today")
        return {"events": today_events, "count": len(today_events), "date": now.date().isoformat()}
        
    except Exception as e:
        logger.error(f"Error fetching today's events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch today's events: {str(e)}")

@app.post("/calendar/create")
async def create_event(event_data: dict):
    """Create a new calendar event"""
    try:
        # Mock event creation
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Creating event: {event_data.get('title', 'Untitled Event')}")
        
        return {
            "status": "created",
            "event_id": event_id,
            "title": event_data.get('title', 'New Event'),
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Calendar Server for Voice AI Agent", "version": "1.0.0"}

if __name__ == "__main__":
    logger.info("Starting Calendar Server on http://0.0.0.0:5001")
    uvicorn.run(app, host="0.0.0.0", port=5001)
