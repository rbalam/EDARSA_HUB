# ARQ CATÁLOGO MAESTRO - FASE 3 SEED - REPORTE DE EJECUCIÓN

**Fecha:** 2025-12-XX  
**Estado:** ✅ COMPLETADO EXITOSAMENTE  
**Autor:** Arquitecto DBA

---

## 1. RESUMEN EJECUTIVO

La ejecución del SEED FASE 3 para el Catálogo Maestro de Sistemas y Capacidades fue **completada exitosamente**. Se insertaron 40 capacidades, 18 variantes de nombres y 16 registros de visibilidad para 5 tipos de sistema.

### Resultado Global
| Componente | Insertados | Omitidos | Total |
|------------|------------|----------|-------|
| Capacidades | 40 | 0 | 40 |
| Variantes | 18 | 9 | 27 |
| Visibilidad | 16 | 0 | 16 |

### Estado Final por Sistema
| Sistema | Capacidades | Variantes | Módulos Visibles |
|---------|-------------|-----------|------------------|
| SOFTRESTAURANT | 15 | 4 | 7 |
| MPRO | 17 | 3 | 7 |
| API_LOCAL (Enterprise) | 4 | 6 | 1 |
| EDARSAHUB_SQL | 4 | 3 | 1 |
| OTRO | 0 | 2 | 0 |

---

## 2. SISTEMAS DETECTADOS EN Sistema_Tipos

| ID | CodigoSistema | NombreSistema | Activo |
|----|---------------|---------------|--------|
| 1 | SOFTRESTAURANT | SoftRestaurant | ✅ |
| 2 | MPRO | ManagementPro | ✅ |
| 3 | API_LOCAL | API Local | ✅ |
| 4 | EDARSAHUB_SQL | EDARSAHUB SQL Server | ✅ |
| 5 | OTRO | Otro | ✅ |

**Nota:** No existe un tipo separado "SOFTRESTAURANT_ENTERPRISE". Los servidores Enterprise usan `API_LOCAL` como tipo de sistema.

---

## 3. SEEDS EJECUTADOS

### 3.1 Script Base
```
/app/docs/ddl/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_SEED_FASE3.sql
```

### 3.2 Método de Ejecución
- Conexión directa a EDARSAHUB via pymssql
- Verificación IF NOT EXISTS antes de cada INSERT
- Transacción con COMMIT al final
- Seed 100% idempotente

---

## 4. CAPACIDADES INSERTADAS

### 4.1 SOFTRESTAURANT (ID=1) - 15 capacidades
| Capacidad | Descripción | RequiereAPI | RequiereSQL |
|-----------|-------------|-------------|-------------|
| EXPLORADOR_BD | Explorador de Base de Datos | ❌ | ✅ |
| EXPLORADOR_TABLAS | Listar tablas de base de datos | ❌ | ✅ |
| EXPLORADOR_COLUMNAS | Listar columnas de tablas | ❌ | ✅ |
| EXPLORADOR_PREVIEW | Preview de datos de tabla | ❌ | ✅ |
| CATALOGO_SQL | Catálogo de consultas SQL | ❌ | ✅ |
| SYNC_VENTAS_HISTORICAS | Sync de ventas históricas | ❌ | ✅ |
| SYNC_VENTAS_POR_HORA | Sync de ventas por hora | ❌ | ✅ |
| SYNC_VENTAS_DIA_SEMANA | Sync de ventas por día de semana | ❌ | ✅ |
| VENTAS_DIA | KPIs de ventas del día | ❌ | ✅ |
| VENTAS_PERIODO | KPIs de ventas por período | ❌ | ✅ |
| COMPRAS | Módulo de compras | ❌ | ✅ |
| INVENTARIOS | Módulo de inventarios | ❌ | ✅ |
| CORTES_Z | Cortes de caja Z | ❌ | ✅ |
| REPORTES | Reportes de inventarios | ❌ | ✅ |
| PROPINAS_TPV | Propinas por TPV | ❌ | ✅ |

