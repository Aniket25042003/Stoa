"""
File: services/api/tests/test_health.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test health in the test suite.
Dependencies: FastAPI
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
