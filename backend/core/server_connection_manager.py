"""
EDARSA HUB - Server Connection Manager
======================================
Gestor centralizado de configuración y conexiones a servidores SQL.

PRINCIPIOS:
1. EDARSA HUB es la fuente ÚNICA de credenciales (MongoDB)
2. Ningún módulo debe hardcodear usuarios o passwords
3. Las credenciales NUNCA se exponen al frontend
4. Soporte para auditoría de accesos

CREADO: 2026-04-19
MOTIVO: Eliminar credenciales dispersas y hardcodeadas
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ServerConnectionManager:
    """
    Gestor centralizado de conexiones a servidores SQL.
    
    Responsabilidades:
    - Resolver configuración activa desde MongoDB
    - Validar credenciales antes de uso
    - Exponer solo metadatos seguros (sin passwords)
    - Logging de auditoría
    
    Uso:
        from core.server_connection_manager import ServerConnectionManager
        
        scm = ServerConnectionManager()
        config = scm.get_server_config(server_id)
        
        # Para queries
        from core.db import execute_sql_query
        result = execute_sql_query(
            config['host'], config['port'], config['database'],
            config['username'], config['password'], query
        )
    """
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos
        self._last_cache_clear = datetime.now(timezone.utc)
        logger.info("ServerConnectionManager inicializado")
    
    def _get_db(self):
        """Obtiene la conexión a MongoDB (lazy loading)"""
        if self._db is None:
            try:
                from pymongo import MongoClient
                import os
                mongo_url = os.environ.get('MONGO_URL')
                client = MongoClient(mongo_url)
                self._db = client['edarsa_hub']
            except Exception as e:
                logger.error(f"Error conectando a MongoDB: {e}")
                raise
        return self._db
    
    def _clear_cache_if_needed(self):
        """Limpia el caché si ha expirado el TTL"""
        now = datetime.now(timezone.utc)
        if (now - self._last_cache_clear).total_seconds() > self._cache_ttl:
            self._cache = {}
            self._last_cache_clear = now
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración completa de un servidor por ID.
        
        Args:
            server_id: UUID del servidor
            
        Returns:
            Dict con configuración completa (incluyendo password) o None
            
        NOTA: Este método devuelve el password. Usar solo en backend.
        """
        self._clear_cache_if_needed()
        
        cache_key = f"server_{server_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            db = self._get_db()
            server = db.servers.find_one(
                {"id": server_id, "active": True},
                {"_id": 0}
            )
            
            if server:
                self._cache[cache_key] = server
                logger.debug(f"ServerConfig cargado: {server.get('name')} ({server_id})")
            else:
                logger.warning(f"Servidor no encontrado o inactivo: {server_id}")
                
            return server
        except Exception as e:
            logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
            return None
    
    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de un servidor por nombre.
        
        Args:
            name: Nombre del servidor
            
        Returns:
            Dict con configuración completa o None
        """
        try:
            db = self._get_db()
            server = db.servers.find_one(
                {"name": name, "active": True},
                {"_id": 0}
            )
            return server
        except Exception as e:
            logger.error(f"Error obteniendo servidor por nombre {name}: {e}")
            return None
    
    def get_servers_by_type(self, system_type: str, visible_only: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene todos los servidores de un tipo específico.
        
        Args:
            system_type: Tipo de sistema (SoftRestaurant, MPRO, etc.)
            visible_only: Si True, solo devuelve servidores visibles en operaciones
            
        Returns:
            Lista de configuraciones de servidores
        """
        try:
            db = self._get_db()
            query = {"system_type": system_type, "active": True}
            if visible_only:
                query["visible_en_operaciones"] = {"$ne": False}
            
            servers = list(db.servers.find(query, {"_id": 0}))
            logger.debug(f"Encontrados {len(servers)} servidores tipo {system_type}")
            return servers
        except Exception as e:
            logger.error(f"Error obteniendo servidores tipo {system_type}: {e}")
            return []
    
    def get_safe_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información SEGURA de un servidor (SIN password).
        
        Usar este método para exponer info al frontend o logs públicos.
        
        Args:
            server_id: UUID del servidor
            
        Returns:
            Dict sin campos sensibles
        """
        server = self.get_server_config(server_id)
        if not server:
            return None
        
        # Remover campos sensibles
        safe_info = {k: v for k, v in server.items() 
                     if k not in ('password', '_id')}
        return safe_info
    
    def validate_credentials(self, server_id: str) -> bool:
        """
        Valida que un servidor tenga credenciales configuradas.
        
        Args:
            server_id: UUID del servidor
            
        Returns:
            True si tiene host, username y password configurados
        """
        server = self.get_server_config(server_id)
        if not server:
            return False
        
        required_fields = ['host', 'username', 'password', 'database']
        for field in required_fields:
            if not server.get(field):
                logger.warning(f"Servidor {server_id} sin campo requerido: {field}")
                return False
        
        return True
    
    def log_connection_attempt(self, server_id: str, success: bool, 
                               error_msg: Optional[str] = None):
        """
        Registra un intento de conexión para auditoría.
        
        Args:
            server_id: UUID del servidor
            success: Si la conexión fue exitosa
            error_msg: Mensaje de error si falló
        """
        try:
            db = self._get_db()
            db.server_connection_log.insert_one({
                "server_id": server_id,
                "timestamp": datetime.now(timezone.utc),
                "success": success,
                "error": error_msg[:500] if error_msg else None
            })
        except Exception as e:
            # No fallar por error de logging
            logger.warning(f"Error registrando intento de conexión: {e}")


# Singleton global
_manager_instance = None

def get_server_manager() -> ServerConnectionManager:
    """Obtiene la instancia singleton del ServerConnectionManager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ServerConnectionManager()
    return _manager_instance


# Funciones de conveniencia
def get_server_config(server_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper para obtener config de servidor"""
    return get_server_manager().get_server_config(server_id)

def get_safe_server_info(server_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper para obtener info segura (sin password)"""
    return get_server_manager().get_safe_server_info(server_id)
