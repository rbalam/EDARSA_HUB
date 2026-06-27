# BLUEPRINT EDARSAHUB HOSPITALITY V1

## Principio
EDARSAHUB Hospitality es un satélite nativo del ERP EDARSAHUB. No es sistema separado.

## Máximas
- No romper producción.
- No MongoDB.
- No conexión LIVE operativa.
- SQL Server como fuente única.
- No duplicar usuarios, RBAC, catálogos, conexiones, endpoints ni lógica.
- Usar unidad_negocio_pk.
- Reutilizar filtros corporativos.
- Reutilizar scheduler/jobs.
- Reutilizar notificaciones.
- Reutilizar Comandero/POS para Room Service.
- Reutilizar Finanzas, Contabilidad, Nómina, Compras, Inventarios y Proveedores.
- Automatizar todo lo que pueda ejecutar el sistema con seguridad.
- Multidioma transversal a todo EDARSAHUB.
- Multiconectividad mundial configurable por cliente.
- Activar solo servicios usados por cada cliente para evitar ruido operativo.

## Módulos propuestos
- Dashboard Hospitality
- Reservas
- Calendario Maestro
- Huéspedes / Guest 360
- Recursos Reservables
- Habitaciones
- Camping / Glamping
- Tours / Experiencias
- Marina / Embarcaciones
- Sky / Heli / Trekking
- Spa / Gimnasio / Estética
- Room Service
- Housekeeping
- Mantenimiento
- Guest Success
- Encuestas
- Reputación
- Revenue Management
- Conectores
- Configuración

## UX
Debe conservar estilo EDARSAHUB:
- mismos colores
- mismas fuentes
- mismo sidebar
- mismas cards KPI
- mismos filtros corporativos
- patrón Portal Proveedores
- patrón Inteligencia Comercial
- multiventanas
- tabs simples
- permisos por candado y menú contextual

## Permisos contextuales
No solo menús. También:
- editar compra
- imprimir
- autorizar
- cancelar
- alta catálogo
- cambio de precios
- activar conector
- ver datos sensibles
- cerrar incidencia crítica
- modificar tarifa
- reasignar recurso
- aprobar descuento

## Fase 1 permitida
Solo crear estructura base, rutas stub, páginas stub y blueprint.
No crear tablas.
No modificar lógica existente.
No conectar APIs externas.
No activar menú global sin revisión.
