import os
import json
import logging
import time
import glob
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple

from playwright.sync_api import sync_playwright, Browser, Page, Error as PlaywrightError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('instagram_downloader')

class InstagramClient:
    """Instagram client for downloading content with manual login capabilities."""
    
    BASE_URL = "https://www.instagram.com/"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    PROFILE_URL = "https://www.instagram.com/accounts/edit/"
    
    def __init__(
        self,
        username: Optional[str] = None,
        session_path: Optional[str] = None,
        headless: bool = False,
        timeout: int = 60000,
        browser_type: str = "chromium",  # Can be "chromium", "firefox", or "webkit"
        use_project_dir: bool = False  # New parameter to control session storage location
    ):
        """
        Initialize the Instagram client.
        
        Args:
            username: Username for the account (used for session filename)
            session_path: Path to save/load session data. Default is ~/.instagram_downloader/sessions/
            headless: Whether to run the browser in headless mode
            timeout: Timeout for browser operations in milliseconds
            browser_type: Type of browser to use (chromium, firefox, or webkit)
            use_project_dir: If True, save session in the project directory instead of home directory
        """
        self.headless = headless
        self.timeout = timeout
        self.browser_type = browser_type
        self.username = username
        
        # Set up session directory
        if session_path is None:
            if use_project_dir:
                # Save in the project directory
                current_dir = Path.cwd()
                self.session_dir = current_dir / "sessions"
            else:
                # Use the default home directory location
                home_dir = Path.home()
                self.session_dir = home_dir / ".instagram_downloader" / "sessions"
        else:
            self.session_dir = Path(session_path)
        
        # Create session directory if it doesn't exist
        self.session_dir.mkdir(exist_ok=True, parents=True)
        
        # If username is provided, set the session path for this specific account
        if username:
            self.session_path = self.session_dir / f"{username.lower()}_session.json"
            logger.info(f"Using session file for user '{username}': {self.session_path}")
        else:
            # Default session path
            self.session_path = self.session_dir / "default_session.json"
            logger.info(f"Using default session file: {self.session_path}")
        
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_logged_in = False
        self.current_username = None
    
    def _init_browser(self) -> bool:
        """
        Initialize the browser using Playwright.
        
        Returns:
            bool: True if browser was initialized successfully, False otherwise
        """
        try:
            self.playwright = sync_playwright().start()
            
            # Select browser based on browser_type
            if self.browser_type == "firefox":
                browser_instance = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_instance = self.playwright.webkit
            else:
                browser_instance = self.playwright.chromium
            
            # Launch browser with additional arguments for stability
            self.browser = browser_instance.launch(
                headless=self.headless,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer'
                ]
            )
            
            # Create a new context and page
            context = self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            self.page = context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            return True
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            self._cleanup_browser()
            return False
    
    def _cleanup_browser(self) -> None:
        """Safely close browser and clean up resources."""
        try:
            if self.page:
                self.page.close()
                self.page = None
        except Exception as e:
            logger.debug(f"Error closing page: {e}")
        
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")
        
        try:
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logger.debug(f"Error stopping playwright: {e}")
    
    def verify_login_status(self) -> bool:
        """
        Verify if the current session is valid by checking if we're still logged in
        and retrieving the current username.
        
        This method requires an open browser connection.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        try:
            if not self.page:
                return False
            
            # Go to profile page to check login status and get username
            self.page.goto(self.PROFILE_URL)
            
            # Check if we're redirected to login page
            if "login" in self.page.url:
                logger.info("Session is invalid: redirected to login page")
                return False
            
            # Try to get the username from the profile page
            try:
                # Try multiple selectors to find the username
                username_field = self.page.locator('input[name="username"]').first
                extracted_username = username_field.get_attribute("value")
                
                if not extracted_username:
                    # Try alternative method - go to the main profile page
                    self.page.goto(self.BASE_URL)
                    time.sleep(2)  # Give it time to load
                    
                    # Try to get username from the profile icon link
                    profile_link = self.page.locator('a[href*="/accounts/activity/"]').first
                    if profile_link:
                        # Username might be in the alt text of the image
                        img = profile_link.locator('img').first
                        if img:
                            alt_text = img.get_attribute("alt")
                            if alt_text and "profile picture" in alt_text.lower():
                                # Format is usually "username's profile picture"
                                extracted_username = alt_text.split("'")[0]
                
                if extracted_username:
                    self.current_username = extracted_username
                    logger.info(f"Verified login as user: {self.current_username}")
                    
                    # If we didn't have a username before, update the session path
                    if not self.username and self.current_username:
                        self.username = self.current_username
                        original_path = self.session_path
                        self.session_path = self.session_dir / f"{self.current_username.lower()}_session.json"
                        logger.info(f"Updated session path from {original_path} to {self.session_path}")
                    
                    self.is_logged_in = True
                    return True
                else:
                    logger.warning("Could not extract username from profile page")
                    # Try to extract username from the session filename
                    if self.username:
                        self.current_username = self.username
                        logger.info(f"Using username from session filename: {self.current_username}")
                    self.is_logged_in = True  # Still logged in, just couldn't get username
                    return True
            except Exception as e:
                logger.warning(f"Error extracting username: {e}")
                # Try to extract username from the session filename
                if self.username:
                    self.current_username = self.username
                    logger.info(f"Using username from session filename: {self.current_username}")
                # We're still on the profile page and not redirected to login, so we're logged in
                self.is_logged_in = True
                return True
                
        except Exception as e:
            logger.error(f"Error verifying login status: {e}")
            return False
    
    def manual_login(self, max_retries: int = 3) -> bool:
        """
        Open browser for manual login and save the session after successful login.
        
        Args:
            max_retries: Maximum number of retries if browser crashes
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self._init_browser():
                    retry_count += 1
                    logger.warning(f"Failed to initialize browser. Retry {retry_count}/{max_retries}")
                    time.sleep(2)
                    continue
                
                # Navigate to Instagram login page
                self.page.goto(self.LOGIN_URL)
                
                # Wait for user to manually log in
                logger.info("Please log in to Instagram manually in the opened browser...")
                logger.info("Once you're logged in, the session will be saved automatically.")
                
                # Wait for navigation to the main Instagram page after login
                # This happens when login is successful
                self.page.wait_for_url(self.BASE_URL, timeout=300000)  # 5 minutes timeout
                
                # Check if login was successful
                if "accounts/login" not in self.page.url:
                    # Verify login and get username
                    if self.verify_login_status():
                        logger.info("Login successful!")
                        # Save the session with the username if available
                        self._save_session()
                        return True
                    else:
                        logger.error("Login verification failed")
                        return False
                else:
                    logger.error("Login failed or timed out")
                    return False
                    
            except PlaywrightError as e:
                logger.error(f"Playwright error during manual login: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying... ({retry_count}/{max_retries})")
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error during manual login: {e}")
                return False
                
            finally:
                self._cleanup_browser()
        
        logger.error(f"Failed to complete login after {max_retries} attempts")
        return False
    
    def _save_session(self) -> None:
        """Save the browser cookies and storage state to file."""
        if not self.is_logged_in or not self.page:
            logger.warning("Cannot save session: Not logged in or browser not initiated")
            return
        
        try:
            # Get cookies and storage state
            storage_state = self.page.context.storage_state()
            
            # Add metadata to the session
            session_data = {
                "storage_state": storage_state,
                "metadata": {
                    "username": self.current_username,
                    "created_at": time.time(),
                    "last_used": time.time()
                }
            }
            
            # Save to file
            with open(self.session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Session saved to {self.session_path}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def load_session(self) -> bool:
        """
        Load session from saved file.
        
        Returns:
            bool: True if session was loaded successfully, False otherwise
        """
        if not self.session_path.exists():
            logger.warning(f"Session file not found: {self.session_path}")
            return False
        
        try:
            # Load session from file
            with open(self.session_path, 'r') as f:
                session_data = json.load(f)
            
            # Extract storage state and basic validation
            if "storage_state" in session_data:
                storage_state = session_data["storage_state"]
                cookies = storage_state.get('cookies', [])
                
                # Basic validation: check if essential cookies exist and aren't expired
                # For Instagram, sessionid is the most important cookie
                session_valid = False
                current_time = time.time()
                
                for cookie in cookies:
                    if cookie.get('name') == 'sessionid':
                        # Check if the cookie is still valid (not expired)
                        expires = cookie.get('expires', 0)
                        if expires > current_time:
                            session_valid = True
                            
                            # Load metadata if available
                            if "metadata" in session_data:
                                metadata = session_data["metadata"]
                                self.current_username = metadata.get("username")
                                
                                # If username is not in metadata, use the one from filename
                                if not self.current_username and self.username:
                                    self.current_username = self.username
                                
                                logger.info(f"Session validated for user: {self.current_username}")
                                
                                # Update the last used timestamp
                                session_data["metadata"]["last_used"] = time.time()
                                with open(self.session_path, 'w') as f:
                                    json.dump(session_data, f, indent=2)
                            
                            break
                
                if session_valid:
                    self.is_logged_in = True
                    return True
                else:
                    logger.warning("Session appears to be invalid or expired based on cookie expiry")
                    return False
            else:
                # Old format session without proper structure
                logger.warning("Session file has invalid format")
                return False
                
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    @classmethod
    def list_sessions(cls, session_dir: Optional[str] = None, use_project_dir: bool = False) -> List[Dict[str, Any]]:
        """
        List all available sessions with their metadata.
        
        Args:
            session_dir: Directory where sessions are stored
            use_project_dir: If True, look for sessions in the project directory
            
        Returns:
            List of dictionaries with session information
        """
        # Determine session directory
        if session_dir:
            session_dir_path = Path(session_dir)
        elif use_project_dir:
            session_dir_path = Path.cwd() / "sessions"
        else:
            session_dir_path = Path.home() / ".instagram_downloader" / "sessions"
        
        if not session_dir_path.exists():
            logger.warning(f"Session directory not found: {session_dir_path}")
            return []
        
        sessions = []
        session_files = list(session_dir_path.glob("*_session.json")) + [session_dir_path / "default_session.json"]
        
        for session_file in session_files:
            if not session_file.exists():
                continue
                
            try:
                file_name = session_file.name
                
                # Extract username from filename first (most reliable method)
                filename_username = None
                if file_name.endswith('_session.json'):
                    filename_username = file_name.replace('_session.json', '')
                    if filename_username == 'default':
                        filename_username = None
                
                # Try to load session file to get metadata
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Extract metadata if available
                if "metadata" in session_data:
                    metadata = session_data["metadata"]
                    metadata_username = metadata.get("username")
                    created_at = metadata.get("created_at", 0)
                    last_used = metadata.get("last_used", 0)
                else:
                    # Old format session
                    metadata_username = None
                    created_at = session_file.stat().st_mtime
                    last_used = created_at
                
                # Use filename username if metadata username is not available
                username = metadata_username if metadata_username else filename_username
                if not username:
                    username = 'نامشخص'
                
                # Check if session is valid by checking cookie expiry
                is_valid = False
                if "storage_state" in session_data:
                    storage_state = session_data["storage_state"]
                    cookies = storage_state.get('cookies', [])
                    current_time = time.time()
                    
                    for cookie in cookies:
                        if cookie.get('name') == 'sessionid':
                            expires = cookie.get('expires', 0)
                            if expires > current_time:
                                is_valid = True
                                break
                
                sessions.append({
                    "username": username,
                    "file_path": str(session_file),
                    "file_name": file_name,
                    "created_at": created_at,
                    "last_used": last_used,
                    "file_size": session_file.stat().st_size,
                    "is_valid": is_valid
                })
            except Exception as e:
                logger.warning(f"Error reading session file {session_file}: {e}")
        
        return sorted(sessions, key=lambda x: x.get("last_used", 0), reverse=True)
    
    @classmethod
    def remove_session(cls, username: str, session_dir: Optional[str] = None, use_project_dir: bool = False) -> bool:
        """
        Remove a session for a specific username.
        
        Args:
            username: Username of the session to remove
            session_dir: Directory where sessions are stored
            use_project_dir: If True, look for sessions in the project directory
            
        Returns:
            True if session was removed successfully, False otherwise
        """
        # Determine session directory
        if session_dir:
            session_dir_path = Path(session_dir)
        elif use_project_dir:
            session_dir_path = Path.cwd() / "sessions"
        else:
            session_dir_path = Path.home() / ".instagram_downloader" / "sessions"
        
        # Construct the session file path
        session_file = session_dir_path / f"{username.lower()}_session.json"
        
        # If username is 'default', use the default session path
        if username.lower() == "default":
            session_file = session_dir_path / "default_session.json"
        
        # Check if the file exists
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return False
        
        try:
            # Delete the session file
            session_file.unlink()
            logger.info(f"Session removed: {session_file}")
            return True
        except Exception as e:
            logger.error(f"Error removing session file: {e}")
            return False 