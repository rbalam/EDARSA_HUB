"""
EDARSA HUB - Tests Ampliados para core/security.py
==================================================
Tests de cobertura para JWT, hashing y permisos.

PASO 5: Ampliar cobertura de 41% a ~65%.
NO conecta a servicios reales.

CODE QUALITY: Usa TestConfig para credenciales centralizadas.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
import jwt

# Importar configuración centralizada de tests
from tests.test_config import TestConfig


class TestPasswordHashing:
    """Tests de hashing de contraseñas"""
    
    @pytest.mark.unit
    def test_hash_password_returns_string(self):
        """Test: hash_password retorna string"""
        from core.security import hash_password
        
        result = hash_password(TestConfig.TEST_USER_PASSWORD)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.unit
    def test_hash_password_is_different_from_input(self):
        """Test: Hash es diferente de la contraseña original"""
        from core.security import hash_password
        
        password = TestConfig.TEST_USER_PASSWORD
        hashed = hash_password(password)
        
        assert hashed != password
    
    @pytest.mark.unit
    def test_hash_password_generates_unique_hashes(self):
        """Test: Misma contraseña genera hashes diferentes (salt)"""
        from core.security import hash_password
        
        password = TestConfig.TEST_USER_PASSWORD
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # bcrypt usa salt aleatorio, los hashes deben ser diferentes
        assert hash1 != hash2
    
    @pytest.mark.unit
    def test_verify_password_correct(self):
        """Test: verify_password retorna True para contraseña correcta"""
        from core.security import hash_password, verify_password
        
        password = TestConfig.TEST_USER_PASSWORD
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """Test: verify_password retorna False para contraseña incorrecta"""
        from core.security import hash_password, verify_password
        
        password = TestConfig.TEST_USER_PASSWORD
        hashed = hash_password(password)
        
        assert not verify_password("wrong_password_definitely", hashed)
    
    @pytest.mark.unit
    def test_verify_password_empty(self):
        """Test: verify_password con contraseña vacía"""
        from core.security import hash_password, verify_password
        
        hashed = hash_password(TestConfig.TEST_USER_PASSWORD)
        
        assert not verify_password("", hashed)


class TestJwtCreation:
    """Tests de creación de tokens JWT"""
    
    @pytest.mark.unit
    def test_create_token_returns_string(self):
        """Test: create_token retorna string"""
        from core.security import create_token
        
        token = create_token("user-123", "test@test.com", "Usuario")
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.unit
    def test_create_token_is_valid_jwt(self):
        """Test: Token creado es JWT válido"""
        from core.security import create_token, JWT_SECRET, JWT_ALGORITHM
        
        token = create_token("user-123", "test@test.com", "Administrador")
        
        # Decodificar para verificar estructura
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        assert "user_id" in payload
        assert "email" in payload
        assert "role" in payload
        assert "exp" in payload
    
    @pytest.mark.unit
    def test_create_token_contains_correct_data(self):
        """Test: Token contiene datos correctos"""
        from core.security import create_token, JWT_SECRET, JWT_ALGORITHM
        
        user_id = "abc-123"
        email = "admin@test.com"
        role = "Supervisor"
        
        token = create_token(user_id, email, role)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
    
    @pytest.mark.unit
    def test_create_token_has_expiration(self):
        """Test: Token tiene fecha de expiración"""
        from core.security import create_token, JWT_SECRET, JWT_ALGORITHM
        
        token = create_token("user-123", "test@test.com", "Usuario")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # La expiración debe ser en el futuro
        assert exp_time > now


class TestJwtVerification:
    """Tests de verificación de tokens JWT"""
    
    @pytest.mark.unit
    def test_verify_token_valid(self):
        """Test: verify_token acepta token válido"""
        from core.security import create_token, verify_token
        
        token = create_token("user-123", "test@test.com", "Usuario")
        payload = verify_token(token)
        
        assert payload["email"] == "test@test.com"
    
    @pytest.mark.unit
    def test_verify_token_invalid_signature(self):
        """Test: verify_token rechaza token con firma inválida"""
        from core.security import verify_token, JWT_ALGORITHM
        from fastapi import HTTPException
        
        # Crear token con secret diferente
        fake_token = jwt.encode(
            {"user_id": "fake", "email": "fake@fake.com", "role": "Usuario", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong_secret",
            algorithm=JWT_ALGORITHM
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(fake_token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    def test_verify_token_expired(self):
        """Test: verify_token rechaza token expirado"""
        from core.security import verify_token, JWT_SECRET, JWT_ALGORITHM
        from fastapi import HTTPException
        
        # Crear token ya expirado
        expired_token = jwt.encode(
            {"user_id": "user", "email": "test@test.com", "role": "Usuario", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail.lower()
    
    @pytest.mark.unit
    def test_verify_token_malformed(self):
        """Test: verify_token rechaza token malformado"""
        from core.security import verify_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("esto.no.es.un.token.valido")
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    def test_verify_token_empty(self):
        """Test: verify_token rechaza token vacío"""
        from core.security import verify_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_token("")


class TestUserPermissions:
    """Tests de permisos de usuario"""
    
    @pytest.mark.unit
    def test_admin_has_all_server_access(self):
        """Test: Administrador tiene acceso a todos los servidores"""
        from core.security import user_has_server_access
        
        admin_user = {
            "id": "admin-1",
            "email": "admin@test.com",
            "role": "Administrador",
            "allowed_servers": []
        }
        
        assert user_has_server_access(admin_user, "any-server-id")
    
    @pytest.mark.unit
    def test_user_has_access_to_allowed_server(self):
        """Test: Usuario tiene acceso a servidor permitido"""
        from core.security import user_has_server_access
        
        user = {
            "id": "user-1",
            "email": "user@test.com",
            "role": "Usuario",
            "allowed_servers": ["server-1", "server-2"]
        }
        
        assert user_has_server_access(user, "server-1")
    
    @pytest.mark.unit
    def test_user_no_access_to_restricted_server(self):
        """Test: Usuario NO tiene acceso a servidor no permitido"""
        from core.security import user_has_server_access
        
        user = {
            "id": "user-1",
            "email": "user@test.com",
            "role": "Usuario",
            "allowed_servers": ["server-1"]
        }
        
        assert not user_has_server_access(user, "server-99")
    
    @pytest.mark.unit
    def test_supervisor_follows_allowed_servers(self):
        """Test: Supervisor sigue reglas de allowed_servers"""
        from core.security import user_has_server_access
        
        supervisor = {
            "id": "sup-1",
            "email": "sup@test.com",
            "role": "Supervisor",
            "allowed_servers": ["server-a", "server-b"]
        }
        
        assert user_has_server_access(supervisor, "server-a")
        assert not user_has_server_access(supervisor, "server-c")
    
    @pytest.mark.unit
    def test_user_with_empty_allowed_servers(self):
        """Test: Usuario sin servidores permitidos"""
        from core.security import user_has_server_access
        
        user = {
            "id": "user-1",
            "email": "user@test.com",
            "role": "Usuario",
            "allowed_servers": []
        }
        
        assert not user_has_server_access(user, "any-server")


class TestFilterServers:
    """Tests de filtrado de servidores por permisos"""
    
    @pytest.mark.unit
    def test_admin_sees_all_servers(self):
        """Test: Administrador ve todos los servidores"""
        from core.security import filter_servers_by_permissions
        
        admin = {"role": "Administrador", "allowed_servers": []}
        servers = [
            {"id": "s1", "name": "Server 1"},
            {"id": "s2", "name": "Server 2"},
            {"id": "s3", "name": "Server 3"}
        ]
        
        # Nota: La firma es filter_servers_by_permissions(servers, user)
        filtered = filter_servers_by_permissions(servers, admin)
        
        assert len(filtered) == 3
    
    @pytest.mark.unit
    def test_user_sees_only_allowed_servers(self):
        """Test: Usuario ve solo servidores permitidos"""
        from core.security import filter_servers_by_permissions
        
        user = {"role": "Usuario", "allowed_servers": ["s1", "s3"]}
        servers = [
            {"id": "s1", "name": "Server 1"},
            {"id": "s2", "name": "Server 2"},
            {"id": "s3", "name": "Server 3"}
        ]
        
        # Nota: La firma es filter_servers_by_permissions(servers, user)
        filtered = filter_servers_by_permissions(servers, user)
        
        assert len(filtered) == 2
        assert all(s["id"] in ["s1", "s3"] for s in filtered)
    
    @pytest.mark.unit
    def test_empty_servers_list(self):
        """Test: Lista vacía de servidores"""
        from core.security import filter_servers_by_permissions
        
        user = {"role": "Usuario", "allowed_servers": ["s1"]}
        servers = []
        
        # Nota: La firma es filter_servers_by_permissions(servers, user)
        filtered = filter_servers_by_permissions(servers, user)
        
        assert len(filtered) == 0


class TestSecurityInit:
    """Tests de inicialización del módulo de seguridad"""
    
    @pytest.mark.unit
    def test_init_security_accepts_db(self):
        """Test: init_security acepta conexión de BD"""
        from core.security import init_security
        
        mock_db = MagicMock()
        
        # No debe lanzar excepción
        init_security(mock_db)
    
    @pytest.mark.unit
    def test_get_db_after_init(self):
        """Test: get_db funciona después de init"""
        from core.security import init_security, get_db
        
        mock_db = MagicMock()
        init_security(mock_db)
        
        result = get_db()
        assert result is mock_db
