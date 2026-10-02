# ARBITROA BOS — A3 Domain Data Contract V1

## 1. Estado y alcance
A0, A1 y A2 estan certificados. Este gate define el **contrato de datos fisico minimo** del bounded context ARBITROA. No ejecuta DDL. No crea tablas. No implementa API/UI. Su funcion es congelar nombres, ownership, relaciones e invariantes antes de A4.

Maximas obligatorias: EDARSAHUB SQL Server es fuente canonica; SQL-first; no MongoDB; no duplicar identidad, usuarios, RBAC, empresas, documentos, notificaciones ni finanzas; REUTILIZAR > EXTENDER > CREAR; no crecer `backend/core`; Production prohibida.

## 2. Contratos BOS reutilizados
ARBITROA referencia, no duplica:
- `dbo.Gobierno_Persona(PersonaID)` para identidad transversal.
- `dbo.Usuario_Catalogo(UsuarioID)` para actor autenticado/auditoria.
- `dbo.Sistema_Empresas(EmpresaID)` y `dbo.Sistema_Sucursales(SucursalID)` cuando exista relacion corporativa real.
- `dbo.Cliente_Catalogo(ClienteID)` cuando una organizacion deportiva sea tambien cliente comercial real; nunca obligatorio.
- `dbo.Gobierno_Documento(DocumentoID)` y versionado documental.
- RBAC/menu BOS existente.
- Communications BOS para despacho de alertas.
- Finanzas BOS para pagos reales en A10, sujeto a auditoria semantica previa.

## 3. Convenciones fisicas
- Esquema SQL: `dbo`; prefijo obligatorio `ARBITROA_`.
- PK operativas: `BIGINT IDENTITY(1,1)` salvo catalogos pequenos, donde `INT IDENTITY` es suficiente.
- Agregados expuestos externamente usan `PublicUUID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWSEQUENTIALID()` con `UNIQUE`.
- Timestamps de sistema: `DATETIME2(0)` UTC (`SYSUTCDATETIME()`).
- Fecha/hora deportiva local: almacenar instante UTC + `ZonaHorariaIANA VARCHAR(64)`; no guardar hora local como unica verdad.
- Soft state: `Activo BIT`; no borrado fisico normal de hechos oficiales.
- Actor: `UsuarioAltaID` / `UsuarioActualizacionID` con FK a `Usuario_Catalogo` cuando aplique.
- JSON solo para payload sport-specific o metadatos no estructurales; identidad, FK, estados, importes y fechas deben ser columnas tipadas.
- No usar `TipoEntidad + EntidadID` sin FK. Relaciones polimorficas deben tener FKs tipadas y CHECK de cardinalidad.

## 4. Catalogos y fundacion — ownership A4
### 4.1 `ARBITROA_Deportes`
Catalogo multi-deporte. Columnas minimas: `DeporteID INT`, `Codigo VARCHAR(40) UNIQUE`, `Nombre NVARCHAR(100)`, `Activo`, auditoria. Semillas iniciales solo cuando A4 lo autorice: futbol, futbol7, futbol_rapido, basquetbol, voleibol, beisbol. Los IDs nunca se hardcodean.

### 4.2 `ARBITROA_Organizaciones`
Representa organizacion deportiva/operativa sin convertirla artificialmente en empresa/sucursal BOS.
Columnas: `OrganizacionID BIGINT`, `PublicUUID`, `TipoOrganizacion VARCHAR(30)`, `Codigo VARCHAR(60)`, `Nombre NVARCHAR(200)`, `EmpresaID INT NULL`, `ClienteID INT NULL`, `Activo`, vigencia y auditoria.
Tipos V1: `SINDICATO`, `LIGA`, `ASOCIACION`, `EMPRESA_SEDE`, `OTRA`.
FK opcionales a `Sistema_Empresas` y `Cliente_Catalogo`.
UNIQUE filtrado/canonico: `Codigo` activo.

