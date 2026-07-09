"""
Feedback & Support System for CLARIQ

Handles user feedback, bug reports, and support requests
Stores in database and sends email notifications to owner
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

class FeedbackDB:
    """Database for feedback and support tickets"""
    
    def __init__(self, db_path: str = "clariq_feedback.sqlite"):
        self.db_path = db_path
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize feedback database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_email TEXT NOT NULL,
                user_name TEXT,
                type TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_to TEXT,
                response TEXT,
                response_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_id INTEGER,
                ticket_number TEXT UNIQUE,
                category TEXT,
                resolution TEXT,
                resolution_date TIMESTAMP,
                FOREIGN KEY(feedback_id) REFERENCES feedback(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def submit_feedback(self, user_email: str, subject: str, message: str, 
                       feedback_type: str = "general", user_id: str = None, 
                       user_name: str = None, priority: str = "normal") -> dict:
        """Submit feedback/issue"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback 
            (user_email, user_name, user_id, type, subject, message, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_email, user_name, user_id, feedback_type, subject, message, priority))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "id": feedback_id,
            "status": "received",
            "message": "Thank you for your feedback. We'll review it shortly."
        }
    
    def get_feedback(self, feedback_id: int) -> dict:
        """Get feedback details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "user_id": row[1],
            "user_email": row[2],
            "user_name": row[3],
            "type": row[4],
            "subject": row[5],
            "message": row[6],
            "status": row[7],
            "priority": row[8],
            "created_at": row[9],
            "updated_at": row[10],
            "assigned_to": row[11],
            "response": row[12],
            "response_at": row[13]
        }
    
    def get_all_feedback(self, status: str = None) -> list:
        """Get all feedback, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM feedback WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "user_email": row[2],
                "user_name": row[3],
                "type": row[4],
                "subject": row[5],
                "status": row[7],
                "priority": row[8],
                "created_at": row[9]
            })
        
        return results
    
    def update_feedback_status(self, feedback_id: int, status: str, 
                              response: str = None) -> bool:
        """Update feedback status and add response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if response:
            cursor.execute("""
                UPDATE feedback 
                SET status = ?, response = ?, response_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, response, feedback_id))
        else:
            cursor.execute("""
                UPDATE feedback 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, feedback_id))
        
        conn.commit()
        conn.close()
        
        return True


class EmailNotifier:
    """Send email notifications for feedback"""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = None,
                 smtp_user: str = None, smtp_password: str = None,
                 from_email: str = None):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM", self.smtp_user)
    
    def send_feedback_notification(self, feedback_data: dict, 
                                   owner_email: str) -> bool:
        """Send feedback to owner"""
        
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            print("⚠️ Email not configured. Set SMTP_* environment variables.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = owner_email
            
            # Email subject
            subject = f"[CLARIQ FEEDBACK] {feedback_data['type'].upper()} - {feedback_data['subject']}"
            msg['Subject'] = subject
            
            # Email body
            body = f"""
New {feedback_data['type']} received on CLARIQ:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From: {feedback_data['user_name']} ({feedback_data['user_email']})
Type: {feedback_data['type'].upper()}
Priority: {feedback_data.get('priority', 'normal').upper()}
Date: {feedback_data.get('created_at', datetime.now().isoformat())}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Subject: {feedback_data['subject']}

Message:
{feedback_data['message']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reply to: {feedback_data['user_email']}

Manage feedback: https://tryclariq.com/admin/feedback
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"❌ Error sending feedback email: {e}")
            return False
    
    def send_user_confirmation(self, user_email: str, feedback_id: int) -> bool:
        """Send confirmation email to user"""
        
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = user_email
            msg['Subject'] = f"We received your feedback (Ticket #{feedback_id})"
            
            body = f"""
Thank you for your feedback!

We have received your submission and assigned it ticket #{ feedback_id}.
Our team will review your feedback shortly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket #: {feedback_id}
Status: Open
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If your issue is urgent, please reach out to support@tryclariq.com

Check your feedback status: https://tryclariq.com/support/ticket/{feedback_id}

Best regards,
The CLARIQ Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"❌ Error sending confirmation email: {e}")
            return False


# Initialize database on import
feedback_db = FeedbackDB("data/clariq_feedback.sqlite")
email_notifier = EmailNotifier()
