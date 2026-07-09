"""
Automated milestone alerts for pilot program.
Sends notifications when pilots reach key performance milestones.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from db.pilots_db import get_pilot, list_pilots
from db.actions_db import count_actions
from db.revenue_calc import calculate_pilot_revenue
from email_service import email_service


# Milestone definitions
MILESTONES = {
    'first_reorder': {'action': 'reorder', 'threshold': 1, 'emoji': '🎉', 'title': 'First Reorder'},
    'ten_reorders': {'action': 'reorder', 'threshold': 10, 'emoji': '🔟', 'title': '10 Reorders'},
    'twentyfive_reorders': {'action': 'reorder', 'threshold': 25, 'emoji': '🌟', 'title': '25 Reorders'},
    'fifty_reorders': {'action': 'reorder', 'threshold': 50, 'emoji': '🚀', 'title': '50 Reorders'},
    'hundred_reorders': {'action': 'reorder', 'threshold': 100, 'emoji': '💯', 'title': '100 Reorders'},
    'thousand_dollars': {'type': 'revenue', 'threshold': 1000, 'emoji': '💰', 'title': '$1,000 Revenue'},
    'five_thousand_dollars': {'type': 'revenue', 'threshold': 5000, 'emoji': '💸', 'title': '$5,000 Revenue'},
    'ten_thousand_dollars': {'type': 'revenue', 'threshold': 10000, 'emoji': '💵', 'title': '$10,000 Revenue'},
    'positive_roi': {'type': 'roi', 'threshold': 0, 'emoji': '📈', 'title': 'Positive ROI'},
    'doubled_roi': {'type': 'roi', 'threshold': 100, 'emoji': '🎯', 'title': '100% ROI (2x return)'},
}

class AlertManager:
    """Manage pilot milestone alerts."""
    
    def __init__(self):
        self.db_path = 'backend/db/alerts.sqlite'
        self.init_db()
    
    def init_db(self):
        """Initialize alerts database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Alerts table
            c.execute('''CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pilot_id INTEGER,
                milestone_key TEXT,
                milestone_title TEXT,
                value_achieved REAL,
                threshold REAL,
                alert_type TEXT,
                sent BOOLEAN DEFAULT 0,
                created_at TEXT,
                sent_at TEXT
            )''')
            
            # Alert subscriptions
            c.execute('''CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pilot_id INTEGER,
                email TEXT,
                milestone_key TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TEXT
            )''')
            
            # Create indices
            c.execute('CREATE INDEX IF NOT EXISTS idx_alert_pilot ON alerts(pilot_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_alert_sent ON alerts(sent)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_alert_milestone ON alerts(milestone_key)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_sub_pilot ON alert_subscriptions(pilot_id)')
            
            conn.commit()
        finally:
            conn.close()
    
    def check_and_create_alerts(self, pilot_id: int):
        """Check pilot against all milestones and create new alerts."""
        pilot = get_pilot(pilot_id)
        if not pilot:
            return []
        
        new_alerts = []
        created_alerts = self._get_existing_alerts(pilot_id)
        
        for milestone_key, milestone_def in MILESTONES.items():
            if milestone_key in created_alerts:
                continue  # Already alerted
            
            should_alert = False
            value_achieved = 0
            
            if 'action' in milestone_def:
                # Action-based milestone
                action_count = count_actions(milestone_def['action'], pilot_id)
                value_achieved = action_count
                if action_count >= milestone_def['threshold']:
                    should_alert = True
            
            elif milestone_def.get('type') == 'revenue':
                # Revenue-based milestone
                revenue = calculate_pilot_revenue(pilot_id).get('total_revenue', 0)
                value_achieved = revenue
                if revenue >= milestone_def['threshold']:
                    should_alert = True
            
            elif milestone_def.get('type') == 'roi':
                # ROI-based milestone
                try:
                    from db.roi_calc import calculate_pilot_roi
                    roi_data = calculate_pilot_roi(pilot_id)
                    roi_pct = roi_data.get('roi_metrics', {}).get('roi_percent', 0)
                    value_achieved = roi_pct
                    
                    if roi_pct >= milestone_def['threshold']:
                        should_alert = True
                except:
                    pass
            
            if should_alert:
                self._create_alert(pilot_id, milestone_key, milestone_def, value_achieved)
                new_alerts.append({
                    'milestone_key': milestone_key,
                    'title': milestone_def['title'],
                    'value_achieved': round(value_achieved, 2)
                })
        
        return new_alerts
    
    def _get_existing_alerts(self, pilot_id: int) -> set:
        """Get set of milestones already alerted for a pilot."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT milestone_key FROM alerts WHERE pilot_id = ?', (pilot_id,))
            return {row[0] for row in c.fetchall()}
        finally:
            conn.close()
    
    def _create_alert(self, pilot_id: int, milestone_key: str, milestone_def: Dict, value_achieved: float):
        """Create an alert record."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO alerts 
                (pilot_id, milestone_key, milestone_title, value_achieved, threshold, alert_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (pilot_id, milestone_key, milestone_def['title'], value_achieved,
                 milestone_def['threshold'], 'milestone', datetime.utcnow().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get_pending_alerts(self) -> List[Dict]:
        """Get all unsent alerts."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''SELECT id, pilot_id, milestone_key, milestone_title, 
                        value_achieved, threshold, created_at
                FROM alerts WHERE sent = 0 ORDER BY created_at DESC''')
            
            alerts = []
            for row in c.fetchall():
                pilot = get_pilot(row[1])
                alerts.append({
                    'id': row[0],
                    'pilot_id': row[1],
                    'pilot_name': pilot.get('name') if pilot else 'Unknown',
                    'milestone_key': row[2],
                    'milestone_title': row[3],
                    'value_achieved': row[4],
                    'threshold': row[5],
                    'created_at': row[6],
                })
            
            return alerts
        finally:
            conn.close()
    
    def send_alert(self, alert_id: int, recipient_email: str, recipient_name: str = 'Team') -> Dict:
        """Send an alert email and mark as sent."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''SELECT pilot_id, milestone_key, milestone_title, value_achieved, threshold
                FROM alerts WHERE id = ?''', (alert_id,))
            
            row = c.fetchone()
            if not row:
                return {'success': False, 'error': 'Alert not found'}
            
            pilot_id, milestone_key, milestone_title, value_achieved, threshold = row
            pilot = get_pilot(pilot_id)
            milestone_def = MILESTONES.get(milestone_key, {})
            
            # Format email
            emoji = milestone_def.get('emoji', '⭐')
            subject = f"{emoji} Pilot Milestone Reached: {milestone_title}"
            
            body = f"""
Congratulations! {emoji}

A pilot in your program has reached a significant milestone:

Pilot: {pilot.get('name')}
Store: {pilot.get('store_name')}
Milestone: {milestone_title}
Value Achieved: {value_achieved}
Threshold: {threshold}

This is great progress for your pilot program! Visit the dashboard to see more details.

Best regards,
CLARIQ Team
            """
            
            # Send email
            result = email_service.send_email(
                to_email=recipient_email,
                subject=subject,
                body=body.strip(),
                html=False
            )
            
            # Mark as sent
            if result.get('success'):
                c.execute('''UPDATE alerts SET sent = 1, sent_at = ? WHERE id = ?''',
                    (datetime.utcnow().isoformat(), alert_id))
                conn.commit()
            
            return result
        finally:
            conn.close()
    
    def send_all_pending_alerts(self, recipient_email: str, recipient_name: str = 'Team') -> Dict:
        """Send all pending alerts to recipient."""
        pending = self.get_pending_alerts()
        
        sent_count = 0
        failed_count = 0
        
        for alert in pending:
            result = self.send_alert(alert['id'], recipient_email, recipient_name)
            if result.get('success'):
                sent_count += 1
            else:
                failed_count += 1
        
        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total_alerts': len(pending),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_pilot_milestones(self, pilot_id: int) -> Dict:
        """Get milestone progress for a pilot."""
        pilot = get_pilot(pilot_id)
        if not pilot:
            return {'error': 'Pilot not found'}
        
        milestones_data = {}
        
        for milestone_key, milestone_def in MILESTONES.items():
            milestone_data = {
                'key': milestone_key,
                'title': milestone_def['title'],
                'emoji': milestone_def.get('emoji', '⭐'),
                'threshold': milestone_def['threshold'],
                'achieved': False,
                'progress_percent': 0,
                'value_current': 0,
            }
            
            if 'action' in milestone_def:
                current = count_actions(milestone_def['action'], pilot_id)
                milestone_data['value_current'] = current
                milestone_data['achieved'] = current >= milestone_def['threshold']
                milestone_data['progress_percent'] = min(100, int(current / milestone_def['threshold'] * 100))
            
            elif milestone_def.get('type') == 'revenue':
                current = calculate_pilot_revenue(pilot_id).get('total_revenue', 0)
                milestone_data['value_current'] = round(current, 2)
                milestone_data['achieved'] = current >= milestone_def['threshold']
                milestone_data['progress_percent'] = min(100, int(current / milestone_def['threshold'] * 100))
            
            elif milestone_def.get('type') == 'roi':
                try:
                    from db.roi_calc import calculate_pilot_roi
                    roi_data = calculate_pilot_roi(pilot_id)
                    current = roi_data.get('roi_metrics', {}).get('roi_percent', 0)
                    milestone_data['value_current'] = round(current, 1)
                    milestone_data['achieved'] = current >= milestone_def['threshold']
                    milestone_data['progress_percent'] = min(100, int(current / max(1, milestone_def['threshold']) * 100)) if milestone_def['threshold'] > 0 else 0
                except:
                    pass
            
            milestones_data[milestone_key] = milestone_data
        
        return {
            'pilot_id': pilot_id,
            'pilot_name': pilot.get('name'),
            'milestones': milestones_data,
            'total_milestones': len(MILESTONES),
            'achieved_count': sum(1 for m in milestones_data.values() if m['achieved']),
        }


# Global alert manager instance
alert_manager = AlertManager()
