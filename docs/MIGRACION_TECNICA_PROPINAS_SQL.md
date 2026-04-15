# DOCUMENTO DE MIGRACIÓN TÉCNICA
# Módulo Propinas TPV: Arquitectura SQL + Cache

**Versión:** 1.0  
**Fecha:** 15 de Abril de 2026  
**Autor:** Arquitecto EDARSA HUB  
**CAB Referencia:** `ARQUITECTURA_PROPINAS_TPV_v3.md`

---

## 1. RESUMEN EJECUTIVO

### Cambio Implementado
Refactorización del módulo de Propinas TPV para usar SQL Server EDARSA HUB como fuente oficial de datos financieros, relegando MongoDB a un rol exclusivo de cache de lectura.

### Arquitectura Final

```
SoftRestaurant ──READ──► Backend ──WRITE──► SQL Server EDARSA HUB
                           │                        │
                           │                        │
                           └──CACHE──► MongoDB ◄────┘
                                         │
                                         ▼
                                     Frontend
```

### Estado de Producción
- **NO LIBERAR A PRODUCCIÓN TODAVÍA**
- Pendiente: Validación VPN de SoftRestaurant
- Pendiente: Pruebas end-to-end con datos reales

---

## 2. ARCHIVOS CREADOS

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `sql_scripts.py` | Scripts DDL para tablas SQL | ~250 |
| `sql_repository.py` | Repositorio de persistencia SQL | ~550 |
| `cache_manager.py` | Gestor de cache MongoDB | ~350 |
| `service_sql.py` | Servicio orquestador SQL + Cache | ~350 |
| `routes_sql.py` | Endpoints API refactorizados | ~400 |

### Total: ~1900 líneas de código nuevo

---

## 3. TABLAS SQL CREADAS

### 3.1 `propinas_tpv_control`
- **Propósito:** Registro oficial de control de propinas por corte
- **Registros esperados:** 1 por corte Z (~30-100/día)
- **Campos clave:**
  - Llave única: `(server_id, sucursal_id, folio_corte, fecha_corte)`
  - Datos operativos: propinas, ventas, comisión
  - Estado de cuadre: PENDIENTE, PAGADO, CUADRADO, DESCUADRE
  - Auditoría: fechas, usuarios, versión

### 3.2 `propinas_tpv_config`
- **Propósito:** Configuración jerárquica (GLOBAL → EMPRESA → SUCURSAL)
- **Campos clave:**
  - Alcance y vigencia
  - Porcentaje de comisión (default: 2%)
  - Tolerancia de descuadre (default: $5 MXN)
  - Mapeo de conceptos SoftRestaurant

### 3.3 `propinas_tpv_historial`
- **Propósito:** Auditoría de cambios
- **Campos clave:**
  - Acción realizada
  - Estado anterior/nuevo
  - Usuario y fecha
  - FK a propinas_tpv_control

---

## 4. COLECCIONES MONGODB (SOLO CACHE)

| Colección | TTL | Propósito |
|-----------|-----|-----------|
| `propinas_cache_listado` | 5 min | Cache de listados paginados |
| `propinas_cache_resumen` | 5 min | Cache de agregaciones |
| `propinas_cache_config` | 1 hora | Cache de configuración |
| `propinas_cache_detalle` | 10 min | Cache de detalles individuales |

### Características:
- Índices TTL para limpieza automática
- Invalidación en cada escritura SQL
- Keys basadas en hash de parámetros

---

## 5. FLUJO DE DATOS

### 5.1 Sincronización (Escritura)

```
1. Usuario solicita sincronización
         │
         ▼
2. Backend consulta SoftRestaurant (query defensiva)
         │
         ▼
3. Calcular comisión 2%
         │
         ▼
4. UPSERT en SQL Server (propinas_tpv_control)
         │
         ▼
5. Invalidar cache MongoDB
         │
         ▼
6. Retornar resultado
```

### 5.2 Consulta (Lectura)

```
1. Frontend solicita listado
         │
         ▼
2. Verificar cache MongoDB
         │
    ┌────┴────┐
    │         │
  VÁLIDO   EXPIRADO
    │         │
    ▼         ▼
 Retornar  Consultar SQL Server
            │
            ▼
         Actualizar cache
            │
            ▼
         Retornar
```

---

## 6. ENDPOINTS ACTUALIZADOS

