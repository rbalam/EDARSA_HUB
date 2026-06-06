# AUDITORÍA — connection_resolver.py SQL-FIRST

Fecha: 2026-06-05 00:29:00

## Referencias Mongo / SQL

- L8 [SQL]: `2. Menú "Servidores SQL" es la fuente oficial de configuración`
- L9 [SQL]: `3. Toda conexión SQL debe resolverse desde esta capa central`
- L14 [SQL]: `- CIENFUEGOS/LA ESTELAR/130 MID → SQL desde menú Servidores`
- L15 [SQL]: `- MPRO (ORIGEN/130 QRO) → Acumulados: SQL MPRO | Ventas del día: API local`
- L53 [SQL]: `SQL = "sql"                                    # Consulta SQL directa`
- L59 [SQL]: `MENU_SERVIDORES_SQL = "menu_servidores_sql"   # Menú oficial de Servidores SQL`
- L60 [SQL]: `MPRO_SQL = "mpro_sql"                         # SQL del servidor MPRO`
- L75 [SQL]: `source_type: SourceType                       # SQL o API`
- L78 [SQL]: `# Datos de conexión SQL`
- L99 [SQL]: `if self.source_type == SourceType.SQL:`
- L135 [SQL]: `"source_type": SourceType.SQL,`
- L136 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L138 [SQL]: `"description": "SQL histórico desde menú Servidores"`
- L141 [SQL]: `"source_type": SourceType.SQL,`
- L142 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L147 [SQL]: `"source_type": SourceType.SQL,`
- L148 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L150 [SQL]: `"description": "Cheques del día desde SQL"`
- L153 [SQL]: `"source_type": SourceType.SQL,`
- L154 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L156 [SQL]: `"description": "SQL histórico comparativo"`
- L159 [SQL]: `"source_type": SourceType.SQL,`
- L160 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L162 [SQL]: `"description": "Proyección basada en SQL histórico"`
- L165 [SQL]: `"source_type": SourceType.SQL,`
- L166 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L171 [SQL]: `"source_type": SourceType.SQL,`
- L172 [SQL]: `"connection_origin": ConnectionOrigin.MENU_SERVIDORES_SQL,`
- L174 [SQL]: `"description": "Inventarios desde SQL"`
- L181 [SQL]: `"source_type": SourceType.SQL,`
- L182 [SQL]: `"connection_origin": ConnectionOrigin.MPRO_SQL,`
- L184 [SQL]: `"description": "SQL MPRO nube - Venta_Encabezado"`
- L199 [SQL]: `"source_type": SourceType.SQL,`
- L200 [SQL]: `"connection_origin": ConnectionOrigin.MPRO_SQL,`
- L202 [SQL]: `"description": "SQL MPRO nube comparativo"`
- L205 [SQL]: `"source_type": SourceType.SQL,`
- L206 [SQL]: `"connection_origin": ConnectionOrigin.MPRO_SQL,`
- L208 [SQL]: `"description": "Proyección basada en SQL MPRO"`
- L211 [SQL]: `"source_type": SourceType.SQL,`
- L212 [SQL]: `"connection_origin": ConnectionOrigin.MPRO_SQL,`
- L217 [SQL]: `"source_type": SourceType.SQL,`
- L218 [SQL]: `"connection_origin": ConnectionOrigin.MPRO_SQL,`
- L220 [SQL]: `"description": "Inventarios desde MPRO SQL"`
- L236 [SQL]: `- Obtener configuración de conexión desde menú Servidores SQL`
- L250 [SQL]: `if source.source_type == SourceType.SQL:`
- L251 [SQL]: `# Usar execute_sql_query con source.host, etc.`
- L274 [MONGO]: `"""Obtiene conexión a MongoDB"""`
- L277 [MONGO]: `from pymongo import MongoClient`
- L279 [MONGO]: `mongo_url = os.environ.get('MONGO_URL')`
- L280 [MONGO]: `client = MongoClient(mongo_url)`
- L283 [MONGO]: `logger.error(f"[ConnectionResolver] Error conectando a MongoDB: {e}")`
- L288 [MONGO]: `"""Obtiene configuración de servidor desde MongoDB (menú Servidores SQL)"""`
- L301 [MONGO]: `"""Obtiene configuración de API local desde MongoDB"""`
- L328 [SQL]: `server_id: UUID del servidor desde menú Servidores SQL`
- L337 [SQL]: `# Obtener configuración del servidor desde menú Servidores SQL`
- L349 [SQL]: `error_message=f"Servidor {server_id} no encontrado en menú Servidores SQL"`
- L389 [SQL]: `if source_type == SourceType.SQL:`
- L437 [SQL]: `# API no configurada - fallback a SQL para métricas que lo soporten`
- L439 [SQL]: `logger.warning(f"[ConnectionResolver] API no disponible para {sucursal_nombre}, `
- L445 [SQL]: `source_type=SourceType.SQL,  # Fallback a SQL`
- L446 [SQL]: `connection_origin=ConnectionOrigin.MPRO_SQL,`
- L527 [SQL]: `Dict con estado de SQL y API (si aplica)`
- L529 [SQL]: `from core.db import execute_sql_query`
- L534 [SQL]: `"sql_status": "unknown",`
- L538 [SQL]: `# Resolver para SQL`
- L539 [SQL]: `sql_source = self.resolve_source(server_id, MetricType.ACCUMULATED_SALES)`
- L541 [SQL]: `if sql_source.is_valid() and sql_source.source_type == SourceType.SQL:`
- L543 [SQL]: `test_result = execute_sql_query(`
- L544 [SQL]: `sql_source.host,`
- L545 [SQL]: `sql_source.port,`
- L546 [SQL]: `sql_source.database_name,`
- L547 [SQL]: `sql_source.username,`
- L548 [SQL]: `sql_source.password,`
- L551 [SQL]: `result["sql_status"] = "ok" if test_result else "no_response"`
- L553 [SQL]: `result["sql_status"] = "error"`
- L554 [SQL]: `result["sql_error"] = str(e)[:200]`
- L556 [SQL]: `result["sql_status"] = "not_configured"`
- L594 [SQL]: `result = execute_sql_query(source.host, source.port, ...)`

