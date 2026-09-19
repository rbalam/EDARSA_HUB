# RRR - GATE 2 - Arquitectura Fisica V1

## Estado
Diseno fisico propuesto. NO ejecutado en SQL. Production=false. Basado en RRR_GATE1_READONLY_DOSSIER_V1.md certificado.

## Objetivo
Definir el minimo nucleo fisico necesario para Gate 3 Engine sin duplicar maestros existentes y manteniendo separacion estricta entre RRR Score, Reward Balance y Rank.

## Fuentes canonicas que RRR referencia
- dbo.Cliente_Catalogo: ClienteID canonico.
- dbo.Venta_Encabezado: VentaID/ClienteID para transacciones cuando aplique.
- dbo.Venta_Detalle y dbo.Venta_Pagos: detalle economico, no almacenamiento RRR.
- dbo.Producto_Catalogo: productos canonicos.
- dbo.Usuario_Catalogo y RBAC actual: administracion/auditoria.
- dbo.Operativo_Notificaciones_Log: infraestructura/log de notificaciones.
- dbo.CavasCorporativas_* y dbo.CavaSocios_*: interoperabilidad solamente; dominio separado.

## Nucleo fisico minimo CREATE

### 1. dbo.RRR_Reglas
Cabecera estable de cada regla de negocio. No contiene valores hardcodeados de score/beneficio como codigo de aplicacion; solo identidad, tipo, alcance configurable y estado.

### 2. dbo.RRR_ReglasVersiones
Version inmutable/configurable de una regla. Contiene ConfigJson, vigencias, version y hash. Permite reproducir por que una transaccion genero un movimiento.

### 3. dbo.RRR_Eventos
Registro idempotente de eventos RRR aceptados/rechazados. Referencia ClienteID y opcionalmente VentaID. Guarda fuente, clave fuente, fecha_operacion, timestamp, hash de payload, estado de validacion y antifraude.

### 4. dbo.RRR_LedgerMovimientos
Fuente de verdad economica/redimible de Reward Balance. Append-only. Cada movimiento referencia cliente, evento y regla/version cuando aplique. Soporta EARN, REDEEM, REVERSAL, EXPIRE y ADJUST; reversas referencian el movimiento original. El balance se calcula como suma neta de ledger valido.

### 5. dbo.RRR_ScoreHistorial
Historial de Score no redimible, con modelo/version, valor y ComponentesJson para explicabilidad. No se mezcla con ledger.

### 6. dbo.RRR_RankingHistorial
Historial de Rank/tier derivado. Guarda modelo/version y RankCode configurable; no fija nombres comerciales definitivos en schema ni check constraints. Puede referenciar el Score usado para el calculo.

### 7. dbo.RRR_Beneficios
Catalogo/configuracion de beneficios propios de RRR. Debe permitir tipo/configuracion/vigencia y una referencia de interoperabilidad externa opcional, sin copiar beneficios ni movimientos internos de Cavas.

## Objetos derivados, no tablas fuente de verdad
- dbo.vw_RRR_ClienteBalance: SUM neta de RRR_LedgerMovimientos vigentes/no anulados por ClienteID.
- dbo.vw_RRR_ClienteEstadoActual: ultimo Score + ultimo Rank + balance derivado para Customer 360.
Estas vistas se proponen para Gate 3/4; el saldo nunca debe convertirse en una tabla mutable autoritativa.

## Resenas / feedback
Gate 1 identifico CRM_PostventaEncuestas como candidato EXTEND. Gate 2 V1 NO altera esa tabla porque la evidencia disponible no certifica todavia el contrato exacto de extension requerido. El nucleo RRR debe consumir una referencia de encuesta/feedback mediante capa de integracion posterior, o extender CRM de forma minima tras un preflight dedicado. No crear un segundo maestro de encuestas mientras exista ese candidato canonico.

## Segmentacion y atribucion
No se crean tablas en este DDL minimo. Gate 4/5 decidiran si se resuelven mediante vistas/snapshots o tablas especificas, usando primero fuentes comerciales y Customer 360.

## Antifraude e idempotencia
- Unique por SourceSystem + SourceKey en RRR_Eventos.
- Unique por IdempotencyKey en RRR_LedgerMovimientos.
- ReversalMovimientoID solo puede apuntar a otro movimiento del ledger; la logica backend debe impedir cadenas invalidas y doble reversa.
- EstadoValidacion/EstadoAntifraude se almacenan para trazabilidad, pero reglas antifraude viven configuradas/versionadas.

## Fechas
RRR_Eventos incluye FechaOperacion para dominios comerciales y OcurridoAtUtc para trazabilidad tecnica. No sustituir fecha_operacion por fecha civil.

## Claves y tipos
Se propone uniqueidentifier para nuevas PK RRR y claves foraneas a maestros que ya usan uniqueidentifier cuando el contrato canonico lo permita. Antes de ejecutar migracion, Gate 2B/ejecucion debe validar tipos exactos de ClienteID, VentaID, EmpresaID/UnidadID y UsuarioID contra SQL real. Si existe diferencia de tipo, se ajusta el DDL antes de ejecutar; no se fuerza conversion ni se altera maestro existente.

## Orden de migracion propuesto
1. RRR_Reglas
2. RRR_ReglasVersiones
3. RRR_Eventos
4. RRR_Beneficios
5. RRR_LedgerMovimientos
6. RRR_ScoreHistorial
7. RRR_RankingHistorial
8. vistas derivadas

## Gate de ejecucion
Este Gate 2 solo certifica diseno. La migracion SQL debe ser un job posterior separado, con preflight READ_ONLY de tipos/FK/nombres, dry-run/validacion y Production=false hasta autorizacion expresa.
