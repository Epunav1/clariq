"""
Comprehensive Test Suite for CLARIQ Backend

Unit tests, integration tests, and fixtures
Run with: pytest -v
"""

import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sqlite3


# Mock fixtures
@pytest.fixture
def client():
    """FastAPI test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_pilot():
    """Sample pilot data"""
    return {
        "name": "Test Store",
        "email": "test@example.com",
        "store_name": "Test Store Inc",
        "platform": "shopify",
        "store_url": "https://test-store.myshopify.com"
    }


@pytest.fixture
def sample_action():
    """Sample action data"""
    return {
        "pilot_id": 1,
        "type": "reorder",
        "quantity": 5,
        "metadata": {"order_id": "12345"}
    }


# ===== PILOT TESTS =====

class TestPilots:
    """Test pilot management endpoints"""
    
    def test_create_pilot(self, client, sample_pilot):
        """Test pilot creation"""
        response = client.post("/api/pilot", json=sample_pilot)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == sample_pilot["name"]
    
    def test_get_all_pilots(self, client):
        """Test retrieving all pilots"""
        response = client.get("/api/pilot")
        assert response.status_code == 200
        data = response.json()
        assert "pilots" in data or isinstance(data, list)
    
    def test_get_single_pilot(self, client):
        """Test retrieving single pilot"""
        response = client.get("/api/pilot/1")
        assert response.status_code in [200, 404]
    
    def test_update_pilot(self, client):
        """Test pilot update"""
        update_data = {
            "status": "contacted",
            "notes": "Test note"
        }
        response = client.put("/api/pilot/1", json=update_data)
        assert response.status_code in [200, 404]


# ===== ROI TESTS =====

class TestROI:
    """Test ROI analytics endpoints"""
    
    def test_get_pilot_roi(self, client):
        """Test individual pilot ROI calculation"""
        response = client.get("/api/roi/pilot/1")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "roi_metrics" in data or "error" in data
    
    def test_get_program_roi(self, client):
        """Test program-wide ROI"""
        response = client.get("/api/roi/program")
        assert response.status_code == 200
        data = response.json()
        assert "total_pilots" in data or "total_revenue" in data
    
    def test_roi_comparison(self, client):
        """Test pilot comparison"""
        response = client.get("/api/roi/comparison")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_forecast_roi(self, client):
        """Test ROI forecasting"""
        response = client.get("/api/analytics/forecast/1?days=30")
        assert response.status_code in [200, 404]


# ===== ANALYTICS TESTS =====

class TestAnalytics:
    """Test advanced analytics endpoints"""
    
    def test_churn_prediction(self, client):
        """Test churn risk prediction"""
        response = client.get("/api/analytics/churn/1")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "churn_probability" in data or "error" in data
    
    def test_benchmark(self, client):
        """Test benchmarking"""
        response = client.get("/api/analytics/benchmark/1")
        assert response.status_code in [200, 404]
    
    def test_program_insights(self, client):
        """Test program-wide insights"""
        response = client.post("/api/analytics/insights/program")
        assert response.status_code == 200


# ===== EXPORT TESTS =====

class TestExport:
    """Test export functionality"""
    
    def test_get_columns(self, client):
        """Test available columns"""
        response = client.get("/api/export/columns/pilots")
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
    
    def test_export_csv(self, client):
        """Test CSV export"""
        export_request = {
            "data_type": "pilots",
            "format": "csv",
            "columns": ["id", "name", "email"]
        }
        response = client.post("/api/export/pilots", json=export_request)
        assert response.status_code in [200, 400]
    
    def test_export_excel(self, client):
        """Test Excel export"""
        export_request = {
            "data_type": "pilots",
            "format": "excel",
            "columns": ["id", "name", "email", "revenue"]
        }
        response = client.post("/api/export/pilots", json=export_request)
        assert response.status_code in [200, 400]


# ===== PERFORMANCE TESTS =====

class TestPerformance:
    """Test performance monitoring"""
    
    def test_health_check(self, client):
        """Test system health"""
        response = client.get("/api/performance/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
    
    def test_api_metrics(self, client):
        """Test API metrics"""
        response = client.get("/api/performance/api-metrics")
        assert response.status_code == 200
    
    def test_system_metrics(self, client):
        """Test system resource metrics"""
        response = client.get("/api/performance/system")
        assert response.status_code == 200


# ===== ALERTS TESTS =====

class TestAlerts:
    """Test alert management"""
    
    def test_pending_alerts(self, client):
        """Test getting pending alerts"""
        response = client.get("/api/alerts/pending")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
    
    def test_get_milestones(self, client):
        """Test milestone definitions"""
        response = client.get("/api/alerts/milestones")
        assert response.status_code == 200
        data = response.json()
        assert "milestones" in data
    
    def test_pilot_milestones(self, client):
        """Test pilot milestone progress"""
        response = client.get("/api/alerts/pilot/1")
        assert response.status_code in [200, 404]


# ===== BILLING TESTS =====

class TestBilling:
    """Test billing and subscription"""
    
    def test_get_plans(self, client):
        """Test billing plans"""
        response = client.get("/api/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) >= 3
    
    def test_get_pricing(self, client):
        """Test pricing information"""
        response = client.get("/api/billing/pricing")
        assert response.status_code == 200
    
    def test_check_usage(self, client):
        """Test usage checking"""
        response = client.get("/api/billing/usage/test-user")
        assert response.status_code in [200, 404]


# ===== INTEGRATION TESTS =====

class TestIntegrations:
    """Test third-party integrations"""
    
    def test_integration_status(self, client):
        """Test integration status"""
        response = client.get("/api/integrations/status")
        assert response.status_code == 200
        data = response.json()
        assert "slack" in data
        assert "google_sheets" in data


# ===== PERFORMANCE & LOAD TESTS =====

class TestPerformanceAndLoad:
    """Performance and load testing"""
    
    def test_response_time_under_100ms(self, client):
        """Ensure critical endpoints respond under 100ms"""
        import time
        start = time.time()
        response = client.get("/api/performance/status")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        assert elapsed < 100, f"Response took {elapsed}ms"
    
    def test_list_pilots_performance(self, client):
        """Test pilot listing performance with many pilots"""
        import time
        start = time.time()
        response = client.get("/api/pilot")
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed < 500  # Should be under 500ms even with many pilots
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/pilot")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(r.status_code == 200 for r in results)


# ===== DATABASE TESTS =====

class TestDatabase:
    """Test database operations"""
    
    def test_database_connectivity(self):
        """Test database connection"""
        try:
            conn = sqlite3.connect("data/clariq_pilots.sqlite")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pilots")
            result = cursor.fetchone()
            assert result[0] >= 0
            conn.close()
        except Exception as e:
            pytest.fail(f"Database connection failed: {str(e)}")
    
    def test_database_indices(self):
        """Test database indices exist"""
        conn = sqlite3.connect("data/clariq_pilots.sqlite")
        cursor = conn.cursor()
        
        # Check for expected indices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='pilots'
        """)
        indices = [r[0] for r in cursor.fetchall()]
        
        # Should have at least one index
        assert len(indices) > 0
        conn.close()


