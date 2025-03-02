"""
Tests for the Instagram Downloader client.
"""

import os
import pytest
from pathlib import Path
from instagram_downloader import InstagramClient

# Skip tests that require browser if CI environment is detected
skip_browser_tests = pytest.mark.skipif(
    os.environ.get('CI') == 'true',
    reason="Skipping browser tests in CI environment"
)

def test_client_initialization():
    """Test that the client initializes correctly."""
    client = InstagramClient(headless=True)
    assert client is not None
    client.close()

def test_session_path_construction():
    """Test that session paths are constructed correctly."""
    # Test with default username
    client1 = InstagramClient()
    assert "session.json" in str(client1.session_path)
    client1.close()
    
    # Test with custom username
    client2 = InstagramClient(session_username="testuser")
    assert "testuser_session.json" in str(client2.session_path)
    client2.close()

@skip_browser_tests
def test_session_validation():
    """Test session validation functionality."""
    client = InstagramClient(headless=True)
    # This is just testing the method exists and returns a boolean
    # The actual result depends on whether a valid session exists
    result = client.has_valid_session()
    assert isinstance(result, bool)
    client.close()

# Add more tests as needed 