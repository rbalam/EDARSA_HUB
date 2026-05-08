# P1-FETCH-MIGRATION - DIAGNÓSTICO
## Migración de Fetch Directo a api.js Centralizado

**Fecha:** 2025-12-27  
**Estado:** EN PROGRESO  
**Objetivo:** Migrar 12 archivos de `fetch` directo a `api.js`

---

## 1. RESUMEN DE ARCHIVOS

| # | Archivo | Fetch Calls | Tipo Principal |
|---|---------|-------------|----------------|
| 1 | Catalogos.js | 6 | GET, POST |
| 2 | Finanzas.js | 8 | GET, POST, PUT |
| 3 | ImportadorRH.js | 11 | GET, POST, PUT, DELETE |
| 4 | MisTareas.js | 12 | GET, POST, PUT |
| 5 | Nominas.js | 6 | GET, POST |
| 6 | Proveedores.js | 5 | GET, POST |
| 7 | RecursosHumanos.js | 19 | GET, POST, PUT, DELETE, Blob |
| 8 | Usuarios.js | 13 | GET, POST, PUT |
| 9 | AuditoriasProgramadas.jsx | 2 | POST, GET |
| 10 | CentroControl.jsx | 9 | GET, POST, PUT, DELETE |
| 11 | ConfigAsignaciones.jsx | 9 | GET, POST, PUT |
| 12 | Scheduler.jsx | 5 | GET, POST |

**Total:** 105 fetch calls a migrar

---

## 2. DIAGNÓSTICO POR ARCHIVO

### 2.1 Catalogos.js (6 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 107 | /api/catalogos/dominios | GET | JSON | BAJO | Migrar a api.get() |
| 2 | 138 | /api/catalogos/{dominio}/{tabla} | GET | JSON | BAJO | Migrar a api.get() |
| 3 | 187 | /api/catalogos/{dominio}/{tabla}/{id} | GET | JSON | BAJO | Migrar a api.get() |
| 4 | 218 | /api/catalogos/{dominio}/{tabla}/{id} | PUT | JSON | BAJO | Migrar a api.put() |
| 5 | 242 | /api/catalogos/admin/verificar-tablas | GET | JSON | BAJO | Migrar a api.get() |
| 6 | 259 | /api/catalogos/admin/crear-tablas | POST | JSON | BAJO | Migrar a api.post() |

### 2.2 Finanzas.js (8 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 300 | Dinámico (variable endpoint) | GET | JSON | MEDIO | Migrar con cuidado |
| 2 | 477 | /api/finanzas/cuentas-por-pagar/{id}/decision-pago | PUT | JSON | BAJO | Migrar a api.put() |
| 3 | 585 | /api/finanzas/cuentas-por-pagar/decision-pago-masivo | POST | JSON | BAJO | Migrar a api.post() |
| 4 | 627 | /api/finanzas/cuentas-por-pagar/decision-pago-masivo | POST | JSON | BAJO | Migrar a api.post() |
| 5 | 711 | /api/finanzas/ingresos/cortes-caja/{id}/deposito-efectivo | POST | JSON | BAJO | Migrar a api.post() |
| 6 | 735 | /api/finanzas/ingresos/cortes-caja/{id}/deposito-tarjetas | POST | JSON | BAJO | Migrar a api.post() |
| 7 | 821 | Dinámico | GET | JSON | MEDIO | Migrar con cuidado |
| 8 | 848 | /api/finanzas/presupuestos/{id} | PUT | JSON | BAJO | Migrar a api.put() |

### 2.3 ImportadorRH.js (11 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 48 | /api/rrhh/importar/staging/estadisticas | GET | JSON | BAJO | Migrar |
| 2 | 64 | /api/rrhh/importar/staging/pendientes | GET | JSON | BAJO | Migrar |
| 3 | 82 | /api/rrhh/importar/staging/incompletos | GET | JSON | BAJO | Migrar |
| 4 | 99 | /api/rrhh/importar/staging/excluidos | GET | JSON | BAJO | Migrar |
| 5 | 129 | /api/rrhh/importar/homologacion/estadisticas | GET | JSON | BAJO | Migrar |
| 6 | 144 | /api/rrhh/importar/homologacion/equivalencias | GET | JSON | BAJO | Migrar |
| 7 | 161 | /api/rrhh/importar/homologacion/ejecutar | POST | JSON | BAJO | Migrar |
| 8 | 186 | /api/rrhh/importar/staging/aprobar/{id} | POST | JSON | BAJO | Migrar |
| 9 | 211 | /api/rrhh/importar/staging/{id}/actualizar | PUT | JSON | BAJO | Migrar |
| 10 | 241 | /api/rrhh/importar/staging/{id}/excluir | PUT | JSON | BAJO | Migrar |
| 11 | 270 | /api/rrhh/importar/staging/{id}/restaurar | PUT | JSON | BAJO | Migrar |

