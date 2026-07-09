from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from db.snowflake_client import run_query

router = APIRouter()


class ReorderRequest(BaseModel):
    store: str = "default"
    days_window: int = 30
    threshold_days: int = 14
    min_sales: int = 3


@router.post("/reorder")
async def recommend_reorder(req: ReorderRequest):
    """Recommend products to reorder based on recent sales velocity and current inventory.

    Returns a list of candidate products with estimated days-to-stockout and a simple recommendation.
    """
    try:
        # SQL: total sold per product in last `days_window` days and current inventory
        sql = f"""
        SELECT
            p.product_id,
            p.title,
            p.inventory_quantity,
            COALESCE(s.total_sold, 0) AS total_sold,
            CASE WHEN {req.days_window} = 0 THEN 0
                 ELSE COALESCE(s.total_sold, 0) / {req.days_window}
            END AS avg_daily_sales
        FROM CLARIQ_DB.SHOPIFY_RAW.RAW_PRODUCTS p
        LEFT JOIN (
            SELECT oli.product_id, SUM(oli.quantity) AS total_sold
            FROM CLARIQ_DB.SHOPIFY_RAW.RAW_ORDER_LINE_ITEMS oli
            JOIN CLARIQ_DB.SHOPIFY_RAW.RAW_ORDERS o ON oli.order_id = o.order_id
            WHERE o.created_at >= DATEADD(day, -{req.days_window}, CURRENT_DATE())
            GROUP BY oli.product_id
        ) s ON s.product_id = p.product_id
        WHERE p.inventory_quantity IS NOT NULL
        ORDER BY CASE WHEN (COALESCE(s.total_sold,0)/{req.days_window}) = 0 THEN NULL
                      ELSE (p.inventory_quantity / (COALESCE(s.total_sold,0)/{req.days_window}))
                 END ASC NULLS LAST
        LIMIT 500
        """

        result = run_query(sql)

        if result.get("error"):
            raise Exception(result.get("error"))

        rows = result.get("rows", [])
        cols = result.get("columns", [])

        # columns expected: PRODUCT_ID, TITLE, INVENTORY_QUANTITY, TOTAL_SOLD, AVG_DAILY_SALES
        recommendations: List[Dict[str, Any]] = []
        for r in rows:
            # map by index defensively
            def g(i):
                try:
                    return r[i]
                except Exception:
                    return None

            product_id = g(0)
            title = g(1)
            inventory = g(2) or 0
            total_sold = g(3) or 0
            avg_daily = g(4) or 0

            # avoid divide by zero
            days_to_stockout = None
            if avg_daily and avg_daily > 0:
                try:
                    days_to_stockout = float(inventory) / float(avg_daily)
                except Exception:
                    days_to_stockout = None

            rec = {
                "product_id": product_id,
                "title": title,
                "inventory": inventory,
                "total_sold": total_sold,
                "avg_daily_sales": avg_daily,
                "days_to_stockout": days_to_stockout,
                "recommend": False,
                "reason": "",
            }

            # simple recommendation rules
            if (days_to_stockout is not None and days_to_stockout <= req.threshold_days) or (
                avg_daily > 0 and inventory <= max(5, avg_daily * 7)
            ):
                rec["recommend"] = True
                rec["reason"] = (
                    f"Low stock: est {days_to_stockout:.1f} days to stockout" if days_to_stockout is not None
                    else "Low stock"
                )

            # filter low-activity SKUs if requested
            if total_sold >= req.min_sales or rec["recommend"]:
                recommendations.append(rec)

        return {"store": req.store, "recommendations": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
