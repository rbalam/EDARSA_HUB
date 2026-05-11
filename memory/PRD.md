# PRD — EDARSAHUB Dashboard Ejecutivo

**Última actualización:** 06-Mayo-2026

---

## 1. Problema Original

Crear el **Tablero Ejecutivo Comercial Blindado V2** para EDARSAHUB. El tablero directivo NO debe consultar SQL vivo ni caché de MongoDB como fuente principal, sino leer exclusivamente desde tablas consolidadas en EDARSAHUB.

Se deben seguir estrictamente las **15 Máximas Obligatorias**, operando bajo un esquema de **Autorización Controlada** (hacer solo lo que el usuario autorice, fase por fase, sin romper módulos blindados).

---

## 2. Arquitectura

| Capa | Tecnología |
|------|------------|
| Frontend | React |
| Backend | FastAPI |
| Base de datos consolidada | SQL Server (EDARSAHUB) |
| Autenticación actual | MongoDB (Legacy — pendiente migración) |
| Feature Flags | Variables de entorno (.env) |

---

## 3. Estado Actual — Cierre de Iteración

### 3.1 Feature Flag V2

```
REACT_APP_COMERCIAL_V2_ENABLED=true
```

**Tablero activo:** V2 (EDARSAHUB) ✅ ACTIVADO PERMANENTEMENTE (05-Mayo-2026)

---

### 3.2 Backend V2

| Estado | Detalle |
|--------|---------|
| ✅ LISTO | Endpoints validados, schedulers operativos, PROP-002 corregida |

**Endpoints V2 operativos:**
- `/api/v2/comercial/dashboard`
- `/api/v2/comercial/ventas-dia`
- `/api/v2/comercial/ventas-rango`
- `/api/v2/comercial/kpis-historicos`

---

### 3.3 Schedulers

| Scheduler | Frecuencia | Tabla destino | Estado |
|-----------|------------|---------------|--------|
| Ventas cerradas | 15 min | `Comercial_KPIs_Diarios_v2` | ✅ |
| Ventas abiertas | 5 min | `Comercial_Ventas_Dia_Abiertas_v2` | ✅ |

---

### 3.4 Validación (Mayo 2026)

| Unidad | Ventas | Status V2 |
|--------|--------|-----------|
| CIENFUEGOS | $559,865 | ACTUALIZADO |
| 130° MÉRIDA | $409,213 | ACTUALIZADO |
| LA ESTELAR | $462,031 | ACTUALIZADO |
| ORIGEN | $223,447 | ACTUALIZADO |
| 130° QRO | $407,073 | ACTUALIZADO |

**Total ventas Mayo 2026**: $2,061,629.70  
**Resultado:** 5/5 unidades validadas ✅

---

## 4. Tareas Pendientes

### P1 — Crítico

| Tarea | Estado |
|-------|--------|
| ✅ Corrección proyección mensual V2 | ✅ COMPLETADO (04-Mayo-2026) |
| ✅ Recuperar Contraseña PREVIEW | ✅ IMPLEMENTADO (05-Mayo-2026) - PROP-001 v2 |
| ✅ 130° MÉRIDA sin datos en Dashboard V2 | ✅ CORREGIDO (05-Mayo-2026) - PROP-002 |
| ✅ Prueba UI con Feature Flag V2 = true | ✅ VALIDADO |
| ✅ Activación permanente Feature Flag V2 | ✅ COMPLETADO (05-Mayo-2026) - PROP-003 |
| ✅ P1-FASE4A Estabilización Cuadre Cortes Z | ✅ COMPLETADO (05-Mayo-2026) - EDARSAHUB prioritario |
| ✅ P1-FASE5A.1 DDL Cuentas y Saldos Bancarios | ✅ COMPLETADO (05-Mayo-2026) - Tabla + índices + constraints |
| ✅ P1-FASE5A.1-FUNC-BACKEND Endpoints | ✅ COMPLETADO (06-Mayo-2026) - 13 endpoints API |
|| ✅ BUG-RUZ-002 Ventas por Hora | ✅ CERRADO (06-Mayo-2026) - Validado en LA ESTELAR, 130° MÉRIDA, CIENFUEGOS |
|| ✅ BUG-ARQUITECTONICO Fuente No Disponible | ✅ CERRADO (06-Mayo-2026) - Fallback EDARSAHUB para Ventas del Día |
| ✅ P1-FASE5A.1-FUNC-FRONTEND | ✅ IMPLEMENTADO (06-Mayo-2026) - UI Cuentas Bancarias + Tab en Finanzas |
| P1-FASE5A.2 Captura manual de saldos | ⏸️ BACKLOG |
| P1-FASE5A.3 Widget posición efectivo | ⏸️ BACKLOG |
| P1-FASE5A.4 Integración efectivo pendiente | ⏸️ BACKLOG |
| P1-FASE5A.5 Dashboard consolidado | ⏸️ BACKLOG |
| Auth/RBAC migración a EDARSAHUB | ⏸️ BACKLOG |

