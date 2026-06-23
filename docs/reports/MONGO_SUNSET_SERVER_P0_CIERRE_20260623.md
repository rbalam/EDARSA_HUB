# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P0 backend/server.py – 23-Jun-2026

## Estado validado

- `backend/server.py` quedó sin runtime Mongo operativo real.
- Validación final:
  - `python3 -m py_compile backend/server.py` = OK.
  - `await db.*` runtime real = 0.
  - `db.*` operativo real = 0.
- Las coincidencias restantes corresponden a comentarios/docstrings históricos de migración.

## Cambios aplicados

- `db.server_status` migrado a `dbo.Servidores_Status`.
- `db.alerts` migrado a `dbo.Alertas_Sistema`.
- `db.users.count_documents` migrado a `dbo.Usuario_Catalogo`.
- `db.script_logs` migrado a `dbo.ConsultasSQL_EjecucionesLog`.
- `db.inventario_diferencias_detalle` migrado a `dbo.Workflow_DetalleDiferencias`.
- `db.solicitudes_catalogos` neutralizado.
- `db.portal_proveedores` neutralizado.
- `db.nomina_*` neutralizado en rutas legacy `/nomina/*`.
- `db.tareas_sistema` neutralizado.
- `db.users.find_one` sustituido por `current_user`.
- `db.sec_roles.find_one` neutralizado.

## Pendientes técnicos

1. `/nomina/*` legacy quedó neutralizado.
   - Ruta canónica funcional identificada: `/rrhh/nominas/flujo`.
   - Pendiente: migrar frontend `frontend/src/pages/Nominas.js` a endpoints `/rrhh/*`.

2. `/sistema/pendientes-unificados`
   - Catálogos/proveedores quedaron neutralizados.
   - Pendiente: mapeo canónico funcional hacia:
     - `CRM_Tareas`
     - `Operativo_TareasCompras`
     - `Proveedor_Catalogo`
     - `Usuario_Autorizaciones`

3. `marcar_tarea_leida`
   - Función detectada sin decorador activo.
   - Frontend llama: `PUT /sistema/tareas/{id}/marcar-leida`.
   - Pendiente: crear endpoint SQL-first o corregir frontend.

4. Helpers SQL nuevos en `backend/server.py`
   - Pendiente posterior: extraer a repositorio SQL central.
   - No hacerlo hasta cerrar estabilidad/import/build.

## Reglas conservadas

- SQL Server como única fuente operativa.
- Cero MongoDB operativo.
- Sin tablas nuevas.
- Sin hardcodes.
- Cambios con backup previo.
- Compilación validada.
