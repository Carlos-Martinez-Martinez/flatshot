"""
Session Manager for FlatShot
Handles saving and restoring application state (folders, settings, window geometry).
"""
import logging
from typing import Dict, Any, Optional

from flatshot.application.session_service import SessionService


class SessionManager:
    """Manages persistent session state."""
    
    def __init__(self):
        self.logger = logging.getLogger("flatshot.session")
        self.session_file = SessionService.default_session_file()
        self.session_dir = self.session_file.parent
        self.service = SessionService(self.session_file, logger=self.logger)
        
        # Ensure directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def save_session(self, data: Dict[str, Any]) -> bool:
        """Save session data to JSON file."""
        return self.service.save_session(data)
            
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from JSON file."""
        return self.service.load_session()
            
    def clear_session(self):
        """Delete the session file."""
        self.service.clear_session()
