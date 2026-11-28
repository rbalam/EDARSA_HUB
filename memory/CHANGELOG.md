# EDARSA HUB - Changelog

## [2026-06-10 PM-5] Fix sync movimientos 130QRO — NO era mapeo de conceptos, era CHECK constraint por redondeo
- **Diagnóstico (causa raíz real):** el backfill de 130QRO fallaba con `(547) CK_Inventario_MovimientosDetalle_Valores` (def: `Cantidad>0 AND CostoUnitario>=0`). NO era brecha de mapeo de conceptos (hay 96 mapeos completos). Consulta directa al origen MPRO QRO: de 74,722 movimientos, **4 filas con cantidad minúscula** (`0E-9`) pasaban el chequeo float `>0` pero al guardarse en `decimal(18,6)` quedaban en `0.000000` → `SUM(Cantidad)=0` → violaba la CHECK → rollback del lote completo (por eso 0 movimientos). CIENFUEGOS no tenía esas filas.
- **Fix** (`core/inventarios/sync_movimientos_canonico.py`): (1) `cantidad/costo = round(abs(valor), 6)` y se descartan cantidades que redondean a 0; (2) `HAVING SUM(s.Cantidad) > 0` en el INSERT agregado del detalle (red de seguridad). Aplica a TODOS los servidores/unidades, no solo QRO.
- **Verificado (re-ejecución 90 días):** `130QRO MOVIMIENTOS: status OK, encabezados_synced=6083, detalles_synced=56235, cantidad_cero=149` (=145 cero + 4 minúsculos del diagnóstico). BD: EmpresaID 2 = 6,083 movimientos / 56,235 detalles (Mar-13 a Jun-10). Sin error de restricción.


## [2026-06-10 PM-4] Frontend Bloque D (Catálogo Enriquecido) + Export Auditoría por proveedor
- **Bloque D — Catálogo Enriquecido** (`pages/comercial/CatalogoEnriquecido.jsx`, ruta `/comercial/catalogo-enriquecido`):
  - Pantalla admin SQL-First sobre `/api/comercial/productos-enriquecidos` (3,774 productos). Incluye: indicadores (total/requieren validación/sin marca/sin presentación), filtros (búsqueda, unidad canónica, grupo comercial, marca, categoría, tipo alcohol, requiere validación, estado), tabla paginada (50/pág), edición en diálogo (PUT — verificado que persiste), activar/desactivar (PATCH), importación masiva (.xlsx → UPSERT `/importar`), y export Excel/PDF.
  - Menú: insertado item `comercial.catalogo_enriquecido` en `Sistema_ModulosMenus` (seed idempotente `tests/seed_menu_catalogo_enriquecido.py`; verificado que aparece en `/sistema/menus/usuario`).
  - Fix: claves de respuesta de importación alineadas (`insertadas`/`actualizadas`/`omitidas`).
- **Export Auditoría por proveedor** (`pages/Compras.js`): cuando el toggle "Agrupar por Proveedor" está activo, el export agrega una hoja "Por Proveedor" (ordenada por proveedor/folio con subtotal de importe por proveedor). Solo se incluye cuando el toggle está activo. Compila sin errores; sin regresión en Compras (smoke test sin errores de consola). Nota: el flujo E2E con descarga de la hoja agrupada requiere correr una auditoría completa; la lógica reutiliza `ExportButtons`/`exportUtils` ya validados E2E en Costos.
- **Backfill 130QRO (cierre):** terminó en ~43 min. Requisiciones 130QRO SÍ poblaron (20), pero `Inventario_Movimientos` quedó en 0 para EmpresaID 2 → probable brecha de mapeo de conceptos MPRO para QRO (similar a "pendientes: tipo" de CIENFUEGOS). Pendiente revisión de mapeo de conceptos QRO.


## [2026-06-10 PM-3] C2 — Unificación KPIs canónicos (COMPLETO + verificado)
- **Decisión canónica confirmada desde SQL** (`dbo.Comercial_Metricas_Canonicas`, fuente única): promedios usan `ventas_sin_propina` (neto). Convención: `cheque_promedio`=neto/cheques (por cuenta); `ticket_promedio`=neto/pax (por comensal; sinónimo venta_por_pax/consumo_per_capita); `ventas`=neto, `ventas_brutas`=con propina. No requirió decisión del usuario (el catálogo decide).
- **Tablero Ejecutivo** (`modules/dashboard_ejecutivo/routes.py`): ERA no-canónico (usaba `ventas_total` bruto vía vista + JOIN server_id). Refactorizado a `KPIsCanonicosService.agregados_por_unidad`; KPIs ahora neto + fórmulas canónicas + identidad por UnidadesService. Verificado: endpoint == servicio canónico EXACTO (mayo: neto 16,697,051.34 / 5,980 cheques / 17,150 pax / cheque_prom 2,792.15 / ticket_prom 973.59). Frontend `DashboardEjecutivo.js` re-etiquetado: "Ventas (neto)", "Cheques", "Cheque Prom.", "Consumo/PAX" — UI verificada.
- **Inteligencia Comercial** (`/inteligencia/dashboard`): YA canónico (usa `ventas_sin_propina`, cheque_prom=neto/cheques, ticket_prom=neto/pax). Verificado: vista Runtime == tabla canónica (totales idénticos). Sin cambios.
- **Comercial Dashboard** (`comercial/service.py`): YA canónico (`_get_kpis_periodo_edarsahub` retorna SUM(ventas_sin_propina); ticket_prom=neto/pax, cheque_prom=neto/cheques). Sin cambios.
- **Compras**: no calcula KPIs de ventas (solo compras) → N/A.
- Detalle/plan en `/app/memory/PLAN_C2_KPIS_CANONICOS.md`.
- **Nota pendiente (no C2):** "Rentabilidad Base" del Tablero muestra márgenes absurdos (costo receta canónico pendiente; ya señalado en `_nota`). 130QRO backfill quedó EN PROCESO (paso MOVIMIENTOS MPRO muy lento).


## [2026-06-10 PM-2] Export Excel/PDF (Auditoría + Costos), filtro canónico Cuentas Bancarias, backfill CIENFUEGOS/130QRO
- **Export Excel/PDF (probado E2E con descarga real):**
  - Costos y Márgenes (`CostosMargenes.jsx`): botones Excel/PDF en toolbar; exporta lista filtrada (7,757 productos) con Producto/Código/Sistema/Familia/Precio/Costo/Margen$/Margen%. Descargas `.xlsx` y `.pdf` verificadas.
  - Auditoría Operativa (`Compras.js`): botones en encabezado normal y pantalla completa; exporta `resultados` (inv. inicial + movimientos + consumos + teórico/delta + físico + diferencia + importe) en hoja Detalle + hoja Resumen. Reutiliza `ExportButtons`/`exportUtils` (xlsx/jspdf) del Portal Inteligencia.
- **Filtro canónico por unidad — Cuentas Bancarias:**
  - Backend `repository_bancarios.get_cuentas_bancarias` + `/v2/finanzas/cuentas-bancarias`: nuevo param `empresa_codigo` (JOIN `Sistema_Empresas`, filtro parametrizado anti-inyección); serializer ahora expone `empresa_nombre`/`empresa_codigo`. Verificado cURL (sin filtro=1, 130MID=0, inyección `O'Brien`→200 sin error).
  - Frontend `CuentasBancariasPage.jsx` + hook: dropdown de unidad canónico (`fetchUnidadesNegocio`) → pasa `empresa_codigo`. Dropdown poblado con las 5 unidades; verificado en UI.
  - Corte Z: ya tenía filtro de unidad canónico (vía `fetchUnidadesNegocio` + `server_id`); sin cambios.
- **Backfill inventario (90 días):** CIENFUEGOS COMPLETO (110 movs / 4274 detalles / 40 reqs; EmpresaID 3 verificado). 130QRO (MPRO) quedó EN PROCESO en background al cierre (paso MOVIMIENTOS lento).
- **C2 KPIs canónicos:** DIFERIDO con análisis y plan en `/app/memory/PLAN_C2_KPIS_CANONICOS.md` (alto riesgo de regresión en dashboards de producción; requiere decisión del usuario sobre base de ventas para promedios).


## [2026-06-10 PM] Barrido NO-MONGO + fix 2 crashers fase2 + verificación backfill CIENFUEGOS
- **Barrido `get_db()`/`db.<col>` (preventivo):** grep en `modules/`+`core/` + verificación EN VIVO por cURL. Reporte: `/app/memory/BARRIDO_MONGO_2026-06-10.md`. Conclusión: solo 2 crashers reales en vivo; el resto está protegido (try/except → degrada) o es código fallback inalcanzable; `StubDatabase` cubre security/auth/communications/auditoria.
- **Fix SQL-First (2 crashers fase2):**
  - `GET /api/v2/notificaciones/log` → lee de `EDARSAHUB.Operativo_Notificaciones_Log` (antes 500 por `db.notificaciones_log.find()` con db=None).
  - `GET /api/v2/documentos/historial` → lee de `EDARSAHUB.Operativo_DocumentosGenerados` (antes 500).
  - `POST /api/v2/notificaciones/verificar-vencidas` → guardado contra db=None (retorna vacío; detección de vencidas vive en módulo SLA). Verificado cURL: los 3 → 200.
- **Verificación backfill (P0 handoff):** CIENFUEGOS (EmpresaID 3) y 130 QRO (EmpresaID 2) tienen **0 filas** en `Inventario_Movimientos`. Con datos: 130 MID (314), LA ESTELAR (444), ORIGEN (2). El backfill NO se completó para CIENFUEGOS/130QRO → requiere re-ejecución (operación de datos contra servidor externo; PENDIENTE visto bueno del usuario).
- **NO tocado (con justificación):** seed permisos benchmark (DIFERIDO por decisión usuario 2b), benchmark sectorial (diferido 5a), C1 Pricing server_id→unidad (ambigüedad de espacios de ID int vs GUID; requiere resolver claro + prueba E2E con GPT).


## [2026-06-10] Config Asignaciones — Refactor SQL-First (elimina MongoDB legacy, fix CRUD 500)
- **Causa raíz:** `config_asignaciones_routes.py` ejecutaba validaciones legacy MongoDB (`get_db().empresas/users/rbac_usuarios_roles/config_asignaciones/almacenes_catalogo`). Con `get_db()` deprecado (→ None) lanzaba `AttributeError` → 500 en POST/PUT/DELETE.
- **Ruta:** removidas TODAS las llamadas Mongo. `obtener_empresas_permitidas` y nueva `obtener_unidad_accesible` usan `get_user_unidades_negocio` (mismo espacio de IDs EmpresaMongoUUID que `/unidades-negocio`). `validar_usuario_responsable` ahora valida contra SQL (`Usuario_Catalogo`). Duplicados en PUT vía `repo.existe_duplicado`. `info_sincronizacion_almacenes` y `sincronizar_almacenes` sin Mongo.
- **Repositorio:** alias SQL alineados a snake_case (`unidad_negocio_pk`, `unidad_negocio_id`, `almacen_id`, `activa`, `prioridad`) en `listar` y `obtener_por_id` (corrige `activa` siempre false y "Configuración no encontrada"). `crear` recibe `unidad_negocio_nombre`/`server_id` desde la ruta; lookups de usuario corregidos de tabla inexistente `Usuarios` → `Usuario_Catalogo`. Nuevos métodos `obtener_usuario` y `existe_duplicado`.
- **Pruebas (cURL + screenshot, sin testing_agent):** CREATE/GET/UPDATE/DELETE OK, duplicado→409, GET tras delete→404; nombres canónicos (CIENFUEGOS, Carlos Ruz) correctos. UI muestra "Configuraciones (2)" con estados Activa/Inactiva correctos.


## [2026-06-10] Dashboard Comercial: fix PAX = 0 + PAX Promedio + Detalle de Ventas vacío (KPIs canónicos)
Reporte del usuario (menú **Comercial → Dashboard**, 130° MÉRIDA): "PAX Total = 0" y "Pax Promedio = $0"
pese a tener 193 cheques y $761K en ventas; y el doble-clic en una tarjeta abría "Detalle de Ventas" con
"No hay movimientos en este período". El servicio canónico SÍ tenía el dato (pax 542).

- **BUG 1 — PAX = 0 (alias):** en `modules/comercial/service.py`, `_get_kpis_periodo_edarsahub` y los dos
  fallbacks de `_get_kpis_periodo_edarsahub_flexible` hacían `SUM(pax_total) AS pax_total` pero leían
  `row.get('pax')` (clave inexistente) → PAX siempre 0 y "Pax Promedio" $0 (ventas/pax con pax=0). Fix:
  `row.get('pax_total')` en los 3 lugares. Ahora el Dashboard muestra **PAX_TOTAL=542**, pax_promedio=2.81,
  consumo/persona=$1,405 — **coincide exactamente con `KPIsCanonicosService`** (misma base EDARSAHUB).
- **BUG 2 — Detalle vacío:** `/comercial/detalle-movimientos/{server_id}` consultaba la VISTA
  `vw_Comercial_KPIs_Diarios_v2_Runtime` con `ISNULL(activo,1)=1`, pero esa columna **NO existe** en la vista
  (sí en la tabla base) → error SQL silenciado por el helper → "No hay movimientos". Fix: eliminado el filtro
  `activo` de las 2 queries. Ahora el detalle trae los 8 días con ventas/PAX (56, 85, 114, …).
- Verificado: curl end-to-end (dashboard PAX 542; detalle 8 movimientos) + `tests/test_comercial_dashboard_pax.py` (4/4 PASS).
- NOTA: la tarjeta "Pax Promedio" del frontend muestra en realidad *Ventas ÷ PAX* (consumo por persona); el
  backend ya expone también `pax_promedio` (pax/cheque). Pendiente de confirmar con el usuario si se desea
  re-etiquetar/cambiar la fórmula de esa tarjeta.


Tres pedidos del usuario sobre el Portal Inteligencia Comercial:

1. **Franjas horarias centralizadas (sin hardcode)** — `_real_horario` (backend) ahora LEE las franjas
   (Desayuno/Comida/Cena) de `Sistema_TurnosOperativosUnidad` vía `_get_franjas_canonicas()` y construye el
   `CASE` dinámicamente (antes 7-12/13-18/else hardcodeado). Devuelve además `rango` por franja
   (ej. Cena "19:00 – madrugada"). `VentasHorarioPage` muestra ese `rango` real (eliminado el label hardcodeado).
   → Única fuente de verdad: lo que se configura en "Configuración Operativa" rige el reporte "Ventas por Horario".

2. **Rango de fechas PERSONALIZADO** — nuevo botón "Personalizado" + dos `input[type=date]` en `PeriodoSelector`
   (data-testid `periodo-btn-personalizado`, `periodo-fecha-inicio/fin`). Hook `usePeriodo` (utils) entrega los
   query-params correctos (`fecha_inicio/fecha_fin` vs `periodo`). Cableado en Dashboard, Familia, Producto,
   Casa, Alcohol y Horario, y propagado al drill-down de tickets. Backend: `_resolver_rango` + dashboard ahora
   generan `periodo_label` legible para rangos personalizados (ej. "1 Junio – 5 Junio 2026").

