"""
Sync Status Service
Tracks sync status for objects between Salesforce and local workbook
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config.settings.app_config import DATA_ROOT

class SyncStatusService:
    """Service for tracking sync status of objects"""
    
    def __init__(self):
        self.status_file = DATA_ROOT / 'sync_status.json'
        self._ensure_status_file()
    
    def _ensure_status_file(self):
        """Ensure the status file exists with default structure"""
        if not self.status_file.exists():
            default_status = {
                'last_updated': datetime.now().isoformat(),
                'objects': {}
            }
            self._save_status(default_status)
    
    def _load_status(self) -> Dict:
        """Load sync status from file"""
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default if file is missing or corrupted
            return {
                'last_updated': datetime.now().isoformat(),
                'objects': {}
            }
    
    def _save_status(self, status: Dict):
        """Save sync status to file"""
        status['last_updated'] = datetime.now().isoformat()
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def get_object_status(self, object_name: str) -> Dict:
        """Get sync status for a specific object"""
        status = self._load_status()
        return status['objects'].get(object_name, {
            'status': 'Not Synced',
            'last_sync': None,
            'last_upload': None,
            'record_count': 0,
            'upload_success': False
        })
    
    def get_all_status(self) -> Dict:
        """Get sync status for all objects"""
        return self._load_status()
    
    def update_sync_status(self, object_name: str, record_count: int, sync_success: bool = True):
        """Update sync status after a sync operation"""
        status = self._load_status()
        
        if object_name not in status['objects']:
            status['objects'][object_name] = {}
        
        object_status = status['objects'][object_name]
        object_status.update({
            'last_sync': datetime.now().isoformat(),
            'record_count': record_count,
            'sync_success': sync_success,
            'status': 'Synced' if sync_success else 'Sync Failed'
        })
        
        self._save_status(status)
    
    def update_upload_status(self, object_name: str, upload_success: bool, 
                           records_processed: int = 0, records_failed: int = 0,
                           upload_message: str = ''):
        """Update upload status after an upload operation"""
        status = self._load_status()
        
        if object_name not in status['objects']:
            status['objects'][object_name] = {}
        
        object_status = status['objects'][object_name]
        object_status.update({
            'last_upload': datetime.now().isoformat(),
            'upload_success': upload_success,
            'records_processed': records_processed,
            'records_failed': records_failed,
            'upload_message': upload_message
        })
        
        # Update overall status
        if upload_success:
            object_status['status'] = 'Synced'
        elif records_processed > 0 and records_failed > 0:
            object_status['status'] = 'Partially Synced'
        else:
            object_status['status'] = 'Upload Failed'
        
        self._save_status(status)
    
    def mark_object_as_modified(self, object_name: str):
        """Mark an object as modified (needs sync)"""
        status = self._load_status()
        
        if object_name not in status['objects']:
            status['objects'][object_name] = {}
        
        object_status = status['objects'][object_name]
        object_status['status'] = 'Modified'
        object_status['last_modified'] = datetime.now().isoformat()
        
        self._save_status(status)
    
    def reset_object_status(self, object_name: str):
        """Reset sync status for an object"""
        status = self._load_status()
        
        if object_name in status['objects']:
            status['objects'][object_name] = {
                'status': 'Not Synced',
                'last_sync': None,
                'last_upload': None,
                'record_count': 0,
                'upload_success': False
            }
            self._save_status(status)
    
    def get_sync_summary(self) -> Dict:
        """Get a summary of sync status across all objects"""
        status = self._load_status()
        objects = status['objects']
        
        summary = {
            'total_objects': len(objects),
            'synced': len([obj for obj in objects.values() if obj.get('status') == 'Synced']),
            'not_synced': len([obj for obj in objects.values() if obj.get('status') == 'Not Synced']),
            'modified': len([obj for obj in objects.values() if obj.get('status') == 'Modified']),
            'failed': len([obj for obj in objects.values() if 'Failed' in obj.get('status', '')]),
            'last_updated': status.get('last_updated')
        }
        
        return summary

# Global instance
sync_status_service = SyncStatusService()