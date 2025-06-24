"""
File Upload Service
Handles file uploads for Revenue Cloud data
"""
import os
import json
import csv
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from datetime import datetime

from config.settings.app_config import UPLOADS_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS


class FileUploadService:
    """Service for handling file uploads and processing"""
    
    def __init__(self):
        self.uploads_dir = UPLOADS_DIR
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
        
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate file before processing"""
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Check file size
        if file_size > self.max_size:
            return False, f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB"
        
        return True, None
    
    def save_upload(self, file_data: bytes, filename: str, object_name: str, 
                    session_id: str) -> Tuple[bool, Dict]:
        """Save uploaded file and return metadata"""
        try:
            # Create session upload directory
            session_dir = self.uploads_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = Path(filename).stem.replace(' ', '_')
            file_ext = Path(filename).suffix
            saved_filename = f"{object_name}_{safe_name}_{timestamp}{file_ext}"
            
            # Save file
            file_path = session_dir / saved_filename
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Process file based on type
            if file_ext.lower() in ['.xlsx', '.xls']:
                data, headers = self.process_excel(file_path)
            else:
                data, headers = self.process_csv(file_path)
            
            # Create metadata
            metadata = {
                'filename': filename,
                'saved_as': str(file_path),
                'object': object_name,
                'uploaded_at': datetime.now().isoformat(),
                'size': len(file_data),
                'record_count': len(data),
                'headers': headers,
                'session_id': session_id
            }
            
            # Save metadata
            metadata_path = file_path.with_suffix('.meta.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, {
                'file_path': str(file_path),
                'metadata': metadata,
                'preview': data[:5] if data else []  # First 5 records
            }
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def process_excel(self, file_path: Path) -> Tuple[List[Dict], List[str]]:
        """Process Excel file and return data"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            headers = list(df.columns)
            
            # Convert NaN to None
            for record in data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            return data, headers
            
        except Exception as e:
            print(f"Error processing Excel file: {e}")
            return [], []
    
    def process_csv(self, file_path: Path) -> Tuple[List[Dict], List[str]]:
        """Process CSV file and return data"""
        try:
            data = []
            headers = []
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
                for row in reader:
                    # Convert empty strings to None
                    cleaned_row = {k: v if v else None for k, v in row.items()}
                    data.append(cleaned_row)
            
            return data, headers
            
        except Exception as e:
            print(f"Error processing CSV file: {e}")
            return [], []
    
    def prepare_for_salesforce(self, file_path: str, object_name: str, 
                             external_id: Optional[str] = None) -> Tuple[bool, Dict]:
        """Prepare file for Salesforce upload"""
        try:
            path = Path(file_path)
            
            # Load data
            if path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            
            # Create CSV for Salesforce CLI
            csv_path = path.with_suffix('.salesforce.csv')
            df.to_csv(csv_path, index=False)
            
            return True, {
                'csv_path': str(csv_path),
                'record_count': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_upload_history(self, session_id: str) -> List[Dict]:
        """Get upload history for a session"""
        history = []
        session_dir = self.uploads_dir / session_id
        
        if session_dir.exists():
            for meta_file in session_dir.glob('*.meta.json'):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                        history.append(metadata)
                except Exception as e:
                    print(f"Error reading metadata: {e}")
        
        # Sort by upload time (newest first)
        history.sort(key=lambda x: x['uploaded_at'], reverse=True)
        return history
    
    def cleanup_old_uploads(self, days: int = 7) -> None:
        """Clean up uploads older than specified days"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for session_dir in self.uploads_dir.iterdir():
            if session_dir.is_dir():
                # Check if directory is old
                if datetime.fromtimestamp(session_dir.stat().st_mtime) < cutoff:
                    # Remove directory and contents
                    import shutil
                    shutil.rmtree(session_dir)
                    print(f"Cleaned up old upload directory: {session_dir}")


# Singleton instance
file_upload_service = FileUploadService()