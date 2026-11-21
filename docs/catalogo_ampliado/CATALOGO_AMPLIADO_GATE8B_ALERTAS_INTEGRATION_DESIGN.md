# Catalogo Ampliado - Gate 8B Alertas Integration Design

## Base certificada
Gate 8A certifico SQL real READ_ONLY para Gobierno_AlertaRegla y Gobierno_AlertaEvento. Este Gate 8B no crea tablas ni ejecuta alertas; fija el contrato de integracion para la siguiente implementacion.

## Principio rector
Catalogo Ampliado es propietario unicamente de reglas y eventos de cumplimiento. No crea un motor paralelo de tareas, notificaciones, comunicaciones ni scheduler.

## Componentes canonicos a reutilizar
1. dbo.Sistema_Tareas: destino canonico para canal TAREA. El patron de escritura ya existe en backend/modules/catalogos_workflow_sql/repository.py.
2. backend/core/communications/notifications: capa canonica de notificaciones. Catalogo Ampliado debe consumir esta capa, no insertar directamente en proveedores externos.
3. dbo.Operativo_Notificaciones_Log: evidencia/log canonico de entrega. Incluye NotificacionID, TareaID, Mensaje, Canal y ErrorMensaje.
4. dbo.Sistema_NotificacionesConfig: configuracion canonica de notificaciones.
5. dbo.Usuario_PortalConfiguracion: preferencias de usuario; respetar RecibeEmailNotificaciones, RecibeWhatsAppNotificaciones y RecibePushNotificaciones.
6. dbo.Usuario_Catalogo: identidad canonica del destinatario.
7. dbo.Gobierno_AlertaRegla y dbo.Gobierno_AlertaEvento: dominio propio de Gobierno Corporativo.

## Flujo objetivo
### A. Planificacion idempotente
- Seleccionar solo documentos activos cuya ultima version este VALIDADA y tenga FechaVencimiento.
- Resolver la empresa propietaria desde EmpresaID directo o desde PersonaEmpresaRolID.
- Aplicar solo reglas activas cuyo EmpresaID sea la empresa o NULL y cuyo TipoDocumentoID corresponda o sea NULL.
- FechaObjetivo = FechaVencimiento.
- FechaProgramada = FechaObjetivo - DiasAntes.
- Crear Gobierno_AlertaEvento solo si no existe la combinacion unica DocumentoVersionID + AlertaReglaID + FechaObjetivo.
- Nunca duplicar eventos por reintento.

### B. Ejecucion
- Procesar exclusivamente eventos PENDIENTE cuya FechaProgramada <= fecha operativa/fecha actual segun contrato que se certifique en implementacion.
- Verificar nuevamente que regla, documento, version y destinatario sigan vigentes antes de entregar.
- Si la condicion ya no aplica, Estado=CANCELADA.

### C. Canal TAREA
- Crear la tarea mediante la infraestructura/patron canonico de Sistema_Tareas; no crear tabla propia.
- TipoTarea propuesto: CUMPLIMIENTO_DOCUMENTAL.
- Modulo: CATALOGO_AMPLIADO.
- EntidadTipo: GOBIERNO_ALERTA_EVENTO.
- EntidadID: AlertaEventoID.
- AsignadoAUsuarioID: UsuarioObjetivoID resuelto de la regla.
- Guardar en Gobierno_AlertaEvento.TareaReferencia la identidad canonica retornada por el motor de tareas, serializada como texto compatible con varchar(50). No inventar otra clave.

### D. Canales EMAIL / WHATSAPP / APP
- Invocar exclusivamente backend/core/communications/notifications.
- Resolver identidad/destino desde Usuario_Catalogo y las preferencias/configuraciones canonicas.
- EMAIL requiere permiso/preferencia activa de email.
- WHATSAPP requiere permiso/preferencia activa de WhatsApp.
- APP se mapea al canal push/app soportado por la capa canonica y requiere RecibePushNotificaciones.
- El resultado debe quedar registrado por la infraestructura existente en Operativo_Notificaciones_Log.
- Guardar Gobierno_AlertaEvento.NotificacionReferencia con el NotificacionID canonico retornado/registrado, sin duplicar log propio.

## Estados de Gobierno_AlertaEvento
Usar exclusivamente los estados ya permitidos por SQL: PENDIENTE, GENERADA, ENVIADA, ERROR, CANCELADA.
- PENDIENTE: evento planificado, aun sin artefacto canonico.
- GENERADA: tarea/notificacion canonica creada y referencia persistida.
- ENVIADA: entrega confirmada por infraestructura canonica cuando el canal implique envio. Para TAREA, GENERADA es el estado terminal de creacion salvo que el contrato canonico de tareas exija otra transicion certificada.
- ERROR: fallo real despues de intento; ErrorMensaje sanitizado, sin secretos.
- CANCELADA: regla/documento/destinatario dejo de aplicar antes de ejecucion.

## Idempotencia y concurrencia
- La UQ de Gobierno_AlertaEvento(DocumentoVersionID,AlertaReglaID,FechaObjetivo) es el candado primario de planificacion.
- Antes de crear Sistema_Tareas o enviar notificacion, bloquear/releer el evento y verificar que TareaReferencia/NotificacionReferencia sigan NULL.
- Un retry con referencia ya persistida no vuelve a entregar.
- Si la entrega canonica retorna idempotency key, usar AlertaEventoID como correlacion de negocio sin crear otro motor de deduplicacion.

## RBAC y seguridad
- Endpoints administrativos permanecen bajo get_current_user + has_full_access.
- La ejecucion automatica no debe depender de un usuario frontend ni bypass de RBAC; debe usar una identidad tecnica ya autorizada por la infraestructura canonica, si existe, y dejar auditoria.
- Nunca exponer secretos/proveedores en respuestas API.

## Scheduler
- No crear scheduler propio dentro de Catalogo Ampliado.
- La siguiente implementacion debe registrar/enganchar el planner/dispatcher en el scheduler/automatizacion canonico existente, despues de certificar su punto de extension exacto.

## API futura minima
- GET /catalogo-ampliado/empresas/{empresa_id}/alertas/eventos : consulta administrativa de eventos por empresa.
- POST interno/servicio planner: no exponer como endpoint publico si el scheduler puede invocar servicio interno.
- POST interno/servicio dispatcher: igual criterio; sin endpoint publico salvo necesidad operativa certificada.

## Pruebas obligatorias para Gate de implementacion
1. Planner idempotente: dos ejecuciones producen un solo evento.
2. Documento/version no validado: no genera evento.
3. Regla inactiva: no genera ni entrega.
4. TAREA: crea exactamente una tarea canonica y persiste TareaReferencia.
5. EMAIL/WHATSAPP/APP: pasan por core communications y generan evidencia canonica; no insercion paralela.
6. Preferencia de usuario deshabilitada: fail-closed, no envio.
7. Retry: no duplica tarea/notificacion.
8. Error: Estado=ERROR y ErrorMensaje sanitizado.
9. Cancelacion por regla/documento no vigente.
10. RBAC de consulta administrativa.
11. E2E real SQL con cleanup completo y residue=0.
12. Production=false.

## Criterio de salida de Gate 8B
Gate 8B queda certificado cuando este contrato se integra sin modificar codigo funcional, pasa tests de contratos existentes y quality/diff gate. El siguiente Gate sera implementacion controlada sobre este contrato; no DDL nuevo salvo que una auditoria adicional pruebe una carencia real.
