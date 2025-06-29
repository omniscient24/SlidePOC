#!/usr/bin/env python3
"""
Revenue Cloud UI Configuration Manager
Handles saving and loading UI preferences and migration configurations.
"""

import json
import os
from pathlib import Path
from datetime import datetime

class UIConfig:
    def __init__(self):
        self.config_dir = Path.home() / '.revenue_cloud_migration'
        self.config_file = self.config_dir / 'ui_config.json'
        self.history_file = self.config_dir / 'migration_history.json'
        
        # Default configuration
        self.default_config = {
            'target_org': 'fortradp2',
            'workbook_path': 'data/Revenue_Cloud_Complete_Upload_Template.xlsx',
            'theme': 'light',
            'auto_clean': True,
            'auto_analyze': True,
            'log_level': 'info',
            'window_geometry': '1200x800',
            'last_migration': None,
            'recent_orgs': [],
            'recent_workbooks': []
        }
        
        self.config = self.load_config()
        self.history = self.load_history()
    
    def load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    # Merge with defaults to handle new keys
                    return {**self.default_config, **saved_config}
            except:
                pass
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_history(self):
        """Load migration history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_history(self):
        """Save migration history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_to_history(self, entry):
        """Add a migration entry to history."""
        entry['timestamp'] = datetime.now().isoformat()
        self.history.insert(0, entry)
        
        # Keep only last 50 entries
        self.history = self.history[:50]
        self.save_history()
    
    def update_recent(self, org=None, workbook=None):
        """Update recent orgs and workbooks lists."""
        if org and org not in self.config['recent_orgs']:
            self.config['recent_orgs'].insert(0, org)
            self.config['recent_orgs'] = self.config['recent_orgs'][:10]
        
        if workbook and workbook not in self.config['recent_workbooks']:
            self.config['recent_workbooks'].insert(0, workbook)
            self.config['recent_workbooks'] = self.config['recent_workbooks'][:10]
        
        self.save_config()
    
    def get_migration_stats(self):
        """Get migration statistics from history."""
        if not self.history:
            return {
                'total_migrations': 0,
                'successful_migrations': 0,
                'total_records': 0,
                'most_recent': None
            }
        
        successful = [h for h in self.history if h.get('status') == 'success']
        total_records = sum(h.get('total_records', 0) for h in self.history)
        
        return {
            'total_migrations': len(self.history),
            'successful_migrations': len(successful),
            'total_records': total_records,
            'most_recent': self.history[0] if self.history else None
        }

class MigrationProfile:
    """Manages different migration profiles for different scenarios."""
    
    def __init__(self):
        self.profiles_dir = Path.home() / '.revenue_cloud_migration' / 'profiles'
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
    def save_profile(self, name, configuration):
        """Save a migration profile."""
        profile_file = self.profiles_dir / f"{name}.json"
        
        profile_data = {
            'name': name,
            'created': datetime.now().isoformat(),
            'configuration': configuration,
            'description': configuration.get('description', ''),
            'objects': configuration.get('objects', []),
            'field_mappings': configuration.get('field_mappings', {}),
            'validation_rules': configuration.get('validation_rules', [])
        }
        
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        return profile_file
    
    def load_profile(self, name):
        """Load a migration profile."""
        profile_file = self.profiles_dir / f"{name}.json"
        
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_profiles(self):
        """List all available profiles."""
        profiles = []
        
        for profile_file in self.profiles_dir.glob('*.json'):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profiles.append({
                        'name': data.get('name', profile_file.stem),
                        'created': data.get('created', ''),
                        'description': data.get('description', '')
                    })
            except:
                pass
        
        return sorted(profiles, key=lambda x: x['created'], reverse=True)
    
    def delete_profile(self, name):
        """Delete a migration profile."""
        profile_file = self.profiles_dir / f"{name}.json"
        if profile_file.exists():
            profile_file.unlink()
            return True
        return False

# Sample profiles for common scenarios
DEFAULT_PROFILES = {
    'full_migration': {
        'name': 'Full Migration',
        'description': 'Complete CPQ to Revenue Cloud migration with all objects',
        'objects': [
            'ProductCatalog', 'ProductCategory', 'ProductClassification',
            'AttributeCategory', 'AttributePicklist', 'AttributeDefinition',
            'ProductSellingModel', 'Product2', 'Pricebook2',
            'ProductAttributeDefinition', 'AttributePicklistValue',
            'ProductCategoryProduct', 'PricebookEntry', 'ProductComponentGroup',
            'ProductRelatedComponent'
        ],
        'validation_rules': [
            'check_required_fields',
            'validate_relationships',
            'check_data_types'
        ]
    },
    'products_only': {
        'name': 'Products Only',
        'description': 'Migrate only product catalog without pricing',
        'objects': [
            'ProductCatalog', 'ProductCategory', 'Product2',
            'ProductCategoryProduct'
        ],
        'validation_rules': [
            'check_required_fields',
            'validate_product_codes'
        ]
    },
    'attributes_only': {
        'name': 'Attributes Only',
        'description': 'Migrate product attributes and configurations',
        'objects': [
            'AttributeCategory', 'AttributePicklist', 'AttributeDefinition',
            'ProductAttributeDefinition', 'AttributePicklistValue'
        ],
        'validation_rules': [
            'check_attribute_types',
            'validate_picklist_values'
        ]
    }
}

def initialize_default_profiles():
    """Create default migration profiles if they don't exist."""
    profile_manager = MigrationProfile()
    
    for profile_key, profile_data in DEFAULT_PROFILES.items():
        if not profile_manager.load_profile(profile_data['name']):
            profile_manager.save_profile(profile_data['name'], profile_data)

if __name__ == '__main__':
    # Test configuration
    config = UIConfig()
    print("Current Configuration:")
    print(json.dumps(config.config, indent=2))
    
    print("\nMigration Statistics:")
    stats = config.get_migration_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Initialize default profiles
    initialize_default_profiles()
    
    profile_manager = MigrationProfile()
    print("\nAvailable Profiles:")
    for profile in profile_manager.list_profiles():
        print(f"  - {profile['name']}: {profile['description']}")