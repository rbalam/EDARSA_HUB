# EDARSA HUB - CRM COMERCIAL ENTERPRISE
## Product Requirements Document

### Original Problem Statement
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB.

### Core Requirements
- **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido
- **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad productiva
- **MÁXIMA DE ORO**: NO DUPLICAR tablas, conexiones, filtros, flujos, usuarios, ni unidades de negocio

### User's Preferred Language
Spanish (Español)

### Estado (2026-06 · fork) — Destinatarios de alertas por USUARIO + RBAC (NO-HARDCODE)
- ✅ **Números modelados como datos del usuario** (`dbo.Usuario_Catalogo`), no en código ni listas sueltas:
  Ricardo Balam (UsuarioID 8) → `Celular` = número personal, `Telefono` = número empresarial EDARSA.
- ✅ **Rol-tag RBAC `ALERTAS_CRITICAS_RECIBIR`** creado en `dbo.Usuario_Roles` (RolID 42) y asignado SOLO a
  Ricardo vía `Usuario_RolesAsignacion` (evita notificar a los 4 SUPERADMIN). El rol NO otorga permisos de
  acceso; es solo etiqueta para resolver destinatarios. Código de rol configurable en `.env`
  (`ALERTAS_RECIPIENTS_ROLE`).
- ✅ **`recipients_manager.get_email_recipients()` / `get_whatsapp_recipients()` ahora resuelven la UNIÓN**
  deduplicada de: (1) lista canónica `Sistema_AlertasDestinatarios` [CONSERVADA por decisión del usuario] +
  (2) usuarios activos con el rol (Email / Celular + Telefono) + (3) respaldo `.env ALERT_*_TO`. Verificado:
  2 correos (ricardo@, carlosruz@) y 2 WhatsApp deduplicados.
- ✅ Todo el notificador (excepciones + resumen diario + prueba) hereda esta resolución automáticamente.
- ⚠️ **Twilio sigue en 401** (`AUTH_ERROR`): el `TWILIO_AUTH_TOKEN` presente es inválido. El dueño rotará el
  token desde Twilio Console. Hasta entonces WhatsApp no envía; **el correo sí funciona**.
- Nota arquitectura: existen 2 capas de roles — `Usuario_Roles` (int, usada por `Usuario_RolesAsignacion` y
  la vista `vw_Usuario_RolesContexto_Efectivo`) y `Sistema_RBAC_Roles` (GUID). El rol-tag vive en la primera.


### 📋 BACKLOG (pendiente, no implementado)
### Estado actualizado (2026-06-13) — Cuentas por Pagar 100% canónico (NO-LIVE) + job en scheduler
- ✅ **Causa raíz "información demo"**: el worker de subprocess SQL fallaba con `ModuleNotFoundError: core`
  (faltaba `PYTHONPATH` en el subprocess) → toda consulta a CxP en vivo fallaba y caía a DEMO.
  **FIX** en `modules/finanzas/sql_subprocess_helper.py`: se inyecta `PYTHONPATH=/app/backend` al env
  del subprocess (aplica a TODOS los workers de finanzas).
- ✅ **Tabla canónica `dbo.Finanzas_CxP_Sync`** (migración `cxp_sync_canonico_20260613.py`) poblada por el
  **job `core/scheduler/jobs/cxp_sync_job.py`** desde SoftRestaurant (CIENFUEGOS/ESTELAR/130MID) + MPRO
  (ORIGEN=0023/130QRO=0021, mapeo canónico desde `Unidades_Negocio`, sin hardcode; sucursales MPRO no
  canónicas se omiten). Refresh idempotente con **guard anti-borrado** (no vacía si la extracción falla).
- ✅ **Job registrado en el scheduler** (`sync_cxp_facturas`, cron 04:30 diario) + ejecución manual
  (`POST /api/v2/scheduler/jobs/sync_cxp_facturas/run`) + bitácora. CLI: `scripts/sync_cxp_canonico.py`.
- ✅ **Endpoints CxP reescritos a NO-LIVE** (lectura exclusiva de la canónica, demo eliminado):
  `/cuentas-por-pagar` (agrupado A/B/X con detalle de facturas), `/resumen` (antigüedad), `/proveedores`,
  `/sucursales`. **Filtro de unidad arreglado** (front mapea GUID→código canónico; backend filtra por código/nombre).
- **Verificado por cURL** (admin@edarsa.com): CIENFUEGOS=368 facturas $5.04M; 5 unidades, $37.9M total;
  aging ORIGEN correcto; corrida vía scheduler repuebla las 5 unidades. ⚠️ Validación VISUAL pendiente
  del usuario (ricardo@edarsa.com.mx). Datos = 2,803 facturas reales, CERO demo.


### 📋 BACKLOG (pendiente, no implementado)
- **🟡 Escalar el ENRIQUECIDO (tipo de servicio + pagos por ticket) a las 5 unidades × 24 meses.**
  Pilotos ESTELAR y ORIGEN (mayo-2026) ya cargados y validados. El escalado completo (2024-06 →
  2026-06) está LISTO en `scripts/escalar_enrich_5u_24m.py` pero **NO ejecutado** por decisión del
  usuario (queda pendiente de su autorización explícita para correrlo). ESTADO: PENDIENTE / BACKLOG.

- **🔴 Handlers REALES de re-sync por tipo (lo más valioso):** cablear los handlers reales de
  Detalle de Ventas, Productos, Proveedores, Filtros, Requisiciones e Inventarios Físicos a sus
  fuentes/scripts reales, para que "Ejecutar" funcione en TODOS los tipos del catálogo (hoy solo
  `comercial_ventas_cerradas` ejecuta de verdad; el resto devuelve "Disponible próximamente").
  Al implementarse, marcar `HandlerImplementado=1` en `dbo.Sistema_Sync_Catalogo`. ESTADO: PENDIENTE.
- **🟡 Pantalla de edición del catálogo de sincronizaciones:** UI para crear/editar tipos, grupos y
  dependencias (obligatorias vs sugeridas) y orden. El backend CRUD ya está listo
  (`/resync/catalogo` POST/PUT/PATCH). Futuro: orden y dependencias arrastrables. ESTADO: PENDIENTE.
- **🧭 NAVEGACIÓN — Enlazar pantallas huérfanas al menú Enterprise (auditoría 2026-06-12):**
  rutas que existen en `App.js` pero NO son accesibles desde el menú Enterprise (solo por URL o
  desde el menú LEGACY de `Layout.js`). PENDIENTE decidir cuáles enlazar y en qué grupo:
    - `/admin/dba-credential` (DBA Diagnóstico)
    - `/importador-rh` (Importador de RH)
    - `/produccion` (el Enterprise usa `/tablajeria`)
    - `/admin/dashboard-ejecutivo` (posible duplicado de `/tablero-ejecutivo` → revisar si retirar o enlazar)
    - `/admin/centro-excepciones`
    - `/operativo`
    - `/proveedores` (interno, distinto del portal externo `/portal-proveedores`)
  ESTADO: PENDIENTE (decisión del usuario por cada una).
- **🧭 NAVEGACIÓN — Consolidar menús (retirar el legacy de `Layout.js`):** hoy conviven DOS menús
  (el Enterprise activo `EnterpriseSidebarMenu.jsx` + el legacy en `Layout.js`). Consolidar todo en
  el Enterprise y retirar el legacy para evitar pantallas "perdidas" y centralizar el mantenimiento
  del menú en un solo lugar. ESTADO: PENDIENTE.
- **CTA inteligente del semáforo (Benchmark Sectorial):** que el botón "Ajustar en Análisis IA"
  abra el tab Análisis IA **precargando la categoría/producto detectado como "Caro" u "Oportunidad"**,
  para pasar del diagnóstico sectorial a la sugerencia de precio con un clic (sin volver a buscar el
  producto). Solicitado por el usuario el 2026-06-11. ESTADO: PENDIENTE.
- **🔴 A) Migración NO-LIVE de `POST /api/compras/productos-para-captura` (DIFERIDA, autorizada 2026-06-12):**
  hoy el endpoint conecta EN VIVO al POS (viola NO-LIVE). Migrarlo a leer de tablas sync de EDARSAHUB.
  BLOQUEANTE: las tablas de DETALLE de compras/requisiciones (líneas) están VACÍAS (solo encabezados se
  sincronizan). Requiere primero poblar/crear el job de sync de detalle. El usuario eligió desbloqueo
  pragmático (B) ahora; A queda como siguiente incremento. ESTADO: PENDIENTE.

### Estado actualizado (2026-06-13) — Reportes ISCAM: agrupación + rango mes-año + exportación
- ✅ **Agrupación por Año / Mes / Día + "Sin agrupar"** en los reportes ISCAM (backend `group_by` en
  `iscam_routes.py`, todo NO-LIVE desde Sync_Sales / Finanzas_CortesCaja[_DetallePagos]):
  - Ventas por Periodo (Año/Mes), Resumen de Cuentas (Año/Mes/Día/Sin agrupar), Comandas
    (Año/Mes/Día/Sin agrupar), Pagos por Ticket (Año/Mes/Día con desglose por forma de pago / Sin agrupar).
  - Drills (`/productos`, `/tickets`, `/tipos-servicio`) ahora reciben `group_by` para que el drill por
    Año/Mes/Día matchee el periodo correcto.
- ✅ **Selector de periodo por RANGO mes-año** (Desde mes/año → Hasta mes/año) en el frontend; default
  últimos 12 meses. Reemplaza los date-pickers Desde/Hasta.
- ✅ **Exportación a Excel y PDF** en todos los reportes (client-side, exporta la vista actual con la
  agrupación activa), reutilizando el util canónico `portal-inteligencia/utils/exportUtils.js`.
- 📁 Frontend reescrito: `portal-inteligencia/pages/ReportesISCAMPage.jsx` (toolbar de controles,
  `GenericTable` para vistas agrupadas, tablas custom + drills para "Sin agrupar", botones export).
