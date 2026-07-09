"""
Slack Integration Service for CLARIQ

Sends alerts, notifications, and reports to Slack channels
"""

import os
import json
from typing import Dict, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SlackNotificationService:
    """Service for sending notifications to Slack"""
    
    def __init__(self):
        self.token = os.getenv('SLACK_BOT_TOKEN')
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.client = WebClient(token=self.token) if self.token else None
    
    def is_configured(self) -> bool:
        """Check if Slack is configured"""
        return bool(self.token or self.webhook_url)
    
    def send_milestone_alert(self, pilot_name: str, store_name: str, 
                           milestone_title: str, milestone_emoji: str,
                           value_achieved: float, threshold: float) -> Dict:
        """Send milestone achievement alert to Slack"""
        if not self.is_configured():
            return {'success': False, 'message': 'Slack not configured'}
        
        message = {
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': f'{milestone_emoji} Milestone Achieved!',
                        'emoji': True
                    }
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f'*Pilot:* {pilot_name}'
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f'*Store:* {store_name}'
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f'*Milestone:* {milestone_title}'
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f'*Achievement:* {value_achieved} / {threshold}'
                        }
                    ]
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': f'_Reported at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}_'
                        }
                    ]
                }
            ]
        }
        
        return self._send_message(message)
    
    def send_alert(self, title: str, message: str, severity: str = 'info',
                  additional_fields: Optional[Dict] = None) -> Dict:
        """Send general alert to Slack"""
        if not self.is_configured():
            return {'success': False, 'message': 'Slack not configured'}
        
        color_map = {
            'critical': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'success': '#28a745'
        }
        
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': title,
                    'emoji': True
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': message
                }
            }
        ]
        
        if additional_fields:
            fields = []
            for key, value in additional_fields.items():
                fields.append({
                    'type': 'mrkdwn',
                    'text': f'*{key}:* {value}'
                })
            blocks.append({
                'type': 'section',
                'fields': fields
            })
        
        msg_data = {'blocks': blocks}
        return self._send_message(msg_data)
    
    def send_pilot_report(self, pilot_name: str, metrics: Dict) -> Dict:
        """Send pilot performance report to Slack"""
        if not self.is_configured():
            return {'success': False, 'message': 'Slack not configured'}
        
        message = {
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': f'📊 Pilot Report: {pilot_name}',
                        'emoji': True
                    }
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f"*Revenue:* ${metrics.get('revenue', 0):.2f}"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*ROI:* {metrics.get('roi_percent', 0):.1f}%"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*Reorders:* {metrics.get('reorder_count', 0)}"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*Status:* {metrics.get('roi_status', 'Unknown')}"
                        }
                    ]
                }
            ]
        }
        
        return self._send_message(message)
    
    def send_churn_warning(self, pilot_name: str, churn_probability: float,
                          recommendation: str) -> Dict:
        """Send churn warning to Slack"""
        if not self.is_configured():
            return {'success': False, 'message': 'Slack not configured'}
        
        message = {
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': '⚠️ Churn Risk Alert',
                        'emoji': True
                    }
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f'*Pilot:* {pilot_name}'
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f'*Risk Level:* {churn_probability:.1%}'
                        }
                    ]
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f'*Recommendation:* {recommendation}'
                    }
                }
            ]
        }
        
        return self._send_message(message)
    
    def _send_message(self, message: Dict) -> Dict:
        """Internal method to send message"""
        try:
            if self.webhook_url:
                # Use webhook
                import requests
                response = requests.post(self.webhook_url, json=message, timeout=10)
                return {
                    'success': response.status_code == 200,
                    'message': f'Webhook response: {response.status_code}'
                }
            elif self.client:
                # Use SDK
                response = self.client.chat_postMessage(
                    channel=os.getenv('SLACK_CHANNEL', '#alerts'),
                    blocks=message.get('blocks')
                )
                return {'success': True, 'message': 'Message sent'}
        except Exception as e:
            logger.error(f'Slack notification failed: {str(e)}')
            return {'success': False, 'message': str(e)}


# Global instance
slack_service = SlackNotificationService()
