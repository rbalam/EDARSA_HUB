# EDARSA HUB - Core Module
# ========================
# Módulo central con configuración, conexiones y utilidades compartidas
# 
# COMPONENTES:
# - db.py: Conexiones SQL Server, execute_sql_query()
# - security.py: JWT, autenticación, get_current_user()
# - cerebro.py: MODELOS DE DATOS, ENUMS, CONSTANTES (FUENTE DE VERDAD)
# - exceptions.py: Excepciones personalizadas
# - utils.py: Utilidades compartidas
#
# REGLA DE NEGOCIO:
# Todo el conocimiento del sistema está centralizado en cerebro.py
# Este es el CEREBRO de EDARSA HUB - la única fuente de verdad.

__version__ = "1.0.0"

# Exports principales
from core.cerebro import (
    # Enums
    SystemType,
    RoleName,
    EstatusGeneral,
    EstatusTarea,
    PrioridadTarea,
    TipoTarea,
    EtapaNomina,
    TipoNomina,
    CategoriaIncidencia,
    EstatusProveedor,
    EstadoScript,
    
    # Constantes
    MODULOS_DISPONIBLES,
    SQL_TIMEOUT_DEFAULT,
    SQL_TIMEOUT_API_LOCAL,
    TIMEZONE_MEXICO,
    HORA_REPLICA_DEFAULT,
    JWT_ALGORITHM,
    
    # Modelos principales
    UserInDB,
    Role,
    Server,
    ServerStatus,
    KPIsCache,
    
    # Mapeos
    MONGODB_COLLECTIONS,
    MONGODB_INDEXES,
    
    # Validaciones
    validar_rfc,
    validar_clabe,
    validar_email_corporativo,
)

