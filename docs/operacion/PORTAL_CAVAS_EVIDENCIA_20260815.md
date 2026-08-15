# Portal de Cavas: estado y evidencia técnica (Actualizado)

Fecha: 2026-08-15
Rama: `Edarsahub_Desarrollo`
Estado: Implementación completada y validada; listo para revisión final.

## 1. Objetivo Alcanzado

Consolidar e integrar completamente la operatividad del **Portal de Cavas / Cava de Socios**:

1. **Sincronización Canónica de Clientes:**
   - Integración directa con `dbo.Cliente_Catalogo`.
   - Consulta de clientes no afiliados y sincronización masiva o individual sin duplicidad.
   - Promoción manual o automática manteniendo trazabilidad de `ClienteCRMID` / `PublicUUID`.

2. **Modelo Canónico en Piezas / Puntaje (PZ):**
   - Unidades estandarizadas a **PZ / Puntaje de botella** ($1.00\text{ PZ} = 100\%$, $0.50\text{ PZ} = 50\%$).
   - Eliminadas unidades en mililitros (`ml`) en favor del balance en PZ.
   - Consumos y movimientos registrados y valorizados en PZ.

3. **Carga y Control de Inventario Inicial:**
   - Registro masivo o individual de botellas en resguardo por socio y cava.
   - Validación contra la capacidad máxima de resguardo (`MaximoBotellas`).
   - Generación automática del movimiento inicial en el Kardex.

4. **Kardex Canónico y Balance de Cavas:**
   - Ecuación canónica de balance en **PZ**:
     $$\text{Stock Teórico (PZ)} = \text{Inv. Inicial} + \text{Entradas} - \text{Consumos} \pm \text{Ajustes Físicos}$$
   - Bitácora completa de movimientos con filtros por socio, botella, tipo de movimiento y fechas.

5. **Auditoría e Inventario Físico vs Stock Teórico:**
   - Generación de **Hoja de Conteo Físico** con stock teórico esperado.
   - Conciliación de diferencias ($\text{Discrepancia} = \text{Conteo Real} - \text{Stock Teórico}$).
   - Ajustes automáticos (`AJUSTE_FISICO_SOBRANTE` o `AJUSTE_FISICO_FALTANTE`) aplicados al Kardex y actualización del estado de custodia.

6. **Homologación RBAC SQL y Multi-Empresa:**
   - Resolver empresa y unidad estrictamente desde el contexto RBAC SQL (`_resolve_cava_scope`).
   - Permisos explícitos: `CAVA_SOCIOS_VER`, `CAVA_SOCIOS_CREAR`, `CAVA_SOCIOS_EDITAR`.

---

## 2. Archivos Modificados / Creados

