#!/usr/bin/env python3
"""
Memory Helper - Quick way to save prompts and information to CPQ Memory
Usage: 
  - As a script: python memory_helper.py "Your memory text here"
  - As a function: from memory_helper import remember
"""

import sys
import subprocess
import json
from datetime import datetime

def remember(text, entity_type="User Note", entity_name=None):
    """
    Save text to CPQ Memory.
    
    Args:
        text: The text to remember
        entity_type: Type of entity (default: "User Note")
        entity_name: Name of entity (default: auto-generated with timestamp)
    
    Returns:
        True if successful, False otherwise
    """
    if not entity_name:
        entity_name = f"Note {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Prepare the memory command
    memory_data = {
        "entities": [{
            "name": entity_name,
            "entityType": entity_type,
            "observations": [text]
        }]
    }
    
    # Use mcp CLI or API to save
    try:
        # This would integrate with your MCP memory server
        print(f"💾 Saving to memory: {entity_name}")
        print(f"   Type: {entity_type}")
        print(f"   Content: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        # Here you would call the actual MCP memory API
        # For now, we'll save to a local file as a demo
        with open('.memories.json', 'a') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'entity': entity_name,
                'type': entity_type,
                'content': text
            }, f)
            f.write('\n')
        
        print("✅ Saved to memory!")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to memory: {e}")
        return False

def main():
    """Command line interface for quick memory saving."""
    if len(sys.argv) < 2:
        print("Usage: memory_helper.py <text to remember> [entity_name] [entity_type]")
        print("\nExamples:")
        print('  memory_helper.py "Remember to test the upload function with production data"')
        print('  memory_helper.py "API endpoint is /api/v2/upload" "API Documentation" "Technical Note"')
        sys.exit(1)
    
    text = sys.argv[1]
    entity_name = sys.argv[2] if len(sys.argv) > 2 else None
    entity_type = sys.argv[3] if len(sys.argv) > 3 else "User Note"
    
    remember(text, entity_type, entity_name)

if __name__ == "__main__":
    main()