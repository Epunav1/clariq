"""
Advanced Analytics Engine for CLARIQ Pilot Program

Features:
- Predictive ROI forecasting using linear/exponential regression
- Cohort analysis (grouping pilots by attributes)
- Churn risk prediction
- Competitive benchmarking
- Trend analysis and forecasting
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from db.pilots_db import get_pilot, list_pilots
from db.actions_db import get_pilot_actions, get_action_summary
from db.revenue_calc import calculate_revenue
from db.roi_calc import calculate_pilot_roi
import json

class AdvancedAnalytics:
    """Advanced analytics and forecasting engine"""
    
    def __init__(self, db_path: str = "data/clariq_analytics.sqlite"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize analytics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cohorts (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    definition TEXT,
                    pilot_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS churn_predictions (
                    pilot_id INTEGER PRIMARY KEY,
                    churn_probability REAL,
                    churn_risk_level TEXT,
                    contributing_factors TEXT,
                    recommendation TEXT,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS forecast_data (
                    id INTEGER PRIMARY KEY,
                    pilot_id INTEGER,
                    metric TEXT,
                    forecast_period_days INTEGER,
                    predicted_value REAL,
                    confidence_interval REAL,
                    forecast_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(pilot_id) REFERENCES pilots(id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_forecast_pilot ON forecast_data(pilot_id)")
            conn.commit()
    
    # ===== PREDICTIVE FORECASTING =====
    def forecast_roi(self, pilot_id: int, days: int = 30) -> Dict:
        """
        Forecast ROI for next N days using historical trend
        
        Args:
            pilot_id: Pilot ID
            days: Number of days to forecast
            
        Returns:
            {
                'pilot_id': int,
                'current_roi': float,
                'forecast': {
                    'days_30': float,
                    'days_60': float,
                    'days_90': float
                },
                'trend': 'increasing|stable|decreasing',
                'confidence': 0.0-1.0,
                'factors': [...]
            }
        """
        pilot = get_pilot(pilot_id)
        if not pilot:
            return {'error': 'Pilot not found'}
        
        # Get current ROI
        current_roi_data = calculate_pilot_roi(pilot_id)
        current_roi = current_roi_data.get('roi_metrics', {}).get('roi_percent', 0)
        
        # Get historical ROI data (actions over time)
        actions = get_pilot_actions(pilot_id)
        
        # Calculate historical trend
        if len(actions) < 3:
            # Not enough data, return conservative forecast
            return {
                'pilot_id': pilot_id,
                'current_roi': current_roi,
                'forecast': {
                    'days_30': current_roi * 1.1,
                    'days_60': current_roi * 1.2,
                    'days_90': current_roi * 1.3
                },
                'trend': 'unknown',
                'confidence': 0.3,
                'note': 'Limited historical data'
            }
        
        # Calculate growth rate from actions
        timestamps = [a['created_at'] for a in sorted(actions, key=lambda x: x['created_at'])]
        if len(timestamps) < 2:
            return {'error': 'Insufficient action history'}
        
        # Linear regression on order count over time
        action_counts = np.array([len([a for a in actions if a['created_at'] <= ts]) for ts in timestamps])
        days_elapsed = np.array([(pd.to_datetime(ts) - pd.to_datetime(timestamps[0])).days for ts in timestamps])
        
        # Avoid division by zero
        if np.max(days_elapsed) == 0:
            growth_rate = 0
            trend = 'stable'
        else:
            # Linear fit
            coeffs = np.polyfit(days_elapsed, action_counts, 1)
            growth_rate = coeffs[0]
            
            if growth_rate > 0.1:
                trend = 'increasing'
            elif growth_rate < -0.05:
                trend = 'decreasing'
            else:
                trend = 'stable'
        
        # Forecast ROI based on growth
        base_multiplier = 1.0 + (growth_rate / 10)
        forecast_30 = current_roi * (base_multiplier ** 1)
        forecast_60 = current_roi * (base_multiplier ** 2)
        forecast_90 = current_roi * (base_multiplier ** 3)
        
        return {
            'pilot_id': pilot_id,
            'current_roi': current_roi,
            'forecast': {
                'days_30': round(forecast_30, 2),
                'days_60': round(forecast_60, 2),
                'days_90': round(forecast_90, 2)
            },
            'trend': trend,
            'growth_rate': round(growth_rate, 4),
            'confidence': min(0.9, 0.3 + len(actions) * 0.05),
            'factors': [
                f'Action growth rate: {growth_rate:.2f}/day',
                f'Current momentum: {trend}',
                f'Historical actions: {len(actions)}'
            ]
        }
    
    def forecast_revenue(self, pilot_id: int, days: int = 30) -> Dict:
        """Forecast revenue for next N days"""
        pilot = get_pilot(pilot_id)
        if not pilot:
            return {'error': 'Pilot not found'}
        
        current_revenue = calculate_revenue(pilot_id)
        actions = get_pilot_actions(pilot_id)
        
        # Calculate average daily revenue from reorders
        reorder_actions = [a for a in actions if a['type'] == 'reorder']
        
        if not reorder_actions:
            return {
                'pilot_id': pilot_id,
                'current_revenue': current_revenue,
                'forecast': {
                    'days_30': current_revenue,
                    'days_60': current_revenue,
                    'days_90': current_revenue
                },
                'trend': 'no_activity',
                'confidence': 0.1
            }
        
        # Average revenue per reorder
        avg_revenue_per_reorder = current_revenue / len(reorder_actions) if reorder_actions else 0
        
        # Calculate reorder frequency
        if len(reorder_actions) >= 2:
            time_spans = []
            for i in range(1, len(reorder_actions)):
                try:
                    from datetime import datetime
                    t1 = datetime.fromisoformat(reorder_actions[i]['created_at'])
                    t0 = datetime.fromisoformat(reorder_actions[i-1]['created_at'])
                    time_spans.append((t1 - t0).days)
                except:
                    continue
            
            avg_days_between_reorders = np.mean(time_spans) if time_spans else 30
        else:
            avg_days_between_reorders = 30
        
        # Forecast based on frequency
        reorders_in_30_days = 30 / avg_days_between_reorders if avg_days_between_reorders > 0 else 0
        
        return {
            'pilot_id': pilot_id,
            'current_revenue': current_revenue,
            'forecast': {
                'days_30': round(current_revenue + (reorders_in_30_days * avg_revenue_per_reorder), 2),
                'days_60': round(current_revenue + (reorders_in_30_days * 2 * avg_revenue_per_reorder), 2),
                'days_90': round(current_revenue + (reorders_in_30_days * 3 * avg_revenue_per_reorder), 2)
            },
            'reorder_frequency_days': round(avg_days_between_reorders, 1),
            'avg_revenue_per_reorder': round(avg_revenue_per_reorder, 2),
            'confidence': min(0.9, 0.4 + len(reorder_actions) * 0.1)
        }
    
    # ===== COHORT ANALYSIS =====
    def create_cohort(self, name: str, definition: Dict) -> Dict:
        """
        Create a pilot cohort based on criteria
        
        Definition example:
        {
            'status': 'active',
            'min_revenue': 1000,
            'max_roi': 100,
            'industry': 'retail'
        }
        """
        pilots = list_pilots()
        matching_pilots = self._filter_pilots(pilots, definition)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cohorts (name, definition, pilot_count)
                VALUES (?, ?, ?)
            """, (name, json.dumps(definition), len(matching_pilots)))
            conn.commit()
        
        return {
            'cohort_name': name,
            'pilot_count': len(matching_pilots),
            'pilots': matching_pilots,
            'definition': definition
        }
    
    def analyze_cohort(self, name: str) -> Dict:
        """Analyze metrics for a cohort"""
        with sqlite3.connect(self.db_path) as conn:
            cohort = conn.execute(
                "SELECT definition, pilot_count FROM cohorts WHERE name = ?",
                (name,)
            ).fetchone()
        
        if not cohort:
            return {'error': 'Cohort not found'}
        
        definition = json.loads(cohort[0])
        pilots = list_pilots()
        matching_pilots = self._filter_pilots(pilots, definition)
        
        # Calculate cohort metrics
        revenues = []
        rois = []
        reorder_counts = []
        
        for pilot in matching_pilots:
            revenue = calculate_revenue(pilot['id'])
            roi_data = calculate_pilot_roi(pilot['id'])
            roi_pct = roi_data.get('roi_metrics', {}).get('roi_percent', 0)
            reorders = roi_data.get('action_metrics', {}).get('reorder_count', 0)
            
            revenues.append(revenue)
            rois.append(roi_pct)
            reorder_counts.append(reorders)
        
        return {
            'cohort_name': name,
            'pilot_count': len(matching_pilots),
            'definition': definition,
            'metrics': {
                'revenue': {
                    'avg': round(np.mean(revenues), 2) if revenues else 0,
                    'median': round(np.median(revenues), 2) if revenues else 0,
                    'min': round(np.min(revenues), 2) if revenues else 0,
                    'max': round(np.max(revenues), 2) if revenues else 0
                },
                'roi': {
                    'avg': round(np.mean(rois), 2) if rois else 0,
                    'median': round(np.median(rois), 2) if rois else 0,
                    'min': round(np.min(rois), 2) if rois else 0,
                    'max': round(np.max(rois), 2) if rois else 0
                },
                'reorders': {
                    'avg': round(np.mean(reorder_counts), 2) if reorder_counts else 0,
                    'total': sum(reorder_counts)
                }
            }
        }
    
    # ===== CHURN PREDICTION =====
    def predict_churn_risk(self, pilot_id: int) -> Dict:
        """
        Predict churn risk for a pilot (0-100%)
        
        Factors:
        - Days since last action
        - Action frequency decline
        - ROI trend
        - Engagement level
        """
        pilot = get_pilot(pilot_id)
        if not pilot:
            return {'error': 'Pilot not found'}
        
        actions = get_pilot_actions(pilot_id)
        if not actions:
            return {
                'pilot_id': pilot_id,
                'churn_probability': 0.8,
                'churn_risk_level': 'high',
                'factors': ['No activity recorded'],
                'recommendation': 'Immediate outreach recommended'
            }
        
        # Factor 1: Days since last action
        try:
            from datetime import datetime
            last_action = max([datetime.fromisoformat(a['created_at']) for a in actions])
            days_inactive = (datetime.now() - last_action).days
            inactivity_score = min(100, days_inactive * 5)  # Max 100
        except:
            inactivity_score = 0
        
        # Factor 2: Action frequency trend
        recent_actions = [a for a in actions if (datetime.now() - datetime.fromisoformat(a['created_at'])).days <= 30]
        old_actions = [a for a in actions if 30 < (datetime.now() - datetime.fromisoformat(a['created_at'])).days <= 60]
        
        frequency_decline = 0
        if len(old_actions) > 0:
            frequency_ratio = len(recent_actions) / len(old_actions)
            if frequency_ratio < 0.5:
                frequency_decline = 50
            elif frequency_ratio < 0.8:
                frequency_decline = 25
        
        # Factor 3: ROI trend
        roi_data = calculate_pilot_roi(pilot_id)
        roi_status = roi_data.get('roi_metrics', {}).get('roi_status', '')
        roi_score = 0
        if roi_status == 'Loss':
            roi_score = 40
        elif roi_status == 'Break-even':
            roi_score = 20
        
        # Factor 4: Engagement level (number of different action types)
        action_types = set([a['type'] for a in actions])
        engagement_score = max(0, 30 - len(action_types) * 5)
        
        # Combine factors
        churn_probability = (inactivity_score * 0.4 + frequency_decline * 0.3 + roi_score * 0.2 + engagement_score * 0.1) / 100
        churn_probability = min(1.0, max(0.0, churn_probability))
        
        # Risk level
        if churn_probability > 0.7:
            risk_level = 'high'
        elif churn_probability > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Recommendations
        recommendations = []
        if days_inactive > 30:
            recommendations.append('Contact pilot to check in')
        if frequency_decline > 25:
            recommendations.append('Activity declining - offer support')
        if roi_status == 'Loss':
            recommendations.append('Negative ROI - discuss optimization strategies')
        if len(action_types) < 2:
            recommendations.append('Low engagement - introduce new features')
        
        # Store prediction
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO churn_predictions
                (pilot_id, churn_probability, churn_risk_level, contributing_factors, recommendation)
                VALUES (?, ?, ?, ?, ?)
            """, (pilot_id, churn_probability, risk_level, 
                  json.dumps(recommendations), '; '.join(recommendations)))
            conn.commit()
        
        return {
            'pilot_id': pilot_id,
            'pilot_name': pilot.get('name', 'Unknown'),
            'churn_probability': round(churn_probability, 2),
            'churn_risk_level': risk_level,
            'days_inactive': days_inactive,
            'frequency_decline_pct': round(frequency_decline, 1),
            'roi_status': roi_status,
            'engagement_score': round(100 - engagement_score, 1),
            'contributing_factors': recommendations,
            'recommendation': recommendations[0] if recommendations else 'Monitor pilot'
        }
    
    # ===== BENCHMARKING =====
    def benchmark_pilot(self, pilot_id: int) -> Dict:
        """Compare pilot to industry benchmarks and peer averages"""
        pilot = get_pilot(pilot_id)
        if not pilot:
            return {'error': 'Pilot not found'}
        
        # Get pilot metrics
        pilot_revenue = calculate_revenue(pilot_id)
        pilot_roi_data = calculate_pilot_roi(pilot_id)
        pilot_roi = pilot_roi_data.get('roi_metrics', {}).get('roi_percent', 0)
        pilot_reorders = pilot_roi_data.get('action_metrics', {}).get('reorder_count', 0)
        
        # Get all pilots for comparison
        all_pilots = list_pilots()
        all_revenues = []
        all_rois = []
        all_reorders = []
        
        for p in all_pilots:
            if p['id'] != pilot_id:  # Exclude self
                rev = calculate_revenue(p['id'])
                roi_d = calculate_pilot_roi(p['id'])
                all_revenues.append(rev)
                all_rois.append(roi_d.get('roi_metrics', {}).get('roi_percent', 0))
                all_reorders.append(roi_d.get('action_metrics', {}).get('reorder_count', 0))
        
        # Calculate percentiles
        def percentile(data, pilot_val):
            if not data:
                return 50
            return round(sum([1 for v in data if v <= pilot_val]) / len(data) * 100)
        
        return {
            'pilot_id': pilot_id,
            'pilot_name': pilot.get('name', 'Unknown'),
            'benchmarks': {
                'revenue': {
                    'pilot_value': round(pilot_revenue, 2),
                    'peer_average': round(np.mean(all_revenues), 2) if all_revenues else 0,
                    'peer_median': round(np.median(all_revenues), 2) if all_revenues else 0,
                    'percentile': percentile(all_revenues, pilot_revenue),
                    'above_average': pilot_revenue > np.mean(all_revenues) if all_revenues else False
                },
                'roi': {
                    'pilot_value': round(pilot_roi, 2),
                    'peer_average': round(np.mean(all_rois), 2) if all_rois else 0,
                    'peer_median': round(np.median(all_rois), 2) if all_rois else 0,
                    'percentile': percentile(all_rois, pilot_roi),
                    'above_average': pilot_roi > np.mean(all_rois) if all_rois else False
                },
                'reorders': {
                    'pilot_value': pilot_reorders,
                    'peer_average': round(np.mean(all_reorders), 1) if all_reorders else 0,
                    'peer_median': round(np.median(all_reorders), 1) if all_reorders else 0,
                    'percentile': percentile(all_reorders, pilot_reorders)
                }
            },
            'performance_summary': self._get_performance_summary(
                percentile(all_revenues, pilot_revenue),
                percentile(all_rois, pilot_roi),
                percentile(all_reorders, pilot_reorders)
            )
        }
    
    def _filter_pilots(self, pilots: List[Dict], criteria: Dict) -> List[Dict]:
        """Filter pilots by criteria"""
        filtered = pilots
        
        for key, value in criteria.items():
            if key == 'status':
                filtered = [p for p in filtered if p.get('status') == value]
            elif key == 'min_revenue':
                filtered = [p for p in filtered if calculate_revenue(p['id']) >= value]
            elif key == 'max_revenue':
                filtered = [p for p in filtered if calculate_revenue(p['id']) <= value]
            elif key == 'min_roi':
                filtered = [p for p in filtered if calculate_pilot_roi(p['id']).get('roi_metrics', {}).get('roi_percent', 0) >= value]
            elif key == 'max_roi':
                filtered = [p for p in filtered if calculate_pilot_roi(p['id']).get('roi_metrics', {}).get('roi_percent', 0) <= value]
            elif key == 'platform':
                filtered = [p for p in filtered if p.get('platform') == value]
        
        return filtered
    
    def _get_performance_summary(self, revenue_pct: int, roi_pct: int, reorder_pct: int) -> str:
        """Generate performance summary based on percentiles"""
        avg_pct = (revenue_pct + roi_pct + reorder_pct) / 3
        
        if avg_pct >= 80:
            return 'Top Performer'
        elif avg_pct >= 60:
            return 'Above Average'
        elif avg_pct >= 40:
            return 'Average'
        elif avg_pct >= 20:
            return 'Below Average'
        else:
            return 'Needs Attention'


# Global instance
advanced_analytics = AdvancedAnalytics()
