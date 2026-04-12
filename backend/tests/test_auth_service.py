"""
EDARSA HUB - Tests para modules/auth/service.py
================================================
Tests de cobertura para lógica de autenticación y usuarios.

PASO 5: Ampliar cobertura de auth/service.py a ~50%.
NO conecta a servicios reales - usa MOCKS exclusivamente.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
import uuid


class TestRegisterUser:
    """Tests de registro de usuarios"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test: Registro exitoso de nuevo usuario"""
        from modules.auth.service import register_user
        from modules.auth.schemas import UserCreate
        
        user_data = UserCreate(
            email="nuevo@test.com",
            name="Nuevo Usuario",
            password="password123",
            role="Usuario"
        )
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value=None)
            mock_repo.create_user = AsyncMock()
            
            result = await register_user(user_data)
            
            assert "token" in result
            assert "user" in result
            assert result["user"]["email"] == "nuevo@test.com"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_already_exists(self):
        """Test: Error cuando usuario ya existe"""
        from modules.auth.service import register_user
        from modules.auth.schemas import UserCreate
        
        user_data = UserCreate(
            email="existente@test.com",
            name="Usuario Existente",
            password="password123",
            role="Usuario"
        )
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value={"email": "existente@test.com"})
            
            with pytest.raises(HTTPException) as exc_info:
                await register_user(user_data)
            
            assert exc_info.value.status_code == 400
            assert "ya existe" in exc_info.value.detail


