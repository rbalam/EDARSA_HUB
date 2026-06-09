# DIAGNÓSTICO — Portal Inteligencia: Auth (cookie→Bearer) + eliminación de mock
Fecha: 2026-06 · Régimen: SQL-First, NO-LIVE, sin hardcode, sin testing_agent_v3_fork
Sin regex amplio · Sin cambios de diseño/menús/KPIs · Backend solo si el diagnóstico lo exige.

## A. CAUSA RAÍZ (AUTH)
- **Backend `/api/auth/me`** (`modules/auth/routes.py:383-409`) usa `get_current_user_dual(request)` →
  **ACEPTA Authorization: Bearer O Cookie**. ✅ NO requiere cambio backend.
- El portal (`App.jsx`) llama `/api/auth/me` con `{ credentials:'include' }` (solo cookie) y **NO** envía
  el token operativo vigente (Bearer) que el sistema principal guarda en `sessionStorage`
  bajo la llave canónica `edarsa_memory_token` (definida en `lib/api.js::getToken`).
  La cookie httpOnly de *access* es de corta duración y el portal **no hace refresh**, por eso
  `/auth/me` responde 401 y el portal cae a **modo demo**.
- Fuente canónica de token a reutilizar: `frontend/src/lib/api.js` (axios `api` con interceptor
  Bearer + refresh + manejo 401; en rutas `/inteligencia-comercial` NO redirige forzado a /login).

