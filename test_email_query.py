#!/usr/bin/env python3
"""
Email Query Test Script
Tests the email query functionality with better error reporting
"""

import requests
import json
import time

def test_email_query():
    """Test email query functionality"""
    print("🔍 TESTING EMAIL QUERY FUNCTIONALITY")
    print("=" * 50)
    
    # Wait for servers to start
    print("⏳ Waiting for servers to start...")
    time.sleep(15)
    
    # Test server connectivity
    servers = [
        ("MCP Server", "http://localhost:8080/health"),
        ("Main Server", "http://localhost:5005/health"),
        ("Whisper Server", "http://localhost:5004/health"),
        ("TTS Server", "http://localhost:5002/health")
    ]
    
    print("\n🔍 Server Status Check:")
    all_running = True
    for name, url in servers:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: HTTP {response.status_code}")
                all_running = False
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Not responding ({e})")
            all_running = False
    
    if not all_running:
        print("\n❌ Not all servers are running. Email queries may fail.")
        return
    
    # Test direct MCP email endpoint
    print("\n📧 Testing MCP Gmail endpoint directly:")
    try:
        gmail_response = requests.get("http://localhost:8080/gmail/recent", timeout=30)
        if gmail_response.status_code == 200:
            data = gmail_response.json()
            print(f"✅ MCP Gmail endpoint: Found {len(data.get('emails', []))} emails")
        else:
            print(f"❌ MCP Gmail endpoint failed: HTTP {gmail_response.status_code}")
            print(f"Response: {gmail_response.text}")
    except requests.exceptions.Timeout:
        print("❌ MCP Gmail endpoint: Timeout after 30 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ MCP Gmail endpoint: Connection error - MCP server not responding")
    except Exception as e:
        print(f"❌ MCP Gmail endpoint: {e}")
    
    print("\n📱 Ready for Android app testing!")
    print("Try asking: 'Check my emails' or 'Do I have any new messages?'")
    print("The improved error handling should now give you better feedback.")

if __name__ == "__main__":
    test_email_query()
