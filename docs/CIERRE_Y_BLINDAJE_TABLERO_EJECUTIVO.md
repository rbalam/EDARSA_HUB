# CIERRE Y BLINDAJE - TABLERO EJECUTIVO EDARSA HUB
## Documento de Control de Cambios y Protección
## Fecha de Cierre: 2026-04-19
## Versión: 1.0.0 - CONGELADA

---

# ⚠️ ADVERTENCIA CRÍTICA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   TABLERO EJECUTIVO CERRADO Y BLINDADO                                       ║
║                                                                               ║
║   NO MODIFICAR SIN AUTORIZACIÓN EXPRESA Y CAMBIO CONTROLADO                  ║
║                                                                               ║
║   Este documento establece el estado oficial y congelado del Tablero          ║
║   Ejecutivo de EDARSA HUB. Cualquier modificación debe seguir el             ║
║   protocolo de cambio controlado establecido en la Sección XII.              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# I. RESUMEN EJECUTIVO

## Estado del Tablero
- **Estado**: ✅ ESTABLE, VALIDADO, CONGELADO FUNCIONALMENTE
- **Fecha de Cierre**: 2026-04-19
- **Última Validación**: Abril 2026 - $9,258,756.71 en ventas consolidadas
- **Unidades Activas**: 5 (CIENFUEGOS, LA ESTELAR, 130° MERIDA, ORIGEN, 130° QUERETARO)
- **Sistemas Integrados**: SoftRestaurant, MPRO

## Valores de Referencia (Abril 2026)
| Métrica | Valor Validado |
|---------|----------------|
| Ventas Acumuladas | $9,258,756.71 |
| PAX | 9,316 |
| Cheques | 3,216 |
| Ticket Promedio | $2,878.83 |
| Proyección Mensual | ~$15.6M |
| Var vs Mes Anterior | -3.5% |
| Var vs Año Anterior | +6.4% |

---

# II. ALCANCE CERRADO

## Funcionalidades Incluidas
1. ✅ Ventas acumuladas por período (mes/meses/año)
2. ✅ Ventas del día (operación actual)
3. ✅ PAX (comensales)
4. ✅ Cheques (tickets)
5. ✅ Ticket promedio
6. ✅ Proyección de ventas
7. ✅ Comparativo vs mes anterior
8. ✅ Comparativo vs año anterior (días equivalentes)
9. ✅ Detalle por unidad de negocio
10. ✅ Consolidado general

## Funcionalidades EXCLUIDAS del Tablero
- Inventarios (módulo separado)
- Finanzas (módulo separado)
- RH/Nómina (módulo separado)
- Compras (módulo separado)

---

# III. KPIs Y DEFINICIÓN FUNCIONAL

## 3.1 Ventas Acumuladas
- **Definición**: Suma de ventas cerradas en el período seleccionado
- **Fuente SoftRestaurant**: `cheques.total` WHERE `pagado=1 AND cancelado=0`
- **Fuente MPRO**: `Venta_Encabezado.Vn_Precio_Neto_Importe` WHERE `Es_Cve_Estado <> 'CA'`
- **Filtro de fecha**: Por apertura de turno (SoftRestaurant) / Por fecha de venta (MPRO)

## 3.2 Ventas del Día
- **Definición**: Ventas de la operación actual (turnos abiertos + último cerrado)
- **Fuente SoftRestaurant**: `tempcheques.total` (primero) o `cheques` del día
- **Fuente MPRO**: API local `/api/ventas/dia`
- **Comportamiento**: Se actualiza en tiempo real durante la operación

## 3.3 PAX (Comensales)
- **Definición**: Número de personas atendidas
- **Fuente SoftRestaurant**: `cheques.nopersonas`
- **Fuente MPRO**: `Comanda.Co_Personas`

## 3.4 Cheques (Tickets)
- **Definición**: Número de cuentas/folios cerrados
- **Fuente SoftRestaurant**: `COUNT(cheques.folio)`
- **Fuente MPRO**: `COUNT(DISTINCT Venta_Encabezado.Vn_Folio)`