### 4.3 `ARBITROA_Afiliaciones`
Relacion historica sindicato/organizacion padre -> liga/organizacion afiliada.
Columnas: `AfiliacionID`, `OrganizacionPadreID`, `OrganizacionAfiliadaID`, `VigenteDesde`, `VigenteHasta`, `Estado`, auditoria.
CHECK padre != afiliada y fechas validas. UNIQUE activo por par. Indices por padre, afiliada y vigencia.
Estados: `PENDIENTE`, `VIGENTE`, `SUSPENDIDA`, `TERMINADA`.

### 4.4 `ARBITROA_OrganizacionPersonas`
Hecho de dominio; no reemplaza RBAC. Relaciona `Gobierno_Persona` con una organizacion y rol operativo/deportivo.
Columnas: `OrganizacionPersonaID`, `OrganizacionID`, `PersonaID`, `RolDominio VARCHAR(40)`, vigencias, `Activo`, auditoria.
Ejemplos de rol: `REPRESENTANTE`, `COORDINADOR_ARBITRAL`, `AUTORIDAD_DISCIPLINARIA`, `DELEGADO`, `ADMIN_SEDE`.
UNIQUE activo por organizacion/persona/rol.

### 4.5 `ARBITROA_Sedes`
Columnas: `SedeID`, `PublicUUID`, `OrganizacionPropietariaID NULL`, `ClienteID NULL`, `Nombre`, direccion operativa, lat/lon opcionales, `ZonaHorariaIANA`, estado operativo base, `Activo`, auditoria.
No almacenar tracking de personas. Coordenadas son de la sede.

### 4.6 `ARBITROA_Canchas`
Columnas: `CanchaID`, `SedeID`, `Codigo`, `Nombre`, `TipoSuperficie`, capacidades/atributos operativos minimos, `Activo`, auditoria.
UNIQUE `SedeID + Codigo`.

### 4.7 `ARBITROA_Reglamentos`
Versionado normativo estructural, archivo real en Gobierno documental.
Columnas: `ReglamentoID`, `OrganizacionID NULL`, `DeporteID`, `Nombre`, `NumeroVersion`, `VigenteDesde`, `VigenteHasta`, `DocumentoID BIGINT NULL`, `ConfiguracionJSON NVARCHAR(MAX) NULL`, `Estado`, auditoria.
FK a `Gobierno_Documento`. UNIQUE por alcance/deporte/version. Estado: `BORRADOR`, `VIGENTE`, `SUSTITUIDO`, `INACTIVO`.

**A4 solo puede materializar estas siete tablas de fundacion mas RBAC/menu necesario. Ninguna tabla de gates posteriores se crea anticipadamente.**

## 5. Competencia y participantes — ownership A5
### 5.1 `ARBITROA_Temporadas`
`TemporadaID`, `PublicUUID`, `LigaID -> ARBITROA_Organizaciones`, `DeporteID`, `Codigo`, `Nombre`, fechas, estado, auditoria. UNIQUE liga/deporte/codigo.

### 5.2 `ARBITROA_Torneos`
`TorneoID`, `PublicUUID`, `TemporadaID`, `Codigo`, `Nombre`, categoria/division, reglamento vigente opcional, fechas, estado, auditoria.
Estados: `CONFIGURACION`, `ABIERTO`, `EN_CURSO`, `CERRADO`, `CANCELADO`.

### 5.3 `ARBITROA_Equipos`
`EquipoID`, `PublicUUID`, `LigaID`, `Codigo`, `Nombre`, `Activo`, auditoria. UNIQUE liga/codigo.

### 5.4 `ARBITROA_TorneoEquipos`
Membresia versionada de equipo en torneo. `TorneoEquipoID`, `TorneoID`, `EquipoID`, `Estado`, fechas, auditoria. UNIQUE torneo/equipo activo.

### 5.5 `ARBITROA_EquipoPersonas`
Roster tipado sobre `Gobierno_Persona`. `EquipoPersonaID`, `EquipoID`, `PersonaID`, `RolParticipante` (`JUGADOR`, `DT`, `AUXILIAR`, `DELEGADO`, `MEDICO`, `OTRO`), dorsal opcional, vigencias, estado, auditoria.
No copiar nombre, CURP, email u otra PII canonica desde Gobierno_Persona.
UNIQUE activo por equipo/persona/rol.

