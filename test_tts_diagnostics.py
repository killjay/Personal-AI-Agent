#!/usr/bin/env python3
"""
Diagnostic script to test TTS functionality end-to-end
"""

import requests
import json
import time

def test_servers():
    """Test all server endpoints"""
    servers = [
        ("Main Server", "http://localhost:5005/health"),
        ("Whisper Server", "http://localhost:5004/health"), 
        ("TTS Server", "http://localhost:5002/health"),
        ("TTS Test Server", "http://localhost:5006/health")
    ]
    
    print("🔍 TESTING SERVER CONNECTIVITY")
    print("=" * 50)
    
    for name, url in servers:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {data.get('status', 'OK')}")
            else:
                print(f"⚠️  {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Not responding ({e})")
    
    print("\n🌐 TESTING EXTERNAL CONNECTIVITY")
    print("=" * 50)
    
    # Test external IP connectivity (what Android app would use)
    external_url = "http://192.168.1.120:5005/health"
    try:
        response = requests.get(external_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ External IP accessible: {external_url}")
        else:
            print(f"⚠️  External IP issue: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ External IP not accessible: {e}")
        print("💡 This could be why the Android app cannot connect!")
    
    print("\n📱 ANDROID TTS TEST")
    print("=" * 50)
    print("1. Make sure your Android device is connected to the same Wi-Fi network")
    print("2. Update Android app server URL to: http://192.168.1.120:5006/voice")
    print("3. Test recording and check if TTS works")
    print("4. Check Android logs: adb logcat -s VoiceAgent")

if __name__ == "__main__":
    test_servers()
