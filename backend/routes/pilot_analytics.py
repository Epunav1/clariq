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


@router.get('/cohorts')
async def get_cohort_analysis():
    """Analyze pilot performance by cohort (grouped by signup week)."""
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        pilots = list_pilots()
        
        # Group pilots by signup week
        cohorts = defaultdict(list)
        
        for p in pilots:
            created_at_str = p.get('created_at')
            if created_at_str:
                try:
                    created_date = datetime.fromisoformat(created_at_str)
                    # Get the Monday of the week
                    week_start = created_date - timedelta(days=created_date.weekday())
                    cohort_key = week_start.strftime('%Y-W%U')  # Format: 2024-W01
                    cohort_label = week_start.strftime('%b %d, %Y')  # Format: Jan 01, 2024
                    cohorts[cohort_key].append({
                        'key': cohort_key,
                        'label': cohort_label,
                        'pilot': p
                    })
                except:
                    continue
        
        # Analyze each cohort
        cohort_results = []
        
        for cohort_key in sorted(cohorts.keys()):
            cohort_pilots = [c['pilot'] for c in cohorts[cohort_key]]
            cohort_label = cohorts[cohort_key][0]['label'] if cohorts[cohort_key] else cohort_key
            
            # Calculate metrics for this cohort
            total_pilots = len(cohort_pilots)
            contacted = sum(1 for p in cohort_pilots if p['status'] == 'contacted')
            completed = sum(1 for p in cohort_pilots if p['status'] == 'completed')
            
            total_reorders = 0
            total_discounts = 0
            total_promotions = 0
            total_queries = 0
            total_revenue = 0
            
            for p in cohort_pilots:
                pilot_id = p['id']
                total_reorders += count_actions(action_type='reorder', pilot_id=pilot_id)
                total_discounts += count_actions(action_type='discount', pilot_id=pilot_id)
                total_promotions += count_actions(action_type='promotion', pilot_id=pilot_id)
                total_queries += count_actions(action_type='query', pilot_id=pilot_id)
                
                revenue_data = calculate_pilot_revenue(pilot_id)
                total_revenue += revenue_data.get('total_revenue', 0)
            
            # Calculate rates
            engagement_rate = round((contacted / total_pilots * 100), 1) if total_pilots > 0 else 0
            completion_rate = round((completed / total_pilots * 100), 1) if total_pilots > 0 else 0
            avg_reorders = round(total_reorders / total_pilots, 2) if total_pilots > 0 else 0
            avg_revenue = round(total_revenue / total_pilots, 2) if total_pilots > 0 else 0
            
            # Assign cohort health tier
            if engagement_rate >= 70 and avg_reorders >= 1:
                health = 'strong'
                health_label = '💪 Strong'
            elif engagement_rate >= 50 and avg_reorders >= 0.5:
                health = 'healthy'
                health_label = '✓ Healthy'
            elif engagement_rate >= 30:
                health = 'emerging'
                health_label = '🌱 Emerging'
            else:
                health = 'early'
                health_label = '⏳ Early'
            
            cohort_results.append({
                'cohort': cohort_key,
                'label': cohort_label,
                'size': total_pilots,
                'contacted': contacted,
                'completed': completed,
                'engagement_rate': engagement_rate,
                'completion_rate': completion_rate,
                'avg_reorders': avg_reorders,
                'total_reorders': total_reorders,
                'total_discounts': total_discounts,
                'total_promotions': total_promotions,
                'total_queries': total_queries,
                'total_revenue': round(total_revenue, 2),
                'avg_revenue': avg_revenue,
                'health': health,
                'health_label': health_label,
                'pilots': [
                    {
                        'id': p['id'],
                        'name': p['name'],
                        'store_name': p['store_name'],
                        'status': p['status'],
                        'reorders': count_actions(action_type='reorder', pilot_id=p['id'])
                    }
                    for p in cohort_pilots
                ]
            })
        
        # Calculate aggregate stats
        all_cohorts = cohort_results
        avg_engagement = round(sum(c['engagement_rate'] for c in all_cohorts) / len(all_cohorts), 1) if all_cohorts else 0
        avg_completion = round(sum(c['completion_rate'] for c in all_cohorts) / len(all_cohorts), 1) if all_cohorts else 0
        best_cohort = max(all_cohorts, key=lambda c: c['engagement_rate']) if all_cohorts else None
        
        return {
            "cohorts": all_cohorts,
            "summary": {
                "total_cohorts": len(all_cohorts),
                "avg_engagement_rate": avg_engagement,
                "avg_completion_rate": avg_completion,
                "best_performing_cohort": best_cohort['label'] if best_cohort else None,
                "strong_cohorts": len([c for c in all_cohorts if c['health'] == 'strong']),
                "healthy_cohorts": len([c for c in all_cohorts if c['health'] == 'healthy'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

