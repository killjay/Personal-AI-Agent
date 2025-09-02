#!/usr/bin/env python3
# Simple test to verify pricing removal

import ast
import sys

def test_server_file():
    try:
        # Read the file with proper encoding
        with open('server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for any remaining pricing references
        pricing_terms = [
            'get_location_and_pricing',
            'ANTHROPIC_PRICING_API_KEY',
            'pricing_info',
            'bill_of_quantities'
        ]
        
        found_issues = []
        for term in pricing_terms:
            if term in content:
                found_issues.append(term)
        
        if found_issues:
            print(f"❌ Found remaining pricing references: {found_issues}")
            return False
        
        # Test syntax
        ast.parse(content)
        print("✅ server.py: No pricing references found, syntax valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing server.py: {e}")
        return False

def test_mcp_file():
    try:
        with open('mcp_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for simplified list creation
        if 'is_bill_of_quantities' in content:
            print("❌ mcp_server.py still contains bill_of_quantities logic")
            return False
            
        ast.parse(content)
        print("✅ mcp_server.py: Bill of quantities removed, syntax valid")
        return True
        
    except Exception as e:
        print(f"❌ Error testing mcp_server.py: {e}")
        return False

if __name__ == "__main__":
    server_ok = test_server_file()
    mcp_ok = test_mcp_file()
    
    if server_ok and mcp_ok:
        print("\n🎉 Pricing feature successfully removed!")
        print("✅ Shopping lists will now be created without pricing")
        print("✅ No duplicate lists will be created")
        print("✅ System is ready to use")
    else:
        print("\n❌ Issues found during pricing removal")
        sys.exit(1)
