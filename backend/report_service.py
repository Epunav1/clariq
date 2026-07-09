"""Email report generation service for pilot program metrics."""

from db.pilots_db import list_pilots
from db.actions_db import count_actions
from db.revenue_calc import calculate_pilot_revenue
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def generate_weekly_summary_report(end_date: Optional[str] = None) -> Dict:
    """Generate a comprehensive weekly summary report."""
    if not end_date:
        end_date = datetime.utcnow().isoformat()
    else:
        end_date = datetime.fromisoformat(end_date).isoformat()
    
    end_datetime = datetime.fromisoformat(end_date)
    start_datetime = end_datetime - timedelta(days=7)
    
    pilots = list_pilots()
    
    # Calculate metrics
    total_pilots = len(pilots)
    contacted = sum(1 for p in pilots if p.get('status') == 'contacted')
    completed = sum(1 for p in pilots if p.get('status') == 'completed')
    
    total_reorders = 0
    total_discounts = 0
    total_promotions = 0
    total_queries = 0
    total_revenue = 0
    days_active_sum = 0
    
    active_pilots = []
    
    for p in pilots:
        pilot_id = p['id']
        
        # Get actions
        reorders = count_actions(action_type='reorder', pilot_id=pilot_id)
        discounts = count_actions(action_type='discount', pilot_id=pilot_id)
        promotions = count_actions(action_type='promotion', pilot_id=pilot_id)
        queries = count_actions(action_type='query', pilot_id=pilot_id)
        
        total_reorders += reorders
        total_discounts += discounts
        total_promotions += promotions
        total_queries += queries
        
        # Get revenue
        revenue_data = calculate_pilot_revenue(pilot_id)
        revenue = revenue_data.get('total_revenue', 0)
        total_revenue += revenue
        
        # Calculate days active
        days_active = 0
        if p.get('contacted_at'):
            try:
                contacted_date = datetime.fromisoformat(p['contacted_at'])
                days_active = (datetime.utcnow() - contacted_date).days
            except:
                pass
        
        days_active_sum += days_active
        
        if reorders > 0 or revenue > 0:
            active_pilots.append({
                'name': p['name'],
                'store': p['store_name'],
                'reorders': reorders,
                'revenue': revenue,
                'status': p.get('status', 'new')
            })
    
    # Sort active pilots by revenue
    active_pilots.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Calculate averages
    avg_reorders = round(total_reorders / total_pilots, 2) if total_pilots > 0 else 0
    avg_revenue = round(total_revenue / total_pilots, 2) if total_pilots > 0 else 0
    avg_days_active = round(days_active_sum / total_pilots, 1) if total_pilots > 0 else 0
    
    # Engagement metrics
    engagement_rate = round((contacted / total_pilots * 100), 1) if total_pilots > 0 else 0
    completion_rate = round((completed / total_pilots * 100), 1) if total_pilots > 0 else 0
    
    return {
        'report_type': 'weekly_summary',
        'generated_at': datetime.utcnow().isoformat(),
        'period': f"{start_datetime.strftime('%Y-%m-%d')} to {end_datetime.strftime('%Y-%m-%d')}",
        'metrics': {
            'total_pilots': total_pilots,
            'contacted': contacted,
            'completed': completed,
            'engagement_rate': engagement_rate,
            'completion_rate': completion_rate,
            'total_reorders': total_reorders,
            'avg_reorders': avg_reorders,
            'total_discounts': total_discounts,
            'total_promotions': total_promotions,
            'total_queries': total_queries,
            'total_revenue': round(total_revenue, 2),
            'avg_revenue': avg_revenue,
            'avg_days_active': avg_days_active,
        },
        'top_performers': active_pilots[:5],
        'performance_tier': 'strong' if engagement_rate >= 70 else 'healthy' if engagement_rate >= 50 else 'emerging'
    }


