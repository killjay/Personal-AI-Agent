#!/usr/bin/env python3

import requests
import json

def test_server_query(query, description):
    """Test the server with a specific query"""
    print(f"\n{'='*50}")
    print(f"🔍 Testing: {description}")
    print(f"📝 Query: '{query}'")
    print(f"{'='*50}")
    
    try:
        # Create mock audio data for the query
        data = {
            "text": query,
            "action": "email_test"
        }
        
        # Test direct endpoint to simulate voice processing
        response = requests.post("http://localhost:5005/voice", files={'file': ('test.wav', b'fake_audio_data')}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Response: {result.get('message', 'No message')}")
            print(f"📋 Action: {result.get('action', 'No action')}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")

def test_mcp_connection():
    """Test if MCP server is responding"""
    print(f"\n{'='*50}")
    print("🔗 Testing MCP Server Connection")
    print(f"{'='*50}")
    
    try:
        # Test MCP server health
        mcp_response = requests.get("http://localhost:8080/health", timeout=5)
        if mcp_response.status_code == 200:
            print("✅ MCP Server: Running")
        else:
            print(f"⚠️ MCP Server: Responding but status {mcp_response.status_code}")
            
        # Test auth status
        auth_response = requests.get("http://localhost:8080/auth/status", timeout=5)
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            if auth_data.get("authenticated", False):
                print("✅ MCP Authentication: Authenticated")
            else:
                print("⚠️ MCP Authentication: Not authenticated")
        
        # Test Gmail endpoint
        gmail_response = requests.get("http://localhost:8080/gmail/unread", timeout=5)
        if gmail_response.status_code == 200:
            gmail_data = gmail_response.json()
            email_count = len(gmail_data.get('emails', []))
            print(f"✅ Gmail Endpoint: Found {email_count} emails")
        else:
            print(f"❌ Gmail Endpoint: Error {gmail_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ MCP Server Connection Error: {e}")

def main():
    print("🎯 EMAIL QUERY SPECIFICITY TEST")
    print("Testing improved query routing logic...")
    
    # Test MCP connection first
    test_mcp_connection()
    
    # Note: Since we can't easily simulate real voice data, this will just test server availability
    # The real test would be using the Android app
    
    print(f"\n{'='*50}")
    print("📱 TESTING INSTRUCTIONS")
    print(f"{'='*50}")
    print("1. Use your Android app to test these queries:")
    print("   📧 'Do I have any new emails?' - Should mention ONLY emails")
    print("   📧 'Check my inbox' - Should mention ONLY emails") 
    print("   📅 'What's on my calendar today?' - Should mention ONLY calendar")
    print("   📅 'Do I have any meetings?' - Should mention ONLY calendar")
    print("")
    print("2. Expected behavior:")
    print("   ✅ Email queries = Email responses only")
    print("   ✅ Calendar queries = Calendar responses only")  
    print("   ❌ No more mixed responses!")
    print("")
    print("3. Key improvements:")
    print("   🔧 Smarter keyword detection")
    print("   🔧 Prioritizes specific queries over time-based words")
    print("   🔧 Only fetches relevant data")
    print("   🔧 Gptoss gets context-specific prompts")

if __name__ == "__main__":
    main()