## 3.5 Ticket Promedio
- **Definición**: Ventas / Cheques
- **Cálculo**: Se realiza en backend después de obtener ventas y cheques
- **Validación**: Si cheques = 0, ticket promedio = 0

## 3.6 Proyección
- **Definición**: Estimación de ventas al cierre del mes
- **Cálculo**: `(Ventas acumuladas / Días transcurridos) * Días del mes`
- **Nota**: Solo aplica para mes actual o parcial

## 3.7 Comparativos
- **vs Mes Anterior**: Compara mismos días del mes anterior
- **vs Año Anterior**: Compara mismos días del año anterior
- **Fórmula**: `((Actual - Anterior) / Anterior) * 100`

---

# IV. MATRIZ DE FUENTES POR KPI

| KPI | SoftRestaurant | MPRO | Tabla/Endpoint | Validación |
|-----|----------------|------|----------------|------------|
| Ventas Acumuladas | SQL histórico | SQL histórico | cheques / Venta_Encabezado | ✅ |
| Ventas del Día | SQL tempcheques | API local | tempcheques / /api/ventas/dia | ✅ |
| PAX | SQL histórico | SQL histórico | cheques.nopersonas / Comanda | ✅ |
| Cheques | SQL histórico | SQL histórico | COUNT(folio) / COUNT(Vn_Folio) | ✅ |
| Ticket Promedio | Cálculo backend | Cálculo backend | Ventas/Cheques | ✅ |
| Proyección | Cálculo backend | Cálculo backend | Extrapolación lineal | ✅ |
| Comparativo Mes Ant | SQL histórico | SQL histórico | Misma query, fechas ajustadas | ✅ |
| Comparativo Año Ant | SQL histórico | SQL histórico | Misma query, fechas ajustadas | ✅ |

---

# V. MATRIZ DE CONEXIONES POR UNIDAD

| Unidad | Sistema | Tipo Conexión | Origen Conexión | Acumulados | Día |
|--------|---------|---------------|-----------------|------------|-----|
| CIENFUEGOS | SoftRestaurant | SQL | Menú Servidores SQL | ✅ SQL | ✅ SQL tempcheques |
| LA ESTELAR | SoftRestaurant | SQL | Menú Servidores SQL | ✅ SQL | ✅ SQL tempcheques |
| 130° MERIDA | SoftRestaurant | SQL | Menú Servidores SQL | ✅ SQL | ✅ SQL tempcheques |
| ORIGEN | MPRO | SQL + API | Menú Servidores SQL | ✅ SQL MPRO | ✅ API local |
| 130° QUERETARO | MPRO | SQL + API | Menú Servidores SQL | ✅ SQL MPRO | ✅ API local |

### Reglas de Conexión
1. **SoftRestaurant**: TODA conexión sale del menú oficial de Servidores SQL
2. **MPRO Acumulados**: SQL desde menú Servidores SQL (servidor MPRO nube)
3. **MPRO Día**: API de servidores locales (cuando disponible)
4. **NO hay connection strings hardcodeados**
5. **NO hay bypass al menú de servidores**

---

# VI. FILTROS ACTIVOS Y COMPORTAMIENTO

## 6.1 Filtro de Período
| Parámetro | Valores | Comportamiento |
|-----------|---------|----------------|
| `meses` | "01"-"12" o "ventas_dia" | Mes(es) a consultar |
| `anios` | "2024", "2025", "2026" | Año(s) a consultar |
| `tipo_comparacion` | "dias_equiv" (default) | Comparación por días equivalentes |

## 6.2 Filtro de Unidad
- **Por defecto**: Todas las unidades permitidas por RBAC
- **Filtrable**: Por servidor específico (uso interno)

## 6.3 Comportamiento de Fechas
- **Fecha inicio**: Primer día del mes/período
- **Fecha fin**: Último día del mes O día actual (el menor)
- **Formato interno**: YYYYMMDD (sin guiones)

