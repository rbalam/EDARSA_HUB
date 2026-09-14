# EDARSAHUB Services - Gate 0B Repository Contract Discovery R1

## 1. Certificacion de entrada
Gate 0A termino con `CERTIFIED_READ_ONLY`, `quality_gate=PASS`, `percent_complete=100`, `blockers=[]`, `files_changed=[]` y `production_touched=false`. La identidad SQL fue `EDARSAHUB / HRLectura / HRLectura`.

## 2. Decision arquitectonica
EDARSAHUB Services se construye como satelite/bounded context y no como crecimiento de `backend/core`. BOS conserva identidad, RBAC, empresas/unidades, documentos, finanzas, notificaciones y otros contratos transversales. Cada vertical consume esos contratos y agrega solo delta de dominio.

## 3. REUSE - identidad y maestros
### 3.1 Persona
- `dbo.Gobierno_Persona` es la identidad transversal de persona.
- `dbo.Gobierno_PersonaVinculo` enlaza persona con `Usuario_Catalogo`, `Cliente_Catalogo`, `Proveedor_Catalogo` y contactos tipados.
- Repositorio canonico observado: `backend/modules/catalogo_ampliado/repository.py`, SQL-first.

Decision: prestadores independientes, profesionistas, trabajadores, tecnicos, arquitectos, ingenieros, vendedores y participantes deben referenciar `Gobierno_Persona` cuando semanticamente sean persona. Prohibido crear `Services_Personas` como segundo maestro.

### 3.2 Clientes/proveedores
Reutilizar `Cliente_Catalogo`, `Cliente_Contactos`, `Cliente_Direcciones` y maestros de proveedor existentes. Services puede mantener relacion/rol de dominio, pero no duplicar datos maestros.

### 3.3 Empresas/unidades
Reutilizar `Sistema_Empresas`, `Sistema_Sucursales`, `Unidades_Negocio` y helpers canonicos. Empresas prestadoras externas no deben forzarse artificialmente a ser una empresa interna BOS; modelar relacion externa cuando corresponda.

## 4. REUSE - RBAC y seguridad
Reutilizar `Usuario_Catalogo`, `Usuario_EmpresasAsignacion`, `Usuario_AlmacenesAsignacion`, `Usuario_SucursalesAsignacion`, `Usuario_RolesAsignacion`, `Usuario_RolesContexto`, `Sistema_RBAC_Permisos`, `Sistema_RBAC_Roles`, `Sistema_RBAC_RolesPermisos` y vistas/helpers efectivos. No crear auth, roles ni permisos paralelos.

## 5. REUSE/EXTEND - expedientes, eventos y comisiones
Gate 0A encontro `COA_Expedientes`, `COA_ExpedienteEventos`, `COA_ExpedienteReferencias`, `COA_ReglasComision`, `COA_ReglasComisionCondiciones` y `COA_ComisionAplicada`. El repositorio documenta reglas de comision versionadas y condiciones configurables.

Decision: el motor de comisiones de ventas inmobiliarias y otros esquemas de Services debe evaluar primero extension/reutilizacion de COA, no crear un segundo motor. Services puede requerir adaptadores/relaciones de dominio y reglas adicionales (devengo, split, clawback, hitos), pero solo despues de comprobar incompatibilidades reales.

## 6. REUSE/EXTEND - activos, mantenimiento y ordenes de trabajo
Gate 0A encontro `ActivoFijo_Activos`, `ActivoFijo_OrdenesTrabajo`, `ActivoFijo_OrdenTrabajoCostos`, `ActivoFijo_PlanesMantenimiento`, `ActivoFijo_Medidores`, ubicaciones, movimientos y autorizaciones.

Decision: `Work Order`, mantenimiento, equipos, maquinaria y costos de intervencion no deben duplicarse a ciegas. Gate 1 debe decidir si Services consume/expande estos contratos o introduce una orden de servicio de dominio con integracion explicita.

## 7. REUSE - comercial
Reutilizar contratos existentes de `Venta_Cotizaciones`, `Venta_Pedidos`, `CRM_Leads`, `CRM_Oportunidades` y procedimientos comerciales existentes cuando su semantica aplique. No crear un CRM paralelo para Services.

## 8. REUSE - documentos y evidencia
Primera opcion: Gobierno documental (`Gobierno_Documento`, versionado/movimientos/tipos) y patrones de evidencia existentes. Construction, Land, Legal, Healthcare y otros verticales deben conservar solo la relacion semantica con su agregado cuando sea suficiente.

