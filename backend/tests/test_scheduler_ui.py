"""
EDARSA HUB - Scheduler UI Backend Tests
========================================
Tests for Scheduler API endpoints with RBAC protection.

Endpoints tested:
- GET /api/v2/scheduler/status - SCHEDULER_VER
- GET /api/v2/scheduler/config - SCHEDULER_VER
- GET /api/v2/scheduler/logs - SCHEDULER_VER
- GET /api/v2/scheduler/logs/stats - SCHEDULER_VER
- POST /api/v2/scheduler/jobs/{job_id}/pause - SCHEDULER_GESTIONAR
- POST /api/v2/scheduler/jobs/{job_id}/resume - SCHEDULER_GESTIONAR
- POST /api/v2/scheduler/jobs/{job_id}/run - SCHEDULER_ADMIN
"""

import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stock-tracker-990.preview.emergentagent.com')

# Test credentials (centralized)
# Note: For scheduler UI tests, we use specific RBAC test accounts
# These should be in env vars for real deployment
ADMIN_CREDENTIALS = {
    "email": os.environ.get("TEST_SCHEDULER_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
    "password": os.environ.get("TEST_SCHEDULER_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
}

OPERADOR_CREDENTIALS = {
    "email": os.environ.get("TEST_SCHEDULER_OPERADOR_EMAIL", "operador.test@edarsa.com"),
    "password": os.environ.get("TEST_SCHEDULER_OPERADOR_PASSWORD", TEST_ADMIN_PASSWORD)
}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for testing."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=ADMIN_CREDENTIALS
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def operador_token():
    """Get operador token for testing."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=OPERADOR_CREDENTIALS
    )
    assert response.status_code == 200, f"Operador login failed: {response.text}"
    return response.json()["token"]


class TestSchedulerStatusEndpoint:
    """Tests for GET /api/v2/scheduler/status"""
    
    def test_admin_can_get_status(self, admin_token):
        """Admin (SCHEDULER_VER) can get scheduler status."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "running" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        
        # Validate jobs have required fields
        if data["jobs"]:
            job = data["jobs"][0]
            assert "id" in job
            assert "name" in job
            assert "next_run" in job
            assert "trigger" in job
    
    def test_operador_cannot_get_status(self, operador_token):
        """Operador (no SCHEDULER_VER) gets 403."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/status",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["permiso_requerido"] == "SCHEDULER_VER"


class TestSchedulerConfigEndpoint:
    """Tests for GET /api/v2/scheduler/config"""
    
    def test_admin_can_get_config(self, admin_token):
        """Admin can get scheduler configuration."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "enabled" in data
        assert "timezone" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], dict)
        
        # Validate job config structure
        if data["jobs"]:
            job_config = list(data["jobs"].values())[0]
            assert "job_id" in job_config
            assert "enabled" in job_config
            assert "interval_seconds" in job_config
    
    def test_operador_cannot_get_config(self, operador_token):
        """Operador gets 403 for config."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/config",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403


class TestSchedulerLogsEndpoint:
    """Tests for GET /api/v2/scheduler/logs"""
    
    def test_admin_can_get_logs(self, admin_token):
        """Admin can get execution logs."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs?hours=24&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "items" in data
        assert "total" in data
        assert "filters" in data
        assert isinstance(data["items"], list)
        
        # Validate log entry structure
        if data["items"]:
            log = data["items"][0]
            assert "id" in log
            assert "job_name" in log
            assert "status" in log
            assert "started_at" in log
            assert "duration_ms" in log
    
    def test_admin_can_filter_logs_by_job(self, admin_token):
        """Admin can filter logs by job_name."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs?job_name=sla_processor&hours=24",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All logs should be for sla_processor
        for log in data["items"]:
            assert log["job_name"] == "sla_processor"
    
    def test_admin_can_filter_logs_by_status(self, admin_token):
        """Admin can filter logs by status."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs?status=success&hours=24",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All logs should have success status
        for log in data["items"]:
            assert log["status"] == "success"
    
    def test_operador_cannot_get_logs(self, operador_token):
        """Operador gets 403 for logs."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403


class TestSchedulerStatsEndpoint:
    """Tests for GET /api/v2/scheduler/logs/stats"""
    
    def test_admin_can_get_stats(self, admin_token):
        """Admin can get execution statistics."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs/stats?hours=24",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "stats" in data
        assert "period_hours" in data
        assert "timestamp" in data
        assert data["period_hours"] == 24
    
    def test_operador_cannot_get_stats(self, operador_token):
        """Operador gets 403 for stats."""
        response = requests.get(
            f"{BASE_URL}/api/v2/scheduler/logs/stats",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403


class TestSchedulerPauseResumeEndpoints:
    """Tests for POST /api/v2/scheduler/jobs/{job_id}/pause and /resume"""
    
    def test_admin_can_pause_job(self, admin_token):
        """Admin (SCHEDULER_GESTIONAR) can pause a job."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/pause",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        assert data["job_id"] == "sla_processor"
    
    def test_admin_can_resume_job(self, admin_token):
        """Admin can resume a paused job."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/resume",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resumed"
        assert data["job_id"] == "sla_processor"
    
    def test_operador_cannot_pause_job(self, operador_token):
        """Operador (no SCHEDULER_GESTIONAR) gets 403 for pause."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/pause",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["permiso_requerido"] == "SCHEDULER_GESTIONAR"
    
    def test_operador_cannot_resume_job(self, operador_token):
        """Operador gets 403 for resume."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/resume",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403
        assert response.json()["detail"]["permiso_requerido"] == "SCHEDULER_GESTIONAR"


class TestSchedulerRunEndpoint:
    """Tests for POST /api/v2/scheduler/jobs/{job_id}/run"""
    
    def test_admin_can_run_job(self, admin_token):
        """Admin (SCHEDULER_ADMIN) can run a job manually."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/run",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "executed"
        assert data["job_id"] == "sla_processor"
    
    def test_operador_cannot_run_job(self, operador_token):
        """Operador (no SCHEDULER_ADMIN) gets 403 for run."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/run",
            headers={"Authorization": f"Bearer {operador_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["permiso_requerido"] == "SCHEDULER_ADMIN"
    
    def test_run_unknown_job_returns_error(self, admin_token):
        """Running unknown job returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/v2/scheduler/jobs/unknown_job/run",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400


class TestSchedulerNoAuth:
    """Tests for endpoints without authentication."""
    
    def test_status_without_token_returns_401(self):
        """Status endpoint without token returns 401."""
        response = requests.get(f"{BASE_URL}/api/v2/scheduler/status")
        assert response.status_code == 401
    
    def test_config_without_token_returns_401(self):
        """Config endpoint without token returns 401."""
        response = requests.get(f"{BASE_URL}/api/v2/scheduler/config")
        assert response.status_code == 401
    
    def test_logs_without_token_returns_401(self):
        """Logs endpoint without token returns 401."""
        response = requests.get(f"{BASE_URL}/api/v2/scheduler/logs")
        assert response.status_code == 401
    
    def test_pause_without_token_returns_401(self):
        """Pause endpoint without token returns 401."""
        response = requests.post(f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/pause")
        assert response.status_code == 401
    
    def test_run_without_token_returns_401(self):
        """Run endpoint without token returns 401."""
        response = requests.post(f"{BASE_URL}/api/v2/scheduler/jobs/sla_processor/run")
        assert response.status_code == 401
