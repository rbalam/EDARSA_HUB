# AUDITORÍA — Gobierno de Acceso Comercial, Benchmark y Confidencialidad
Fecha: 2026-06-09 · Régimen: NO-LIVE · NO MongoDB (fuente: EDARSAHUB SQL) · Sin hardcode
Estado: **AUDITORÍA + PROPUESTA — NO IMPLEMENTADO (esperando autorización; sin crear tablas)**

---

## 1. RESPUESTA A LAS 16 VALIDACIONES OBLIGATORIAS

| # | Validación | Estado | Evidencia / Detalle |
|---|------------|--------|---------------------|
| 1 | ¿Existe tabla/campo de **grupo corporativo**? | ❌ NO | `Sistema_Empresas` NO tiene `GrupoCorporativoID`. No hay `Sistema_GruposCorporativos`. Solo `Cliente_Grupos` (grupos de CLIENTES del CRM, no de propiedad) y `RH_GruposNomina` (nómina). |
| 2 | ¿Relación empresa → grupo corporativo? | ❌ NO | No existe. La cúspide actual es Empresa. |
| 3 | ¿Relación unidad → empresa → grupo? | ⚠️ PARCIAL | `Unidades_Negocio` (id, codigo, nombre, server_id, sucursal_origen_id, system_type) **no** tiene empresa_id. El vínculo unidad→empresa es **indirecto** vía `server_id` → `Sistema_EmpresasServidores` → `Sistema_Empresas`. Falta el nivel grupo. |
| 4 | ¿Permisos por grupo? | ❌ NO | No hay scope por grupo (no existe el grupo). |
| 5 | ¿Permisos por unidad? | ✅ SÍ | `Usuario_RolesContexto` (121 filas): Usuario→Rol→**EmpresaID/UnidadNegocioID/SucursalID**. `Usuario_EmpresasAsignacion` (38), `Usuario_SucursalesAsignacion`, `Usuario_ServidoresAsignacion`, `Usuario_AlmacenesAsignacion`. |
| 6 | ¿Usuarios externos con scopes? | ⚠️ PARCIAL | Infra de portal externo existe: `Cliente_UsuariosPortal`, `Proveedor_UsuariosPortal`, `Portal_Proveedores`, `Cliente_RolUsuarioPortal`, `Proveedor_RolUsuarioPortal`, flag `EsUsuarioPortal` en `Usuario_Catalogo`. **Pero NO hay scope de benchmark/comparables para externos.** |
| 7 | ¿Forma de clasificar empresas externas comparables? | ❌ NO | No hay clasificación sectorial/segmento/comparable. Existe `Comercial_Competidores` (3 filas) y `Comercial_CompetidoresCatalogo` (competencia de precios, no benchmark de desempeño propio anónimo). |
| 8 | ¿Datos suficientes para benchmark interno? | ✅ SÍ (agregado) | `Comercial_KPIs_Diarios_v2` = **3,405 filas** por unidad/día con ventas_total, tickets, pax, ticket_promedio, propinas, ventas_abiertas/cerradas. 5 unidades activas (130MID, CIENFUEGOS, ESTELAR, 130QRO, ORIGEN). |
| 9 | ¿Datos suficientes para benchmark sectorial? | ❌ NO | Solo 1 grupo (EDARSA). No hay datos de otros grupos/empresas externas para sector. `Comercial_PricingBenchmarkProducto` = 1 fila. |
| 10 | ¿Riesgos de identificación indirecta? | ⚠️ SÍ | Con 5 unidades, cualquier comparativo "unidad vs unidad" sin enmascarar revela identidad. K-anonymity necesaria si se abre a externos. |
| 11 | ¿Endpoints exponen nombres indebidamente? | ⚠️ SÍ (potencial) | Endpoints comerciales devuelven `unidad_negocio_nombre`, `sucursal_nombre`, `NombreEmpresa` en claro. Hoy sin riesgo (cada usuario ve solo lo suyo) pero **no hay capa de enmascaramiento** para escenarios de comparación. |
| 12 | ¿Frontend recibe datos que backend debería enmascarar? | ⚠️ SÍ | No existe capa de anonimización en backend; todo nombre que llega al front llega en claro. |
| 13 | ¿Exportaciones podrían filtrar nombres reales? | ⚠️ SÍ | Export de reportes hoy entrega nombres reales (correcto para alcance propio; faltaría gobernar export en benchmark). |
| 14 | ¿Drill-down respeta confidencialidad? | ⚠️ N/A | No hay drill-down cross-unidad/cross-grupo todavía. |
| 15 | ¿Ticket/comanda bloqueado para terceros? | ✅ implícito | `Comercial_Inteligencia_VentasDetalleProducto` (detalle ticket) está **VACÍA (0 filas)** y los endpoints filtran por server_id permitido. No hay acceso a tickets de terceros hoy. |
| 16 | ¿Costo/margen bloqueado para externos sin permiso? | ⚠️ PARCIAL | `costos_margenes` ya tiene RBAC canónico (es_aprobador/lectura), pero no distingue "externo" ni "tercero". |

