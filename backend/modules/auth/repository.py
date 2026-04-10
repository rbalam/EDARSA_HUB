"""
EDARSA HUB - Auth Repository
============================
Acceso a datos de usuarios y autenticación.

NOTA: Las queries actuales están en server.py.
Este archivo se usará cuando se autorice la migración.
"""

from typing import Optional, Dict, Any, List


class AuthRepository:
    """Repositorio de datos de autenticación"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.users
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuario por email"""
        raise NotImplementedError("Use server.py until migration")
    
    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca usuario por ID"""
        raise NotImplementedError("Use server.py until migration")
    
    async def create(self, user_data: Dict[str, Any]) -> str:
        """Crea un nuevo usuario"""
        raise NotImplementedError("Use server.py until migration")
    
    async def update(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Actualiza un usuario"""
        raise NotImplementedError("Use server.py until migration")
    
    async def list_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Lista todos los usuarios"""
        raise NotImplementedError("Use server.py until migration")