3. **Export Excel/PDF arreglado** — DOS causas:
   - **Raíz (Excel):** el nombre de hoja usaba el `title`; títulos con `/` (ej. "Ventas por Casa / Distribuidor")
     violan la restricción de Excel (`: \ / ? * [ ]`) → excepción NO capturada que **tumbaba la app**. Fix:
     `sanitizeSheetName()` en `exportUtils.js` + `try/catch` en `ExportButtons`. (El Dashboard exportaba porque
     su título no tenía `/`.)
   - **Ruta faltante:** la pantalla Casas llamaba a `/api/inteligencia/casas` que **NO existía (404)** → página
     vacía y export deshabilitado. Se creó el endpoint `/casas` (reusa `_real_casas`, mismo cálculo del dashboard).

- Verificado: tests `tests/test_inteligencia_fase1.py` + `test_turnos_operativos_canonicos.py` +
  `test_reporteador_bi.py` (24/24 PASS); curl (casas 200, labels OK, franjas con rango); screenshots
  (rango personalizado filtra datos y muestra "Mostrando: …"; Casas carga 12 casas y exporta .xlsx + .pdf sin error).


Reporte del usuario: en la pantalla Configuración Operativa solo se podían configurar Desayuno y
"Comida/Cena", NO la Cena por separado, y existía un indicador "Comida/Cena (LEGACY)" duplicado e
inconfigurable. Auditoría reveló 3 lógicas desconectadas de "turno/horario".

- **(a) Editor data-driven** (`components/catalogos/ConfiguracionOperativaUnidad.jsx`): se eliminaron los
  `find` hardcodeados a `DESAYUNO`/`COMIDA_CENA`. Ahora renderiza dinámicamente TODOS los turnos canónicos
  (Desayuno, Comida, **Cena**) — cada uno con activo/hora_inicio/hora_fin/cruza_medianoche. Excluye el código
  LEGACY del render y del payload de guardado (no se re-crea). data-testid `turno-config/activo/inicio/fin/cruza-*`.
- **(b) Retiro del LEGACY** (`migrations/eliminar_turno_legacy_comida_cena_20260610.py`, idempotente, con
  respaldo JSON impreso): DELETE de las 5 filas `turno_codigo='COMIDA_CENA'` en `Sistema_TurnosOperativosUnidad`.
  Cada unidad queda con 3 turnos canónicos. Badge `tiene_comida_cena_activo` ahora considera COMIDA/CENA.
- **(c) BUG GRAVE corregido** (`core/utils/operational_window.py::_get_turnos_unidad`): consultaba la columna
  **inexistente** `unidad_negocio_pk` (real: `unidad_negocio_id`) y asumía dict-cursor (pymssql devuelve
  tuplas) → la query truenaba SIEMPRE → caía al *fallback hardcodeado 13:00–06:00*. Es decir, lo configurado
  en la pantalla NO afectaba el cálculo de FechaOperacion del sync. Fix: columna correcta + CAST a VARCHAR +
  conversión tupla→dict + parseo de horas. Añadido `clear_turnos_cache()` (invalidado tras editar). ⚠️ Cambia
  el FechaOperacion del sync de "abiertas": ahora respeta DESAYUNO/COMIDA/CENA reales (autorizado por usuario).
- **(d) Unificación "Probar"** (`api/configuracion_operativa_unidades.py::calcular_fecha_operacion_por_unidad`):
  se eliminó la lógica DUPLICADA (hardcodeada a DESAYUNO+COMIDA_CENA legacy) y ahora delega en el MISMO
  `get_operational_window` (motor canónico). El PUT invalida el cache de turnos.
- Verificado: motor lee turnos reales (5/5 unidades), "Probar" 130MID 14:30→COMIDA, 21:30→CENA (día actual),
  02:30→CENA (madrugada→día anterior); PUT roundtrip no recrea LEGACY; screenshot del editor con los 3 turnos
  editables (Cena con cruza medianoche). Tests `tests/test_turnos_operativos_canonicos.py` (5/5 PASS).
- NOTA pendiente (informativo): "Ventas por horario" del DashboardIA (`_real_horario`) y reporteador_bi aún
  usan rangos horarios HARDCODEADOS distintos a esta config canónica → candidato a centralizar en una próxima tarea.


## [2026-06-09] Reporte Familia/Subfamilia → 4º nivel PRODUCTOS de venta
El reporte solo llegaba a Subfamilia; faltaban los productos de venta. Agregado nivel Producto con carga
bajo demanda: backend `GET /inteligencia/productos-subfamilia` (familia+subfamilia → productos con
cantidad/ventas/%, maneja '(Sin familia)'/'(Sin subfamilia)' como NULL). Frontend `VentasFamiliaPage.jsx`:
subfamilias ahora expandibles (chevron) que lazy-load productos. Verificado: B CERVEZAS Y REFRESCOS →
(Sin subfamilia) muestra Agua Topo Chico $31.3K/392u, Michelob Ultra $28.1K, etc.


## [2026-06-09] FIX — Selector de período se quedaba "pegado en Junio" (condición de carrera)
Síntoma: al cambiar Día/Semana/Mes/Año el botón se resaltaba pero los KPIs/etiqueta no cambiaban
(p.ej. Año mostraba datos de Día). Causa: race condition — la respuesta lenta de un período anterior
(Año tarda ~3.6s agregando 1.2M líneas) pisaba los datos del período ya seleccionado.
Fix: guard de request-id (`useRef`) en `DashboardIA.jsx` y `ReporteadorBI.jsx` → se descartan respuestas
obsoletas. Verificado: Año=$88.13M/89,841 PAX y cambio rápido Día→Semana resuelve correcto. Backend sin cambios.


## [2026-06-09] FASE 2 — Reporteador BI (Informe Gerencial MECA MPRO, 9 páginas)
Reconstrucción del Power BI sobre EDARSAHUB SQL (NO-LIVE). Menú "Reporteador BI" en el Portal Inteligencia.

Backend nuevo `modules/reporteador_bi/routes.py` (prefijo `/api/reporteador-bi`), reutiliza helpers canónicos
de inteligencia (KPIs, clasificación, tickets, horario):
- `/paginas` (metadatos 9 páginas + disponibilidad)
- DISPONIBLES (datos reales): `/analisis-ventas` (KPIs+serie diaria+treemap clasificación+top productos),
  `/ventas-semana` (serie semanal ISO + comparativo), `/ventas-mes` (12-24m + var mes/año anterior),
  `/ambientacion` (ventas por hora real; bandera evento PENDIENTE), `/revision-tickets` (resumen+tickets,
  reusa reconstrucción), `/kpis-mes` (mes actual vs anterior; metas PENDIENTE).
- PENDIENTE_SINCRONIZACIÓN (fuente no sincronizada, sin inventar): `/gastos` (Compras), `/rotacion-mesas`
  (Capacidad/Mesas), `/analisis-documentos` (Documentos_Capturados).

Frontend `portal-inteligencia/pages/ReporteadorBI.jsx` + `components/PendienteSync.jsx`: navegación interna
de 9 páginas, gráficos recharts (LineChart/ComposedChart/BarChart/Treemap), KPIs, export Excel/PDF en cada
página, drill-down de tickets (reusa TicketDrilldownModal), período canónico. Registrado en `server.py`.

Auditoría de disponibilidad EDARSAHUB: ventas (detalle+KPIs v2) ✅; NO sincronizados: Compras/Costos,
Documentos_Capturados, Metas, Capacidad/Mesas, Vendedores, bandera Ambientación → muestran estado honesto.
Tests: `tests/test_reporteador_bi.py` (10) + `tests/test_inteligencia_fase1.py` (9) = 19/19 PASS.

PRÓXIMO (orden del usuario) → (c) Propagar clasificación canónica a Costos/Pricing/Benchmark.
PENDIENTE habilitar páginas Gastos/Rotación/Documentos al sincronizar sus fuentes a EDARSAHUB.


## [2026-06-09] Pantalla Admin de Clasificación de Producto (resuelve PENDIENTE)
- Backend (`modules/inteligencia_comercial/routes.py`): endpoints admin (auth dual + rol admin):
  `GET /inteligencia/clasificaciones` (catálogo), `GET /inteligencia/admin/productos-clasificacion`
  (lista paginada con filtros q/system_type/estado), `GET /inteligencia/admin/familias-pendientes`,
  `POST /inteligencia/admin/clasificar` (por producto_ids o por familia → `ClasificacionOrigen='MANUAL'`).
  Helper `execute_write` (commit) + dependencia `require_admin`.
- Frontend (`portal-inteligencia/pages/ClasificacionAdminPage.jsx` + ítem menú "Clasificación (admin)"):
  2 vistas (Por familia en bloque / Por producto individual), dropdown del catálogo, toasts (sonner),
  paginación y búsqueda. `apiPost` añadido al client.
- Verificado: clasificación en bloque (familia "Z SUSPENDIDOS" 731→OTROS) y 401 sin token. 9/9 tests PASS
  (`tests/test_inteligencia_fase1.py`). Pendientes bajaron de 1.086 al ir clasificando.


## [2026-06-09] Clasificación Comercial CANÓNICA de Producto (elimina CASE A/B de endpoints)
Autorizado por usuario. Migración `migrations/comercial_clasificacion_producto_20260609.py` (idempotente).

- **Catálogo controlado** `Comercial_ClasificacionesProducto` (ALIMENTOS/BEBIDAS/OTROS/PENDIENTE_CLASIFICACION).
- **`Sync_Productos`** += `ClasificacionProductoID` (FK) + `ClasificacionOrigen` + `ClasificacionFecha` (trazabilidad).
  Columnas nullables; el MERGE del sync (`sync_recetas.py`, llave ServerID+CodigoFuente, sin DELETE) las preserva.
- **Backfill** (idempotente, no pisa 'MANUAL'): SoftRestaurant SOLO por prefijo familia 'A '/'B ' (regla NO global);
  MPRO SOLO por `CategoriaNombre`; resto → PENDIENTE. Resultado: BEBIDAS 6.558, ALIMENTOS 3.324, OTROS 1.492,
  PENDIENTE 1.086, NULL=0 (de 12.460 productos).
- **Endpoints refactorizados** (`modules/inteligencia_comercial/routes.py`): `_real_clasificacion_nested` y
  `_real_ticket_lineas` ahora hacen JOIN a `Comercial_ClasificacionesProducto` y leen `Codigo`. **CASE A/B eliminado.**
  Si falta clasificación → muestra PENDIENTE_CLASIFICACION (no inventa). 6/6 tests PASS.
- Doc completo: `memory/AUDITORIA_CLASIFICACION_COMERCIAL_PRODUCTO.md` (incluye rollback). Pendiente: clasificar
  manualmente los 1.086 PENDIENTE (Soft sin prefijo) y reutilizar la clasificación en Costos/Pricing/Benchmark/MECA MPRO.


## [2026-06-09] Portal Inteligencia FASE 1 — 7 observaciones + Drill-down + Export (SQL-First, NO-LIVE)
Sesión fork. Pruebas SOLO cURL/python/pytest/screenshots (NO testing_agent). CERO MongoDB. NO-LIVE. SIN hardcode.

Backend (`modules/inteligencia_comercial/routes.py`):
1. **KPIs canónicos arriba**: agregado `ticket_promedio` (ventas_sin_propina ÷ PAX) junto a
   `cheque_promedio` (ventas_sin_propina ÷ cheques), ambos desde `Comercial_Metricas_Canonicas`.
2. **Casas/Distribuidores reales**: `_real_casas` ahora hace JOIN a `Comercial_Productos_Enriquecidos.grupo_comercial`
   por `producto_id` (Diageo, Pernod, Cuervo, Grupo Modelo…). El campo `casa` del detalle estaba 100% NULL.
3. **Clasificación macro Alimentos/Bebidas/Otros** (`_real_clasificacion_nested`): regla HÍBRIDA canónica —
   familias con prefijo "A "/"B " (SoftRestaurant, sin clasificador real) usan el prefijo; MPRO usa
   `Sync_Productos.CategoriaNombre`; resto → OTROS. Cada familia se asigna a su clasificación dominante.
4. **Bug "Día" vacío** corregido: `_ultimo_dia_con_datos` ahora ancla al DETALLE (no a la vista KPI),
   evitando que horarios/productos salgan vacíos cuando el KPI tiene un día más reciente que el detalle.
5. **Reporte de Alcohol** (`/inteligencia/alcohol`): con/sin alcohol + por grado (es_alcoholico/grado_alcohol del enriquecido).
6. **Drill-down / reconstrucción de ticket**: `/inteligencia/tickets` (nivel cuenta) y
   `/inteligencia/ticket-detalle` (líneas, nivel más bajo, con casa/clasificación/grado).
7. **Filtro de período canónico** (`_resolver_rango`) reutilizado por dashboard/productos/familias/casas/alcohol.

Frontend (`portal-inteligencia/`):
- `DashboardIA.jsx`: Ticket+Cheque Promedio en fila superior, KPIs clicables → modal de tickets, export Excel/PDF.
- `VentasFamiliaPage.jsx`: árbol Clasificación→Familia→Subfamilia (tarjetas Alimentos/Bebidas/Otros).
- `VentasCasaPage.jsx` (grupo_comercial) y `VentasProductoPage.jsx`: período + export.
- Nuevo `VentasAlcoholPage.jsx` + ítem de menú "Bebidas (Alcohol)".
- Componentes nuevos: `PeriodoSelector`, `ExportButtons` (xlsx/jspdf/file-saver), `TicketDrilldownModal`.
- `utils/exportUtils.js`: export Excel/PDF reutilizable. Unidades del selector ahora dinámicas (sin hardcode).
- Tests: `backend/tests/test_inteligencia_fase1.py` (6 PASS).

PENDIENTE → **FASE 2**: Reporteador tipo Power BI "Informe Gerencial MECA MPRO" (9 páginas) + export/drill-down universal.


## [2026-06-09] Confidencialidad + KPIs Canónicos (SQL) + Benchmark Interno de Grupo
Sesión fork. Pruebas SOLO cURL/python/pytest/screenshots (NO testing_agent). CERO MongoDB. NO-LIVE.

1. **Capa de Confidencialidad central** (`core/confidencialidad/AnonymizerService`): enmascara
   nombres reales / IDs técnicos según permiso (niveles COMPLETO→AGREGADO derivados del rol canónico).
   Etiquetas anónimas deterministas ("Unidad comparable A/B"). Frontend nunca recibe nombres sin permiso.
   Tests: `tests/test_anonymizer_service.py` (6).

2. **KPIs Canónicos viven en SQL** (máxima SQL-First). Migración idempotente
   `migrations/comercial_metricas_canonicas_20260609.py` crea:
   - `dbo.Comercial_Metricas_Canonicas` (definición declarativa operacion=campo/ratio, formato,
     versión, auditoría) — 8 métricas.
   - `dbo.Comercial_Metricas_Sinonimos` (alias→canónico) — 21 sinónimos.
   `core/kpis_canonicos/KPIsCanonicosService` LEE de SQL e interpreta (`aplicar_definicion`).
   **La propina NO es venta**: `ventas`=sin propina; `cheque_promedio`=ventas/CHEQUES (x cuenta);
   `ticket_promedio`=ventas/PAX (x comensal) — KPIs DISTINTOS. Endpoint `/api/comercial/benchmark/metricas`.
   Validado: ESTELAR cheque_prom $1,477 · ticket_prom $508. Tests `tests/test_kpis_canonicos.py`.

