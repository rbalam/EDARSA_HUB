# ARBITROA BOS - Master Architecture V1

## 1. Decision arquitectonica
ARBITROA nace como **BOS Satellite / bounded context** de EDARSAHUB. No crece `backend/core`, no crea un segundo cerebro, no duplica identidad, RBAC, menus, auditoria, notificaciones ni otros servicios corporativos cuando exista contrato canonico reutilizable.

ARBITROA es dueno del dominio arbitral/deportivo. EDARSAHUB BOS sigue siendo cerebro, gobierno y unica fuente de verdad empresarial.

## 2. Principios no negociables
1. SQL-first. MongoDB no puede ser fuente nueva ni primaria del dominio.
2. No crear tabla, columna, fuente, catalogo, helper, endpoint transversal o conexion antes de demostrar que no existe equivalente canonico reutilizable.
3. Auth, usuarios y RBAC deben reutilizar EDARSAHUB. Prohibido crear `arbitroa_users` u otro silo de identidad.
4. Menus/permisos deben registrarse por el gobierno SQL existente de Sistema_Modulos/Sistema_ModulosMenus/Sistema_ModulosPermisos; no hardcodear navegacion.
5. ARBITROA vive en modulo/paquete propio; no agregar dominio vertical a `backend/core`.
6. Reutilizar helpers canonicos de empresa/unidad/scope, fechas, zona horaria, filtros, documentos, auditoria, notificaciones, scheduler/Worker y finanzas si la auditoria demuestra suficiencia.
7. GEO y SAFE son subdominios ARBITROA, no aplicaciones con auth/base/RBAC duplicados.
8. Cambios quirurgicos, reversibles, con pruebas y evidencia. Production queda fuera hasta autorizacion humana separada.
9. UX operable por personas no tecnicas, especialmente en movil/campo.
10. La reduccion de consumo de creditos Emergent es KPI de arquitectura: reutilizar infraestructura BOS antes de pedir generacion nueva.

## 3. Limite del bounded context
### 3.1 EDARSAHUB BOS gobierna/reutiliza cuando exista
- identidad, autenticacion y sesiones;
- usuarios, roles, permisos y scopes;
- empresas/unidades/organizaciones corporativas;
- menus y navegacion gobernada;
- auditoria/bitacora transversal;
- documentos/adjuntos transversales;
- notificaciones/comunicaciones;
- scheduler y Universal Worker;
- AI Gateway / proveedores IA aprobados;
- helpers de fecha/zona horaria/moneda/idioma;
- contratos financieros reutilizables, sin asumir su suficiencia hasta discovery.

### 3.2 ARBITROA es dueno de
- sindicato y relacion operativa con ligas afiliadas cuando no exista maestro corporativo equivalente;
- temporadas, torneos, jornadas y partidos;
- equipos, planteles y participacion deportiva;
- perfil arbitral, habilitaciones, disponibilidad, designaciones y cobertura;
- asistencia arbitral y control de participantes;
- cedulas, incidencias, disciplina, vetos/suspensiones y cierres;
- estadistica deportiva y evaluacion arbitral;
- reglas de servicio arbitral, tarifas operativas y liquidacion por partido, enlazadas con Finanzas canonico cuando corresponda;
- automatizaciones especificas del dominio.

## 4. Subdominios
### ARBITROA GEO
Localizacion temporal por evento, consentimiento, geocercas, ETA, riesgo de arribo y alertas. Nunca tracking 24/7. GEO ayuda al control; no sustituye check-in oficial.

### ARBITROA SAFE
Proteccion civil, checklist de sede, seguridad, protocolos de emergencia y aptitud operativa. Alcoholimetria es opcional, sensible, purpose-bound, con minimizacion, acceso restringido y retencion definida. SAFE no sustituye autoridad medica, disciplinaria ni de proteccion civil.

## 5. Modelo conceptual - no autoriza tablas
Entidades conceptuales del dominio: LigaAfiliada, Temporada, Torneo, Jornada, Partido, Equipo, Plantel, Jugador/Participante, PerfilArbitral, Habilitacion, Disponibilidad, Designacion, Asistencia, Cedula, Incidencia, Sancion/Veto, Capacitacion, EstadisticaPartido, EvaluacionArbitral, TarifaServicio, ServicioArbitral, Liquidacion, GeoSesion/Evento, SafeChecklist/Evento.

**Ningun nombre anterior es nombre fisico autorizado de tabla.** Los nombres fisicos solo se definen despues del discovery SQL y repositorio.

## 6. Reglas funcionales congeladas
1. Jerarquia deportiva base: Liga -> Temporada -> Torneo -> Jornada -> Partido.
2. Calendario admite captura manual e importacion masiva controlada Excel/CSV con staging/validacion, duplicados y bitacora; nunca overwrite ciego.
3. Designacion distingue asignado, notificado, confirmado, en camino, arribado/check-in, reemplazado, ausencia y cierre.
4. Participantes pueden validarse por lista precargada y credencial QR/barcode/folio, con contingencia manual auditada.
5. Voz es un **input alternativo**: transcribe y propone campos de catalogo del formulario oficial. No crea un segundo tipo de cedula ni permite cierre sin confirmacion humana.
6. Toda cedula/incidencia tiene estados y cierre formal; nada queda indefinidamente abierto.
7. Estadisticas (goles, faltas, tarjetas, expulsiones) se capturan como hechos estructurados y despues alimentan analitica.
8. Evaluacion arbitral es dominio separado de estadistica deportiva y alimenta ranking/desempeno.
9. Vetos, suspensiones, conflictos y habilitaciones deben poder bloquear/senalizar operaciones segun reglas configuradas, no hardcode.
10. Ingreso del sindicato y pago/liquidacion a arbitros son flujos separados: programado -> cubierto -> facturable y rol prestado -> liquidable -> autorizado -> pagado.
11. Geolocalizacion solo en ventanas operativas ligadas a evento/consentimiento y con minimizacion.
12. SAFE almacena solo el minimo necesario y aplica RBAC reforzado a datos sensibles.

