#!/usr/bin/env python3
"""
Test the complete voice workflow:
Android app → Whisper → Main Server → Gptoss → MCP Server → Response
"""

import requests
import json

def test_gmail_query():
    """Test email query workflow"""
    print("🧪 Testing Gmail Query Workflow...")
    print("=" * 50)
    
    # Simulate the query that would come from Android app after Whisper transcription
    test_query = "do I have new emails"
    
    print(f"📱 Simulated query: '{test_query}'")
    
    # Test MCP server status first
    try:
        mcp_response = requests.get("http://localhost:5003/auth/status", timeout=3)
        mcp_data = mcp_response.json()
        print(f"🔗 MCP Server Status: {'✅ Authenticated' if mcp_data.get('authenticated') else '❌ Not Authenticated'}")
        
        if not mcp_data.get("authenticated"):
            print(f"🔑 Please authenticate at: http://localhost:5003/auth/login")
            return
            
    except Exception as e:
        print(f"❌ MCP Server Error: {e}")
        return
    
    # Test main server processing (this simulates what happens after Whisper)
    try:
        # Create a mock request to the voice endpoint
        # In real usage, this would be audio file from Android app
        print(f"🎤 Sending query to main server...")
        
        # For testing, we'll directly call our Gmail handler
        # In real usage, this happens inside the /voice endpoint after Whisper
        
        # Test Gmail data fetch
        gmail_response = requests.get("http://localhost:5003/gmail/unread", timeout=10)
        if gmail_response.status_code == 200:
            gmail_data = gmail_response.json()
            email_count = len(gmail_data.get("emails", []))
            print(f"📧 Gmail Response: {email_count} unread emails found")
            
            if email_count > 0:
                print("📋 Sample emails:")
                for i, email in enumerate(gmail_data["emails"][:3]):
                    print(f"   {i+1}. From: {email.get('sender', 'Unknown')}")
                    print(f"      Subject: {email.get('subject', 'No Subject')}")
        else:
            print(f"❌ Gmail API Error: {gmail_response.status_code}")
            return
            
    # Test Gptoss integration with the data
    print(f"🤖 Testing Gptoss integration...")
        
        # This simulates what happens in handle_gmail_calendar_query
        headers = {
            "x-api-key": "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",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        context_data = f"Gmail Data ({email_count} emails):\n"
        if email_count > 0:
            for email in gmail_data["emails"][:3]:
                context_data += f"- From: {email.get('sender', 'Unknown')}\n"
                context_data += f"  Subject: {email.get('subject', 'No Subject')}\n"
        
    gptoss_prompt = f"""You are June, a helpful voice assistant. The user asked: "{test_query}"

Here is the relevant data from their Gmail:
{context_data}

Based on this real data, provide a natural, conversational response that directly answers their question. Keep it under 50 words for voice delivery."""

    gptoss_payload = {
            "model": "gptoss-20b-20240307",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": gptoss_prompt}]
        }
        
    gptoss_response = requests.post("https://api.gptoss.com/v1/messages", headers=headers, json=gptoss_payload, timeout=30)
        
        if gptoss_response.status_code == 200:
            gptoss_data = gptoss_response.json()
            response_text = gptoss_data["content"][0]["text"].strip()
            print(f"💬 Gptoss Response: '{response_text}'")
            print(f"📱 This would be spoken by the Android app!")
        else:
            print(f"❌ Gptoss API Error: {gptoss_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

def test_calendar_query():
    """Test calendar query workflow"""
    print("\n🧪 Testing Calendar Query Workflow...")
    print("=" * 50)
    
    test_query = "what's on my schedule today"
    print(f"📱 Simulated query: '{test_query}'")
    
    try:
        # Test Calendar data fetch
        calendar_response = requests.get("http://localhost:5003/calendar/today", timeout=10)
        if calendar_response.status_code == 200:
            calendar_data = calendar_response.json()
            event_count = len(calendar_data.get("events", []))
            print(f"📅 Calendar Response: {event_count} events found for today")
            
            if event_count > 0:
                print("📋 Today's events:")
                for i, event in enumerate(calendar_data["events"][:3]):
                    print(f"   {i+1}. {event.get('title', 'No Title')}")
                    print(f"      Time: {event.get('start', 'Unknown time')}")
            
            # Test Gptoss response
            context_data = f"Calendar Data ({event_count} events today):\n"
            if event_count > 0:
                for event in calendar_data["events"][:3]:
                    context_data += f"- {event.get('title', 'No Title')} at {event.get('start', 'Unknown time')}\n"
            
            gptoss_prompt = f"""You are June, a helpful voice assistant. The user asked: "{test_query}"

Here is their calendar data:
{context_data}

Provide a natural response about their schedule. Keep it under 50 words."""

            headers = {
                "x-api-key": "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",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            gptoss_payload = {
                "model": "gptoss-20b-20240307",
                "max_tokens": 150,
                "messages": [{"role": "user", "content": claude_prompt}]
            }
            
            claude_response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=claude_payload, timeout=30)
            
            if claude_response.status_code == 200:
                claude_data = claude_response.json()
                response_text = claude_data["content"][0]["text"].strip()
                print(f"💬 Claude Response: '{response_text}'")
                print(f"📱 This would be spoken by the Android app!")
        else:
            print(f"❌ Calendar API Error: {calendar_response.status_code}")
            
    except Exception as e:
        print(f"❌ Calendar Test Error: {e}")

if __name__ == "__main__":
    print("🚀 Voice AI Agent - Complete Workflow Test")
    print("==========================================")
    print("Testing the complete flow:")
    print("Android App → Whisper → Main Server → Claude → MCP Server → Response")
    print()
    
    test_gmail_query()
    test_calendar_query()
    
    print("\n✅ Workflow Test Complete!")
    print("\n🔍 Next Steps:")
    print("1. Authenticate with Google: http://localhost:5003/auth/login")
    print("2. Test with real voice input through Android app")
    print("3. The workflow will be:")
    print("   📱 Record voice → 🎤 Whisper transcription → 🤖 Main server")
    print("   → 🧠 Claude analysis → 📧📅 Real Gmail/Calendar data → 🔊 Voice response")
