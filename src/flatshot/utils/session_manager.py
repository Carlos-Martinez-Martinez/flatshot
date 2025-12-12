"""
Session Manager for FlatShot
Handles saving and restoring application state (folders, settings, window geometry).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class SessionManager:
    """Manages persistent session state."""
    
    def __init__(self):
        self.session_dir = Path.home() / ".flatshot"
        self.session_file = self.session_dir / "session.json"
        self.logger = logging.getLogger("flatshot.session")
        
        # Ensure directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def save_session(self, data: Dict[str, Any]) -> bool:
        """Save session data to JSON file."""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info("Session saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False
            
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from JSON file."""
        if not self.session_file.exists():
            return None
            
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info("Session loaded successfully")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return None
            
    def clear_session(self):
        """Delete the session file."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                self.logger.info("Session cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear session: {e}")
