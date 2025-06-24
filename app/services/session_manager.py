"""
Session Manager for Revenue Cloud Migration Tool
Handles user sessions with file-based storage
"""
import json
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import hashlib
import secrets

from config.settings.app_config import (
    SESSIONS_DIR, 
    SESSION_LIFETIME_HOURS,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY
)


class SessionManager:
    """Manages user sessions with file-based storage"""
    
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_expired_sessions()
    
    def create_session(self, username: str, connection_id: str = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            'session_id': session_id,
            'username': username,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=SESSION_LIFETIME_HOURS)).isoformat(),
            'active_connection_id': connection_id,
            'active_connection_alias': None,  # Will be set when connection is selected
            'csrf_token': secrets.token_urlsafe(32)
        }
        
        self._save_session(session_id, session_data)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data if valid"""
        if not session_id:
            return None
            
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check expiration
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.destroy_session(session_id)
                return None
            
            # Update last accessed time
            session_data['last_accessed'] = datetime.now().isoformat()
            self._save_session(session_id, session_data)
            
            return session_data
            
        except Exception as e:
            print(f"Error reading session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data"""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.update(updates)
        self._save_session(session_id, session_data)
        return True
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        try:
            if session_file.exists():
                session_file.unlink()
            return True
        except Exception as e:
            print(f"Error destroying session {session_id}: {e}")
            return False
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session expiration"""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data['expires_at'] = (
            datetime.now() + timedelta(hours=SESSION_LIFETIME_HOURS)
        ).isoformat()
        
        self._save_session(session_id, session_data)
        return True
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid (exists and not expired)"""
        session_data = self.get_session(session_id)
        return session_data is not None
    
    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token for a session"""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        return secrets.compare_digest(
            session_data.get('csrf_token', ''),
            token
        )
    
    def _save_session(self, session_id: str, session_data: Dict) -> None:
        """Save session data to file"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove expired session files"""
        try:
            for session_file in self.sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(data.get('expires_at', ''))
                    if datetime.now() > expires_at:
                        session_file.unlink()
                except Exception:
                    # If we can't read it, it's probably corrupted
                    session_file.unlink()
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
    
    @staticmethod
    def get_session_cookie(cookies: str) -> Optional[str]:
        """Extract session ID from cookie string"""
        if not cookies:
            return None
        
        for cookie in cookies.split(';'):
            parts = cookie.strip().split('=', 1)
            if len(parts) == 2 and parts[0] == SESSION_COOKIE_NAME:
                return parts[1]
        
        return None
    
    @staticmethod
    def create_session_cookie(session_id: str) -> str:
        """Create session cookie string"""
        cookie_parts = [
            f"{SESSION_COOKIE_NAME}={session_id}",
            "Path=/"
        ]
        
        if SESSION_COOKIE_HTTPONLY:
            cookie_parts.append("HttpOnly")
        
        if SESSION_COOKIE_SECURE:
            cookie_parts.append("Secure")
        
        cookie_parts.append("SameSite=Lax")
        
        return "; ".join(cookie_parts)
    
    @staticmethod
    def create_logout_cookie() -> str:
        """Create cookie string to clear session"""
        return f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0"


# Singleton instance
session_manager = SessionManager()


# Decorator for requiring authentication
def require_auth(handler_method):
    """Decorator to require authentication for a handler method"""
    def wrapper(self):
        # Get session from cookie
        cookies = self.headers.get('Cookie', '')
        session_id = SessionManager.get_session_cookie(cookies)
        
        if not session_id:
            self._redirect_to_login()
            return
        
        # Validate session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            self._redirect_to_login()
            return
        
        # Add session to handler
        self.session = session_data
        
        # Call original method
        return handler_method(self)
    
    return wrapper


def require_connection(handler_method):
    """Decorator to require an active Salesforce connection"""
    def wrapper(self):
        # First check authentication
        if not hasattr(self, 'session'):
            # Apply auth decorator first
            require_auth(lambda s: None)(self)
            if not hasattr(self, 'session'):
                return
        
        # Check for active connection
        if not self.session.get('active_connection_id'):
            self._redirect_to_connections()
            return
        
        # Call original method
        return handler_method(self)
    
    return wrapper