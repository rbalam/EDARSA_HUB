# ARBITROA BOS - A2 Repository Contract Discovery V1

## 1. Resultado ejecutivo
A1 certifico la conexion canonica `EDARSAHUB / HRLectura / HRLectura`, con `quality_gate=PASS`, `tests=PASS`, `CERTIFIED_READ_ONLY`, `files_changed=[]` y `production_touched=false`. El repositorio y SQL demuestran que ARBITROA debe construirse como bounded context satelite y **reutilizar primero** los contratos BOS existentes.

## 2. REUTILIZAR
### 2.1 Identidad transversal de persona
- `dbo.Gobierno_Persona` es el maestro transversal de persona.
- `dbo.Gobierno_PersonaVinculo` enlaza persona con `Usuario_Catalogo`, `Cliente_Catalogo`, `Proveedor_Catalogo` y contactos tipados.
- `dbo.Gobierno_PersonaEmpresaRol` vincula persona, empresa y rol corporativo.
- Repositorio existente: `backend/modules/catalogo_ampliado/repository.py`, SQL-first.

Decision: arbitros, coordinadores, autoridades y cualquier participante que requiera identidad transversal deben referenciar `Gobierno_Persona(PersonaID)` cuando corresponda. Prohibido un segundo maestro `Arbitroa_Personas`. Los perfiles deportivos son extensiones de dominio, no identidad duplicada.

### 2.2 Usuarios y autorizacion
Reutilizar:
- `Usuario_Catalogo`;
- `Usuario_RolesAsignacion`;
- `Usuario_RolesContexto`;
- `vw_Usuario_RolesContexto`;
- `vw_Usuario_RolesContexto_Efectivo`;
- `Sistema_CatalogosPermisos`;
- `Sistema_Modulos`;
- `Sistema_ModulosMenus`;
- `Sistema_ModulosPermisos`;
- `Sistema_RBAC_PerfilCatalogo`;
- helpers RBAC existentes.

Decision: ARBITROA registra permisos y menu en BOS; no crea auth, roles ni menu paralelos.

### 2.3 Empresas/unidades/sucursales
Reutilizar como maestros corporativos:
- `Sistema_Empresas`;
- `Sistema_Sucursales`;
- `Unidades_Negocio`;
- vistas/helpers canonicos de unidad cuando aplique.

Decision: una liga/organizacion externa no se fuerza artificialmente a ser sucursal. El modelo de dominio puede requerir entidad propia, pero debe enlazarse a maestros corporativos solo cuando semanticamente corresponda.

### 2.4 Documentos/evidencia
Reutilizar como primera opcion:
- `Gobierno_Documento`;
- `Gobierno_DocumentoVersion`;
- `Gobierno_DocumentoMovimiento`;
- `Gobierno_TipoDocumento`.

Decision: cedulas, evidencia, reglamentos, certificados y documentos SAFE deben consumir este gobierno documental mediante relacion de dominio; no crear almacenamiento documental paralelo sin evidencia de insuficiencia.

### 2.5 Notificaciones/comunicaciones
El repositorio documenta como contratos existentes:
- `Sistema_NotificacionesConfig`;
- `Operativo_Notificaciones_Log`;
- `NotificationDispatcher`;
- `TemplateService`.

Decision: alertas y comunicaciones ARBITROA deben extender plantillas/eventos/canales existentes. No crear segunda cola ni segundo dispatcher.

### 2.6 Auditoria
Reutilizar las bitacoras y patrones transversales existentes (`Usuario_LogActividades`, `Usuario_LogRBACVerificacion` y gobierno/auditoria aplicable). Cada agregado ARBITROA puede requerir historial propio de negocio solo cuando sea parte de su invariancia; no duplicar auditoria transversal.

### 2.7 Worker / AI governance
Reutilizar Universal Worker como ejecutor determinista. Para IA, consumir el Agent Harness/AI Gateway cuando el flujo se implemente; ningun agente obtiene autoridad propia.

### 2.8 Finanzas
Existen `Finanzas_Pagos`, `Finanzas_EstatusPago`, CxP y otros contratos financieros. A10 debe auditar semantica exacta antes de integrar liquidaciones arbitrales.

Decision: no crear tesoreria, bancos, pagos ni contabilidad paralela. El dominio ARBITROA puede mantener hechos `servicio arbitral/liquidable` y entregar su pago al contrato financiero canonico cuando se confirme compatibilidad.

## 3. EXTENDER
Extensiones permitidas solo en bounded context ARBITROA, referenciando maestros canonicos:
- perfil arbitral de una `Gobierno_Persona`;
- habilitaciones/certificaciones deportivas;
- disponibilidad;
- participacion deportiva;
- designaciones;
- reglas/vetos disciplinarios;
- relacion documental de dominio;
- eventos de notificacion ARBITROA;
- permisos/menu ARBITROA registrados en tablas BOS existentes.