### P1 — Alto
| Tarea | Estado |
|-------|--------|
| Panel Programaciones Fase A (Solo lectura) | ⏸️ BACKLOG |
| Fase 4 — Tesorería | ⏸️ BACKLOG |

### P2 — Medio
| Tarea | Estado |
|-------|--------|
| Fase 5 — Dashboard Finanzas Consolidado | ⏸️ BACKLOG |

---

## 5. Reglas de Operación

1. **Autorización Controlada:** No ejecutar cambios sin permiso explícito.
2. **Documentar antes de implementar:** Proponer, esperar OK.
3. **No romper módulos blindados:** V1 intocable.
4. **Feature Flags:** No activar sin autorización.
5. **15 Máximas Obligatorias:** Siempre vigentes.

---

## 6. Documentación Técnica

- `/app/docs/reports/plan_tablero_ejecutivo_comercial_blindado_v2.md`
  - Sección 26: Cierre de iteración
  - Sección 27: P0 Proyección mensual mayo SoftRestaurant — corrección días transcurridos

---

## 7. Corrección Proyección V2 (03-Mayo-2026)

**Fórmula implementada:**
```
proyeccion = (venta_acumulada / dias_transcurridos) × dias_proyectables
```

**Archivo modificado:** `/app/frontend/src/pages/TableroEjecutivo.js`
**Función:** `transformV2ToV1Format()`

**Reglas:**
- `dias_transcurridos`: días calendario del mes en curso
- `dias_proyectables`: días totales del mes (enero = 30)
- Extensible para futuro calendario operativo EDARSAHUB

---

## 8. Registro de Cierres Formales

### P1-FASE4A — Estabilización de Cuadre de Cortes Z (05-Mayo-2026)

**Estado**: ✅ CERRADA Y ACEPTADA

**Resumen**: Tesorería/sucursales usa EDARSAHUB.Servidores_Conexiones como fuente primaria y MongoDB solo como fallback legacy. No se tocó frontend, MongoDB, EDARSAHUB ni `list_servers()` global.

**Archivo modificado**: `/app/backend/modules/finanzas/tesoreria.py`  
**Función creada**: `get_tesoreria_sucursales_operativas()`  
**Endpoint**: `GET /api/finanzas/tesoreria/sucursales`

**Documentación**: `/app/docs/proposals/P1-FASE4-TESORERIA-diagnostico.md`

---

## 9. Próximos Pasos Pendientes de Autorización

| Fase | Descripción | Estado |
|------|-------------|--------|
| P1-FASE5A.2 | Captura manual de saldos (puede combinarse con frontend 5A.1) | ⏸️ BACKLOG |
| P1-FASE5A.3 | Widget posición efectivo bancario | ⏸️ BACKLOG |
| P1-FASE5A.4 | Integración efectivo pendiente depositar | ⏸️ BACKLOG |
| P1-FASE5A.5 | Dashboard posición efectivo consolidado | ⏸️ BACKLOG |
| P1 | Panel Programaciones Fase A | Requiere propuesta formal |
| P0 | Auth/RBAC migración a EDARSAHUB | BACKLOG |

**Nota**: No iniciar implementación sin propuesta separada con alcance, riesgos, archivos, endpoints, tablas, pruebas y no regresión.

---

## 11. Registro P1-FASE5A.1-FUNC-BACKEND — Endpoints Completado (06-Mayo-2026)

**Archivos creados:**