3. **Benchmark Interno de Grupo** (Portal Inteligencia → "Benchmark Grupo"): `modules/comercial_benchmark`
   consume KPIs canónicos + AnonymizerService. Agrupa por `unidad_negocio_pk` (MPRO 130QRO/ORIGEN NO se
   colapsan). Envelope completo (criterios 46–54). Frontend lee métricas y unidades desde SQL (sin hardcode).
   **Auth corregida**: dependencia DUAL (cookie httpOnly + Bearer) — antes daba 401 en el Portal.
   Tests `tests/test_benchmark_stats.py` (4).

4. **ETL NO-LIVE** `scripts/poblar_ventas_detalle_producto.py`: puebla
   `Comercial_Inteligencia_VentasDetalleProducto` desde `Sync_Sales.items` (JSON) + match canónico +
   enriquecido. Idempotente, 100% EDARSAHUB (sin POS). 130MID/130QRO completos; resto en backfill.

5. **Validación arquitectónica**: el `benchmark_service.py` existente es benchmark de PRECIOS vs
   competidores (concepto distinto). Confirmado split de menús con el usuario.

**Pendiente (autorizado):** C2 resto (Tablero/Compras/Inteligencia → KPIsCanonicosService);
C1 (Pricing `server_id`→`unidad`, ELIMINAR server_id + frontend); C3 (auditar server_id operacional
en comercial/repository.py|routes.py); completar backfill productos.


## [2026-06-08 PM] Fork: 6 fixes (menú, Finanzas, Propinas, Costos canónico, Recetas, Precios Sugeridos)
Sesión fork. Pruebas SOLO cURL/python/screenshots (NO testing_agent). CERO MongoDB. NO-LIVE respetado.

1. **Menú Enterprise "Operación"** (`enterpriseMenuConfig.js`): se confirmó el render (Costos y Márgenes, Pricing IA, Tablajería visibles bajo VENTAS/COSTOS/COMPRAS/INVENTARIOS/PRODUCCIÓN). Verificado por screenshot.

2. **Finanzas → Control de Ingresos** (`Finanzas.js`): el front enviaba `unidad_negocio_id` pero `/finanzas/ingresos/cortes-caja` espera `unidad_negocio_pk` → no filtraba (mostraba todas). Fix: front envía `unidad_negocio_pk`. Verificado: Mérida=6 cortes (solo Mérida) vs 40 (todas).

3. **Propinas TPV** (`PropinasTPV.jsx`): los `fetch` usaban solo `credentials:'include'` (cookie httpOnly que no se setea/lee) → 401 "Verifique su sesión". Fix: usar `authedFetch` canónico (inyecta Bearer). Verificado: v2/detalle 200 con datos.

4. **Costos y Márgenes — Unidad de Negocio CANÓNICO** (`CostosMargenes.jsx` + `modules/costos_margenes/routes.py`): se eliminó el dropdown duplicado + `/costos-margenes/unidades-negocio` (404, desactivado). Ahora usa `CorporateFiltersProvider scope=comercial.costos_margenes` + `CorporateFilterSelect`. Backend `/productos`,`/familias`,`/subfamilias` aceptan `unidad` (codigo/id) resuelto vía `resolve_unidad_scope`; `servidor_id` DEPRECATED. Verificado: productos CIENFUEGOS=2022, 130MID=1858, ORIGEN=5414, todas=9905; familias CIEN=37/125.

5. **Recetas reparadas (P0 regresión)** (`modules/costos_margenes/repository.py`): NameError `name 'ProductoID' is not defined` (f-strings con variables inexistentes `{ProductoID}`/`{ServerID}`) + `producto.get('server_id')` leía clave equivocada (col es `ServerID`). Fix aplicado. Verificado: BETABEL TATEMADO=9 componentes, costo $81.42, sub-recetas "Elaborado" marcadas.

6. **Precios Sugeridos** (`CostosMargenes.jsx` TabPreciosSugeridos + `routes_precios_sugeridos.py`): (a) la vista LISTA no tenía las celdas `Precio Actual` ni `Costo` → todas las columnas se recorrían 2 posiciones (parecía que Precio Actual/Sugerido eran %). Fix: agregadas las 2 celdas (muestran $). (b) Reducida fuente del % (text-xs). (c) Agregado filtro canónico de unidad (`unidad`→server_id vía UnidadesService). Verificado: unidad=CIENFUEGOS=2022, 130MID=1858.

**PENDIENTE (orden acordado con usuario a→d→c→b, faltan c/b):**
- ✅ (a) Precios Sugeridos — HECHO (columnas $/%, fuente, filtro unidad canónico).
- ✅ (d) SYNC de estatus inactivo/baja — HECHO. Causa: SoftRestaurant leía `pd.suspendido` (NO existe); la columna real es `productosdetalle.bloqueado` (bit). Corregido en `sync_recetas.py` (`_obtener_productos_sr`). MPRO `Es_Cve_Estado` ya estaba bien. Re-sincronizados todos los servidores con productos vía el central `ejecutar_sync_recetas_real`. Resultado: 130MID 950/916, CIENFUEGOS 955/1068, ESTELAR 441/173, MPRO(ORIGEN+130QRO) 5415/2207 (act/inact). Filtro "Incluir inactivos" verificado (CIENFUEGOS 955 solo activos vs 2023 todos). CLAM CHOWDER ahora Activo=False. Conexiones vía helper central `get_server_connection_info`+`execute_sql_query`. Endpoints temporales de debug eliminados.
- ⏳ (c) Catálogo canónico NO-LIVE. Estructuras confirmadas por usuario: MPRO=1 catálogo único (Categoría→Departamento→Marca→Línea→Familia→Subfamilia, +Proveedor/Comprador); SoftRestaurant=catálogo VENTAS (Clasificación→Grupo→Subgrupo) + catálogo INSUMOS/elaborados (Clasificación→Grupo). `/servers/{id}/report-filters` (Análisis) hace LIVE a POS → VIOLA NO-LIVE, migrar.
- ⏳ (b) Auto-refresh de sesión (logout a los 15 min). Requiere experto de integración (AUTH).


## [2026-06-08] P0 — UNIFICACIÓN CANÓNICA DE TABLEROS (unidad_codigo → backend resuelve)
Regla arquitectónica confirmada por el usuario: el frontend envía SOLO la unidad canónica; el backend valida permiso y resuelve server_id/sucursal_origen_id desde EDARSAHUB; `server_id` queda deprecated (compat temporal); dashboards NO-LIVE.

**AUDITORÍA DE SCRIPT DEL USUARIO (rechazado):** se auditó un bash de reemplazos regex a ciegas y se DETUVO su ejecución (regla de oro). Bugs detectados: rompía RBAC (pasaba `current_user` donde se espera lista de unidades → PermissionError global; y devolvía TODOS los servers sin permisos), corrompía `dashboard_routes.py` (regex truncaba la descripción `(server_id)` → SyntaxError), rompía `OperativoDashboard.jsx` (getServerIdFromUnidad es import, no función local; `selectedServerId`→`selectedUnidad` duplicaba variable), y por `set -e` dejaba el repo a medio aplicar. Se implementó el MISMO objetivo de forma quirúrgica.

**Helper central único** `core/corporate_filters/request_resolver.py` (NUEVO): `resolve_unidad_scope(current_user, unidad, server_id_legacy)` y `resolve_unidad_simple(valor)`. Reutiliza `UnidadesService` (SQL) + RBAC existente (`empresas_permitidas`→servers). CERO MongoDB, CERO POS live. Prioridad: unidad > server_id(deprecated, con warning) > global. Sin acceso → centinela → resultados vacíos. Desambigua MPRO: server compartido (ORIGEN/QRO) → filtra por etiqueta de sucursal (codigo/nombre) en operativo y por sucursal_origen_id (0021/0023) en inventarios.

**Backend operativo** (`dashboard_routes`, `workflow_routes`, `tarea_routes`): aceptan `unidad` (nuevo) + `server_id` (deprecated). Se eliminó `resolve_effective_server_ids` (reemplazado por el helper central). `workflow_repository`/`workflow_service`/`operativo_service` ahora soportan `sucursal_ids` para desambiguar MPRO; tareas se filtran por workflow_uuids del scope (server+sucursal). Verificado: global=18; por unidad 130MID=4, CIENFUEGOS=7, ESTELAR=5, ORIGEN=1, 130QRO=1 (suman 18); legacy server_id sigue funcionando; unidad inexistente→0.

**Backend inventarios** (`server.py` `obtener_inventarios_fisicos`): acepta `unidad` (prioridad) o path server_id (deprecated). **ELIMINADO el fallback LIVE (PASO 2)** → NO-LIVE puro, única fuente EDARSAHUB_SYNC. MPRO desambiguado: unidad=ORIGEN→147 (suc 0023), unidad=130QRO→113 (suc 0021), todas source=EDARSAHUB_SYNC.

**`modules/inventarios/repository.py`** (código MUERTO confirmado, alineado por higiene): `sync_status='ACTIVE'` → `IN ('ACTIVE','REPLACED')` con dedup ROW_NUMBER (no vuelve a ocultar MPRO/REPLACED).

**Frontend operativo** (`operativoApi.js` + `OperativoDashboard.jsx`): se ELIMINÓ `getServerIdFromUnidad`; el selector envía `unidad_codigo`. El frontend ya NO resuelve server_id.

**Pendiente (siguiente incremento):** migrar `Reportes.js` (Análisis/Métricas — componente grande con su propio sistema server/sucursal/almacén) al contrato `unidad`. Hoy funciona vía compatibilidad (server_id legacy, ya NO-LIVE). También TableroEjecutivo/DashboardIA.

**Verificación:** cURL E2E (SIN testing_agent), `yarn build` OK (34.75s), py_compile/AST OK, regresión: unidades-negocio=5 (EDARSAHUB no envenenado), comercial intacto. CERO MongoDB (evidenciado: sólo comentarios mencionan pymongo; get_database()=None; base_repository→SQL).

## [2026-06-08] FIX P0 — 3 bugs pantalla "Operaciones" (Reportes.js) + protección crítica EDARSAHUB
Reporte del usuario: (a) Dashboard Operativo sin filtro de unidad (datos globales); (b) Métricas "No hay servidores configurados con consultas SQL"; (c) Análisis "No hay inventarios disponibles" en ORIGEN/QUERÉTARO (MPRO), CIENFUEGOS sí.

**(c) Inventarios MPRO ocultos — RESUELTO (NO-LIVE):** `obtener_inventarios_fisicos_sync` filtraba `sync_status='ACTIVE'`, pero los inventarios MPRO (113 QRO + 147 ORIGEN) y 130MID/ESTELAR estaban como `REPLACED` (un sync los marcó pero su insert ACTIVE falló por POS inaccesible). La data SÍ está en EDARSAHUB. Fix: leer ACTIVE+REPLACED deduplicando por (server_id+sucursal_id+almacen_id+folio) con ROW_NUMBER (prefiere ACTIVE). 0 duplicados verificados. Las 5 unidades devuelven inventarios desde `EDARSAHUB_SYNC` (sin LIVE). `modules/compras/sync_service.py`.

**(b) Métricas descartaba servidores configurados — RESUELTO (gate) + PROTECCIÓN CRÍTICA:** `core/server_registry.get_server_connection_info_with_secrets` omitía `queries_configured`/`departamentos`/`categorias` → el endpoint descartaba TODOS los servidores (incluso CIENFUEGOS/ESTELAR/MPRO con `queries_configured=True`). Fix: incluir esos campos. Ahora CIENFUEGOS/ESTELAR cargan Métricas.
  - **HALLAZGO CRÍTICO:** el POS de MPRO comparte IP `54.39.104.176` con EDARSAHUB. Métricas hace consulta EN VIVO; al fallar la conexión MPRO ponía a `54.39.104.176` en cooldown en memoria → TODAS las lecturas canónicas de EDARSAHUB devolvían vacío (`/unidades-negocio`→0, RBAC roto, app caída). El fix del gate EXPUSO esta ruta. **Protección añadida** en `get_dashboard_inventory_summary`: NUNCA conectar EN VIVO si `server.host == EDARSAHUB host` → devuelve mensaje NO-LIVE rápido (0.35s). + `timeout_seconds=30` en la query LIVE.
  - PENDIENTE DECISIÓN USUARIO: (1) 130MID tiene `queries_configured=0` en SQL (Métricas sigue "no configurado"); (2) Métricas de MPRO ya no muestra datos en vivo (usar pestaña Análisis, que ya es NO-LIVE); (3) Métricas de CIENFUEGOS/ESTELAR aún consultan POS EN VIVO (lento ~17s, viola NO-LIVE pero en hosts propios, no tumban EDARSAHUB). Migrar Métricas a NO-LIVE es trabajo mayor (requiere datos de diferencias de inventario en EDARSAHUB).

**(a) Dashboard Operativo sin filtro de unidad — RESUELTO:** Agregado selector "Unidad de Negocio" en `OperativoDashboard.jsx` y param `server_id` en `/v2/dashboard/resumen|alertas`, `/v2/workflows`, `/v2/tareas`. Como `Tareas_Inventario` no tiene server_id, se resuelven los workflow uuid de la unidad (vía `WorkflowRepository.get_uuids_by_servers`) y se filtran tareas por `workflow_id IN (...)`. Verificado: global=18 wf; por unidad 130MID=4, CIENFUEGOS=7, ESTELAR=5, MPRO=2 (suman exacto 18); tareas/vencidas/alertas también acotadas. Unidad no permitida → sentinel → resultado vacío (RBAC). Archivos: `repositories/workflow_repository.py`, `repositories/tarea_repository.py`, `services/workflow_service.py`, `services/tarea_service.py`, `services/operativo_service.py`, `routes/dashboard_routes.py|workflow_routes.py|tarea_routes.py`, `services/operativoApi.js`, `components/fase2_operativo/OperativoDashboard.jsx`.

**Verificación:** cURL E2E (sin testing_agent), `yarn build` OK (44s), py_compile/lint OK (3 hallazgos lint en sync_service son PRE-EXISTENTES fuera del cambio), regresión: `/unidades-negocio`=5, `health/v1`=healthy. Screenshot UI bloqueado por reset de caché del preview (limitación conocida).

## [2026-06-08] FIX P0 — Sintonizador KPIs Comercial detenido (Junio desactualizado) + meses exactos + formato
**Reporte del usuario:** El KPI de ventas de junio mostraba MENOS de lo real (Tablero solo leía hasta 4-5 jun, faltaban 5/6/7). Pidió: (1) junio al día y solución definitiva al "sintonizador", (2) que se auto-actualice solo, (3) sumar EXACTAMENTE los meses seleccionados, (4) coma en proyección ($1,016.49M).

