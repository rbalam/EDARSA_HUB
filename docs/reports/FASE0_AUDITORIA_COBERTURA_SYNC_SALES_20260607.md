# FASE 0 — Auditoría de Cobertura PIC (SOLO LECTURA)

Fecha: 2026-06-07
Alcance: diagnóstico de por qué `Sync_Sales` (detalle de producto) solo tiene 79 tickets, sin realizar cambios.

---

## 1. Métricas comparativas (datos reales)

### A) `dbo.Sync_Sales` (detalle con items JSON)
| Métrica | Valor |
|---|---|
| Tickets (distintos) | **79** |
| Líneas de producto (OPENJSON items) | **1,374** |
| Rango de fechas | **2026-06-01 00:00 → 2026-06-01 13:15** (un solo día) |
| Suma ventas (MontoTotal) | **$309,092.31** |
| Unidades | 5 (130MID=19, 130QRO=11, CIENFUEGOS=27, ESTELAR=2, ORIGEN=20) |
| `created_at` de las filas | **2026-06-03 00:20:50 → 00:21:37** (ventana de ~47 s) → carga puntual única |

### B) `dbo.vw_Comercial_KPIs_Diarios_v2_Runtime` (KPI canónico agregado)
| Métrica | Valor |
|---|---|
| Filas (día×unidad) | 3,392 |
| Unidades | 5 |
| Rango de fechas | **2024-05-01 → 2026-06-05** (~2 años) |
| Suma ventas_total | **$431,766,974.05** |
| Tickets_total | **125,833** |

### Diferencia A vs B (cobertura global del detalle)
| | Sync_Sales (detalle) | KPI canónico | Cobertura |
|---|---|---|---|
| Tickets | 79 | 125,833 | **0.06%** |
| Ventas | $309,092 | $431,766,974 | **0.07%** |
| Días | 1 | ~766 | **~0.13%** |

### C) Mismo día (2026-06-01): el detalle SÍ está completo
| Unidad | KPI tickets | Sync tickets | KPI ventas | Sync ventas |
|---|---|---|---|---|
| 130 MÉRIDA | 17 | 19 | 79,474 | 80,309 |
| 130 QUERÉTARO | 11 | 11 | 69,731 | 69,731 |
| CIENFUEGOS | 27 | 27 | 101,260 | 102,260 |
| LA ESTELAR | 3 | 2 | 560 | 560 |
| ORIGEN | 20 | 20 | 56,232 | 56,232 |
| **TOTAL** | **78** | **79** | **307,257** | **309,092** |

**Cobertura del 2026-06-01 ≈ 100%.** El detalle por producto está completo y cuadra con el KPI **para ese día**. El problema NO es el parser de items ni la calidad del detalle: es que **solo se cargó un día**.

---

## 2. CAUSA RAÍZ EXACTA (encontrada en el código, no inventada)

Archivo: `backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py`

### Causa 1 — Sin backfill histórico: ventana fija de 1 día
- `job_inteligencia_comercial_sync(dias_atras: int = 1, ...)` (línea 364-365).
- `fecha_fin = datetime.now()`, `fecha_inicio = fecha_fin - timedelta(days=dias_atras)` (líneas 381-382).
- Cron registrado en `Sys_Scheduler_Jobs`: `inteligencia_comercial_sync` = `0 * * * *` (cada hora), `LastRunDate = 2026-06-06 11:00`.
- Conclusión: cada corrida solo intenta "ayer→hoy". **No existe mecanismo de backfill** de 2024-2026. Los 79 tickets del 2026-06-01 fueron una **carga puntual única** (todos los `created_at` dentro de 47 segundos del 2026-06-03), no producto de la extracción recurrente.

### Causa 2 — La conexión al POS es un STUB (nunca llega al POS real)
- `get_pos_connection(config)` (líneas 94-100) **ignora `config`** y hace `return get_sql_connection()` → conecta a **EDARSAHUB**, NO a los servidores POS (SoftRestaurant `servercienfuegos.ddns.net,6669`, MPRO, etc.).
- Las queries de extracción (`get_softrestaurant_query`, `get_mpro_query`) corren entonces contra EDARSAHUB.
- Tablas POS en EDARSAHUB: `cheques`=NO, `turnos`=NO, `cheqdet`=NO, `productos`=NO, `Articulo`=NO, `Comanda`=NO (las de SoftRestaurant/MPRO **no existen**). `Venta_Encabezado`=SÍ, `Venta_Detalle`=SÍ (pero incompletas para este flujo).
- Credenciales POS en entorno: `CIENFUEGOS_DB_PASS`, `130MID_DB_PASS`, `ESTELAR_DB_PASS`, `130QRO_DB_PASS`, `ORIGEN_DB_PASS` → **TODAS VACÍAS**.
- Conclusión: aunque se corra el job, **no puede extraer detalle real** del POS (sin credenciales, sin conectividad, sin tablas origen en el destino stub).

### Consecuencia arquitectónica
- El **detalle a nivel ticket/producto histórico NO existe en ninguna parte de EDARSAHUB**. Solo la tabla agregada `Comercial_KPIs_Diarios_v2` (sumas diarias por unidad, **sin producto**) tiene el histórico completo.
- Por lo tanto, NO es posible "descomponer" el KPI agregado en productos. Para tener 100% de detalle histórico se requiere **extraer del POS real** (SoftRestaurant/MPRO) con credenciales y conectividad válidas, y hacer **backfill** del periodo.

---

## 3. BLOQUEADOR para FASE 1

La FASE 1 ("corregir el sync para traer 100% tickets/detalle") es **inviable en este entorno** mientras:
1. Las credenciales POS (`*_DB_PASS`) estén vacías.
2. Los servidores POS externos (DDNS) no sean alcanzables desde el pod.
3. `get_pos_connection` siga apuntando a EDARSAHUB en vez del POS (esto sí es corregible en código, pero sin (1) y (2) no sirve).

**Se requiere decisión/insumo del usuario antes de FASE 1** (ver opciones en el chat).

---

## 4. Lo que NO se hizo (por mandato)
- No se modificó ningún dato ni esquema.
- No se ejecutó el script de "Dimensiones Operativas" recibido (es FASE 1+ y depende del POS bloqueado; además referencia columnas `PIC_*` inexistentes — ver auditoría en el chat).