- **Verificado por cURL** (5 reportes × modos de agrupación + detalle, ej. periodos/anio → 2026
  $14.69M / 2025 $11.38M; pagos-ticket/mes con desglose por forma) y **pytest 6/6**. Frontend compila
  sin errores. ⚠️ Verificación VISUAL del portal pendiente del usuario (login automatizado bloqueado
  por reset de sessionStorage del preview — limitación conocida del entorno).


### Estado actualizado (2026-06-13) — Enriquecido por TICKET (tipo de servicio + formas de pago)
- ✅ **Job de sync ENRIQUECIDO** para poblar, por ticket, desde el POS (SOLO LECTURA, NO-LIVE en
  pantallas), 100% canónico y sin hardcode:
  - **(a) Tipo de servicio → `dbo.Sync_Sales`** (columnas nuevas `TipoServicioID`/`TipoServicio`).
    Fuentes: SoftRestaurant `cheques.tipodeservicio` (+catálogo `tiposervicio`); MPRO `Comanda.Co_Tipo`.
  - **(b) Formas de pago por ticket → `dbo.Finanzas_CortesCaja_DetallePagos`** (tabla canónica
    existente, antes VACÍA/sin uso; se le agregaron columnas de enlace `UnidadNegocio/NumeroTicket/
    FechaHora/Propina` y se hizo `CorteCajaID` NULLABLE). Fuentes: SoftRestaurant `chequespagos`+
    `formasdepago`; MPRO `Comanda_Pago`+`Forma_Pago` (enlace `Co_Folio=Vn_Folio`, verificado).
  - **Migración** idempotente `migrations/enrich_tiposervicio_detallepagos_20260613.py` (+índices
    `IX_DetallePagos_Unidad_Ticket/_Fecha`, `IX_SyncSales_Unidad_Ticket`).
  - **Módulo** `core/scheduler/jobs/inteligencia_comercial_enrich.py` (`enrich_unidad`, idempotente
    por DELETE+INSERT del rango; inserts multi-fila por performance). Integrado al loop del job
    `inteligencia_comercial_sync_job` (paso 4, no-fatal) + bitácora `Sistema_SyncPOS_Bitacora`
    (eventos ENRICH visibles en el Monitor/Scheduler). CLI `scripts/pilot_enrich_tiposervicio_pagos.py`
    (soporta `--dry-run`).
  - **Piloto autorizado (1 unidad × 1 mes) cargado y validado:** ESTELAR mayo-2026 (1,881 tickets,
    2,460 pagos, $2,924,063; idempotente en re-run) y ORIGEN/MPRO mayo-2026 (1,057 tickets, 1,175
    pagos, $2,448,971). KPIs canónicos NO tocados.
  - **Consumo ISCAM (NO-LIVE):** 2 endpoints nuevos en `iscam_routes.py`:
    `GET /inteligencia/iscam/formas-pago/por-ticket` (resumen por forma + detalle por pago, desde
    DetallePagos) y `GET /inteligencia/iscam/ventas-periodos/tipos-servicio` (desglose del Reporte 1
    desde Sync_Sales). Frontend `ReportesISCAMPage.jsx`: nueva sub-pestaña **"Pagos por Ticket"** y
    drill por DOBLE CLIC en la columna Cheques → tipo de servicio. Scoping por unidad intacto (403 en
    unidad ajena, verificado).
  - **Verificado por cURL + python -c + pytest** (`tests/test_enrich_tiposervicio_pagos.py`, 6/6).
    SIN testing_agent. ⚠️ Verificación VISUAL del frontend pendiente del usuario (el screenshot
    automatizado del portal externo sigue bloqueado por el reset de sessionStorage del preview).
  - ⏳ **PENDIENTE (escalar):** correr el enriquecido para las 5 unidades × 24 meses (autorización del
    usuario para el escalado, igual que el backfill de Sync_Sales).


### Estado actualizado (2026-06-12) — Reportes ISCAM (Portal Inteligencia)
- ✅ **Menú "Reportes ISCAM"** agregado al Portal de Inteligencia Comercial, 100% sobre tablas
  CANÓNICAS (NO-LIVE, sin hardcode, SIN DUPLICAR — reutiliza tablas existentes):
  - **Fuentes:** `dbo.Sync_Sales` (112k tickets, encabezado + `items` JSON de productos) y
    `dbo.Finanzas_CortesCaja` (formas de cobro: efectivo/tarjeta/amex/vales/otros/propinas/comisiones)
    — esta última REUTILIZADA del módulo Finanzas por indicación del usuario (no recrear).
  - **Backend** `modules/inteligencia_comercial/iscam_routes.py` (`iscam_router`, prefix
    `/api/inteligencia/iscam`, montado con `intel_portal_guard` → scoping por unidad para externos):
      1. `/ventas-periodos` (12 periodos) + drill `/productos` + drill `/tickets`
      2. `/cuentas` (resumen) + drill `/cuentas/detalle`
      3. `/comandas` (OPENJSON sobre items)
      4. `/formas-pago` (desde Finanzas_CortesCaja, con totales y efectivo)
  - **Índices canónicos** creados para performance: `IX_SyncSales_Unidad_Fecha`,
    `IX_CortesCaja_Unidad_Fecha` (report 1 pasó de 26s → 0.6s).
  - **Frontend** `portal-inteligencia/pages/ReportesISCAMPage.jsx`: 4 sub-pestañas, tablas con tema
    oscuro, **drill-down por DOBLE CLIC** (periodo→productos→tickets; cuenta→productos), filtros de
    fecha, fila de TOTALES en formas de pago. Verificado por cURL + screenshots (login externo →
    ESTELAR → tabla + drill OK). Sin testing_agent.
  - ⚠️ **PENDIENTE (enriquecer sync, opción b del usuario):** desglose por TIPO DE SERVICIO
    (Comedor/Domicilio/Rápido) del Reporte 1 y formas de pago A NIVEL TICKET (tabla canónica
    `dbo.Finanzas_CortesCaja_DetallePagos` existe pero está VACÍA) no están sincronizados todavía.
    Hoy formas de pago es a nivel CORTE (turno/caja), que es la granularidad canónica disponible.

### Estado actualizado (2026-06-12) — Portal Inteligencia Comercial EXTERNO (login propio + scoping)
- ✅ **Feature: Portal de Inteligencia Comercial como portal EXTERNO** (como Proveedores), priorizado por
  el usuario. Antes solo accedían usuarios internos del CRM. Ahora:
  - **Backend (100% SQL, NO-Mongo)**: tabla canónica `dbo.Portal_Inteligencia_Usuarios`
    (migración `migrations/portal_intel_usuarios_20260612.py`) con usuarios externos (email, bcrypt,
    `UnidadesAsignadas` JSON, activo). Nuevo router `routes/portal_inteligencia.py`:
    auth propia (cookie httpOnly `edarsa_intel_access_token`, JWT type `portal_intel`, bcrypt passlib)
    + endpoints admin CRUD (`/api/portal-intel/admin/usuarios`, protegidos por admin CRM).
  - **Guard DUAL** `intel_portal_guard` aplicado al router `/api/inteligencia/*`: acepta usuario INTERNO
    del CRM (acceso completo) O EXTERNO del portal (restringido a sus unidades). Para externos exige
    `unidad` ∈ asignadas (bloquea "todas" y unidades ajenas con 403). `/inteligencia/unidades` devuelve
    solo las unidades del externo. NOTA: esto cerró un hueco — los endpoints de inteligencia ahora
    exigen sesión (antes estaban abiertos).
  - **Frontend**: login externo propio (`portal-inteligencia/pages/LoginInteligencia.jsx`), cliente API
    dedicado (cookie + Bearer, sin redirección al CRM), `App.jsx` con sesión DUAL, dropdown de unidades
    acotado (sin "Todas" para externos), oculta vista "Clasificación (admin)". Admin de usuarios externos
    integrada como pestaña **"Usuarios Inteligencia"** en la pantalla de Proveedores
    (`pages/UsuariosInteligencia.jsx`): CRUD + asignación de unidades con checkboxes.
  - **Verificado** (cURL + screenshots, sin testing_agent): login externo OK, scoping de unidades
    (solo asignadas), 403 en unidad ajena/"todas", 401 sin sesión, admin CRUD operativo, coexiste con
    acceso interno. Credenciales de prueba creadas: socio@externo.com / socio123 (ORIGEN, LA ESTELAR).
  - ⏳ **Subdominio propio** (ej. inteligencia.edarsa.com.mx): pendiente, se gestiona con Soporte Emergent.

