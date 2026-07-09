"""
Shopify data sync module with multi-store support.
Wraps and extends the existing shopify_sync.py logic.
"""

import requests
import snowflake.connector
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ShopifySync:
    """Syncs Shopify store data to Snowflake."""
    
    def __init__(self, shop_domain: str, access_token: str):
        """
        Initialize Shopify sync for a specific store.
        
        Args:
            shop_domain: Shopify domain (e.g., 'mystore.myshopify.com')
            access_token: Shopify API access token
        """
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = "2024-01"
        self.headers = {"X-Shopify-Access-Token": access_token}
        self.base_url = f"https://{shop_domain}/admin/api/{self.api_version}"
        self.records_synced = 0
        
    def get_snowflake_connection(self):
        """Get Snowflake connection."""
        return snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
    
    def sync_orders(self) -> Tuple[int, str]:
        """
        Sync orders from Shopify to Snowflake RAW_ORDERS table.
        
        Returns:
            Tuple of (records_synced, status_message)
        """
        try:
            url = f"{self.base_url}/orders.json?limit=250&status=any"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            orders = response.json().get("orders", [])
            if not orders:
                return 0, f"No orders found for {self.shop_domain}"
            
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            
            inserted = 0
            for order in orders:
                try:
                    cursor.execute("""
                        MERGE INTO RAW_ORDERS t USING (
                            SELECT %s as order_id
                        ) s ON t.order_id = s.order_id
                        WHEN NOT MATCHED THEN
                            INSERT (order_id, created_at, customer_id, email, total_price,
                                   subtotal_price, total_tax, financial_status, fulfillment_status, 
                                   currency, store_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        WHEN MATCHED THEN UPDATE SET
                            financial_status = %s, fulfillment_status = %s
                    """, (
                        str(order.get("id")),
                        str(order.get("id")), order.get("created_at"),
                        str(order.get("customer", {}).get("id", "")), order.get("email", ""),
                        float(order.get("total_price", 0)), float(order.get("subtotal_price", 0)),
                        float(order.get("total_tax", 0)), order.get("financial_status", ""),
                        order.get("fulfillment_status", ""), order.get("currency", "USD"),
                        self.shop_domain,
                        order.get("financial_status", ""), order.get("fulfillment_status", "")
                    ))
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Error inserting order {order.get('id')}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.records_synced += inserted
            return inserted, f"Synced {inserted} orders"
        
        except Exception as e:
            error_msg = f"Order sync failed: {str(e)}"
            logger.error(error_msg)
            return 0, error_msg
    
    def sync_customers(self) -> Tuple[int, str]:
        """
        Sync customers from Shopify to Snowflake RAW_CUSTOMERS table.
        
        Returns:
            Tuple of (records_synced, status_message)
        """
        try:
            url = f"{self.base_url}/customers.json?limit=250"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            customers = response.json().get("customers", [])
            if not customers:
                return 0, f"No customers found for {self.shop_domain}"
            
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            
            inserted = 0
            for customer in customers:
                try:
                    default_addr = customer.get("default_address", {})
                    cursor.execute("""
                        MERGE INTO RAW_CUSTOMERS t USING (
                            SELECT %s as customer_id
                        ) s ON t.customer_id = s.customer_id
                        WHEN NOT MATCHED THEN
                            INSERT (customer_id, created_at, email, first_name, last_name,
                                   orders_count, total_spent, city, country, store_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        WHEN MATCHED THEN UPDATE SET
                            orders_count = %s, total_spent = %s
                    """, (
                        str(customer.get("id")),
                        str(customer.get("id")), customer.get("created_at"), customer.get("email", ""),
                        customer.get("first_name", ""), customer.get("last_name", ""),
                        int(customer.get("orders_count", 0)), float(customer.get("total_spent", 0)),
                        default_addr.get("city", ""), default_addr.get("country", ""),
                        self.shop_domain,
                        int(customer.get("orders_count", 0)), float(customer.get("total_spent", 0))
                    ))
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Error inserting customer {customer.get('id')}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.records_synced += inserted
            return inserted, f"Synced {inserted} customers"
        
        except Exception as e:
            error_msg = f"Customer sync failed: {str(e)}"
            logger.error(error_msg)
            return 0, error_msg
    
    def sync_products(self) -> Tuple[int, str]:
        """
        Sync products from Shopify to Snowflake RAW_PRODUCTS table.
        
        Returns:
            Tuple of (records_synced, status_message)
        """
        try:
            url = f"{self.base_url}/products.json?limit=250"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            products = response.json().get("products", [])
            if not products:
                return 0, f"No products found for {self.shop_domain}"
            
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            
            inserted = 0
            for product in products:
                try:
                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    cursor.execute("""
                        MERGE INTO RAW_PRODUCTS t USING (
                            SELECT %s as product_id
                        ) s ON t.product_id = s.product_id
                        WHEN NOT MATCHED THEN
                            INSERT (product_id, created_at, title, product_type, vendor, 
                                   status, price, inventory_quantity, store_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        WHEN MATCHED THEN UPDATE SET
                            status = %s, price = %s, inventory_quantity = %s
                    """, (
                        str(product.get("id")),
                        str(product.get("id")), product.get("created_at"), product.get("title", ""),
                        product.get("product_type", ""), product.get("vendor", ""),
                        product.get("status", ""), float(variant.get("price", 0)),
                        int(variant.get("inventory_quantity", 0)), self.shop_domain,
                        product.get("status", ""), float(variant.get("price", 0)),
                        int(variant.get("inventory_quantity", 0))
                    ))
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Error inserting product {product.get('id')}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.records_synced += inserted
            return inserted, f"Synced {inserted} products"
        
        except Exception as e:
            error_msg = f"Product sync failed: {str(e)}"
            logger.error(error_msg)
            return 0, error_msg
    
    def sync_all(self) -> Tuple[int, str]:
        """
        Sync all data (orders, customers, products) for this store.
        
        Returns:
            Tuple of (total_records_synced, combined_status)
        """
        self.records_synced = 0
        statuses = []
        
        # Sync each data type
        order_count, order_status = self.sync_orders()
        statuses.append(order_status)
        
        customer_count, customer_status = self.sync_customers()
        statuses.append(customer_status)
        
        product_count, product_status = self.sync_products()
        statuses.append(product_status)
        
        combined = " | ".join(statuses)
        return self.records_synced, combined