EXTENDER no significa agregar columnas deportivas a tablas canonicas de Gobierno/RBAC. Preferir tablas del bounded context con FK al maestro.

## 4. CREAR - DOMINIO NUEVO CANDIDATO
A1 `SPORTS_DOMAIN_COLLISION_SCAN` no encontro un dominio arbitral/deportivo previo. El unico objeto real con coincidencia `Jornada` fue `RH_Cat_Jornadas` y constraints laborales asociados; no representa jornada deportiva.

Por tanto, queda autorizada **conceptualmente**, no fisicamente todavia, la creacion de agregados ARBITROA para:
- ligas afiliadas y convenios operativos deportivos;
- temporadas/torneos/jornadas deportivas/partidos;
- equipos/planteles/participacion de jugadores;
- perfiles/habilitaciones/disponibilidad/designaciones arbitrales;
- asistencia/check-in de partido;
- cedulas/incidencias/disciplina/sanciones/vetos;
- hechos de estadistica deportiva;
- evaluacion arbitral;
- tarifa/servicio/liquidacion de dominio;
- GEO temporal;
- SAFE/proteccion civil y aptitud operativa.

Los nombres fisicos, columnas, PK, FK e indices se definen solo en A3.

## 5. NO TOCAR / NO REUTILIZAR COMO FUENTE NUEVA
- MongoDB y cualquier coleccion legacy.
- `Sistema_EmpresasMongoMap` o `Usuario_MigracionMongoTrace` como modelo de dominio; son legado/migracion, no fuente canonica ARBITROA.
- tablas `Backup_*`, `BAK_*`, `P4_14_Backup_*`.
- `RH_Cat_Jornadas` para jornadas deportivas.
- `Cliente_UsuariosPortal` o `Proveedor_UsuariosPortal` como auth de ARBITROA.
- `RH_Colaboradores_Expediente` como maestro universal de arbitros; solo podria vincularse si una persona tambien es colaborador real de RH.
- `backend/core`: no agregar archivos ARBITROA al core.

## 6. Patron de persona
Patron recomendado:
`Gobierno_Persona` -> `ARBITROA_PerfilArbitral` / `ARBITROA_ParticipacionPersona` (nombres provisionales).

Una persona puede existir sin usuario. Un usuario debe vincularse a la identidad canonica segun contratos BOS. Jugadores pueden ser personas de Gobierno si se requiere identidad transversal; A3 debe decidir mecanismo minimo sin duplicar PII.

## 7. Patron de modulo backend
Crear `backend/modules/arbitroa/` como bounded context cuando A3/A4 lo autoricen. No crear `backend/core/arbitroa*`. Consumir helpers existentes mediante imports estables.

Subdominios pueden vivir como paquetes internos (`geo`, `safe`) si el tamano lo requiere, manteniendo un solo ownership de ARBITROA.

## 8. Patron frontend
Registrar ARBITROA por menu SQL gobernado. Rutas/componentes deben quedar dentro del dominio frontend existente, evitando hardcodear unidades, roles o permisos. Reutilizar layout, cliente API, manejo de auth y componentes comunes ya existentes.

## 9. Patron notificaciones
ARBITROA genera eventos de dominio; Communications resuelve canal/template/envio/log. GEO y SAFE no crean dispatchers separados.

## 10. Patron documental
El archivo fisico/metadata/versionado es Gobierno documental. ARBITROA conserva solo la relacion semantica del documento con partido, cedula, incidente, persona, sede, habilitacion o checklist.

## 11. Patron financiero
ARBITROA captura hechos operativos: partido cubierto, rol prestado, tarifa aplicada, monto liquidable y estado de autorizacion. La salida bancaria/pago real se integra a Finanzas BOS; no se implementa un sistema bancario dentro del satelite.

## 12. Core Slimming
Toda nueva logica vertical va a `backend/modules/arbitroa`. El core solo se consume. Si una capacidad verdaderamente transversal falta, debe pasar por un gate BOS separado; ARBITROA no la introduce escondida dentro del core.

## 13. Impacto en creditos Emergent
A1/A2 confirman reutilizacion significativa. No se autoriza aun una cifra nueva final, pero el baseline pre-auditoria de 385 creditos debe bajar porque ARBITROA no necesita generar desde cero identidad, auth, RBAC, menu governance, documento/versionado, comunicaciones, auditoria transversal, Worker ni parte de Finanzas.

A3 debe estimar creditos solo sobre **delta real** del bounded context.

## 14. Siguiente gate
A3 DOMAIN DATA CONTRACT debe definir el esquema fisico minimo del delta ARBITROA con:
- FK a Gobierno_Persona y maestros BOS donde corresponda;
- ownership claro;
- PK/FK/unique/indexes;
- estados y transiciones;
- auditoria de negocio;
- retencion/PII;
- idempotencia;
- estrategia de migracion;
- rollback;
- DDL todavia separado de ejecucion.

A3 no debe ejecutar SQL ni implementar UI. Primero contrato y pruebas estaticas.