## 6. Calendario y partido — ownership A6
### 6.1 `ARBITROA_Jornadas`
Jornada **deportiva**, distinta de `RH_Cat_Jornadas`. `JornadaID`, `TorneoID`, numero/codigo, nombre, rango de fechas, estado. UNIQUE torneo/codigo.

### 6.2 `ARBITROA_Partidos`
Agregado principal: `PartidoID`, `PublicUUID`, `TorneoID`, `JornadaID NULL`, `CanchaID`, `EquipoLocalID`, `EquipoVisitanteID`, `InicioUTC`, `ZonaHorariaIANA`, `Estado`, marcador oficial nullable, `ReglamentoID NULL`, auditoria.
CHECK local != visitante.
Estados: `PROGRAMADO`, `CONFIRMADO`, `EN_CURSO`, `SUSPENDIDO`, `FINALIZADO`, `CERRADO`, `CANCELADO`. Solo `CERRADO` es hecho final para cedula/estadistica oficial.
Indices: torneo/inicio, cancha/inicio, equipo local/inicio, equipo visitante/inicio, estado/inicio.

### 6.3 `ARBITROA_ImportacionesCalendario`
Cabecera idempotente para Excel/CSV. `ImportacionID`, liga/torneo, `SourceSHA256 CHAR(64)`, nombre de archivo, estado, totales y auditoria. UNIQUE por alcance + hash.
Estados: `CARGADA`, `VALIDADA`, `CON_ERRORES`, `APLICADA`, `CANCELADA`.

### 6.4 `ARBITROA_ImportacionCalendarioFilas`
Staging persistente: `ImportacionFilaID`, `ImportacionID`, `NumeroFila`, campos normalizados, `EstadoValidacion`, `ErroresJSON`, `PartidoID NULL`. UNIQUE importacion/numeroFila. Nunca es fuente oficial de partidos hasta `APLICADA`.

## 7. Arbitraje, restricciones y cobertura — ownership A7
### 7.1 `ARBITROA_PerfilesArbitrales`
Extension 1:1 de persona. `PerfilArbitralID`, `PersonaID BIGINT UNIQUE`, `CodigoArbitro`, categoria, zona base, estado operativo, `Activo`, auditoria. FK a `Gobierno_Persona`.
Estados: `ACTIVO`, `SUSPENDIDO`, `INACTIVO`, `EN_VALIDACION`.

### 7.2 `ARBITROA_HabilitacionesArbitrales`
`HabilitacionID`, `PerfilArbitralID`, `DeporteID`, categoria/rol habilitado, vigencia, `DocumentoID NULL`, estado. UNIQUE activo por perfil/deporte/rol/categoria.

### 7.3 `ARBITROA_DisponibilidadesArbitrales`
Ventanas de disponibilidad/no disponibilidad. `DisponibilidadID`, `PerfilArbitralID`, `InicioUTC`, `FinUTC`, `Tipo`, motivo, auditoria. CHECK fin > inicio.

### 7.4 `ARBITROA_Restricciones`
Veto/restriccion tipada. `RestriccionID`, `PersonaID NULL`, `EquipoID NULL`, `OrganizacionID NULL`, `SedeID NULL`, `TorneoID NULL`, `PartidoID NULL`, `Alcance`, `Tipo`, `Severidad`, motivo, vigencias, `DocumentoID NULL`, `Estado`, auditoria.
Todas las referencias tienen FK reales. CHECK exige al menos un objetivo y consistencia con `Alcance`; no existe `EntidadID` generico.
Estado: `BORRADOR`, `VIGENTE`, `SUSPENDIDA`, `REVOCADA`, `VENCIDA`.

