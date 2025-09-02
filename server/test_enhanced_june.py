#!/usr/bin/env python3
"""
Test script for enhanced June Voice AI functionality
Tests all major features: calling, dialing, email, calendar, notes, lists
"""

import requests
import json
import time

SERVER_URL = "http://localhost:5005/process"

def test_command(text, expected_action=None):
    """Test a voice command"""
    print(f"\n🎤 Testing: '{text}'")
    print("-" * 50)
    
    try:
        response = requests.post(SERVER_URL, 
                               json={"text": text}, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            
            if expected_action:
                actual_action = result.get("action")
                if actual_action == expected_action:
                    print(f"✅ Action matches expected: {expected_action}")
                else:
                    print(f"❌ Action mismatch - Expected: {expected_action}, Got: {actual_action}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)  # Rate limiting

def main():
    print("🎯 Testing Enhanced June Voice AI Functionality")
    print("=" * 60)
    
    # Test direct dialing
    test_command("dial 200", "call")
    test_command("dial 26181258", "call") 
    test_command("phone 123456", "call")
    
    # Test contact calling
    test_command("call John", "call")
    test_command("call mom", "call")
    test_command("ring Sarah", "call")
    
    # Test email functionality
    test_command("check my email", "email")
    test_command("send email to John", "email")
    test_command("gmail inbox", "email")
    
    # Test calendar functionality  
    test_command("schedule a meeting", "calendar")
    test_command("what meetings do I have today", "calendar")
    test_command("book appointment with doctor", "calendar")
    
    # Test notes functionality
    test_command("take a note", "note")
    test_command("remember to buy milk", "note")
    test_command("write down meeting notes", "note")
    
    # Test list functionality
    test_command("add milk to shopping list", "list")
    test_command("create grocery list", "list")
    test_command("shopping items", "list")
    
    # Test document creation
    test_command("draft a letter", "document")
    test_command("create resume", "document") 
    test_command("write proposal", "document")
    
    print("\n🏁 Testing completed!")

if __name__ == "__main__":
    main()
