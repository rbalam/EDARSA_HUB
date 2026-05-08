"""
EDARSA HUB - SQL Server Connection Pool
=======================================
Capa centralizada de connection pooling para SQL Server.

PRIORIDAD 1 DEL REFACTOR (Abril 2026)

OBJETIVOS:
- Eliminar overhead de 100-500ms por conexión
- Reutilizar conexiones existentes
- Manejar múltiples servidores SQL configurados
- Logging claro para diagnóstico
- Cierre seguro de conexiones

ARQUITECTURA:
    ┌─────────────────────────────────────────────┐
    │              ConnectionPoolManager           │
    │  (Singleton - administra todos los pools)    │
    ├─────────────────────────────────────────────┤
    │  Pool "server_1"  │  Pool "server_2"  │ ... │
    │  [conn][conn]     │  [conn][conn]     │     │
    └─────────────────────────────────────────────┘

USO:
    from core.pool import get_connection, release_connection
    
    # Obtener conexión del pool
    conn = get_connection(server_config)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
    finally:
        release_connection(server_config, conn)

    # O usar el context manager
    with pooled_connection(server_config) as conn:
        cursor = conn.cursor()
        ...

COMPATIBILIDAD:
- execute_sql_query() usa internamente este pool
- Todos los módulos existentes siguen funcionando sin cambios
"""

import os
import logging
import threading
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from contextlib import contextmanager
from dataclasses import dataclass, field

# Drivers SQL Server
import pymssql
import pytds

# Pool management
from dbutils.pooled_db import PooledDB


# =============================================================================
# CONFIGURACIÓN DEL POOL
# =============================================================================

@dataclass
class PoolConfig:
    """
    Configuración para un pool de conexiones SQL Server.
    
    RESILIENTE (Abril 2026):
    - Timeouts incrementados para servidores remotos con latencia
    - Compatible con reintentos automáticos en capa superior
    - Health check habilitado por defecto
    """
    # Tamaño del pool
    min_connections: int = 1      # Conexiones mínimas mantenidas
    max_connections: int = 10     # Conexiones máximas permitidas
    max_shared: int = 3           # Cuántas veces se puede compartir una conexión
    
    # Timeouts RESILIENTES (incrementados para servidor remoto)
    connection_timeout: int = 30   # Timeout para establecer conexión (antes: 15s)
    query_timeout: int = 90        # Timeout para queries (antes: 45s)
    blocking_timeout: int = 45     # Tiempo de espera si pool está lleno (antes: 30s)
    
    # Mantenimiento
    max_usage: int = 0            # Máximo de usos por conexión (0 = ilimitado)
    max_idle_time: int = 600      # Tiempo máximo de inactividad (10 min)
    ping_check: bool = True       # Verificar conexión antes de usar


# Configuración por defecto
DEFAULT_POOL_CONFIG = PoolConfig()


# =============================================================================
# POOL MANAGER - SINGLETON
# =============================================================================

# Contextos de aislamiento disponibles
POOL_CONTEXT_WEB = "web"       # Para endpoints HTTP/API
POOL_CONTEXT_JOBS = "jobs"     # Para scheduler/jobs de fondo
POOL_CONTEXTS = [POOL_CONTEXT_WEB, POOL_CONTEXT_JOBS]


