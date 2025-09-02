#!/usr/bin/env python3
"""
Test script for the enhanced voice endpoint
Tests both JSON and multipart form data formats
"""

import requests
import base64
import json
import os

# Test audio data (small WAV file header + some data)
test_audio_bytes = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00' + b'\x00' * 1000

def test_json_request():
    """Test the endpoint with JSON request (original format)"""
    print("Testing JSON request format...")
    
    # Encode audio as base64
    audio_base64 = base64.b64encode(test_audio_bytes).decode('utf-8')
    
    payload = {
        "audio": audio_base64
    }
    
    try:
        response = requests.post(
            'http://localhost:5005/voice',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ JSON request test PASSED")
        else:
            print("❌ JSON request test FAILED")
            
    except Exception as e:
        print(f"❌ JSON request test ERROR: {e}")

def test_multipart_file():
    """Test the endpoint with multipart form data (file upload)"""
    print("\nTesting multipart file upload...")
    
    try:
        # Create a temporary file
        with open('test_audio.wav', 'wb') as f:
            f.write(test_audio_bytes)
        
        # Send as file upload
        with open('test_audio.wav', 'rb') as f:
            files = {'audio': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(
                'http://localhost:5005/voice',
                files=files,
                timeout=10
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Multipart file test PASSED")
        else:
            print("❌ Multipart file test FAILED")
            
        # Cleanup
        os.remove('test_audio.wav')
        
    except Exception as e:
        print(f"❌ Multipart file test ERROR: {e}")

def test_form_data():
    """Test the endpoint with form data (base64 in form field)"""
    print("\nTesting form data with base64...")
    
    # Encode audio as base64
    audio_base64 = base64.b64encode(test_audio_bytes).decode('utf-8')
    
    try:
        data = {'audio_data': audio_base64}
        response = requests.post(
            'http://localhost:5005/voice',
            data=data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Form data test PASSED")
        else:
            print("❌ Form data test FAILED")
            
    except Exception as e:
        print(f"❌ Form data test ERROR: {e}")

def test_health_endpoints():
    """Test that all servers are running"""
    print("\nTesting server health...")
    
    servers = [
        ("Main AI Server", "http://localhost:5005/health"),
        ("TTS Server", "http://localhost:5002/health"),
        ("Whisper Server", "http://localhost:5004/health"),
        ("MCP Server", "http://localhost:8080/health")
    ]
    
    for name, url in servers:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"❌ {name}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Not reachable - {e}")

if __name__ == "__main__":
    print("🧪 Testing Voice Endpoint...")
    print("=" * 50)
    
    # Test server health first
    test_health_endpoints()
    
    # Test different request formats
    test_json_request()
    test_multipart_file()
    test_form_data()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