### 7.5 `ARBITROA_Designaciones`
`DesignacionID`, `PartidoID`, `PerfilArbitralID`, `RolArbitral`, `Estado`, timestamps de propuesta/aceptacion/rechazo/reasignacion, motivo y auditoria.
UNIQUE activo partido+rol+perfil; indices por perfil/fecha y partido/estado.
Estados: `PROPUESTA`, `NOTIFICADA`, `ACEPTADA`, `RECHAZADA`, `CANCELADA`, `REASIGNADA`, `CUMPLIDA`, `AUSENTE`.

### 7.6 `ARBITROA_AsistenciasPartido`
Check-in formal autoritativo para arbitros y participantes. `AsistenciaID`, `PartidoID`, `PersonaID`, `DesignacionID NULL`, `EquipoPersonaID NULL`, `TipoParticipante`, `Estado`, `Metodo`, `CheckInUTC`, `CheckOutUTC NULL`, `UsuarioRegistroID NULL`, evidencia documental opcional y auditoria.
CHECK: para ARBITRO requiere DesignacionID; para jugador/staff requiere EquipoPersonaID. GEO no puede marcar asistencia automaticamente.
Metodos: `QR`, `CODIGO_BARRAS`, `FOLIO`, `MANUAL`, `ROSTER`.
Estados: `PENDIENTE`, `PRESENTE`, `AUSENTE`, `NO_ELEGIBLE`, `SUSPENDIDO`, `VETADO`.
UNIQUE partido/persona/tipoParticipante.

## 8. Cedula, incidencias y disciplina — ownership A8
### 8.1 `ARBITROA_Cedulas`
`CedulaID`, `PublicUUID`, `PartidoID UNIQUE`, `Estado`, marcador capturado, resumen, `DocumentoID NULL`, `CerradaUTC NULL`, `CerradaPorUsuarioID NULL`, auditoria.
Estados: `BORRADOR`, `CAPTURA`, `PENDIENTE_VALIDACION`, `CERRADA`, `ANULADA`. Solo `CERRADA` alimenta oficialidad. Reapertura requiere evento de auditoria y permiso especifico; no update silencioso.

### 8.2 `ARBITROA_Incidencias`
`IncidenciaID`, `PublicUUID`, `PartidoID`, `CedulaID NULL`, `TipoIncidencia`, `Severidad`, `MinutoJuego NULL`, `PersonaID NULL`, `EquipoID NULL`, `SedeID NULL`, descripcion, `Estado`, auditoria. Referencias tipadas.

### 8.3 `ARBITROA_ExpedientesDisciplina`
`ExpedienteID`, `PublicUUID`, liga/torneo/partido/incidencia opcionales tipados, persona/equipo involucrado tipado, estado, fechas, auditoria.
Estados: `ABIERTO`, `EN_REVISION`, `AUDIENCIA`, `RESUELTO`, `APELADO`, `CERRADO`.

### 8.4 `ARBITROA_ResolucionesDisciplina`
`ResolucionID`, `ExpedienteID`, version, tipo, texto/resumen, `DocumentoID NULL`, fecha, estado, usuario autoridad. UNIQUE expediente/version.

### 8.5 `ARBITROA_Sanciones`
`SancionID`, `ExpedienteID`, `PersonaID NULL`, `EquipoID NULL`, `OrganizacionID NULL`, tipo, vigencias, alcance, estado y auditoria. Debe tener objetivo tipado valido. Las sanciones efectivas pueden proyectarse a `ARBITROA_Restricciones`; no duplicar reglas manualmente.

### 8.6 `ARBITROA_BitacoraVoz`
Persistencia gobernada del flujo voz -> transcripcion -> propuesta -> confirmacion humana. `BitacoraVozID`, `PartidoID`, `CedulaID NULL`, `PersonaCapturaID`, `AudioDocumentoID NULL`, `TranscripcionDocumentoID NULL`, `ExtraccionJSON`, `Estado`, `ConfirmadaPorUsuarioID NULL`, timestamps.
Estados: `CAPTURADA`, `TRANSCRITA`, `PROPUESTA`, `CONFIRMADA`, `DESCARTADA`. Ninguna `PROPUESTA` modifica cedula/incidencia oficial sin confirmacion humana.