---

# VII. PARÁMETROS Y CONFIGURACIONES

## 7.1 Timeouts
```python
SQL_TIMEOUT_DEFAULT = 90  # segundos
SQL_TIMEOUT_API_LOCAL = 30  # segundos
LOGIN_TIMEOUT = 30  # segundos
```

## 7.2 Caché
```python
CACHE_TTL = 300  # 5 minutos
CACHE_COLLECTION = "kpis_cache"
```

## 7.3 Reintentos
```python
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # segundos
RETRY_BACKOFF = 2  # multiplicador
```

## 7.4 Flags Funcionales
| Flag | Valor | Descripción |
|------|-------|-------------|
| `solo_ventas_dia` | True/False | Modo solo ventas del día |
| `visible_en_operaciones` | True/False | Filtro de servidores visibles |
| `active` | True/False | Servidor activo/inactivo |

---

# VIII. REGLAS FUNCIONALES

## 8.1 Reglas de Cálculo
1. **Ventas acumuladas NO incluyen** ventas del día de turnos abiertos
2. **Ventas del día incluyen** tempcheques + último turno cerrado del día
3. **Comparativo usa días equivalentes**, no el mes completo
4. **Proyección es lineal** basada en días transcurridos

## 8.2 Reglas de Fuentes
1. **SoftRestaurant**: TODO por SQL (acumulados + día)
2. **MPRO Acumulados**: SOLO por SQL MPRO
3. **MPRO Día**: SOLO por API local (si disponible)
4. **NO mezclar** rutas SQL y API para el mismo KPI
5. **NO usar** fuentes alternativas sin autorización

## 8.3 Reglas de Error
1. Si falla conexión SQL → usar caché si existe
2. Si no hay caché → marcar como "offline"
3. **NUNCA** devolver $0 como venta real si hay error
4. **SIEMPRE** reportar status técnico: ok/partial/error/offline

---

# IX. CASOS DE PRUEBA DE REFERENCIA

## Prueba 1: Acumulado Mensual
```bash
GET /api/comercial/tablero-ejecutivo?meses=04&anios=2026
ESPERADO: Ventas > $0, PAX > 0, Cheques > 0, 5 unidades
```

## Prueba 2: Multiselección de Meses
```bash
GET /api/comercial/tablero-ejecutivo?meses=01,02,03&anios=2026
ESPERADO: Suma de los 3 meses, comparativos ajustados
```

## Prueba 3: Ventas del Día
```bash
GET /api/comercial/tablero-ejecutivo?meses=ventas_dia
ESPERADO: Ventas del día actual (puede ser $0 si no hay operación)
```

## Prueba 4: Comparativo Año Anterior
```bash
# Verificar que var_vs_año_ant sea número válido
ESPERADO: Porcentaje con signo (positivo o negativo)
```

## Prueba 5: Unidad con Error
```bash
# Simular servidor no disponible
ESPERADO: status="offline", usar caché, NO mostrar $0 falso
```

## Prueba 6: Consolidado General
```bash
# Sumar todas las unidades
ESPERADO: totales.ventas = SUM(unidades[].ventas)
```

---

# X. ARCHIVOS CRÍTICOS (NO MODIFICAR SIN AUTORIZACIÓN)

## Backend - Core
| Archivo | Función | Criticidad |
|---------|---------|------------|
| `/app/backend/core/connection_resolver.py` | Resolver central de conexiones | 🔴 CRÍTICO |
| `/app/backend/core/providers.py` | Providers por sistema | 🔴 CRÍTICO |
| `/app/backend/core/db.py` | Conexiones SQL | 🔴 CRÍTICO |
| `/app/backend/core/server_connection_manager.py` | Gestor de conexiones | 🟡 ALTO |

## Backend - Comercial
| Archivo | Función | Criticidad |
|---------|---------|------------|
| `/app/backend/modules/comercial/service.py` | Lógica de KPIs | 🔴 CRÍTICO |
| `/app/backend/modules/comercial/routes.py` | Endpoint tablero | 🔴 CRÍTICO |
| `/app/backend/modules/comercial/repository.py` | Acceso a datos | 🟡 ALTO |