class ConnectionPoolManager:
    """
    Administrador centralizado de pools de conexiones SQL Server.
    
    Patrón Singleton - una sola instancia global.
    
    AISLAMIENTO POR CONTEXTO (Abril 2026):
    - Pools separados por contexto: "web" vs "jobs"
    - Si un job corrompe su conexión, NO afecta a endpoints web
    - Cada servidor SQL tiene pools independientes por contexto
    
    ARQUITECTURA:
        ┌─────────────────────────────────────────────────────────────┐
        │              ConnectionPoolManager (SINGLETON)               │
        ├─────────────────────────────────────────────────────────────┤
        │                                                              │
        │   context="web"                 context="jobs"               │
        │   ┌────────────────────┐       ┌────────────────────┐       │
        │   │ 54.39...:CENTRAL   │       │ 54.39...:CENTRAL   │       │
        │   │ [conn][conn][conn] │       │ [conn][conn]       │       │
        │   └────────────────────┘       └────────────────────┘       │
        │                                                              │
        └─────────────────────────────────────────────────────────────┘
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Pools organizados por contexto
        # Estructura: { "web": { pool_key: PooledDB }, "jobs": { pool_key: PooledDB } }
        self._pools: Dict[str, Dict[str, PooledDB]] = {ctx: {} for ctx in POOL_CONTEXTS}
        self._pool_configs: Dict[str, Dict[str, PoolConfig]] = {ctx: {} for ctx in POOL_CONTEXTS}
        self._pool_stats: Dict[str, Dict[str, Dict[str, Any]]] = {ctx: {} for ctx in POOL_CONTEXTS}
        self._driver_preference: Dict[str, Dict[str, str]] = {ctx: {} for ctx in POOL_CONTEXTS}
        self._pool_lock = threading.Lock()
        self._initialized = True
        
        logging.info("ConnectionPoolManager inicializado con aislamiento por contexto (web/jobs)")
    
    def _generate_pool_key(self, host: str, port: int, database: str) -> str:
        """Genera una clave única para identificar un pool (sin contexto)"""
        return f"{host}:{port}/{database}"
    
    def _create_pymssql_pool(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        config: PoolConfig,
        instance: str = None
    ) -> PooledDB:
        """Crea un pool usando pymssql como driver"""
        server_string = f"{host}\\{instance}" if instance else host
        
        logging.info(f"Creando pool pymssql para {server_string}:{port}/{database}")
        
        return PooledDB(
            creator=pymssql,
            mincached=config.min_connections,
            maxcached=config.max_connections,
            maxshared=config.max_shared,
            maxconnections=config.max_connections,
            blocking=True,
            maxusage=config.max_usage if config.max_usage > 0 else None,
            setsession=None,
            ping=1 if config.ping_check else 0,
            # Parámetros de conexión pymssql
            server=server_string,
            port=port,
            user=username,
            password=password,
            database=database,
            timeout=config.query_timeout,
            login_timeout=config.connection_timeout,
            charset='UTF-8',
            autocommit=True  # CRÍTICO: UPDATEs se commitean automáticamente
        )
    
    def _create_pytds_pool(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        config: PoolConfig
    ) -> PooledDB:
        """Crea un pool usando pytds como driver"""
        logging.info(f"Creando pool pytds para {host}:{port}/{database}")
        
        return PooledDB(
            creator=pytds,
            mincached=config.min_connections,
            maxcached=config.max_connections,
            maxshared=config.max_shared,
            maxconnections=config.max_connections,
            blocking=True,
            maxusage=config.max_usage if config.max_usage > 0 else None,
            setsession=None,
            ping=0,  # pytds no soporta ping nativo
            # Parámetros de conexión pytds
            server=host,
            port=port,
            user=username,
            password=password,
            database=database,
            timeout=config.query_timeout,
            login_timeout=config.connection_timeout,
            autocommit=True  # CRÍTICO: UPDATEs se commitean automáticamente
        )
    
    def get_or_create_pool(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        instance: str = None,
        config: PoolConfig = None,
        context: str = POOL_CONTEXT_WEB
    ) -> PooledDB:
        """
        Obtiene un pool existente o crea uno nuevo para el contexto especificado.
        
        AISLAMIENTO (Abril 2026): Pools separados por contexto.
        
        Args:
            host: Hostname del servidor
            port: Puerto
            database: Base de datos
            username: Usuario
            password: Contraseña
            instance: Instancia SQL (opcional)
            config: Configuración del pool (usa default si no se especifica)
            context: Contexto de aislamiento ("web" o "jobs")
            
        Returns:
            PooledDB configurado para el contexto
        """
        # Validar contexto
        if context not in POOL_CONTEXTS:
            logging.warning(f"Contexto inválido '{context}', usando 'web'")
            context = POOL_CONTEXT_WEB
        
        pool_key = self._generate_pool_key(host, port, database)
        
        # Verificar si ya existe en el contexto
        if pool_key in self._pools[context]:
            return self._pools[context][pool_key]
        
        with self._pool_lock:
            # Double-check dentro del lock
            if pool_key in self._pools[context]:
                return self._pools[context][pool_key]
            
            config = config or DEFAULT_POOL_CONFIG
            
            # CORRECCIÓN 2026-04-29: Usar pymssql primero porque pytds tiene bug
            # con ciertas configuraciones de SQL Server que devuelve datos incorrectos.
            # El bug fue detectado cuando pytds devolvía 2 facturas/$5,500 pero
            # pymssql directo devolvía correctamente 398 facturas/$2,911,864.47
            
            # Intentar primero con pymssql (más confiable)
            try:
                pool = self._create_pymssql_pool(
                    host, port, database, username, password, config, instance
                )
                # Test de conexión
                test_conn = pool.connection()
                test_conn.close()
                
                self._pools[context][pool_key] = pool
                self._pool_configs[context][pool_key] = config
                self._driver_preference[context][pool_key] = "pymssql"
                self._pool_stats[context][pool_key] = {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "driver": "pymssql",
                    "context": context,
                    "connections_served": 0,
                    "errors": 0
                }
                logging.info(f"Pool pymssql [{context}] creado para {pool_key}")
                return pool
                
            except Exception as pymssql_error:
                logging.warning(f"pymssql pool [{context}] falló para {pool_key}: {pymssql_error}")
            
            # Fallback a pytds (solo si pymssql falla)
            try:
                pool = self._create_pytds_pool(
                    host, port, database, username, password, config
                )
                # Test de conexión
                test_conn = pool.connection()
                test_conn.close()
                
                self._pools[context][pool_key] = pool
                self._pool_configs[context][pool_key] = config
                self._driver_preference[context][pool_key] = "pytds"
                self._pool_stats[context][pool_key] = {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "driver": "pytds",
                    "context": context,
                    "connections_served": 0,
                    "errors": 0
                }
                logging.info(f"Pool pytds [{context}] (fallback) creado para {pool_key}")
                return pool
                
            except Exception as pytds_error:
                logging.error(f"No se pudo crear pool [{context}] para {pool_key}: {pytds_error}")
                raise ConnectionError(f"No se pudo crear pool [{context}] para {pool_key}")
    
    def get_connection(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        instance: str = None,
        context: str = POOL_CONTEXT_WEB
    ):
        """
        Obtiene una conexión del pool para el contexto especificado.
        
        AISLAMIENTO (Abril 2026): Usa pool separado según contexto.
        
        Args:
            context: "web" para endpoints, "jobs" para scheduler
        
        Returns:
            Conexión del pool (debe ser liberada con close())
        """
        # Validar contexto
        if context not in POOL_CONTEXTS:
            context = POOL_CONTEXT_WEB
            
        pool_key = self._generate_pool_key(host, port, database)
        
        try:
            pool = self.get_or_create_pool(
                host, port, database, username, password, instance, context=context
            )
            conn = pool.connection()
            
            # Actualizar stats
            if pool_key in self._pool_stats[context]:
                self._pool_stats[context][pool_key]["connections_served"] += 1
                self._pool_stats[context][pool_key]["last_used"] = datetime.now(timezone.utc).isoformat()
            
            logging.debug(f"Conexión [{context}] obtenida del pool {pool_key}")
            return conn
            
        except Exception as e:
            if pool_key in self._pool_stats[context]:
                self._pool_stats[context][pool_key]["errors"] += 1
            logging.error(f"Error obteniendo conexión [{context}] del pool {pool_key}: {e}")
            raise
    
    def close_pool(self, host: str, port: int, database: str, context: str = None) -> bool:
        """
        Cierra un pool específico y libera todas sus conexiones.
        
        Args:
            context: Si se especifica, cierra solo ese contexto. Si es None, cierra ambos.
        
        Returns:
            True si se cerró exitosamente
        """
        pool_key = self._generate_pool_key(host, port, database)
        contexts_to_close = [context] if context else POOL_CONTEXTS
        closed_any = False
        
        with self._pool_lock:
            for ctx in contexts_to_close:
                if ctx not in POOL_CONTEXTS:
                    continue
                if pool_key in self._pools[ctx]:
                    try:
                        self._pools[ctx][pool_key].close()
                        del self._pools[ctx][pool_key]
                        if pool_key in self._pool_configs[ctx]:
                            del self._pool_configs[ctx][pool_key]
                        if pool_key in self._driver_preference[ctx]:
                            del self._driver_preference[ctx][pool_key]
                        logging.info(f"Pool [{ctx}] {pool_key} cerrado")
                        closed_any = True
                    except Exception as e:
                        logging.error(f"Error cerrando pool [{ctx}] {pool_key}: {e}")
        return closed_any
    
    def close_all_pools(self, context: str = None):
        """
        Cierra todos los pools activos.
        
        Args:
            context: Si se especifica, cierra solo pools de ese contexto.
        """
        contexts_to_close = [context] if context else POOL_CONTEXTS
        
        with self._pool_lock:
            for ctx in contexts_to_close:
                if ctx not in POOL_CONTEXTS:
                    continue
                for pool_key, pool in list(self._pools[ctx].items()):
                    try:
                        pool.close()
                        logging.info(f"Pool [{ctx}] {pool_key} cerrado")
                    except Exception as e:
                        logging.error(f"Error cerrando pool [{ctx}] {pool_key}: {e}")
                self._pools[ctx].clear()
                self._pool_configs[ctx].clear()
                self._driver_preference[ctx].clear()
        logging.info(f"Pools cerrados para contextos: {contexts_to_close}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de todos los pools por contexto.
        
        Returns:
            Dict con estadísticas organizadas por contexto
        """
        stats = {
            "contexts": {}
        }
        
        total_pools = 0
        for ctx in POOL_CONTEXTS:
            ctx_stats = {
                "total_pools": len(self._pools[ctx]),
                "pools": {}
            }
            for pool_key in self._pools[ctx]:
                pool_stat = self._pool_stats[ctx].get(pool_key, {}).copy()
                pool_stat["driver"] = self._driver_preference[ctx].get(pool_key, "unknown")
                ctx_stats["pools"][pool_key] = pool_stat
            stats["contexts"][ctx] = ctx_stats
            total_pools += ctx_stats["total_pools"]
        
        stats["total_pools"] = total_pools
        return stats
    
    def get_pool_driver(self, host: str, port: int, database: str, context: str = POOL_CONTEXT_WEB) -> Optional[str]:
        """Obtiene el driver usado por un pool específico en un contexto"""
        if context not in POOL_CONTEXTS:
            context = POOL_CONTEXT_WEB
        pool_key = self._generate_pool_key(host, port, database)
        return self._driver_preference[context].get(pool_key)