## 9. REUSE - inventarios, materiales y costos
Gate 0A encontro inventarios/almacenes/materiales/costos y automatizaciones relacionadas. Construction/Fabrication deben consumir maestros y movimientos canonicos donde corresponda. BOM, despiece, optimizacion de corte y sobrantes reutilizables son delta especializado, no razon para duplicar inventario.

## 10. EXTEND - Universal Services
Candidatos de delta de dominio:
- perfil/rol de prestador asociado a persona u organizacion;
- especialidades, habilidades y credenciales;
- disponibilidad y cobertura;
- service catalog;
- engagement y motores `Appointment`, `Case`, `Project`, `Work Order`, `Event`, `Recurrence`;
- SLA y evidencia de ejecucion.

Los nombres fisicos se definen en Gate 1/2; no se autoriza DDL todavia.

## 11. EXTEND/NEW - Construction
Candidatos:
- obra/proyecto especializado;
- etapas, frentes, partidas, conceptos;
- contratistas/subcontratistas/cuadrillas;
- avance fisico, generadores, estimaciones y change orders;
- relacion con materiales, activos, compras y costos canonicos;
- calidad, seguridad y entrega.

No crear un ERP financiero dentro de Construction.

## 12. EXTEND/NEW - Fabrication
Delta especializado candidato:
- BOM/configuracion parametrica;
- despiece;
- optimizacion de barras/tableros/vidrio;
- corte;
- sobrantes reutilizables y merma;
- orden de fabricacion e instalacion.

Inventario, materiales, proveedores y costos se reutilizan.

## 13. EXTEND/NEW - Interiors and Design
Delta especializado candidato:
- espacios;
- brief/moodboard/layout;
- especificacion de materiales, mobiliario, iluminacion y equipos;
- propuestas visuales, renders e imagen/video;
- alternativas y sustituciones conectadas a costo/disponibilidad.

La IA visual no sustituye plano tecnico ni documento aprobado.

## 14. EXTEND/NEW - Real Estate and Land
Delta especializado candidato:
- `LandParcel` jerarquico con lineage parent-child;
- predio/macrolote/fraccionamiento/privada/manzana/lote/sublote y areas no vendibles configurables;
- GIS/geometria/superficie;
- subdivisiones, fusiones, segregaciones y relotificaciones como eventos;
- conciliacion superficie juridica/catastral/CAD-GIS/comercial;
- escrituras, registro, clave catastral y relacion con notario/notaria;
- inventario comercial, apartados, promesas, compraventa, financiamiento/cartera y escrituracion.

Finanzas BOS conserva pagos/cobranza/bancos; Land conserva hechos inmobiliarios y referencias.

## 15. CONSOLIDATE
- Comisiones: consolidar con COA antes de crear otra capacidad.
- Ordenes de trabajo/mantenimiento: consolidar semanticamente con ActivoFijo donde corresponda.
- Persona/cliente/proveedor: consolidar en maestros existentes mediante vinculos/roles, nunca copiar.
- Documentos: consolidar en Gobierno documental salvo requerimiento regulatorio justificado.

## 16. DO_NOT_CREATE
- segundo maestro de personas;
- segundo CRM;
- segundo RBAC/auth/menu;
- segundo motor generico de comisiones;
- segundo inventario;
- segundo sistema financiero/bancario;
- tablas separadas por profesion/oficio (`Plomeros`, `Electricistas`, `Arquitectos`, etc.);
- logica Services dentro de `backend/core`;
- MongoDB como fuente operativa nueva;
- dashboards administrativos LIVE.

## 17. Modelo de ownership candidato
- BOS/Gobierno: persona, documentos, empresas/unidades y contratos transversales.
- Auth/RBAC: usuarios/permisos/alcances.
- Comercial/CRM: leads, oportunidades, clientes, cotizaciones/pedidos cuando aplique.
- Finanzas: pagos, bancos, conciliacion y contabilidad.
- Operaciones/Inventarios: materiales, almacenes y movimientos.
- ActivoFijo: activos/mantenimiento/OT donde semanticamente corresponda.
- COA: reglas/comisiones/expedientes reutilizables donde exista compatibilidad.
- Services: engagement y reglas verticales.

## 18. Siguiente gate
Gate 1 debe producir `Enterprise Capability Map + Bounded Context Ownership Matrix` y resolver formalmente cada capacidad como `REUSE / EXTEND / CONSOLIDATE / NEW / DO_NOT_CREATE`, con dependencias y fronteras. No ejecutar DDL ni implementar UI todavia.
