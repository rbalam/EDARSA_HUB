# Calendario Corporativo Canónico — Alcance V1.0 y V1.2

## 1. Decisión arquitectónica

El Calendario Corporativo es un servicio canónico y transversal de
EDARSAHUB.

Su ubicación visual inicial se encuentra en Administración / Sistema,
pero no pertenece funcionalmente a un único módulo.

La ruta canónica inicial es:

`/admin/calendario-corporativo`

El identificador Enterprise es:

`sistema.calendario_corporativo`

## 2. Alcance funcional V1.0

V1.0 implementará únicamente Días Especiales Comerciales para:

- Dashboard Ejecutivo;
- Tablero Comercial;
- Portal de Inteligencia Comercial.

Los tres módulos deberán consumir la misma fuente, contrato, permisos,
resolución temporal y catálogo de fechas.

No se permiten calendarios paralelos ni catálogos duplicados por
pantalla.

## 3. Capacidades comerciales previstas para V1.0

- Día de las Madres.
- San Valentín.
- Navidad.
- Año Nuevo.
- Buen Fin.
- Hot Sale.
- Aniversarios comerciales.
- Eventos promocionales por empresa.
- Eventos promocionales por unidad.
- Comparación de una misma fecha comercial entre años.
- Selecciones de fechas no consecutivas.
- Reglas temporales avanzadas.
- Filtros y última selección por usuario.

## 4. Dominios diferidos a V1.2

- CRM.
- Pedidos.
- Compras.
- Inventarios.
- Finanzas.
- Cuentas por pagar.
- Cuentas por cobrar.
- Nómina y Recursos Humanos.
- Operaciones.
- Mantenimiento.
- Automatizaciones.
- Eventos personales.
- Notificaciones.
- Integraciones con calendarios externos.

## 5. Arquitectura futura obligatoria

La implementación V1.2 deberá conservar:

- SQL EDARSAHUB como fuente única;
- cero MongoDB;
- contrato canónico;
- RBAC por empresa, unidad, rol y usuario;
- workflows auditables;
- versionado;
- cancelación sin borrado físico;
- recurrencias;
- referencias a módulos origen;
- control anti-duplicados;
- integración por servicios, no por consultas directas entre módulos.

## 6. Modelo SQL objetivo

Diseño previsto, sujeto a auditoría antes de crear DDL:

- Calendar_Event
- Calendar_EventScope
- Calendar_EventRecurrence
- Calendar_EventOccurrence
- Calendar_EventSource
- Calendar_EventParticipant
- Calendar_EventRoleAssignment
- Calendar_EventRequest
- Calendar_EventAudit
- User_SavedFilter
- User_LastSelection

La documentación del modelo no autoriza su creación ni ejecución.

## 7. Workflow objetivo

Estados previstos:

- DRAFT
- SUBMITTED
- UNDER_REVIEW
- APPROVED
- REJECTED
- PUBLISHED
- CHANGE_REQUESTED
- CANCELLED
- ARCHIVED

Las fechas personales privadas podrán tener un flujo simplificado.

Toda fecha compartida por empresa, unidad, perfil, rol o proceso deberá
pasar por solicitud, revisión, autorización y publicación.

## 8. Permisos objetivo

- CALENDAR_VIEW
- CALENDAR_CREATE_PERSONAL
- CALENDAR_REQUEST
- CALENDAR_REVIEW
- CALENDAR_AUTHORIZE
- CALENDAR_PUBLISH
- CALENDAR_MODIFY
- CALENDAR_CANCEL
- CALENDAR_MANAGE_SCOPES
- CALENDAR_MANAGE_INTEGRATIONS
- CALENDAR_ADMIN

La definición documental no crea permisos ni modifica RBAC actual.

## 9. Integración transversal

Los módulos origen conservarán su fuente de verdad.

El calendario almacenará únicamente su representación temporal y la
referencia canónica:

- source_module
- source_entity_type
- source_entity_id
- source_event_type

Un enlace desde el calendario deberá validar nuevamente el RBAC del
módulo origen.

## 10. Fechas civiles y operativas

Cada evento deberá declarar su semántica temporal.

Tipos previstos:

- CIVIL
- OPERATIVA
- CONTABLE
- VENCIMIENTO
- PAGO
- RECEPCION

Los días especiales comerciales de V1.0 se resolverán según
`fecha_operacion` cuando sean utilizados por KPIs comerciales.

## 11. Zonas horarias

El modelo futuro deberá utilizar identificadores IANA y la precedencia:

unidad > empresa > plataforma.

La implementación completa de zonas horarias está diferida a V1.2.

## 12. Regla para nuevas pantallas

Todo módulo nuevo debe quedar preparado para tabs mediante un
contenedor desacoplado.

Agregar tabs no deberá:

- cambiar la ruta principal;
- duplicar lógica;
- montar componentes deshabilitados;
- ejecutar consultas innecesarias;
- afectar otros tabs;
- debilitar RBAC;
- omitir el registro Enterprise.