**Total Mongo refs: 7 | Total SQL refs: 71**

## Funciones / Clases

- L34: `class SystemType(Enum):`
- L40: `class MetricType(Enum):`
- L51: `class SourceType(Enum):`
- L57: `class ConnectionOrigin(Enum):`
- L69: `class ResolvedSource:`
- L230: `class ConnectionResolver:`
- L567: `def get_connection_resolver() -> ConnectionResolver:`
- L575: `def resolve_source(`
- L599: `def get_resolution_matrix() -> Dict[str, Any]:`

## Consumidores del resolver

- `backend/scripts/audit_auth_rbac_mongo.py` L6: `"/app/backend/core/connection_resolver.py",`
- `backend/scripts/audit_connection_resolver_sql_first.py` L6: `TARGET = ROOT / "backend/core/connection_resolver.py"`
- `backend/scripts/audit_connection_resolver_sql_first.py` L13: `md.append("# AUDITORÍA — connection_resolver.py SQL-FIRST\n\n")`
- `backend/scripts/audit_connection_resolver_sql_first.py` L43: `if "connection_resolver" in t or "ConnectionResolver" in t:`
- `backend/scripts/audit_connection_resolver_sql_first.py` L45: `if "connection_resolver" in line or "ConnectionResolver" in line:`
- `backend/core/__init__.py` L9: `# - connection_resolver.py: Resolver centralizado de conexiones (NUEVO`
- `backend/core/__init__.py` L19: `# - ConnectionResolver: Resolver central - TODOS los módulos deben usa`
- `backend/core/__init__.py` L65: `from core.connection_resolver import (`
- `backend/core/__init__.py` L66: `ConnectionResolver,`
- `backend/core/__init__.py` L73: `get_connection_resolver`
- `backend/core/regression_checker.py` L219: `from core.connection_resolver import get_resolution_matrix`
- `backend/core/regression_checker.py` L330: `from core.connection_resolver import (`
- `backend/core/regression_checker.py` L331: `get_connection_resolver,`
- `backend/core/regression_checker.py` L335: `resolver = get_connection_resolver()`
- `backend/core/regression_checker.py` L344: `message="ConnectionResolver no inicializado",`
- `backend/core/regression_checker.py` L353: `message="ConnectionResolver operativo",`
- `backend/core/regression_checker.py` L364: `message=f"No se puede importar ConnectionResolver: {str(e)[:200]}",`
- `backend/core/centro_control/routes.py` L320: `- ConnectionResolver no operativo`
- `backend/core/centro_control/routes.py` L565: `from core.connection_resolver import get_resolution_matrix`

**Total consumidores: 19**

## Dictamen

⚠️ **MIXTO**: Tiene referencias Mongo legacy. Evaluar si son productivas o fallback.
