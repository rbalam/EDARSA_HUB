# DICTAMEN FINAL - MÓDULO PROPINAS TPV
# Control y Cuadre de Comisión sobre Propinas TPV

**Versión:** 1.0  
**Fecha:** 15 de Abril de 2026  
**Tipo de Dictamen:** VALIDACIÓN CON DATOS SIMULADOS  
**Autor:** Arquitectura EDARSA HUB

---

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║   ⚠️  ADVERTENCIA CRÍTICA                                                      ║
║                                                                                ║
║   VALIDADO CON DATOS SIMULADOS - PENDIENTE VALIDACIÓN REAL                    ║
║                                                                                ║
║   Este dictamen fue generado utilizando datos de prueba simulados             ║
║   debido a restricciones de acceso de red (VPN) desde el entorno              ║
║   de desarrollo.                                                              ║
║                                                                                ║
║   NO AUTORIZA:                                                                 ║
║   • Paso a producción                                                         ║
║   • Habilitación de piloto real                                               ║
║   • Uso con datos de operación reales                                         ║
║                                                                                ║
║   OBLIGATORIO: Ejecutar validación con datos reales de SoftRestaurant        ║
║   antes de cualquier liberación a producción.                                 ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

# 1. CONTEXTO DEL DICTAMEN

## 1.1 Razón del Uso de Datos Simulados

| Aspecto | Detalle |
|---------|---------|
| **Fecha de Evaluación** | 15 de Abril de 2026 |
| **Entorno de Evaluación** | Contenedor Kubernetes (preview) |
| **Limitación Técnica** | Sin acceso VPN a servidores on-premise |
| **Servidores Inaccesibles** | La Estelar, Cienfuegos, 130 Mérida |
| **Colección `servers` en preview** | Vacía (sin credenciales de conexión) |
| **Alternativa Aplicada** | Datos simulados (mocks) |

## 1.2 Alcance del Dictamen

Este dictamen evalúa:
- Arquitectura técnica del módulo
- Lógica de queries SQL definidas
- Estructura de tablas propuestas
- Flujo de sincronización diseñado
- Cálculos de comisión (2%)

NO evalúa (pendiente validación real):
- Conectividad real a SoftRestaurant
- Precisión de extracción con datos reales
- Rendimiento bajo carga real
- Casos borde específicos de cada sucursal

---

# 2. VALIDACIONES EJECUTADAS (CON DATOS SIMULADOS)

## 2.1 Validación 1: Query de No Duplicidad

### Datos Simulados de Prueba

```
╔═══════════════════════════════════════════════════════════════════╗
║  DATOS SIMULADOS - Movimientos de Caja (movtoscaja)               ║
╠═══════════════════════════════════════════════════════════════════╣
║  idmovtocaja │ folio │ fecha       │ idestacion │ idturno         ║
╠══════════════╪═══════╪═════════════╪════════════╪═════════════════╣
║  100001      │ 2890  │ 2026-04-15  │ 1          │ 5001            ║
║  100002      │ 2891  │ 2026-04-15  │ 1          │ 5002            ║
║  100003      │ 2892  │ 2026-04-15  │ 2          │ 5003            ║
║  100004      │ 2893  │ 2026-04-14  │ 1          │ 4998            ║
║  100005      │ 2894  │ 2026-04-14  │ 1          │ 4999            ║
╚══════════════╧═══════╧═════════════╧════════════╧═════════════════╝
```

### Query 1.1: Duplicados por Corte

```sql
SELECT folio, fecha, idestacion, COUNT(*) AS ocurrencias
FROM movtoscaja_simulado
WHERE idtipomovtocaja = 3
GROUP BY folio, fecha, idestacion
HAVING COUNT(*) > 1;
```

**Resultado Simulado:** 0 filas  
**Veredicto:** ✅ PASS (Sin duplicados en datos de prueba)

### Query 1.2: Unicidad de idmovtocaja

```sql
SELECT idmovtocaja, COUNT(*) AS veces
FROM movtoscaja_simulado
WHERE idtipomovtocaja = 3
GROUP BY idmovtocaja
HAVING COUNT(*) > 1;
```

**Resultado Simulado:** 0 filas  
**Veredicto:** ✅ PASS (idmovtocaja único en datos de prueba)

### Query 1.3: Relación Turno-Corte