| Archivo | Propósito |
|---------|-----------|
| `modules/finanzas/utils_bancarios.py` | Enmascaramiento y validaciones |
| `modules/finanzas/models_bancarios.py` | Modelos Pydantic |
| `modules/finanzas/repository_bancarios.py` | Queries EDARSAHUB |
| `modules/finanzas/cuentas_bancarias.py` | Router cuentas |
| `modules/finanzas/saldos_bancarios.py` | Router saldos |

**Endpoints creados (13):**

| Ruta | Método | Propósito |
|------|--------|-----------|
| `/api/v2/finanzas/bancos` | GET | Catálogo bancos |
| `/api/v2/finanzas/cuentas-bancarias` | GET | Listar cuentas |
| `/api/v2/finanzas/cuentas-bancarias/{id}` | GET | Obtener cuenta |
| `/api/v2/finanzas/cuentas-bancarias` | POST | Crear cuenta |
| `/api/v2/finanzas/cuentas-bancarias/{id}` | PUT | Editar cuenta |
| `/api/v2/finanzas/cuentas-bancarias/{id}/desactivar` | POST | Baja lógica |
| `/api/v2/finanzas/cuentas-bancarias/{id}/saldos` | GET | Listar saldos |
| `/api/v2/finanzas/cuentas-bancarias/{id}/saldo-actual` | GET | Último saldo |
| `/api/v2/finanzas/saldos-bancarios` | POST | Capturar saldo |
| `/api/v2/finanzas/saldos-bancarios/{id}/corregir` | POST | Corregir |
| `/api/v2/finanzas/saldos-bancarios/{id}/cancelar` | POST | Cancelar |
| `/api/v2/finanzas/saldos-bancarios/{id}/historial` | GET | Auditoría |
| `/api/v2/finanzas/saldos-bancarios/total` | GET | Saldo total |

**Endpoint NO creado (por diseño):** `GET /cuentas-bancarias/{id}/completa` - expone datos sin enmascarar

**Documentación:** `/app/docs/proposals/P1-FASE5A-1-ENDPOINTS-CUENTAS-SALDOS-BANCARIOS.md`

---

## 10. Registro P1-FASE5A.1 — DDL Completado (05-Mayo-2026)

**Tablas creadas/modificadas en EDARSAHUB:**

| Objeto | Tipo | Acción |
|--------|------|--------|
| `Finanzas_SaldosBancarios` | TABLE | CREADA (18 columnas) |
| `Finanzas_Cat_CuentasBancarias` | TABLE | MODIFICADA (+3 columnas auditoría) |

**Índices creados:**

| Índice | Tipo | Propósito |
|--------|------|-----------|
| `UQ_SaldosBancarios_CuentaFecha_EsVigente` | UNIQUE FILTRADO | Solo 1 saldo vigente por cuenta+fecha |
| `IX_SaldosBancarios_FechaSaldo` | NONCLUSTERED | Consultas por fecha |
| `IX_SaldosBancarios_CuentaHistorial` | NONCLUSTERED | Historial por cuenta |
| `IX_SaldosBancarios_UltimoVigente` | NONCLUSTERED FILTRADO | Último saldo vigente |

**CHECK constraints:**
- `CK_SaldosBancarios_Moneda` (MXN, USD, EUR, CAD)
- `CK_SaldosBancarios_FuenteDatos` (MANUAL, IMPORTACION, API, CONCILIACION)
- `CK_SaldosBancarios_Estatus` (VIGENTE, CORREGIDO, CANCELADO, HISTORICO)
- `CK_SaldosBancarios_TipoCambio` (NULL o > 0)
- `CK_SaldosBancarios_EsVigente_Estatus` (coherencia)
- `CK_SaldosBancarios_Activo_Estatus` (coherencia)
- `CK_SaldosBancarios_CancelacionMotivo` (cancelación requiere motivo)

**Foreign Keys:**
- `FK_SaldosBancarios_CuentaBancaria` → `Finanzas_Cat_CuentasBancarias`
- `FK_SaldosBancarios_UsuarioCreacion/Modificacion/Cancelacion` → `Usuario_Catalogo`
- `FK_CuentasBancarias_Banco` → `Global_Cat_Bancos`
- `FK_CuentasBancarias_UsuarioCreacion/Modificacion` → `Usuario_Catalogo`