### Estado actualizado (2026-06-12) — Catálogo Canónico de Sincronizaciones (agrupación + dependencias)
- ✅ **Feature: sincronizaciones agrupadas con ejecución grupo/individual + sugerencia por dependencias.**
  Solicitado por el usuario. Antes el panel Re-sync exponía UN solo tipo hardcodeado.
  - **Catálogo canónico SQL (NO hardcode):** nueva tabla `dbo.Sistema_Sync_Catalogo`
    (migración `migrations/sync_catalogo_canonico_20260612.py`, idempotente). Campos: Codigo, Nombre,
    Grupo, Descripcion, Orden, NivelRiesgo, PermiteResync/DryRun, Requiere Unidad/RangoFechas,
    RangoMaxDias, Handler, **HandlerImplementado**, TablaDestino, **Dependencias (JSON
    [{codigo,obligatoria}])**, Activo. Seed: 7 tipos en 3 grupos → Comercial (Detalle de Ventas,
    Ventas Cerradas), Catálogos (Productos, Proveedores, Filtros), Inventarios (Requisiciones,
    Inventarios Físicos). Dependencias derivadas por el agente (opcionales/sugeridas).
  - **Servicio** `modules/sistema/sync_catalogo_service.py`: get_catalogo/_agrupado, CRUD
    (crear/actualizar/toggle), y `resolver_dependencias()` (expansión recursiva + orden topológico).
  - **API** (en `api/admin_scheduler_resync.py`): `GET /resync/catalogo`, `POST/PUT/PATCH /resync/catalogo`
    (CRUD, perm SCHEDULER_ADMIN), `POST /resync/resolve`. `/resync/options` ahora devuelve `grupos`.
    `_get_tipo_sync_config` lee del catálogo. **Guard honesto:** tipos sin handler real
    (HandlerImplementado=0) NO se simulan ni ejecutan (DRY RUN y REAL devuelven "Disponible
    próximamente" + bitácora HANDLER_NO_IMPLEMENTADO). Solo `comercial_ventas_cerradas` ejecuta real.
  - **Frontend** `components/admin/ResyncPanel.jsx` (reescrito): selección agrupada por checkbox
    (individual o "seleccionar grupo"), badges de dependencias y "Handler pendiente". Al ejecutar:
    llama `/resync/resolve` → **comportamiento (b)**: agrega dependencias automáticamente y abre
    diálogo de confirmación con el conjunto ORDENADO; el usuario puede des-seleccionar las opcionales
    (las obligatorias quedan bloqueadas). Ejecuta el conjunto en orden (DRY RUN/REAL) mostrando
    resultados por tipo. Verificado por cURL + screenshots (panel y resolve OK). NO se usó testing_agent.
  - ⚠️ **PENDIENTE (handlers reales):** Detalle de Ventas, Productos, Proveedores, Filtros,
    Requisiciones e Inventarios Físicos están en el catálogo pero su handler de re-sync aún NO está
    implementado (sin mock). Cablearlos a sus fuentes/scripts reales es el siguiente incremento.
  - ⚠️ **PENDIENTE (UI):** editor visual del catálogo (crear/editar tipos, grupos y dependencias).
    El backend CRUD ya está listo; falta la pantalla de configuración.

### Estado actualizado (2026-06-12) — Navegación: sincronizaciones accesibles
- ✅ **Enlaces de menú a sincronizaciones/scheduler arreglados (opción C):** las pantallas de
  sincronización existían pero no eran accesibles desde el menú Enterprise. Fix en
  `config/enterpriseMenuConfig.js` (grupo Administración/Sistema → sección Automatización):
  (1) item **"Programación"**: ruta corregida `/programacion` (rota) → `/scheduler` (real) y
  removido `comingSoon` (estaba deshabilitado). Abre `Scheduler.jsx` = "Scheduler del Sistema"
  con jobs programados (SYNC Comercial V2, SLA Processor, Auditorías Scheduler, etc.) + pestaña
  Re-sync Manual. (2) Nuevo item **"Monitor de Sincronización"** → `/admin/sync-monitor`
  (`SyncMonitor.js`): estado de syncs por servidor, tipos, errores 24h, actividad. Icono
  `RefreshCw` agregado al import y al mapa `ICONS` de `EnterpriseSidebarMenu.jsx`. Verificado por
  screenshot: ambas rutas renderizan con sesión admin. Aclaración al usuario: el menú
  "Automatizaciones" (`/automatizaciones`) es solo para automatizaciones operativas de Compras y
  auditorías de inventario programadas (NO para sincronizaciones de catálogos).
- 📝 **AUDITORÍA de pantallas huérfanas (rutas en App.js NO accesibles desde el menú Enterprise):**
  Arregladas: `/scheduler`, `/admin/sync-monitor`. Pendientes (solo accesibles por URL o desde el
  menú LEGACY de `Layout.js`, no del Enterprise): `/admin/dba-credential` (DBA Diagnóstico),
  `/importador-rh`, `/produccion` (Enterprise usa `/tablajeria`), `/admin/dashboard-ejecutivo`
  (posible duplicado de `/tablero-ejecutivo`), `/admin/centro-excepciones`, `/operativo`,
  `/proveedores` (interno, distinto del portal externo). PENDIENTE decisión del usuario si quiere
  enlazar alguna de estas. el sistema
  reventaba con `Uncaught runtime error: Cannot access 'getCostoSegunUnidad' before initialization`
  y expulsaba al login. Causa raíz (TDZ / temporal dead zone): el `useMemo` `auditoriaExport`
  (Compras.js) invocaba `getCostoSegunUnidad(r)` dentro del `.map(resultados)`, pero la función
  estaba declarada como `const` MÁS ABAJO en el mismo componente. En el render inicial `resultados`
  está vacío → no se llama → no crashea; al correr la auditoría `resultados` se puebla → el map la
  invoca antes de su inicialización → ReferenceError → error boundary → logout. Fix: `getCostoSegunUnidad`
  movido ANTES del useMemo como `useCallback([unidadAnalisis])` y agregado a las deps del useMemo;
  eliminada la definición original duplicada. Frontend compila limpio (sin el warning previo de deps),
  smoke E2E sin runtime error. el error
  "Error al obtener productos de las requisiciones" se debía a **timeout** del cliente axios.
  Diagnóstico (cURL, sin testing_agent): el endpoint `POST /api/compras/productos-para-captura`
  responde 200 en ~0.5s (warm) con `server_id` (código o GUID) para CIENFUEGOS, pero la llamada
  del frontend usaba el timeout default de 15s mientras sus hermanas en vivo (`pedidos-vigentes`,
  `inventarios-fisicos`) usan 30s — el POS en vivo es lento/variable → en navegador excedía 15s →
  `catch` → alert. Fix en `frontend/src/pages/Compras.js` (`iniciarCapturaManual`): ambas llamadas
  a `productos-para-captura` ahora usan `{ timeout: 30000 }` + mensaje honesto si es timeout.
  NOTA: la requisición del screenshot (00000031014) venía de localStorage (pedidos-vigentes ya es
  NO-LIVE y devuelve 0 para CIENFUEGOS). Frontend compila limpio. Migración NO-LIVE = backlog A.

### Estado actualizado (2026-06-11)
- ✅ **Semáforo de oportunidad de precio (mejora sobre Benchmark Sectorial):** `vista_vs_sector`
  ahora clasifica cada categoría comparable con umbral configurable (`umbral_pct`, default 15):
  CARO (>+umbral, rojo), BARATO/oportunidad↑ (<-umbral, verde), ALINEADO. Devuelve resumen
  `oportunidades{caro,barato,alineado}` + `accion_sugerida`. Frontend: columna "Oportunidad" con
  semáforo, barra resumen y CTA "Ajustar en Análisis IA" (→ tab `analisis`). Verificado por cURL
  (ALIMENTOS→BARATO, BEBIDAS→CARO). pytest puro en `tests/test_benchmark_sectorial.py` (5/5).
- ✅ **C1 — Eliminado `server_id` del módulo Pricing IA (`routes_pricing_ai.py`):**
  `server_id` ahora es OPCIONAL/legacy en los 3 modelos (AnalizarProducto/SugerirComparables/
  GenerarJustificacion); se resuelve canónicamente desde `empresa_id`(+`unidad_negocio_pk`) con
  nuevo `modules/comercial/services/unidad_resolver.resolver_server_id` (vía
  `Sistema_EmpresasServidores`, RolConexion='PRINCIPAL_SQL'; graceful→None→HTTP 400). Cliente usa
  filtros canónicos; sin GUID. Backward-compat: si se manda server_id explícito, también funciona.
  **Bugs latentes preexistentes corregidos (f-strings con variable mal nombrada que provocaban
  NameError/TypeError y rompían el módulo):**
    - `pricing_ai_service.py`: `_guardar_analisis_ia` (`{ServerID}/{EmpresaID}/{UnidadNegocioID}`→snake),
      prompt sugerir-comparables (`:.2f if...`), prompt generar-justificacion (`margen_propuesto` None).
    - `perfil_unidad_service.py`, `benchmark_service.py`, `competidores_service.py`,
      `competidores_enterprise_service.py`, `impuestos_service.py`, `precios_vinos_service.py`,
      `pricing_sugerido_service.py`: `{ServerID}/{UnidadNegocioID}/{EmpresaID}/{SucursalID}`→snake_case.
  **Verificado por cURL:** los 4 endpoints pricing-ai (analizar-producto/sugerir-comparables/
  generar-justificacion/analizar-benchmark) responden 200 success SIN server_id (GPT-5.2 real).
  Regresión 200: benchmark/resumen, benchmark/estado-preparacion, competidores, perfil-unidad,
  dashboard/metricas, dashboard/estadisticas-competidores. Sin MongoDB, sin hardcode.

### Estado actualizado (2026-06-11) — Sesión previa (RBAC + Benchmark Sectorial)
- ✅ **P2 RBAC permisos `comercial.*` sembrados (benchmark/competidores/perfil/precios):**
  Causa: los endpoints de Pricing IA/Benchmark usan permisos con formato punto/minúsculas
  (`comercial.benchmark.ver`), pero el motor RBAC (`core/rbac/repository_sql.py`) sólo generaba
  el formato legacy `{Modulo}_{Accion}` y NO existían módulos `comercial.*` ni las acciones
  `INACTIVAR/VALIDAR/VER_IA/GENERAR`. Sólo admin (bypass) podía entrar. Fix:
  (1) Parche **aditivo** en `repository_sql.py` (`get_all_roles` + `get_roles_usuario`) para emitir
  también `{Modulo}.{accion_lower}` sin romper el formato legacy.
  (2) Script idempotente `scripts/create_comercial_pricing_rbac.py`: crea 4 acciones, 5 módulos
  `comercial.*` y 82 permisos por rol (SUPERADMIN/ADMIN/ADMIN_COMERCIAL/DIRECCION/GERENTE_UNIDAD/
  CONFIGURADOR_COMERCIAL/ANALISTA_COMERCIAL/VISOR_COMERCIAL/GERENCIA/AUDITOR).
  Verificado e2e por cURL con usuario NO-admin `VISOR_COMERCIAL` (qa.visorcomercial@edarsa.com):
  200 en benchmark/competidores (.ver), 403 en validar/crear. Regresión OK (tablero ejecutivo 200).
- ✅ **P2 Benchmark Sectorial — Incremento 1 (reporte backend + tab frontend):**
  Backend `modules/comercial/services/benchmark_sectorial_service.py` + `routes_benchmark_sectorial.py`
  (RBAC `comercial.benchmark.ver`, NO-LIVE, deriva de tablas canónicas, sin hardcode). 4 endpoints:
  `/api/comercial/benchmark-sectorial/{sectores,vs-sector,interno,por-segmento}`. Puente de IDs:
  `Sistema_EmpresasServidores` (EmpresaID int → ServidorID GUID → `Sync_Productos.ServerID`) para
  nuestros precios; competencia desde `Comercial_CompetidoresMenuItems`+`Comercial_Competidores`
  (TipoRestaurante=giro, SegmentoPrecio=segmento). 3 vistas: vs sector / interno entre unidades /
  por segmento + métrica % desviación por categoría. Frontend tab `TabBenchmarkSectorial.jsx` en
  `PricingIA.jsx`. Verificado backend por cURL; frontend compila limpio (screenshot bloqueado por
  el reset de sessionStorage del preview en navegación automatizada). Estados honestos SIN_DATOS.
  **NOTA real de datos**: categorías propias (ALIMENTOS/BEBIDAS) no empatan con las del competidor
  (Carnes/Entradas) → 0 comparables hoy (mismatch de taxonomía + datos escasos). Aquí entra el
  Incremento 2 (ingesta).
- ⏳ **Pendiente Benchmark Sectorial — Incremento 2 (INGESTA):** alimentar datos de competencia/sector
  cuando faltan, vía adjunto (Excel/PDF/JPG/Word) o link. Requiere object storage + extracción
  (LLM). PENDIENTE confirmar integración con el usuario antes de construir.
  → **RESUELTO 2026-06-11 (ver abajo).**

- ✅ **P2 Benchmark Sectorial — Incremento 2 (INGESTA de competencia) COMPLETADO (2026-06-11):**
  - Tabla staging `Comercial_Ingesta_Competencia` (migración `migrations/comercial_ingesta_competencia_20260611.py`).
  - Object storage helper `core/object_storage.py` (Emergent, EMERGENT_LLM_KEY) — archiva TODO adjunto para auditoría; referencia en SQL (NO Mongo).
  - Servicio `modules/comercial/services/ingesta_competencia_service.py` + `routes_ingesta_competencia.py`.
  - Extracción: **Excel/CSV** = plantilla directa (openpyxl/csv); **PDF/imagen/Word/txt** = IA **gemini-2.5-flash** (emergentintegrations, FileContentWithMimeType / texto); **link** = scraping (requests+bs4) → IA.
  - Flujo: upload/link → archiva + extrae → staging PENDIENTE → **validación humana** (editar filas) → confirmar (inserta a `Comercial_Competidores` + `Comercial_CompetidoresMenuItems`, una o varias unidades vía CSV de EmpresaID) o rechazar.
  - RBAC: ver=`comercial.competidores.ver`, crear/confirmar=`comercial.competidores.crear` (ya sembrados).
  - Endpoints: `/api/comercial/ingesta-competencia/{,/upload,/link,/{id},/{id}/filas,/{id}/confirmar,/{id}/rechazar,/{id}/archivo,/plantilla}`.
  - Frontend: 4º sub-tab "Ingesta de Datos" en `TabBenchmarkSectorial.jsx` (`TabIngestaCompetencia.jsx`): subir/link/plantilla + preview editable + confirmar/rechazar + historial.
  - **Verificado e2e por cURL:** Excel (4 filas→2 competidores+4 items, archivado en object storage OK), IA Gemini (.txt→3 productos OK), editar filas OK, rechazar OK; el reporte sectorial toma los datos nuevos (comparables ALIMENTOS/BEBIDAS). Frontend compila limpio.
  - Deps añadidas: `python-docx`, `beautifulsoup4` (en requirements.txt vía pip freeze).
  - ⚠️ Screenshot automatizado del UI bloqueado por reset de sessionStorage del preview; pendiente verificación visual del usuario.

### Estado actualizado (2026-06-09)
- ✅ **Portal Inteligencia operativo SIN demo + datos 100% reales (P0):** (1) AUTH del portal migrada
  de cookie a token operativo Bearer (sessionStorage, fuente canónica `lib/api.js`); eliminado el modo
  demo (`Usuario Externo`/`Usuario Demo`/`demo@edarsa.com`); estados honestos SIN_SESION/SESION_EXPIRADA/
  SIN_PERMISO. Cliente único `portal-inteligencia/api/client.js`. (2) Eliminado TODO el mock: frontend
  (`FALLBACK_*`, `Math.random`, alcohol 35) y **backend** (`inteligencia_comercial/routes.py`: bloques
  horario 20/50/30, top_productos/casas/familias hardcodeados) reemplazados por agregados REALES desde
  `Comercial_Inteligencia_VentasDetalleProducto`. `casa` NULL → SIN_DATOS_SYNC honesto. Verificado cURL +
  screenshots (admin@edarsa.com). Doc: `memory/DIAGNOSTICO_PORTAL_INTELIGENCIA_AUTH_MOCK.md`.
  Pendiente (no regresión): seed permisos/unidades `comercial.benchmark.*`.

- ✅ **P2 TableroEjecutivo + RBAC string→SQL:** (1) Eliminadas las cifras de ventas hardcodeadas del fallback del Tablero Ejecutivo (backend caché estático $15.7M + frontend `FALLBACK_TABLERO_EJECUTIVO` que era código muerto); fallback honesto NO-LIVE (`fuente=SQL_NO_DISPONIBLE`, KPIs en 0, unidades canónicas desde `UnidadesService`). (2) Porteros admin/superadmin migrados a `es_admin`/`es_superadmin` en `core/security.py`, `core/rbac/middleware.py`, `costos_margenes/routes.py` y `routes_precios.py`. Verificado cURL + 5 tests + 19 regresión. Total comercial intacto.
- ✅ **Centralización modales de detalle + selector inventarios (P1):** 3 módulos canónicos compartidos entre Análisis y Auditoría.
- ✅ **Compras → contrato canónico `unidad` (P0):** helper central `canonical_server_id()` aplicado a los 9 endpoints de Compras. Acepta unidad (codigo/pk) + compatibilidad legacy `server_id`. NO-LIVE. Verificado cURL + 6 tests.
- ✅ **P0 Usuarios Activo/Inactivo:** corregido (todos aparecían "Inactivo" por mismatch `activo`/`active`; los inactivos no listaban; filas duplicadas). Dedup + campo `active` + `incluir_inactivos` + endpoint `PATCH /admin-sql/users/{id}/toggle-activo` (revoca sesiones al inactivar, bloquea auto-inactivación) + UI: checkbox "Mostrar inactivos" + botón Activar/Inactivar. Verificado E2E.
- ✅ **Catálogo canónico NO-LIVE (P0):** `report-filters` ya no consulta POS en vivo (MPRO de `Sync_Productos`, SR de `Sync_Catalogo_Filtros`).
- ✅ **Auto-refresh de sesión (P0):** corregido el auto-logout a 15 min.
- ⏳ **Siguiente (pedido por el usuario):** nivel Categoría en filtro de Costos y Márgenes; migrar tableros `server_id`→`unidad`; DashboardIA mock→`Sync_Sales`; export Auditoría Excel/PDF.

### Estado previo (2026-06-08)
- ✅ **Unificación canónica de tableros (P0):** contrato `unidad_codigo` → backend valida permiso y resuelve server_id/sucursal_origen_id (helper central `core/corporate_filters/request_resolver.py`). `server_id` deprecated (compat con warning). Operativo + Inventarios migrados. MPRO desambiguado (ORIGEN/QRO). Detalle en CHANGELOG 2026-06-08.
- ✅ **NO-LIVE puro en inventarios:** eliminado el fallback LIVE (PASO 2) en `obtener_inventarios_fisicos`. Única fuente EDARSAHUB_SYNC.
- ✅ **CERO MongoDB** verificado en todo el refactor.
- ⏳ **Siguiente incremento:** migrar `Reportes.js` (Análisis/Métricas) y TableroEjecutivo/DashboardIA al contrato `unidad` (hoy funcionan vía compatibilidad server_id, ya NO-LIVE).
- ⏳ Pendiente decisión usuario previa: (1) 130MID con `queries_configured=0`; (2) migrar Métricas SoftRestaurant a NO-LIVE.

---

## Architecture

### SQL-FIRST Architecture
- `core/sql_first/connection_factory.py` - Hub central para todas las conexiones SQL
- `core/sql_first/db.py` - Funciones base de conexión EDARSAHUB
- `core/db.py` - Wrapper de compatibilidad legacy (sin conexiones directas)
- `core/rbac_sql/service.py` - Servicio RBAC usando tablas canónicas

### Canonical SQL Tables
| Tabla | Propósito |
|-------|-----------|
| `Usuario_Catalogo` | Fuente única de usuarios (reemplaza Sys_Usuarios) |
| `Usuario_Roles` | Catálogo de roles |
| `Usuario_RolesAsignacion` | Asignación usuario-rol |
| `Usuario_EmpresasAsignacion` | Asignación usuario-empresa |
| `Usuario_SucursalesAsignacion` | Asignación usuario-sucursal |
| `Usuario_ServidoresAsignacion` | Asignación usuario-servidor |
| `Usuario_Modulos` | Catálogo de módulos para permisos |
| `Usuario_Acciones` | Catálogo de acciones RBAC |
| `Usuario_PermisosRolModulo` | Permisos rol-módulo-acción |
| `Sistema_Modulos` | Módulos del sistema (para menú) |
| `Sistema_ModulosMenus` | Menús por módulo |
| `Sistema_DeudaTecnica_TablasDuplicadas` | Registro de tablas obsoletas |

### Technical Debt (Tracked)
- `RBAC_Roles` - 6 rows (datos de transición)
- `RBAC_Permisos` - 9 rows (datos de transición)

---

## Implementation Status

### Phase P4 - SQL-FIRST Migration ✅ COMPLETE
- [x] P4-02: Centralización conexiones SQL
- [x] P4-03: Ajuste schema canónico
- [x] P4-04/05/06/07: Config segura y RBAC SQL
- [x] P4-09/09B: Aplicación Máxima de Oro, roles canónicos
- [x] P4-10/11/12: Validación contexto e integridad
- [x] P4-13: Backup colecciones Mongo candidatas
- [x] P4-14: Corrección huérfanos/duplicados (0 encontrados)
- [x] P4-15: Validación Mongo vs SQL (9 candidatas, 7 pendientes)
- [x] P4-16: Eliminación tablas RBAC_* vacías (6 eliminadas)
- [x] P4-17/17B: Dictamen Final APROBADO, core/db.py refactorizado

### P0-D - Una Sola Verdad Comercial ✅ COMPLETE (2026-06-XX)
Menú Comercial (`/api/comercial/tablero-ejecutivo`) devolvía $0. Causa raíz: `service.py`
filtraba la vista `vw_Comercial_KPIs_Diarios_v2_Runtime` por `unidad_negocio_pk` (que en la
vista es un GUID, NO el código) y forzaba `sucursal_id='DEFAULT'` (rompía 130QRO=0021 y
ORIGEN=0023). Fix quirúrgico en `_get_kpis_periodo_edarsahub` y el "portero" `query_ultimo_dia`
de `_obtener_kpis_tablero_desde_edarsahub`: filtro por `unidad_negocio_id` (texto canónico),
sin forzar `sucursal_id`, KPI = `ventas_sin_propina`. Los 3 módulos comerciales ahora cuadran
en **$1,573,660.81** (Junio 2026). Verificado vía cURL + SQL directo. Regresión:
`backend/tests/test_p0d_menu_comercial_filtro_canonico.py` (4 tests, estáticos). Script del
usuario AUDITADO y RECHAZADO (regex frágil que dejaba `sucursal_id` a medias, `yarn build`
innecesario, validación a endpoint inexistente `/api/inteligencia-comercial/resumen` sin JWT);
intención aplicada manualmente.

### Phase V1.0 - Estabilización Producción ✅ COMPLETE (2026-06-07)
Los 5 bloqueadores P0 del Dictamen cerrados y verificados (cURL/pytest, sin testing_agent):
- [x] P0-1: Vistas corruptas `vw_vw...Runtime` normalizadas (Tablero Ejecutivo + Comercial) → 200
- [x] P0-2: `rbac_helper.py` SQL-First async + 11 funciones module-level en `repository.py` + alcance SuperAdmin por CodigoRol → CRUD Usuarios/Roles 200
- [x] P0-3: Configuración Operativa cursor tupla-vs-dict (`_rows_dicts`/`_one_dict`) → 200
- [x] P0-4: Explorador BD `_execute_sql_direct_with_error` repuesto en `core/db.py` → 200
- [x] P0-5: Finanzas `/health` 502 → canónico NO-LIVE (externos opt-in) → 200/0.28s
- Detalle completo en CHANGELOG.md [2026-06-07] Fase 1.

### Phase P5 - MongoDB Sunset ✅ IN PROGRESS
- [x] P5-01: Backup controlado y eliminación de 9 colecciones Mongo
- [x] P5-02: Consolidación RBAC_Roles en Usuario_Roles
- [x] P5-05: Fix /auth/me token parsing
- [x] P5-06: Migración completa de usuarios Mongo a Usuario_Catalogo
- [x] P5-07: Cierre migración Auth SQL (AuthRepository creado, MongoDB fallback eliminado)
- [x] P5-10B: Menú 100% SQL canónico sin hardcodes (2026-06-06)
  - MenuService lee de Sistema_Modulos + Sistema_ModulosMenus
  - SUPERADMIN detectado por CodigoRol o NivelJerarquia >= 100
  - Frontend delegado al backend SQL
  - password_hash eliminado de respuestas API
- [x] P5-1 (2026-06-07): Sunset mínimo `comercial/historical_kpis_repository.py` — 3 funciones Mongo rotas neutralizadas a stubs + import huérfano `secret_manager` removido. Módulo era código muerto inerte (sin importadores). health/v1 → healthy.
- [ ] Eliminar 28 colecciones Mongo restantes (pendiente script usuario)
  - [x] (2026-06-07) RESPALDO COMPLETO NO destructivo realizado vía `mongodump` de las 5 bases locales (edarsa_hub=28, test_database=61, cab003=10, edarsahub=6, stock_tracker=2 → 107 colecciones, 3066 docs, 2.4MB). Ruta: `/app/backups/mongo_sunset_20260607_181350/`. Reporte: `REPORTE_RESPALDO_MONGO.md` + `MANIFEST_SHA256.json` (SHA256 por archivo + global). NADA borrado/desinstalado: pendiente decisión de borrado quirúrgico del usuario tras revisar el reporte.
  - [x] (2026-06-07) VALIDACIÓN POR MUESTREO DE LLAVES (Fase 6-ter, SOLO LECTURA): 27 colecciones CUBIERTA_PARCIALMENTE validadas doc-por-doc contra su tabla SQL (COUNT parametrizado). Veredicto duro: **6 CUBIERTA_CONFIRMADA** (toda la muestra hallada unívocamente → candidatas a borrado CON respaldo): `users`→Usuario_Catalogo, `inventarios_procesados_auto`→Inventarios_ProcesadosAuto (vía col MongoId), `portal_suppliers`→Portal_Proveedores (vía MongoId), `consultas_custom`→Sistema_ConsultasCustom, `sec_modulos_sistema`→Sistema_Modulos, `server_status`→Sistema_ServidoresEstado. **18 NO_CUBIERTA + 3 SIN_LLAVE** (NO borrar): destacan rbac_roles/sec_roles/roles/rbac_usuarios_roles (nombres no coinciden en Sistema_RBAC_Roles) y rbac_permisos/sec_permisos_catalogo (AMBIGUO en RBAC_Permisos). Reportes en `/app/docs/reports/mongo_validacion_muestra_llaves_20260607_191439/` (MD/JSON + CSV detalle por doc + CSV resumen). NADA borrado/modificado.
### P0 - Bitácora RBAC → SQL-First + Eliminación de Alcance legacy ✅ COMPLETE (2026-06-07)
Completadas las 2 features hermanas que seguían en Mongo stub (tras auditar y RECHAZAR el
script del usuario por: colisión de rutas con endpoints legacy no eliminados, `UsuarioID
UNIQUEIDENTIFIER` incompatible con el INT real, y crear un 3er sistema de alcance paralelo):
- **Bitácora RBAC → SQL**: nueva tabla `dbo.Usuario_RBAC_Bitacora` (UsuarioID INT,
  `migrations/rbac_bitacora_sql_20260607.py`); en `rbac_pilot_service.py` se añadieron
  `registrar_bitacora()` (no-fatal), `get_bitacora()` (filtros fecha/email/resultado/tipo +
  paginación OFFSET/FETCH) y `get_bitacora_evento()`. Se **re-instrumentaron** los 5 endpoints
  de perfiles/roles/permisos para escribir auditoría. Los endpoints legacy `GET /admin/bitacora`
  y `/admin/bitacora/{id}` (Mongo) fueron **reemplazados** por versiones SQL (gate `es_superadmin`).
  Contrato de respuesta idéntico al que espera el frontend (`useBitacoraRBACData.js`:
  skip/limit/fecha_inicio/fecha_fin/email/resultado/tipo → {total,pagina,paginas_total,eventos[]}).
- **Alcance legacy → ELIMINADO**: borrados `GET/POST /admin/alcance/*` (Mongo muerto, 0
  consumidores) porque el alcance canónico ya vive en `/api/config-asignaciones`
  (`Usuario_EmpresasAsignacion`/`Usuario_SucursalesAsignacion`). NO se creó tabla nueva.
- Eliminados 2 helpers de auditoría Mongo huérfanos (`registrar_auditoria_*_fase*`).
- NOTA: durante el borrado de helpers se eliminaron por error los endpoints
  `/admin/permisos/asignar` y `/admin/roles/asignar` (estaban intercalados); fueron
  **restaurados** en su versión SQL-First.
Verificado: cURL E2E (asignar perfil/rol/permiso generan bitácora; filtros OK; detalle OK;
`/admin/alcance/*` → 404; `/admin-sql/users` 26 usuarios). 19/19 tests, lint limpio,
regresión role-migration OK (pool-stats 200, config-asignaciones 200).

### P0 - Consolidación RBAC Canónica (helper SQL central) ✅ COMPLETE (2026-06-07)
A petición del usuario (tras auditar y RECHAZAR su script por crear un 3er helper con
niveles hardcodeados de solo 5 roles + reemplazo masivo ciego), se implementó la versión
segura reusando la infraestructura existente:
- **(A) Helpers canónicos en `core/rbac_helper_sql.py`** (sin 3er archivo, sin hardcodear
  niveles): `get_role_code()` (resuelve el código canónico desde los 23 roles de
  `Usuario_Roles` vía SQL + compatibilidad con role_code/_sql_rol_codigo/CodigoRol/role/
  NombreRol/rol), `es_superadmin()`, `es_admin()` (={SUPERADMIN,ADMIN}),
  `es_supervisor_o_superior()` (={SUPERADMIN,ADMIN,SUPERVISOR}). Conjuntos explícitos que
  preservan la semántica legacy y corrigen la **negación falsa al SUPERADMIN**.
- **(B) Migración quirúrgica** (no `text.replace` ciego) de porteros en 4 archivos:
  `server.py` (24 gates), `routes_competidores_enterprise.py` (5, con rename de var local
  `es_superadmin`→`es_super` para evitar colisión), `config_asignaciones_routes.py` (4),
  `catalogos/routes.py` (9). **Bug corregido**: endpoints con `!= 'Administrador'` /
  `not in ['Administrador','Supervisor']` que NEGABAN al SUPERADMIN (ej. `/api/sistema/pool-stats`
  daba 403, ahora 200). Se DEJÓ INTACTO `auth/routes.py` (ya correcto vía `tiene_acceso_global`,
  listas heterogéneas con Director/Gerente/Auditor → riesgo sin beneficio).
- **(C) Auditoría** `migrations/auditar_hardcodes_rbac.py` → CSV con hardcodes restantes
  clasificados por riesgo en `/app/docs/reports/P0_RBAC_HARDCODES_RESTANTES_*.csv`.
- Bonus: corregidos 2 bugs pre-existentes en `catalogos/routes.py` (`Descripcion`/`Codigo`
  indefinidos → NameError) y 2 corrupciones de cola de archivo.
Verificado: cURL per-rol (SUPERADMIN pasa gates antes denegados; comercial intacto
$1,573,660.81), 15/15 tests (`test_rbac_helpers_canonicos.py` + `test_rbac_helper.py` +
`test_rol_canonicidad_normalize_user.py`), lint limpio.
BACKLOG (en CSV): porteros restantes en `rh/solicitudes_catalogo.py`, `costos_margenes/*`,
`core/security.py`, `core/rbac/middleware.py`, frontend `Layout.js`.

### P0 - RBAC Piloto (Perfiles/Roles/Permisos) → SQL-First ✅ COMPLETE (2026-06-07)
Bug reportado por el usuario: "no encuentra los perfiles RBAC" → toast "Perfil
PERFIL_GESTOR_SISTEMA no encontrado o inactivo" al asignar un perfil en la pantalla
Usuarios. Causa raíz: el panel "Seguridad RBAC" (perfiles `sec_perfiles`, roles
`sec_roles`, permisos `sec_permisos`) corría 100% sobre MongoDB (`db = get_stub_database()`
en server.py:117), deshabilitado en la arquitectura SQL-First.
Migración SQL-First (opción (b) elegida por el usuario):
- Nuevas tablas SQL: `dbo.Sistema_RBAC_PerfilCatalogo` (catálogo perfil→roles CSV, 5 perfiles
  FASE 13 sembrados desde el respaldo mongodump `sec_perfiles.bson`) y
  `dbo.Usuario_RBAC_Asignacion` (asignación por usuario, Tipo: PERFIL|ROL|PERMISO).
- Nuevo servicio `modules/admin_sql/rbac_pilot_service.py` (get_perfiles_catalogo,
  asignar_perfil, retirar_perfil, toggle_asignacion, get_rbac_map).
- 5 endpoints reescritos a SQL en server.py (sin Mongo): `GET /admin/perfiles`,
  `POST /admin/perfiles/asignar|retirar`, `POST /admin/roles/asignar`,
  `POST /admin/permisos/asignar`. `/admin-sql/users` ahora devuelve `sec_perfil`,
  `sec_roles`, `sec_permisos` desde SQL.
- Semántica preservada del modelo legacy: asignar perfil = setea sec_perfil + sobrescribe
  sec_roles; retirar perfil = limpia sec_perfil+sec_roles (conserva permisos directos).
Verificado: cURL E2E (listar/asignar/estado/toggle rol/toggle permiso/retirar) sobre Carlos
Ruz (carlosruz@edarsa.com.mx) + screenshot (panel carga sin el error). Migración idempotente
en `migrations/rbac_pilot_sql_20260607.py`.
PENDIENTE (features separadas aún en Mongo stub, NO reportadas): visor "Bitácora RBAC"
(`/admin/bitacora`) y asignación de "Alcance" empresas/unidades/sucursales (`/admin/alcance/*`).

- [ ] Remover pymongo de dependencias (requirements)

### P0 - Canonicidad de Rol (SUPERADMIN ↔ SuperAdministrador) ✅ COMPLETE (2026-06-07)
Bug urgente reportado por el usuario: `role` en current_user/JWT llevaba el **CodigoRol**
canónico (`SUPERADMIN`), pero ~185 guards de backend y ~47 del frontend comparan por
igualdad contra el **NombreRol** legacy (`SuperAdministrador`). Resultado: el
SuperAdministrador era rechazado en decenas de endpoints (p.ej. `/api/config-asignaciones`
devolvía 403). Causa raíz adicional ("dos claves distintas"): 5 sitios en
`routes_competidores_enterprise.py` leían la clave equivocada `current_user.get('rol')`
(no existe; la clave es `'role'`).
Fix de punto único en `modules/auth/repository.py::_normalize_user`:
- `role` = `NombreRol` legacy (lo que esperan guards + frontend).
- Se conserva el CodigoRol canónico en `role_code` y `_sql_rol_codigo` (para RBAC canónico-aware).
- Ajuste puntual `inteligencia_comercial_routes.py:113` (set acepta `SUPERADMINISTRADOR`).
- 5x `current_user.get('rol')` → `current_user.get('role')` en competidores enterprise.
Verificado vía cURL: login Ricardo OK, `/api/config-asignaciones` 200 (antes 403),
`/api/inteligencia/dashboard` 200, total comercial canónico intacto **$1,573,660.81**.
Regresión: `tests/test_rol_canonicidad_normalize_user.py` (4 tests) + `tests/test_rbac_helper.py` (5).
Equivalencia respetada: SUPERADMIN↔SuperAdministrador, ADMIN↔Administrador,
SUPERVISOR↔Supervisor, USUARIO↔Usuario, VISOR↔Visor.
- La contraseña del usuario fue restablecida mediante procedimiento controlado; el valor no se conserva en Git.

---

## Testing Protocol
- **Permitido**: bash, cURL, python -c, screenshots
- **PROHIBIDO**: testing_agent_v3_fork

---

## Key Files Reference
- `/app/backend/core/sql_first/db.py`
- `/app/backend/core/sql_first/connection_factory.py`
- `/app/backend/core/db.py` (wrapper legacy)
- `/app/backend/core/rbac_sql/service.py`
- `/app/backend/core/config/edarsahub_config.py`
- `/app/backend/modules/auth/repository.py` (AuthRepository SQL-only)
- `/app/backend/modules/sistema/menu_service.py` (MenuService SQL canónico)
- `/app/backend/modules/sistema/menu_routes.py` (Rutas de menú)
- `/app/backend/auditorias_p4/` (logs y backups P4)
- `/app/backend/auditorias_p5/` (logs y backups P5)

---

## Environment Variables
```
EDARSAHUB_SQL_HOST=54.39.104.176
EDARSAHUB_SQL_PORT=1433
EDARSAHUB_SQL_DATABASE=EDARSAHUB
EDARSAHUB_SQL_USER=HRLectura
EDARSAHUB_SQL_PASSWORD=******
```

---

*Last Updated: 2026-06-06*
*Phase: P4 Complete, P5-10B Complete (Menu SQL + Enterprise Menu)*
*Pending: Final MongoDB Sunset*

## Enterprise Menu System
El sistema ahora tiene un menú Enterprise organizado por grupos:
- **Operación**: Ventas, Compras, Inventarios, Producción
- **Finanzas**: Flujo, Bancos, Contabilidad, Comisiones
- **Personas**: RH, CRM, Cava de Socios
- **Inteligencia**: Dirección, BI, IA, Auditoría
- **Gestión**: Proyectos, Marketing
- **Corporativo**: Activos, Catálogos
- **Integraciones**: Conectores, APIs
- **Administración/Sistema**: Control, Infraestructura, Seguridad
- **Satélites**: Comandero, Super Caja, PIC

Archivos clave:
- `/app/frontend/src/config/enterpriseMenuConfig.js` - Configuración canónica
- `/app/frontend/src/components/navigation/EnterpriseSidebarMenu.jsx` - Componente visual
- Flag `USE_ENTERPRISE_MENU` en Layout.js para activar/desactivar

### P1B - Sync POS Canónico Configurable (Modo Seguro) ✅ COMPLETE (2026-06-08)
Script `.sh` del usuario AUDITADO y RECHAZADO (2 bloqueantes críticos invisibles a sus propias
validaciones: NameError `tipo_ejecucion` por firma ya modificada → rompía el cron horario; y
`detectar_faltantes_syncpos` consultaba `Venta_Detalle.PIC_*` que NO existe en EDARSAHUB,
oculto por `|| true`). Intención implementada MANUALMENTE y corregida, con autorización del
usuario en MODO SEGURO:
- **SQL** (`migrations/p1b_sync_pos_config.py`, idempotente): crea `dbo.Sistema_SyncPOS_Config`,
  `_EstadoUnidad`, `_Faltantes`, `_Bitacora`. Seed `INTELIGENCIA_COMERCIAL_POS` con
  **Habilitado=0, PermitirPOSAutomatico=0, BackfillAutomaticoHabilitado=0** (NO conecta al POS).
- **Job** (`core/scheduler/jobs/inteligencia_comercial_sync_job.py`): `UNIDADES_CONFIG` deprecado
  a `{}` (eliminados hosts `.ddns.net`, `sa`, `*_DB_PASS`, `EDARSAHUB_SQL_PASSWORD`). Helpers
  canónicos leen `Unidades_Negocio`+`Servidores_Conexiones` y reúsan `get_server_connection_config`
  de Comercial V2 (sin duplicar desencriptado). Gate `should_run_syncpos_now` → cron horario hace
  SKIPPED sin tocar POS. Firma extendida con `tipo_ejecucion`.
- **Scripts**: `scripts/auditar_sync_pos_canonico.py` (auditoría sin secretos, `has_password` bool),
  `scripts/guardrail_sync_pos_secrets.py`, `scripts/backfill_inteligencia_comercial_pos.py`.
- Verificado: migración OK, py_compile OK, guardrail OK, lint OK, auditoría 5/5 unidades resueltas
  sin exponer password, AUTO=skipped (no conecta POS), backend 200, bitácora registró SKIPPED.
- **DIFERIDO por decisión del usuario**: detección de faltantes hasta definir tabla final de detalle
  (Venta_Detalle vs Comercial_Inteligencia_VentasDetalleProducto; Sync_Sales solo staging).
- **Activación**: por SQL `UPDATE dbo.Sistema_SyncPOS_Config SET Habilitado=1, PermitirPOSAutomatico=1`
  cuando el usuario valide conectividad. Reporte: `docs/reports/P1B_SYNC_POS_CANONICO_AUTO_20260608.md`.

### P0 - Corrección Exposición de Secretos / POS SQL-First ✅ COMPLETE (2026-06-08)
Script `.sh` del usuario AUDITADO y RECHAZADO (Parche 1 duplicaba helpers de P1B; Parche 2 rompía
la pantalla viva de Finanzas CxP y NO redactaba el secreto real; Parche 3 rompía URLs funcionales).
- Se detectó y eliminó un secreto en texto plano; el valor no se conserva en Git y requiere rotación.
manualmente con autorización:
- **`modules/finanzas/repository_softrestaurant.py`** (LIVE): `SOFTRESTAURANT_SERVERS` migrado a
  builder `_build_softrestaurant_servers()` que resuelve host/puerto/db/usuario/password desde
  `Unidades_Negocio.server_id`+`Servidores_Conexiones` vía `get_server_connection_config` (sin
  hardcodes; solo metadata no-secreta id/view). Endpoint CxP `/sucursales` → 200, 3 sucursales OK.
- **`modules/comercial/adapters.py`**: eliminados defaults hardcodeados con IP pública en
  `os.environ.get("API_MPRO_*_URL", "http://54.39.104.176:...")` (vars ya en `.env`).
- **`modules/comercial_v2/carga_historica_24_meses.py`**: eliminado `close_pool` con host hardcodeado.
- **`core/server_registry.py`**: host de ejemplo en docstring neutralizado.
- **`frontend/src/pages/Servidores.js`**: eliminado fallback hardcodeado de `loadApiConnections()`
  (IPs públicas); en error → `setApiConnections([])`+toast; placeholder neutro. Sin tocar endpoints
  ni mover a `REACT_APP_*`.
- Verificado: grep runtime 0 ocurrencias de `C0ntr4s3ña`/IP/ddns en archivos tocados; py_compile OK;
  lint limpio; backend RUNNING; CxP 200. Reporte: `docs/reports/P0_FIX_SECRET_EXPOSURE_20260608.md`.
- PENDIENTE (arquitectura, separado): `repository_softrestaurant.py` aún consulta POS EN VIVO
  (subprocess) → migrar a tabla pre-calculada EDARSAHUB (NO-LIVE) es trabajo futuro.

### Opción A — Backfill detalle Sync_Sales: PILOTO ✅ VALIDADO (2026-06-08)
Usuario autorizó Opción A (lectura POS en vivo) + piloto controlado. Hallazgo: el histórico de
**KPIs ya estaba completo** (`Comercial_KPIs_Diarios_v2`: 3,392 filas, 2024-05→2026-06,
$431,766,974.05, `SQL_LIVE`); lo faltante es el DETALLE en `Sync_Sales`. Por eso el backfill puebla
SOLO `Sync_Sales`, sin tocar KPIs (regla protegida).
- **Conectividad**: las 5 unidades POS alcanzables desde el pod (probe read-only).
- **Piloto ESTELAR mayo-2026**: 1,881 tickets / 25,541 líneas / $2,924,063 insertados a `Sync_Sales`
  en 63.7s. Comparación vs KPI canónico (solo lectura): −0.18% ($2,924,063 vs $2,929,406). 0 tickets sin detalle.
- **Validado**: idempotencia (re-run insertó 0, 1881 duplicados); `Comercial_KPIs_Diarios_v2` INTACTO
  (3,392 filas/$431,766,974.05); solo `Sync_Sales` tocado (79→1,960). Credenciales canónicas, sin secretos,
  por lotes, transaccional con rollback, bitácora.
- Scripts: `scripts/probe_pos_connectivity.py`, `scripts/pilot_backfill_sync_sales.py`.
- **PENDIENTE autorización del usuario**: escalar a 24 meses × 5 unidades (~225,720 tickets, ~2h, por lotes
  mes×unidad). Validar query MPRO (130QRO/ORIGEN) en mini-piloto antes de escalar esa rama.
- Reporte: `docs/reports/PILOTO_OPCION_A_BACKFILL_SYNC_SALES_20260608.md`.

### Backfill Opción A (detalle Sync_Sales) ✅ COMPLETADO (2026-06-08)
Usuario autorizó Opción A (lectura POS en vivo) + escalado por tandas + desbloqueo CIENFUEGOS/MPRO.
**`Sync_Sales` pasó de 79 → 112,313 tickets** (detalle ticket/producto real) para las 5 unidades,
24 meses (2024-06→2026-06; ESTELAR desde 2025-06 por límite real de su POS):
- 130MID 26,796 · CIENFUEGOS 30,183 · ESTELAR 16,216 · 130QRO 17,612 · ORIGEN 21,506.
- **KPIs canónicos INTACTOS** (`Comercial_KPIs_Diarios_v2` = 3,392 / $431,766,974.05 / SQL_LIVE) — regla
  protegida cumplida: SOLO se pobló `Sync_Sales`, sin tocar/re-derivar KPIs ni vw_*.
- Diferencias detalle vs KPI (mayo-26) sanas: ESTELAR −0.18%, 130QRO −1.9%, ORIGEN −1.3%, CIENFUEGOS +4.7% (reportadas, no corregidas).
- Desbloqueos: CIENFUEGOS (SQL 2014 sin FOR JSON) → extracción two-pass armando JSON en Python; MPRO
  (CENTRAL2020) → detalle en `Comanda_Detalle` + filtro `Sc_Cve_Sucursal=sucursal_origen_id` (0021/0023) + NOLOCK/retry.
- Credenciales canónicas, idempotente (NumeroTicket+unidad+fecha), por lotes, transaccional, bitácora.
- Scripts: `probe_pos_connectivity.py`, `pilot_backfill_sync_sales.py`, `backfill_sync_sales_batch.py`.
- Reporte: `docs/reports/BACKFILL_OPCION_A_COMPLETADO_20260608.md`.
- **SIGUIENTE (PIC Fase 2)**: conectar tarjetas "Top Productos"/"Casas" del DashboardIA a `Sync_Sales` real (eran mock).

### P0 — Retiro de `server_id` en tableros de lectura · FASE 1 (Métricas) ✅ COMPLETE (2026-06-08)
Decisión del usuario: **opción (b)** — mantener los endpoints operativos por servidor
(`/servers/{server_id}/...` de la pestaña Análisis) INTACTOS, y migrar SOLO la capa de
lectura/reportes al contrato canónico `unidad`. Admin screens conservan `server_id`.
- **Frontend `pages/Dashboard.js` (pestaña Métricas):** eliminada la resolución local de
  `server_id` (`getServerIdFromUnidad`/`useMemo selectedServer`). Ahora envía la `unidad`
  (id/código) directamente: `GET /dashboard/inventory-summary?unidad=...` y
  `GET /inventarios/pendientes/{unidad}`. Diff = solo cambio funcional (sin reordenar hooks,
  para no introducir comentarios `eslint-disable` de reglas que el build CRA no conoce
  —`set-state-in-effect`/`immutability`— que rompían la compilación).
- **Backend `server.py`:**
  - `/dashboard/inventory-summary`: nuevo param `unidad` (+ `server_id` DEPRECATED compat).
    Resuelve server_id central con `resolve_unidad_scope` (RBAC + canónico). access_denied → vacío.
  - `/inventarios/pendientes/{server_id}`: el token de ruta se resuelve con `resolve_unidad_simple`
    → si es unidad, se traduce a su server_id; si es server_id legacy (pantalla Análisis), se deja
    igual. RBAC aguas abajo vía `has_server_access` intacto.
- **Informes (`/auditoria/informes/*`):** ya eran agnósticos a servidor en lectura (GET sin filtro
  por server; el create solo guarda `servidor_id` como metadato derivado de Análisis). NO requirió cambio.
- Verificado cURL E2E: CIENFUEGOS por `unidad` (id y código) → success=True/datos OK; MPRO (QRO/ORIGEN)
  → guarda NO-LIVE intacta (prueba que el resolver resolvió bien); compat legacy `server_id` → misma
  respuesta (sin regresión; 130MID sigue con queries_configured=0, estado de datos conocido);
  `pendientes` resuelve token-unidad y server_id directo → 200. Lint del proyecto limpio, CRA compila,
  smoke E2E visual (selección CIENFUEGOS renderiza KPIs/gráficos sin error).
- **PENDIENTE (reportar al usuario):** FASE 2 — migrar TableroEjecutivo, DashboardIA, Compras,
  Finanzas/Propinas, Tesorería, Costos, Pricing al contrato `unidad`.

### P0 — Inventarios físicos SoftRestaurant rotos + crash login ✅ COMPLETE (2026-06-08)
Bug reportado (urgente): en la pestaña **Análisis**, los inventarios de **SoftRestaurant**
(130MID, CIENFUEGOS, ESTELAR) salían "No hay inventarios disponibles" y un crash
`undefined is not an object (evaluating 'userData.role')` sacaba del sistema. MPRO sí
mostraba inventarios. Regla del usuario: AMBOS sistemas deben funcionar, no romper uno
arreglando el otro (este ajuste ya se había perdido ~4 veces).
- **Causa raíz (read-only confirmada):** `Compras_Inventarios_Fisicos_Sync` SÍ tiene datos
  SoftRestaurant (CIEN 185 / MID 172 / ESTELAR 131) pero su columna `sucursal` viene VACÍA
  (single-tenant). El frontend SR envía el placeholder `sucursal='SoftRestaurant'` y el
  endpoint filtraba SIEMPRE por sucursal → `sucursal LIKE '%SoftRestaurant%'` = 0 filas.
- **Fix canónico (sistema-agnóstico, sin hardcode 'MPRO'/'SoftRestaurant')** en
  `server.py::obtener_inventarios_fisicos`: el filtro por sucursal SOLO aplica cuando un
  mismo server_id aloja >1 unidad (caso MPRO ORIGEN/QRO) usando
  `_shared_server(server_id)`. Para single-tenant → `sucursal_filtro=None` → el server_id
  basta. Futuro-proof: si se agrega otro sistema, el criterio (¿server con varias unidades?)
  sigue válido.
- **Crash login:** guard null-safety en `AuthContext.jsx` (`userData?.role`).
- **Verificado cURL E2E:** SoftRestaurant con `sucursal=SoftRestaurant` → CIEN 185 / MID 172
  / ESTELAR 131 (antes 0); MPRO desambiguación intacta (QRO 113 solo '130° QUERETARO',
  ORIGEN 147 solo 'ORIGEN'); sin crash; smoke visual OK. Regresión:
  `tests/test_inventarios_fisicos_scope_canonico.py` (3 tests, blindan la invariante canónica).
- **PENDIENTE (propuesto, requiere autorización):** mostrar el **comentario capturado** en los
  selectores Inventario Inicial/Final SOLO MPRO. Hoy NO es posible NO-LIVE porque
  `Compras_Inventarios_Fisicos_Sync` NO tiene columna `comentario`, la query fuente MPRO
  (`query_inventarios_fisicos_mpro`) NO lo selecciona y el INSERT del sync NO lo guarda; el
  read devuelve `comentario=''` hardcodeado (server.py:7428). El frontend YA lo renderiza si
  viene (Reportes.js 1837/1939). Solución robusta data-driven (sin hardcode de system_type):
  (1) agregar columna `comentario` a la tabla sync, (2) seleccionar el campo real en la query
  MPRO (definir nombre exacto de columna, p.ej. observaciones), (3) incluirlo en el INSERT,
  (4) backfill MPRO, (5) read devuelve el valor real. SoftRestaurant queda '' automáticamente.

### P0 — Protección anti-cooldown EDARSAHUB en /inventarios/pendientes ✅ COMPLETE (2026-06-08)
Reporte: "Tablero Ejecutivo roto" (pantalla en blanco). Diagnóstico: el tablero NO estaba roto
(endpoint 200, ventas Junio=$3,792,053.41, 5 unidades, 0 errores). La causa de verlo vacío fue
un **cooldown transitorio de EDARSAHUB**: en logs, timeout de conexión a `54.39.104.176` (host
que comparte EDARSAHUB con el POS de MPRO). Un intento de conexión EN VIVO fallido a ese host
pone EDARSAHUB en cooldown y TODAS las lecturas canónicas (tablero, unidades, RBAC) devuelven
vacío → "el sistema se cae" (la fragilidad que el usuario ha perdido ~4 veces).
- **Disparador cerrado:** `/inventarios/pendientes/{server_id}` conectaba EN VIVO al POS; para
  MPRO eso es el host de EDARSAHUB. Métricas (Dashboard.js) autollama pendientes al elegir
  unidad. Se añadió la MISMA guarda NO-LIVE que ya tenía `/dashboard/inventory-summary`: si el
  host del server resuelto == host EDARSAHUB → NO conecta live, devuelve vacío con `no_live:true`.
- **Verificado cURL:** pendientes MPRO → vacío en 0.78s sin tocar EDARSAHUB; pendientes
  SoftRestaurant → sigue live OK; Tablero Ejecutivo → $3,792,053.41 / 5 unidades / 0 errores;
  inventarios MPRO=113 y SoftR=185 intactos. Sin regresiones.
- NOTA arquitectónica (backlog): otros endpoints operativos MPRO de Análisis
  (`/servers/{server_id}/almacenes|sucursales`) aún pueden conectar live al host compartido;
  migrarlos a NO-LIVE es trabajo futuro para blindar 100% el anti-cooldown.

### FASE A — Comentario MPRO en inventarios (NO-LIVE) ✅ COMPLETE (2026-06-08)
Objetivo: mostrar el comentario capturado en los selectores Inventario Inicial/Final, SOLO MPRO
(SoftRestaurant no tiene ese campo). Autorizado por el usuario (columna + backfill).
- **Descubrimiento de esquema (read-only, proceso aislado para no afectar cooldown):** el campo real
  es **`Fisico.Fi_Comentario`** (nvarchar 50) en el POS MPRO (db CENTRAL2020). La tabla
  `Inventario_Fisico` que usa `repository.py::query_inventarios_fisicos_mpro` NO existe (código
  legacy muerto). El sync REAL usa `sync_service.py::sync_inventarios_fisicos_from_server` →
  tabla **`Fisico`** con `Fi_Folio`.
- **Cambios:** (1) columna `comentario NVARCHAR(255)` en `Compras_Inventarios_Fisicos_Sync`
  (idempotente). (2) query sync MPRO: `MAX(F.Fi_Comentario) as comentario` (1 por folio,
  prefiere no-vacío). (3) query sync SoftRestaurant: `'' as comentario`. (4) INSERT incluye
  comentario. (5) read `obtener_inventarios_fisicos_sync` SELECT + endpoint
  `obtener_inventarios_fisicos` devuelven el comentario real (antes hardcodeado `''`, server.py).
- **Backfill** (`scripts/backfill_comentario_mpro.py`): UPDATE por folio (sin re-sync/REPLACE,
  no perturba filas). 245 folios leídos del POS (244 con comentario) → 238 filas MPRO actualizadas.
- **Verificado cURL:** MPRO QRO 102/113 con comentario (CONSIGNACION/BARRA/COCINA),
  ORIGEN 136/147 (CAVA/BARRA/BODEGA), SoftRestaurant 0 (vacío, data-driven). Frontend ya
  renderiza `inv.comentario` (Reportes.js 1837/1939, Compras.js 756). Tablero Ejecutivo intacto.
- **PENDIENTE:** Fase C (anti-cooldown: derivar almacenes/sucursales del inventario NO-LIVE,
  eliminar `/servers/{id}/almacenes|sucursales` vivos) y Fase B (unificar el filtro
  Análisis↔Auditoría en un solo componente canónico).

### FASE C — Anti-cooldown: sucursales/almacenes MPRO NO-LIVE ✅ COMPLETE (2026-06-08)
Objetivo: eliminar las conexiones EN VIVO al host compartido de EDARSAHUB (54.39.104.176) que
disparan el cooldown. Enfoque elegido: **backend-only** (cero cambio de UI → cero riesgo de
regresión visual), en lugar de refactor del frontend.
- `/servers/{id}/sucursales` y `/servers/{id}/almacenes`: si el server es el host compartido de
  EDARSAHUB (`_is_edarsahub_shared_host`), se derivan de `Compras_Inventarios_Fisicos_Sync`
  (helpers `_derive_sucursales_from_sync` / `_derive_almacenes_from_sync`) en vez de conectar en
  vivo. RBAC de almacenes y filtros de permisos/visibilidad de sucursales se mantienen.
- `/servers/{id}/inventarios` ya era NO-LIVE (no se tocó). SoftRestaurant sigue en vivo a su propio
  POS (host distinto, sin riesgo de cooldown).
- **Verificado cURL:** MPRO sucursales → [0021 130° QUERETARO, 0023 ORIGEN]; almacenes QRO=3
  (ALMACEN GENERAL/BODEGA/CONSIGNACION), ORIGEN=2; SoftRestaurant almacenes=10 (live OK);
  Tablero Ejecutivo $3,792,053.41 / 5 unidades / 0 errores. Sin regresiones.
- NOTA: los almacenes MPRO ahora son solo los que TIENEN inventarios físicos en el sync (correcto
  para análisis de inventarios). Si se requiere mostrar almacenes sin inventarios, sería ajuste aparte.
- **PENDIENTE Fase B** (unificar Análisis↔Auditoría) — también arregla bugs de modales de detalle:
  Reportes usa `/reports/movement-details` y `/reports/sales-details` (fallan), Compras usa
  `/compras/detalle-movimientos` (OK) y `/compras/detalle-consumos` (falla "sin registros").

### NO-LIVE total + unificación detalle (respuesta a 4 puntos del usuario) ✅ (2026-06-08)
El usuario señaló: (1) SoftRestaurant aún consultaba almacenes EN VIVO (debe ser EDARSAHUB
exclusivo); (2) Auditoría MPRO ORIGEN daba "Error de conexión" (debe leer de EDARSAHUB como
SoftRestaurant); (3) detalle de consumos de Auditoría no salía y la fecha inicial debe tomarse
del inventario inicial; (4) el detalle de ventas de Análisis SÍ funciona y Auditoría debe usar lo mismo.
- **Change A — almacenes/sucursales NO-LIVE para TODOS los sistemas:** `/servers/{id}/almacenes`
  y `/sucursales` ahora derivan SIEMPRE de `Compras_Inventarios_Fisicos_Sync` (helpers
  `_derive_*_from_sync`), sin conexión viva a ningún POS. El filtro por sucursal solo aplica a
  servers compartidos (MPRO) vía `_shared_server`. Verificado: SoftR CIEN almacenes=10 / sucursal
  virtual; MPRO ORIGEN=2, QRO=3 (filtrado correcto por nombre o sucursal_id).
- **Change B — `/compras/pedidos-vigentes` NO-LIVE:** eliminado el fallback LIVE (PASO 2). Si el
  sync no trae requisiciones → devuelve `[]` sin conectar. Esto elimina el banner "Error de
  conexión" en Auditoría MPRO (antes lanzaba 503). Verificado: ORIGEN → 200 `[]` en 0.9s.
- **Change C — `/compras/detalle-consumos` unificado:** ahora delega en `get_sales_details` (la
  MISMA lógica que `/reports/sales-details` de Análisis, que funciona para MPRO y SoftRestaurant),
  usando `fecha_inicio` (del inventario inicial) y mapeando al formato del modal de Compras
  (fecha/concepto/descripcion/cantidad/almacen/referencia + campos legacy). Smoke: 200, shape OK.
- NOTA: el detalle de ventas/consumos sigue usando conexión viva al POS (igual que Análisis hoy).
  Para NO-LIVE total del detalle habría que migrarlo a `Sync_Sales` (tarea futura). Tablero
  Ejecutivo intacto ($3,792,053.41 / 5 unidades / 0 errores). Regresión: 3 tests pasan.
- **PENDIENTE verificación del usuario:** abrir Auditoría MPRO ORIGEN (sin error) y doble clic en
  un producto real para ver consumos. Movimientos de Auditoría ya funcionaba (no se tocó).

## 🥇 MÁXIMA DE ORO (REGLA PERMANENTE — 2026-06-07)
**CADA VEZ que algo se vaya a HARDCODEAR, se REQUIERE la AUTORIZACIÓN ESCRITA del usuario ANTES de hacerlo.**
- Aplica a: unidades, credenciales, hosts, rutas, horarios, roles/permisos, productos, casas/marcas, periodos, IDs, URLs, valores de negocio, fallbacks, etc.
- Si un valor no puede venir de SQL/env/config canónica, DETENERSE y pedir autorización escrita explícita; nunca hardcodear por defecto.
- Preferir siempre fuente canónica: EDARSAHUB SQL (p.ej. catálogos como dbo.Servidores_Conexiones) o variables de entorno.
- Si se detecta hardcoding pre-existente, reportarlo (no asumir que es propio) y proponer migración a fuente canónica, también con autorización.