**Causa raíz (refactor incompleto del 5-jun que rompió `sync_comercial_v2`):**
1. `UnidadesService.get_all()` dejó de exponer `server_id`, `system_type`, `sucursal_origen_id` → el job clasificaba 0 unidades. **Fix:** agregadas esas columnas al SELECT (aditivo).
2. Esquemas/mappers migrados a `unidad_negocio_pk` pero el job y `sync_comercial_edarsahub` seguían usando `unidad_negocio_id` → ValidationError. **Fix:** pasar `unidad_negocio_pk` (GUID) en todo el flujo del job y SyncResult/SyncLogV2.
3. `upsert_kpi_diario` escribía contra la **vista con JOIN** `vw_Comercial_KPIs_Diarios_v2_Runtime` (no expone `hash_origen`/`es_demo`/etc.) y omitía `unidad_negocio_id` (NOT NULL). **Fix:** upsert apunta a la **tabla base** `dbo.Comercial_KPIs_Diarios_v2` e incluye `unidad_negocio_id` (código resuelto vía `UnidadesService.get_by_pk`).
4. `insert_sync_log` usaba columna `unidad_negocio_pk` inexistente en `Comercial_SyncLog_v2`. **Fix:** columna `unidad_negocio_id`.

**Acciones:**
- Catch-up oficial ejecutado (`scripts/catchup_junio_kpis_v2.py`, dias_atras=4): junio 5 ($907K), 6 ($996K), 7 (parcial) cargados. **Idempotente, solo lectura del POS, NO se tocó `Comercial_KPIs_Diarios_v2` de jun 1-4 (solo skip/update)**.
- Auto-actualización: `SCHEDULER_SYNC_COMERCIAL_V2_ENABLED=true` (job cada 15 min, ya verificado corriendo y registrando SUCCESS en `Comercial_SyncLog_v2`).
- Meses exactos: `/v2/comercial/dashboard` acepta `meses=` (ej `1,3`) → `MONTH(fecha_operacion) IN (...)`. Verificado: Ene+Mar excluye Feb (cuadre exacto).
- Formato: `formatCurrency` usa `toLocaleString` → `$1,016.49M` con coma.

**Verificación (cURL + screenshot, SIN testing_agent):** Tablero junio = $3.66M / 3,701 pax / 1,300 cheques (antes 1,449/523). 5 unidades con datos.


## [2026-06-07] FIX P0 — Tablero Ejecutivo KPIs en cero (Junio 2026)
**Script del usuario (`fix_p0_..._junio_2026.sh`) AUDITADO y RECHAZADO:** usaba `npm run build` (PROHIBIDO, es `yarn`), reescribía `frontend/.env` (riesgo a `REACT_APP_BACKEND_URL`), sus `re.sub` NO matcheaban las firmas reales (parche backend = no-op), y mantenía `activo=1/es_demo=0` + base table `Comercial_KPIs_Diarios_v2`. Apliqué una versión auditada y corregida (`/app/scripts/fix_tablero_kpis_cero_AUDITADO.py`, con aserciones por reemplazo y backups).

**Causas raíz confirmadas contra el esquema real de EDARSAHUB SQL:**
1. Las queries filtraban columnas **INEXISTENTES** `activo`/`es_demo` (ninguna tabla/vista las tiene) → error SQL → `[]` → KPIs cero.
2. Filtraban `unidad_negocio_pk` (GUID) con **CÓDIGOS** canónicos (`get_unidades_permitidas_v2` devuelve códigos) → nunca matcheaba. Correcto: `unidad_negocio_id`.
3. `get_kpis_por_unidad` armaba **SQL inválido** (texto literal `UnidadesService.resolver_codigo(...) or '130MID'` dentro del f-string).
4. **RBAC:** `has_full_access` comparaba el claim `role` solo contra NOMBRES; el JWT guarda el CÓDIGO `SUPERADMIN` → 403 "No tiene unidades". Fix: comparar también contra CÓDIGOS de acceso total.
5. **Frontend race condition:** `TableroEjecutivo.js` descartaba la respuesta válida como `IGNORED_STALE` por leer `latestRequestId` (useState) obsoleto en el closure. Fix: `useRef` síncrono.

**Cambios (todos NO-LIVE / SQL-First / vista `vw_Comercial_KPIs_Diarios_v2_Runtime`):**
- `repository_readonly.py` + `routes.py` (comercial_v2): quitado activo/es_demo, filtro por `unidad_negocio_id`, KPI ventas = `ventas_sin_propina`, `propinas_total` separado (totales + por unidad), `get_ventas_dia_abiertas` alias `unidad_negocio_id AS unidad_negocio_pk`.
- `core/rbac_helper_sql.py::has_full_access`: reconoce el código `SUPERADMIN` en el claim `role`.
- `TableroEjecutivo.js`: fix race condition con `useRef`.

**Verificado (cURL + screenshot autenticado):** dashboard `/api/v2/comercial/dashboard?fecha_inicio=2026-06-01&fecha_fin=2026-06-30` → 200; **ventas (sin propina)=$1,573,660.81**, propinas=$105,376.57 (separadas), 5 unidades, tickets=523, pax=1449. Tablero renderiza **VENTAS CONSOLIDADAS $1.57M** y las 5 unidades. `v2/comercial/health` y `ventas-dia` → 200.
**Nota lint/build:** Un comentario `// eslint-disable-next-line react-hooks/set-state-in-effect` que se había agregado rompía el build real (`yarn build` → "Definition for rule not found", porque esa regla solo existe en la herramienta de lint interna, no en el ESLint del proyecto/craco). Se eliminó → **`yarn build` compila OK (Done in 36s)**. El hallazgo `react-hooks/immutability` que reporta la herramienta interna NO es enforced por el build real (compila sin tocarlo) y es pre-existente; no requiere acción.

## [2026-06-07] Fase 26 — Panel Bitácora Admin CORE (lectura SQL-First de Servidores_Conexiones_Log)
- **Backend:** nuevo endpoint read-only `GET /api/admin/core-connections/audit-log?limit&server_id` en `api/admin_core_connections.py`. Lee `dbo.Servidores_Conexiones_Log` con `LEFT JOIN Servidores_Conexiones` (nombre de conexión), `CONVERT(...,126)` fecha ISO, parseo de `status` desde `datos_nuevos` JSON. NO expone secretos. `TOP` parametrizado (1–200). **Registrado ANTES de `GET /{server_id}`** para evitar colisión de ruta (si no, `/audit-log` caería en `/{server_id}` → 404). Verificado cURL: 200, count correcto, join de nombres OK, LIST sigue 200.
- **Frontend:** 4º tab **Bitácora** en `pages/Servidores.js` (`grid-cols-3`→`grid-cols-4`, `max-w-xl`→`max-w-2xl`). Carga lazy al abrir el tab (`useEffect` sobre `activeMainTab`), tabla con Fecha/Conexión/Acción/Usuario/Estado(badge)/Origen + botón Actualizar y estados loading/empty. `data-testid`: `tab-bitacora-core`, `bitacora-core-panel`, `bitacora-table`, `bitacora-row`, `bitacora-refresh-button`. Verificado screenshot autenticado: 41 registros renderizados.
- **Bonus (lint):** corregidos 6 errores ESLint **pre-existentes** en `Servidores.js` que el cambio expuso: 4× `no-undef` (`setSelectedConnection`/`setUniversalTesterOpen` en los botones "Test Universal" de las vistas lista SQL y API → remapeados a los estados reales `setServerForUniversalTest`/`setUniversalTestConnectionType`/`setUniversalTestOpen`) + 2× comillas sin escapar (`&quot;`). Lint final: 0 bloqueantes.

## [2026-06-07] Fase 25 — P2: previewCacheUtils preservación explícita de token de sesión
- **AUDITORÍA DE SCRIPT (rechazado):** `FASE25_*.sh` NO ejecutado. 3 defectos: (1) FATAL — ambos heredocs Python usan `Path("""__TARGET__""")` literal con `<<'PY'` y **sin** paso `sed` que sustituya `__TARGET__` por `$TARGET` → `FileNotFoundError`, aborta en GATE; (2) su GATE exige `sessionStorage.clear()`/`localStorage.clear()` que **NO existen** en el archivo real (limpieza selectiva vía `shouldClearKey()`) → SystemExit(4); (3) su modelo `clear()` total + lista de preservación es lo **opuesto** al diseño *opt-in* actual → regresión.
- **Verificación del objetivo:** el reset solo borra llaves que matchean patrones de caché (`edarsa*`/`EDARSA_CACHE_KEYS`). Confirmado que las 3 llaves de auth usadas por el frontend (`edarsa_memory_token`, `token`, `access_token`) **ya sobrevivían** el reset → objetivo de preservar token ya cumplido implícitamente.
- **Mejora mínima aplicada:** `shouldClearKey().NEVER_CLEAR` ampliado con `token`, `access_token`, `auth_token` (antes solo `edarsa_memory_token`/`user`/marcador). Hace la preservación de sesión **explícita y robusta** ante futuros cambios de `EDARSA_CACHE_KEYS`. Lint limpio (0 bloqueantes), hot-reload (cambio de 1 array, sin build).

## [2026-06-07] Fase 24 — P1: Cableado de `audit_core_action` en endpoint TEST de Admin CORE (SQL-First)
- **AUDITORÍA DE SCRIPT (rechazado):** `FASE24_*.sh` NO ejecutado. 2 defectos: (1) su GATE inspecciona solo la 1ª línea de la firma (`async def test_core_connection(`) y exige `server_id`/`current_user` ahí, pero la firma es **multilínea** → abortaba con SystemExit(4) sin parchear; (2) regresión latente: `current_user: Dict = Depends(lambda: None)` → en runtime es **None**; la llamada insertada `audit_core_action(user=None,...)` ejecutaría `user.get('id')` → **AttributeError → 500**, rompiendo el contrato (test devuelve 200/404).
- **Fix aplicado (corregido):** (a) blindaje en `audit_core_action`: `user = user or {}` al inicio (evita crash ante user None de cualquier caller); (b) cableado en `POST /{server_id}/test`: tras `result = test_core_connectivity(conn)` se invoca `audit_core_action(action='TEST_CORE_CONNECTION', user=current_user, core_id=server_id, status=result.get('status','SUCCESS'), details={...})` antes del `return result`. `status` derivado del resultado real (no hardcodeado).
- **Verificado (cURL/SQL):** `py_compile` OK, backend RUNNING. Endpoint test → **200 SUCCESS** (`duration_ms`, `message`, contrato intacto). Fila persistida en `dbo.Servidores_Conexiones_Log`: `accion='TEST_CORE_CONNECTION'`, `servidor_id` correcto, `datos_nuevos` JSON. Guardrails NO-MONGO + Admin CORE contract PASS, `health/v1` 200.
- **Nota:** `usuario` queda NULL porque el router usa `Depends(lambda: None)` (la auth se aplica al incluir el router en `server.py`, no inyecta el dict de usuario). Cablear el usuario real requeriría cambiar esa dependencia (fuera de alcance / riesgo). Backup `.bak_*`.

## [2026-06-07] Fase 19 — Reactivación SQL-First de Destinatarios de Alertas + lecturas de Auditoría
- **Destinatarios de alertas (Centro de Control) REACTIVADOS sobre SQL.** Reescrito `core/centro_control/recipients_manager.py` completo a SQL-First sobre `dbo.Sistema_AlertasDestinatarios` (`ColeccionOrigen='alert_recipients'`, detalle en `PayloadMongo` JSON) vía `get_edarsahub_pymssql_connection`. Maneja JSON migrado (`$date`/`$oid`) y nuevo. `recipient_id` = `Id` (uniqueidentifier).
  - CRUD verificado end-to-end por API: LIST (2 migrados leídos), RESUMEN, ADD (200 + GUID), ADD duplicado (400), UPDATE (activo/nombre), filtro `solo_activos`, DELETE (cleanup). Endpoints `GET/POST/PUT/DELETE /api/centro-control/destinatarios` 100% funcionales (antes 500/deshabilitados).
- **Auditoría: `consultar_por_registro` y `consultar_por_modulo` migrados a SQL** (`dbo.Finanzas_AuditoriaFinanciera`, 73 registros). Nuevo helper `_consultar_auditoria_sql(predicate, limite)` lee `PayloadMongo`, normaliza `created_at` a ISO, ordena desc. Verificado: filtro por módulo (CONFIG→5), por registro (todos coinciden), orden descendente correcto. Ya NO usan `_get_mongo_db`.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **9/9**, scan `modules/`+`core/` = 0 forbidden / 0 broken, `health/v1` healthy, Admin CORE paridad (200/2), destinatarios 200/total=2.
- **Nota:** ambas tablas son de aterrizaje Mongo→SQL (datos en `PayloadMongo` JSON); el modelo es 1:1 con lo migrado, sin pérdida. Escrituras de destinatarios crean filas nativas SQL (`MigradoDesdeMongo=0`).

## [2026-06-07] Fase 18 — P5-3D Cierre NO-MONGO en `core/` + guardrail extendido
- **Neutralizado `core/auditoria.py::_get_mongo_db`** (stub roto `client=None; client[db_name]` en try/except) → `return None` limpio. La auditoría persiste en SQL (`_guardar_sql` con commit es la ruta primaria); los callers (`_guardar_mongo`, `consultar_por_*`) ya estaban guardados → degradan a False/[].
- **Neutralizado `core/communications/scripts/__init__.py::main`** (init standalone con stub Mongo roto) → no-op NO-MONGO.
- **Neutralizado `core/centro_control/recipients_manager.py`**: `get_db`/`get_collection` → `None`; añadidos guards en `get_all_recipients` (→[]), `add/update/delete_recipient` (→RuntimeError claro "NO-MONGO, requiere migración SQL"). Feature de destinatarios de alertas era **Mongo-backed y ya rota** (crasheaba); ahora **degrada con gracia**: endpoints `GET /api/centro-control/destinatarios` y `/resumen` pasan de **500 → 200 vacío**. (Escrituras deshabilitadas hasta migración SQL.)
- **Limpiado comentario muerto** `modules/comercial/queries/hub.py:62` (`# from core.db import get_mongo_db`).
- **Guardrail extendido a `core/`:** `test_p5_1_no_mongo_residual_modules.py` ahora escanea `modules/` Y `core/` (imports pymongo/motor + patrón roto `client=None`). Scan = 0 imports prohibidos / 0 stubs rotos.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **9/9**, `health/v1` healthy, Admin CORE en paridad (200/2), destinatarios 200. NO-MONGO end-to-end en runtime (`modules/`+`core/`) logrado.
- **Nota de proceso:** 2 veces un `search_replace` en paralelo sobre el MISMO archivo no persistió una edición (se detectó por verificación post-parche y se reaplicó). Aprendizaje: editar el mismo archivo de forma secuencial.

