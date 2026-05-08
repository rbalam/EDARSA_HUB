"""
Test Suite: Centro de Control - Recipients Manager (MongoDB)
============================================================
Tests for CRUD operations on alert recipients stored in MongoDB.

Features tested:
- GET /api/centro-control/destinatarios - List all recipients
- POST /api/centro-control/destinatarios - Create recipient (email/whatsapp)
- PUT /api/centro-control/destinatarios/{id} - Update/toggle recipient
- DELETE /api/centro-control/destinatarios/{id} - Delete recipient
- GET /api/centro-control/destinatarios/resumen - Summary of recipients
- Verify email_notifications.py reads from MongoDB
- Verify whatsapp_notifications.py reads from MongoDB
"""

import pytest
import requests
import os
from tests.test_config import test_config

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRecipientsManagerCRUD:
    """CRUD operations for alert recipients in MongoDB"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.created_ids = []
    
    def teardown_method(self, method):
        """Cleanup test-created recipients"""
        for recipient_id in self.created_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/centro-control/destinatarios/{recipient_id}",
                    headers=self.headers
                )
            except Exception:
                pass
    
    # =========================================================================
    # GET /api/centro-control/destinatarios
    # =========================================================================
    
    def test_list_recipients_returns_200(self):
        """GET /destinatarios should return 200 with list of recipients"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "destinatarios" in data
        assert isinstance(data["destinatarios"], list)
        print(f"✓ GET /destinatarios: {data['total']} recipients found")
    
    def test_list_recipients_filter_by_type_email(self):
        """GET /destinatarios?tipo=email should filter by email type"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?tipo=email",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        for recipient in data["destinatarios"]:
            assert recipient["tipo"] == "email"
        print(f"✓ GET /destinatarios?tipo=email: {data['total']} email recipients")
    
    def test_list_recipients_filter_by_type_whatsapp(self):
        """GET /destinatarios?tipo=whatsapp should filter by whatsapp type"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?tipo=whatsapp",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        for recipient in data["destinatarios"]:
            assert recipient["tipo"] == "whatsapp"
        print(f"✓ GET /destinatarios?tipo=whatsapp: {data['total']} whatsapp recipients")
    
    def test_list_recipients_requires_auth(self):
        """GET /destinatarios without auth should return 401/403"""
        response = self.client.get(f"{BASE_URL}/api/centro-control/destinatarios")
        assert response.status_code in [401, 403]
        print("✓ GET /destinatarios requires authentication")
    
    # =========================================================================
    # POST /api/centro-control/destinatarios
    # =========================================================================
    
    def test_create_email_recipient(self):
        """POST /destinatarios should create email recipient"""
        payload = {
            "tipo": "email",
            "destinatario": "TEST_pytest_email@example.com",
            "nombre": "PyTest Email User"
        }
        response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["destinatario"]["tipo"] == "email"
        assert data["destinatario"]["destinatario"] == "TEST_pytest_email@example.com"
        assert data["destinatario"]["nombre"] == "PyTest Email User"
        assert data["destinatario"]["activo"]
        assert "id" in data["destinatario"]
        self.created_ids.append(data["destinatario"]["id"])
        print(f"✓ POST /destinatarios (email): Created ID {data['destinatario']['id']}")
    
    def test_create_whatsapp_recipient(self):
        """POST /destinatarios should create whatsapp recipient"""
        payload = {
            "tipo": "whatsapp",
            "destinatario": "+521111111111",
            "nombre": "PyTest WhatsApp User"
        }
        response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["destinatario"]["tipo"] == "whatsapp"
        assert data["destinatario"]["destinatario"] == "+521111111111"
        assert data["destinatario"]["activo"]
        self.created_ids.append(data["destinatario"]["id"])
        print(f"✓ POST /destinatarios (whatsapp): Created ID {data['destinatario']['id']}")
    
    def test_create_whatsapp_formats_phone_number(self):
        """POST /destinatarios should format phone number to E.164"""
        payload = {
            "tipo": "whatsapp",
            "destinatario": "52 2222 222222",  # Without + and with spaces
            "nombre": "PyTest Format Test"
        }
        response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        # Should be formatted to E.164 (+ prefix, no spaces)
        assert data["destinatario"]["destinatario"].startswith("+")
        assert " " not in data["destinatario"]["destinatario"]
        self.created_ids.append(data["destinatario"]["id"])
        print(f"✓ POST /destinatarios formats phone: {data['destinatario']['destinatario']}")
    
    def test_create_duplicate_recipient_fails(self):
        """POST /destinatarios with duplicate should return 400"""
        payload = {
            "tipo": "email",
            "destinatario": "TEST_duplicate@example.com",
            "nombre": "First"
        }
        # Create first
        response1 = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response1.status_code == 200
        self.created_ids.append(response1.json()["destinatario"]["id"])
        
        # Try to create duplicate
        response2 = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response2.status_code == 400
        assert "ya existe" in response2.json().get("detail", "").lower()
        print("✓ POST /destinatarios rejects duplicates")
    
    def test_create_invalid_type_fails(self):
        """POST /destinatarios with invalid type should return 400"""
        payload = {
            "tipo": "sms",  # Invalid type
            "destinatario": "TEST_invalid@example.com"
        }
        response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 400
        print("✓ POST /destinatarios rejects invalid type")
    
    def test_create_empty_destinatario_fails(self):
        """POST /destinatarios with empty destinatario should return 400"""
        payload = {
            "tipo": "email",
            "destinatario": "   "  # Empty/whitespace
        }
        response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 400
        print("✓ POST /destinatarios rejects empty destinatario")
    
    # =========================================================================
    # PUT /api/centro-control/destinatarios/{id}
    # =========================================================================
    
    def test_update_recipient_toggle_active(self):
        """PUT /destinatarios/{id} should toggle active status"""
        # Create recipient first
        create_response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json={"tipo": "email", "destinatario": "TEST_toggle@example.com"}
        )
        recipient_id = create_response.json()["destinatario"]["id"]
        self.created_ids.append(recipient_id)
        
        # Deactivate
        response = self.client.put(
            f"{BASE_URL}/api/centro-control/destinatarios/{recipient_id}",
            headers=self.headers,
            json={"activo": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert not data["destinatario"]["activo"]
        
        # Verify with GET
        get_response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?solo_activos=false",
            headers=self.headers
        )
        recipients = get_response.json()["destinatarios"]
        found = next((r for r in recipients if r["id"] == recipient_id), None)
        assert found is not None
        assert not found["activo"]
        print(f"✓ PUT /destinatarios/{recipient_id}: Toggled active to False")
    
    def test_update_recipient_change_name(self):
        """PUT /destinatarios/{id} should update name"""
        # Create recipient first
        create_response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json={"tipo": "email", "destinatario": "TEST_rename@example.com", "nombre": "Original"}
        )
        recipient_id = create_response.json()["destinatario"]["id"]
        self.created_ids.append(recipient_id)
        
        # Update name
        response = self.client.put(
            f"{BASE_URL}/api/centro-control/destinatarios/{recipient_id}",
            headers=self.headers,
            json={"nombre": "Updated Name"}
        )
        assert response.status_code == 200
        assert response.json()["destinatario"]["nombre"] == "Updated Name"
        print(f"✓ PUT /destinatarios/{recipient_id}: Updated name")
    
    def test_update_nonexistent_recipient_fails(self):
        """PUT /destinatarios/{id} with invalid ID should return 400"""
        response = self.client.put(
            f"{BASE_URL}/api/centro-control/destinatarios/000000000000000000000000",
            headers=self.headers,
            json={"activo": False}
        )
        assert response.status_code == 400
        print("✓ PUT /destinatarios rejects nonexistent ID")
    
    # =========================================================================
    # DELETE /api/centro-control/destinatarios/{id}
    # =========================================================================
    
    def test_delete_recipient(self):
        """DELETE /destinatarios/{id} should remove recipient"""
        # Create recipient first
        create_response = self.client.post(
            f"{BASE_URL}/api/centro-control/destinatarios",
            headers=self.headers,
            json={"tipo": "email", "destinatario": "TEST_delete@example.com"}
        )
        recipient_id = create_response.json()["destinatario"]["id"]
        
        # Delete
        response = self.client.delete(
            f"{BASE_URL}/api/centro-control/destinatarios/{recipient_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.json()["success"]
        
        # Verify deletion with GET
        get_response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?solo_activos=false",
            headers=self.headers
        )
        recipients = get_response.json()["destinatarios"]
        found = next((r for r in recipients if r["id"] == recipient_id), None)
        assert found is None
        print(f"✓ DELETE /destinatarios/{recipient_id}: Recipient removed")
    
    def test_delete_nonexistent_recipient_fails(self):
        """DELETE /destinatarios/{id} with invalid ID should return 404"""
        response = self.client.delete(
            f"{BASE_URL}/api/centro-control/destinatarios/000000000000000000000000",
            headers=self.headers
        )
        assert response.status_code == 404
        print("✓ DELETE /destinatarios rejects nonexistent ID")
    
    # =========================================================================
    # GET /api/centro-control/destinatarios/resumen
    # =========================================================================
    
    def test_recipients_summary(self):
        """GET /destinatarios/resumen should return summary by type"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios/resumen",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "whatsapp" in data
        assert "total" in data
        assert "count" in data["email"]
        assert "recipients" in data["email"]
        assert "count" in data["whatsapp"]
        assert "recipients" in data["whatsapp"]
        print(f"✓ GET /destinatarios/resumen: {data['total']} total recipients")


class TestNotificationServicesReadFromMongoDB:
    """Verify email and whatsapp services read recipients from MongoDB"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def test_email_config_shows_mongodb_recipients(self):
        """GET /email/config should show recipients from MongoDB"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/email/config",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "recipients_count" in data["config"]
        assert "recipients" in data["config"]
        # Should have at least the seeded email recipient
        assert data["config"]["recipients_count"] >= 1
        print(f"✓ Email config shows {data['config']['recipients_count']} recipients from MongoDB")
    
    def test_whatsapp_config_shows_mongodb_recipients(self):
        """GET /whatsapp/config should show recipients from MongoDB"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/whatsapp/config",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "recipients_count" in data["config"]
        assert "recipients" in data["config"]
        # Should have at least the seeded whatsapp recipient
        assert data["config"]["recipients_count"] >= 1
        print(f"✓ WhatsApp config shows {data['config']['recipients_count']} recipients from MongoDB")
    
    def test_notificaciones_config_shows_all_services(self):
        """GET /notificaciones/config should show all notification services"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "servicios" in data
        assert "email" in data["servicios"]
        assert "whatsapp" in data["servicios"]
        assert "websocket" in data["servicios"]
        
        # Email should be configured with MongoDB recipients
        email_config = data["servicios"]["email"]["config"]
        assert email_config["configured"]
        assert email_config["recipients_count"] >= 1
        
        # WhatsApp should be configured with MongoDB recipients
        whatsapp_config = data["servicios"]["whatsapp"]["config"]
        assert whatsapp_config["configured"]
        assert whatsapp_config["recipients_count"] >= 1
        
        print("✓ All notification services configured with MongoDB recipients")


class TestSeededRecipients:
    """Verify seeded recipients exist in MongoDB"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def test_seeded_email_recipient_exists(self):
        """Seeded email recipient director@edarsa.com.mx should exist"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?tipo=email",
            headers=self.headers
        )
        assert response.status_code == 200
        recipients = response.json()["destinatarios"]
        email_addresses = [r["destinatario"] for r in recipients]
        assert "director@edarsa.com.mx" in email_addresses
        print("✓ Seeded email recipient director@edarsa.com.mx exists")
    
    def test_seeded_whatsapp_recipient_exists(self):
        """Seeded whatsapp recipient +521234567890 should exist"""
        response = self.client.get(
            f"{BASE_URL}/api/centro-control/destinatarios?tipo=whatsapp",
            headers=self.headers
        )
        assert response.status_code == 200
        recipients = response.json()["destinatarios"]
        phone_numbers = [r["destinatario"] for r in recipients]
        assert "+521234567890" in phone_numbers
        print("✓ Seeded whatsapp recipient +521234567890 exists")


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_config.TEST_ADMIN_EMAIL,
        "password": test_config.TEST_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")