## 9. Estadistica y evaluacion — ownership A9
### 9.1 `ARBITROA_TiposEventoDeportivo`
Catalogo por deporte: `TipoEventoID`, `DeporteID`, `Codigo`, `Nombre`, reglas de cardinalidad/valor, `Activo`. UNIQUE deporte/codigo.

### 9.2 `ARBITROA_EventosPartido`
Hecho deportivo estructurado: `EventoPartidoID`, `PartidoID`, `TipoEventoID`, `Secuencia`, `Periodo`, `SegundoJuego NULL`, `EquipoID NULL`, `PersonaID NULL`, `ValorDecimal NULL`, `ValorTexto NULL`, `PayloadJSON NULL`, `EsOficial`, auditoria. UNIQUE partido/secuencia. Solo eventos oficiales de partido `CERRADO` alimentan KPIs historicos.

### 9.3 `ARBITROA_EvaluacionesArbitrales`
`EvaluacionID`, `PartidoID`, `PerfilArbitralID`, `EvaluadorPersonaID`, puntajes tipados minimos, observaciones, estado, auditoria. UNIQUE partido/perfil/evaluador.

## 10. Operacion financiera — ownership A10
### 10.1 `ARBITROA_TarifasArbitrales`
Regla comercial/operativa, no pago bancario. `TarifaID`, liga/torneo/deporte/rol, vigencia, moneda, importe, estado, auditoria. UNIQUE por alcance/rol/vigencia segun reglas A10.

### 10.2 `ARBITROA_ServiciosLiquidables`
Hecho derivado de designacion cumplida: `ServicioLiquidableID`, `DesignacionID UNIQUE`, `TarifaID`, `PersonaID`, `Importe`, `Moneda`, `Estado`, `FinanzasPagoID NULL`, autorizacion y auditoria.
Estados: `PENDIENTE`, `VALIDADO`, `AUTORIZADO`, `ENVIADO_FINANZAS`, `PAGADO`, `CANCELADO`.
`FinanzasPagoID` solo se incorpora si A10 certifica FK/semantica compatible; hasta entonces permanece fuera del DDL ejecutable.

## 11. Automatizacion — ownership A11
No se crean tablas de agentes si Agent Harness cubre registry/ejecucion. ARBITROA puede emitir eventos de dominio desde sus propias transiciones; scheduler/communications/agent harness se reutilizan. Cualquier persistencia adicional exige discovery especifico.

## 12. GEO temporal — ownership A12
### 12.1 `ARBITROA_GeoSesiones`
Sesion consentida por persona+partido. `GeoSesionID`, `PartidoID`, `PersonaID`, consentimiento, `InicioUTC`, `FinUTC`, estado, precision/parametros minimos. UNIQUE una sesion activa por partido/persona.
Estados: `PENDIENTE`, `COMPARTIENDO`, `FINALIZADA`, `REVOCADA`, `EXPIRADA`.

### 12.2 `ARBITROA_GeoMuestras`
`GeoMuestraID`, `GeoSesionID`, `FechaUTC`, lat/lon, precision, velocidad/rumbo opcionales, fuente. Indice `GeoSesionID,FechaUTC`.
Retencion corta configurable; objetivo inicial de diseño: 72 horas despues del cierre del partido, salvo requerimiento legal/operativo documentado. Las muestras no prueban asistencia.

### 12.3 `ARBITROA_GeoEventos`
Eventos derivados: `GeoEventoID`, sesion, tipo (`EN_RUTA`, `FUERA_RUTA`, `CERCA`, `DENTRO_GEOFENCE`, `SIN_SENAL`, etc.), fecha y metadatos. No reemplaza `ARBITROA_AsistenciasPartido`.

## 13. SAFE / Proteccion Civil — ownership A13
### 13.1 `ARBITROA_SedeSeguridadPerfil`
1:1 con sede. Contactos/protocolos/equipamiento operativo, nivel de riesgo y estado. No expediente medico.