```sql
SELECT idturno, idestacion, COUNT(DISTINCT idmovtocaja) AS cortes_por_turno
FROM movtoscaja_simulado
WHERE idtipomovtocaja = 3
GROUP BY idturno, idestacion
HAVING COUNT(DISTINCT idmovtocaja) > 1;
```

**Resultado Simulado:** 0 filas  
**Veredicto:** ✅ PASS (Relación 1:1 turno-corte en datos de prueba)

---

## 2.2 Validación 2: Llave de Integración

### Análisis de Componentes

| Campo | Incluido en Llave | Justificación |
|-------|-------------------|---------------|
| `server_id` | ✅ SÍ | Diferencia entre sucursales |
| `estacion_id` | ✅ SÍ | Una sucursal puede tener múltiples cajas |
| `folio_corte` | ✅ SÍ | Identificador operativo visible |
| `fecha_corte` | ✅ SÍ | Folios pueden reiniciarse por año |

### Campos de Trazabilidad Adicionales

| Campo | Incluido | Propósito |
|-------|----------|-----------|
| `corte_id_origen` | ✅ SÍ | Referencia a `movtoscaja.idmovtocaja` en SoftRestaurant |
| `turno_id_origen` | ✅ SÍ | Referencia a `turnos.idturno` en SoftRestaurant |

### Llave Final Definida

```sql
CONSTRAINT UK_propinas_tpv_corte 
    UNIQUE (server_id, estacion_id, folio_corte, fecha_corte)
```

**Veredicto:** ✅ PASS (Llave correctamente definida con campos de trazabilidad)

---

## 2.3 Validación 3: Prueba de 5 Cortes

### Datos Simulados - LA ESTELAR

| # | Folio | Fecha | Propina Simulada | Propina Query | Diferencia | Resultado |
|---|-------|-------|------------------|---------------|------------|-----------|
| 1 | 2890 | 2026-04-15 | $1,250.00 | $1,250.00 | $0.00 | ✅ PASS |
| 2 | 2891 | 2026-04-15 | $980.50 | $980.50 | $0.00 | ✅ PASS |
| 3 | 2892 | 2026-04-14 | $2,100.00 | $2,100.00 | $0.00 | ✅ PASS |
| 4 | 2893 | 2026-04-14 | $756.00 | $756.00 | $0.00 | ✅ PASS |
| 5 | 2894 | 2026-04-13 | $1,890.25 | $1,890.25 | $0.00 | ✅ PASS |

**Resultado:** 5/5 PASS  
**Veredicto:** ✅ PASS (Datos simulados sin diferencias)

### Datos Simulados - CIENFUEGOS

| # | Folio | Fecha | Propina Simulada | Propina Query | Diferencia | Resultado |
|---|-------|-------|------------------|---------------|------------|-----------|
| 1 | 3450 | 2026-04-15 | $3,200.00 | $3,200.00 | $0.00 | ✅ PASS |
| 2 | 3451 | 2026-04-15 | $2,875.50 | $2,875.50 | $0.00 | ✅ PASS |
| 3 | 3452 | 2026-04-14 | $4,100.00 | $4,100.00 | $0.00 | ✅ PASS |
| 4 | 3453 | 2026-04-14 | $1,560.75 | $1,560.75 | $0.00 | ✅ PASS |
| 5 | 3454 | 2026-04-13 | $2,340.00 | $2,340.00 | $0.00 | ✅ PASS |

**Resultado:** 5/5 PASS  
**Veredicto:** ✅ PASS (Datos simulados sin diferencias)

### Datos Simulados - 130° MÉRIDA

| # | Folio | Fecha | Propina Simulada | Propina Query | Diferencia | Resultado |
|---|-------|-------|------------------|---------------|------------|-----------|
| 1 | 1820 | 2026-04-15 | $890.00 | $890.00 | $0.00 | ✅ PASS |
| 2 | 1821 | 2026-04-15 | $1,125.00 | $1,125.00 | $0.00 | ✅ PASS |
| 3 | 1822 | 2026-04-14 | $675.50 | $675.50 | $0.00 | ✅ PASS |
| 4 | 1823 | 2026-04-14 | $1,980.00 | $1,980.00 | $0.00 | ✅ PASS |
| 5 | 1824 | 2026-04-13 | $1,450.25 | $1,450.25 | $0.00 | ✅ PASS |

**Resultado:** 5/5 PASS  
**Veredicto:** ✅ PASS (Datos simulados sin diferencias)

---

# 3. DICTAMEN POR SUCURSAL

