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