### 13.2 `ARBITROA_SafeChecklists`
Checklist pre-partido/sede versionado: `ChecklistID`, `PartidoID NULL`, `SedeID`, tipo, estado, usuario responsable, inicio/cierre.
Estados: `BORRADOR`, `EN_REVISION`, `APROBADO`, `CONDICIONADO`, `RECHAZADO`.

### 13.3 `ARBITROA_SafeChecklistItems`
`ChecklistItemID`, `ChecklistID`, codigo, resultado, observacion, evidencia `DocumentoID NULL`. UNIQUE checklist/codigo.

### 13.4 `ARBITROA_SafeIncidentes`
Incidente de seguridad/proteccion civil: sede/partido, tipo, severidad, descripcion, autoridades notificadas, documento/evidencia y estado.

### 13.5 `ARBITROA_AptitudOperativa`
Registro minimo de aptitud para asignacion/servicio. `AptitudID`, `PersonaID`, `PartidoID NULL`, `FechaUTC`, `ResultadoOperativo`, `Metodo`, `DocumentoID NULL`, `UsuarioRegistroID`. No almacena diagnosticos ni expediente medico. Alcohol testing, si existe, registra solo resultado operativo minimo y evidencia gobernada; IA nunca determina intoxicacion ni sancion.

## 14. Documentos de dominio
Para relaciones N:M documentales se reserva `ARBITROA_DocumentoVinculos` en el gate que primero lo necesite. Debe usar `DocumentoID` + FKs tipadas nullable (`PartidoID`, `IncidenciaID`, `PerfilArbitralID`, `SedeID`, `ExpedienteID`, etc.) y CHECK exactamente un destino. Prohibido `EntidadTipo/EntidadID` sin integridad referencial.

## 15. Estados e invariantes transversales
1. Todo cambio terminal relevante conserva historial/auditoria; no se reescribe silenciosamente.
2. `Partido.CERRADO` requiere cedula `CERRADA` o excepcion autorizada y auditada.
3. Marcador oficial se consolida una sola vez desde cedula cerrada; staging/import nunca es fuente oficial.
4. Designacion `CUMPLIDA` requiere asistencia formal `PRESENTE` salvo override autorizado/auditado.
5. GEO nunca crea asistencia.
6. Restricciones/sanciones vigentes bloquean o advierten segun severidad; no se ignoran silenciosamente.
7. Voz/IA solo propone; confirmacion humana produce mutacion oficial.
8. Un `Gobierno_Persona` puede no tener usuario. Nunca crear usuario para poder representar jugador/arbitro.
9. Ningun agregado ARBITROA replica nombre/RFC/CURP/email como fuente maestra. Snapshots legales solo cuando exista justificacion explicita futura.

## 16. Idempotencia
- Import calendario: hash SHA256 + alcance; reimport del mismo archivo no duplica partidos.
- Designaciones: claves unicas activas por partido/rol/persona segun contrato.
- Cedula: una cabecera por partido.
- Servicio liquidable: uno por designacion cumplida.
- Eventos externos futuros deben llevar `IdempotencyKey` o hash de origen con UNIQUE en su tabla de ingreso; no se agregan hasta existir integracion concreta.

## 17. PII, privacidad y retencion
- PII canonica vive en `Gobierno_Persona`; ARBITROA guarda FKs.
- Documentos sensibles viven en Gobierno documental con sensibilidad/RBAC.
- GEO es temporal, consentido, partido-especifico y con retencion corta.
- SAFE no guarda historia clinica.
- Logs no deben contener tokens, credenciales, documentos completos, CURP/RFC innecesarios ni coordenadas permanentes fuera del modulo GEO.
- Exportaciones deben aplicar RBAC y minimizacion.

## 18. Multi-tenant y autorizacion
El scope de dominio se deriva por `LigaID/OrganizacionID` y afiliaciones. El acceso se resuelve con RBAC BOS + relaciones de dominio, nunca con IDs enviados por cliente sin validacion. SUPERADMIN conserva acceso global conforme BOS. No hardcodear empresas, ligas, roles ni permisos.