class TestLoginUser:
    """Tests de login de usuarios"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test: Login exitoso con credenciales válidas"""
        from modules.auth.service import login_user
        from core.security import hash_password
        
        hashed_pw = hash_password("password123")
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value={
                "id": "user-123",
                "email": "test@test.com",
                "password": hashed_pw,
                "name": "Test User",
                "role": "Usuario",
                "active": True
            })
            
            result = await login_user("test@test.com", "password123")
            
            assert "token" in result
            assert "user" in result
            assert "password" not in result["user"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """Test: Error con contraseña incorrecta"""
        from modules.auth.service import login_user
        from core.security import hash_password
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value={
                "id": "user-123",
                "email": "test@test.com",
                "password": hash_password("correcta"),
                "name": "Test User",
                "role": "Usuario",
                "active": True
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await login_user("test@test.com", "incorrecta")
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test: Error cuando usuario no existe"""
        from modules.auth.service import login_user
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc_info:
                await login_user("noexiste@test.com", "password")
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_inactive_user(self):
        """Test: Error cuando usuario está inactivo"""
        from modules.auth.service import login_user
        from core.security import hash_password
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_email = AsyncMock(return_value={
                "id": "user-123",
                "email": "inactivo@test.com",
                "password": hash_password("password123"),
                "name": "Inactive User",
                "role": "Usuario",
                "active": False
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await login_user("inactivo@test.com", "password123")
            
            assert exc_info.value.status_code == 401
            assert "inactivo" in exc_info.value.detail.lower()


class TestGetUsers:
    """Tests de obtención de usuarios"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_users_admin(self):
        """Test: Admin puede obtener todos los usuarios"""
        from modules.auth.service import get_users
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.get_all_users = AsyncMock(return_value=[
                {"id": "user-1", "email": "user1@test.com"},
                {"id": "user-2", "email": "user2@test.com"}
            ])
            
            result = await get_users(admin_user)
            
            assert len(result) == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_users_non_admin_forbidden(self):
        """Test: Usuario no admin no puede obtener usuarios"""
        from modules.auth.service import get_users
        
        regular_user = {"role": "Usuario", "id": "user-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_users(regular_user)
        
        assert exc_info.value.status_code == 403


class TestUpdateUser:
    """Tests de actualización de usuarios"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_admin(self):
        """Test: Admin puede actualizar usuario"""
        from modules.auth.service import update_user
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.update_user = AsyncMock()
            
            result = await update_user("user-123", {"name": "Nuevo Nombre"}, admin_user)
            
            assert "message" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_non_admin_forbidden(self):
        """Test: Usuario no admin no puede actualizar"""
        from modules.auth.service import update_user
        
        regular_user = {"role": "Usuario", "id": "user-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            await update_user("user-123", {"name": "Test"}, regular_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_with_password(self):
        """Test: Actualizar usuario con nueva contraseña"""
        from modules.auth.service import update_user
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.update_user = AsyncMock()
            
            result = await update_user("user-123", {"password": "nueva_contraseña"}, admin_user)
            
            # Verificar que se llamó update_user con password hasheado
            mock_repo.update_user.assert_called_once()
            call_args = mock_repo.update_user.call_args
            update_data = call_args[0][1]
            
            # El password debe estar hasheado (no ser la cadena original)
            assert "password" in update_data
            assert update_data["password"] != "nueva_contraseña"


class TestDeleteUser:
    """Tests de eliminación de usuarios"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_user_admin(self):
        """Test: Admin puede desactivar usuario"""
        from modules.auth.service import delete_user
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.deactivate_user = AsyncMock()
            
            result = await delete_user("user-123", admin_user)
            
            assert "message" in result
            mock_repo.deactivate_user.assert_called_once_with("user-123")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_user_non_admin_forbidden(self):
        """Test: Usuario no admin no puede eliminar"""
        from modules.auth.service import delete_user
        
        regular_user = {"role": "Supervisor", "id": "sup-1"}
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_user("user-123", regular_user)
        
        assert exc_info.value.status_code == 403


class TestUpdateUserPermissions:
    """Tests de actualización de permisos"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_permissions_admin(self):
        """Test: Admin puede actualizar permisos"""
        from modules.auth.service import update_user_permissions
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        permissions = {
            "allowed_servers": ["server-1", "server-2"],
            "allowed_sucursales": {"server-1": ["SUC001"]}
        }
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_id = AsyncMock(return_value={"id": "user-123"})
            mock_repo.update_user = AsyncMock()
            
            result = await update_user_permissions("user-123", permissions, admin_user)
            
            assert "message" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_permissions_user_not_found(self):
        """Test: Error si usuario no existe"""
        from modules.auth.service import update_user_permissions
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_user_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc_info:
                await update_user_permissions("no-existe", {}, admin_user)
            
            assert exc_info.value.status_code == 404


class TestRolesOperations:
    """Tests de operaciones con roles"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_roles_admin(self):
        """Test: Admin puede obtener roles"""
        from modules.auth.service import get_roles
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.get_all_roles = AsyncMock(return_value=[
                {"id": "role-1", "nombre": "Administrador"},
                {"id": "role-2", "nombre": "Usuario"}
            ])
            
            result = await get_roles(admin_user)
            
            assert len(result) == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_roles_creates_defaults_if_empty(self):
        """Test: Crea roles predeterminados si no existen"""
        from modules.auth.service import get_roles
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.get_all_roles = AsyncMock(return_value=[])
            mock_repo.create_default_roles = AsyncMock(return_value=[
                {"id": "role-1", "nombre": "Administrador"},
                {"id": "role-2", "nombre": "Supervisor"},
                {"id": "role-3", "nombre": "Usuario"}
            ])
            
            result = await get_roles(admin_user)
            
            assert len(result) == 3
            mock_repo.create_default_roles.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_role_success(self):
        """Test: Admin puede crear rol"""
        from modules.auth.service import create_role
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        role_data = {"nombre": "Auditor", "descripcion": "Rol de auditoría", "permisos": ["comercial"]}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_role_by_name = AsyncMock(return_value=None)
            mock_repo.create_role = AsyncMock(return_value={"id": "new-role", **role_data})
            
            result = await create_role(role_data, admin_user)
            
            assert result["nombre"] == "Auditor"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self):
        """Test: Error al crear rol con nombre duplicado"""
        from modules.auth.service import create_role
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_role_by_name = AsyncMock(return_value={"nombre": "Existente"})
            
            with pytest.raises(HTTPException) as exc_info:
                await create_role({"nombre": "Existente"}, admin_user)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_role_success(self):
        """Test: Admin puede eliminar rol no de sistema"""
        from modules.auth.service import delete_role
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_role_by_id = AsyncMock(return_value={
                "id": "custom-role",
                "nombre": "Custom",
                "es_sistema": False
            })
            mock_repo.count_users_with_role = AsyncMock(return_value=0)
            mock_repo.delete_role = AsyncMock()
            
            result = await delete_role("custom-role", admin_user)
            
            assert "message" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_role_system_role_forbidden(self):
        """Test: No se puede eliminar rol de sistema"""
        from modules.auth.service import delete_role
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_role_by_id = AsyncMock(return_value={
                "id": "admin-role",
                "nombre": "Administrador",
                "es_sistema": True
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_role("admin-role", admin_user)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_role_with_users_forbidden(self):
        """Test: No se puede eliminar rol con usuarios asignados"""
        from modules.auth.service import delete_role
        
        admin_user = {"role": "Administrador", "id": "admin-1"}
        
        with patch("modules.auth.service.repo") as mock_repo:
            mock_repo.find_role_by_id = AsyncMock(return_value={
                "id": "used-role",
                "nombre": "EnUso",
                "es_sistema": False
            })
            mock_repo.count_users_with_role = AsyncMock(return_value=5)
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_role("used-role", admin_user)
            
            assert exc_info.value.status_code == 400
            assert "5 usuario" in exc_info.value.detail


class TestServiceImports:
    """Tests de importación correcta del módulo"""
    
    @pytest.mark.unit
    def test_all_functions_importable(self):
        """Test: Todas las funciones se pueden importar"""
        from modules.auth.service import (
            register_user,
            login_user,
            get_users,
            update_user,
            delete_user,
            update_user_permissions,
            get_roles,
            create_role,
            update_role,
            delete_role
        )
        
        assert callable(register_user)
        assert callable(login_user)
        assert callable(get_users)
        assert callable(update_user)
        assert callable(delete_user)
        assert callable(update_user_permissions)
        assert callable(get_roles)
        assert callable(create_role)
        assert callable(update_role)
        assert callable(delete_role)