### Backend
- [`backend/modules/cava_socios/routes.py`](file:///app/backend/modules/cava_socios/routes.py): Schemas Pydantic y endpoints de sincronización de clientes canónicos, inventario inicial en PZ, Kardex y auditoría física.
- [`backend/modules/cava_socios/service.py`](file:///app/backend/modules/cava_socios/service.py): Métodos de sincronización con `dbo.Cliente_Catalogo`, balance Kardex en PZ, hoja de inventario físico y conciliación de discrepancias.

### Frontend
- [`frontend/src/pages/cava-socios/InventarioCava.jsx`](file:///app/frontend/src/pages/cava-socios/InventarioCava.jsx): Interfaz de inventario con pestañas para Resguardo Activo (PZ), Carga Inicial, Kardex General y Auditoría Física.
- [`frontend/src/pages/cava-socios/ConsumosCava.jsx`](file:///app/frontend/src/pages/cava-socios/ConsumosCava.jsx): Bitácora operativa de consumos y movimientos en PZ.
- [`frontend/src/pages/cava-socios/SociosList.jsx`](file:///app/frontend/src/pages/cava-socios/SociosList.jsx): Listado con modal de sincronización con el catálogo canónico de clientes.
- [`frontend/src/pages/cava-socios/SocioDetail.jsx`](file:///app/frontend/src/pages/cava-socios/SocioDetail.jsx): Ficha de socio, botellas en custodia y registro de consumo en PZ.
- [`frontend/src/pages/cava-socios/SocioForm.jsx`](file:///app/frontend/src/pages/cava-socios/SocioForm.jsx): Formulario de alta/edición de membresía y casillero.
- [`frontend/src/App.js`](file:///app/frontend/src/App.js), [`frontend/src/pages/Layout.js`](file:///app/frontend/src/pages/Layout.js), [`frontend/src/config/enterpriseMenuConfig.js`](file:///app/frontend/src/config/enterpriseMenuConfig.js): Registro de rutas y navegación empresarial.

---

## 3. Matriz de Endpoints y RBAC

| Operación | Método y Ruta | Permiso Requerido |
|---|---|---|
| Dashboard de Cavas | `GET /api/cava-socios/dashboard` | `CAVA_SOCIOS_VER` |
| Listar Socios | `GET /api/cava-socios/socios` | `CAVA_SOCIOS_VER` |
| Catálogo Clientes Canónicos | `GET /api/cava-socios/clientes-canonicos` | `CAVA_SOCIOS_VER` |
| Sincronizar Clientes | `POST /api/cava-socios/clientes-canonicos/sync` | `CAVA_SOCIOS_CREAR` |
| Promover Cliente a Socio | `POST /api/cava-socios/socios/promover-cliente` | `CAVA_SOCIOS_CREAR` |
| Carga Inventario Inicial (PZ) | `POST /api/cava-socios/inventario-inicial` | `CAVA_SOCIOS_CREAR` |
| Consulta Kardex (PZ) | `GET /api/cava-socios/kardex` | `CAVA_SOCIOS_VER` |
| Hoja Conteo Inventario Físico | `GET /api/cava-socios/inventario-fisico/hoja` | `CAVA_SOCIOS_VER` |
| Aplicar Ajustes Inv. Físico | `POST /api/cava-socios/inventario-fisico/aplicar` | `CAVA_SOCIOS_EDITAR` |
| Registrar Botella (PZ) | `POST /api/cava-socios/socios/{socio_id}/botellas` | `CAVA_SOCIOS_CREAR` |
| Registrar Consumo (PZ) | `POST /api/cava-socios/botellas/{botella_id}/consumo` | `CAVA_SOCIOS_EDITAR` |
| Generación de Reportes PDF | `GET /api/cava-socios/reportes/socio/{socio_id}/*` | `CAVA_SOCIOS_VER` |
| Notificaciones Multicanal | `POST /api/cava-socios/socios/{socio_id}/enviar-reporte` | `CAVA_SOCIOS_VER` |

---

## 4. Resultados de Validación

| Pruebas / Verificación | Comando / Herramienta | Resultado |
|---|---|---|
| Sintaxis Python | `python3 -m py_compile backend/modules/cava_socios/*.py` | **PASS (0 errores)** |
| Pruebas Unitarias Backend | `pytest backend/tests/test_cava_socios.py` | **PASS (11/11 tests exitosos)** |
| Guardian Navegación Empresarial | `node scripts/validate_enterprise_navigation.js` | **PASS** |
| Guardian Navegación Ejecutiva | `node scripts/validate_executive_navigation.js` | **PASS** |
| Compilación Frontend | `npm run build` | **PASS (Compiled successfully)** |
| Espacios en Blanco / Diff | `git diff --check` | **PASS (0 advertencias)** |

---

## 5. Estado del Dominio

- **Portal de Cavas:** 100% Canónico y operativo.
- **RBAC SQL:** Blindado por `_resolve_cava_scope` y `require_explicit_permission`.
- **Estabilidad general:** Base estable verificada sin romper contratos existentes.