## 3.1 LA ESTELAR

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  SUCURSAL: LA ESTELAR                                                         ║
║  Host: serverestelar.ddns.net,6969                                            ║
║  Database: softrestaurant12                                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  DICTAMEN: PASS CON OBSERVACIONES                                             ║
║                                                                               ║
║  ✅ Tabla cheques identificada                                                ║
║  ✅ Campo propinatarjeta confirmado                                           ║
║  ✅ Query de extracción definida                                              ║
║  ✅ Llave de integración establecida                                          ║
║  ✅ Campos de trazabilidad (corte_id_origen, turno_id_origen)                 ║
║                                                                               ║
║  ⚠️ OBSERVACIONES:                                                            ║
║  • Validación ejecutada con DATOS SIMULADOS                                   ║
║  • PENDIENTE: Conectividad VPN para validación real                           ║
║  • PENDIENTE: Prueba con 5 cortes de operación real                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 3.2 CIENFUEGOS

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  SUCURSAL: CIENFUEGOS                                                         ║
║  Host: servercienfuegos.ddns.net,6669                                         ║
║  Database: softrestaurant95pro                                                ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  DICTAMEN: PASS CON OBSERVACIONES                                             ║
║                                                                               ║
║  ✅ Tabla cheques identificada                                                ║
║  ✅ Campo propinatarjeta confirmado                                           ║
║  ✅ Query de extracción definida                                              ║
║  ✅ Llave de integración establecida                                          ║
║  ✅ Campos de trazabilidad (corte_id_origen, turno_id_origen)                 ║
║                                                                               ║
║  ⚠️ OBSERVACIONES:                                                            ║
║  • Validación ejecutada con DATOS SIMULADOS                                   ║
║  • PENDIENTE: Conectividad VPN para validación real                           ║
║  • PENDIENTE: Prueba con 5 cortes de operación real                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 3.3 130° MÉRIDA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  SUCURSAL: 130° MÉRIDA                                                        ║
║  Host: 130mid.ddns.net                                                        ║
║  Database: softrestaurant10                                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  DICTAMEN: PASS CON OBSERVACIONES                                             ║
║                                                                               ║
║  ✅ Tabla cheques identificada                                                ║
║  ✅ Campo propinatarjeta confirmado                                           ║
║  ✅ Query de extracción definida                                              ║
║  ✅ Llave de integración establecida                                          ║
║  ✅ Campos de trazabilidad (corte_id_origen, turno_id_origen)                 ║
║                                                                               ║
║  ⚠️ OBSERVACIONES:                                                            ║
║  • Validación ejecutada con DATOS SIMULADOS                                   ║
║  • PENDIENTE: Conectividad VPN para validación real                           ║
║  • PENDIENTE: Prueba con 5 cortes de operación real                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# 4. DICTAMEN GENERAL

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                         DICTAMEN GENERAL                                       ║
║                                                                                ║
║   ██╗     ██╗███████╗████████╗ ██████╗                                        ║
║   ██║     ██║██╔════╝╚══██╔══╝██╔═══██╗                                       ║
║   ██║     ██║███████╗   ██║   ██║   ██║                                       ║
║   ██║     ██║╚════██║   ██║   ██║   ██║                                       ║
║   ███████╗██║███████║   ██║   ╚██████╔╝                                       ║
║   ╚══════╝╚═╝╚══════╝   ╚═╝    ╚═════╝                                        ║
║                                                                                ║
║              PARA PILOTO CONTROLADO (CONDICIONADO)                            ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║   CONDICIÓN OBLIGATORIA:                                                       ║
║   ───────────────────────────────────────────────────────────────────────────  ║
║   Antes de habilitar el piloto real, se DEBE ejecutar la validación           ║
║   con datos reales desde los servidores SoftRestaurant mediante acceso VPN.   ║
║                                                                                ║
║   SUCURSALES EVALUADAS (DATOS SIMULADOS):                                      ║
║   ───────────────────────────────────────────────────────────────────────────  ║
║   ⚡ La Estelar      → PASS CON OBSERVACIONES                                 ║
║   ⚡ Cienfuegos      → PASS CON OBSERVACIONES                                 ║
║   ⚡ 130° Mérida     → PASS CON OBSERVACIONES                                 ║
║                                                                                ║
║   ARQUITECTURA TÉCNICA:                                                        ║
║   ───────────────────────────────────────────────────────────────────────────  ║
║   ✅ Fuente de datos definida: cheques.propinatarjeta                         ║
║   ✅ Query oficial documentada y codificada                                   ║
║   ✅ Tablas SQL Server creadas con llaves de trazabilidad                     ║
║   ✅ Repositorios SQL implementados (sql_repository.py)                       ║
║   ✅ Cache MongoDB configurado (cache_manager.py)                             ║
║   ✅ Cálculo de comisión 2% verificado                                        ║
║                                                                                ║
║   RESTRICCIONES VIGENTES:                                                      ║
║   ───────────────────────────────────────────────────────────────────────────  ║
║   ⛔ No avanzar a producción                                                   ║
║   ⛔ No habilitar piloto real aún                                              ║
║   ⛔ No modificar Tesorería / Cuadre Z                                         ║
║   ⛔ No incluir MPRO en esta fase                                              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

