from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Utilidades de Migración MongoDB → SQL Server
=========================================================
Funciones helper para convertir código legacy MongoDB a SQL-First.
Alineado al Canonical Data Model Oficial de EDARSAHUB (Fase 2).

Uso con Google AI Studio / Gemini API.
"""

# ============================================
# MAPEO OFICIAL DE ENTIDADES
# ============================================

MONGO_TO_SQL_MAPPING = {
    # Colección MongoDB → Tabla SQL Server
    "mongo_db.servers": "Servidores_Conexiones",
    "mongo_db.ventas": "Comercial_Ventas_Sync",
    "mongo_db.inventarios": "Compras_Inventarios_Fisicos_Sync",
    "mongo_db.leads": "CRM_Leads",
    "mongo_db.accounts": "CRM_Cuentas",
    "mongo_db.cuentas": "CRM_Cuentas",
    "mongo_db.metas": "Comercial_Metas",
    "mongo_db.kpis_cache": "Comercial_KPIs_Cache",
    "mongo_db.dashboard_cache": "Comercial_Dashboard_Cache",
    "mongo_db.server_status": "Servidores_Status",
    "mongo_db.users": "Usuario_Catalogo",
    "mongo_db.roles": "Usuario_Roles",
    "mongo_db.clientes": "Cliente_Catalogo",
    "mongo_db.cotizaciones": "Venta_Cotizaciones",
    "mongo_db.pedidos": "Venta_Pedidos",
    "mongo_db.remisiones": "Venta_Remisiones",
    "mongo_db.solicitudes_alta": "CRM_ClientesSolicitudesAlta",
}

# ============================================
# SYSTEM PROMPT PARA GEMINI
# ============================================

SYSTEM_PROMPT = """Eres un experto en migración de MongoDB a SQL Server para EDARSA HUB.

ARQUITECTURA OBLIGATORIA:
- SQL-First: EDARSAHUB es la única fuente de verdad
- NO-LIVE: Sin conexiones directas a APIs externas
- MongoDB PROHIBIDO: Todo código debe usar execute_hub_query()

FUNCIÓN PRINCIPAL:
from core.pool import execute_hub_query, execute_hub_query_single, execute_hub_insert
from core.unidades_service import UnidadesService

# SELECT múltiples registros
results = execute_hub_query("SELECT * FROM Tabla WHERE col = %s", (param,))

# SELECT un registro
result = execute_hub_query_single("SELECT * FROM Tabla WHERE id = %s", (id,))

# INSERT/UPDATE/DELETE
execute_hub_insert("INSERT INTO Tabla (col) VALUES (%s)", (valor,))

REGLAS DE CONVERSIÓN:
1. find() → SELECT con execute_hub_query()
2. find_one() → SELECT TOP 1 con execute_hub_query_single()
3. insert_one() → INSERT con execute_hub_insert()
4. update_one() → UPDATE con execute_hub_insert()
5. delete_one() → DELETE con execute_hub_insert()
6. Eliminar async/await - código síncrono
7. Retornar diccionarios limpios (sin ObjectId)

Responde SOLO con código Python funcional."""


def migrar_mongo_a_sql(codigo_mongo: str) -> str:
    """
    Convierte código MongoDB a SQL Server alineado al 
    Canonical Data Model Oficial de EDARSAHUB (Fase 2).
    
    Args:
        codigo_mongo: Código Python con operaciones MongoDB
        
    Returns:
        Código Python convertido a SQL Server
        
    Ejemplo:
        codigo_legacy = '''
        async def get_servers():
            db = get_db()
            return await db.servers.find({"active": True}).to_list(100)
        '''
        
        codigo_sql = migrar_mongo_a_sql(codigo_legacy)
        print(codigo_sql)
        # Output:
        # def get_servers():
        #     return execute_hub_query("SELECT * FROM Servidores_Conexiones WHERE activo = 1")
    """
    import google.generativeai as genai
    
    # Configurar modelo (requiere API key configurada)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""Convierte este código MongoDB a SQL Server usando execute_hub_query():
    
    MAPEADO DE ENTIDADES REALES (EDARSAHUB SQL):
    - mongo_db.servers     → Servidores_Conexiones
    - mongo_db.ventas      → Comercial_Ventas_Sync
    - mongo_db.inventarios → Compras_Inventarios_Fisicos_Sync
    - mongo_db.leads       → CRM_Leads
    - mongo_db.accounts    → CRM_Cuentas
    - mongo_db.metas       → Comercial_Metas

    REQUISITO OBLIGATORIO:
    - Retornar código síncrono estándar de Python.
    - Utilizar execute_hub_query() importada de core.pool.
    - Formatear la salida para entregar diccionarios limpios.
    
    CÓDIGO MONGO A TRANSFORMAR:
    {codigo_mongo}
    """
    
    response = model.generate_content([SYSTEM_PROMPT, prompt])
    return response.text