def generate_cohort_report(end_date: Optional[str] = None) -> Dict:
    """Generate cohort performance report."""
    if not end_date:
        end_date = datetime.utcnow().isoformat()
    else:
        end_date = datetime.fromisoformat(end_date).isoformat()
    
    from collections import defaultdict
    
    pilots = list_pilots()
    cohorts = defaultdict(list)
    
    # Group by week
    for p in pilots:
        created_at_str = p.get('created_at')
        if created_at_str:
            try:
                created_date = datetime.fromisoformat(created_at_str)
                week_start = created_date - timedelta(days=created_date.weekday())
                cohort_key = week_start.strftime('%Y-W%U')
                cohort_label = week_start.strftime('%b %d')
                cohorts[cohort_key].append({'label': cohort_label, 'pilot': p})
            except:
                continue
    
    # Analyze cohorts
    cohort_data = []
    for cohort_key in sorted(cohorts.keys()):
        cohort_pilots = [c['pilot'] for c in cohorts[cohort_key]]
        cohort_label = cohorts[cohort_key][0]['label'] if cohorts[cohort_key] else cohort_key
        
        total = len(cohort_pilots)
        contacted = sum(1 for p in cohort_pilots if p.get('status') == 'contacted')
        reorders = sum(count_actions(action_type='reorder', pilot_id=p['id']) for p in cohort_pilots)
        revenue = sum(calculate_pilot_revenue(p['id']).get('total_revenue', 0) for p in cohort_pilots)
        
        engagement = round((contacted / total * 100), 1) if total > 0 else 0
        
        cohort_data.append({
            'cohort': cohort_label,
            'size': total,
            'engagement': engagement,
            'reorders': reorders,
            'revenue': round(revenue, 2)
        })
    
    return {
        'report_type': 'cohort_analysis',
        'generated_at': datetime.utcnow().isoformat(),
        'cohorts': cohort_data
    }


def format_email_body(report: Dict, recipient_name: str = "Team") -> str:
    """Format report data as email body text."""
    body = f"Hi {recipient_name},\n\n"
    body += f"📊 CLARIQ Pilot Program Report\n"
    body += f"Generated: {datetime.fromisoformat(report['generated_at']).strftime('%b %d, %Y at %I:%M %p')}\n"
    body += f"Period: {report.get('period', 'N/A')}\n\n"
    
    if report['report_type'] == 'weekly_summary':
        m = report['metrics']
        body += f"=== KEY METRICS ===\n"
        body += f"Total Pilots: {m['total_pilots']}\n"
        body += f"Contacted: {m['contacted']} ({m['engagement_rate']}%)\n"
        body += f"Completed: {m['completed']} ({m['completion_rate']}%)\n"
        body += f"Total Reorders: {m['total_reorders']} (avg {m['avg_reorders']}/pilot)\n"
        body += f"Total Revenue: ${m['total_revenue']} (avg ${m['avg_revenue']}/pilot)\n"
        body += f"Avg Days Active: {m['avg_days_active']}\n\n"
        
        body += f"=== ACTION BREAKDOWN ===\n"
        body += f"Discounts: {m['total_discounts']}\n"
        body += f"Promotions: {m['total_promotions']}\n"
        body += f"Queries: {m['total_queries']}\n\n"
        
        body += f"=== PERFORMANCE TIER ===\n"
        tier_desc = {
            'strong': '💪 Strong (Excellent engagement, high reorder rate)',
            'healthy': '✓ Healthy (Good engagement, steady momentum)',
            'emerging': '🌱 Emerging (Growing engagement, building momentum)'
        }
        body += f"{tier_desc.get(report['performance_tier'], 'N/A')}\n\n"
        
        if report.get('top_performers'):
            body += f"=== TOP 5 PERFORMERS ===\n"
            for idx, p in enumerate(report['top_performers'], 1):
                body += f"{idx}. {p['name']} ({p['store']}): {p['reorders']} reorders, ${p['revenue']} revenue\n"
            body += "\n"
    
    elif report['report_type'] == 'cohort_analysis':
        body += f"=== COHORT PERFORMANCE ===\n"
        for c in report.get('cohorts', []):
            body += f"{c['cohort']}: {c['size']} pilots, {c['engagement']}% engaged, {c['reorders']} reorders, ${c['revenue']} revenue\n"
        body += "\n"
    
    body += f"View full dashboard: https://tryclariq.com/dashboard\n"
    body += f"\nBest regards,\nCLARIQ Team"
    
    return body