# =============================================================================
# INSTANCIA GLOBAL DEL POOL MANAGER
# =============================================================================

_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Obtiene la instancia singleton del pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


# =============================================================================
# FUNCIONES DE CONVENIENCIA (API PÚBLICA)
# =============================================================================

def get_connection(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    instance: str = None,
    context: str = POOL_CONTEXT_WEB
):
    """
    Obtiene una conexión del pool centralizado para el contexto especificado.
    
    IMPORTANTE: La conexión debe ser cerrada con conn.close() 
    para devolverla al pool.
    
    AISLAMIENTO (Abril 2026): Usar context="jobs" para schedulers/jobs.
    
    Args:
        host: Hostname del servidor
        port: Puerto
        database: Base de datos
        username: Usuario
        password: Contraseña
        instance: Instancia SQL (opcional)
        context: "web" (default) o "jobs" para aislamiento
        
    Returns:
        Conexión SQL Server
    """
    return get_pool_manager().get_connection(
        host, port, database, username, password, instance, context=context
    )


@contextmanager
def pooled_connection(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    instance: str = None,
    context: str = POOL_CONTEXT_WEB
):
    """
    Context manager para obtener y liberar conexiones automáticamente.
    
    AISLAMIENTO (Abril 2026): Usar context="jobs" para schedulers/jobs.
    
    Uso:
        with pooled_connection(host, port, db, user, pwd) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
    
        # Para jobs de fondo:
        with pooled_connection(host, port, db, user, pwd, context="jobs") as conn:
            ...
    
    La conexión se devuelve automáticamente al pool al salir del bloque.
    """
    conn = None
    try:
        conn = get_connection(host, port, database, username, password, instance, context=context)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logging.warning(f"Error cerrando conexión [{context}]: {e}")


