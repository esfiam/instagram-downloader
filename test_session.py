#!/usr/bin/env python3
"""
Test script to check if the Instagram session has been saved correctly.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

def check_session_file(session_path):
    """Check if a session file exists and is valid."""
    
    # Check if the session file exists
    if not session_path.exists():
        print(f"❌ Session file not found at {session_path}")
        return False
    
    print(f"✅ Session file exists at {session_path}")
    
    # Check if the file contains valid JSON
    try:
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        print("✅ Session file contains valid JSON data")
    except json.JSONDecodeError:
        print("❌ Session file does not contain valid JSON data")
        return False
    
    # Check if the JSON has the expected structure
    if not isinstance(session_data, dict):
        print("❌ Session data is not a dictionary")
        return False
    
    # Check for required keys in the session data
    required_keys = ['cookies', 'origins']
    missing_keys = [key for key in required_keys if key not in session_data]
    
    if missing_keys:
        print(f"❌ Session data is missing required keys: {', '.join(missing_keys)}")
        return False
    
    print("✅ Session data has the expected structure")
    
    # Check if there are any cookies
    if not session_data.get('cookies', []):
        print("⚠️ Session data doesn't contain any cookies")
    else:
        print(f"✅ Session contains {len(session_data['cookies'])} cookies")
    
    # Print some basic info about the session
    print("\nSession Summary:")
    print(f"- File size: {session_path.stat().st_size} bytes")
    print(f"- Last modified: {datetime.fromtimestamp(session_path.stat().st_mtime)}")
    print(f"- Number of cookies: {len(session_data.get('cookies', []))}")
    print(f"- Number of origins: {len(session_data.get('origins', []))}")
    
    # All checks passed
    print("\n✅ Session appears to be valid and properly saved")
    return True

def test_session():
    """Test both the home directory session and project directory session."""
    
    # Path to the default session file in home directory
    home_session_path = Path.home() / ".instagram_downloader" / "session.json"
    
    # Path to the project directory session file
    project_session_path = Path.cwd() / "sessions" / "session.json"
    
    # Check both paths
    print("Checking home directory session:")
    home_result = check_session_file(home_session_path)
    
    print("\n" + "-" * 50 + "\n")
    
    print("Checking project directory session:")
    project_result = check_session_file(project_session_path)
    
    # Return True if either session is valid
    return home_result or project_result

if __name__ == "__main__":
    print("Instagram Session Test")
    print("=====================\n")
    
    result = test_session()
    
    if result:
        print("\nTest result: PASSED - At least one valid session found")
        sys.exit(0)
    else:
        print("\nTest result: FAILED - No valid sessions found")
        sys.exit(1) 