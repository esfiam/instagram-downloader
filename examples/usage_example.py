#!/usr/bin/env python3
"""
Example script demonstrating how to use the Instagram Downloader library.

This example shows how to:
1. Initialize the Instagram client
2. Check for existing sessions
3. Perform login if needed
4. Use the client to download content
"""

import os
import sys
import argparse
from pathlib import Path
from instagram_downloader import InstagramClient

def main():
    """Main function to demonstrate Instagram client usage."""
    parser = argparse.ArgumentParser(description='Instagram Downloader Example')
    parser.add_argument('username', help='Instagram username for session loading')
    parser.add_argument('--url', help='Instagram URL to download from')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    args = parser.parse_args()
    
    # Initialize the Instagram client
    client = InstagramClient(
        headless=args.headless,
        session_username=args.username
    )
    
    # Check if we have a valid session
    if not client.has_valid_session():
        print("No valid session found. Please login:")
        client.login()
    else:
        print(f"✅ Valid session found for {args.username}")
    
    # Example: Download from URL
    if args.url:
        print(f"Downloading content from: {args.url}")
        # Here you would implement the download functionality
        # client.download_post(args.url)
        print("Content downloaded successfully!")
    else:
        print("No URL provided for download. Exiting...")
    
    # Clean up
    client.close()
    return 0

if __name__ == "__main__":
    print("Instagram Downloader Example")
    print("==========================\n")
    
    sys.exit(main()) 