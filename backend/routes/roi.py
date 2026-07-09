"""
ROI Analytics API endpoints for pilot program.
Provides detailed profitability metrics and financial analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from db.roi_calc import calculate_pilot_roi, calculate_program_roi, get_roi_parameters, update_roi_parameters

router = APIRouter()


class ROIParameters(BaseModel):
    cost_per_pilot: Optional[float] = 500
    pilot_product_cost: Optional[float] = 50
    discount_cost_pct: Optional[float] = 0.15
    promotion_cost_pct: Optional[float] = 0.10
    query_resolution_value: Optional[float] = 20


@router.get('/pilot/{pilot_id}')
async def get_pilot_roi(pilot_id: int):
    """Get detailed ROI analysis for a specific pilot."""
    try:
        roi = calculate_pilot_roi(pilot_id)
        if 'error' in roi:
            raise HTTPException(status_code=404, detail=roi['error'])
        return roi
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/program')
async def get_program_roi():
    """Get aggregate ROI analysis for entire pilot program."""
    try:
        roi = calculate_program_roi()
        if 'error' in roi:
            raise HTTPException(status_code=400, detail=roi['error'])
        return roi
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/comparison')
async def get_roi_comparison():
    """Get ROI comparison across all pilots ranked by profitability."""
    try:
        program_roi = calculate_program_roi()
        
        # Sort pilots by net profit descending
        pilots = program_roi.get('pilot_results', [])
        sorted_pilots = sorted(
            pilots,
            key=lambda p: p.get('profit_metrics', {}).get('net_profit', 0),
            reverse=True
        )
        
        # Add ranking
        for idx, pilot in enumerate(sorted_pilots, 1):
            pilot['profit_rank'] = idx
            roi_pct = pilot.get('roi_metrics', {}).get('roi_percent', 0)
            if roi_pct > 100:
                pilot['profit_tier'] = 'Exceptional'
            elif roi_pct > 50:
                pilot['profit_tier'] = 'Strong'
            elif roi_pct > 0:
                pilot['profit_tier'] = 'Positive'
            else:
                pilot['profit_tier'] = 'Break-even'
        
        return {
            'program_summary': program_roi.get('program_summary'),
            'aggregate_metrics': program_roi.get('aggregate_metrics'),
            'pilots_ranked': sorted_pilots,
            'tier_distribution': {
                'exceptional': sum(1 for p in sorted_pilots if p.get('profit_tier') == 'Exceptional'),
                'strong': sum(1 for p in sorted_pilots if p.get('profit_tier') == 'Strong'),
                'positive': sum(1 for p in sorted_pilots if p.get('profit_tier') == 'Positive'),
                'breakeven': sum(1 for p in sorted_pilots if p.get('profit_tier') == 'Break-even'),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/parameters/{pilot_id}')
async def get_pilot_roi_parameters(pilot_id: int):
    """Get ROI calculation parameters for a pilot."""
    try:
        params = get_roi_parameters(pilot_id)
        return {'pilot_id': pilot_id, 'parameters': params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/parameters/{pilot_id}')
async def update_pilot_roi_parameters(pilot_id: int, params: ROIParameters):
    """Update ROI calculation parameters for a pilot."""
    try:
        updated = update_roi_parameters(pilot_id, params.dict(exclude_none=True))
        return {'pilot_id': pilot_id, 'parameters': updated, 'message': 'Parameters updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/forecast/{pilot_id}')
async def get_roi_forecast(pilot_id: int, additional_reorders: int = 5):
    """Forecast ROI if pilot achieves additional reorders."""
    try:
        roi = calculate_pilot_roi(pilot_id)
        if 'error' in roi:
            raise HTTPException(status_code=404, detail=roi['error'])
        
        # Calculate forecast
        current_roi_pct = roi['roi_metrics']['roi_percent']
        avg_order_value = roi['revenue_metrics']['avg_order_value']
        estimated_cogs_pct = 0.45
        current_profit = roi['profit_metrics']['net_profit']
        investment = roi['investment_metrics']['total_investment']
        
        # Additional profit from new reorders
        additional_revenue = additional_reorders * avg_order_value
        additional_profit = additional_revenue * (1 - estimated_cogs_pct)
        
        forecasted_profit = current_profit + additional_profit
        forecasted_roi = (forecasted_profit / investment * 100) if investment > 0 else 0
        
        return {
            'pilot_id': pilot_id,
            'current_roi_percent': round(current_roi_pct, 1),
            'additional_reorders': additional_reorders,
            'additional_revenue': round(additional_revenue, 2),
            'additional_profit': round(additional_profit, 2),
            'forecasted_total_profit': round(forecasted_profit, 2),
            'forecasted_roi_percent': round(forecasted_roi, 1),
            'roi_improvement': round(forecasted_roi - current_roi_pct, 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/breakeven/{pilot_id}')
async def get_breakeven_analysis(pilot_id: int):
    """Analyze breakeven point and profit threshold."""
    try:
        roi = calculate_pilot_roi(pilot_id)
        if 'error' in roi:
            raise HTTPException(status_code=404, detail=roi['error'])
        
        investment = roi['investment_metrics']['total_investment']
        avg_order_value = roi['revenue_metrics']['avg_order_value']
        current_reorders = roi['action_metrics']['reorder_count']
        current_revenue = roi['total_revenue']
        
        # Calculate breakeven metrics
        breakeven_revenue = investment * 1.5  # Need 50% more than investment for profitability
        breakeven_orders = breakeven_revenue / avg_order_value if avg_order_value > 0 else 0
        
        progress_to_breakeven = (current_reorders / breakeven_orders * 100) if breakeven_orders > 0 else 0
        orders_needed = max(0, breakeven_orders - current_reorders)
        
        # Days to breakeven estimate
        days_active = roi['days_active']
        daily_reorders = current_reorders / days_active if days_active > 0 else 0
        days_to_breakeven = orders_needed / daily_reorders if daily_reorders > 0 else 0
        
        return {
            'pilot_id': pilot_id,
            'investment': round(investment, 2),
            'profitability_threshold_revenue': round(breakeven_revenue, 2),
            'profitability_threshold_orders': round(breakeven_orders, 1),
            'current_reorders': current_reorders,
            'current_revenue': round(current_revenue, 2),
            'progress_to_profitability_pct': round(min(progress_to_breakeven, 100), 1),
            'orders_to_profitability': round(max(0, orders_needed), 1),
            'estimated_days_to_profitability': round(max(0, days_to_breakeven), 1) if days_to_breakeven != float('inf') else None,
            'is_profitable': current_revenue >= breakeven_revenue,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