| Endpoint | Método | Cambio |
|----------|--------|--------|
| `/api/finanzas/propinas/health` | GET | Ahora muestra arquitectura SQL + Cache |
| `/api/finanzas/propinas/inicializar-sql` | POST | **NUEVO** - Crea tablas SQL |
| `/api/finanzas/propinas/sincronizar` | POST | Escribe a SQL Server (antes: MongoDB) |
| `/api/finanzas/propinas` | GET | Lee de SQL con cache |
| `/api/finanzas/propinas/resumen` | GET | Lee de SQL con cache |
| `/api/finanzas/propinas/{id}` | GET | Lee de SQL con cache |
| `/api/finanzas/propinas/{id}/pago` | PUT | Escribe a SQL Server |
| `/api/finanzas/propinas/cache/stats` | GET | **NUEVO** - Estadísticas de cache |
| `/api/finanzas/propinas/cache/invalidar` | POST | **NUEVO** - Invalidar cache |

---

## 7. EVIDENCIA DE NO AFECTACIÓN A TESORERÍA

### Verificación Realizada

```bash
# Endpoint de Tesorería verificado
curl /api/finanzas/tesoreria/cuadres/resumen
# Resultado: OK (responde correctamente)
```

### Aislamiento Garantizado

| Aspecto | Tesorería (Protegido) | Propinas TPV (Refactorizado) |
|---------|----------------------|------------------------------|
| Router | `/api/finanzas/tesoreria/*` | `/api/finanzas/propinas/*` |
| Archivos | `tesoreria.py`, `repository_cuadres_z.py` | `routes_sql.py`, `sql_repository.py` |
| MongoDB | `tesoreria_cuadres_z` | `propinas_cache_*` (nuevas) |
| SQL Server | No usa | `propinas_tpv_*` (nuevas) |

### Archivos NO Modificados

- ✅ `TesoreriaCorteZ.jsx` (771 líneas intactas)
- ✅ `tesoreria.py` (endpoints intactos)
- ✅ `repository_cuadres_z.py` (lógica intacta)
- ✅ Colección `tesoreria_cuadres_z` (intacta)

---

## 8. RIESGOS PENDIENTES DE VALIDACIÓN VPN

| Riesgo | Mitigación |
|--------|------------|
| Esquema de SoftRestaurant varía | Query defensiva con `schema_detector.py` |
| Columna `idconcepto` no existe | Detección automática, fallback seguro |
| Timeout de conexión | Manejo de excepciones, reintentos |
| Datos inconsistentes | Validación antes de persistir |

### Acciones Requeridas Antes de Producción

1. **Validación VPN:** Ejecutar `/api/finanzas/propinas/detectar-esquema-todos` desde ambiente con VPN
2. **Preview de datos:** Ejecutar `/api/finanzas/propinas/preview` para validar lectura real
3. **Prueba de sincronización:** Ejecutar sincronización en ambiente de prueba
4. **Validación de cuadre:** Verificar cálculos de comisión con datos reales

---

## 9. PASOS PARA ACTIVAR EN PRODUCCIÓN

### Pre-requisitos
- [ ] Validación VPN completada
- [ ] Resultados de detección de esquema documentados
- [ ] Aprobación del usuario para continuar

### Secuencia de Activación

```
1. Ejecutar inicialización SQL
   POST /api/finanzas/propinas/inicializar-sql
   (Crea tablas en EDARSA HUB si no existen)

2. Validar tablas creadas
   Verificar en SQL Server: propinas_tpv_control, propinas_tpv_config, propinas_tpv_historial

3. Ejecutar sincronización de prueba
   POST /api/finanzas/propinas/sincronizar
   {"fecha_inicio": "2026-04-15", "fecha_fin": "2026-04-15"}

4. Validar datos sincronizados
   GET /api/finanzas/propinas?fecha_inicio=2026-04-15

5. Validar cache
   GET /api/finanzas/propinas/cache/stats

6. Monitorear logs de backend
   tail -f /var/log/supervisor/backend.out.log
```

---

## 10. CONCLUSIÓN

### Implementación Completada

| Componente | Estado |
|------------|--------|
| Scripts SQL DDL | ✅ Creado |
| Repositorio SQL | ✅ Creado |
| Cache Manager | ✅ Creado |
| Servicio SQL | ✅ Creado |
| Rutas SQL | ✅ Creado |
| Integración server.py | ✅ Actualizado |
| Health check | ✅ Funcionando |
| Tab Tesorería | ✅ NO AFECTADO |

### Próximos Pasos

1. **Inmediato:** Esperar validación VPN del usuario
2. **Post-validación:** Ejecutar inicialización SQL en EDARSA HUB
3. **Post-inicialización:** Pruebas de sincronización con datos reales
4. **Post-pruebas:** Desarrollo de frontend (tab separado)

---

**FIN DEL DOCUMENTO DE MIGRACIÓN TÉCNICA**