### 2.4 MisTareas.js (12 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 100 | Dinámico | GET | JSON | MEDIO | Migrar |
| 2 | 183 | /api/portal/admin/all-suppliers | GET | JSON | BAJO | Migrar |
| 3 | 198 | /api/servers | GET | JSON | BAJO | Migrar |
| 4 | 239 | /api/sistema/solicitudes | GET | JSON | BAJO | Migrar |
| 5 | 279 | /api/sistema/solicitudes/{id}/aprobar | POST | JSON | BAJO | Migrar |
| 6 | 314 | /api/sistema/solicitudes/{id}/rechazar | POST | JSON | BAJO | Migrar |
| 7 | 347 | /api/sistema/permisos-catalogos | GET | JSON | BAJO | Migrar |
| 8 | 405 | /api/sistema/solicitudes/{id}/corregir | POST | JSON | BAJO | Migrar |
| 9 | 428 | /api/sistema/catalogos/{id}/niveles | GET | JSON | BAJO | Migrar |
| 10 | 447 | /api/sistema/tareas/{id}/marcar-leida | PUT | JSON | BAJO | Migrar |
| 11 | 651 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |
| 12 | 685 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |

### 2.5 Nominas.js (6 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 106 | Dinámico | GET | JSON | MEDIO | Migrar |
| 2 | 187 | /api/nomina/ciclos | GET | JSON | BAJO | Migrar |
| 3 | 229 | /api/nomina/ciclos/{id}/avanzar | POST | JSON | BAJO | Migrar |
| 4 | 270 | /api/nomina/ciclos/{id}/rechazar | POST | JSON | BAJO | Migrar |
| 5 | 306 | /api/nomina/configuracion | GET | JSON | BAJO | Migrar |
| 6 | 348 | /api/nomina/ciclos/{id}/movimientos | GET | JSON | BAJO | Migrar |

### 2.6 Proveedores.js (5 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 40 | /api/portal/admin/all-suppliers | GET | JSON | BAJO | Migrar |
| 2 | 62 | /api/servers | GET | JSON | BAJO | Migrar |
| 3 | 79 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |
| 4 | 112 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |
| 5 | 158 | /api/portal/admin/reset-password | POST | JSON | BAJO | Migrar |

### 2.7 RecursosHumanos.js (19 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 234 | Dinámico | GET | JSON | MEDIO | Migrar |
| 2 | 393 | /api/nomina/ciclos | GET | JSON | BAJO | Migrar |
| 3 | 418 | /api/nomina/ciclos/{id}/avanzar | POST | JSON | BAJO | Migrar |
| 4 | 443 | /api/nomina/ciclos/{id}/rechazar | POST | JSON | BAJO | Migrar |
| 5 | 475 | /api/nomina/configuracion | GET | JSON | BAJO | Migrar |
| 6 | 521 | Dinámico | GET | JSON | MEDIO | Migrar |
| 7 | 668 | /api/rrhh/incidencias | POST | JSON | BAJO | Migrar |
| 8 | 823 | Dinámico | POST/PUT | JSON | MEDIO | Migrar |
| 9 | 857 | /api/rrhh/catalogos/puestos/{id} | DELETE | JSON | BAJO | Migrar |
| 10 | 924 | Dinámico | POST/PUT | JSON | MEDIO | Migrar |
| 11 | 958 | /api/rrhh/catalogos/tipos-incidencias/{id} | DELETE | JSON | BAJO | Migrar |
| 12 | 1023 | Dinámico | POST/PUT | JSON | MEDIO | Migrar |
| 13 | 1065 | /api/rrhh/colaboradores/{id} | PUT | JSON | BAJO | Migrar |
| 14 | 1101 | /api/rrhh/incidencias | POST | JSON | BAJO | Migrar |
| 15 | 1164 | /api/rrhh/incidencias/plantilla-excel | GET | **BLOB** | ALTO | Conservar fetch + responseType |
| 16 | 1201 | /api/rrhh/incidencias/importar-excel | POST | **FormData** | ALTO | Migrar con cuidado |
| 17 | 1379 | Dinámico | POST/PUT | JSON | MEDIO | Migrar |
| 18 | 1419 | /api/rrhh/candidatos | POST | JSON | BAJO | Migrar |
| 19 | 1442 | /api/rrhh/candidatos/{id} | DELETE | JSON | BAJO | Migrar |

### 2.8 Usuarios.js (13 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 135 | /api/sistema/estructura-organizacional | GET | JSON | BAJO | Migrar |
| 2 | 138 | /api/sistema/mapeo-servidores | GET | JSON | BAJO | Migrar |
| 3 | 174 | /api/portal/admin/all-suppliers | GET | JSON | BAJO | Migrar |
| 4 | 201 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |
| 5 | 236 | /api/portal/admin/approve-supplier | POST | JSON | BAJO | Migrar |
| 6 | 291 | /api/sistema/usuarios-asignables | GET | JSON | BAJO | Migrar |
| 7 | 305 | /api/sistema/catalogos-disponibles | GET | JSON | BAJO | Migrar |
| 8 | 331 | /api/sistema/permisos-catalogos | GET | JSON | BAJO | Migrar |
| 9 | 357 | /api/sistema/catalogos/{id}/niveles | GET | JSON | BAJO | Migrar |
| 10 | 785 | /api/admin/permisos/asignar | POST | JSON | BAJO | Migrar |
| 11 | 816 | /api/admin/roles/asignar | POST | JSON | BAJO | Migrar |
| 12 | 847 | /api/admin/perfiles/asignar | POST | JSON | BAJO | Migrar |
| 13 | 877 | /api/admin/perfiles/retirar | POST | JSON | BAJO | Migrar |

