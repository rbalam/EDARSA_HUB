# DICTAMEN FINAL - MONGO CORE

Fecha: 2026-06-04

## Resultado Ejecutivo

P0 MONGO CORE: CERRADO

## Archivos Auditados

### core/db.py
Estado: SEGURO

Hallazgos:
- Contiene funciones Mongo legacy.
- No alimenta endpoints visuales productivos.
- Consumido principalmente por scripts, pruebas, administración y compatibilidad legacy.

Acción:
- Mantener temporalmente.
- No es bloqueo para producción.

---

### core/auth/user_repository_sql.py

Estado: SQL-FIRST

Hallazgos:
- Operación productiva basada en SQL Server.
- Referencias Mongo únicamente para comparación y migración.

Acción:
- Sin cambios requeridos.

---

### core/rbac/middleware.py

Estado: SQL-FIRST OPERATIVO

Hallazgos:
- _get_db() obtiene referencia Mongo legacy.
- El objeto db se propaga hacia RBACService.
- RBACRepository ignora dicho parámetro.
- RBACRepositorySQL ejecuta todas las consultas productivas.

Flujo validado:

middleware
→ RBACService
→ RBACRepository
→ RBACRepositorySQL
→ EDARSAHUB SQL

MongoDB NO participa en autorización productiva.

Acción futura:
- Eliminar _get_db().
- Pasar None explícitamente.
- Refactor cosmético P2.

---

### core/connection_resolver.py

Estado: PENDIENTE P2

Hallazgos:
- Mantiene resolución Mongo para configuraciones.
- No bloquea operación comercial actual.

Acción futura:
- Migrar completamente a Servidores_Conexiones SQL.

---

## Conclusión

Se confirma que:

- Auth productivo = SQL
- RBAC productivo = SQL
- Endpoints visuales = SQL
- Comercial = SQL
- Costos/Márgenes = SQL
- Precios Constantes = SQL

MongoDB ya NO es fuente productiva para operación comercial ni autorización.

Clasificación final:

P0 Mongo Core = CERRADO

Pendientes:

P1 Mongo Operativo
P2 Connection Resolver
P2 Limpieza de código legacy Mongo
