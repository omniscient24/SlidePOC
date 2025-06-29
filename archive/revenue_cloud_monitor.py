#!/usr/bin/env python3
"""
Revenue Cloud Migration Progress Monitor
Provides real-time monitoring and progress tracking for migration operations.
"""

import time
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
import json

class MigrationMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.current_operation = None
        self.current_object = None
        self.progress_queue = queue.Queue()
        self.is_running = False
        
        # Object processing tracking
        self.object_stats = {}
        self.total_objects = 0
        self.completed_objects = 0
        
        # Record-level tracking
        self.total_records = 0
        self.processed_records = 0
        self.failed_records = 0
        
        # Performance metrics
        self.operation_times = {}
        self.record_processing_rate = 0
        
        # Event listeners
        self.listeners = []
    
    def start_migration(self, operation_name, total_objects=0):
        """Start monitoring a migration operation."""
        self.start_time = datetime.now()
        self.current_operation = operation_name
        self.total_objects = total_objects
        self.completed_objects = 0
        self.is_running = True
        
        self.broadcast_event({
            'type': 'migration_started',
            'operation': operation_name,
            'timestamp': self.start_time.isoformat()
        })
    
    def start_object(self, object_name, total_records=0):
        """Start processing a specific object."""
        self.current_object = object_name
        object_start_time = datetime.now()
        
        self.object_stats[object_name] = {
            'start_time': object_start_time,
            'end_time': None,
            'total_records': total_records,
            'processed_records': 0,
            'failed_records': 0,
            'status': 'processing',
            'errors': []
        }
        
        self.broadcast_event({
            'type': 'object_started',
            'object': object_name,
            'total_records': total_records,
            'timestamp': object_start_time.isoformat()
        })
    
    def update_progress(self, records_processed=0, records_failed=0):
        """Update progress for current object."""
        if self.current_object and self.current_object in self.object_stats:
            stats = self.object_stats[self.current_object]
            stats['processed_records'] += records_processed
            stats['failed_records'] += records_failed
            
            # Calculate processing rate
            elapsed = (datetime.now() - stats['start_time']).total_seconds()
            if elapsed > 0:
                rate = stats['processed_records'] / elapsed
                self.record_processing_rate = rate
            
            self.broadcast_event({
                'type': 'progress_update',
                'object': self.current_object,
                'processed': stats['processed_records'],
                'failed': stats['failed_records'],
                'total': stats['total_records'],
                'rate': self.record_processing_rate
            })
    
    def complete_object(self, status='success', errors=None):
        """Mark current object as complete."""
        if self.current_object and self.current_object in self.object_stats:
            stats = self.object_stats[self.current_object]
            stats['end_time'] = datetime.now()
            stats['status'] = status
            if errors:
                stats['errors'] = errors
            
            # Update totals
            self.completed_objects += 1
            self.processed_records += stats['processed_records']
            self.failed_records += stats['failed_records']
            
            # Calculate duration
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            self.operation_times[self.current_object] = duration
            
            self.broadcast_event({
                'type': 'object_completed',
                'object': self.current_object,
                'status': status,
                'duration': duration,
                'processed': stats['processed_records'],
                'failed': stats['failed_records']
            })
    
    def complete_migration(self):
        """Complete the migration operation."""
        self.end_time = datetime.now()
        self.is_running = False
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        summary = {
            'operation': self.current_operation,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration': total_duration,
            'total_objects': self.completed_objects,
            'total_records': self.processed_records,
            'failed_records': self.failed_records,
            'success_rate': (self.processed_records - self.failed_records) / self.processed_records * 100 if self.processed_records > 0 else 0,
            'average_rate': self.processed_records / total_duration if total_duration > 0 else 0
        }
        
        self.broadcast_event({
            'type': 'migration_completed',
            'summary': summary
        })
        
        return summary
    
    def get_progress(self):
        """Get current progress information."""
        if not self.is_running:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        # Estimate time remaining
        if self.completed_objects > 0 and self.total_objects > 0:
            avg_time_per_object = elapsed / self.completed_objects
            remaining_objects = self.total_objects - self.completed_objects
            estimated_remaining = avg_time_per_object * remaining_objects
        else:
            estimated_remaining = None
        
        return {
            'operation': self.current_operation,
            'current_object': self.current_object,
            'elapsed_time': elapsed,
            'estimated_remaining': estimated_remaining,
            'objects_completed': self.completed_objects,
            'objects_total': self.total_objects,
            'records_processed': self.processed_records,
            'records_failed': self.failed_records,
            'current_rate': self.record_processing_rate,
            'object_stats': self.object_stats
        }
    
    def add_listener(self, callback):
        """Add an event listener."""
        self.listeners.append(callback)
    
    def remove_listener(self, callback):
        """Remove an event listener."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def broadcast_event(self, event):
        """Broadcast event to all listeners."""
        event['timestamp'] = datetime.now().isoformat()
        
        # Add to queue
        self.progress_queue.put(event)
        
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Error in listener: {e}")
    
    def format_duration(self, seconds):
        """Format duration in human-readable format."""
        if seconds is None:
            return "Unknown"
        
        duration = timedelta(seconds=int(seconds))
        return str(duration)
    
    def generate_progress_report(self):
        """Generate a detailed progress report."""
        report = []
        report.append("MIGRATION PROGRESS REPORT")
        report.append("=" * 60)
        report.append(f"Operation: {self.current_operation}")
        report.append(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'Not started'}")
        
        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            report.append(f"Elapsed: {self.format_duration(elapsed)}")
            report.append(f"Status: In Progress")
        else:
            report.append(f"Ended: {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'Not completed'}")
            if self.start_time and self.end_time:
                duration = (self.end_time - self.start_time).total_seconds()
                report.append(f"Duration: {self.format_duration(duration)}")
            report.append(f"Status: Completed")
        
        report.append("")
        report.append("OBJECT SUMMARY")
        report.append("-" * 60)
        report.append(f"{'Object':<30} {'Status':<12} {'Records':<10} {'Failed':<10} {'Time':<10}")
        report.append("-" * 60)
        
        for obj_name, stats in self.object_stats.items():
            duration = self.operation_times.get(obj_name, 0)
            report.append(
                f"{obj_name:<30} {stats['status']:<12} "
                f"{stats['processed_records']:<10} {stats['failed_records']:<10} "
                f"{self.format_duration(duration):<10}"
            )
        
        report.append("-" * 60)
        report.append(f"{'TOTAL':<30} {'':<12} {self.processed_records:<10} {self.failed_records:<10}")
        
        if self.processed_records > 0:
            success_rate = (self.processed_records - self.failed_records) / self.processed_records * 100
            report.append(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if self.record_processing_rate > 0:
            report.append(f"Average Processing Rate: {self.record_processing_rate:.1f} records/second")
        
        return "\n".join(report)

class ProgressBar:
    """Simple progress bar for console output."""
    
    def __init__(self, total, prefix='Progress', width=50):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
    
    def update(self, current):
        """Update progress bar."""
        self.current = current
        self.draw()
    
    def increment(self, amount=1):
        """Increment progress."""
        self.current += amount
        self.draw()
    
    def draw(self):
        """Draw the progress bar."""
        if self.total == 0:
            percent = 100
        else:
            percent = min(100, (self.current / self.total) * 100)
        
        filled = int(self.width * percent / 100)
        bar = '█' * filled + '░' * (self.width - filled)
        
        print(f'\r{self.prefix}: [{bar}] {percent:.1f}% ({self.current}/{self.total})', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

def monitor_subprocess(process, monitor, object_name, total_records=0):
    """Monitor a subprocess and update progress."""
    monitor.start_object(object_name, total_records)
    
    # Read output line by line
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if not line:
            continue
        
        # Parse progress from output
        if 'processed' in line.lower():
            # Extract number of processed records
            try:
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    processed = int(numbers[0])
                    monitor.update_progress(records_processed=processed)
            except:
                pass
        
        # Check for errors
        if 'error' in line.lower() or 'failed' in line.lower():
            monitor.object_stats[object_name]['errors'].append(line)
    
    # Wait for process to complete
    process.wait()
    
    # Mark object as complete
    status = 'success' if process.returncode == 0 else 'failed'
    monitor.complete_object(status=status)

if __name__ == '__main__':
    # Example usage
    monitor = MigrationMonitor()
    
    # Simulate a migration
    monitor.start_migration("Test Migration", total_objects=3)
    
    # Simulate object processing
    for obj in ['Product2', 'PricebookEntry', 'ProductCategory']:
        monitor.start_object(obj, total_records=100)
        
        # Simulate progress
        for i in range(10):
            time.sleep(0.1)
            monitor.update_progress(records_processed=10)
        
        monitor.complete_object(status='success')
    
    # Complete migration
    summary = monitor.complete_migration()
    
    # Print report
    print(monitor.generate_progress_report())