---

## 2. INVENTARIO DE LO QUE YA EXISTE (REUTILIZAR)

### RBAC granular (robusto, SQL-First)
- **Permisos compuestos** = `Usuario_Modulos` (≈58 módulos, soporta jerarquía con punto: `crm.clientes`, `cava_socios.botellas`) × `Usuario_Acciones` (16: VER, CREAR, EDITAR, ELIMINAR, AUTORIZAR, APLICAR, REVERTIR, CONFIGURAR, ENVIAR, GESTIONAR, ADMIN, EJECUTAR, CANCELAR, RECHAZAR, **EXPORTAR**, **IMPORTAR**). Código: `MODULO_ACCION`.
- Módulo **`INTELIGENCIA_COMERCIAL`** YA existe.
- `Usuario_PermisosRolModulo` (459 filas) con flags **`RestriccionPropietario`**, **`RestriccionSucursal`**, `RequiereAutorizacion`, `NivelAutorizacionRequerido` → infraestructura de restricción a nivel permiso ya disponible.
- **23 roles** con `NivelJerarquia`: SUPERADMIN(100), ADMIN(90), CRM_ADMIN(90), ADMIN_COMERCIAL(85), DIRECCION(80), GERENTE(70), CRM_AUDIT(70), GERENTE_OPS(60), GERENTE_UNIDAD(55), SUPERVISOR/CRM_EJEC(50), CONFIGURADOR_COMERCIAL(45), ANALISTA_COMERCIAL(40), AUDITOR(30), OPERADOR(20), VISOR_COMERCIAL/USUARIO(10), VISOR(5), GERENCIA/COMPRAS/VENTAS/TESORERIA(0).
- Helpers canónicos (sin hardcode): `es_admin`, `es_superadmin`, `es_supervisor_o_superior`, `es_aprobador`, `puede_solicitar_comercial`, `tiene_acceso_lectura_comercial`, `get_role_code`, `get_role_level`.

### Scope corporativo
- `resolve_unidad_scope(user)` → `allowed_server_ids` vía `get_user_empresas_permitidas` → `get_servers_for_empresas`. Lista vacía = acceso total (admin).
- `CorporateFilterService` / `UnidadesService` (catálogo canónico de unidades).
- `Usuario_RolesContexto` (Usuario↔Rol↔Empresa/Unidad/Sucursal) = mecanismo de scope contextual ya poblado (121 filas).

### Datos disponibles (NO-LIVE)
- ✅ `Comercial_KPIs_Diarios_v2` (3,405) → base sólida para **benchmark interno agregado** (ticket promedio, PAX, ventas/hora-turno requiere detalle).
- ⚠️ `Comercial_Inteligencia_VentasDetalleProducto` (0 filas) → necesaria para benchmark por producto/casa/marca/turno. **VACÍA**.
- ⚠️ `Comercial_KPIs_Mensuales_v2` (0 filas) → vacía.

---

## 3. BRECHAS (NO EXISTE — requiere construcción)

- **A. Entidad Grupo Corporativo**: no existe nivel sobre Empresa. Decisión pendiente del usuario (ver §5).
- **B. Permisos de benchmark** (`comercial.benchmark.grupo.*`, `comercial.benchmark.sector.*`): NO existen, pero se materializan como **filas** en `Usuario_Modulos`+`Usuario_Acciones`+`Usuario_PermisosRolModulo` → **sin tablas nuevas**.
- **C. Capa de anonimización/enmascaramiento en backend**: NO existe. Debe construirse como servicio central (regla de centralización) que recibe `(rows, user, scope)` y devuelve etiquetas "Unidad comparable A / Promedio grupo / Benchmark sector" según permiso. **Frontend nunca recibe nombres reales sin permiso.**
- **D. Clasificación de comparables externos + k-anonymity**: NO existe (y sin datos externos hoy). Diferir hasta tener datos/contratos.
- **E. Datos detallados de ventas** vacíos → benchmark a nivel producto/casa/marca/turno no tiene insumo hasta poblar `VentasDetalleProducto` (o derivar de otra fuente NO-LIVE).

---

## 4. MATRIZ DE VISIBILIDAD PROPUESTA (borrador, por tipo de usuario)

Leyenda: ✅ permitido · ⛔ prohibido por defecto · 🔒 solo con permiso explícito · Anon = nivel anonimización mínimo.

