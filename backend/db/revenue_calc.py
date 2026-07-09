"""
Revenue calculation module for pilot program metrics.
Queries Snowflake for actual order data to compute real revenue values.
"""

from db.snowflake_client import run_query
from db.actions_db import get_actions
import logging

logger = logging.getLogger(__name__)


def get_store_ids_for_pilot(pilot_id: int) -> list:
    """
    Get all unique store IDs associated with a pilot from their logged actions.
    
    Args:
        pilot_id: The pilot applicant ID
        
    Returns:
        List of store_id strings, or empty list if no actions found
    """
    try:
        actions = get_actions(pilot_id=pilot_id)
        store_ids = list(set(a.get('store_id') for a in actions if a.get('store_id')))
        return [s for s in store_ids if s]  # filter out None/empty
    except Exception as e:
        logger.error(f"Error getting store IDs for pilot {pilot_id}: {e}")
        return []


def calculate_pilot_revenue(pilot_id: int, store_ids: list = None) -> dict:
    """
    Calculate actual revenue for a pilot based on orders in Snowflake.
    
    Queries RAW_ORDERS table for orders matching the pilot's store(s),
    sums the order totals, and returns revenue metrics.
    
    Args:
        pilot_id: The pilot applicant ID
        store_ids: Optional list of store IDs. If not provided, will fetch from actions.
        
    Returns:
        dict with keys:
            - total_revenue: Sum of all order totals (float)
            - order_count: Number of orders (int)
            - avg_order_value: Average per order (float)
            - currency: Currency code (str)
            - data_quality: "real" or "estimated" depending on Snowflake availability
    """
    if store_ids is None:
        store_ids = get_store_ids_for_pilot(pilot_id)
    
    # If no store_ids found, return zero with estimated flag
    if not store_ids:
        return {
            "total_revenue": 0,
            "order_count": 0,
            "avg_order_value": 0,
            "currency": "USD",
            "data_quality": "estimated"
        }
    
    try:
        # Build WHERE clause for store IDs
        store_id_list = "', '".join(store_ids)
        
        # Query Snowflake for order totals
        sql = f"""
        SELECT 
            COUNT(*) as order_count,
            SUM(TOTAL_PRICE) as total_revenue,
            AVG(TOTAL_PRICE) as avg_order_value,
            'USD' as currency
        FROM RAW_ORDERS
        WHERE STORE_ID IN ('{store_id_list}')
        """
        
        result = run_query(sql)
        
        if 'error' in result:
            logger.warning(f"Snowflake query error for pilot {pilot_id}: {result['error']}")
            return {
                "total_revenue": 0,
                "order_count": 0,
                "avg_order_value": 0,
                "currency": "USD",
                "data_quality": "estimated"
            }
        
        # Extract results
        if result.get('rows') and len(result['rows']) > 0:
            row = result['rows'][0]
            order_count = row[0] or 0
            total_revenue = row[1] or 0
            avg_order_value = row[2] or 0
            
            # Convert to float if needed
            try:
                total_revenue = float(total_revenue) if total_revenue else 0
                avg_order_value = float(avg_order_value) if avg_order_value else 0
            except (ValueError, TypeError):
                total_revenue = 0
                avg_order_value = 0
            
            return {
                "total_revenue": round(total_revenue, 2),
                "order_count": int(order_count) if order_count else 0,
                "avg_order_value": round(avg_order_value, 2) if avg_order_value else 0,
                "currency": "USD",
                "data_quality": "real"
            }
        else:
            return {
                "total_revenue": 0,
                "order_count": 0,
                "avg_order_value": 0,
                "currency": "USD",
                "data_quality": "estimated"
            }
            
    except Exception as e:
        logger.error(f"Error calculating revenue for pilot {pilot_id}: {e}")
        return {
            "total_revenue": 0,
            "order_count": 0,
            "avg_order_value": 0,
            "currency": "USD",
            "data_quality": "estimated"
        }


def get_reorder_revenue(pilot_id: int) -> float:
    """
    Get total revenue specifically from reorder actions.
    
    For each reorder action logged, attempts to find corresponding order(s)
    in the timeframe around the action and sums their values.
    
    Args:
        pilot_id: The pilot applicant ID
        
    Returns:
        float: Total revenue attributed to reorders, or 0 if unable to calculate
    """
    try:
        # Get all reorder actions for this pilot
        reorder_actions = get_actions(action_type='reorder', pilot_id=pilot_id)
        
        if not reorder_actions:
            return 0
        
        store_ids = list(set(a.get('store_id') for a in reorder_actions if a.get('store_id')))
        
        if not store_ids:
            return 0
        
        # Get revenue for stores associated with reorders
        revenue_data = calculate_pilot_revenue(pilot_id, store_ids)
        
        # Scale by reorder count (this is approximate - assumes reorders drove ~proportional revenue)
        return revenue_data.get('total_revenue', 0)
        
    except Exception as e:
        logger.error(f"Error calculating reorder revenue for pilot {pilot_id}: {e}")
        return 0
