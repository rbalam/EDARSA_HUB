# EDARSA HUB - ARQ: Catálogo Maestro de Sistemas y Capacidades SQL-First

## Reporte Consolidado

**Fecha:** 2025-12-XX  
**Versión:** 1.0  
**Estado:** FASE 1 DIAGNÓSTICO COMPLETADO - PENDIENTE AUTORIZACIÓN FASES 2-7

---

## 1. RESUMEN EJECUTIVO

### Problema Resuelto
Cada vez que se agrega un nuevo sistema (ej: SoftRestaurant Enterprise), se requieren modificaciones en **múltiples puntos del código**:
- Filtros frontend (Servidores.js, Reportes.js)
- Explorador BD
- Listado de conexiones
- Carga de tablas
- Sync históricos
- Queries por sistema
- Normalizadores system_type

Esto genera **deuda técnica, bugs y tiempo de desarrollo elevado**.

### Solución Propuesta
**Catálogo Maestro de Sistemas + Motor de Capacidades** donde:
1. Un sistema nuevo se registra en EDARSAHUB SQL
2. Se le asignan capacidades
3. Aparece automáticamente en filtros/menús/módulos aplicables
4. **No se modifica frontend** por cada sistema
5. **No se modifica backend** por cada sistema (salvo adapter tecnológico nuevo)

---

## 2. TABLAS PROPUESTAS/USADAS

### Tablas EXISTENTES (Reutilizadas)
| Tabla | Propósito |
|-------|-----------|
| `Sistema_Tipos` | Catálogo de tipos de sistema |
| `Sistema_Empresas` | Catálogo maestro de empresas |
| `Sistema_EmpresasServidores` | Relación empresa ↔ servidor |
| `Servidores_Conexiones` | Conexiones SQL/API |

### Tablas NUEVAS (Propuestas)
| Tabla | Propósito |
|-------|-----------|
| `Sistema_Capacidades` | Capacidades por tipo de sistema |
| `Sistema_ModulosVisibilidad` | Visibilidad en módulos/menús |
| `Sistema_TiposVariantes` | Mapeo de variantes de nombres |

---

## 3. DDL

### Ubicación
```
/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_DDL_FASE2.sql
```

### Características
- IF NOT EXISTS (idempotente)
- No destructivo
- Foreign keys a Sistema_Tipos existente
- Índices optimizados

### Tablas Creadas
1. **Sistema_Capacidades**: CodigoCapacidad, RequiereApiLocal, RequiereSqlDirecto, ConfiguracionJSON
2. **Sistema_ModulosVisibilidad**: CodigoModulo, Visible, OrdenMenu
3. **Sistema_TiposVariantes**: VarianteNombre, EsCanonico

---

## 4. SEEDS

### Ubicación
```
/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SEED_FASE3.sql
```

### Sistemas Iniciales
- SOFTRESTAURANT
- MPRO (ManagementPro)
- SOFTRESTAURANT_ENTERPRISE (si existe)
- SQLSERVER_GENERIC (si existe)
- EDARSAHUB_SQL (si existe)

### Capacidades por Sistema

| Capacidad | SR | MPRO | Descripción |
|-----------|:--:|:----:|-------------|
| EXPLORADOR_BD | ✓ | ✓ | Explorar BD |
| EXPLORADOR_TABLAS | ✓ | ✓ | Listar tablas |
| EXPLORADOR_COLUMNAS | ✓ | ✓ | Listar columnas |
| EXPLORADOR_PREVIEW | ✓ | ✓ | Preview datos |
| SYNC_VENTAS_HISTORICAS | ✓ | ✓ | Sync históricos |
| SYNC_VENTAS_POR_HORA | ✓ | ✓ | Sync por hora |
| SYNC_VENTAS_DIA_SEMANA | ✓ | ✓ | Sync día semana |
| VENTAS_DIA | ✓ | ✓ | KPIs día |
| VENTAS_PERIODO | ✓ | ✓ | KPIs período |
| COMPRAS | ✓ | ✓ | Módulo compras |
| INVENTARIOS | ✓ | ✓ | Módulo inventarios |
| CORTES_Z | ✓ | ✓ | Cortes caja |
| PROPINAS_TPV | ✓ | ✓ | Propinas |
| CATALOGO_SQL | ✓ | ✓ | Consultas SQL |
| SUCURSALES_VISIBLES | ✗ | ✓ | Config sucursales |
| CUENTAS_POR_PAGAR | ✗ | ✓ | CxP Finanzas |

---

## 5. RESOLVER CENTRAL

### Propuesta
```python
# /app/backend/core/system_capability_resolver.py

class SystemCapabilityResolver:
    """Resolver central para capacidades de sistemas."""
    
    def system_supports(self, codigo_sistema: str, capacidad: str) -> bool
    def get_systems_for_capability(self, capacidad: str) -> List[str]
    def get_query_for_capability(self, codigo_sistema: str, capacidad: str) -> Optional[str]
    def get_visible_systems_for_module(self, modulo: str) -> List[Dict]
    def normalize_system_type(self, system_type: str) -> str
    def get_connection_strategy(self, server_id: str) -> str
```

### Fuente de Datos
- EDARSAHUB SQL (NO MongoDB)
- Tablas: Sistema_Tipos, Sistema_Capacidades, Sistema_ModulosVisibilidad
- Cache en memoria con TTL

---

## 6. ENDPOINTS