def get_pool_statistics() -> Dict[str, Any]:
    """
    Obtiene estadísticas de todos los pools de conexiones.
    
    Returns:
        Dict con estadísticas globales y por pool
    """
    return get_pool_manager().get_pool_stats()


def close_all_pools():
    """
    Cierra todos los pools de conexiones.
    Útil para shutdown limpio de la aplicación.
    """
    get_pool_manager().close_all_pools()


def configure_pool(
    host: str,
    port: int,
    database: str,
    config: PoolConfig
):
    """
    Pre-configura un pool con settings específicos antes de usarlo.
    
    Args:
        host: Hostname
        port: Puerto
        database: Base de datos
        config: Configuración personalizada del pool
    """
    manager = get_pool_manager()
    pool_key = manager._generate_pool_key(host, port, database)
    manager._pool_configs[pool_key] = config
    logging.info(f"Pool {pool_key} pre-configurado")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Clases
    'PoolConfig',
    'ConnectionPoolManager',
    
    # Funciones principales
    'get_connection',
    'pooled_connection',
    'get_pool_statistics',
    'close_all_pools',
    'configure_pool',
    
    # Singleton
    'get_pool_manager',
    
    # Constantes
    'DEFAULT_POOL_CONFIG',
    
    # Contextos de aislamiento (Abril 2026)
    'POOL_CONTEXT_WEB',
    'POOL_CONTEXT_JOBS',
    'POOL_CONTEXTS',
]