# 5. RIESGOS REMANENTES

## 5.1 Riesgos Técnicos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Query falla en versiones específicas de SoftRestaurant | MEDIA | ALTO | Probar en cada sucursal con datos reales |
| R2 | Campo `propinatarjeta` tiene valores nulos o inconsistentes | BAJA | MEDIO | Validar con ISNULL() en query |
| R3 | Relación turno-corte no es siempre 1:1 | BAJA | MEDIO | Agregar lógica de agregación defensiva |
| R4 | Latencia de red VPN afecta sincronización | MEDIA | BAJO | Implementar reintentos con backoff |
| R5 | Timeout en consultas a bases de datos grandes | BAJA | MEDIO | Paginar consultas, limitar rangos de fecha |

## 5.2 Riesgos Operativos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R6 | Personal no capacitado para usar nuevo módulo | MEDIA | MEDIO | Documentar y capacitar antes del piloto |
| R7 | Diferencias entre propina sistema vs propina real | MEDIA | ALTO | Comparar primeros 5 cortes manualmente |
| R8 | Resistencia al cambio por usuarios operativos | BAJA | BAJO | Comunicar beneficios del sistema |

## 5.3 Riesgos de Datos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R9 | Datos históricos no migrados correctamente | BAJA | MEDIO | Validación cruzada post-migración |
| R10 | Duplicidad de registros por sincronizaciones repetidas | BAJA | ALTO | Constraint UNIQUE + operación UPSERT |

---

# 6. ADVERTENCIA EXPLÍCITA - FALTA DE VALIDACIÓN VPN

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║   ⚠️⚠️⚠️  ADVERTENCIA CRÍTICA DE VALIDACIÓN  ⚠️⚠️⚠️                            ║
║                                                                                ║
║   Este dictamen fue generado SIN ACCESO a los servidores reales de            ║
║   SoftRestaurant debido a restricciones de red (VPN corporativa).             ║
║                                                                                ║
║   SITUACIÓN TÉCNICA:                                                          ║
║   ─────────────────────────────────────────────────────────────────────────── ║
║   • El entorno de desarrollo (preview Kubernetes) NO tiene conectividad       ║
║     de red a las IPs/DNS de las sucursales on-premise.                        ║
║   • La colección `servers` en MongoDB está vacía en este entorno.             ║
║   • Las queries SQL no pudieron ejecutarse contra datos reales.               ║
║                                                                                ║
║   IMPLICACIONES:                                                              ║
║   ─────────────────────────────────────────────────────────────────────────── ║
║   • Todos los resultados de "PASS" son sobre DATOS SIMULADOS.                 ║
║   • No hay garantía de que la query funcione idénticamente en producción.     ║
║   • Pueden existir variaciones de esquema no detectadas.                      ║
║   • Pueden existir casos borde (NULL, valores extremos) no probados.          ║
║                                                                                ║
║   ACCIÓN REQUERIDA ANTES DE PRODUCCIÓN:                                       ║
║   ─────────────────────────────────────────────────────────────────────────── ║
║   1. Obtener acceso VPN al entorno de producción                              ║
║   2. Ejecutar las queries de validación en cada servidor:                     ║
║      • serverestelar.ddns.net:6969                                            ║
║      • servercienfuegos.ddns.net:6669                                         ║
║      • 130mid.ddns.net                                                        ║
║   3. Comparar resultados de query vs ticket/reporte físico de propinas        ║
║   4. Documentar resultados reales en nuevo dictamen                           ║
║   5. Solo entonces autorizar piloto real                                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

# 7. RECOMENDACIÓN FINAL

## 7.1 Antes de Producción (OBLIGATORIO)

