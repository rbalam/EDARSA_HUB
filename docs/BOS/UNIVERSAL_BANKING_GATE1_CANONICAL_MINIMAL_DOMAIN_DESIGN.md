# UNIVERSAL BANKING — Gate 1 Canonical Minimal Domain Design

Estado objetivo: DOCUMENTAL / NO DDL / NO DML / NO BANK CONNECTIONS

## 1. Entrada certificada

Gate 0 quedó CERTIFIED_READ_ONLY / PASS / 100%, con SQL runtime y Globalization certificados.
Gate 1 READ_ONLY quedó CERTIFIED_READ_ONLY / PASS / 100%.

Principio vinculante:
REUSE -> CONSOLIDATE -> EXTRACT -> EXTEND -> CREATE_ONLY_WHEN_PROVEN_MISSING.

EDARSAHUB SQL Server sigue siendo cerebro y única fuente canónica de verdad.

## 2. Decisiones vinculantes de reutilización

### 2.1 ProviderConnection
NO crear tabla ProviderConnection.

REUSE / EXTEND:
- dbo.Servidores_Conexiones
- dbo.Servidores_ConexionEstado
- dbo.Sistema_Tipos
- dbo.Sistema_VersionesSistemas
- core.connection_resolver
- core.server_registry
- core.secret_manager

La conexión bancaria es una conexión/sistema/version existente con metadata específica, no un subsistema paralelo.

### 2.2 BankingCapability
NO crear catálogo BankingCapability.

REUSE / EXTEND:
- dbo.Sistema_Capacidades
- dbo.Sistema_Sync_Capacidades cuando aplique vínculo ejecución/capacidad
- SystemCapabilityResolver

Las capacidades bancarias se modelan como filas/códigos del registry existente.

Capacidades candidatas:
- ACCOUNT_INFORMATION
- BALANCES
- TRANSACTIONS
- STATEMENTS
- PAYMENTS
- BULK_PAYMENTS
- INTERNATIONAL_PAYMENTS
- COLLECTIONS
- DIRECT_DEBIT
- REAL_TIME_PAYMENTS
- PAYMENT_STATUS
- PAYMENT_RECEIPTS
- WEBHOOKS
- HOST_TO_HOST
- SFTP
- SWIFT
- OPEN_BANKING

No sembrar nada hasta Gate posterior con evidencia y migración idempotente.

### 2.3 ExternalExecution
NO crear un ledger de ejecución paralelo.

REUSE / EXTEND:
- dbo.Sync_Control_Ejecuciones

Este ledger ya soporta o fue preparado para:
- ConexionID
- UnidadNegocioID
- CodigoSync
- StartedAtUTC
- FinishedAtUTC
- IdempotencyKey

Universal Banking deberá usarlo como ejecución transversal.

Si Banking necesita estado técnico adicional específico de pagos, crear únicamente un child/domain projection vinculado a SyncControlID y a la entidad financiera correspondiente; nunca otro ledger completo.

### 2.4 BankFile / evidencia
REUSE:
- dbo.Sync_Control_Evidencias

Ya soporta:
- TipoEvidencia
- HashSHA256
- Referencia
- NombreOriginal
- MimeType
- Bytes
- FechaCapturaUTC
- unique run/hash

Para archivos Banorte/BBVA:
RAW inmutable + SHA256 + nombre original + timestamps + evidencia.

NO crear una tabla por formato:
- Banorte_PP
- Banorte_RE3
- Banorte_MT940
- BBVA_File
etc.

Si se requiere lifecycle operativo del archivo, podrá existir una proyección Banking específica mínima ligada a SyncControlID/EvidenciaID; la evidencia física sigue siendo transversal.

### 2.5 Identificadores externos de integración
REUSE:
- dbo.Sistema_IdentificadoresExternos

Uso permitido:
IDs externos de sistema/conexión/unidad, por ejemplo LOCATION, MERCHANT, STORE, CONTRACT, CUSTOMER_EXTERNAL_ID.

NO usar esta tabla para forzar identificadores bancarios de dominio que no dependen de una conexión.

IBAN pertenece a cuenta bancaria.
SWIFT/BIC pertenece a institución financiera.
ABA/Routing pertenece a institución/clearing.
UETR pertenece a mensaje/transferencia internacional.

Por tanto, estos identificadores deben resolverse dentro del modelo bancario mínimo, sin columnas dispersas y sin confundirlos con integration IDs.

## 3. Reutilización financiera obligatoria

