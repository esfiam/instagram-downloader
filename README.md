# Instagram Downloader

A Python library for downloading Instagram content with manual login functionality and session management.

## Features

- Manual login using Playwright (browser automation)
- Session management (saving, loading, validating)
- Multiple account support
- Browser-less session validation
- Command-line session management tool

## Installation

```bash
pip install -r requirements.txt
playwright install
```

## Usage

### As a Library

```python
from instagram_downloader import InstagramClient

# Initialize the client
client = InstagramClient(username="your_username")

# Check if a valid session exists
if not client.load_session():
    # Perform manual login if no valid session exists
    client.manual_login()

# Now you can use the client for other operations
# ...
```

### Command-line Session Management

The package includes a command-line tool for managing Instagram sessions.

```bash
# List all saved sessions
python manage_sessions.py list

# Add a new session (will open browser for manual login)
python manage_sessions.py add --username your_username

# Test if a session is valid
python manage_sessions.py test --username your_username

# Remove a session
python manage_sessions.py remove --username your_username

# Use sessions from project directory instead of home directory
python manage_sessions.py list --project-dir
```

## Development Guide

### Using the InstagramClient Class

The `InstagramClient` class provides the core functionality for managing Instagram sessions and interactions. Here's how to use it in your code:

#### Initialization

```python
from instagram_downloader import InstagramClient

# Basic initialization with default settings
client = InstagramClient(username="your_username")

# Advanced initialization with custom settings
client = InstagramClient(
    username="your_username",
    headless=True,                # Run browser in headless mode
    timeout=30000,                # Set timeout for operations (ms)
    browser_type="firefox",       # Choose browser: "chromium", "firefox", or "webkit"
    use_project_dir=True,         # Store sessions in project directory
    session_path="/custom/path"   # Use custom session directory
)
```

#### Session Management

```python
# Check if session exists and is valid
if client.load_session():
    print("Session loaded successfully")
else:
    print("No valid session found, manual login required")
    client.manual_login()
```

#### Class Methods for Batch Operations

```python
# List all available sessions
sessions = InstagramClient.list_sessions(use_project_dir=True)
for session in sessions:
    print(f"Username: {session['username']}")
    print(f"Valid: {session['is_valid']}")
    print(f"Last used: {session['last_used']}")

# Remove a session
InstagramClient.remove_session(username="target_username", use_project_dir=True)
```

### Example: Creating a Custom Script

```python
#!/usr/bin/env python3
"""
Example script showing how to use the InstagramClient class.
"""

from instagram_downloader import InstagramClient
import sys

def main():
    # Check if username is provided
    if len(sys.argv) < 2:
        print("Usage: python script.py [username]")
        sys.exit(1)
    
    username = sys.argv[1]
    
    # Initialize client
    client = InstagramClient(username=username)
    
    # Try to load existing session
    if not client.load_session():
        print("No valid session found. Performing manual login...")
        if not client.manual_login():
            print("Login failed!")
            sys.exit(1)
    
    print(f"Successfully logged in as: {client.current_username}")
    
    # Now you can perform other operations with the authenticated client
    # For example, downloading content, analytics, etc.

if __name__ == "__main__":
    main()
```

## Session Management

Sessions are stored in JSON files in the following locations:

- Default: `~/.instagram_downloader/sessions/`
- Project directory: `./sessions/` (when using `--project-dir` flag)

Each session file contains cookies and storage state from the browser, allowing you to 
maintain your login across multiple script runs without having to log in each time.

## Requirements

- Python 3.7+
- Playwright 