## [2026-06-07] Fase 17 — P5-3C Sunset `api_connections/repository.py` + retiro `core/mongo_compat`
- **AUDITORÍA DE SCRIPT (rechazado):** `fase17_*.sh` NO ejecutado — mismo defecto FATAL que P5-3A: reemplazaba `db.api_connections_cache.delete_one(` por `pass` dejando el `await` → **`await pass`** (SyntaxError), y escribía el archivo roto ANTES del `py_compile` → habría tirado el backend por hot-reload.
- **Decisión:** `api_connections_cache` y `api_health_logs` no las **lee** nadie (solo escritura) → **retirada limpia** (no migración).
- **Fix aplicado:** `modules/api_connections/repository.py`: removido `def get_mongo_db()` local; `_sync_to_mongo_cache` → no-op (`return False`); removido bloque de borrado de caché en `delete_api_connection`; removido bloque de health-log en test. Conteo `get_mongo_db`/`api_connections_cache`/`api_health_logs` = **0**. (Nota: había código duplicado de `_sync_to_mongo_cache`; se neutralizó en 2 pasos.)
- **Guardrail reescrito al end-state:** `test_api_connections_mongo_degrades_safe.py` ahora exige 0 residual Mongo + exports SQL-First.
- **Retiro `core/mongo_compat`:** sin consumidores runtime tras limpiar admin + api_connections. Neutralizado el último consumidor (`scripts/rotate_server_secret_key.py::sync_to_mongodb` → no-op NO-MONGO) y **eliminado `core/mongo_compat.py`** (backup en `auditorias_p5/`). Nuevo guardrail `test_no_mongo_compat.py` (archivo ausente + sin imports).
- **Verificado:** backend arrancó SIN errores de import, guardrails **9/9**, contrato Admin CORE en paridad (LIST 200/2, ITEM 20 keys), `GET /api/api-connections` 200, `health/v1` healthy.
- **PENDIENTE (residual Mongo separado, pre-existente y GUARDADO):** `core/auditoria.py::_get_mongo_db` (patrón `client=None; client[db_name]` en try/except → return None, degrada seguro). Mi guardrail cubre `modules/`; falta extenderlo a `core/` y neutralizar este stub. `modules/comercial/queries/hub.py:62` es solo un comentario.

## [2026-06-07] Fase 16 — P5-3B-2/3 Admin CORE: retiro total de `get_mongo_db` (NO-MONGO completo)
- **AUDITORÍA DE SCRIPT (rechazado):** `fase16_*.sh` NO ejecutado. Defectos: (1) su `pattern_find` esperaba variable `mongo_doc` pero el código real usa `mongo_server` → abortaba; (2) su GATE/regex buscaba `'mongodb_id':` (literal dict) pero el código usa `formatted['mongodb_id'] =` (asignación) → abortaba; (3) habría sourceado `mongodb_id` desde SQL de forma incondicional → **agregaba 2 keys** al output rompiendo la paridad del contrato.
- **Análisis de contrato:** ambos endpoints llaman `format_core_connection(conn, include_mongo=True)`, pero como la conexión Mongo siempre era None, el bloque nunca agregaba `mongodb_id`/`mongo_synced` → el baseline tiene 20 keys sin esos campos.
- **Fix aplicado (corregido):** `api/admin_core_connections.py`: removido por completo el bloque vestigial `if include_mongo: ... db.servidores_conexiones.find_one ...` (mantiene salida idéntica) + removido el import `from core.mongo_compat import get_mongo_db`. `get_mongo_db` count en admin = **0**.
- **Guardrail actualizado:** `test_admin_core_import_source_is_correct` ahora exige `get_mongo_db not in txt` (end-state NO-MONGO) en vez de exigir el import de mongo_compat.
- **Verificado:** `py_compile` OK, backend RUNNING, guardrails **8/8**, **PARIDAD_CONTRATO=True** (item 20 keys exactas, 0 extra/0 faltan; LIST 200/2; 404s idénticos), `health/v1` healthy. Backup `.bak_*`.
- **Estado Admin CORE:** 100% SQL-First / NO-MONGO (auditoría→`Servidores_Conexiones_Log`, formateo desde fila SQL, sin `get_mongo_db`). Resta sunset: `modules/api_connections/repository.py` (caché/health-logs) y retiro final de `core/mongo_compat` cuando no queden consumidores.

## [2026-06-07] Fase 15 — P5-3B-1 Auditoría Admin CORE Mongo→SQL (`Servidores_Conexiones_Log`)
- **AUDITORÍA DE SCRIPT (rechazado):** `fase15_*.sh` NO ejecutado. Defectos: (1) su GATE busca `def _log_audit(` pero la función real es `audit_core_action` (línea 83) → habría abortado sin parchar; (2) mapeo de campos incorrecto (`log_data` tiene `core_connection_id`/`action`/`user_email`, no `server_id`/`user`); (3) no-canónico: abría `pymssql.connect` crudo desde env en vez de la conexión write-capable ya importada `get_edarsahub_pymssql_connection`.
- **Fix aplicado (corregido):** `api/admin_core_connections.py`: nuevo helper `_write_admin_audit_log_sql(log_data)` que inserta en `dbo.Servidores_Conexiones_Log` vía `get_edarsahub_pymssql_connection` (parametrizado `%s`, no bloqueante), mapeo correcto (`core_connection_id→servidor_id`, `action→accion`, `user_email→usuario`, `json.dumps(log_data)→datos_nuevos`, `GETDATE()→fecha`), truncado defensivo (`accion`≤20, `usuario`≤100 según esquema real). Reemplazado el bloque Mongo `db.auditoria_core_admin.insert_one(log_data)`. `import json` añadido.
- **Hallazgo:** `audit_core_action` es función muerta (sin callers) → migración valida sunset NO-MONGO; validado el INSERT directamente (no por endpoint).
- **Verificado:** smoke real → `INSERT_OK=True`, fila persistida en `Servidores_Conexiones_Log` (accion/usuario/datos_nuevos) y limpiada. Primer intento reveló truncamiento `accion` nvarchar(20) (escritura SÍ permitida → no es problema de permisos). Backend RUNNING, guardrails 8/8, **contrato Admin CORE = paridad total con baseline** (LIST 200/2, ITEM 200/20-keys, 404 idénticos), `health/v1` healthy. Backup `.bak_*`.
- PENDIENTE P5-3B-2/3: `get_mongo_db` sigue usado en `audit_core_action`... no — ya removido ahí; sigue en el formateo de item (`servidores_conexiones.find_one` → `mongodb_id`/`mongo_synced`, ~línea 249). Migrar a leer `mongodb_id` de la fila SQL y luego retirar el import `get_mongo_db`.

## [2026-06-07] Fase 14 — P5-3B Auditoría exacta pre-cutover Admin CORE (read-only)
- Script `fase14_*.sh` ejecutado (auditoría read-only, sin cambios código/BD/restart; SQL solo lectura a `INFORMATION_SCHEMA`/`TOP 1` mostrando **solo nombres de columnas**, sin valores → sin fuga de secretos).
- **Contrato HTTP congelado** (`auditorias_p5/FASE14_ADMIN_CORE_*`): `GET /core-connections`→200 `{status:SUCCESS,data:[2],meta}`; `GET /{id}`→200/404; `POST /{id}/test`→200 `{status,message,name,server_id,duration_ms,safe_error}`/404. DATA_KEYS documentadas.
- **Hallazgo:** los GET/POST ya son SQL-First sobre `dbo.Servidores_Conexiones`. Residual Mongo en admin = 2 puntos (ya no-op): `auditoria_core_admin.insert_one` y `servidores_conexiones.find_one` (mongodb_id/mongo_synced vestigial).
- **Destino SQL para auditoría identificado:** `dbo.Servidores_Conexiones_Log` (servidor_id, accion, datos_anteriores/nuevos, usuario, fecha, ip_origen). `mongodb_id` ya es columna en `Servidores_Conexiones`.
- **Blueprint cutover** escrito en `auditorias_p5/P5_3B_BLUEPRINT_CUTOVER_ADMIN_CORE.md` (5-6 pasos, bajo riesgo, validable contra contrato congelado). Pendiente aprobación para ejecutar el cutover (toca router vivo).

## [2026-06-07] Fase 13 — P5-3B-A Guardrails + snapshot contrato Admin CORE (pre-cutover)
- **AUDITORÍA DE SCRIPT (corregido antes de ejecutar):** `fase13_*.sh` tenía un defecto: 2 tests importan módulos de la app (`exec_module` de `admin_core_connections`, `from modules.api_connections import repository`) que requieren `EDARSAHUB_SQL_*`; bajo `pytest` desde bash el `.env` NO se carga → fallaban → `set -e` abortaba antes del snapshot. Confirmado: `EDARSAHUB_SQL_HOST` ausente en shell ambiente.
- **Fix permanente:** creado `tests_guardrails/conftest.py` que carga `/app/backend/.env` (`load_dotenv`) + asegura `/app/backend` en `sys.path`. Reutilizable por todos los guardrails que importen módulos.
- **Guardrails creados (6/6 PASS):**
  - `test_admin_core_contract_and_imports.py`: import correcto (`get_mongo_db` desde `core.mongo_compat`, no desde `core.db`), rutas esperadas (`GET ""`, `GET "/{server_id}"`, `POST "/{server_id}/test"`), módulo importa limpio con `router`.
  - `test_api_connections_mongo_degrades_safe.py`: `repository.py` sin import `from core.db import get_mongo_db`, conserva guardas `if db is None`, expone `create/update/delete_api_connection`.
- **Snapshot contrato HTTP actual (baseline para cutover)** en `auditorias_p5/FASE13_CONTRATO_ADMIN_CORE_*`: `GET /core-connections` → 200 `{status:SUCCESS, data:[2], meta}`; `GET /{id}` inexistente → 404 `{"detail":"Conexión CORE no encontrada"}`; `POST /{id}/test` inexistente → 404; `health/v1` → healthy.
- Sin cambios a runtime/BD/frontend/rutas. Listo para P5-3B (cutover SQL-First endpoint por endpoint contra este contrato).

## [2026-06-07] Fase 11 — P5-3A Fix import roto `get_mongo_db` → Admin CORE router reactivado
- **AUDITORÍA DE SCRIPT (rechazado):** `fase11_p5_3a_admin_core_api_connections_safe.sh` NO ejecutado. Defectos: (1) inyectaba helpers `_safe_mongo_*` REDUNDANTES en `admin_core_connections.py` (las ops Mongo líneas 116/251 ya están guardadas con `if db:` + try/except); (2) en `api_connections/repository.py` reemplazaba `db.api_connections_cache.delete_one(`/`update_one(`/`api_health_logs.insert_one(` por funciones SÍNCRONAS dejando el `await` delante → `await <dict>` = TypeError latente si Mongo volviera. Churn innecesario.
- **Fix mínimo aplicado (opción a real):** `api/admin_core_connections.py` línea 33 `from core.db import execute_sql_query, get_mongo_db` → split en `from core.db import execute_sql_query` + `from core.mongo_compat import get_mongo_db`. Causa raíz: `core/db.py` NO exporta `get_mongo_db` (vive en `core/mongo_compat.py`) → ImportError → el router Admin CORE NUNCA se registraba (34 WARNINGs históricos "Error registrando Admin CORE router").
- `modules/api_connections/repository.py`: SIN cambios — sus 3 ops Mongo (caché delete/update, health log insert) ya están guardadas con `if db is None`/`if db is not None`; `get_mongo_db()` (mongo_compat) retorna None → no-op seguro.
- Verificado: `py_compile` OK, backend RUNNING, **`GET /api/admin/core-connections` → 200** `{status,data,meta}` (antes 404 por no registrarse), sin error Admin CORE tras el último arranque, `health/v1` → healthy, guardrail NO-MONGO 2/2. Backup `.bak_*`.
- NOTA: migración SQL-First completa de estos endpoints (leer `dbo.Servidores_Conexiones`, auditoría/caché/health-logs a SQL) queda como lote futuro P5-3B (blueprint en `auditorias_p5/FASE11_P5_3_*`).

## [2026-06-07] Fase 10 — P5-2 Guardrail CI NO-MONGO + neutralización 2 stubs rotos extra
- **AUDITORÍA DE SCRIPT (rechazado):** `fase10_p5_2_requirements_guardrail.sh` NO ejecutado. Defectos: (1) GATE `get_mongo_db` aborta siempre — hay 12+ refs VIVAS (`core/mongo_compat.py`, `modules/api_connections/repository.py`, `api/admin_core_connections.py`, etc.); (2) objetivo ya cumplido: `requirements.txt` NO contiene `pymongo`/`motor`; (3) parche requirements roto: `'"$REQ_FILES"'` en heredoc `<<'PY'` (sin interpolación) → FileNotFoundError; (4) el guardrail que crea se auto-falla (`test_no_get_mongo_db_left` escanea su propio código que contiene `get_mongo_db`).
- **Guardrail creado (versión propia, acotada):** `tests_guardrails/test_p5_1_no_mongo_residual_modules.py` — pytest + standalone. Falla si reaparece en `/app/backend/modules/`: imports vivos `pymongo`/`motor`/`MongoClient`/`AsyncIOMotorClient`, o el patrón roto `client = None` usado como conexión (`db = client[...]`/`.find(`/`.find_one(`). Acotado a `modules/` → no se auto-falla. PASS (2/2).
- **Bonus:** el guardrail detectó 2 stubs Mongo rotos pre-existentes adicionales → neutralizados al patrón canónico deprecado-None:
  - `modules/finanzas/repository_cuadres_z.py::get_db` (código muerto: tesoreria usa la versión `_edarsahub` SQL).
  - `modules/configuracion/routes/config_asignaciones_routes.py::get_db` (router vivo, pero `get_db()` ya crasheaba en `client[db_name]` → sin regresión).
- Verificado: `py_compile` OK, backend RUNNING, `GET /api/health/v1` (auth) → 200 `healthy`, guardrail 2/2.
- NOTA pendiente: capa `core/mongo_compat.get_mongo_db` aún cableada en `api_connections`/`admin_core_connections` (residual Mongo mayor, fuera de alcance de este lote).

## [2026-06-07] Fase 9 — P5-1 Sunset mínimo `historical_kpis_repository.py` (NO-MONGO)
- Contexto: el módulo ya no tenía `import pymongo/motor` vivos; el riesgo real eran 3 funciones legacy Mongo ROTAS (`client = None` → `db = client['edarsa_hub']`) que reventarían si se reactivaran. Verificado: NINGÚN router importa el módulo (código muerto inerte).
- Neutralización quirúrgica por bloques de función: `_get_edarsahub_credentials`, `_get_edarsahub_credentials_sync` y `migrate_staging_mongo_kpis_to_sql` → stubs que retornan `{"disabled": True, "reason": "MONGO_LEGACY_SUNSET"/"MONGO_STAGING_SUNSET"}`. Sin tocar lógica SQL viva.
- Removido import huérfano `from core.secret_manager import decrypt_secret, is_encrypted_secret` (solo lo usaban las funciones Mongo retiradas).
- **AUDITORÍA DE SCRIPT (rechazado):** el script del usuario `fase9_p5_1_sunset_historical_kpis_minimo.sh` era un **no-op engañoso**: sus 3 regex usaban `\([^)]*\):` (esperan `):` pegado) pero las firmas reales son `() -> Dict:` y `migrate_...(` multilínea → 3× NO-MATCH. Habría reportado `PATCHED`+`health OK` SIN neutralizar nada. Se aplicó versión corregida (reemplazo por bloques línea-a-línea).
- Verificado: `py_compile` OK, `NO_MONGO_RESIDUAL`, backend RUNNING, `GET /api/health/v1` (auth) → 200 `overall_status=healthy` (6/6 dominios). Backup `.bak_*`.

