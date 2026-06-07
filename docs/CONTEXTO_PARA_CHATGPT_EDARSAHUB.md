# CONTEXTO EDARSA HUB — PÉGALO A ChatGPT ANTES DE PEDIRLE SCRIPTS

> Copia TODO este bloque al inicio de tu chat con ChatGPT. Así dejará de inventar
> tablas, columnas, parámetros y comandos. Está verificado contra la base, el
> backend y el frontend reales (Junio 2026).

---

## 0) REGLA #1 — IMPORTANTE
ChatGPT **NO tiene acceso** a mi base de datos, ni a mi frontend, ni a mi backend.
Solo conoce lo que yo le pegue aquí. Si le falta un dato, **debe pedírmelo**, NO inventarlo.
Si un script asume un nombre de tabla/columna/endpoint que no está en este documento,
está MAL y no debe entregarse.

> Nota práctica: el agente de Emergent (quien ejecuta los cambios) **SÍ** tiene acceso
> directo a EDARSAHUB SQL, al frontend y al backend. Para muchos cambios es más rápido
> y seguro pedírselos directamente al agente en lenguaje natural (sin pasar por scripts).

---

## 1) MÁXIMAS ARQUITECTÓNICAS (INQUEBRANTABLES)
- **EDARSAHUB SQL es la ÚNICA fuente de verdad.** Ninguna pantalla/reporte consulta bases externas en vivo (POS, SoftRestaurant, MPRO, sucursales). **NO-LIVE.**
- **NO MongoDB.** Está 100% eliminado. Todo es **SQL-First**.
- **NO** inventar datos, **NO** hardcodear importes ni unidades.
- **El KPI de ventas usa `ventas_sin_propina`.** Las propinas (`propinas_total`) van **separadas y fuera** del KPI.
- **Gestor de paquetes frontend: `yarn`. NUNCA `npm`.** (`npm run build` está PROHIBIDO; usar `yarn build`).
- No duplicar tablas/conexiones/flujos/usuarios/unidades. No crear módulos paralelos: corregir el flujo existente.
- Validar todo script con `python3 -m py_compile` (backend) y `yarn build` (frontend) ANTES de darlo por bueno.

---

## 2) BASE DE DATOS — EDARSAHUB SQL Server (vía pymssql)

### Vista CANÓNICA del Tablero Comercial (DIARIO)
`dbo.vw_Comercial_KPIs_Diarios_v2_Runtime` — columnas reales:
```
id, unidad_negocio_pk (uniqueidentifier/GUID), unidad_id, unidad_negocio_id (CÓDIGO texto, p.ej. '130MID'),
unidad_negocio_nombre, UnidadNegocio, unidad_codigo, unidad_nombre_catalogo, server_id, sucursal_id,
sucursal_nombre, sistema_origen, fecha_operacion (date), anio, mes, dia,
ventas_total, ventas_sin_propina, propinas_total, tickets_total, pax_total, ticket_promedio, pax_promedio,
ventas_cerradas, ventas_abiertas, total_estimado_dia, es_venta_abierta, es_corte_cerrado,
fecha_sincronizacion, version
```
⚠️ **NO existen las columnas `activo` ni `es_demo`.** Filtrar por ellas rompe la query (KPIs en cero).
⚠️ Para filtrar por unidad usar **`unidad_negocio_id`** (CÓDIGO), NO `unidad_negocio_pk` (GUID), porque
los "permisos de unidad" del usuario vienen como CÓDIGOS canónicos.

### Vista MENSUAL
`dbo.vw_Comercial_KPIs_Mensuales_v2_Runtime`:
```
id, unidad_negocio_pk, unidad_id, unidad_negocio_id, unidad_negocio_nombre, UnidadNegocio, unidad_codigo,
unidad_nombre_catalogo, server_id, sistema_origen, anio, mes, dias_con_datos, dias_mes_total,
ventas_total, ventas_sin_propina, propinas_total, tickets_total, pax_total, ticket_promedio, pax_promedio,
proyeccion_mes, ventas_mes_anterior, var_vs_mes_anterior, ventas_anio_anterior, var_vs_anio_anterior,
es_mes_completo, fecha_calculo, version
```

### Ventas del Día (snapshot abiertas+cerradas)
`dbo.Comercial_Ventas_Dia_Abiertas_v2`:
```
id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id, sucursal_nombre, sistema_origen,
snapshot_timestamp, fecha_operacion, ventas_abiertas, tickets_abiertos, pax_abiertos,
ventas_cerradas_dia, tickets_cerrados_dia, pax_cerrados_dia, total_estimado_dia,
fuente_original, sync_run_id, fecha_ultima_actualizacion
```
⚠️ Esta tabla **NO tiene `unidad_negocio_pk`** (solo `unidad_negocio_id`).