### 2.9 AuditoriasProgramadas.jsx (2 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 226 | /api/v2/auditorias-programadas/{id}/{action} | POST | JSON | BAJO | Migrar |
| 2 | 258 | Dinámico | GET | JSON | BAJO | Migrar |

### 2.10 CentroControl.jsx (9 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 137 | /api/centro-control/regresiones | GET | JSON | BAJO | Migrar |
| 2 | 157 | /api/centro-control/alertas/acknowledge | POST | JSON | BAJO | Migrar |
| 3 | 185 | /api/centro-control/destinatarios | GET | JSON | BAJO | Migrar |
| 4 | 201 | /api/notificaciones/config | GET | JSON | BAJO | Migrar |
| 5 | 224 | /api/centro-control/destinatarios | POST | JSON | BAJO | Migrar |
| 6 | 246 | /api/centro-control/destinatarios/{id} | PUT | JSON | BAJO | Migrar |
| 7 | 265 | /api/centro-control/destinatarios/{id} | DELETE | JSON | BAJO | Migrar |
| 8 | 287 | /api/centro-control/notificaciones/email/test | POST | JSON | BAJO | Migrar |
| 9 | 315 | /api/centro-control/notificaciones/whatsapp/test | POST | JSON | BAJO | Migrar |

### 2.11 ConfigAsignaciones.jsx (9 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 159 | /api/unidades-negocio | GET | JSON | BAJO | Migrar |
| 2 | 184 | /api/centro-control/jobs | GET | JSON | BAJO | Migrar |
| 3 | 201 | /api/config-asignaciones | GET | JSON | BAJO | Migrar |
| 4 | 249 | /api/users | GET | JSON | BAJO | Migrar |
| 5 | 265 | /api/servers/{id}/sucursales | GET | JSON | BAJO | Migrar |
| 6 | 296 | /api/servers/{id}/departamentos | GET | JSON | BAJO | Migrar |
| 7 | 655 | /api/config-asignaciones/{id} | PUT | JSON | BAJO | Migrar |
| 8 | 703 | /api/config-asignaciones | POST | JSON | BAJO | Migrar |
| 9 | 775 | /api/config-asignaciones/{id} | DELETE | JSON | BAJO | Migrar |

### 2.12 Scheduler.jsx (5 fetch)

| # | Línea | Endpoint | Método | Tipo | Riesgo | Estrategia |
|---|-------|----------|--------|------|--------|------------|
| 1 | 222 | /api/v2/scheduler/status | GET | JSON | BAJO | Migrar |
| 2 | 237 | /api/v2/scheduler/config | GET | JSON | BAJO | Migrar |
| 3 | 259 | /api/v2/scheduler/logs | GET | JSON | BAJO | Migrar |
| 4 | 274 | /api/v2/scheduler/logs/stats | GET | JSON | BAJO | Migrar |
| 5 | 326 | /api/v2/scheduler/jobs/{id}/{action} | POST | JSON | BAJO | Migrar |

---

## 3. CASOS ESPECIALES

### 3.1 Descargas Blob (Excel)

**Archivo:** RecursosHumanos.js (línea 1164)
**Endpoint:** /api/rrhh/incidencias/plantilla-excel
**Estrategia:** Usar api con responseType: 'blob'

```javascript
// Migración con blob
const response = await api.get('/rrhh/incidencias/plantilla-excel', {
  responseType: 'blob'
});
```

### 3.2 FormData (Upload)

**Archivo:** RecursosHumanos.js (línea 1201)
**Endpoint:** /api/rrhh/incidencias/importar-excel
**Estrategia:** Usar api.post con FormData, sin Content-Type manual

```javascript
// Migración con FormData
const formData = new FormData();
formData.append('file', file);
const response = await api.post('/rrhh/incidencias/importar-excel', formData);
// Axios detecta FormData y no setea Content-Type manualmente
```

---

## 4. PLAN DE MIGRACIÓN

### Orden de migración (menor a mayor riesgo):

1. **Riesgo BAJO (87 fetch):** Migraciones directas
2. **Riesgo MEDIO (16 fetch):** Endpoints dinámicos, validar
3. **Riesgo ALTO (2 fetch):** Blob y FormData, probar cuidadosamente

---

**Documento creado:** 2025-12-27  
**Estado:** DIAGNÓSTICO COMPLETADO - LISTO PARA MIGRACIÓN
