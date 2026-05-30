# =============================================================================
# SNIPPET: CONFIGURACIÓN EMPRESARIAL DE CONNECTION POOL (SQLAlchemy Async)
# OBJETIVO: Evitar errores de conexión agotada y conexiones "zombies"
# =============================================================================

# Guardar/Modificar en el archivo de configuración de base de datos del Backend
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Configuración Empresarial del Connection Pool
# Reemplaza 'DATABASE_URL' por la variable de entorno real de tu base de datos EDARSA HUB
DATABASE_URL = os.environ.get('DATABASE_URL', 'mssql+aioodbc://user:pass@server/database')

engine = create_async_engine(
    DATABASE_URL, 
    pool_size=20,           # Conexiones base disponibles simultáneamente
    max_overflow=10,        # Conexiones extra permitidas en picos de tráfico
    pool_timeout=30,        # Si no hay conexiones, espera 30s antes de fallar (no tira error inmediato)
    pool_pre_ping=True,     # HEALTH CHECK INTERNO: Verifica que la conexión a SQL esté viva antes de usarla
    pool_recycle=1800,      # RECICLAJE: Destruye y recrea conexiones cada 30 mins para evitar conexiones "zombies"
    echo=False              # Desactivar logs de SQL en producción
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# =============================================================================
# DEPENDENCY INJECTION PARA FASTAPI
# =============================================================================
async def get_db_session():
    """
    Genera una sesión de base de datos para inyección de dependencias.
    Uso en FastAPI: db: AsyncSession = Depends(get_db_session)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# =============================================================================
# NOTAS DE CONFIGURACIÓN
# =============================================================================
# pool_size=20: Para un servidor con 4 workers, esto da 80 conexiones totales
# max_overflow=10: Permite hasta 30 conexiones por worker en picos
# pool_pre_ping=True: CRÍTICO - Evita "connection is closed" errors
# pool_recycle=1800: Conexiones se reciclan cada 30 minutos
