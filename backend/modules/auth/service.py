"""
EDARSA HUB - Auth Service
=========================
Lógica de negocio de autenticación.

NOTA: La lógica actual está en server.py.
Este archivo se usará cuando se autorice la migración.
"""

from typing import Optional, Dict, Any


class AuthService:
    """Servicio de autenticación"""
    
    def __init__(self, db):
        self.db = db
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autentica un usuario por email y password.
        
        NOTA: No implementado - usar lógica de server.py
        """
        raise NotImplementedError("Use server.py login until migration")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo usuario.
        
        NOTA: No implementado - usar lógica de server.py
        """
        raise NotImplementedError("Use server.py registration until migration")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por ID.
        
        NOTA: No implementado - usar lógica de server.py
        """
        raise NotImplementedError("Use server.py until migration")
    
    async def update_permissions(self, user_id: str, permissions: Dict[str, Any]) -> bool:
        """
        Actualiza permisos de un usuario.
        
        NOTA: No implementado - usar lógica de server.py
        """
        raise NotImplementedError("Use server.py until migration")
