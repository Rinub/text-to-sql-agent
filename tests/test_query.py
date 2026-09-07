"""
Integration tests for the Text-to-SQL Agent API.

Run with:
    pytest tests/test_query.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /api/v1/health endpoint."""

    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestSchemaEndpoint:
    """Tests for the /api/v1/schema endpoint."""

    def test_get_schema(self):
        response = client.get("/api/v1/schema")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert len(data["tables"]) >= 4  # customers, products, orders, order_items

    def test_schema_has_expected_tables(self):
        response = client.get("/api/v1/schema")
        data = response.json()
        table_names = [t["table_name"] for t in data["tables"]]
        assert "customers" in table_names
        assert "products" in table_names
        assert "orders" in table_names
        assert "order_items" in table_names


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data


class TestQueryEndpoint:
    """Tests for the /api/v1/query endpoint."""

    def test_query_validation_empty(self):
        """Reject empty or too-short questions."""
        response = client.post("/api/v1/query", json={"question": "ab"})
        assert response.status_code == 422  # Validation error

    def test_query_validation_missing_field(self):
        """Reject requests without the question field."""
        response = client.post("/api/v1/query", json={})
        assert response.status_code == 422

    def test_query_live(self):
        response = client.post(
            "/api/v1/query",
            json={"question": "How many customers are there?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_success"] is True
        assert data["sql"]
        assert data["result"]