| Capacidad | SUPERADMIN | DIRECCION/ADMIN_COMERCIAL | GERENTE_UNIDAD | ANALISTA_COMERCIAL | AUDITOR | Externo Proveedor/Casa | Socio/Inversionista | Cliente autorizado |
|-----------|-----------|---------------------------|----------------|--------------------|---------|------------------------|---------------------|--------------------|
| 1 Entrar al portal | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 Ver unidades propias | ✅ | ✅ (grupo) | ✅ (su unidad) | 🔒 scope | ✅ (lectura) | 🔒 scope | 🔒 scope | 🔒 scope |
| 3 Nombres unidades propias | ✅ | ✅ | ✅ | 🔒 | ✅ | ⛔ | 🔒 | ⛔ |
| 4 Ver unidades hermanas | ✅ | ✅ | comparado anónimo | 🔒 | ✅ | ⛔ | anónimo | ⛔ |
| 5 Nombres unidades hermanas | ✅ | ✅ 🔒 | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ |
| 6 Benchmark grupo anónimo | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 | ✅ | 🔒 |
| 7 Benchmark sectorial | ✅ | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | ⛔ |
| 8 Nombres empresas externas | 🔒 contrato | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| 9 Nombres unidades externas | 🔒 contrato | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| 10 Ver producto | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 (su casa/marca) | 🔒 | 🔒 |
| 11 Ver casa/marca/proveedor | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 (lo suyo) | 🔒 | 🔒 |
| 12 Ver costo/margen | ✅ | 🔒 | 🔒 | 🔒 | ✅ (lectura) | ⛔ | 🔒 | ⛔ |
| 13 Ticket propio | ✅ | ✅ | ✅ | 🔒 | ✅ | ⛔ | ⛔ | ⛔ |
| 14 Ticket otras unidades propias | ✅ | ✅ | ⛔ | ⛔ | ✅ | ⛔ | ⛔ | ⛔ |
| 15 Ticket de terceros | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| 16 Exportar | ✅ | ✅ | 🔒 | 🔒 | ✅ | 🔒 | 🔒 | ⛔ |
| 17 Datos técnicos (server_id/host/RFC) | ✅ (admin) | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ | ⛔ |
| 18 Anon mínima requerida | ninguna | nombres propios | nombres propios / resto anónimo | scope anónimo | nombres (lectura) | enmascarado | agregado/anónimo | agregado |

---

## 5. DECISIONES REQUERIDAS DEL USUARIO (antes de implementar)

1. **Grupo Corporativo**: ¿se crea el nivel? Opciones:
   - (a) Nueva tabla `Sistema_GruposCorporativos` + `GrupoCorporativoID` en `Sistema_Empresas` (requiere DDL → tu autorización).
   - (b) Tratar la Empresa como "grupo" provisional (todas las unidades EDARSA = 1 grupo) sin DDL, y diferir el grupo real.
2. **Permisos benchmark**: aprobar el set propuesto (`comercial.benchmark.grupo.*` / `comercial.benchmark.sector.*`) materializado como módulo(s) `COMERCIAL_BENCHMARK` + acciones existentes (VER/EXPORTAR), **sin tablas nuevas**.
3. **Capa de anonimización backend**: aprobar construir servicio central `comercial_confidencialidad/anonimizer` (regla de centralización) que enmascara nombres/IDs técnicos según permiso, antes de responder.
4. **Datos detallados vacíos** (`VentasDetalleProducto` 0 filas): ¿poblar esa tabla (job de sync NO-LIVE) o construir benchmark v1 solo con `KPIs_Diarios_v2` (nivel unidad/día) y diferir producto/casa/turno?
5. **Benchmark sectorial**: hoy NO hay datos externos ni contratos. ¿Diferir sector y entregar primero **benchmark interno de grupo anónimo** (que sí tiene datos)?

---

## 6. PLAN DE IMPLEMENTACIÓN PROPUESTO (por fases, tras autorización)

- **Fase G1 — Permisos benchmark (sin DDL)**: seed de módulo/acciones + asignación a roles. Tests pytest.
- **Fase G2 — Servicio central de anonimización/enmascaramiento (backend)**: `AnonymizerService` + `ConfidentialityScope` (qué nombres puede ver el usuario). Tests de no-fuga.
- **Fase G3 — Endpoint Benchmark Interno (agregado)**: `/api/comercial/benchmark/interno` usando `KPIs_Diarios_v2`; devuelve valor propio, promedio/mediana/p25/p75 grupo, diferencia abs/%, percentil, cobertura, **nivel_anonimizacion_aplicado, permiso_usado, advertencias, source_table, generated_at**.
- **Fase G4 — Frontend Reportador comparativo** (consume G3, respeta enmascaramiento).
- **Fase G5 (diferida)** — Grupo corporativo real + benchmark sectorial + k-anonymity (cuando haya DDL autorizado y datos externos).

> Cada respuesta de comparación incluirá SIEMPRE: valor_propio, valor_benchmark, diferencia_absoluta, diferencia_porcentual, posicion_relativa, percentil, cobertura, nivel_anonimizacion_aplicado, permiso_usado, advertencias, source_table, generated_at (criterios 46–54).