REUSE:
- dbo.Global_Cat_Bancos
- dbo.Economia_Paises
- dbo.Proveedor_Monedas
- dbo.Unidades_Negocio.timezone_iana
- dbo.Unidades_Negocio.locale_operativo
- dbo.Finanzas_Cat_CuentasBancarias
- dbo.Finanzas_SaldosBancarios
- dbo.Proveedor_CuentasBancarias
- dbo.Finanzas_CxP_Sync
- dbo.Finanzas_CxP_DecisionesPago
- dbo.Finanzas_CxP_PagosOrigenQueue
- dbo.Finanzas_Pagos
- dbo.Finanzas_EstatusPago
- Finanzas_Conciliacion*
- RBAC canónico
- Scheduler canónico
- JobLogger canónico
- Secrets/config canónicos

NO crear equivalentes paralelos.

## 4. Piezas realmente nuevas después de reutilización

### 4.1 PaymentRail
REALMENTE_NUEVO como concepto de dominio.

Debe distinguir, por ejemplo:
- MX_SPEI
- MX_TEF
- US_ACH
- US_FEDWIRE
- EU_SEPA
- UK_FPS
- SWIFT

No confundir rail con banco, canal o formato.

### 4.2 BankingChannel
REALMENTE_NUEVO como semántica de dominio, pero debe apoyarse en Servidores_Conexiones para infraestructura.

Ejemplos:
- REST_API
- HOST_TO_HOST
- SFTP
- SWIFT
- OPEN_BANKING

No crear un segundo registry de conexiones.

### 4.3 Banking Identifier model
REALMENTE_NUEVO únicamente para identificadores bancarios de dominio no cubiertos por estructuras actuales.

Separación obligatoria:
Account identifiers:
- CLABE
- IBAN
- ACCOUNT_NUMBER
- local schemes

Institution identifiers:
- SWIFT/BIC
- ABA/ROUTING
- local clearing/bank codes

No agregar columnas internacionales una por una a tablas legacy si un modelo atómico resuelve el caso.

### 4.4 Banking external event
REALMENTE_NUEVO como proyección/evento de dominio cuando el evento no sea sólo evidencia.

Debe mapear eventos externos:
- ACK/NACK
- accepted
- processing
- rejected
- settled
- cancelled
- unknown

y conservar:
- provider/bank
- external code
- external status
- external reference
- occurred_at
- received_at
- raw evidence reference
- idempotency/dedup key

No reemplaza Finanzas_EstatusPago.

## 5. Estado y responsabilidad

Separación vinculante:

A. Autorización
Finanzas_CxP_DecisionesPago

B. Despacho
Finanzas_CxP_PagosOrigenQueue

C. Ejecución transversal
Sync_Control_Ejecuciones

D. Evento bancario externo
Universal Banking event projection

E. Hecho financiero
Finanzas_Pagos + Finanzas_EstatusPago

F. Conciliación
Finanzas_Conciliacion*

TIMEOUT != FAILED.
Ante timeout:
UNKNOWN -> query status -> evento/receipt -> conciliación -> resolución.
Nunca reenviar automáticamente por timeout.

## 6. Banorte y BBVA

Banorte y BBVA son adapters.

NO son dueños de:
- pagos
- cuentas
- beneficiarios
- saldos
- conciliación
- scheduler
- RBAC
- moneda
- país
- timezone
- capabilities registry
- secrets registry

Flujo:
CxP -> autorización -> PagosOrigenQueue -> Sync_Control_Ejecuciones -> Adapter -> evento/evidencia -> Finanzas_Pagos -> conciliación.

## 7. Core slimming

No agregar lógica bancaria específica a backend/core.

Core sólo puede aportar infraestructura ya transversal:
- connection resolution
- secrets
- scheduler
- SQL-first
- capability resolution
- corporate scope

El dominio Universal Banking debe vivir fuera de Core como bounded context cohesionado.

## 8. Gate 1 closure criteria

Gate 1 queda documentalmente cerrado si:
- este dossier es el único cambio materializado;
- no hay DDL/DML;
- no hay conexiones bancarias;
- no hay pagos;
- no hay cambios en Producción;
- no se crean tablas o endpoints;
- no se crean adapters;
- no se duplica ninguna capacidad existente.

GATE_1_DESIGN_COMPLETE=true
DDL_EXECUTED=false
DML_EXECUTED=false
BANK_CONNECTIONS_EXECUTED=false
REAL_PAYMENTS_EXECUTED=false
PRODUCTION_TOUCHED=false