### 4.2 MPRO (ID=2) - 17 capacidades
| Capacidad | Descripción | RequiereAPI | RequiereSQL |
|-----------|-------------|-------------|-------------|
| EXPLORADOR_BD | Explorador de Base de Datos | ❌ | ✅ |
| EXPLORADOR_TABLAS | Listar tablas de base de datos | ❌ | ✅ |
| EXPLORADOR_COLUMNAS | Listar columnas de tablas | ❌ | ✅ |
| EXPLORADOR_PREVIEW | Preview de datos de tabla | ❌ | ✅ |
| CATALOGO_SQL | Catálogo de consultas SQL | ❌ | ✅ |
| SYNC_VENTAS_HISTORICAS | Sync de ventas históricas | ❌ | ✅ |
| SYNC_VENTAS_POR_HORA | Sync de ventas por hora (Fecha_Alta) | ❌ | ✅ |
| SYNC_VENTAS_DIA_SEMANA | Sync de ventas por día de semana | ❌ | ✅ |
| VENTAS_DIA | KPIs de ventas del día | ✅ | ✅ |
| VENTAS_PERIODO | KPIs de ventas por período | ❌ | ✅ |
| COMPRAS | Módulo de compras | ❌ | ✅ |
| INVENTARIOS | Módulo de inventarios | ❌ | ✅ |
| CORTES_Z | Cortes de caja Z | ❌ | ✅ |
| REPORTES | Reportes de inventarios | ❌ | ✅ |
| PROPINAS_TPV | Propinas por TPV | ❌ | ✅ |
| **SUCURSALES_VISIBLES** | Configuración de sucursales visibles | ❌ | ✅ |
| **CUENTAS_POR_PAGAR** | Cuentas por pagar en Finanzas | ❌ | ✅ |

### 4.3 API_LOCAL / Enterprise (ID=3) - 4 capacidades
| Capacidad | Descripción | RequiereAPI | RequiereSQL |
|-----------|-------------|-------------|-------------|
| EXPLORADOR_BD | Explorador de Base de Datos vía API | ✅ | ❌ |
| EXPLORADOR_TABLAS | Listar tablas vía API | ✅ | ❌ |
| EXPLORADOR_COLUMNAS | Listar columnas vía API | ✅ | ❌ |
| EXPLORADOR_PREVIEW | Preview de datos vía API | ✅ | ❌ |

**⚠️ DECISIÓN:** No se activaron SYNC_VENTAS_* para API_LOCAL porque los servidores Enterprise (CHAPUR NORTE, CHAPUR NORTE BACKOFICE) **no tienen query_ventas validada**.

### 4.4 EDARSAHUB_SQL (ID=4) - 4 capacidades
| Capacidad | Descripción |
|-----------|-------------|
| EXPLORADOR_BD | Explorador de BD EDARSAHUB |
| EXPLORADOR_TABLAS | Listar tablas EDARSAHUB |
| EXPLORADOR_COLUMNAS | Listar columnas EDARSAHUB |
| EXPLORADOR_PREVIEW | Preview de datos EDARSAHUB |

---

## 5. VARIANTES INSERTADAS

### Por Sistema
| Sistema | Variante | Canónico |
|---------|----------|----------|
| **SOFTRESTAURANT** | SOFTRESTAURANT | ✅ |
| | soft_restaurant | |
| | SR | |
| | SOFT | |
| **MPRO** | MPRO | ✅ |
| | ManagementPro | |
| | ManagmentPro | |
| **API_LOCAL** | API_LOCAL | ✅ |
| | API Local | |
| | Enterprise | |
| | SOFRESATAURANT_ENTER | |
| | SoftRestaurant Enterprise | |
| | SOFTRESTAURANT_ENTERPRISE | |
| **EDARSAHUB_SQL** | EDARSAHUB_SQL | ✅ |
| | EDARSA_HUB | |
| | EDARSAHUB | |
| **OTRO** | OTRO | ✅ |
| | OTHER | |