**Documentación**: `/app/docs/proposals/P1-FASE5A-1-CUENTAS-Y-SALDOS-BANCARIOS-DDL.md`

---

*Fin del PRD*

---

## FASE 0 COMPLETADA — AUDITORÍA DE FUENTES DE DATOS (08-Mayo-2026)

### Documentos Generados

1. `/app/docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md` — Inventario completo de 203 tablas EDARSAHUB y 72 colecciones MongoDB
2. `/app/docs/PROPUESTA_MIGRACION_AUTH_RBAC_SERVIDORES_EDARSAHUB.md` — Propuesta de migración sin implementación

### Hallazgos Principales

| Módulo | Estado Actual | Dictamen |
|--------|---------------|----------|
| Auth/RBAC | MongoDB (15 users, 6 roles, 43 permisos) | MONGO_LEGACY_DEUDA_TÉCNICA |
| Servidores | EDARSAHUB primario (17) + MongoDB fallback (13) | EDARSAHUB_EXISTE_PERO_CÓDIGO_USA_MONGO |
| Finanzas | EDARSAHUB 100% | EDARSAHUB_PRIMARIO_CONFIRMADO |
| RH/Nóminas | EDARSAHUB 100% | EDARSAHUB_PRIMARIO_CONFIRMADO |
| Comercial | Híbrido correcto | HÍBRIDO_CORRECTO_CON_REGLAS |

### Próximas Autorizaciones Pendientes

- [ ] FASE A0: Backup MongoDB auth
- [ ] DDL: Agregar campos faltantes a Usuario_Catalogo
- [ ] FASE A2: Poblar EDARSAHUB en modo espejo
- [ ] FASE A4: Piloto SuperAdministrador

### Regla Vigente

**AUTORIZACIÓN CONTROLADA**: No se implementan cambios sin dictamen expreso del usuario.

---

## FASE A4.1 COMPLETADA — MIGRACIÓN USUARIOS MongoDB → EDARSAHUB (10-Mayo-2026)

### Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Usuarios migrados | 10 |
| Usuarios productivos (Activo=1) | 9 |
| Usuarios deshabilitados (Activo=0) | 1 |
| Usuarios @test.com excluidos | 5 |
| Tabla de trazabilidad creada | `Usuario_MigracionMongoTrace` |

### Tablas Afectadas en EDARSAHUB

| Tabla | Acción | Registros |
|-------|--------|-----------|
| `Usuario_Catalogo` | INSERT | 10 |
| `Usuario_MigracionMongoTrace` | CREATE + INSERT | 10 |
| `Usuario_RolesAsignacion` | Sin cambios | 0 |
| `Usuario_EmpresasAsignacion` | Sin cambios | 0 |

### Usuarios Migrados

| UsuarioID | Email | Rol MongoDB | Clasificación | Activo |
|-----------|-------|-------------|---------------|--------|
| 1 | admin@edarsa.com | Administrador | PRODUCTIVO | ✅ |
| 2 | admin@inventario.com | SuperAdministrador | PRODUCTIVO | ✅ |
| 3 | carlosruz@edarsa.com.mx | Administrador | PRODUCTIVO | ✅ |
| 4 | noxte@alpyc.com | Supervisor | PRODUCTIVO | ✅ |
| 5 | auditoria@edarsa.com.mx | Usuario | PRODUCTIVO | ✅ |
| 6 | almacen@cienfuegos.mx | Usuario | PRODUCTIVO | ✅ |
| 7 | administracion@cienfuegos.mx | Supervisor | PRODUCTIVO | ✅ |
| 8 | ricardo@edarsa.com.mx | SuperAdministrador | PRODUCTIVO | ✅ |
| 9 | david.ricardez@cienfuegos.mx | Usuario | PRODUCTIVO | ✅ |
| 10 | test_propinas@edarsa.com | DESHABILITADO | DESHABILITADO | ❌ |

### Usuarios NO Migrados (Excluidos por decisión)

| Email | Motivo |
|-------|--------|
| test_validacion@test.com | Cuenta de prueba @test.com |
| test_rbac_val@test.com | Cuenta de prueba @test.com |
| superadmin@test.com | Cuenta de prueba @test.com |
| superadmin2@test.com | Cuenta de prueba @test.com |
| usuario_test_portal@test.com | Cuenta de prueba @test.com |