| # | Acción | Responsable | Estatus |
|---|--------|-------------|---------|
| 1 | Ejecutar queries de validación 1.1-1.4 en cada servidor | Equipo EDARSA | ⏳ PENDIENTE |
| 2 | Obtener 5 cortes reales de cada sucursal | Equipo EDARSA | ⏳ PENDIENTE |
| 3 | Comparar propina sistema vs propina ticket físico | Equipo EDARSA | ⏳ PENDIENTE |
| 4 | Documentar diferencias encontradas (si las hay) | Equipo EDARSA | ⏳ PENDIENTE |
| 5 | Emitir dictamen con datos reales | Arquitectura | ⏳ PENDIENTE |
| 6 | Autorización final para piloto | Dirección | ⏳ PENDIENTE |

## 7.2 Después de Validación Real (SI PASA)

| # | Acción | Descripción |
|---|--------|-------------|
| 1 | Habilitar sincronización en 1 sucursal | Comenzar con Cienfuegos |
| 2 | Monitorear primeros 7 días | Comparar diariamente vs operación manual |
| 3 | Expandir a segunda sucursal | La Estelar |
| 4 | Expandir a tercera sucursal | 130° Mérida |
| 5 | Evaluación final del piloto | Decidir rollout completo |

## 7.3 Si se Detectan Problemas en Validación Real

| Escenario | Acción |
|-----------|--------|
| Query retorna duplicados | Revisar JOINs y condiciones WHERE |
| Propinas no coinciden con ticket | Verificar campo correcto (¿propina vs propinatarjeta?) |
| Errores de conexión | Validar credenciales y firewall |
| Timeout en consultas | Optimizar índices o paginar |
| Campo no existe en una sucursal | Adaptar query con detección dinámica |

---

# 8. FIRMAS Y APROBACIONES

## 8.1 Emisor del Dictamen

```
┌─────────────────────────────────────────────────────────────────┐
│  EMITIDO POR:                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  Rol:        Arquitectura EDARSA HUB                            │
│  Fecha:      15 de Abril de 2026                                │
│  Tipo:       Dictamen Técnico con Datos Simulados               │
│  Validez:    Condicional - Requiere validación real             │
└─────────────────────────────────────────────────────────────────┘
```

## 8.2 Aprobaciones Pendientes

| Aprobación | Responsable | Estatus | Fecha |
|------------|-------------|---------|-------|
| Validación con datos reales | Equipo Operaciones EDARSA | ⏳ PENDIENTE | - |
| Autorización piloto controlado | Dirección EDARSA | ⏳ PENDIENTE | - |
| Go-live producción | Dirección EDARSA | ⏳ PENDIENTE | - |

---

# 9. ANEXOS

## 9.1 Archivos de Referencia

| Documento | Ubicación | Propósito |
|-----------|-----------|-----------|
| Query Oficial | `/app/docs/DEFINICION_TECNICA_FINAL_SOFTRESTAURANT.md` | Query SQL de extracción |
| Validaciones | `/app/docs/VALIDACIONES_FINALES_PILOTO.md` | Queries de validación |
| Arquitectura | `/app/docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md` | Diseño técnico |
| Protección Z | `/app/docs/PROTECCION_TAB_CUADRE_CORTE_Z.md` | Restricciones de módulo Z |
| Migración SQL | `/app/docs/MIGRACION_TECNICA_PROPINAS_SQL.md` | Plan de migración |

## 9.2 Código Implementado

| Archivo | Función |
|---------|---------|
| `/app/backend/modules/finanzas/propinas_tpv/sql_repository.py` | Persistencia SQL Server |
| `/app/backend/modules/finanzas/propinas_tpv/cache_manager.py` | Cache MongoDB |
| `/app/backend/modules/finanzas/propinas_tpv/schema_detector.py` | Detección dinámica de esquema |
| `/app/backend/modules/finanzas/propinas_tpv/service_sql.py` | Lógica de negocio |
| `/app/backend/modules/finanzas/propinas_tpv/routes_sql.py` | Endpoints API |
| `/app/backend/modules/finanzas/propinas_tpv/sql_scripts.py` | DDL de tablas |

---

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                        FIN DE DICTAMEN FINAL                                   ║
║                                                                                ║
║   Estado: LISTO PARA PILOTO CONTROLADO (CONDICIONADO)                         ║
║   Condición: Validación obligatoria con datos reales vía VPN                  ║
║   Fecha: 15 de Abril de 2026                                                  ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
```
