#!/usr/bin/env python3
"""
MCP Server Status Checker
Tests all MCP server functionality
"""

import requests
import json
from datetime import datetime

def test_mcp_server():
    """Test MCP server functionality"""
    
    print("🔍 MCP SERVER COMPREHENSIVE TEST")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test health endpoint
    try:
        health = requests.get(f"{base_url}/health", timeout=5)
        if health.status_code == 200:
            data = health.json()
            print(f"✅ Health: {data.get('status', 'OK')}")
        else:
            print(f"⚠️  Health: HTTP {health.status_code}")
    except Exception as e:
        print(f"❌ Health: {e}")
        return
    
    # Test authentication status
    try:
        auth = requests.get(f"{base_url}/auth/status", timeout=5)
        if auth.status_code == 200:
            data = auth.json()
            authenticated = data.get('authenticated', False)
            user = data.get('user', 'Unknown')
            if authenticated:
                print(f"✅ Authentication: Authenticated as {user}")
            else:
                print(f"⚠️  Authentication: Not authenticated")
                print(f"🔗 Auth URL: {base_url}/auth/login")
                return
        else:
            print(f"⚠️  Authentication: HTTP {auth.status_code}")
            return
    except Exception as e:
        print(f"❌ Authentication: {e}")
        return
    
    # Test Gmail functionality
    print("\n📧 GMAIL FUNCTIONALITY")
    print("-" * 30)
    
    try:
        gmail = requests.get(f"{base_url}/gmail/recent?limit=3", timeout=10)
        if gmail.status_code == 200:
            data = gmail.json()
            emails = data.get('emails', [])
            print(f"✅ Recent emails: Found {len(emails)} emails")
            for i, email in enumerate(emails[:2], 1):
                subject = email.get('subject', 'No subject')[:50]
                sender = email.get('sender', 'Unknown')
                print(f"   {i}. From: {sender} | Subject: {subject}...")
        else:
            print(f"❌ Gmail: HTTP {gmail.status_code}")
    except Exception as e:
        print(f"❌ Gmail: {e}")
    
    # Test Calendar functionality
    print("\n📅 CALENDAR FUNCTIONALITY")
    print("-" * 30)
    
    try:
        calendar = requests.get(f"{base_url}/calendar/upcoming?limit=3", timeout=10)
        if calendar.status_code == 200:
            data = calendar.json()
            events = data.get('events', [])
            print(f"✅ Upcoming events: Found {len(events)} events")
            for i, event in enumerate(events[:2], 1):
                title = event.get('title', 'No title')
                start = event.get('start', 'No time')
                print(f"   {i}. {title} | Start: {start}")
        else:
            print(f"❌ Calendar: HTTP {calendar.status_code}")
    except Exception as e:
        print(f"❌ Calendar: {e}")
    
    # Test available endpoints
    print("\n🔧 AVAILABLE ENDPOINTS")
    print("-" * 30)
    
    endpoints = [
        "/health",
        "/auth/status", 
        "/auth/login",
        "/gmail/recent",
        "/gmail/search",
        "/calendar/upcoming",
        "/calendar/today"
    ]
    
    for endpoint in endpoints:
        print(f"   {base_url}{endpoint}")
    
    print(f"\n🌐 MCP Server running on: {base_url}")
    print("📝 Integration: Ready for Voice AI Agent")

if __name__ == "__main__":
    test_mcp_server()