### Otras tablas relevantes
- `dbo.Comercial_SyncLog_v2` (logs de sync; tiene `unidad_negocio_id`, no `pk`).
- `dbo.Servidores_Conexiones` y `dbo.Servidores_Conexiones_Log` (Admin CORE + bitácora).
- `dbo.Sistema_AlertasDestinatarios` (destinatarios de alertas).
- `dbo.Finanzas_AuditoriaFinanciera` (auditoría financiera).

Unidades activas (Junio 2026), códigos canónicos: `130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN`.

---

## 3) BACKEND — FastAPI + pymssql
- Todas las rutas montan bajo prefijo **`/api`**. Backend en `0.0.0.0:8001` (gestionado por supervisor).
- Auth: **JWT Bearer**. El claim `role` trae el **CÓDIGO** del rol (p.ej. `SUPERADMIN`).
  Acceso total se resuelve con `core/rbac_helper_sql.has_full_access` (compara contra NOMBRES y CÓDIGOS).
- Las "unidades permitidas" del usuario = **lista de CÓDIGOS** (no GUIDs).

### Endpoints del Tablero Comercial V2 (módulo `backend/modules/comercial_v2/`)
| Endpoint | Método | Parámetros (EXACTOS) | Notas |
|---|---|---|---|
| `/api/v2/comercial/dashboard` | GET | **`fecha_inicio` (YYYY-MM-DD, REQUERIDO)**, **`fecha_fin` (REQUERIDO)**, `unidad_negocio_pk` (opcional, es CÓDIGO) | NO acepta `mes`/`anio`/`modo`. Faltar fecha_inicio/fecha_fin = **HTTP 422**. |
| `/api/v2/comercial/ventas-dia` | GET | (ninguno requerido) | Usar para modo "Ventas del Día". |
| `/api/v2/comercial/health` | GET | — | Healthcheck del módulo. |

**Respuesta del dashboard** (shape real):
```json
{
  "success": true,
  "data": {
    "totales": { "ventas_total": <ventas_sin_propina>, "propinas_total": ..., "tickets_total": ..., "pax_total": ..., "total_unidades": ... },
    "unidades": [ { "unidad_negocio_pk": "<código>", "unidad_negocio_nombre": "...", "ventas_total": ..., "ventas_sin_propina": ..., "propinas_total": ..., "tickets_total": ..., "pax_total": ..., "ticket_promedio": ..., "dias": ... } ]
  },
  "metadata": { ... }
}
```
> `totales.ventas_total` ya viene como **ventas SIN propina** (KPI). `propinas_total` va aparte.

### Cómo probar el backend (curl correcto)
```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
TOKEN=$(curl -s -X POST "$API/api/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"admin@edarsa.com","password":"pruebas123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s "$API/api/v2/comercial/dashboard?fecha_inicio=2026-06-01&fecha_fin=2026-06-30" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 4) FRONTEND — React (craco) + shadcn/ui
- Gestor: **`yarn`**. Build de validación: **`yarn build`** (NO `npm`).
- ESLint del proyecto = `eslint-plugin-react-hooks@^7.1.1`, PERO el build (craco) **no tiene definidas**
  las reglas `react-hooks/set-state-in-effect` ni `react-hooks/immutability`. ⚠️ Por eso un comentario
  `// eslint-disable-next-line react-hooks/set-state-in-effect` **rompe** `yarn build`
  ("Definition for rule ... was not found"). **No usar esos disables.**
- El frontend siempre llama al backend usando `process.env.REACT_APP_BACKEND_URL` (+ `/api`).
- Token de sesión: `sessionStorage 'edarsa_memory_token'` (preservado en el reset de caché de preview).

### Componente del Tablero: `frontend/src/pages/TableroEjecutivo.js`
- Llama a `GET /api/v2/comercial/dashboard?fecha_inicio=...&fecha_fin=...` (deriva fechas del mes/año elegido).
- Para "Ventas del Día" llama a `/api/v2/comercial/ventas-dia` (NO al dashboard).
- Detalle: hace `react` race-safe con `useRef` (no descartar respuestas válidas como "stale").
- El selector de Año incluye la opción especial `value='-1'` = "📊 Ventas del Día".
- **NO reemplazar el componente entero.** Tiene: layout/sidebar EDARSA, drill-down de detalle por unidad,
  variaciones vs mes/año anterior. Hacer cambios **quirúrgicos**, no reescrituras.

---

## 5) CREDENCIAL DE PRUEBA
`admin@edarsa.com` / `pruebas123` (Rol: SUPERADMIN).

---

## 6) PLANTILLA PARA PEDIRLE A ChatGPT
> "Usa SOLO el contexto de EDARSA HUB que te pegué. No inventes tablas, columnas ni endpoints.
> Para el Tablero, el endpoint es `/api/v2/comercial/dashboard?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`.
> KPI de ventas = `ventas_sin_propina`; propinas separadas. La vista canónica es
> `vw_Comercial_KPIs_Diarios_v2_Runtime` (sin columnas `activo`/`es_demo`); filtra por `unidad_negocio_id`.
> Valida frontend con `yarn build` (nunca npm) y backend con `py_compile`. Si te falta un dato, pídemelo."
