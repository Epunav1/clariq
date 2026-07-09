"""
Advanced ROI calculations for pilot program.
Computes profit margins, cost per reorder, payback period, and ROI metrics.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict
from db.pilots_db import get_pilot
from db.revenue_calc import calculate_pilot_revenue
from db.actions_db import count_actions


def get_roi_parameters(pilot_id: int) -> Dict:
    """Get or create ROI calculation parameters for a pilot."""
    try:
        conn = sqlite3.connect('backend/db/roi_params.sqlite')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS roi_params (
            pilot_id INTEGER PRIMARY KEY,
            cost_per_pilot REAL DEFAULT 500,
            pilot_product_cost REAL DEFAULT 50,
            discount_cost_pct REAL DEFAULT 0.15,
            promotion_cost_pct REAL DEFAULT 0.10,
            query_resolution_value REAL DEFAULT 20,
            created_at TEXT,
            updated_at TEXT
        )''')
        
        # Get or create parameters
        c.execute('SELECT * FROM roi_params WHERE pilot_id = ?', (pilot_id,))
        row = c.fetchone()
        
        if row:
            return {
                'cost_per_pilot': row[1],
                'pilot_product_cost': row[2],
                'discount_cost_pct': row[3],
                'promotion_cost_pct': row[4],
                'query_resolution_value': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
        else:
            # Insert defaults
            now = datetime.utcnow().isoformat()
            c.execute('''INSERT INTO roi_params 
                (pilot_id, cost_per_pilot, pilot_product_cost, discount_cost_pct, 
                 promotion_cost_pct, query_resolution_value, created_at, updated_at)
                VALUES (?, 500, 50, 0.15, 0.10, 20, ?, ?)''',
                (pilot_id, now, now))
            conn.commit()
            
            return {
                'cost_per_pilot': 500,
                'pilot_product_cost': 50,
                'discount_cost_pct': 0.15,
                'promotion_cost_pct': 0.10,
                'query_resolution_value': 20,
                'created_at': now,
                'updated_at': now
            }
    finally:
        conn.close()


def update_roi_parameters(pilot_id: int, params: Dict) -> Dict:
    """Update ROI calculation parameters."""
    try:
        conn = sqlite3.connect('backend/db/roi_params.sqlite')
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        c.execute('''UPDATE roi_params 
            SET cost_per_pilot=?, pilot_product_cost=?, discount_cost_pct=?,
                promotion_cost_pct=?, query_resolution_value=?, updated_at=?
            WHERE pilot_id=?''',
            (params.get('cost_per_pilot', 500),
             params.get('pilot_product_cost', 50),
             params.get('discount_cost_pct', 0.15),
             params.get('promotion_cost_pct', 0.10),
             params.get('query_resolution_value', 20),
             now,
             pilot_id))
        conn.commit()
        
        return get_roi_parameters(pilot_id)
    finally:
        conn.close()


def calculate_pilot_roi(pilot_id: int) -> Dict:
    """
    Calculate comprehensive ROI metrics for a pilot.
    Returns dict with:
    - total_investment: total cost to acquire and support pilot
    - total_revenue: gross revenue from pilot
    - gross_profit: revenue - cost of goods
    - net_profit: gross profit - all costs
    - roi_percent: (net_profit / total_investment) * 100
    - payback_period_days: days to recover initial investment
    - cost_per_reorder: average cost per reorder achieved
    - break_even_reorders: reorders needed to cover costs
    """
    
    pilot = get_pilot(pilot_id)
    if not pilot:
        return {'error': 'Pilot not found'}
    
    # Get revenue data
    revenue_data = calculate_pilot_revenue(pilot_id)
    total_revenue = revenue_data.get('total_revenue', 0)
    order_count = revenue_data.get('order_count', 0)
    
    # Get action counts
    reorder_count = count_actions('reorder', pilot_id)
    discount_count = count_actions('discount', pilot_id)
    promotion_count = count_actions('promotion', pilot_id)
    query_count = count_actions('query', pilot_id)
    
    # Get ROI parameters
    params = get_roi_parameters(pilot_id)
    
    # Calculate costs
    cost_per_pilot = params['cost_per_pilot']  # Acquisition + onboarding
    pilot_product_cost = params['pilot_product_cost']  # Cost of free/discounted pilot product
    discount_cost = order_count * total_revenue * params['discount_cost_pct']  # Margin lost to discounts
    promotion_cost = promotion_count * 25  # Avg cost per promotion campaign
    query_resolution_value = query_count * params['query_resolution_value']  # Value of resolving support queries
    
    total_investment = cost_per_pilot + pilot_product_cost
    total_costs = total_investment + discount_cost + promotion_cost
    
    # Calculate profit
    estimated_cogs = total_revenue * 0.45  # Assume 45% COGS (typical for e-commerce)
    gross_profit = total_revenue - estimated_cogs
    net_profit = gross_profit - total_costs
    
    # Calculate ROI
    roi_percent = (net_profit / total_investment * 100) if total_investment > 0 else 0
    
    # Calculate cost per reorder
    cost_per_reorder = total_investment / reorder_count if reorder_count > 0 else 0
    
    # Calculate break-even
    break_even_revenue = total_investment + pilot_product_cost + discount_cost
    break_even_reorders = (break_even_revenue / (total_revenue / order_count)) if order_count > 0 else 0
    
    # Calculate payback period (assuming linear daily revenue)
    days_active = (datetime.fromisoformat(pilot['completed_at'] or datetime.utcnow().isoformat()) - 
                   datetime.fromisoformat(pilot['contacted_at'])).days
    daily_revenue = total_revenue / days_active if days_active > 0 else 0
    daily_profit = (total_revenue - estimated_cogs) / days_active if days_active > 0 else 0
    payback_period = total_investment / daily_profit if daily_profit > 0 else float('inf')
    
    return {
        'pilot_id': pilot_id,
        'pilot_name': pilot['name'],
        'store_name': pilot['store_name'],
        'status': pilot['status'],
        'days_active': days_active,
        'total_revenue': round(total_revenue, 2),
        'revenue_metrics': {
            'order_count': order_count,
            'avg_order_value': round(total_revenue / order_count, 2) if order_count > 0 else 0,
            'estimated_cogs': round(estimated_cogs, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_margin_pct': round(gross_profit / total_revenue * 100, 1) if total_revenue > 0 else 0,
        },
        'investment_metrics': {
            'cost_per_pilot': cost_per_pilot,
            'pilot_product_cost': pilot_product_cost,
            'discount_cost': round(discount_cost, 2),
            'promotion_cost': round(promotion_cost, 2),
            'total_investment': round(total_investment, 2),
            'total_costs': round(total_costs, 2),
        },
        'profit_metrics': {
            'gross_profit': round(gross_profit, 2),
            'net_profit': round(net_profit, 2),
            'profit_margin_pct': round(net_profit / total_revenue * 100, 1) if total_revenue > 0 else 0,
        },
        'roi_metrics': {
            'roi_percent': round(roi_percent, 1),
            'roi_status': 'Highly profitable' if roi_percent > 100 else 'Profitable' if roi_percent > 0 else 'Break-even' if roi_percent > -20 else 'Loss',
            'payback_period_days': round(payback_period, 1) if payback_period != float('inf') else None,
            'cost_per_reorder': round(cost_per_reorder, 2),
            'break_even_reorders': round(break_even_reorders, 1),
            'reorders_needed_for_2x_roi': round((total_investment * 3) / (total_revenue / reorder_count), 1) if reorder_count > 0 and total_revenue > 0 else 0,
        },
        'action_metrics': {
            'reorder_count': reorder_count,
            'discount_count': discount_count,
            'promotion_count': promotion_count,
            'query_count': query_count,
        },
        'calculated_at': datetime.utcnow().isoformat(),
    }


def calculate_program_roi(pilot_ids: list = None) -> Dict:
    """Calculate aggregate ROI across all or specified pilots."""
    from db.pilots_db import list_pilots
    
    if not pilot_ids:
        # Get all completed pilots
        pilots = list_pilots()
        pilot_ids = [p['id'] for p in pilots if p['status'] == 'completed']
    
    roi_results = []
    for pid in pilot_ids:
        roi_results.append(calculate_pilot_roi(pid))
    
    if not roi_results:
        return {'error': 'No pilots found'}
    
    # Aggregate metrics
    total_investment = sum(r.get('investment_metrics', {}).get('total_investment', 0) for r in roi_results)
    total_revenue = sum(r.get('total_revenue', 0) for r in roi_results)
    total_net_profit = sum(r.get('profit_metrics', {}).get('net_profit', 0) for r in roi_results)
    avg_roi = sum(r.get('roi_metrics', {}).get('roi_percent', 0) for r in roi_results) / len(roi_results) if roi_results else 0
    
    profitable_pilots = sum(1 for r in roi_results if r.get('profit_metrics', {}).get('net_profit', 0) > 0)
    
    return {
        'program_summary': {
            'total_pilots_analyzed': len(roi_results),
            'profitable_pilots': profitable_pilots,
            'profitability_rate': round(profitable_pilots / len(roi_results) * 100, 1) if roi_results else 0,
        },
        'aggregate_metrics': {
            'total_investment': round(total_investment, 2),
            'total_revenue': round(total_revenue, 2),
            'total_net_profit': round(total_net_profit, 2),
            'overall_roi_percent': round(total_net_profit / total_investment * 100, 1) if total_investment > 0 else 0,
            'avg_roi_per_pilot': round(avg_roi, 1),
            'avg_revenue_per_pilot': round(total_revenue / len(roi_results), 2) if roi_results else 0,
        },
        'pilot_results': roi_results,
        'calculated_at': datetime.utcnow().isoformat(),
    }