### Variantes Omitidas (ya existían en otra ejecución)
- SoftRestaurant
- softrestaurant
- managementpro
- MANAGEMENTPRO
- mpro
- enterprise
- edarsahub
- Otro
- otro

---

## 6. VISIBILIDAD INSERTADA

### SOFTRESTAURANT - 7 módulos
| Módulo | Descripción | Visible | Orden |
|--------|-------------|---------|-------|
| EXPLORADOR_BD | Explorador de Base de Datos | ✅ | 10 |
| COMERCIAL | Dashboard Comercial | ✅ | 1 |
| COMPRAS | Módulo de Compras | ✅ | 3 |
| REPORTES | Reportes de Inventarios | ✅ | 5 |
| FINANZAS | Finanzas y Tesorería | ✅ | 4 |
| SYNC_HISTORICOS | Sincronización Histórica | ✅ | 20 |
| CATALOGO_SQL | Catálogo SQL | ✅ | 15 |

### MPRO - 7 módulos
| Módulo | Descripción | Visible | Orden |
|--------|-------------|---------|-------|
| EXPLORADOR_BD | Explorador de Base de Datos | ✅ | 10 |
| COMERCIAL | Dashboard Comercial | ✅ | 1 |
| COMPRAS | Módulo de Compras | ✅ | 3 |
| REPORTES | Reportes de Inventarios | ✅ | 5 |
| FINANZAS | Finanzas y Tesorería | ✅ | 4 |
| SYNC_HISTORICOS | Sincronización Histórica | ✅ | 20 |
| CATALOGO_SQL | Catálogo SQL | ✅ | 15 |

### API_LOCAL - 1 módulo
| Módulo | Descripción | Visible | Orden |
|--------|-------------|---------|-------|
| EXPLORADOR_BD | Explorador de Base de Datos | ✅ | 10 |

### EDARSAHUB_SQL - 1 módulo
| Módulo | Descripción | Visible | Orden |
|--------|-------------|---------|-------|
| EXPLORADOR_BD | Explorador de Base de Datos | ✅ | 10 |

---

## 7. DECISIONES PARA ENTERPRISE

### Situación Detectada
Los servidores "Enterprise" usan el system_type `SOFRESATAURANT_ENTER` (mal escrito) y están registrados como `tipo_conexion = 'API_LOCAL'`.

| Servidor | system_type | query_ventas |
|----------|-------------|--------------|
| CHAPUR NORTE | SOFRESATAURANT_ENTER | ❌ NO |
| CHAPUR NORTE BACKOFICE | SOFRESATAURANT_ENTER | ❌ NO |

### Decisión Tomada
1. ✅ Mapear `SOFRESATAURANT_ENTER` como variante de `API_LOCAL` (ID=3)
2. ✅ Activar capacidades de EXPLORADOR para API_LOCAL
3. ❌ **NO activar SYNC_VENTAS_*** hasta que se valide query_ventas
4. ✅ Incluir variantes: Enterprise, SOFTRESTAURANT_ENTERPRISE, SoftRestaurant Enterprise

---

## 8. CAPACIDADES SYNC ENTERPRISE

### Estado Actual
| Capacidad | Activada para API_LOCAL |
|-----------|-------------------------|
| SYNC_VENTAS_HISTORICAS | ❌ NO |
| SYNC_VENTAS_POR_HORA | ❌ NO |
| SYNC_VENTAS_DIA_SEMANA | ❌ NO |

### Razón
Los servidores Enterprise (CHAPUR NORTE, CHAPUR NORTE BACKOFICE) **no tienen `query_ventas` configurada**.

### Acción Pendiente
Para activar sync de ventas en Enterprise:
1. Definir y validar query_ventas para SoftRestaurant Enterprise
2. Configurar query_ventas en Servidores_Conexiones para CHAPUR NORTE
3. Ejecutar INSERT adicional en Sistema_Capacidades para API_LOCAL

---

## 9. VALIDACIONES POST-EJECUCIÓN

