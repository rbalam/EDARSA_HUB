# Catalogo Ampliado V1 - Contrato canonico y atomico

## Objetivo
Extender el catalogo existente de empresas/unidades con gobierno corporativo, legal y fiscal sin duplicar maestros de EDARSAHUB.

## Fuentes maestras que NO se duplican
- Empresa: `dbo.Sistema_Empresas`.
- Unidad: resolucion canonica vigente mediante `UnidadesService` y catalogos SQL existentes.
- Usuario: `dbo.Usuario_Catalogo` + RBAC canonico.
- Cliente: `dbo.Cliente_Catalogo`.
- Proveedor: `dbo.Proveedor_Catalogo`; contactos existentes: `dbo.Proveedor_Contactos`.
- Tareas: infraestructura SQL de Fase2 (`Tareas_Inventario` y servicios/rutas existentes) se reutiliza mediante adaptador, no se crea un segundo centro de tareas.
- Notificaciones: `dbo.Operativo_Notificaciones_Log`, email existente y `core.communications`/Twilio para WhatsApp.

## Nuevo nucleo atomico requerido
1. `Gobierno_Persona`: identidad transversal de persona fisica; no reemplaza Usuario/Cliente/Proveedor.
2. `Gobierno_PersonaVinculo`: vincula una persona con identidades canónicas existentes (USUARIO, CLIENTE, PROVEEDOR, CONTACTO_PROVEEDOR), evitando copiar sus datos maestros.
3. `Gobierno_RolCorporativoCatalogo`: tipos de relacion/cargo parametrizables (SOCIO, ACCIONISTA, REPRESENTANTE_LEGAL, APODERADO, CONSEJERO, PRESIDENTE, SECRETARIO, TESORERO, VOCAL, COMISARIO, FIRMANTE y extensiones futuras).
4. `Gobierno_PersonaEmpresaRol`: relacion historica Persona-Empresa-Rol, con vigencias, participacion/facultades y evidencia documental.
5. `Gobierno_TipoDocumento`: catalogo parametrizable de tipos documentales, propietario permitido (PERSONA/EMPRESA/RELACION), requiere_vigencia y reglas preventivas.
6. `Gobierno_Documento`: identidad logica unica del documento y propietario atomico.
7. `Gobierno_DocumentoVersion`: versiones inmutables, archivo/storage key, hash SHA-256, metadata OCR, fechas detectadas/capturadas, estado de revision.
8. `Gobierno_DocumentoMovimiento`: kardex append-only de altas, sustituciones, revisiones, aprobaciones, cambios de vigencia y bajas logicas.
9. `Gobierno_AlertaRegla`: anticipaciones configurables por empresa/tipo documento/usuario; sin hardcodes obligatorios.
10. `Gobierno_AlertaEvento`: materializacion idempotente de alertas preventivas y trazabilidad hacia tarea/notificacion.
11. `Gobierno_EmpresaConfiguracion`: extension 1:1 de `Sistema_Empresas`; contiene `CatalogoLegalAmpliadoActivo` y configuracion propia sin alterar el maestro.

## Invariantes
- SQL-first; MongoDB prohibido como fuente o cache.
- Canonico y atomico: un dato maestro se almacena una vez y las relaciones lo referencian.
- No hardcodes de empresas, unidades, personas, cargos ni dias de alerta.
- Documentos y versiones nunca se sobrescriben: nueva version + kardex.
- Los documentos binarios no se guardan duplicados por empresa/rol; se referencia la misma identidad/version cuando corresponda.
- OCR es asistente: una fecha extraida por OCR tiene estado PENDIENTE hasta validacion humana o regla de confianza autorizada.
- Alertas son preventivas: el sistema prioriza `vence_en_dias`; vencido es excepcion, no el modelo principal.
- Toda escritura sensible registra usuario, fecha UTC y origen.
- Baja logica; historial no destructivo.
- Produccion no se toca sin gate y autorizacion correspondiente.

## Integracion de comunicaciones
- Tarea: reutilizar servicio existente mediante adaptador de dominio para evitar acoplar Gobierno Corporativo a inventarios.
- Email: reutilizar servicio de email existente.
- WhatsApp: reutilizar `core.communications.providers.TwilioWhatsAppProvider`; disponibilidad depende de configuracion valida del provider.
- Todo envio registra evento en log canonico de notificaciones o referencia equivalente auditable.

## V1.0 funcional
- Activar/desactivar Catalogo Legal Ampliado por empresa con permiso.
- Personas unicas y vinculos a identidades existentes.
- Roles corporativos multiples e historicos por empresa.
- Expediente persona/empresa/relacion.
- Carga y versionamiento documental.
- Kardex completo.
- Vigencias manuales y fechas sugeridas por OCR.
- Alertas configurables y preventivas.
- Asignacion de responsables y tareas.
- Email y WhatsApp cuando provider este disponible.
- Dashboard de cumplimiento y proximos vencimientos.
- RBAC explicito para ver/crear/editar/aprobar/documentos/configurar.
- Tests unitarios, integracion, E2E y quality gate antes de integrar.

## Preparacion futura sin implementar ahora
- Firma electronica avanzada.
- Integraciones SAT/Registro Publico/autoridades.
- Due diligence externo y data room.
- IA de riesgo/obligaciones.
- Flujos de aprobacion multinivel mas complejos.

Estas extensiones deben poder agregarse sin reemplazar las identidades ni documentos V1.