### Propuestos
```
GET /api/catalogos/sistemas
GET /api/catalogos/sistemas/capacidades
GET /api/catalogos/sistemas/por-capacidad/{capacidad}
GET /api/catalogos/servidores/por-capacidad/{capacidad}
```

### Existentes (Reutilizados)
```
GET /api/catalogos/sistemas/activos  (ya existe)
GET /api/explorador/conexiones-explorables  (ya existe)
```

---

## 7. ARCHIVOS MODIFICADOS (Propuestos)

### Backend
| Archivo | Cambio Propuesto |
|---------|------------------|
| `core/system_capability_resolver.py` | NUEVO - Resolver central |
| `core/system_type_utils.py` | Usar resolver para normalización |
| `modules/comercial/service.py` | Reemplazar UNIDADES_EDARSAHUB_MAP |
| `modules/comercial/routes.py` | Usar resolver en bifurcaciones |
| `catalogo/catalogo_consultas.py` | Mover queries a Sistema_Consultas |

### Frontend
| Archivo | Cambio Propuesto |
|---------|------------------|
| `pages/Servidores.js` | Consumir endpoint dinámico para dropdown |
| `pages/Reportes.js` | Usar capacidades para lógica de sistema |
| `pages/Compras.js` | Eliminar bifurcaciones hardcodeadas |

---

## 8. MÓDULOS INTEGRADOS

### Fase 6 - Integración No Destructiva
1. ✅ Explorador BD (parcialmente dinámico)
2. ⬜ Filtros de sistema/conexión
3. ⬜ Sync_Historicos candidatos
4. ⬜ Catálogo SQL

### Módulos NO MODIFICADOS (Fase 6)
- Comercial
- Finanzas
- Compras
- Tablero Ejecutivo
- Operaciones
- Auth/RBAC

---

## 9. VALIDACIONES

### Criterios de Éxito
1. [ ] Agregar sistema SoftRestaurant Enterprise desde SQL
2. [ ] Activar capacidad EXPLORADOR_BD
3. [ ] Confirmar que aparece en Explorador sin cambiar frontend
4. [ ] Activar capacidad SYNC_VENTAS_HISTORICAS
5. [ ] Confirmar que aparece como candidato de Sync sin hardcode
6. [ ] Desactivar capacidad y confirmar que desaparece
7. [ ] Confirmar SoftRestaurant y MPRO siguen funcionando
8. [ ] Confirmar no se exponen secrets
9. [ ] Confirmar no se usa MongoDB
10. [ ] Confirmar no regresión de módulos protegidos

---

## 10. NO REGRESIÓN

### Módulos Protegidos
- Comercial, Tablero, Compras, Finanzas, Operaciones
- Catálogos, Servidores, Auth/RBAC

### Estrategia
- Feature flag `CAPABILITY_RESOLVER_ENABLED=false` por defecto
- Compatibilidad hacia atrás con helpers existentes
- No eliminar lógica legacy hasta validar resolver

---

## 11. RIESGOS PENDIENTES

| Riesgo | Mitigación |
|--------|------------|
| Romper Explorador BD | Mantener lógica legacy en paralelo |
| Romper Sync Históricos | Capacidad opcional, no bloquear sync |
| Romper filtros Comercial | Feature flag para activación gradual |
| Romper filtros Frontend | Endpoint + fallback a lista legacy |

---

## 12. PLAN DE FASES SIGUIENTES

### FASE 2 - DDL SQL-First ⬜ (Requiere Autorización)
- Crear tablas Sistema_Capacidades, Sistema_ModulosVisibilidad
- Ejecutar DDL en EDARSAHUB

### FASE 3 - Seed Inicial ⬜ (Requiere Autorización)
- Cargar capacidades para SR y MPRO
- Cargar visibilidad de módulos

### FASE 4 - Resolver Central ⬜ (Requiere Autorización)
- Implementar SystemCapabilityResolver
- Cache en memoria

### FASE 5 - Endpoints ⬜ (Requiere Autorización)
- Crear endpoints de catálogo
- Aplicar RBAC

### FASE 6 - Integración No Destructiva ⬜ (Requiere Autorización)
- Integrar en Explorador BD
- Integrar en Sync Históricos

### FASE 7 - Frontend ⬜ (Requiere Autorización)
- Migrar filtros a endpoints dinámicos
- Eliminar listas hardcodeadas

---

## 13. DOCUMENTOS GENERADOS

| Documento | Ubicación |
|-----------|-----------|
| Diagnóstico FASE 1 | `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE1_DIAGNOSTICO.md` |
| DDL FASE 2 | `/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_DDL_FASE2.sql` |
| SEED FASE 3 | `/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SEED_FASE3.sql` |
| Reporte Consolidado | `/app/docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SQLFIRST_REPORTE.md` |

---

## CONCLUSIÓN

La **FASE 1 (Diagnóstico)** está **COMPLETADA**:
- Matriz de auditoría generada con 30+ puntos de hardcoding identificados
- DDL propuesto con IF NOT EXISTS (idempotente)
- SEED inicial preparado para SR y MPRO
- Plan de fases 2-7 documentado

**SIGUIENTE PASO:** Autorización del usuario para ejecutar DDL FASE 2 en EDARSAHUB.

---

**Autor:** Arquitecto Senior Backend/DBA  
**Revisado por:** Pendiente  
**Aprobado por:** Pendiente