## Frontend
| Archivo | Función | Criticidad |
|---------|---------|------------|
| `/app/frontend/src/pages/Comercial.js` | UI del tablero | 🟡 ALTO |
| `/app/frontend/src/services/comercialApi.js` | Llamadas al API | 🟡 ALTO |

---

# XI. RIESGOS CONOCIDOS

## 11.1 Riesgos de Infraestructura
| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| Servidor SQL no accesible | Caché + status offline | ✅ Implementado |
| API local no disponible | Fallback a SQL para acumulados | ✅ Implementado |
| Timeout de conexión | Reintentos con backoff | ✅ Implementado |

## 11.2 Riesgos de Datos
| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| Datos duplicados | Filtros únicos en queries | ✅ Validado |
| Fechas mal formateadas | Helper centralizado | ✅ Implementado |
| Ventas canceladas | Filtro Es_Cve_Estado <> 'CA' | ✅ Implementado |

## 11.3 Riesgos de Regresión
| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| Cambio incidental en queries | Este documento de blindaje | ✅ Establecido |
| Modificación de fuentes | Protocolo de cambio controlado | ✅ Establecido |
| Mezcla de rutas SQL/API | Matriz de resolución fija | ✅ Documentado |

---

# XII. PROTOCOLO DE CAMBIO CONTROLADO

## ⚠️ REGLA FORMAL

```
CUALQUIER MODIFICACIÓN AL TABLERO EJECUTIVO REQUIERE:

1. Solicitud explícita y documentada
2. Alcance específico del cambio
3. Identificación exacta del KPI afectado
4. Snapshot previo de archivos
5. Pruebas de no regresión (todos los casos de Sección IX)
6. Validación del consolidado general
7. Validación de cada unidad individual
8. Actualización de este documento
9. Aprobación antes de merge/deploy

PROHIBIDO:
- Cambiar "de pasada" al tocar otro módulo
- Refactorizar "para mejorar" sin autorización
- Modificar queries sin documentar
- Cambiar fuentes de datos sin análisis de impacto
```

## Checklist de Cambio Controlado
- [ ] Solicitud documentada con justificación
- [ ] KPI(s) afectado(s) identificado(s)
- [ ] Snapshot de archivos críticos
- [ ] Prueba: Acumulado mensual
- [ ] Prueba: Multiselección de meses
- [ ] Prueba: Ventas del día
- [ ] Prueba: Comparativo año anterior
- [ ] Prueba: Comportamiento con error
- [ ] Prueba: Consolidado = suma de unidades
- [ ] Documento actualizado
- [ ] Aprobación obtenida

---

# XIII. REGISTRO DE VERSIONES

| Versión | Fecha | Descripción | Autor |
|---------|-------|-------------|-------|
| 1.0.0 | 2026-04-19 | Cierre y blindaje inicial | Arquitecto EDARSA HUB |

---

# XIV. FIRMAS Y APROBACIONES

## Cierre de Fase
- **Fecha**: 2026-04-19
- **Estado**: CONGELADO FUNCIONALMENTE
- **Responsable**: Arquitecto de Software Senior

## Validaciones Realizadas
- [x] Ventas acumuladas funcionando
- [x] Ventas del día funcionando
- [x] Comparativos funcionando
- [x] 5 unidades reportando
- [x] Sin ceros falsos por error técnico
- [x] Caché funcionando
- [x] Fuentes correctamente asignadas
- [x] Documentación completa

---

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   TABLERO EJECUTIVO CERRADO Y BLINDADO                                       ║
║                                                                               ║
║   Versión: 1.0.0 - CONGELADA                                                 ║
║   Fecha: 2026-04-19                                                          ║
║                                                                               ║
║   NO MODIFICAR SIN AUTORIZACIÓN EXPRESA Y CAMBIO CONTROLADO                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```