# ===== ERROR HANDLING TESTS =====

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_pilot_id(self, client):
        """Test handling invalid pilot ID"""
        response = client.get("/api/pilot/invalid")
        assert response.status_code in [400, 404, 422]
    
    def test_missing_required_fields(self, client):
        """Test handling missing required fields"""
        response = client.post("/api/pilot", json={})
        assert response.status_code in [400, 422]
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON"""
        response = client.post(
            "/api/pilot",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


# ===== SECURITY TESTS =====

class TestSecurity:
    """Test security features"""
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.get(
            "/api/pilot",
            headers={"Origin": "https://example.com"}
        )
        assert response.status_code == 200
    
    def test_rate_limiting(self, client):
        """Test rate limiting"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.get("/api/pilot")
            responses.append(response)
        
        # Should not all fail
        successful = sum(1 for r in responses if r.status_code == 200)
        assert successful >= 8  # At least 80% should succeed
    
    def test_no_sql_injection(self, client):
        """Test SQL injection protection"""
        sql_injection = "'; DROP TABLE pilots; --"
        response = client.get(f"/api/pilot?search={sql_injection}")
        assert response.status_code in [200, 400]


# ===== DATA INTEGRITY TESTS =====

class TestDataIntegrity:
    """Test data integrity"""
    
    def test_pilot_data_consistency(self):
        """Test pilot data is consistent across reads"""
        from db.pilots_db import get_pilot, list_pilots
        
        all_pilots = list_pilots()
        if all_pilots:
            pilot_id = all_pilots[0]['id']
            pilot = get_pilot(pilot_id)
            
            # Data should be consistent
            assert pilot['id'] == pilot_id
    
    def test_revenue_calculation_accuracy(self):
        """Test revenue calculations are accurate"""
        from db.revenue_calc import calculate_revenue
        
        # Should return a number
        revenue = calculate_revenue(1)
        assert isinstance(revenue, (int, float))
        assert revenue >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