def get_connected_shopify_stores() -> List[Dict]:
    """
    Get list of connected Shopify stores from database.
    Queries connections_db to find Shopify stores with API tokens.
    
    Returns:
        List of dicts with keys: store_id, shop_domain, access_token
    """
    try:
        from db.connections_db import get_connections
        
        connections = get_connections(platform='shopify')
        stores = []
        
        for conn in connections:
            # Map database fields to Shopify sync fields
            shop_domain = conn.get('store_url') or conn.get('store_name', '')
            access_token = conn.get('api_key')
            
            # Only add if we have required fields
            if shop_domain and access_token:
                # Ensure shop_domain looks like mystore.myshopify.com
                if not shop_domain.endswith('.myshopify.com'):
                    if not shop_domain.endswith('.com'):
                        shop_domain = f"{shop_domain}.myshopify.com"
                
                stores.append({
                    'store_id': conn.get('id') or conn.get('store_name', ''),
                    'shop_domain': shop_domain,
                    'access_token': access_token,
                    'name': conn.get('store_name', shop_domain)
                })
        
        return stores
    
    except Exception as e:
        logger.error(f"Error fetching connected stores: {e}")
        # Fallback: try to use environment variable for demo store
        if os.getenv("SHOPIFY_TOKEN"):
            return [{
                'store_id': 'demo',
                'shop_domain': os.getenv("SHOPIFY_SHOP", "demo.myshopify.com"),
                'access_token': os.getenv("SHOPIFY_TOKEN"),
                'name': 'Demo Store'
            }]
        return []


def sync_all_shopify_stores() -> Dict:
    """
    Sync all connected Shopify stores.
    
    Returns:
        Dict with keys: total_records, stores_synced, status_details
    """
    stores = get_connected_shopify_stores()
    
    if not stores:
        logger.warning("No Shopify stores configured")
        return {
            'total_records': 0,
            'stores_synced': 0,
            'status_details': 'No connected Shopify stores found'
        }
    
    total_records = 0
    store_details = []
    
    for store in stores:
        try:
            logger.info(f"Starting sync for store: {store['name']} ({store['shop_domain']})")
            
            syncer = ShopifySync(store['shop_domain'], store['access_token'])
            records, status = syncer.sync_all()
            
            total_records += records
            store_details.append(f"{store['name']}: {status}")
            logger.info(f"Completed sync for {store['name']}: {records} records")
        
        except Exception as e:
            error_msg = f"{store['name']}: Failed - {str(e)}"
            store_details.append(error_msg)
            logger.error(error_msg)
    
    return {
        'total_records': total_records,
        'stores_synced': len(stores),
        'status_details': ' | '.join(store_details)
    }