## B. FRONTEND — AUTH (cookie → Bearer) [EN ALCANCE]
| # | Archivo | Línea/bloque | Hallazgo | Endpoint | Corrección |
|---|---------|--------------|----------|----------|------------|
| 1 | portal-inteligencia/App.jsx | L48-49 | `credentials:'include'` en `/auth/me` | /api/auth/me | usar cliente Bearer (api.get('/auth/me')) |
| 1 | portal-inteligencia/App.jsx | L59-65 | fallback `Usuario Externo` / `demo@edarsa.com` | — | ELIMINAR; estado SIN_SESION/SESION_EXPIRADA/SIN_PERMISO |
| 1 | portal-inteligencia/App.jsx | L66-73 | fallback `Usuario Demo` / `demo@inteligencia.edarsa.com` | — | ELIMINAR |
| 2 | pages/DashboardIA.jsx | L66-69 | `credentials:'include'` | /api/inteligencia/dashboard | cliente Bearer |
| 3 | pages/VentasProductoPage.jsx | L37-40 | `credentials:'include'` | /api/inteligencia/productos | cliente Bearer |
| 4 | pages/VentasFamiliaPage.jsx | L70-73 | `credentials:'include'` | /api/inteligencia/dashboard | cliente Bearer |
| 5 | pages/VentasHorarioPage.jsx | L69-72 | `credentials:'include'` | /api/inteligencia/dashboard | cliente Bearer |
| 6 | pages/VentasCasaPage.jsx | L95-98 | `credentials:'include'` | /api/inteligencia/dashboard | cliente Bearer |
| 7 | pages/AnalisisPAXPage.jsx | L47-50 | `credentials:'include'` | /api/inteligencia/dashboard | cliente Bearer |
| 8 | pages/BenchmarkGrupoPage.jsx | L70,77,92,105 | 4× `credentials:'include'` | /api/comercial/benchmark/* | cliente Bearer |

## C. FRONTEND — MOCK / FALLBACK A ELIMINAR [EN ALCANCE]
| # | Archivo | Línea/bloque | Hallazgo | Corrección |
|---|---------|--------------|----------|------------|
| 1 | DashboardIA.jsx | L29-52 `FALLBACK_KPI` + L55 `useState(FALLBACK_KPI)` | ventas 15.71M, topProductos/topCasas inventados | estado inicial vacío + SIN_DATOS_SYNC |
| 2 | VentasProductoPage.jsx | L9-20 `FALLBACK_PRODUCTOS` + L23 `useState` | Don Julio, alcohol, ventas falsas | estado vacío + SIN_DATOS_SYNC |
| 3 | VentasFamiliaPage.jsx | L7-54 `FALLBACK_FAMILIAS` + L57/L58 | familias/% inventados, expanded hardcode | estado vacío + SIN_DATOS_SYNC |
| 4 | VentasHorarioPage.jsx | L7-53 `FALLBACK_HORARIOS` + L56 + L84-106 merge `|| FALLBACK_*` | horarios y topProductos inventados | estado vacío + SIN_DATOS_SYNC |
| 5 | VentasCasaPage.jsx | L7-78 `FALLBACK_CASAS` + L81 + L107 `Math.random` productos + L108 alcohol default `35` + L110 `Math.random` crecimiento | casas y métricas inventadas | estado vacío + SIN_DATOS_SYNC; sin random/35 |
| 6 | AnalisisPAXPage.jsx | L7-32 `FALLBACK_PAX_DATA` (porUnidad + tendenciaSemanal 100% mock) + L35 + L59-64 merge `|| prev` + L92/103/113 badges fijos `+8.3%/+15.2%/+5.7%` | PAX por unidad y tendencia semanal inventados, % fijos | estado vacío + SIN_DATOS_SYNC; sin badges fijos |

> Huérfanos NO en flujo operativo (no importados por App.jsx): `pages/VentasCasas.jsx`, `pages/VentasPax.jsx`.
> Recomendación: borrarlos (código muerto con mock). No afectan criterios de aceptación.

## D. 🚨 MOCK EN BACKEND — FUERA DEL ALCANCE "solo frontend" — REQUIERE DECISIÓN
`modules/inteligencia_comercial/routes.py`:
| Endpoint | Línea | Hallazgo | Estado |
|----------|-------|----------|--------|
| `/inteligencia/dashboard` | L333-338 | `ventas_horario` = total × **0.20/0.50/0.30** | PORCENTAJES FIJOS |
| `/inteligencia/dashboard` | L340-349 | `top_productos` = nombres inventados × % fijos | PRODUCTOS FALSOS |
| `/inteligencia/dashboard` | L351-359 | `casas_distribuidoras` = DIAGEO/etc × % fijos | FALSO |
| `/inteligencia/dashboard` | L361-368 | `ventas_familia` = Tequilas/etc × % fijos | FALSO |
| `/inteligencia/familias` | L820-830 | familias con % fijos | FALSO |

**REAL ya:** `kpis` y `ventas_por_unidad` del dashboard (vw_Comercial_KPIs_Diarios_v2_Runtime);
`/inteligencia/productos` (View_Inteligencia_Comercial = JOIN Sync_Sales + Products).
Datos REALES disponibles para reconstruir lo falso: `View_Inteligencia_Comercial` y
`Comercial_Inteligencia_VentasDetalleProducto` (poblada por el ETL NO-LIVE).

**Implicación:** los criterios "no productos falsos / no porcentajes fijos 20/50/30" **NO** se pueden
cumplir solo en frontend: si quito el mock del frontend pero el backend sigue enviando esos bloques
fabricados, las tarjetas mostrarán datos falsos del backend.

## E. NUEVO ARCHIVO
- `portal-inteligencia/api/client.js` — cliente API ÚNICO autenticado (reutiliza axios `api` +
  `getToken` de `lib/api.js`). Expone estados canónicos: OK / SIN_SESION / SESION_EXPIRADA /
  SIN_PERMISO / SIN_DATOS_SYNC / ERROR. Lo consumen las 7 páginas + App.jsx.

## F. BACKEND
- NINGÚN cambio en `/api/auth/me` (ya soporta Bearer). El único cambio backend posible es el del
  punto D, **sujeto a tu autorización**.

---

## ✅ EJECUTADO (Opción 1 autorizada por el usuario)
- **AUTH (frontend):** `App.jsx` usa el token operativo vigente (Bearer desde sessionStorage vía
  `lib/api.js`); eliminado el modo demo por completo; estados honestos SIN_SESION / SESION_EXPIRADA /
  SIN_PERMISO (componente `AuthGate`). Cliente único `portal-inteligencia/api/client.js` (Bearer +
  refresh + timeout 35s) consumido por las 7 páginas.
- **MOCK FRONTEND eliminado:** quitados todos los `FALLBACK_*`, `Math.random`, badges fijos y
  defaults (alcohol 35). Estados vacíos vía `components/EstadoVacio.jsx`. Borrados huérfanos
  `VentasCasas.jsx`/`VentasPax.jsx`.
- **MOCK BACKEND eliminado (Opción 1):** en `modules/inteligencia_comercial/routes.py` los bloques
  `ventas_horario` (20/50/30), `top_productos`, `casas_distribuidoras`, `ventas_familia` y los
  endpoints `/productos`, `/familias`, `/casas` ahora se calculan REALES desde
  `Comercial_Inteligencia_VentasDetalleProducto` (1.24M líneas, 2024-06→2026-06). `casa` viene NULL →
  bloque vacío honesto (SIN_DATOS_SYNC), nunca inventado. Familias con subfamilias reales.
- **Verificado (cURL + screenshots, sin testing_agent):** Dashboard $3.88M/3,900 PAX/cheque $2,855.52;
  Top Productos reales (RIB EYE OZ…); Por Horario real; Familia/Subfamilia real; Análisis PAX por
  unidad real; Casas → "Sin datos sincronizados"; sin demo en ninguna pantalla. Rendimiento ~2.5s
  (arranque en frío puntual ~20s cubierto por timeout 35s).
- **Pendiente (no regresión):** Benchmark Grupo muestra "sin unidades" para admin → falta sembrar
  permisos/unidades `comercial.benchmark.*` (P1 backlog, ya documentado). Cálculo `cheque_promedio`
  sigue usando `ventas_sin_propina` (decisión C2 aún abierta, fuera de este alcance).
