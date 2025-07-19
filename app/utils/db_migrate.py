import sqlite3
import os
from pathlib import Path
from datetime import datetime

class DatabaseMigrator:
    def __init__(self, db_path, migrations_dir):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def init_migration_table(self):
        """Create migration tracking table"""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
        
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        return [row[0] for row in cursor.fetchall()]
        
    def get_pending_migrations(self):
        """Get list of migrations that need to be applied"""
        applied = self.get_applied_migrations()
        
        # Get all SQL files from migrations directory
        migration_files = []
        if os.path.exists(self.migrations_dir):
            for file in sorted(os.listdir(self.migrations_dir)):
                if file.endswith('.sql') and file not in applied:
                    migration_files.append(file)
                    
        return migration_files
        
    def apply_migration(self, filename):
        """Apply a single migration file"""
        filepath = os.path.join(self.migrations_dir, filename)
        
        try:
            # Read migration file
            with open(filepath, 'r') as f:
                sql = f.read()
                
            # Execute migration
            cursor = self.connection.cursor()
            cursor.executescript(sql)
            
            # Record migration
            cursor.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (filename,)
            )
            
            self.connection.commit()
            print(f"✓ Applied migration: {filename}")
            return True
            
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Failed to apply {filename}: {str(e)}")
            return False
            
    def run_migrations(self):
        """Run all pending migrations"""
        self.connect()
        
        try:
            # Initialize migration tracking
            self.init_migration_table()
            
            # Get pending migrations
            pending = self.get_pending_migrations()
            
            if not pending:
                print("No pending migrations.")
                return True
                
            print(f"Found {len(pending)} pending migration(s):")
            for migration in pending:
                print(f"  - {migration}")
                
            # Apply each migration
            success = True
            for migration in pending:
                if not self.apply_migration(migration):
                    success = False
                    break
                    
            if success:
                print(f"\n✓ Successfully applied {len(pending)} migration(s)")
            else:
                print("\n✗ Migration failed. Database may be in an inconsistent state.")
                
            return success
            
        finally:
            self.close()
            
    def rollback_last_migration(self):
        """Rollback the last applied migration (if rollback file exists)"""
        # This is a placeholder for rollback functionality
        # Would need corresponding rollback files
        pass


def run_migrations():
    """Convenience function to run migrations"""
    # Get paths
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / 'data' / 'salesforce_data.db'
    migrations_dir = base_dir / 'migrations'
    
    # Create directories if they don't exist
    db_path.parent.mkdir(exist_ok=True)
    migrations_dir.mkdir(exist_ok=True)
    
    # Run migrations
    migrator = DatabaseMigrator(str(db_path), str(migrations_dir))
    return migrator.run_migrations()


if __name__ == "__main__":
    run_migrations()