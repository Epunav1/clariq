from fastapi import APIRouter, HTTPException
from typing import Optional
from db.pilots_db import list_pilots, get_pilot
from db.actions_db import get_actions, count_actions
from db.revenue_calc import calculate_pilot_revenue
from datetime import datetime

router = APIRouter()


@router.get('/results')
async def get_pilot_results():
    """Get detailed pilot performance metrics with all action types."""
    try:
        pilots = list_pilots()
        
        # track action types for summary
        action_types = ['reorder', 'discount', 'promotion', 'query']
        type_counts = {t: 0 for t in action_types}
        
        # enrich each pilot with action counts and time metrics
        results = []
        for p in pilots:
            pilot_id = p['id']
            
            # count all action types for this pilot
            pilot_actions = {}
            for action_type in action_types:
                count = count_actions(action_type=action_type, pilot_id=pilot_id)
                pilot_actions[action_type] = count
                type_counts[action_type] += count
            
            reorder_count = pilot_actions.get('reorder', 0)
            
            # calc days active
            days_active = 0
            if p['contacted_at']:
                try:
                    contacted = datetime.fromisoformat(p['contacted_at'])
                    days_active = (datetime.utcnow() - contacted).days
                except:
                    days_active = 0
            
            # reorder velocity
            velocity = 0
            if days_active > 0:
                velocity = round(reorder_count / days_active, 2)
            
            # calculate real revenue from Snowflake order data
            revenue_data = calculate_pilot_revenue(pilot_id)
            real_revenue = revenue_data.get('total_revenue', 0)
            
            results.append({
                "id": pilot_id,
                "name": p['name'],
                "email": p['email'],
                "store_name": p['store_name'],
                "platform": p['platform'],
                "status": p['status'],
                "contacted_at": p['contacted_at'],
                "created_at": p['created_at'],
                "days_active": days_active,
                "reorder_count": reorder_count,
                "discount_count": pilot_actions.get('discount', 0),
                "promotion_count": pilot_actions.get('promotion', 0),
                "query_count": pilot_actions.get('query', 0),
                "total_actions": sum(pilot_actions.values()),
                "reorder_velocity": velocity,  # reorders per day
                "total_revenue": real_revenue,  # actual revenue from Snowflake orders
                "est_value": real_revenue if real_revenue > 0 else (reorder_count * 5),  # real if available, else estimate
                "revenue_data_quality": revenue_data.get('data_quality', 'estimated'),  # "real" or "estimated"
            })
        
        # aggregate stats
        total_pilots = len(results)
        contacted = sum(1 for r in results if r['status'] == 'contacted')
        total_actions = sum(r['total_actions'] for r in results)
        total_reorders = sum(r['reorder_count'] for r in results)
        avg_reorders = round(total_reorders / total_pilots, 2) if total_pilots > 0 else 0
        total_real_revenue = sum(r['total_revenue'] for r in results)
        total_est_value = sum(r['est_value'] for r in results)
        
        return {
            "pilots": results,
            "summary": {
                "total_pilots": total_pilots,
                "contacted": contacted,
                "pending": total_pilots - contacted,
                "total_actions": total_actions,
                "total_reorders": total_reorders,
                "total_discounts": type_counts['discount'],
                "total_promotions": type_counts['promotion'],
                "total_queries": type_counts['query'],
                "avg_reorders_per_pilot": avg_reorders,
                "total_real_revenue": round(total_real_revenue, 2),  # actual revenue from Snowflake
                "est_total_value": total_est_value,  # fallback estimates
                "data_quality": "real" if total_real_revenue > 0 else "estimated",  # indicates if revenue is real or estimated
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/velocity/{pilot_id}')
async def get_pilot_velocity(pilot_id: int):
    """Get action velocity data for a pilot over time (actions per day)."""
    try:
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        p = get_pilot(pilot_id)
        if not p:
            raise HTTPException(status_code=404, detail='Pilot not found')
        
        # Get all actions for this pilot
        actions = get_actions(pilot_id=pilot_id)
        
        # Group by date and action type
        daily_data = defaultdict(lambda: {'reorder': 0, 'discount': 0, 'promotion': 0, 'query': 0, 'total': 0})
        
        for action in actions:
            try:
                created_at = action.get('created_at')
                if created_at:
                    # Parse ISO format date
                    if isinstance(created_at, str):
                        date_str = created_at.split('T')[0]  # Extract YYYY-MM-DD
                    else:
                        date_str = created_at.strftime('%Y-%m-%d')
                    
                    action_type = action.get('action_type', 'query')
                    daily_data[date_str][action_type] += 1
                    daily_data[date_str]['total'] += 1
            except:
                continue
        
        # Sort by date
        sorted_dates = sorted(daily_data.keys())
        
        # Calculate cumulative and daily velocity
        timeline = []
        cumulative_reorders = 0
        
        for date in sorted_dates:
            daily = daily_data[date]
            cumulative_reorders += daily['reorder']
            
            # Calculate days since contact
            contacted_at = p.get('contacted_at')
            if contacted_at:
                try:
                    contact_date = datetime.fromisoformat(contacted_at).date()
                    current_date = datetime.fromisoformat(date).date()
                    days_since_contact = (current_date - contact_date).days + 1
                except:
                    days_since_contact = 0
            else:
                days_since_contact = 0
            
            timeline.append({
                'date': date,
                'reorders': daily['reorder'],
                'discounts': daily['discount'],
                'promotions': daily['promotion'],
                'queries': daily['query'],
                'total_actions': daily['total'],
                'cumulative_reorders': cumulative_reorders,
                'days_since_contact': days_since_contact,
                'velocity': round(cumulative_reorders / days_since_contact, 2) if days_since_contact > 0 else 0
            })
        
        return {
            "pilot": {
                "id": p['id'],
                "name": p['name'],
                "store_name": p['store_name'],
                "contacted_at": p['contacted_at']
            },
            "timeline": timeline,
            "summary": {
                "total_days": len(sorted_dates),
                "total_actions": sum(d['total'] for d in daily_data.values()),
                "total_reorders": sum(d['reorder'] for d in daily_data.values()),
                "avg_daily_reorders": round(sum(d['reorder'] for d in daily_data.values()) / len(sorted_dates), 2) if sorted_dates else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