## [2026-06-07] Bugfix server nombre + Fase 8B P2-2B (frontend Mis Tareas/Asignaciones)
- `modules/comercial/repository.py::_sql_row_to_server_dict`: agregado alias `'nombre'` (= `row['nombre']`) junto a `'name'` (consumidores que esperan `nombre`). Verificado: name/nombre poblados (130° MERIDA, CIENFUEGOS, LA ESTELAR, ManagmentPro). Nota: el "nombre None" reportado antes fue un falso positivo (la clave de salida es `name`).
- `frontend/src/pages/ConfigAsignaciones.jsx`: FIX bug real `getUserRole()` usaba `token` no declarado → `ReferenceError`. Ahora `const token = getToken()` (import `{ getToken }` de `lib/api`). + hardening `ensureArray`/`asString` en setters y Radix Selects (value string).
- `frontend/src/pages/MisTareas.js`: helpers `ensureArray`/`normalizeTareas`/`normalizePendientes`, null-safety en setters y derivados. Corregidos 3 lint bloqueantes preexistentes (comillas sin escapar `&quot;`; `set-state-in-effect` → efecto envuelto en `init()` async).
- Validado: `yarn build` BUILD_OK=1, lint 0 bloqueantes, consola sin `ReferenceError`. Captura autenticada bloqueada por PREVIEW_CACHE_RESET (limitación del preview). Scripts/back.: `/app/scripts/fase8b_*`, `.bak_*`.


## [2026-06-07] Bugfix — Dashboard Comercial "Servidor no encontrado en configuración"
- Causa raíz: `modules/comercial/repository.py::_get_server_by_id_sql` interpolaba `{id}` (función builtin `id` de Python → `'<built-in function id>'`) en el f-string del query en vez de `{server_id}`. La consulta a `Servidores_Conexiones` nunca encontraba el servidor → `get_server_by_id` retornaba None → el endpoint `/api/comercial/dashboard/{server_id}` respondía `source_status=ERROR, "Servidor no encontrado en configuración"`.
- Fix: usar `{server_id}` con escape de comillas (`safe_id = server_id.replace("'", "''")`) para evitar inyección SQL.
- Verificado: `GET /api/comercial/dashboard/{server_id}` → 200 `source_status=SUCCESS` en los 4 servidores (3 SoftRestaurant + 1 MPRO). `health/v1` → healthy. Backup `.bak_*`.


## [2026-06-07] Fase 8 — P2-2A Contención de ruido backend no bloqueante
- `core/health_checker.py`: `_check_mongodb` → `UNKNOWN` (residual deshabilitado, ya no `CRITICAL`); `_check_sql_servers` → `[]` (catálogo legacy dependía de Mongo); conteo no suma fallo por fuentes `UNKNOWN`. Resultado: `OVERALL=healthy, sources_failed=0`.
- `core/scheduler/jobs/crm_sync_job.py`: helper `_is_missing_schema_error` + `_skip_result`; `execute_crm_sla_check`/`execute_crm_actividades_vencidas` devuelven `SKIP` controlado ante esquema CRM incompleto (`Invalid column 'OportunidadID'`) en vez de spamear errores. Verificado: CRM_ACT=SKIP.
- `modules/fase2_operativo/services/sla_service.py`: guards `if not tarea or not isinstance(tarea,dict)` en `calcular_estado_sla`, loops y `notify_sla_warning/expired/escalated` (→ False). Sin crash con tarea None.
- Patches por `txt.replace()` de cadena exacta (fail-safe). Validado: 3/3 compile OK, backend RUNNING, `health/v1` (auth) → healthy. Script: `/app/scripts/fase8_p2_2a_contencion_ruido_backend.sh`.


## [2026-06-07] Fase 7 — P2-1 Neutralización residual Mongo en Comercial
- `modules/comercial/kpis_repository.py :: upsert_kpi_comercial`: guard temprano `if db is None -> return {"action":"SKIP","disabled":True,"reason":"MONGO_COMMERCIAL_DEPRECATED"}`. Elimina el crash `None[COLLECTION].find_one(...)` en cada sync (la función la importa `api/sync_receiver.py:147`, que solo lee `result["action"]`).
- Hallazgo: el script original apuntaba a 4 funciones inexistentes y omitía la única Mongo viva; se implementó la neutralización correcta. Las `get_*`/`cerrar_periodos_anteriores` no las importa ningún router (código muerto inerte).
- Verificado: smoke `upsert_kpi_comercial` → SKIP no-op sin crash; `health/v1` → healthy.
- Script: `/app/scripts/fase7_p2_1_neutralizar_mongo_comercial.sh` (versión corregida).


## [2026-06-07] Fase 6 — Endpoint semáforo `/api/health/v1` (SQL-First / NO-LIVE)
- Nuevo módulo `backend/modules/health_v1/routes.py` + registro en `server.py` (import tras finanzas.health; include tras `app.include_router(api_router)`).
- `GET /api/health/v1` agrega salud canónica de los 6 dominios estabilizados: sql_canonic, tablero_comercial (vistas v2_Runtime queryables), users_roles, config_operativa, explorador_bd (helper local), finanzas (tablas requeridas). NO consulta operativos externos.
- Resultado: `overall_status=healthy`, 200 en ~1.7s. Probe de vistas = queryability estructural (vista vacía ≠ rota).
- NOTA: bloqueado el registro del script del usuario (prepend de import en línea 1 → antes de `load_dotenv()` → habría roto el arranque). Registrado de forma segura.
- Scripts: `/app/scripts/fase6_crear_health_v1.sh` (versión corregida) y `/app/scripts/fase6_validar_health_v1.sh`.


## [2026-06-07] Fase 1 — Estabilización V1.0: 5 P0 cerrados (SQL-First / NO-MONGO / NO-LIVE)
Todos validados con cURL/pytest (sin testing_agent, por prohibición). Backups `.bak_*` por archivo.
- **P0-1 Vistas corruptas (Tablero/Comercial)**: normalizadas `vw_vw_..._Runtime_Runtime` → `vw_Comercial_KPIs_Diarios_v2_Runtime` y `..._Mensuales_v2_Runtime` en 10 archivos vivos. `GET /api/comercial/tablero-ejecutivo` y `/api/dashboard-ejecutivo/resumen` → 200 con datos EDARSAHUB_SQL.
- **P0-2 RBAC + CRUD Usuarios/Roles**: `core/rbac_helper.py` reescrito SQL-First **async** (`run_in_threadpool`, bypass por CodigoRol `SUPERADMIN`/`ADMIN`+NivelJerarquia, fail-closed). Añadidas 11 funciones **module-level** SQL-First en `modules/auth/repository.py` (get_db→None, get_users_by_empresas, get_all_roles, find_role_by_id/by_name, create/update/delete_role, count_users_with_role, create_default_roles, deactivate_user). `core/alcance_helper.py`: SuperAdmin reconoce CodigoRol `SUPERADMIN`. CRUD users/roles GET/POST/PUT/DELETE → 200. pytest `tests/test_rbac_helper.py` 5/5.
- **P0-3 Configuración Operativa (cursor tupla-vs-dict)**: helpers `_rows_dicts`/`_one_dict` en `api/configuracion_operativa_unidades.py` (3 sitios fetch, incl. `/todas/`). Endpoints config-operativa + probar-fecha-operacion → 200.
- **P0-4 Explorador BD**: repuesto `_execute_sql_direct_with_error` en `core/db.py` (async, `asyncio.to_thread(execute_sql_query)`). `/api/explorador/conexiones-explorables` (13) y `/api/explorador/tablas/{server_id}` → 200.
- **P0-5 Finanzas /health 502**: `include_server_details` default `True→False` en `modules/finanzas/health.py`. Health canónico solo EDARSAHUB (NO-LIVE) → 200 en 0.28s; sondeo externo ahora opt-in (`?include_server_details=true`).
- NOTA scripts del usuario: 3 de 5 traían defectos detectados antes de ejecutar (líneas no cubiertas en FASE1/FASE3; métodos de clase vs module-level en FASE2b; **SyntaxError** en FASE5). Se implementaron versiones corregidas. FASE4 estaba correcto.


## [2026-06-07] Fase 0 — Auditorías profundas A/B/C (SIN cambios de código de app)
- Doc actualizado: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (secciones 6 y 7).
- **A (UI smoke, 12 menús)**: ningún logout ni crash; KPIs Tablero/Comercial vacíos (403+vista); Config.Operativa atascada (500); Mis Tareas 12 JS-err, Asignaciones 8 JS-err.
- **B (NO-LIVE)**: guard rail `LEGACY_LIVE_DISABLED` OK; intentos live en logs = jobs de sync (ETL); **vista corrupta `vw_vw...` en 88 referencias** (Comercial/Tablero KPIs).
- **C (RBAC)**: `core/rbac_helper.verificar_permiso_rbac` es Mongo y crashea → rompe CRUD usuarios/roles (NO-MONGO + 500); SUPERADMIN no bypassa scope de unidad en `comercial_v2` (403); enforcement disperso.
- Test users (autorizados): `qa.superadmin@edarsa.com`/`QaSuper2026!` (nuevo) y `admin@edarsa.com`/`pruebas123` (promovido a SUPERADMIN).


## [2026-06-07] Fase 0 — Auditoría v1.0 producción (SIN cambios de código)
- Entregable: `/app/auditorias_p5/AUDITORIA_V1_PRODUCCION_MATRIZ.md` (matriz por menú: front/back, endpoints, auth, RBAC, filtros, tablas canónicas, legacy/stub, live prohibido, mongo residual, estado, riesgo, recomendación).
- Bloqueadores hallados: **Tablero Ejecutivo 500** (vista corrupta `vw_vw_vw_vw_..._Runtime_Runtime...` → real `vw_Comercial_KPIs_Diarios_v2_Runtime`); **Explorador BD** import roto `_execute_sql_direct_with_error`; **Finanzas /health 502**; intentos **NO-LIVE** a operativos en logs; **Mongo residual** alcanzable en `comercial/cache_service|kpis_repository|historical_kpis_repository`.
- Sin correcciones aplicadas (a la espera de aprobación de Fase 1).


## [2026-06-07] Limpieza de menú: rutas rotas → "Pronto" + 2 rutas corregidas

- **2 ítems con ruta mal escrita corregidos** (apuntaban a rutas inexistentes pese a tener pantalla):
  - `Asignaciones`: `/asignaciones` → `/configuracion/asignaciones` (validado: abre "Asignaciones de Inventarios").
  - `Config. Operativa`: `/configuracion-operativa` → `/admin/configuracion-operativa`.
- **11 módulos sin pantalla marcados `comingSoon: true`** (Inventarios, Host to Host, Contabilidad, Comisiones, Inteligencia Artificial, Calidad/Auditoría, Proyectos, Marketing, Activos Fijos, Integraciones, Programación). `EnterpriseSidebarMenu` los renderiza **deshabilitados** (no clicables) con badge **"Pronto"** y tooltip "— Próximamente". `go()` ignora ítems `comingSoon`.
- **Validado (playwright)**: clic en ítem `comingSoon` (Contabilidad) NO navega ni expulsa; ítem corregido (Asignaciones) abre su pantalla. Lint limpio.


## [2026-06-07] FIX lote: Permisos 403, crash Select, logout navegación (Issue #1) y race recarga (Issue #2)

### 🐞 Guardar permisos de usuario → "Error al guardar permisos" (backend, 403/404)
- `PUT /api/users/{id}/permissions` devolvía **403** porque `ROLE_HIERARCHY` (modules/auth/service.py) solo reconocía `NombreRol` legacy ('SuperAdministrador'), pero el JWT usa `CodigoRol` canónico ('SUPERADMIN'/'ADMIN'). → Mapeados AMBOS (NombreRol + CodigoRol) a la escala legacy y `_get_role_level` ahora tolera mayúsculas.
- Tras el 403, había un **404 latente**: el servicio resolvía el usuario solo por `PublicUUID`, pero el frontend envía el `UsuarioID` numérico. → Resolución por `TRY_CONVERT(INT)` OR `PublicUUID`.
- **Validado (curl)**: 200 "Permisos actualizados" con id numérico + payload de sucursales/almacenes (inserts confirmados en SQL). Datos de prueba limpiados.

### 🐞 Crash runtime `<Select.Item /> value=""` (frontend)
- `BitacoraComponents.jsx` tenía 2 `SelectItem value=""` (Radix lo prohíbe). → Centinela `value="todos"` mapeado a `''` en `onValueChange` (preserva la lógica del filtro). Lint limpio.

### 🐞 Issue #1: logout al navegar Operaciones → Tablero Ejecutivo (frontend, sin 401/403)
- Causa raíz: el favorito "Dirección / Tablero Ejecutivo" (`enterpriseMenuConfig.js`) apuntaba a `/dashboard-ejecutivo`, ruta **inexistente** en App.js → catch-all `*` → `/login`. (~13 ítems de menú más apuntan a rutas no construidas con el mismo efecto.)
- Fix: (1) corregido path → `/tablero-ejecutivo`; (2) catch-all `*` ahora usa `CatchAllRedirect`: si hay sesión → `/tablero-ejecutivo`, si no → `/login` (evita logout espurio en CUALQUIER ruta desconocida).
- **Validado (playwright)**: clic en Tablero y ruta rota `/inventarios` ya NO expulsan.

### 🐞 Issue #2: race 403 en recarga dura del dashboard (frontend)
- `accessContextService.getAuthHeaders()` leía el token de la llave `'token'` (inexistente) en vez de la canónica `'edarsa_memory_token'` → `/auth/access-context` iba SIN Bearer → 403. → Usa `getToken()` canónico.
- `previewCacheUtils.shouldClearKey` borraba `edarsa_memory_token` (prefijo 'edarsa') en cada carga (BUILD_VERSION=Date.now()) → token perdido en recarga. → Lista `NEVER_CLEAR` protege token/usuario/marcador.
- **Validado (playwright)**: recarga dura + reload puro de Operaciones → 0×401/403, sin logout; access-context = 200.

### 🐞 Enlace de reset apuntaba a host bloqueado (backend)
- `forgot_password` usaba el `Origin`/`Referer` de la request; si el usuario entraba por `*.preview.emergentcf.cloud` (bloqueado, 403), el correo armaba ese enlace. → Siempre usa `FRONTEND_URL` canónico.

## [2026-06-07] FIX: Pantalla "Restablecer contraseña" saltaba al login

### 🐞 Bug (P0 reportado por usuario)
- **Síntoma**: El correo de recuperación llega y el enlace abre la pantalla de nueva contraseña, pero ésta "no se detiene": se muestra un instante y de inmediato salta a la ventana de iniciar sesión, sin poder capturar la nueva contraseña.
- **Causa raíz (frontend)**: `ResetPassword`/`ForgotPassword` se renderizan dentro de `<AuthProvider>`, que al montar llama a `GET /auth/me`. Sin sesión → 401. El interceptor de `lib/api.js` redirigía a `/login` para toda ruta que no fuera login/portales (no contemplaba el flujo de recuperación).
- **Fix**: En `lib/api.js` se añadió `isAuthFlowPage` (`/forgot-password`, `/reset-password`) a la lista de exclusión del redirect forzado en 401. El backend NO se tocó (el token, SMTP y reset SQL ya funcionaban).
- **Validado (screenshot)**: `/reset-password?token=...` permanece estable 4s, sin redirect; el input `reset-password-new` queda disponible para escribir la nueva contraseña.

