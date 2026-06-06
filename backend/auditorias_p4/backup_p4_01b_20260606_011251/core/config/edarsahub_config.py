"""
EDARSA HUB - Configuración SQL Server Central
=============================================
FUENTE ÚNICA DE VERDAD para credenciales EDARSAHUB SQL.

USO:
    from core.config.edarsahub_config import get_edarsahub_sql_config
    
    cfg = get_edarsahub_sql_config()
    # cfg.host, cfg.port, cfg.database, cfg.user, cfg.password

REGLAS:
1. NUNCA imprimir passwords en logs
2. NUNCA hardcodear credenciales fuera de este archivo
3. Usar variables de entorno con fallback solo aquí
4. Todos los módulos deben importar desde aquí
"""
import os
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class EdarsahubSQLConfig:
    """Configuración de conexión a EDARSAHUB SQL Server."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    def safe_dict(self) -> dict:
        """Retorna config sin password para logging seguro."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": "***REDACTED***"
        }
    
    def connection_string_pyodbc(self) -> str:
        """String de conexión para pyodbc."""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.user};"
            f"PWD={self.password};"
            "TrustServerCertificate=yes;Encrypt=no;"
        )
    
    def connection_dict_pymssql(self) -> dict:
        """Dict de conexión para pymssql."""
        return {
            "server": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }


# Singleton para evitar múltiples lecturas de env
_config: Optional[EdarsahubSQLConfig] = None


def get_edarsahub_sql_config() -> EdarsahubSQLConfig:
    """
    Obtiene la configuración de EDARSAHUB SQL Server.
    Lee de variables de entorno con fallback a valores por defecto.
    
    Variables de entorno:
    - EDARSAHUB_SQL_HOST
    - EDARSAHUB_SQL_PORT
    - EDARSAHUB_SQL_DATABASE
    - EDARSAHUB_SQL_USER
    - EDARSAHUB_SQL_PASSWORD
    """
    global _config
    
    if _config is not None:
        return _config
    
    _config = EdarsahubSQLConfig(
        host=os.environ.get('EDARSAHUB_SQL_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
        port=int(os.environ.get('EDARSAHUB_SQL_PORT', '1433')),
        database=os.environ.get('EDARSAHUB_SQL_DATABASE', 'EDARSAHUB'),
        user=os.environ.get('EDARSAHUB_SQL_USER', '<REDACTED_EDARSAHUB_SQL_USER>'),
        password=os.environ.get('EDARSAHUB_SQL_PASSWORD', '<REDACTED_EDARSAHUB_SQL_PASSWORD>'),
    )
    
    logger.info(f"[EDARSAHUB_CONFIG] Configuración cargada: {_config.safe_dict()}")
    
    return _config


def get_edarsahub_connection_string() -> str:
    """Atajo para obtener string de conexión pyodbc."""
    return get_edarsahub_sql_config().connection_string_pyodbc()


def reset_config():
    """Resetea el singleton (útil para tests)."""
    global _config
    _config = None