### Restricciones Documentadas Post-A4.1

- ⚠️ Los usuarios migrados **NO tienen rol asignado** en EDARSAHUB
- ⚠️ Los usuarios migrados **NO tienen empresa asignada** en EDARSAHUB
- ⚠️ **MongoDB sigue siendo fuente activa de login**
- ⚠️ `PasswordHashTexto` contiene hash bcrypt pero **no se usa para autenticación todavía**

### Fases Pendientes de Autorización

| Fase | Descripción | Dependencia |
|------|-------------|-------------|
| A4.2 | Asignar roles en `Usuario_RolesAsignacion` | Requiere mapeo Rol MongoDB → RolID SQL |
| A5 | Asignar empresas en `Usuario_EmpresasAsignacion` | Requiere matriz usuario-empresa |
| A6 | Implementar Dual-Read en login | Backend |
| A7 | Switch definitivo a EDARSAHUB | Pruebas completas |

### Confirmaciones de Cero Impacto

- ✅ Login NO fue modificado
- ✅ JWT NO fue modificado
- ✅ Frontend NO fue modificado
- ✅ Módulos protegidos NO fueron tocados
- ✅ MongoDB sigue siendo fuente activa de autenticación

---

## FASE A4.1-R COMPLETADA — REVERSA PARCIAL CONTROLADA (11-Mayo-2026)

### Resumen Ejecutivo

| Métrica | Antes | Después |
|---------|-------|---------|
| Usuarios en Usuario_Catalogo | 10 | **9** |
| Registros en Usuario_MigracionMongoTrace | 10 | **9** |
| Usuario test_propinas@edarsa.com | Existía | **ELIMINADO** |

### Usuario Eliminado

| Campo | Valor |
|-------|-------|
| UsuarioID | 10 |
| Email | test_propinas@edarsa.com |
| Nombre | Test Propinas |
| RolMongoDB | DESHABILITADO |
| Clasificacion | DESHABILITADO |
| Motivo | Usuario no productivo, cuenta deshabilitada en MongoDB |

### Justificación Arquitectónica

- ❌ **DESHABILITADO no es un rol RBAC** — Es un estado de cuenta
- ✅ El estado activo/inactivo se modela en `Usuario_Catalogo.Activo`
- ✅ EDARSAHUB debe contener solo usuarios productivos activos antes de asignar roles
- ✅ Usuario eliminado de EDARSAHUB pero **preservado en MongoDB** como histórico

### Aclaración Importante

El usuario `test_propinas@edarsa.com`:
- **NO fue eliminado de MongoDB** — Sigue existiendo como registro histórico
- **Fue eliminado de EDARSAHUB** — No participa en la migración de roles
- **No se creará rol DESHABILITADO** — Deshabilitado es estado, no rol

### Impacto en FASE A4.2

| Aspecto | Antes A4.1-R | Después A4.1-R |
|---------|--------------|----------------|
| Usuarios a asignar rol | 10 | **9** |
| Roles nuevos requeridos | SUPERADMIN, USUARIO, DESHABILITADO | **SUPERADMIN, USUARIO** |
| Usuarios DESHABILITADOS en EDARSAHUB | 1 | **0** |

### Confirmaciones de Cero Impacto A4.1-R

- ✅ Solo se eliminó test_propinas@edarsa.com (UsuarioID=10)
- ✅ NO se eliminaron usuarios productivos
- ✅ NO se tocó MongoDB
- ✅ Login NO modificado
- ✅ JWT NO modificado
- ✅ Frontend NO modificado
- ✅ Módulos protegidos intactos
- ✅ MongoDB sigue siendo fuente activa de login

---

## FASE 1 COMPLETADA — UniversalQueryTester para SQL Servers (11-Mayo-2026)

### Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Endpoint creado | `POST /api/servers/{server_id}/universal-query-test` |
| Archivos nuevos | 2 (routes.py, __init__.py) |
| Archivos modificados | 2 (Servidores.js, server.py) |
| Test Types soportados | sql_libre, api_rest, conexion, diagnostico |
| Seguridad | Solo SELECT (lectura), BLOCKED_SQL_KEYWORDS |

### Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `/app/frontend/src/components/UniversalQueryTester.jsx` | Componente React modal agnóstico |
| `/app/backend/modules/universal_query/__init__.py` | Inicializador del módulo |
| `/app/backend/modules/universal_query/routes.py` | Router FastAPI con endpoint universal |

### Confirmaciones

- ✅ QueryConfigWizard.js quedó intacto
- ✅ Endpoints legacy /servers/{id}/queries/* intactos
- ✅ MongoDB no modificado
- ✅ No se creó persistencia
- ✅ No se crearon tablas SQL

---

## FASE API-UQT1 COMPLETADA — UniversalQueryTester para Conexiones API (11-Mayo-2026)

### Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Endpoint creado | `POST /api/api-connections/{connection_id}/universal-query-test` |
| Archivos nuevos | 1 (universal_test_routes.py) |
| Archivos modificados | 4 (__init__.py, repository no modificado, server.py, UniversalQueryTester.jsx, Servidores.js) |
| Fuente de datos | EDARSAHUB.Servidores_Conexiones (tipo_conexion = 'API_LOCAL') |
| Seguridad | Solo GET, headers enmascarados, timeout obligatorio, autorización por EmpresaID |

### Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/api_connections/universal_test_routes.py` | Endpoint aislado para conexiones API |

### Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/api_connections/__init__.py` | Import del nuevo router |
| `/app/backend/server.py` | Registro del router API-UQT |
| `/app/frontend/src/components/UniversalQueryTester.jsx` | Prop connectionType ('sql' \| 'api') |
| `/app/frontend/src/pages/Servidores.js` | Botón "Test Universal" en tab Conexiones API |

### Funcionalidades Implementadas

| Funcionalidad | Estado |
|---------------|--------|
| Autenticación obligatoria (current_user) | ✅ |
| Autorización por EmpresaID | ✅ |
| Solo método GET permitido | ✅ |
| Bloqueo POST/PUT/PATCH/DELETE | ✅ |
| Headers sensibles enmascarados | ✅ |
| Params sensibles enmascarados | ✅ |
| URL ejecutada enmascarada | ✅ |
| endpoint_path como URL absoluta bloqueado | ✅ |
| Timeout configurable (1-60s) | ✅ |
| Consultas SQL parametrizadas | ✅ |

### Pruebas Verificadas

| Prueba | Resultado |
|--------|-----------|
| Conexión API válida con usuario autorizado | ✅ 200 |
| Conexión inexistente | ✅ 404 |
| POST bloqueado | ✅ 400 |
| DELETE bloqueado | ✅ 400 |
| URL externa en endpoint_path | ✅ 400 |
| Sin autenticación | ✅ 403 |
| SQL UniversalQueryTester sigue funcionando | ✅ |
| QueryConfigWizard intacto | ✅ |
| MongoDB no modificado | ✅ |
| EDARSAHUB no modificado | ✅ |

### Confirmaciones de No Regresión

- ✅ Endpoint SQL original `/api/servers/{id}/universal-query-test` intacto
- ✅ QueryConfigWizard.js sin modificaciones
- ✅ Endpoints legacy `/servers/{id}/queries/*` intactos
- ✅ MongoDB sin nuevas colecciones
- ✅ EDARSAHUB sin nuevas tablas
- ✅ No se creó persistencia de pruebas
- ✅ Módulos protegidos (Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones) intactos
- ✅ Login/JWT/RBAC sin modificaciones

### Observación de Cierre (11-Mayo-2026)

La prueba contra `130° QRO LOCAL` devolvió HTTP 422 desde la API destino porque requiere parámetro `sql`. Esto se acepta como evidencia de:
- ✅ Conectividad API validada
- ✅ Endpoint alcanzó API destino
- ✅ Manejo de error 422 controlado
- ⚠️ Prueba funcional con payload válido de negocio: PENDIENTE

**Nota:** Antes de uso operativo con APIs tipo `/query`, probar con parámetro requerido por la API destino.

---

## FASE API-UQT1 — CIERRE FORMAL ACEPTADO (11-Mayo-2026)

| Aspecto | Estado |
|---------|--------|
| Implementación | ✅ COMPLETADA |
| Pruebas backend | ✅ APROBADAS |
| No regresión | ✅ VERIFICADA |
| Cierre documental | ✅ **ACEPTADO** |

---

## FASE API-SEC1 — CORRECCIÓN DE SEGURIDAD CONEXIONES API (11-Mayo-2026)

### Estado: ✅ IMPLEMENTADA Y VALIDADA

### Problema Resuelto

Se detectó que la documentación Swagger/API permitía ejecutar manualmente SQL libre mediante:
- Parámetro `sql` en query string
- Header `x-api-key` visible en formularios
- Acceso a comandos SQL arbitrarios vía parámetros API

### Cambios Implementados

| Componente | Cambio |
|------------|--------|
| Backend `universal_test_routes.py` | Nuevo endpoint `POST /api-connections/{id}/test-connection` con query SQL fija |
| Backend `universal_test_routes.py` | Bloqueo de parámetros peligrosos (sql, query, exec, etc.) |
| Backend `universal_test_routes.py` | Detección de patrones SQL en valores |
| Backend `repository.py` | API key enmascarada como `***CONFIGURED***` en listados |
| Frontend `UniversalQueryTester.jsx` | Validación de parámetros bloqueados en UI |
| Frontend `Servidores.js` | Botón "Probar Conexión" usa endpoint seguro |
| Frontend `Servidores.js` | Campo API key con `type="password"` y placeholder seguro |

### Endpoints Resultantes

| Endpoint | Propósito | SQL desde usuario |
|----------|-----------|-------------------|
| `POST /api-connections/{id}/test-connection` | Validación técnica con query fija | ❌ NO |
| `POST /api-connections/{id}/universal-query-test` | Test API REST (con bloqueos) | ❌ BLOQUEADO |
| `POST /servers/{id}/universal-query-test` | Test SQL Server (intacto) | ✅ Permitido |

### Query Fija Hardcodeada

```sql
SELECT TOP 1 name FROM sys.tables ORDER BY name
```

### Parámetros Bloqueados

- `sql`, `query`, `consulta`, `statement`, `command`, `script`, `exec`, `execute`

### Patrones SQL Bloqueados en Valores

- `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `EXEC`, `MERGE`, `CREATE`, `UNION`, `FROM`, `WHERE`, `INFORMATION_SCHEMA`, `sys.tables`

### Validaciones Aprobadas

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Endpoint /test-connection disponible (404 para ID inexistente) | ✅ |
| 2 | Bloqueo de parámetro 'sql' | ✅ |
| 3 | Bloqueo de patrón SQL en valores | ✅ |
| 4 | Autenticación obligatoria (401/403 sin auth) | ✅ |
| 5 | Query fija ejecutada internamente | ✅ |
| 6 | API key enmascarada en listado | ✅ |
| 7 | UniversalQueryTester SQL intacto | ✅ |

### Confirmaciones de No Regresión

- ✅ QueryConfigWizard sin modificaciones
- ✅ Endpoints legacy SQL intactos
- ✅ MongoDB sin modificaciones
- ✅ EDARSAHUB sin modificaciones DDL/DML
- ✅ Módulos protegidos (Comercial, Tablero, KPIs, etc.) intactos
- ✅ Login/JWT/RBAC sin modificaciones

---

## Próximas Fases Pendientes de Autorización

| Fase | Descripción | Estado |
|------|-------------|--------|
| FASE Q1.3 (Pasiva) | Dry-run: Generar INSERTs de migración SIN ejecutar | ⏸️ PENDIENTE |
| FASE Q1.4 | Ejecutar DDL en EDARSAHUB | ⏸️ PENDIENTE |
| FASE A4.2 (Pasiva) | Diagnóstico para asignación de roles a 9 usuarios | ⏸️ PENDIENTE |
| Auth Token Bug | Persistencia de token en frontend Finanzas | ⏸️ PENDIENTE |
| FASE A5 | Poblar Usuario_EmpresasAsignacion | ⏸️ BACKLOG |
| FASE A6 | Dual-read en login | ⏸️ BACKLOG |
| FASES SYNC-C0+ | Sincronización incremental de Compras | ⏸️ BACKLOG |

---

**Última actualización:** 11-Mayo-2026

