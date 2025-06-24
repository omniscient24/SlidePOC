"""
Revenue Cloud Migration Tool - Configuration
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_ROOT = PROJECT_ROOT / 'app'
CONFIG_ROOT = PROJECT_ROOT / 'config'
DATA_ROOT = PROJECT_ROOT / 'data'
STATIC_ROOT = PROJECT_ROOT / 'static'
TEMPLATES_ROOT = PROJECT_ROOT / 'templates'

# Shared resources from parent project
SHARED_ROOT = PROJECT_ROOT.parent
KNOWLEDGE_GRAPHS_DIR = SHARED_ROOT / 'docs' / 'knowledge-graphs'
SHARED_LIBS_DIR = SHARED_ROOT / 'src' / 'shared'
REFERENCE_DOCS_DIR = SHARED_ROOT / 'docs' / 'reference'

# Local directories
CONNECTIONS_DIR = CONFIG_ROOT / 'connections'
SESSIONS_DIR = PROJECT_ROOT / 'sessions'
LOGS_DIR = PROJECT_ROOT / 'logs'
UPLOADS_DIR = DATA_ROOT / 'uploads'
EXPORTS_DIR = DATA_ROOT / 'exports'
WORKBOOKS_DIR = DATA_ROOT / 'workbooks'

# Create directories if they don't exist
for directory in [CONNECTIONS_DIR, SESSIONS_DIR, LOGS_DIR, UPLOADS_DIR, EXPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Application settings
APP_NAME = "Revenue Cloud Migration Tool"
APP_VERSION = "2.0.0"  # Version 2 with improved architecture
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '8080'))

# Session settings
SESSION_LIFETIME_HOURS = 12
SESSION_COOKIE_NAME = 'rcm_session'
SESSION_COOKIE_SECURE = not DEBUG  # Secure in production
SESSION_COOKIE_HTTPONLY = True

# Salesforce CLI settings
DEFAULT_CLI_TIMEOUT = 300  # 5 minutes for long operations
CLI_COMMAND = 'sf'  # or 'sfdx' for older CLI

# File upload settings
MAX_UPLOAD_SIZE_MB = 100
ALLOWED_EXTENSIONS = {'.xlsx', '.csv', '.xls'}
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

# Connection settings
MAX_SAVED_CONNECTIONS = 10
CONNECTION_FILE = CONNECTIONS_DIR / 'connections.json'

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOGS_DIR / 'app.log'

# Knowledge graph mappings
KNOWLEDGE_GRAPHS = {
    'migration': KNOWLEDGE_GRAPHS_DIR / 'CPQ_Revenue_Cloud_Migration_Knowledge_Graph.md',
    'rlm': KNOWLEDGE_GRAPHS_DIR / 'Revenue_Lifecycle_Management_Knowledge_Graph.md',
    'technical': KNOWLEDGE_GRAPHS_DIR / 'Revenue_Cloud_Technical_Implementation_Knowledge_Graph.md',
    'tools': KNOWLEDGE_GRAPHS_DIR / 'Migration_Tool_Suite_Knowledge_Graph.md'
}

# UI Configuration
UI_THEME = {
    'primary_color': '#0066cc',
    'secondary_color': '#28a745',
    'error_color': '#dc3545',
    'warning_color': '#ff6b35',
    'info_color': '#17a2b8',
    'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
}

def get_knowledge_graph_path(graph_name):
    """Get the full path to a knowledge graph file"""
    return KNOWLEDGE_GRAPHS.get(graph_name)

def ensure_shared_access():
    """Verify access to shared resources"""
    issues = []
    
    if not KNOWLEDGE_GRAPHS_DIR.exists():
        issues.append(f"Knowledge graphs directory not found: {KNOWLEDGE_GRAPHS_DIR}")
    
    if not SHARED_LIBS_DIR.exists():
        issues.append(f"Shared libraries directory not found: {SHARED_LIBS_DIR}")
        
    return issues

# Add shared libraries to Python path
import sys
if SHARED_LIBS_DIR.exists():
    sys.path.insert(0, str(SHARED_LIBS_DIR))

# Environment-specific overrides
if os.path.exists(PROJECT_ROOT / '.env'):
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')