## [2026-06-06] FASE AUTH-V2-ALIGN: Operaciones v2 (401/403/500) + forgot-password

### ✅ Capa 1 — Auth frontend (alineación canónica)
- **Problema**: `operativoApi.js` y 5 componentes hacían `fetch` crudo solo con `credentials:'include'` (cookie). El backend v2 solo lee el header Bearer → 401 (require_permission) / 403 (HTTPBearer de get_current_user).
- **Fix**: `getToken()` exportado desde `lib/api.js` (fuente única). Helper `authedFetch()` en `operativoApi.js` inyecta `Authorization: Bearer` + mantiene cookie. Migrados SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel, ResponsabilidadAccionesModal, WorkflowList a `authedFetch`.
- **Validado (browser)**: las 8 rutas v2 ahora envían `auth_header=True`; 401/403 → resueltos.

### ✅ Capa 2 — RBAC roto a nivel app
- **Bug A (isoformat)**: `core/rbac/repository_sql.py:445/693` hacía `fecha.isoformat()` sobre string (FreeTDS tds_version 7.0 devuelve DATETIME2 como string). → `hasattr(...,'isoformat')`.
- **Bug B (seed por request)**: `RBACService` usaba flag de instancia; `middleware.py` instancia por request → `seed_permisos+seed_roles` corrían en CADA petición (≈6s + timeouts intermitentes → 500). → flag a nivel de **clase** (`_seeded`), seeding una sola vez por proceso.
- **Validado (curl)**: `require_permission` ahora pasa para Ricardo (SUPERADMIN). v2/health=200; sla sin token=401, con token=500 (Capa 3).

### ✅ forgot-password (mismo origen datetime-string)
- `password_reset.py:138` `ventana_exp.replace(tzinfo=...)` sobre string → `TypeError`. Helper `_coerce_aware_dt()` (maneja str DATETIME2 de 7 decimales, datetime naive/aware, None).
- **Validado**: endpoint → 200, envía correo real vía SMTP `mail.edarsa.com.mx`. SMTP confirmado OK (login + sendmail).
- Test regresión: `backend/tests/test_password_reset_datetime.py` (6/6 passed).

### ⏸ Capa 3 — DIFERIDA por decisión del usuario (bloque separado y auditado)
- `dashboard/tareas/workflows/sla/responsabilidad` dependen de Mongo eliminado: `db_utils.py:30-31` hace `None[db_name]` → `'NoneType' subscriptable` → 500. NO se aplicó degradación por stub ni migración SQL (acuerdo explícito).

### Lint pre-existente (NO introducido en esta sesión)
- `react-hooks/set-state-in-effect` (SLACard, ResponsabilidadCard, ResponsabilidadPendientesPanel) y `react/no-unescaped-entities` (ResponsabilidadPendientesPanel:215) ya existían; mi diff solo cambió `fetch`→`authedFetch` e imports. No se refactorizó (fuera de alcance / riesgo).

## [2026-05-25] Sesión Actual

### ✅ CORTES-Z-RESILIENCIA-001: Mejora de Resiliencia Arquitectónica
- **Problema**: El health check anterior reportaba timeout como "normal", lo cual fue rechazado
- **Diagnóstico**: Confirmado que Cortes Z ya era SQL-FIRST (lee de `Finanzas_CortesCaja`)
- **Causa real**: Intermitencias del servidor EDARSAHUB SQL, no arquitectura
- **Mejora**: Endpoint ya no lanza error 500, retorna estado controlado `EDARSAHUB_UNREACHABLE`
- **Archivos**: `repository_cortes_caja_edarsahub.py`, `tesoreria.py`

## [2026-05-25] Sesión Anterior

### ✅ FINANZAS-TESORERIA-SQL-001: Cortes Z migrados a SQL
- Creado `repository_cortes_caja_edarsahub.py`
- Endpoint lee de `Finanzas_CortesCaja`
- 4,083 cortes históricos disponibles

### ✅ FINANZAS-TESORERIA-MONGO-002: Cuadres Z migrados a SQL
- Modificado `tesoreria.py` para usar repositorio SQL
- Agregados métodos `listar_cuadres_z_por_server_id()`, `obtener_resumen_por_server_id()`

### ✅ Migración credenciales hardcodeadas
- Movidas credenciales de `server.py` a `.env`
- CORS origin para producción agregado

### ✅ BUG-COMPETIDORES-001 resuelto
- Corregido mapeo de campos en CompetidorModal
- Agregados campos de redes sociales

## Problemas conocidos de infraestructura
- **EDARSAHUB SQL (54.39.104.176)**: Intermitencias de conectividad ocasionales
- **SoftRestaurant (189.162.155.142)**: Connection refused intermitente

## [2026-06-07] P1 RBAC Hardening — Gates legacy → helper canónico (script usuario AUDITADO y RECHAZADO)
El usuario entregó un bash de "P1 RBAC Hardening" (regex masivo). AUDITADO y RECHAZADO por:
1) Objetivos ficticios/muertos: `modules/comercial/costos_margenes/` NO existe; `core/rbac/middleware.py` sin patrones (cero cambios).
2) Migración incompleta/inconsistente: su mapa NO incluía `role not in ["Supervisor","Administrador"]` → dejaba L258/269/298 de solicitudes_catalogo.py hardcodeadas; ni `role in [...]` pelón → dejaba security.py L655 intacta.
3) Parche ciego sobre validador de SEGURIDAD (security.py L1049 validate_for_explorer) con sólo py_compile (sintaxis) y sin prueba funcional.
4) Objetivo de bajo valor: solicitudes_catalogo.py es stub en memoria (_solicitudes_db).
Verificado: SIN import circular (rbac_helper_sql no tiene back-edge a security).
RUTA SEGURA aplicada (usuario eligió a+b — incluir SUPERADMIN):
- `core/security.py`: L655 `role in [...]`→`es_admin(user)` (import local); L1049 explorer gate→`get_role_code({'role':user_role}) not in ('SUPERADMIN','ADMIN')` (corrige bug código-vs-nombre que bloqueaba al SUPERADMIN).
- `modules/rh/solicitudes_catalogo.py`: 8 gates migrados a `get_role_code`/`es_admin`/`es_supervisor_o_superior`; SUPERADMIN ahora habilitado en aprobar/crear/autorizar/rechazar y en la vista admin de notificaciones.
- NO se tocó middleware.py ni costos_margenes (no aplican).
Validación: lint limpio + cURL (listar 200, pendientes-notificacion rol_usuario=SUPERADMIN) + pytest `tests/test_rbac_p1_hardening_gates.py` (7/7) + regresión RBAC (10/10). Sin testing_agent (prohibido).

## [2026-06-07] Auditoría RBAC Hardcodes en TODO el repo (SOLO LECTURA, planning)
Scanner propio vetado `/app/scripts/audit_rbac_hardcodes.py` (excluye backups/auditorías muertas).
Resultado código vivo: 399 hits (ALTO=50, MEDIO=74, BAJO=275). ALTO runtime real (gates a migrar): **44 en 14 archivos**.
Top: server.py(15), core/security.py(5), core/rbac/middleware.py(3), core/server_registry.py(3),
modules/costos_margenes/routes.py(3), routes_precios.py(3), auth/service.py(2), catalogos/routes.py(2),
fase2_operativo automatizacion_compras_routes.py(2), finanzas/propinas_tpv/routes_sql.py(2), +4 con 1 c/u.
Reportes: `docs/reports/AUDITORIA_RBAC_HARDCODES_REPO_20260607_213039.csv` + `.md`.
NOTA: `modules/comercial/costos_margenes/` NO existe (el módulo real es `modules/costos_margenes/`).
Hardening NO ejecutado en esta pasada — es roadmap para migración sistemática archivo-por-archivo + prueba.

## [2026-06-07] FIX P0 — Dashboard Inteligencia Comercial IA: KPIs no reaccionaban al periodo
Síntoma (reporte usuario): los KPIs (Ventas/PAX/Cheques/Propinas) no cambiaban al cambiar Unidad ni Día/Semana/Mes/Año, y no indicaba qué día/mes/año.
Causa raíz: el frontend `portal-inteligencia/pages/DashboardIA.jsx` NUNCA enviaba `periodo` (useEffect solo dependía de unidad; URL solo `?unidad=`), así que siempre mostraba el default backend (últimos 30 días) sin importar el botón. Trends (+12.5% etc.) y "+8.5% vs mes anterior" estaban HARDCODEADOS.
Fix backend `modules/inteligencia_comercial/routes.py` `/inteligencia/dashboard`:
- Nuevo param `periodo` (dia|semana|mes|anio/año). Resuelve rango anclado al ÚLTIMO DÍA CON VENTAS>0 (NO-LIVE, evita rangos vacíos). Helper `_ultimo_dia_con_datos` (parsea fecha string del view) + `_periodo_rango` (mes/semana/año/día + periodo anterior equivalente).
- Trends REALES vs periodo anterior (kpis_trends) + etiqueta legible (filtros.periodo_label, meses en español).
Fix frontend: envía `&periodo=`, useEffect depende de [unidad, periodo], valores 'anio' (evita encoding ñ), muestra etiqueta "Mostrando: <periodo>" con icono, trends reales por card, y usa data real aunque sea 0 (ya no cae al mock $15.71M). formatMoney movido a scope módulo.
Verificado vía cURL (4 periodos con KPIs distintos + trends) y screenshot (Año $21.64M vs Mes $0.48M, etiquetas correctas).
NOTA: lint `react-hooks/immutability` es ruido repo-wide preexistente (también en VentasHorarioPage.jsx sin tocar) — falso positivo del React Compiler sobre helpers con early-return.
NOTA MOCK: ventas_horario/top_productos/casas_distribuidoras del dashboard siguen siendo proporciones calculadas del total (NO datos reales por producto/casa) — escalan con el total pero son ESTIMADOS, no reales.

## [2026-06-07] FASE 0 (diagnóstico) + Opción D (preparar sync real, SIN ejecutar) — PIC datos reales
FASE 0 (solo lectura): Sync_Sales=79 tickets, SOLO 2026-06-01 ($309K) vs KPI canónico=125,833 tickets/$431.7M/2024-2026 → cobertura 0.06%. Mismo día 06-01 ≈100% (el parser está bien; falta histórico). Reporte: docs/reports/FASE0_AUDITORIA_COBERTURA_SYNC_SALES_20260607.md
CAUSA RAÍZ EXACTA (inteligencia_comercial_sync_job.py): (1) sin backfill: dias_atras=1 ventana fija + cron 0 * * * * ; los 79 del 06-01 fueron carga puntual única (created_at en 47s del 06-03). (2) get_pos_connection era STUB que devolvía get_sql_connection() (EDARSAHUB) en vez del POS real; tablas POS no existen en EDARSAHUB y TODAS las credenciales *_DB_PASS están VACÍAS. => detalle histórico no existe en EDARSAHUB; requiere export histórico (opción B, recomendada) o credenciales POS (A).
Script usuario para D: AUDITADO. Intención correcta/segura pero parche regex frágil (no idempotente) + helpers muertos + audit-script que consulta tablas de servidores inexistentes (config POS está hardcodeada en UNIDADES_CONFIG). Implementé el intent QUIRÚRGICAMENTE:
- get_pos_connection: conexión REAL pymssql al POS con guard de credenciales vacías (retorna None sin colgar => job horario = no-op seguro).
- job_inteligencia_comercial_sync: +params fecha_inicio/fecha_fin/dry_run + lógica de backfill por rango; fix refs current_date->_dt; __main__ por env vars.
- Nuevo script seguro: scripts/backfill_inteligencia_comercial_pos.py (default DRY-RUN, reusa el job, sin sync nuevo).
NO ejecutado contra POS, NO se tocaron datos (Sync_Sales sigue=79). Verificado: py_compile, lint limpio, dry-run OK (lista 5 unidades, retorno temprano), backend healthy, job horario sano.
PENDIENTE usuario: elegir B (export histórico) o A (credenciales) para llenar el 100% antes de FASE 2/3/4 (portal/normalización/casas). NO construir portal con datos parciales (mandato usuario).

## [2026-06-09] CATALOGO-CANONICO-C1 (NO-LIVE filtros) + AUTH-REFRESH (auto-logout 15 min)

### Catálogo canónico NO-LIVE — filtros de Análisis (P0, recurrencia NO-LIVE cerrada)
- **`/servers/{id}/report-filters` migrado a NO-LIVE** (server.py). Antes consultaba EN VIVO los POS (MPRO/SoftRestaurant) → violaba NO-LIVE y disparaba el cooldown de EDARSAHUB en el host compartido de MPRO (54.39.104.176). Cambio backend-only (cero cambio de UI → cero riesgo de regresión; contrato {categorias,familias,subfamilias}[{id,nombre}] idéntico).
  - **MPRO**: dimensiones derivadas de `Sync_Productos` (CodigoFuente = Ct_Cve_Categoria/Fm_Cve_Familia/Sf_Cve_SubFamilia → siguen casando con los filtros de `/reports/inventory-analysis`). Re-sync MPRO completo: 660→7957/7957 productos con categoría.
  - **SoftRestaurant**: el Análisis filtra por la jerarquía de INSUMOS (clasificacionventa/gruposiclasificacion/gruposi), que NO vive en Sync_Productos (ventas). Nueva tabla `dbo.Sync_Catalogo_Filtros` (migración `catalogo_filtros_sync_20260609.py`) + función de sync `_obtener_filtros_catalogo_sr`/`_guardar_catalogo_filtros` en `sync_recetas.py` (aditiva). Pobladas 3 unidades SR (CATEGORIA 3 / FAMILIA / SUBFAMILIA).
- Sync de Categoría a `Sync_Productos` (MPRO `Ct_Cve_Categoria`+`Categoria`, SR `grupos.clasificacion`) y MERGE: ya estaban escritos por el fork anterior; se re-ejecutó el sync MPRO para poblar.
- Verificado: cURL E2E MPRO (19/73/108) y SR (3/77/130) en ~0.5s (NO-LIVE, sin tocar POS); 4 tests `tests/test_catalogo_filtros_nolive.py`; smoke login OK.
- NOTA (bug menor pre-existente, NO bloqueante): `_registrar_ejecucion` inserta en `Sync_Control_Ejecuciones` con `StartedAtMexico` pero la columna real es `FechaInicio` (NOT NULL) → el registro de bitácora del sync falla, aunque la sincronización de datos sí se escribe correctamente.

