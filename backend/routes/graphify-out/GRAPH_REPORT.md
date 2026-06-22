# Graph Report - /app/backend/routes  (2026-06-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 86 nodes · 129 edges · 21 communities (8 shown, 13 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ded4bc56`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]

## God Nodes (most connected - your core abstractions)
1. `_get_user_by_id()` - 8 edges
2. `get_current_intel_user()` - 8 edges
3. `_row_to_user()` - 6 edges
4. `_get_user_by_email()` - 6 edges
5. `login_intel()` - 6 edges
6. `_query()` - 5 edges
7. `_write()` - 5 edges
8. `Request` - 5 edges
9. `get_current_supplier_dual()` - 5 edges
10. `login_supplier()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `get_current_intel_user()` --references--> `Any`  [EXTRACTED]
  portal_inteligencia.py → portal_inteligencia.py  _Bridges community 0 → community 3_
- `require_portal_admin()` --references--> `Request`  [EXTRACTED]
  portal_proveedores.py → portal_proveedores.py  _Bridges community 5 → community 4_

## Import Cycles
- None detected.

## Communities (21 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (19): Any, admin_actualizar_usuario(), admin_crear_usuario(), admin_eliminar_usuario(), admin_listar_usuarios(), _clear_intel_cookie(), _create_intel_token(), _get_user_by_email() (+11 more)

### Community 1 - "Community 1"
Cohesion: 0.22
Nodes (11): clear_portal_auth_cookie(), create_portal_token(), login_supplier(), logout_supplier(), Response, Establece la cookie httpOnly para el portal de proveedores.     Cookie separada, Elimina la cookie del portal de proveedores., Crea un JWT token para proveedores (+3 more)

### Community 2 - "Community 2"
Cohesion: 0.25
Nodes (7): approve_supplier(), init_portal_db(), Rutas del Portal de Proveedores NO modifica nada de EDARSA HUB - Router completa, Aprueba o rechaza un proveedor.          P0-PORTAL-PROVEEDORES-AUTH-01: Requiere, Inicializa la conexión a la base de datos para el portal, Registro de nuevo proveedor, register_supplier()

### Community 3 - "Community 3"
Cohesion: 0.43
Nodes (7): _extract_intel_token(), get_current_intel_user(), intel_portal_guard(), me_intel(), Request, Resuelve el usuario externo de Inteligencia desde cookie/Bearer (type=portal_int, Permite acceso a los endpoints de Inteligencia a:       - Usuarios INTERNOS del

### Community 4 - "Community 4"
Cohesion: 0.38
Nodes (7): get_current_supplier_dual(), get_supplier_dual_dep(), get_supplier_profile(), Request, FASE AUTH-SECURITY-01: Obtiene proveedor desde Header O Cookie.     Prioridad: H, Dependencia wrapper para usar con Depends()., Obtiene el perfil del proveedor actual.          FASE AUTH-SECURITY-01: Soporta

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): HTTPAuthorizationCredentials, Dependency para endpoints admin del Portal de Proveedores.          Requiere:, require_portal_admin()

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (3): Sube una factura XML (y opcionalmente PDF), upload_invoice(), UploadFile

## Knowledge Gaps
- **2 isolated node(s):** `HTTPAuthorizationCredentials`, `UploadFile`
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `require_portal_admin()` connect `Community 5` to `Community 2`, `Community 4`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `upload_invoice()` connect `Community 6` to `Community 2`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `login_supplier()` connect `Community 1` to `Community 2`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `Portal de Inteligencia Comercial - EXTERNO =====================================`, `Resuelve el usuario externo de Inteligencia desde cookie/Bearer (type=portal_int`, `Permite acceso a los endpoints de Inteligencia a:       - Usuarios INTERNOS del` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._