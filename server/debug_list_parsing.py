#!/usr/bin/env python3
"""Test script to debug list parsing"""

def test_list_parsing():
    user_query = "Add egg, milk and bread to the shopping list."
    text_lower = user_query.lower()
    
    print(f"Original query: {user_query}")
    print(f"Lowercase: {text_lower}")
    
    # Look for items - handle different sentence structures
    items = []
    list_content = ""
    
    # Pattern 1: "Add X, Y, Z to [shopping/grocery] list"
    if "to" in text_lower and any(word in text_lower for word in ["shopping list", "grocery list", "todo list", "list"]):
        print("Pattern 1: Found 'Add X to list' structure")
        # Find items between "add" and "to"
        if text_lower.startswith("add "):
            parts = text_lower.split(" to ", 1)
            if len(parts) > 1:
                # Get everything after "add " and before " to"
                list_content = parts[0][4:].strip()  # Remove "add " prefix
                print(f"Extracted content: '{list_content}'")
    
    # Pattern 2: "Shopping/grocery list: X, Y, Z" or "Add to list: X, Y, Z"
    elif ":" in user_query:
        print("Pattern 2: Found colon structure")
        parts = user_query.split(":", 1)
        if len(parts) > 1:
            list_content = parts[1].strip()
            print(f"Extracted content: '{list_content}'")
    
    # Pattern 3: Look for items after trigger words
    if not list_content:
        print("Pattern 3: Using trigger words")
        trigger_words = ["add to list", "shopping list", "grocery list", "todo list", "checklist", "shopping", "grocery", "purchase", "store", "market", "buy", "shop", "add", "list"]
        
        for trigger in trigger_words:
            if trigger in text_lower:
                parts = user_query.lower().split(trigger, 1)
                print(f"Found trigger: '{trigger}'")
                print(f"Split parts: {parts}")
                if len(parts) > 1:
                    list_content = parts[1].strip()
                    print(f"Content after trigger: '{list_content}'")
                    
                    # Remove common prefixes and words
                    original_content = list_content
                    for prefix in ["of", "for", ":", "-", "to", "the", "my", "some"]:
                        if list_content.startswith(prefix + " "):
                            list_content = list_content[len(prefix):].strip()
                            print(f"Removed prefix '{prefix}': '{list_content}'")
                    break
    
    print(f"\nFinal list_content: '{list_content}'")
    
    # Parse items (handle multiple separators in sequence)
    items = []
    if list_content:
        # First, normalize the text - replace multiple separators with commas
        normalized_content = list_content
        print(f"Original content: '{normalized_content}'")
        # Replace " and " with ", " 
        normalized_content = normalized_content.replace(" and ", ", ")
        print(f"After replacing 'and': '{normalized_content}'")
        # Replace " & " with ", "
        normalized_content = normalized_content.replace(" & ", ", ")
        print(f"After replacing '&': '{normalized_content}'")
        # Replace "; " with ", "
        normalized_content = normalized_content.replace(";", ",")
        print(f"After replacing ';': '{normalized_content}'")
        
        # Now split by comma
        raw_items = normalized_content.split(",")
        print(f"Split by comma: {raw_items}")
        
        # Clean up items
        items = [item.strip() for item in raw_items if item.strip()]
        print(f"Final items after cleanup: {items}")
    
    if not items:
        items = ["Item from voice note"]
        print(f"No items found, using fallback: {items}")
    
    print(f"\nFinal result: {items}")
    return items

if __name__ == "__main__":
    test_list_parsing()
