# DICTAMEN FINAL — SQL-FIRST / MONGO LEGACY

Fecha: 2026-06-04  
Proyecto: EDARSAHUB

## Estado Ejecutivo

| Frente | Estado | Dictamen |
|---|---|---|
| Auth | CERRADO | Productivo en SQL |
| RBAC | CERRADO | Productivo en SQL |
| Comercial | CERRADO | Endpoints visuales SQL-first |
| Costos/Márgenes | CERRADO | SQL-first |
| Precios Constantes | CERRADO | Migrado a `Sync_Precios_Historicos` |
| Mongo Core | CERRADO | No es fuente productiva visual/auth/RBAC |
| api_connections | CERRADO | SQL-first con Mongo solo como cache auxiliar |
| connection_resolver.py | P2 PENDIENTE | SQL-first mayoritario con fallback Mongo legacy |

## Cierres Validados

### 1. Modal Detalle de Ventas

Endpoint:
`GET /comercial/detalle-movimientos/{server_id}`

Estado:
Migrado a EDARSAHUB SQL usando `Comercial_KPIs_Diarios_v2`.

Validación:
- 130° MÉRIDA
- Junio 2026
- 18 cheques
- 36 PAX
- Fuente SQL

Nota:
El modal muestra agregado diario. Para detalle real por ticket se requiere tabla sincronizada de cheques/comandas.

---

### 2. Precios Constantes

Endpoint:
`GET /comercial/precios-constantes/{server_id}`

Estado:
Migrado a EDARSAHUB SQL usando `Sync_Precios_Historicos`.

Backfill:
5,642 productos.

Distribución:
- ManagmentPro: 1,925
- 130° MÉRIDA: 1,719
- CIENFUEGOS: 1,507
- LA ESTELAR: 491

---

### 3. Endpoints Visuales NO-LIVE

Módulos auditados:
- comercial
- costos_margenes
- compras
- reportes
- explorador_bd
- inventarios
- operaciones

Dictamen:
Los endpoints visuales auditados no consultan servidores LIVE como fuente de datos.

Las consultas LIVE permanecen únicamente en jobs/sync donde son permitidas.

---

### 4. Mongo Core

Archivos auditados:
- `core/db.py`
- `core/auth/user_repository_sql.py`
- `core/rbac/middleware.py`
- `api_connections/repository.py`

Dictamen:
MongoDB no es fuente productiva para:
- autenticación
- autorización
- endpoints visuales comerciales
- precios constantes
- costos/márgenes

---

### 5. RBAC

Flujo validado:

`middleware → RBACService → RBACRepository → RBACRepositorySQL → EDARSAHUB SQL`

MongoDB aparece como parámetro legacy, pero no ejecuta autorización productiva.

Acción futura:
Eliminar `_get_db()` legacy en P2.

---

### 6. api_connections

Dictamen:
SQL-first correcto.

Reglas validadas:
1. Toda escritura va primero a EDARSAHUB SQL.
2. Si EDARSAHUB SQL falla, no se guarda en MongoDB.
3. Si MongoDB falla después de EDARSAHUB SQL, la operación se considera exitosa.
4. MongoDB funciona solo como cache/log auxiliar no autoritativo.

---

## Pendientes P2

### connection_resolver.py

Estado:
SQL-first mayoritario.

Hallazgos:
- 71 referencias SQL.
- 7 referencias Mongo.
- MongoDB se conserva como fallback legacy para configuraciones.

Acción:
Migrar `_get_server_config_mongo()` y `_get_api_config_mongo()` a `Servidores_Conexiones` en SQL Server.

Regla final:
SQL único productivo. MongoDB sin fallback productivo.

---

## Documentos Generados

- `/app/docs/auditorias/DICTAMEN_FINAL_MONGO_CORE_20260604.md`
- `/app/docs/auditorias/AUDITORIA_P1_NO_LIVE_ENDPOINTS_VISUALES_20260604.md`
- `/app/docs/auditorias/AUDITORIA_MONGO_LEGACY_20260604.md`
- `/app/docs/auditorias/AUDITORIA_MONGO_RUTAS_ACTIVAS_20260604.md`
- `/app/docs/auditorias/AUDITORIA_CORE_DB_MONGO_USAGE_20260604.md`
- `/app/docs/auditorias/AUDITORIA_CONNECTION_RESOLVER_SQL_FIRST_20260604.md`

## Estado Final

P0:
- Cerrado.

P1:
- Cerrado para endpoints visuales y comercial.

P2:
- Migración final de `connection_resolver.py`.
- Limpieza de código Mongo legacy.
- Centralización de credenciales.
- Dashboard SQL-First Health.