def generar_query_sql(descripcion: str, tabla: str = None) -> str:
    """
    Genera query SQL optimizada para EDARSAHUB.
    
    Args:
        descripcion: Descripción en lenguaje natural
        tabla: Tabla sugerida (opcional)
    """
    import google.generativeai as genai
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""Genera query SQL para MS SQL Server (EDARSAHUB).

Requisito: {descripcion}
{f'Tabla sugerida: {tabla}' if tabla else ''}

Tablas disponibles:
- Servidores_Conexiones, Servidores_Status
- CRM_Cuentas, CRM_Leads, CRM_ClientesSolicitudesAlta
- Comercial_Ventas_Sync, Comercial_Metas, Comercial_KPIs_Cache
- Compras_Inventarios_Fisicos_Sync
- Venta_Cotizaciones, Venta_Pedidos, Venta_Remisiones
- Usuario_Catalogo, Usuario_Roles
- Unidades_Negocio

Responde SOLO con la query SQL optimizada."""
    
    response = model.generate_content([SYSTEM_PROMPT, prompt])
    return response.text


# ============================================
# CONVERSIONES RÁPIDAS (Sin API)
# ============================================

def convertir_find_to_select(coleccion: str, filtro: dict = None) -> str:
    """Convierte mongo find() a SELECT SQL."""
    tabla = MONGO_TO_SQL_MAPPING.get(f"mongo_db.{coleccion}", coleccion)
    
    if not filtro:
        return f'execute_hub_query("SELECT * FROM {tabla}")'
    
    # Construir WHERE
    conditions = []
    params = []
    for key, value in filtro.items():
        if key == "_id":
            continue
        sql_key = key.replace(".", "_")
        conditions.append(f"{sql_key} = %s")
        params.append(value)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    params_str = ", ".join([f"'{p}'" if isinstance(p, str) else str(p) for p in params])
    
    return f'execute_hub_query("SELECT * FROM {tabla} WHERE {where_clause}", ({params_str},))'


def convertir_insert_to_sql(coleccion: str, documento: dict) -> str:
    """Convierte mongo insert_one() a INSERT SQL."""
    tabla = MONGO_TO_SQL_MAPPING.get(f"mongo_db.{coleccion}", coleccion)
    
    # Filtrar _id
    doc = {k: v for k, v in documento.items() if k != "_id"}
    
    columns = ", ".join(doc.keys())
    placeholders = ", ".join(["%s"] * len(doc))
    values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in doc.values()])
    
    return f'execute_hub_insert("INSERT INTO {tabla} ({columns}) VALUES ({placeholders})", ({values},))'


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Ejemplo de conversión manual
    print("=== Conversión find() → SELECT ===")
    print(convertir_find_to_select("servers", {"active": True}))
    
    print("\n=== Conversión insert() → INSERT ===")
    print(convertir_insert_to_sql("cuentas", {
        "NombreComercial": "Test Corp",
        "RFC": "TCO123456789",
        "UsuarioPropietarioID": 1
    }))
    
    print("\n=== Mapeo de tablas ===")
    for mongo, sql in MONGO_TO_SQL_MAPPING.items():
        print(f"  {mongo} → {sql}")