## 7. Personas e identidad
No se decide aun si Jugador/Arbitro referencian un maestro de personas corporativo o una entidad deportiva especializada. Gate A1/A2 debe auditar la estructura real de personas, empleados, usuarios, proveedores/beneficiarios y contactos. CREATE solo procede si REUSE/EXTEND no preservan semantica, seguridad, performance y lifecycle del dominio.

## 8. Estrategia de datos
Baseline: misma instancia/base EDARSAHUB SQL con aislamiento logico del bounded context, salvo que el discovery demuestre razon tecnica para otra estrategia. Separacion fisica futura debe ser posible por contratos canonicos, sin acoplar frontend a tablas.

No conexiones nuevas si una conexion canonica sirve. No secretos ni credenciales hardcodeadas. No lecturas Live para analitica/administracion cuando el contrato BOS sea HUB/SYNC-S.

## 9. Mobile/campo
ARBITROA debe ser mobile-first para asistencia, credenciales, voz, evidencia, GEO y SAFE, pero SQL/backend conserva autoridad. El dispositivo no es fuente de verdad. Fallas de red usan contingencia/outbox gobernado si el BOS mobile canonico lo soporta; no se disena un segundo sync engine sin discovery.

## 10. IA y agentes
Los agentes del dominio no poseen permisos por si mismos. Deben ejecutarse bajo RBAC/policy/AI Gateway/Worker existentes. Familias objetivo: coordinacion de designaciones, asistencia, incidencias, reglamentos, GEO, contingencias, SAFE y analitica. Primero reglas deterministas y datos estructurados; IA solo donde agrega valor.

## 11. Emergent - KPI de consumo
La estimacion previa de 385 creditos (260 base + 95 GEO + 30 SAFE) queda marcada **BASELINE PRE-AUDITORIA, NO PRESUPUESTO FINAL**.

Meta de A1/A2: cuantificar componentes BOS reutilizables y recalcular el presupuesto Emergent evitando generar auth, RBAC, menus, auditoria, notificaciones, documentos, infraestructura y helpers ya existentes. El contador de creditos debe reportarse por gate/fase como: presupuesto fase, consumo real, acumulado, desviacion y saldo.

Reglas para reducir creditos:
- un solo proyecto/contexto ARBITROA sobre BOS, no tres apps desde cero;
- arquitectura y contratos congelados antes de polish visual;
- prompts por bounded context/gate, no prompts abiertos;
- no pedir a Emergent infraestructura que ya exista;
- reutilizar componentes/UI/API/helpers canonicos;
- agentes IA al final de cada flujo estable;
- testing pesado solo en hitos de riesgo, manteniendo regresion minima en todos los gates.

## 12. Gates de ingenieria/implementacion
A0 MASTER ARCHITECTURE: este contrato; documentacion solamente.
A1 SQL DISCOVERY READ ONLY: inventario SQL de personas, usuarios/RBAC, empresas/unidades, menus/permisos, documentos, auditoria, notificaciones, finanzas/pagos y objetos potencialmente deportivos. Resultado REUTILIZAR/EXTENDER/CREAR/NO TOCAR.
A2 REPOSITORY CONTRACT DISCOVERY: inspeccion de modulos/helpers/endpoints/frontend/scheduler/AI Gateway y errores arquitectonicos documentados. Sin cambios funcionales.
A3 DOMAIN DATA CONTRACT: con evidencia A1/A2, definir esquema fisico minimo y migracion; CREATE requiere prueba de ausencia canonica.
A4 MODULE FOUNDATION + RBAC/MENU: scaffold del satelite y registro por contratos existentes.
A5 LEAGUES/PARTICIPANTS: ligas, equipos, jugadores/planteles, habilitacion/vetos.
A6 CALENDAR/IMPORT: temporadas/torneos/jornadas/partidos e importacion controlada.
A7 ASSIGNMENTS/ATTENDANCE: disponibilidad, designaciones, cobertura, credenciales y check-in/out.
A8 CEDULAS/VOICE/DISCIPLINE: formulario estructurado, voz como input, incidencias, cierre y evidencia.
A9 STATS/EVALUATION: hechos deportivos, estadisticas, evaluacion/ranking.
A10 FINANCIAL OPS: tarifas, servicios facturables y liquidaciones integradas al contrato financiero canonico.
A11 AUTOMATION/AGENTS: alertas, mensajes y agentes gobernados por infraestructura BOS.
A12 GEO: localizacion temporal, geocerca, ETA y contingencia.
A13 SAFE: proteccion civil, seguridad y aptitud operativa opcional.
A14 E2E/SECURITY/UX/CREDIT CERTIFICATION: regresion, tenant/RBAC, performance, recovery, experiencia mobile y presupuesto real Emergent.

Cada gate de implementacion debe terminar con evidencia terminal, tests relevantes, blockers explicitos y `production_touched=false`. Ningun gate autoriza Produccion.

## 13. Criterio de completitud
ARBITROA BOS V1 solo puede declararse completo cuando: no duplica fuentes canonicas; RBAC y menus son BOS; SQL es fuente de verdad; operaciones de campo son auditables y tienen contingencia; voz desemboca en formulario estructurado; GEO es temporal y consentido; SAFE aplica minimizacion y acceso restringido; finanzas separa ingreso y liquidacion; pruebas E2E/seguridad pasan; consumo Emergent real queda documentado; Production no fue tocada durante bootstrap.