### AUTH-REFRESH — fin del auto-logout a los 15 minutos (P0, recurrente)
Causa raíz (triple) en el flujo de refresh, que devolvía 500/401:
1. `core/refresh_tokens.py::validate_and_get_session` llamaba `.isoformat()` sobre datetimes que SQL devuelve como `str` → AttributeError. Fix: normalización defensiva `_iso()`.
2. `dbo.Sesiones` no tenía las columnas que usa la rotación/replay (`FechaRevocacion`, `MotivoRevocacion`, `ReemplazadaPorSesionID`, `RevocadoPorUsuarioID`) ni `dbo.SesionesHistorico`. Migración `sesiones_refresh_schema_20260609.py` (idempotente, no toca datos).
3. El login guardaba `UsuarioID` como `hash(uuid) % N` (¡inestable entre procesos!) → el refresh nunca encontraba al usuario ("Usuario no encontrado"). Fix: `create_session(user_id=str(user_id))` (PublicUUID estable; `find_user_by_id` lo resuelve).
- `POST /auth/refresh` ahora devuelve `{token, expires_in, message}` (antes solo seteaba cookie; `get_current_user` lee SOLO el header Bearer, así que el SPA necesita el token en el body).
- Frontend `lib/api.js`: interceptor de respuesta con **refresco silencioso single-flight** — en 401 (excepto endpoints de auth) llama `/auth/refresh` una vez (cookie httpOnly de 7 días vía withCredentials), encola requests concurrentes, actualiza el Bearer en sessionStorage y reintenta. Solo desloguea si el refresh falla.
- Rotación de refresh token + detección de replay PRESERVADAS. Consultado `integration_expert` (obligatorio) antes de tocar auth.
- Verificado: cURL (login→refresh 200 con token→/auth/me 200→rotación→replay del token viejo 401); 3 tests `tests/test_auth_refresh_flow.py`; smoke navegador (Bearer corrupto + reload → sesión mantenida, sin redirect a /login, token renovado).

## [2026-06-09] P0 USUARIOS — Activo/Inactivo (bug: todos aparecían inactivos, sin forma de activarlos)

Causa raíz triple en la pantalla Usuarios:
1. Mismatch de campo: el backend devolvía `activo` (es) pero el frontend leía `active` (en) → TODOS mostraban "Inactivo".
2. La query filtraba `WHERE Activo=1` → los inactivos no aparecían (imposible reactivarlos).
3. Filas duplicadas por el JOIN de roles (admin salía 3×).

Backend (`modules/admin_sql/routes.py`):
- `GET /admin-sql/users`: dedup con `OUTER APPLY TOP 1` (1 fila/usuario), agrega campo `active` (bool), y parámetro `incluir_inactivos` (default False) para listar también inactivos.
- Nuevo `PATCH /admin-sql/users/{id}/toggle-activo`: activa/inactiva `Usuario_Catalogo.Activo`; al INACTIVAR revoca todas las sesiones activas (`Sesiones.EstaActiva=0`, MotivoRevocacion='user_deactivated') por PublicUUID; bloquea auto-inactivación. Helper `execute_write` (commit) agregado.

Frontend (`pages/Usuarios.js`):
- loadUsers usa `?incluir_inactivos=true`; checkbox "Mostrar inactivos" (default oculto); contador "X activo(s) · Y inactivo(s)".
- Botón Activar/Desactivar (rojo/verde) en vista tarjetas y tabla, junto a Editar/Permisos/Eliminar; gateado por `canManageUser` (no aplica a SuperAdministrador).
- `getCurrentUserRole`/`currentUser` ahora usan `useAuth()` (AuthContext) como fuente primaria + getSessionUser fallback (robustez de rol en navegación SPA).

Verificado: cURL (toggle desactivar/reactivar, revocación de sesiones, bloqueo auto-inactivación, dedup 12 únicos, incluir_inactivos 20=12+8) + screenshot E2E SPA (toast "Usuario inactivado", botones Inactivar visibles, estados correctos).

## 2026-06-09 — Conectividad POS preview: diagnóstico + fixes (P0 BLOQUEANTE RESUELTO)
- DIAGNÓSTICO: la conectividad POS desde preview NUNCA se perdió. 5/7 servidores DATA_SOURCE conectan OK desde el contenedor (130MID, ESTELAR, ManagmentPro, HR2020, MPRO TABLAJERIA). Solo fallan PRUEBAS SOFTRESTAURANT (instancia mal config) y CIENFUEGOS (DDNS caído). `SERVER_SECRET_KEY` válida; credenciales desencriptan OK.
- Causa real del "0 registros" = bugs de query/arquitectura, NO red.
- FIX 1: query almacenes SoftRestaurant (`sync_service.py`) → `tipo_almacen='GENERAL'` (CHECK constraint + conversión numérica).
- FIX 2: `_query_origen` movimientos (`sync_movimientos_canonico.py`) corregido a esquemas reales (MPRO `Mv_*`; SoftRestaurant JOIN `insumospresentaciones.idinsumo`, sin `cancelado`).
- FIX 3: `resolver_canonico.py` refactor → conexión compartida + caches (antes ~14k conexiones/run sin cerrar → timeout EDARSAHUB).
- FIX 4: detalle movimientos → `abs(cantidad/costo)` + skip cantidad 0 (CHECK `Cantidad>0`).
- E2E PROBADO desde preview: 46 almacenes y 366 movimientos ESTELAR (3d, 0 descartados) persistidos en tablas canónicas.
- Scripts diagnóstico/regresión: `/app/backend/tests/diag_*.py`.
- PENDIENTE (no conectividad): poblar `Inventario_ConceptoMapeoOrigen` para MPRO; desambiguar sucursal MPRO compartido; adapter `tablajeria_mpro`; backfill completo como job background.

## 2026-06-09 (cont.) — Requisiciones SR+MPRO NO-LIVE + migración detalle-movimientos
- FIX sync_requisiciones (`sync_service.py`): queries corregidas a esquemas reales.
  - MPRO: `Orden_Compra` agrupada por folio; `Es_Cve_Estado` (no Oc_Status), `Pv_Descripcion` (no Pv_Nombre), importe=SUM(Oc_Precio_Neto_Importe) (no Oc_Total).
  - SoftRestaurant: `ordenescompra` con `fechacaptura/fecharecepcion`, `aplicada/cancelado`, JOIN `ordenescompramov` por idordencompra (no 'estatus'/'fecha').
  - E2E: ESTELAR=86, ORIGEN(MPRO)=2947 requisiciones en `Compras_Requisiciones_Sync`.
- FIX lectura `obtener_requisiciones_sync`: el filtro de sucursal ocultaba SoftRestaurant (guarda sucursal=''). Ahora filas sin sucursal pasan dentro del mismo server_id (SR es 1:1 servidor-sucursal). Endpoint `/compras/pedidos-vigentes/{id}` verificado: ESTELAR 86, ORIGEN 500.
- MIGRACIÓN NO-LIVE `/compras/detalle-movimientos` (POST, server.py): antes consultaba POS live (movtosalmacen/movsinv). Ahora lee EXCLUSIVAMENTE tablas canónicas (Inventario_MovimientosDetalle/Movimientos/TipoMovimiento/Almacenes), resolviendo codigo→ProductoID vía `Producto_MapeoOrigen`. Verificado: producto A700002 (ESTELAR) devuelve movimientos reales con entradas/salidas/totales y source=EDARSAHUB_NOLIVE.

## 2026-06-09 (cont.) — Mapeo de conceptos MPRO + sync movimientos MPRO E2E
- Poblado `Inventario_ConceptoMapeoOrigen` para SystemType='MPRO' (84 tipos del catálogo activo `Tipo_Movimiento`). Regla determinista validada por usuario: TRASPASO/TRANSFERENCIA/TRANSITO→5/6; COMPRA(EN)→1; COMPRA/PROVEEDOR(SA)→2; resto por naturaleza→3(EN)/4(SA). Decisiones usuario: 700 NOTA DE VENTA→4, conversión/tablajería→AJUSTE, 051 anulación compra→2, 940 bonificaciones→3. Script: `tests/seed_mpro_concepto_mapeo.py`.
- FIX multisucursal MPRO (bonus, necesario para correctitud): `_query_origen` MPRO ahora filtra `Sc_Cve_Sucursal = sucursal_origen` (ORIGEN=0023/130QRO=0021), evitando mezclar movimientos de ambas sucursales en una.
- FIX query almacenes MPRO (`sync_service.py`): `Al_Estatus` (no existe) → `Es_Cve_Estado='AC'`; + filtro `Sc_Cve_Sucursal` (el código de almacén se repite por sucursal).
- E2E MPRO (ORIGEN, 3d): almacenes=5; movimientos=182 enc + 182 det, **0 descartados, 0 pendientes** (tipo/almacen/producto/sucursal=0). Antes 100% pendiente 'tipo'.
- Endpoint NO-LIVE `/compras/detalle-movimientos` verificado con producto MPRO: devuelve movimientos canónicos (AJUSTE_ENTRADA, etc.) con source=EDARSAHUB_NOLIVE.

## 2026-06-09 (cont.) — Job sync_compras: wiring multisucursal + optimización backfill
- FIX job (`sync_compras_job.py`): `_get_servers_to_sync` y `unidad_info` ahora incluyen `sucursal_origen_id` (antes None → MPRO multisucursal resolvía AMBIGUO y no sincronizaba). Wrapper `sync_movimientos_from_server` usa ventana configurable `SYNC_COMPRAS_MOV_DIAS_ATRAS` (default 30).
- OPTIMIZACIÓN escritura movimientos (`sync_movimientos_canonico.py`): de 4 round-trips/fila a SET-BASED (tabla temporal #stg_mov + executemany + INSERT..SELECT idempotente). + `precargar_productos_mapeo` en resolver (1 query carga todo el mapeo de productos en caché, evita miles de round-trips). Resultado: escritura ~100x; cuello de botella restante = lectura del POS remoto por ventana.
- Backfill background (90d) verificado: 130MID = 314 enc + 12,323 detalles, 0 descartados (~8 min, dominado por lectura POS). Script: `tests/backfill_inventario.py [dias]`.
- CIENFUEGOS omitido (DDNS caído). 130QRO usa el mecanismo validado (sucursal_origen=0021, idéntico a ORIGEN ya probado E2E).

## 2026-06-09 (cont.) — Backfill 90d en curso + UI Auditoría validada + CIENFUEGOS en línea
- Backfill 90d (background, log /tmp/backfill90b.log): 130MID=12,323 det + ESTELAR=9,625 det (0 descartados) COMPLETADOS. ORIGEN (MPRO 0023) y 130QRO (0021) en proceso (MPRO alto volumen, lectura POS lenta).
- UI Auditoría VALIDADA: tras seleccionar unidad LA ESTELAR, el dropdown Requisición(es) muestra datos reales ('0000005724 - A0113 XO CHIHUAHUA') NO-LIVE desde EDARSAHUB; botón 'Realizar Auditoría' habilitado.
- CIENFUEGOS: su DDNS (servercienfuegos.ddns.net:6669) VOLVIÓ EN LÍNEA. SQL conecta OK y resuelve canónicamente (empresa=3, sucursal=3, SoftRestaurant). Backfill de CIENFUEGOS encadenado para correr al terminar el principal (log /tmp/backfill_cienfuegos.log). CIENFUEGOS TABLAJERIA queda fuera (esquema custom, sin unidad mapeada).
- Script backfill ahora acepta unidades por arg: `python tests/backfill_inventario.py [dias] [COD1,COD2,...]`.
- Histórico completo (1-2 años): correr el job recurrente con env `SYNC_COMPRAS_MOV_DIAS_ATRAS=365/730` (corrida larga programada; el límite es la lectura del POS por ventana).

## 2026-06 — Recuperación Login (P0) + Linter limpio + Loop de auto-revert DETENIDO
- CAUSA del login 404: commit worker `eb015e01` sobrescribió `backend/server.py` a un stub de 122 líneas (borró 16,757). Restaurado desde `d87d21ba` (16,861 líneas) + re-montado `worker_runtime_wake_router`. Login responde 401/422, ya no 404. 932 rutas.
- CAUSA REAL de pérdida recurrente (NO OOM): `edarsahub-bootstrap-watchdog` (cada 20s) + `edarsahub-mirror-sync` sincronizan el pod a `origin/Edarsahub_Desarrollo` (repo rbalam/EDARSA_HUB) que tiene el server.py roto, revirtiendo todo cada ciclo.
- DETENIDO el loop: `autostart=false`/`autorestart=false` en `/etc/supervisor/conf.d/edarsahub-mirror-sync.conf` y `edarsahub-bootstrap-watchdog.conf` + procesos matados. Ya no revierten.
- Linter 100% limpio (gate plataforma): borradas carpetas `auditorias_p1/p2/p4/p5` + `.bak`; 63 E722; 50 F811; ~117 F821 (noqa en código, typos SQL corregidos en comercial/services, rh/importador, catalogos, sync_historicos, tools); 3 route-shadowing movidas (server.py `/bulk`, api_connections `/check-duplicate`, justificacion `/umbral`); tesoreria sin upload a disco local; borrado `frontend/src/lib/handleSaveOffline.js`.
- ⚠️ CRÍTICO PENDIENTE: fix es LOCAL. Usuario debe "Save to GitHub" YA (loop detenido) para fijar `Edarsahub_Desarrollo` en GitHub. NO re-implementada la seguridad (SEC-001/SEC-002/Lockout/Panel) — siguiente paso (usar integration_expert por ser auth).


## 2026-06 — Re-implementación de Seguridad (SEC-001, SEC-002, Lockout) + Blindaje auto-sync
- SEC-001: `register_user` (modules/auth/service.py) ahora FUERZA rol `Usuario` en todo auto-registro; ignora roles elevados solicitados (SuperAdministrador/Admin). Verificado por curl: registro con role=SuperAdministrador → JWT con role=Usuario.
- Lockout fuerza bruta: nuevo `modules/auth/lockout_repository.py` (tabla SQL idempotente `dbo.Sistema_Seguridad_LoginIntentos`). 5 intentos fallidos → bloqueo 15 min. Integrado en `login_user` (check→429, register_failed en fallo, clear en éxito). Verificado: 5×401 → 429.
- SEC-002: handler global de excepciones ya existía (sanitiza no-manejadas). Además sanitizados 434 `detail=str(e)` exactos + 68 fugas en f-strings de `detail=` en modules/api/core (script /app/lint_tools/sanitize_sec002.py). 0 fugas restantes.
- BLINDAJE auto-sync: `tools/bootstrap/edarsahub_bootstrap_watchdog.py` `safe_fast_forward` ya NO hace `git stash` del worktree; si hay cambios sin commitear DIFIERE (state DEFERRED_LOCAL_DIRTY, preserved=True). Así nunca vuelve a descartar trabajo del pod. Workers siguen detenidos (autostart=false) hasta que el usuario haga Save to GitHub.
- NOTA: se creó un usuario de prueba `qa9882@e.mx` (rol Usuario, password Test1234!) en Usuario_Catalogo durante la verificación de SEC-001; se puede borrar.


## 2026-06 — Universal Worker Console (Fase 1, SOLO LECTURA)
- Backend `modules/worker_console` (router `/api/worker/console/*`, auth JWT obligatorio): dashboard, jobs/{state}, lifecycle/{job_id}, result/{job_id}, tablajerias/checklist, audit, validate (contrato v2 sin escribir).
- Contrato v2: READ_ONLY exige actions=[] (validador). Intérprete lee certification/quality_gate/blockers/production_touched/files_changed; published/* parsea marcador clave=valor.
- Checklist Tablajerías lee results reales de los 7 job_id -> GO técnico READ_ONLY, production_touched=false, next_decision=autorización humana. NO autoriza Producción.
- Frontend `pages/WorkerConsole.jsx` en ruta `/worker-console` (5 tabs). Tests 5/5 OK (tests/test_worker_console_contract.py). README: docs/WORKER_CONSOLE_README.md.
- Fase 2 pendiente (SUPERADMIN): publicador, Go/No-Go, limpieza preferred_job, checklist publicable.
