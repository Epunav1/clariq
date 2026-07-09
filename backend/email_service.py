import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

class EmailService:
    def __init__(self):
        """Initialize email service with environment variables."""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', 'noreply@clariq.io')
        self.enabled = bool(self.smtp_user and self.smtp_password)
    
    def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> dict:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body (plain text or HTML)
            html: If True, treat body as HTML; otherwise plain text
        
        Returns:
            dict with keys: success (bool), message (str), sent_at (str or None)
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "Email service not configured. Set SMTP_USER and SMTP_PASSWORD.",
                "sent_at": None
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return {
                "success": True,
                "message": f"Email sent to {to_email}",
                "sent_at": datetime.utcnow().isoformat()
            }
        
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": "SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD.",
                "sent_at": None
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "message": f"SMTP error: {str(e)}",
                "sent_at": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Email error: {str(e)}",
                "sent_at": None
            }
    
    def send_pilot_outreach_email(self, to_email: str, pilot_name: str, store_name: str) -> dict:
        """
        Send a standardized pilot outreach email.
        
        Args:
            to_email: Recipient email
            pilot_name: Name of the pilot applicant
            store_name: Name of their store
        
        Returns:
            dict with success status and message
        """
        subject = "Join clariq's 7-day pilot program — free"
        body = f"""Hi {pilot_name},

Thank you for your interest in clariq's pilot program! We're excited to help {store_name} boost revenue through better data insights.

Here's what you get in the 7-day pilot:
• Unlimited questions asked to clariq's AI
• Real-time insights across all your platforms
• Automatic reorder recommendations
• Full access to all features

No credit card required. Just let us know if you have any questions.

Ready to get started? Reply to this email or visit https://tryclariq.com/pilot

Best regards,
The clariq team

P.S. After 7 days, we'll share your results and discuss next steps."""
        
        return self.send_email(to_email, subject, body)
    
    def send_pilot_results_email(self, to_email: str, pilot_name: str, store_name: str, 
                                 reorder_count: int, est_value: int, days_active: int) -> dict:
        """
        Send pilot results summary email.
        
        Args:
            to_email: Recipient email
            pilot_name: Name of the pilot applicant
            store_name: Name of their store
            reorder_count: Number of reorders placed
            est_value: Estimated revenue impact
            days_active: Number of days pilot was active
        
        Returns:
            dict with success status and message
        """
        subject = f"Your clariq pilot results — {reorder_count} reorders, ${est_value} impact"
        body = f"""Hi {pilot_name},

Your 7-day clariq pilot is complete! Here's what happened at {store_name}:

━━━━━━━━━━━━━━━━━━━━━━
Results Summary
━━━━━━━━━━━━━━━━━━━━━━
• Reorders placed: {reorder_count}
• Days active: {days_active}
• Estimated impact: ${est_value}
• Velocity: {round(reorder_count/days_active, 2) if days_active > 0 else 0}/day

This suggests your store could generate ${est_value * (30/days_active):.0f} per month 
using clariq to drive repeat purchases.

Ready to continue? Let's discuss scaling your pilot into a full rollout.

Best regards,
The clariq team"""
        
        return self.send_email(to_email, subject, body)


# Global instance
email_service = EmailService()
