#!/usr/bin/env python3
"""
Command-line tool for managing Instagram sessions.
"""

import argparse
import os
import time
import sys
from datetime import datetime
from pathlib import Path
from instagram_downloader import InstagramClient

def format_timestamp(timestamp):
    """Format timestamp into human-readable date/time."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def list_sessions(args):
    """List all available sessions."""
    print("\n===== Instagram Session List =====\n")
    
    sessions = InstagramClient.list_sessions(
        session_dir=args.dir, 
        use_project_dir=args.project_dir
    )
    
    if not sessions:
        print("⚠️ No sessions found.")
        return
    
    print(f"Number of sessions: {len(sessions)}\n")
    
    for i, session in enumerate(sessions, 1):
        username = session.get('username', 'Unknown')
        file_name = session.get('file_name', '')
        file_path = session.get('file_path', '')
        created_at = format_timestamp(session.get('created_at', 0))
        last_used = format_timestamp(session.get('last_used', 0))
        file_size = session.get('file_size', 0) / 1024  # KB
        is_valid = session.get('is_valid', False)
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        
        print(f"{i}. Username: {username}")
        print(f"   Filename: {file_name}")
        print(f"   File path: {file_path}")
        print(f"   Status: {status}")
        print(f"   Created at: {created_at}")
        print(f"   Last used: {last_used}")
        print(f"   File size: {file_size:.2f} KB")
        print("   " + "-" * 40)

def add_session(args):
    """Add a new session by performing manual login."""
    print("\n===== Add New Instagram Session =====\n")
    
    username = args.username
    if not username:
        username = input("Please enter your Instagram username: ")
    
    print(f"\nLogging into account '{username}'...")
    print("Browser will open shortly. Please log in manually.")
    
    client = InstagramClient(
        username=username,
        headless=False,
        browser_type=args.browser,
        use_project_dir=args.project_dir,
        session_path=args.dir
    )
    
    if client.manual_login():
        print("\n✅ Login successful!")
        print(f"Session saved for user '{username}'.")
    else:
        print("\n❌ Login failed. Please try again.")

def remove_session(args):
    """Remove a session."""
    print("\n===== Remove Instagram Session =====\n")
    
    username = args.username
    if not username:
        # List available sessions
        sessions = InstagramClient.list_sessions(
            session_dir=args.dir, 
            use_project_dir=args.project_dir
        )
        
        if not sessions:
            print("⚠️ No sessions found to remove.")
            return
        
        print("Available sessions:")
        for i, session in enumerate(sessions, 1):
            status = "✅ Valid" if session.get('is_valid', False) else "❌ Invalid"
            print(f"{i}. {session.get('username', 'Unknown')} - {status}")
        
        choice = input("\nEnter the number of the session to remove (or 'q' to quit): ")
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                username = sessions[idx].get('username', 'default')
            else:
                print("❌ Invalid number!")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return
    
    confirm = input(f"Are you sure you want to remove session '{username}'? (y/n): ")
    if confirm.lower() != 'y':
        print("Remove operation cancelled.")
        return
    
    if InstagramClient.remove_session(
        username=username,
        session_dir=args.dir,
        use_project_dir=args.project_dir
    ):
        print(f"✅ Session '{username}' removed successfully.")
    else:
        print(f"❌ Failed to remove session '{username}'.")

def test_session(args):
    """Test if a session is valid."""
    print("\n===== Test Instagram Session Validity =====\n")
    
    username = args.username
    if not username:
        # List available sessions
        sessions = InstagramClient.list_sessions(
            session_dir=args.dir, 
            use_project_dir=args.project_dir
        )
        
        if not sessions:
            print("⚠️ No sessions found to test.")
            return
        
        print("Available sessions:")
        for i, session in enumerate(sessions, 1):
            status = "✅ Valid" if session.get('is_valid', False) else "❌ Invalid"
            print(f"{i}. {session.get('username', 'Unknown')} - {status}")
        
        choice = input("\nEnter the number of the session to test (or 'q' to quit): ")
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                username = sessions[idx].get('username', 'default')
            else:
                print("❌ Invalid number!")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return
    
    print(f"Testing session validity for user '{username}'...")
    
    # First check without opening browser
    client = InstagramClient(
        username=username,
        headless=args.headless,
        browser_type=args.browser,
        use_project_dir=args.project_dir,
        session_path=args.dir
    )
    
    if client.load_session():
        print(f"✅ Session '{username}' is valid.")
        if client.current_username:
            print(f"Verified username: {client.current_username}")
    else:
        print(f"❌ Session '{username}' is invalid or expired.")
        retry = input("Would you like to log in again? (y/n): ")
        if retry.lower() == 'y':
            if client.manual_login():
                print("\n✅ Re-login successful!")
                print(f"Session for user '{username}' has been updated.")
            else:
                print("\n❌ Re-login failed.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Instagram Session Management Tool")
    
    # Main arguments
    parser.add_argument("command", choices=["list", "add", "remove", "test"], help="Main command")
    parser.add_argument("--project-dir", action="store_true", help="Use project directory instead of default path")
    parser.add_argument("--dir", help="Custom path for storing sessions")
    
    # Command-specific arguments
    parser.add_argument("--username", help="Instagram username")
    parser.add_argument("--browser", default="firefox", choices=["firefox", "chromium", "webkit"], help="Browser type")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_sessions(args)
    elif args.command == "add":
        add_session(args)
    elif args.command == "remove":
        remove_session(args)
    elif args.command == "test":
        test_session(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 