| Validación | Resultado |
|------------|-----------|
| Capacidades por sistema | ✅ Correcto |
| Variantes por sistema | ✅ Correcto |
| Visibilidad por sistema | ✅ Correcto |
| Cero duplicados en Capacidades | ✅ 0 duplicados |
| Cero duplicados en Variantes | ✅ 0 duplicados |
| FKs válidas en Capacidades | ✅ 0 inválidas |
| FKs válidas en Variantes | ✅ 0 inválidas |
| Sistema_Tipos no alterada | ✅ 5 registros |
| Backend operativo | ✅ |
| Login funcional | ✅ |
| Explorador BD | ✅ 12 conexiones |
| /api/consultas-sql/* | ✅ Funcional |
| MongoDB usado | ❌ NO |
| Secrets expuestos | ❌ NO |

---

## 10. NO REGRESIÓN

### Endpoints Verificados
| Endpoint | Estado |
|----------|--------|
| POST /api/auth/login | ✅ Operativo |
| GET /api/explorador/conexiones-explorables | ✅ 12 conexiones |
| GET /api/catalogos/sistemas/activos | ✅ 5 sistemas |
| GET /api/servers | ✅ 8 servidores |
| GET /api/consultas-sql/disponibles | ✅ Operativo |

### Módulos NO Afectados
- Comercial
- Tablero Ejecutivo
- Compras
- Finanzas
- Operaciones
- Sync Históricos
- Auth/RBAC

---

## 11. RIESGOS PENDIENTES

| Riesgo | Mitigación |
|--------|------------|
| Enterprise sin sync ventas | Documentado como pendiente |
| Variantes case-sensitive | Resolver normalizará a mayúsculas |
| Nuevos sistemas futuros | Agregar via SQL, no código |

---

## 12. RECOMENDACIÓN PARA FASE 4 SystemCapabilityResolver

### Próximo Paso
Implementar el **SystemCapabilityResolver** en backend:

```python
# /app/backend/core/system_capability_resolver.py

class SystemCapabilityResolver:
    """
    Resolver central para capacidades de sistemas.
    FUENTE: EDARSAHUB SQL (Sistema_Capacidades, Sistema_TiposVariantes)
    """
    
    def normalize_system_type(self, system_type: str) -> str:
        """Normaliza variantes a código canónico usando Sistema_TiposVariantes"""
        
    def system_supports(self, codigo_sistema: str, capacidad: str) -> bool:
        """Verifica si un sistema soporta una capacidad"""
        
    def get_systems_for_capability(self, capacidad: str) -> List[str]:
        """Obtiene sistemas que soportan una capacidad"""
        
    def get_visible_systems_for_module(self, modulo: str) -> List[Dict]:
        """Obtiene sistemas visibles para un módulo"""
```

### Funcionalidades Clave
1. **normalize_system_type()**: Usar `Sistema_TiposVariantes` para mapear 'SOFRESATAURANT_ENTER' → 'API_LOCAL'
2. **system_supports()**: Consultar `Sistema_Capacidades` para validar soporte
3. **get_systems_for_capability()**: Obtener lista dinámica de sistemas por capacidad
4. **get_visible_systems_for_module()**: Filtrar por `Sistema_ModulosVisibilidad`

### Beneficios Esperados
- Eliminar hardcoding de `['MPRO', 'SoftRestaurant']` en frontend
- Agregar nuevos sistemas sin modificar código
- Activar/desactivar capacidades desde SQL

---

## 13. CONCLUSIÓN

**FASE 3 SEED completada exitosamente.**

- 40 capacidades insertadas para 4 sistemas
- 18 variantes de nombres insertadas
- 16 registros de visibilidad insertados
- Sin duplicados detectados
- FKs 100% válidas
- Sistema_Tipos intacta
- Backend 100% operativo
- Sin regresión detectada

**Próximo paso:** Autorización para FASE 4 - Implementar SystemCapabilityResolver.

---

**Autor:** Arquitecto Senior Backend/DBA  
**Revisado:** Auto-validado  
**Aprobado:** Pendiente confirmación usuario