## 19. Indices minimos obligatorios
Cada FK de alta cardinalidad debe contar con indice de lectura segun flujo. Prioridad: partido por torneo/fecha/cancha/equipos; designacion por arbitro/fecha y partido/estado; asistencia por partido/persona; restricciones por objetivo/vigencia; incidencias por partido; eventos por partido/secuencia; GEO por sesion/fecha. Indices adicionales se justifican con queries reales, no por anticipacion.

## 20. Estrategia de migracion futura
A3 no contiene DDL ejecutable. A4 debe producir DDL separado, idempotente y reversible para solo fundacion. Reglas:
1. Preflight `OBJECT_ID/COL_LENGTH` de dependencias canonicas.
2. `SET XACT_ABORT ON` + transaccion.
3. Crear tablas en orden de dependencia.
4. Crear FK/UNIQUE/CHECK/indices explicitamente nombrados.
5. Seeds por `Codigo`, nunca por ID fijo.
6. Postflight SQL read-only con `HRLectura`.
7. Backup/rollback documentado antes de cualquier alteracion futura de objetos existentes.

## 21. Rollback
Mientras una tabla ARBITROA este vacia y no tenga consumidores certificados, rollback puede eliminar solo objetos creados por el mismo gate en orden inverso. Una vez existan datos oficiales, rollback deja de ser DROP y pasa a desactivar feature/route y conservar datos. Nunca borrar maestros BOS.

## 22. NO CREAR
Explicitamente prohibidos:
- `ARBITROA_Usuarios`, `ARBITROA_Personas`, `ARBITROA_Roles`, `ARBITROA_Permisos`.
- tablas Mongo o documentos Mongo como runtime.
- segundo sistema documental.
- segundo dispatcher/notification queue.
- segundo sistema de pagos/tesoreria/bancos.
- tablas deportivas dentro de `backend/core`.
- `RH_Cat_Jornadas` como jornada deportiva.

## 23. Mapa de materializacion por gates
- A4: 7 tablas de fundacion + registro RBAC/menu BOS.
- A5: 5 tablas de temporada/torneo/equipos/roster.
- A6: 4 tablas calendario/partido/import.
- A7: 6 tablas arbitraje/restricciones/asistencia.
- A8: 6 tablas cedula/incidencia/disciplina/voz.
- A9: 3 tablas eventos/estadistica/evaluacion.
- A10: 2 tablas tarifa/servicio liquidable, previa auditoria Finanzas.
- A11: 0 tablas por defecto; reutilizar Agent Harness/Scheduler/Communications.
- A12: 3 tablas GEO temporales.
- A13: 5 tablas SAFE.

Total contractual maximo V1: 41 tablas candidatas, pero **no se crean juntas**. La regla de gasto es crear solo el subconjunto del gate en curso y solo si sigue faltando tras discovery inmediato.

## 24. Presupuesto de desarrollo recalibrado
El baseline pre-auditoria era 385 creditos. A1/A2/A3 eliminan construccion desde cero de identidad, auth, RBAC, menu governance, documentos, notifications, Worker y parte financiera. Para control interno, A3 fija un nuevo presupuesto de planeacion, no precio oficial de Emergent:
- Core A4-A11: objetivo 175, maximo 220.
- GEO A12: objetivo 65, maximo 85.
- SAFE A13: objetivo 28, maximo 38.
- A14 E2E/certificacion: objetivo 20, maximo 30.
- Total objetivo: 288; maximo de planeacion: 373.
Alerta amarilla >10% sobre presupuesto de gate; roja >20% o cuando un gate intenta recrear capacidad BOS existente.

## 25. Criterio de cierre A3
A3 cierra solo si:
- este contrato queda versionado;
- pruebas estaticas pasan;
- no existe DDL ejecutado;
- no se toca Production;
- no se crea Mongo;
- no se duplica maestro BOS;
- A4 queda limitado a fundacion minima.
