#!/usr/bin/env python3
"""Test script for the voice AI server"""

import requests
import json

def test_list_functionality():
    """Test the list functionality"""
    try:
        # Test query endpoint
        url = "http://localhost:5005/query"
        data = {"text": "add milk, eggs and bread to the shopping list"}
        
        print(f"Testing: {data['text']}")
        
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_list_functionality()
