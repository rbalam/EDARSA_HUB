# Portal de Cavas: estado y evidencia técnica (Actualizado)

Fecha: 2026-08-15
Rama: `Edarsahub_Desarrollo`
HEAD auditado: `2cf9a3248d66a1b5626d1e01b2ce244ae55da725`
Estado: Implementación completada y verificada localmente; sin commit, push ni deploy.

## 1. Objetivo Alcanzado

Integrar completamente el **Portal de Cavas** con el modelo canónico y RBAC de EDARSAHUB:

- Retirar completamente identificadores de empresa hardcodeados (`EMPRESA_ID`).
- Homologar vistas frontend (`SociosList.jsx`, `SocioDetail.jsx`, `SocioForm.jsx`, `CavaSociosDashboard.jsx`) al contrato `unidad_negocio_pk`.
- Implementar endpoint de edición de socio (`PUT /api/cava-socios/socios/{socio_id}`) en backend.
- Envolver todas las páginas con `CorporateFiltersProvider scope="cava_socios"`.
- Resolver empresa y unidad estrictamente desde el contexto RBAC SQL en backend (`_resolve_cava_scope`).
- Crear suite de pruebas unitarias backend (`backend/tests/test_cava_socios.py`).
- Ejecutar y superar `yarn build` y `pytest`.

## 2. Archivos Modificados / Creados

### Backend
- `backend/modules/cava_socios/routes.py`: Agregado `SocioUpdate` Pydantic model y endpoint `@router.put("/socios/{socio_id}")` con permiso `CAVA_SOCIOS_EDITAR`.
- `backend/modules/cava_socios/service.py`: Agregado método `actualizar_socio()` en `CavaSociosService` para actualizar registros en `CavaSocios_Socios`.
- `backend/tests/test_cava_socios.py`: Creada suite de pruebas unitarias para esquemas, resolución de contexto RBAC, endpoints y servicio de cavas (11 tests).

### Frontend
- `frontend/src/pages/cava-socios/SociosList.jsx`: Homologado con `CorporateFiltersProvider scope="cava_socios"` y parámetro `unidad_negocio_pk`.
- `frontend/src/pages/cava-socios/SocioDetail.jsx`: Eliminada referencia hardcodeada `EMPRESA_ID`, homologadas todas las llamadas API (alta botella, registrar consumo, descarga PDF y envíos de reportes) con `unidad_negocio_pk`, agregada exportación con `CorporateFiltersProvider`.
- `frontend/src/pages/cava-socios/SocioForm.jsx`: Conectada creación (`POST`) y edición (`PUT`) de socio mediante `unidad_negocio_pk`.

## 3. Matriz de Endpoints y RBAC

| Flujo | Método y Ruta | Permiso Explicito |
|---|---|---|
| Dashboard | `GET /api/cava-socios/dashboard` | `CAVA_SOCIOS_VER` |
| Listar socios | `GET /api/cava-socios/socios` | `CAVA_SOCIOS_VER` |
| Obtener socio | `GET /api/cava-socios/socios/{socio_id}` | `CAVA_SOCIOS_VER` |
| Crear socio | `POST /api/cava-socios/socios` | `CAVA_SOCIOS_CREAR` |
| Actualizar socio | `PUT /api/cava-socios/socios/{socio_id}` | `CAVA_SOCIOS_EDITAR` |
| Registrar botella | `POST /api/cava-socios/socios/{socio_id}/botellas` | `CAVA_SOCIOS_CREAR` |
| Registrar consumo | `POST /api/cava-socios/botellas/{botella_id}/consumo` | `CAVA_SOCIOS_EDITAR` |
| Ficha PDF | `GET /api/cava-socios/reportes/socio/{socio_id}/ficha` | `CAVA_SOCIOS_VER` |
| Consumos PDF | `GET /api/cava-socios/reportes/socio/{socio_id}/consumos` | `CAVA_SOCIOS_VER` |
| Estado de cuenta PDF | `GET /api/cava-socios/reportes/socio/{socio_id}/estado-cuenta` | `CAVA_SOCIOS_VER` |
| Enviar reporte | `POST /api/cava-socios/socios/{socio_id}/enviar-reporte` | `CAVA_SOCIOS_VER` |
| Enviar todos | `POST /api/cava-socios/socios/{socio_id}/enviar-todos-reportes` | `CAVA_SOCIOS_VER` |

## 4. Resultados de Validación

| Pruebas / Verificación | Comando / Herramienta | Resultado |
|---|---|---|
| Sintaxis Python | `python3 -m py_compile backend/modules/cava_socios/*.py backend/tests/test_cava_socios.py` | **PASS (0 errores)** |
| Pruebas unitarias backend | `PYTHONPATH=backend pytest backend/tests/test_cava_socios.py` | **PASS (11/11 tests exitosos)** |
| Guardian de navegación empresarial | `node scripts/validate_enterprise_navigation.js` | **PASS** |
| Guardian ejecutivo | `node scripts/validate_executive_navigation.js` | **PASS** |
| Compilación Frontend | `yarn build` | **PASS (Compiled successfully)** |

## 5. Estado del Dominio

- **Portal de Cavas:** 100% Canónico.
- **RBAC SQL:** Blindado por `_resolve_cava_scope` y `require_explicit_permission`.
- **Estabilidad general:** Base estable verificada sin romper contratos existentes.
- **Commit / Push / Deploy:** Pendiente de autorización explícita del usuario.
