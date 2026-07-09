"""
Performance monitoring service for system health and analytics.
Tracks API performance, database connections, sync job status, and uptime.
"""

import sqlite3
import time
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from db.sync_status import get_all_sync_jobs, get_sync_job


class PerformanceMonitor:
    """Track system performance metrics."""
    
    def __init__(self):
        self.db_path = 'backend/db/performance_metrics.sqlite'
        self.init_db()
    
    def init_db(self):
        """Initialize performance metrics database."""
        conn = None
        try:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # API call metrics table
            c.execute('''CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                created_at TEXT
            )''')
            
            # System metrics table
            c.execute('''CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                uptime_seconds INTEGER,
                created_at TEXT
            )''')
            
            # Create indices
            c.execute('CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_metrics(endpoint)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_api_created ON api_metrics(created_at)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_system_created ON system_metrics(created_at)')
            
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not initialize performance metrics database: {e}")
        finally:
            if conn:
                conn.close()
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, response_time_ms: float):
        """Record API call metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO api_metrics 
                (endpoint, method, status_code, response_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?)''',
                (endpoint, method, status_code, response_time_ms, datetime.utcnow().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def record_system_metrics(self):
        """Record current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO system_metrics
                (cpu_percent, memory_percent, disk_percent, uptime_seconds, created_at)
                VALUES (?, ?, ?, ?, ?)''',
                (cpu_percent, memory_info.percent, disk_info.percent, 
                 int(time.time()), datetime.utcnow().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get_api_metrics(self, hours: int = 24) -> Dict:
        """Get API performance metrics for last N hours."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            # Overall metrics
            c.execute('''SELECT COUNT(*), AVG(response_time_ms), MAX(response_time_ms),
                        MIN(response_time_ms), SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)
                FROM api_metrics WHERE created_at > ?''', (cutoff_time,))
            row = c.fetchone()
            
            if not row[0]:  # No data
                return {
                    'total_requests': 0,
                    'avg_response_time_ms': 0,
                    'p95_response_time_ms': 0,
                    'error_rate_percent': 0,
                    'endpoints': {}
                }
            
            total_requests = row[0]
            avg_response = row[1] or 0
            max_response = row[2] or 0
            min_response = row[3] or 0
            error_count = row[4] or 0
            
            # Per-endpoint metrics
            c.execute('''SELECT endpoint, method, COUNT(*), AVG(response_time_ms),
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)
                FROM api_metrics WHERE created_at > ?
                GROUP BY endpoint, method
                ORDER BY COUNT(*) DESC''', (cutoff_time,))
            
            endpoints = {}
            for endpoint, method, count, avg_time, errors in c.fetchall():
                key = f"{method} {endpoint}"
                endpoints[key] = {
                    'calls': count,
                    'avg_response_time_ms': round(avg_time, 2),
                    'error_count': errors or 0,
                    'error_rate_percent': round((errors or 0) / count * 100, 2) if count > 0 else 0,
                }
            
            # Calculate p95
            c.execute('''SELECT response_time_ms FROM api_metrics 
                WHERE created_at > ?
                ORDER BY response_time_ms DESC LIMIT 1 OFFSET ?''',
                (cutoff_time, max(0, int(total_requests * 0.05))))
            p95_row = c.fetchone()
            p95 = p95_row[0] if p95_row else avg_response
            
            return {
                'hours': hours,
                'total_requests': total_requests,
                'avg_response_time_ms': round(avg_response, 2),
                'p95_response_time_ms': round(p95, 2),
                'max_response_time_ms': round(max_response, 2),
                'min_response_time_ms': round(min_response, 2),
                'error_count': error_count,
                'error_rate_percent': round(error_count / total_requests * 100, 2) if total_requests > 0 else 0,
                'endpoints': endpoints,
                'status': 'healthy' if error_count / total_requests < 0.05 else 'warning' if error_count / total_requests < 0.10 else 'critical',
            }
        finally:
            conn.close()
    
    def get_system_metrics(self, hours: int = 24) -> Dict:
        """Get system performance metrics for last N hours."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            c.execute('''SELECT AVG(cpu_percent), MAX(cpu_percent),
                        AVG(memory_percent), MAX(memory_percent),
                        AVG(disk_percent), MAX(disk_percent)
                FROM system_metrics WHERE created_at > ?''', (cutoff_time,))
            
            row = c.fetchone()
            
            if not row or not row[0]:
                return {
                    'avg_cpu_percent': 0,
                    'max_cpu_percent': 0,
                    'avg_memory_percent': 0,
                    'max_memory_percent': 0,
                    'avg_disk_percent': 0,
                    'status': 'unknown'
                }
            
            avg_cpu = row[0] or 0
            max_cpu = row[1] or 0
            avg_mem = row[2] or 0
            max_mem = row[3] or 0
            avg_disk = row[4] or 0
            
            # Determine status
            if max_cpu > 80 or max_mem > 80:
                status = 'warning'
            elif avg_cpu > 60 or avg_mem > 60:
                status = 'caution'
            else:
                status = 'healthy'
            
            return {
                'hours': hours,
                'avg_cpu_percent': round(avg_cpu, 1),
                'max_cpu_percent': round(max_cpu, 1),
                'avg_memory_percent': round(avg_mem, 1),
                'max_memory_percent': round(max_mem, 1),
                'avg_disk_percent': round(avg_disk, 1),
                'status': status,
            }
        finally:
            conn.close()
    
    def get_database_health(self) -> Dict:
        """Check database connectivity and health."""
        health = {
            'database': 'unknown',
            'pilots_count': 0,
            'actions_count': 0,
            'connections': 0,
        }
        
        try:
            # Check pilots database
            conn = sqlite3.connect('backend/db/clariq_pilots.sqlite')
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM pilots')
            health['pilots_count'] = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM pilots WHERE status=?', ('completed',))
            health['pilots_completed'] = c.fetchone()[0]
            conn.close()
            
            # Check actions database
            conn = sqlite3.connect('backend/db/clariq_actions.sqlite')
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM actions')
            health['actions_count'] = c.fetchone()[0]
            conn.close()
            
            # Check connections database
            conn = sqlite3.connect('backend/db/clariq_connections.sqlite')
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM connections WHERE status=?', ('connected',))
            health['connections'] = c.fetchone()[0]
            conn.close()
            
            health['database'] = 'healthy'
        except Exception as e:
            health['database'] = 'error'
            health['error'] = str(e)
        
        return health
    
    def get_sync_status(self) -> Dict:
        """Get sync job status and health."""
        try:
            jobs = get_all_sync_jobs(limit=10)
            
            if not jobs:
                return {
                    'total_jobs': 0,
                    'successful': 0,
                    'failed': 0,
                    'status': 'no_data'
                }
            
            successful = sum(1 for j in jobs if j.get('status') == 'success')
            failed = sum(1 for j in jobs if j.get('status') == 'failed')
            total_records = sum(j.get('records_synced', 0) for j in jobs)
            
            # Get last sync time
            last_sync = None
            if jobs and jobs[0].get('last_synced_at'):
                last_sync = jobs[0]['last_synced_at']
            
            return {
                'total_jobs': len(jobs),
                'successful': successful,
                'failed': failed,
                'success_rate_percent': round(successful / len(jobs) * 100, 1) if jobs else 0,
                'total_records_synced': total_records,
                'last_sync': last_sync,
                'status': 'healthy' if failed == 0 else 'warning',
                'recent_jobs': jobs[:5]
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_full_health_report(self) -> Dict:
        """Generate comprehensive system health report."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'api_performance': self.get_api_metrics(24),
            'system_metrics': self.get_system_metrics(24),
            'database_health': self.get_database_health(),
            'sync_status': self.get_sync_status(),
            'overall_status': self._calculate_overall_status(),
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system status."""
        api = self.get_api_metrics(24)
        system = self.get_system_metrics(24)
        db = self.get_database_health()
        sync = self.get_sync_status()
        
        if db.get('database') == 'error' or sync.get('status') == 'error':
            return 'critical'
        
        if api.get('status') == 'critical' or system.get('status') == 'warning' or sync.get('status') == 'warning':
            return 'warning'
        
        return 'healthy'


# Global monitor instance
performance_monitor = PerformanceMonitor()