def format_email_html(report: Dict, recipient_name: str = "Team") -> str:
    """Format report data as HTML email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .header {{ background: #4a5568; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f7f8fb; padding: 20px; }}
            .section {{ background: white; padding: 16px; margin: 12px 0; border-radius: 6px; border-left: 3px solid #4299e1; }}
            .metric {{ display: inline-block; margin-right: 20px; }}
            .metric-label {{ font-size: 12px; color: #718096; }}
            .metric-value {{ font-size: 20px; font-weight: bold; color: #2d3748; }}
            .tier {{ padding: 12px; border-radius: 4px; margin: 8px 0; }}
            .tier-strong {{ background: #c6f6d5; color: #22543d; }}
            .tier-healthy {{ background: #bee3f8; color: #2c5282; }}
            .tier-emerging {{ background: #feebc8; color: #7c2d12; }}
            table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
            th {{ background: #edf2f7; padding: 8px; text-align: left; font-size: 12px; font-weight: 600; }}
            td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; }}
            .footer {{ font-size: 12px; color: #718096; text-align: center; padding: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">📊 CLARIQ Pilot Program Report</h2>
                <p style="margin: 4px 0; opacity: 0.9;">Hi {recipient_name}</p>
            </div>
            <div class="content">
    """
    
    if report['report_type'] == 'weekly_summary':
        m = report['metrics']
        html += f"""
            <div class="section">
                <h3 style="margin-top: 0;">Weekly Summary</h3>
                <p style="color: #718096; margin: 0;">Period: {report.get('period', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h4 style="margin-top: 0; color: #2d3748;">Key Metrics</h4>
                <div class="metric">
                    <div class="metric-label">Total Pilots</div>
                    <div class="metric-value">{m['total_pilots']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Engagement Rate</div>
                    <div class="metric-value">{m['engagement_rate']}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Reorders</div>
                    <div class="metric-value">{m['avg_reorders']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Revenue</div>
                    <div class="metric-value">${m['total_revenue']}</div>
                </div>
            </div>
            
            <div class="section">
                <h4 style="margin-top: 0; color: #2d3748;">Performance Actions</h4>
                <table>
                    <tr>
                        <th>Action Type</th>
                        <th>Count</th>
                    </tr>
                    <tr>
                        <td>Reorders</td>
                        <td><strong>{m['total_reorders']}</strong></td>
                    </tr>
                    <tr>
                        <td>Discounts</td>
                        <td>{m['total_discounts']}</td>
                    </tr>
                    <tr>
                        <td>Promotions</td>
                        <td>{m['total_promotions']}</td>
                    </tr>
                    <tr>
                        <td>Queries</td>
                        <td>{m['total_queries']}</td>
                    </tr>
                </table>
            </div>
        """
        
        tier_class = {
            'strong': 'tier-strong',
            'healthy': 'tier-healthy',
            'emerging': 'tier-emerging'
        }.get(report['performance_tier'], '')
        
        tier_text = {
            'strong': '💪 Strong Performance (Excellent engagement)',
            'healthy': '✓ Healthy Performance (Good momentum)',
            'emerging': '🌱 Emerging Performance (Growing engagement)'
        }.get(report['performance_tier'], 'N/A')
        
        html += f"""
            <div class="section">
                <h4 style="margin-top: 0; color: #2d3748;">Program Health</h4>
                <div class="tier {tier_class}">
                    {tier_text}
                </div>
            </div>
        """
        
        if report.get('top_performers'):
            html += f"""
            <div class="section">
                <h4 style="margin-top: 0; color: #2d3748;">🏆 Top 5 Performers</h4>
                <table>
                    <tr>
                        <th>Pilot</th>
                        <th>Reorders</th>
                        <th>Revenue</th>
                    </tr>
            """
            for p in report['top_performers']:
                html += f"""
                    <tr>
                        <td><strong>{p['name']}</strong><br/><span style="font-size:11px;color:#718096">{p['store']}</span></td>
                        <td>{p['reorders']}</td>
                        <td>${p['revenue']}</td>
                    </tr>
                """
            html += """
                </table>
            </div>
            """
    
    html += """
            </div>
            <div class="footer">
                <p>View full dashboard at <strong>https://tryclariq.com/dashboard</strong></p>
                <p>© 2024 CLARIQ. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
