"""
Google Sheets Integration Service for CLARIQ

Exports pilot data to Google Sheets for real-time collaboration
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service for exporting data to Google Sheets"""
    
    def __init__(self):
        self.creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.client = None
        self.spreadsheet = None
        
        if self.creds_json and self.spreadsheet_id:
            try:
                creds_dict = json.loads(self.creds_json)
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                self.client = gspread.authorize(credentials)
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            except Exception as e:
                logger.error(f'Google Sheets initialization failed: {str(e)}')
    
    def is_configured(self) -> bool:
        """Check if Google Sheets is configured"""
        return bool(self.client and self.spreadsheet)
    
    def export_pilots(self, pilots_data: List[Dict]) -> Dict:
        """Export pilots to Google Sheets"""
        if not self.is_configured():
            return {'success': False, 'message': 'Google Sheets not configured'}
        
        try:
            worksheet = self._get_or_create_worksheet('Pilots')
            
            # Prepare headers
            headers = list(pilots_data[0].keys()) if pilots_data else []
            
            # Clear existing data
            worksheet.clear()
            
            # Write headers
            if headers:
                worksheet.append_row(headers)
                
                # Write data rows
                for pilot in pilots_data:
                    row = [pilot.get(h, '') for h in headers]
                    worksheet.append_row(row)
            
            return {
                'success': True,
                'message': f'Exported {len(pilots_data)} pilots to Google Sheets',
                'worksheet': 'Pilots',
                'row_count': len(pilots_data) + 1
            }
        except Exception as e:
            logger.error(f'Google Sheets export failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def export_actions(self, actions_data: List[Dict]) -> Dict:
        """Export actions to Google Sheets"""
        if not self.is_configured():
            return {'success': False, 'message': 'Google Sheets not configured'}
        
        try:
            worksheet = self._get_or_create_worksheet('Actions')
            
            # Prepare headers
            headers = list(actions_data[0].keys()) if actions_data else []
            
            # Clear and write
            worksheet.clear()
            if headers:
                worksheet.append_row(headers)
                for action in actions_data:
                    row = [action.get(h, '') for h in headers]
                    worksheet.append_row(row)
            
            return {
                'success': True,
                'message': f'Exported {len(actions_data)} actions to Google Sheets',
                'worksheet': 'Actions',
                'row_count': len(actions_data) + 1
            }
        except Exception as e:
            logger.error(f'Google Sheets export failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def create_live_dashboard(self, dashboard_name: str = 'CLARIQ Dashboard') -> Dict:
        """Create live dashboard sheet with key metrics"""
        if not self.is_configured():
            return {'success': False, 'message': 'Google Sheets not configured'}
        
        try:
            worksheet = self._get_or_create_worksheet(dashboard_name)
            worksheet.clear()
            
            # Add dashboard content
            dashboard_content = [
                ['CLARIQ Pilot Program Dashboard'],
                ['Updated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                [],
                ['Key Metrics'],
                ['Total Pilots', '=COUNTA(Pilots!A2:A)'],
                ['Total Revenue', '=SUM(Pilots!D2:D)'],
                ['Average ROI', '=AVERAGE(Pilots!E2:E)'],
                [],
                ['Pilot Performance'],
                ['Name', 'Store', 'Revenue', 'ROI %', 'Status'],
            ]
            
            for row in dashboard_content:
                worksheet.append_row(row)
            
            return {
                'success': True,
                'message': f'Created live dashboard: {dashboard_name}',
                'worksheet': dashboard_name
            }
        except Exception as e:
            logger.error(f'Dashboard creation failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def append_row(self, worksheet_name: str, row_data: List) -> Dict:
        """Append a row to specified worksheet"""
        if not self.is_configured():
            return {'success': False, 'message': 'Google Sheets not configured'}
        
        try:
            worksheet = self._get_or_create_worksheet(worksheet_name)
            worksheet.append_row(row_data)
            
            return {
                'success': True,
                'message': f'Row appended to {worksheet_name}'
            }
        except Exception as e:
            logger.error(f'Row append failed: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    def _get_or_create_worksheet(self, worksheet_name: str):
        """Get existing worksheet or create new one"""
        try:
            return self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=26)


# Global instance
sheets_service = GoogleSheetsService()
