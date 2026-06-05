"""
EDARSA HUB - Configuración Central
===================================
Configuración de la aplicación usando variables de entorno.

NOTA: Este archivo es parte del refactor modular.
La configuración actual sigue en server.py hasta que se autorice la migración.

USO FUTURO:
    from core.config import settings
    # print(settings.MONGO_URL)  # P2-07: MongoDB eliminado
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración central de EDARSA HUB.
    Las variables se cargan automáticamente desde .env
    """
    
    # MongoDB
    MONGO_URL: str = ""  # P2-07: MongoDB eliminado
    DB_NAME: str = os.environ.get("DB_NAME", "test_database")
    
    # JWT
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # APIs MPRO Locales (configuración base)
    API_MPRO_KEY: str = os.environ.get("API_MPRO_KEY", "")
    API_MPRO_QRO_URL: str = os.environ.get("API_MPRO_QRO_URL", "")
    API_MPRO_ORIGEN_URL: str = os.environ.get("API_MPRO_ORIGEN_URL", "")
    
    # Timeouts
    SQL_QUERY_TIMEOUT: int = 30
    API_LOCAL_TIMEOUT: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia singleton de configuración
# NO se usa aún - la configuración actual está en server.py
settings = Settings()
