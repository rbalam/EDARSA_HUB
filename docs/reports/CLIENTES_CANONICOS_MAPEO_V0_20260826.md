# CLIENTES CANONICOS - MAPEO V0

Fecha: 2026-08-26
Estado: PARCIAL CONFIRMADO / PENDIENTE ESQUEMA LIVE DE POS

## 1. Regla rectora

- `dbo.Cliente_Catalogo` es el maestro canonico de clientes y fuente de verdad para clientes reales/facturables.
- CRM debe consumir `Cliente_Catalogo`; no se crea otro maestro de clientes.
- `Cliente_Contactos`, `Cliente_Direcciones` y `Cliente_Grupos` se reutilizan para atributos atomicos relacionados cuando el dato no pertenece al registro maestro.
- `Sync_Customers` es infraestructura intermedia/legacy de sincronizacion; NO es destino canonico ni fuente de verdad.
- Cava de Socios debe referenciar `ClienteID` y conservar solo atributos propios de la relacion de Cava. Nombre, RFC, email, telefono y direccion no deben duplicarse en Cavas.
- No fusionar clientes por nombre. La identidad de origen debe preservarse por sistema + unidad + clave origen usando la estructura canonica ya existente; si el modelo actual no dispone de una relacion de identidad-origen suficiente, se reporta el gap antes de crear estructura.

## 2. Destinos canonicos confirmados

### 2.1 Cliente_Catalogo
Campos confirmados por codigo/documentacion actual:

- ClienteID (PK)
- EmpresaID
- CodigoCliente
- RFC
- RazonSocial
- NombreComercial
- TipoPersona
- MonedaID
- LimiteCredito
- DiasCredito
- EmailPrincipal
- TelefonoPrincipal
- FechaAlta
- Activo
- CreatedBy
- CreatedAt
- EjecutivoPrincipalUserID
- GerenteComercialUserID
- CustomerSuccessUserID
- SectorID
- SubsectorID
- TamanoClienteID
- RiesgoCuentaID
- EsProspecto
- EsPartner
- EsCuentaEstrategica
- FechaUltimaInteraccion
- ScoreCuenta
- OrigenCuentaID

Nota: la documentacion historica indica 44 columnas en total; el esquema live completo queda pendiente de obtener con acceso POS/SQL operativo.

### 2.2 Cliente_Contactos
Destino para contactos personales asociados a un ClienteID.
Campos utilizados actualmente por CRM:

- ClienteID
- Nombre
- ApellidoPaterno
- ApellidoMaterno
- Email
- Telefono
- Celular
- Puesto
- EsPrincipal
- Activo
- CreatedBy
- CreatedAt

### 2.3 Cliente_Direcciones
Existe como entidad atomica ya reconocida por el modelo CRM. Debe recibir domicilio(s) del cliente cuando el origen los tenga, en lugar de crear columnas duplicadas en Cavas/CRM.

### 2.4 Cliente_Grupos
Existe como entidad atomica ya reconocida. Debe evaluarse como destino natural para clasificaciones comerciales de origen cuando semantica y cardinalidad coincidan. No crear una nueva tabla de grupos hasta auditar esta tabla live.

### 2.5 CRM_Cuentas
No sustituye a Cliente_Catalogo. Es la capa CRM para prospectos/cuentas comerciales y puede ligarse por `ClienteID` al cliente real canonico.

## 3. Mapeo conceptual SoftRestaurant -> canonico

La pantalla operativa de SoftRestaurant confirma catalogos `Clientes`, `Tipo de Clientes`, `Clientes de servicio a domicilio`, `Zonas de servicio a domicilio` y `Colonias`. En CIENFUEGOS se observa Tipo de Cliente `104 - SOCIOS CAVA`.

| Concepto origen SoftRestaurant | Destino canonico | Regla |
|---|---|---|
| Clave cliente | Identidad origen + `Cliente_Catalogo.CodigoCliente` solo si la semantica corporativa lo permite | Nunca usar la clave POS sola como identidad global. Debe quedar asociada tambien a sistema/unidad origen. |
| Nombre / razon social | `Cliente_Catalogo.RazonSocial` / `NombreComercial` | Normalizar sin destruir valor original. Persona fisica puede requerir nombre comercial = nombre mostrado si no hay razon social. |
| RFC | `Cliente_Catalogo.RFC` | Señal fuerte de identidad cuando sea RFC valido y no generico. No unica evidencia para registros sin RFC. |
| Email | `Cliente_Catalogo.EmailPrincipal` y/o `Cliente_Contactos.Email` | Principal al maestro; multiples contactos a tabla atomica. |
| Telefono / celular | `Cliente_Catalogo.TelefonoPrincipal` y/o `Cliente_Contactos` | No crear telefono en Cava. |
| Tipo de cliente | Relacion/categoria existente (`Cliente_Grupos` o catalogo equivalente tras validar esquema) | `104 = SOCIOS CAVA` es dato de catalogo de CIENFUEGOS, no hardcode estructural. |
| Domicilio | `Cliente_Direcciones` | Atomicidad: multiples domicilios por cliente si el origen los soporta. |
| Colonia | `Cliente_Direcciones` / catalogo geografico existente | No duplicar catalogo de colonias sin comprobar estructura existente. |
| Zona servicio domicilio | Relacion de direccion/segmentacion existente | No convertir automaticamente en atributo del cliente maestro si pertenece a domicilio/ruta. |
| Estatus/activo | `Cliente_Catalogo.Activo` | Requiere traduccion de estados del origen. Nunca borrar fisicamente por baja POS. |
| Fecha alta/modificacion | campos canonicos existentes de alta/auditoria | Preservar fecha origen si hay campo equivalente; no reemplazar auditoria EDARSAHUB. |
| SOCIOS CAVA | relacion de Cava sobre ClienteID + clasificacion comercial existente | Ser socio no crea otro cliente. |

## 4. Mapeo conceptual ManagementPro -> canonico

La interfaz de ManagementPro confirma `Clientes` y catalogos relacionados: Segmentos, Sectores, Rutas de venta, Grupos comerciales, Cadenas comerciales, Giros comerciales, Subrogados, Reclasificador de clientes y asignacion a rutas. Existe `Grupo comercial = SOCIOS CAVA` en el origen observado.

| Concepto origen MPRO | Destino canonico | Regla |
|---|---|---|
| ID/Clave cliente MPRO | Identidad origen + posible `Cliente_Catalogo.CodigoCliente` | La identidad externa debe ser sistema + unidad + clave. |
| Nombre/Razon social | `Cliente_Catalogo.RazonSocial` / `NombreComercial` | No crear maestro MPRO paralelo. |
| RFC | `Cliente_Catalogo.RFC` | Matching fuerte solo si es valido/no generico. |
| Email | `Cliente_Catalogo.EmailPrincipal` / `Cliente_Contactos.Email` | Multiples emails/contactos deben mantenerse atomicos si el origen los diferencia. |
| Telefono/celular | `Cliente_Catalogo.TelefonoPrincipal` / `Cliente_Contactos` | Mismo criterio. |
| Segmento | catalogo/relacion comercial existente | No asumir que `SectorID` es SegmentoID; validar semantica antes de mapear. |
| Sector | `Cliente_Catalogo.SectorID` si el catalogo canonico es semanticamente equivalente | Requiere tabla de equivalencias, no IDs de origen directos. |
| Ruta de venta | relacion comercial/ruta existente | No agregar `Ruta` como texto repetido al maestro si ya existe dominio de rutas. |
| Grupo comercial | `Cliente_Grupos` o relacion canonica equivalente | `SOCIOS CAVA` es clasificacion de origen; Cavas usa ClienteID. |
| Cadena comercial | relacion jerarquica/comercial existente | Validar si el cliente pertenece a cadena o si cadena representa otra entidad. |
| Giro comercial | catalogo/relacion comercial existente | No duplicar `Giro` si existe sector/giro canonico. |
| Subrogado | relacion cliente-cliente existente si ya existe | No convertir en columna booleana sin confirmar cardinalidad y semantica. |
| Reclasificador | historial/regla de clasificacion existente | Debe preservar clasificacion vigente e historial si el origen lo ofrece. |
| Credito / limite | `Cliente_Catalogo.LimiteCredito`, `DiasCredito`, y condiciones existentes | No sobreescribir condiciones EDARSAHUB mas recientes sin politica de precedencia. |
| Moneda | `Cliente_Catalogo.MonedaID` | Traducir catalogo origen -> MonedaID canonica. |
| Activo/estatus | `Cliente_Catalogo.Activo` | Baja origen no implica DELETE. |

## 5. Reglas de identidad y deduplicacion

Orden propuesto de resolucion, pendiente de validar contra datos live:

1. Coincidencia exacta de identidad origen ya registrada: sistema + unidad + clave origen -> mismo ClienteID.
2. RFC valido y no generico, con validaciones de conflicto -> candidato fuerte.
3. Email normalizado + telefono normalizado, con nombre compatible -> candidato fuerte/moderado.
4. Telefono unico + nombre compatible -> candidato moderado.
5. Nombre solamente -> NUNCA fusion automatica.
6. Registros `CAVA VIRTUAL`, `CAVA PEND`, `CAVA01`, etc. -> preservar como registros origen; no inferir persona real ni fusionar automaticamente.

Una coincidencia dudosa debe quedar separada/pendiente de resolucion, no fusionarse destructivamente.

## 6. Precedencia de actualizacion del cliente canonico

- La sincronizacion debe ser idempotente.
- Un POS nunca debe vaciar un dato canonico de mejor calidad con NULL/vacio.
- Conservar datos mas completos cuando fuentes discrepen, siguiendo una politica determinista por campo.
- Datos CRM editados/autorizados en EDARSAHUB no deben ser reemplazados ciegamente por un POS si EDARSAHUB es la fuente maestra para ese atributo.
- Clasificaciones de cada origen deben conservar procedencia, no simplemente sobrescribir una unica etiqueta global.

## 7. Compatibilidad CRM obligatoria

CRM ya consulta `Cliente_Catalogo` directamente y `CRM_Cuentas` se liga a `ClienteID`. Por tanto:

- Todo cliente sincronizado debe quedar inmediatamente visible para `CRMComercialService.listar_clientes` si `Activo=1`.
- La sincronizacion no debe generar otra entidad que el CRM tenga que replicar.
- Oportunidades, cuentas CRM, cotizaciones y pedidos deben conservar sus FK a `ClienteID`.
- `Cliente_Contactos` se reutiliza para contactos; no duplicar contactos del POS dentro de `CRM_Cuentas` salvo snapshots operativos ya existentes.

## 8. Cava de Socios

Objetivo de convergencia:

- `CavaSocios_Socios` debe referenciar `ClienteID` canonico.
- NombreCompleto, Email, Telefono, RFC u otros datos generales duplicados deben migrarse/reconciliarse con Cliente_Catalogo / Cliente_Contactos y dejar de ser fuente de verdad en Cavas.
- La tabla de Cavas conserva exclusivamente membresia, unidad, estado, fechas y reglas propias de custodia.
- `Tipo Cliente = SOCIOS CAVA` (SoftRestaurant) y `Grupo Comercial = SOCIOS CAVA` (MPRO) sirven para identificar relacion/membresia, no para crear clientes nuevos.

## 9. Bloqueo actual para Mapeo V1 exacto de columnas POS

El segundo barrido de esquema live fallo antes de consultar los POS porque el runner de GitHub Actions no tiene `SERVER_SECRET_KEY` configurada. `EDARSAHUB_SQL_PASSWORD` si esta disponible, pero `SERVER_SECRET_KEY` llega vacia. Sin ella no se pueden descifrar en memoria las credenciales almacenadas en `Servidores_Conexiones`, por lo que no es seguro ni correcto adivinar nombres fisicos de columnas SoftRestaurant/MPRO.

Esto no cambia la arquitectura ni el destino canonico; bloquea solamente el detalle exacto `tabla.columna origen -> tabla.columna EDARSAHUB`.

## 10. Siguiente estado esperado: MAPEO V1

Cuando se ejecute el mismo auditor en un entorno que ya tenga `SERVER_SECRET_KEY` (worker/servidor EDARSAHUB), completar para cada unidad:

- tabla fisica fuente
- columna fisica fuente
- tipo SQL fuente
- cardinalidad/nullability
- ejemplo enmascarado
- destino canonico exacto
- transformacion
- regla de precedencia
- clave idempotente
- tratamiento de conflicto
- conteo origen
- conteo sincronizable

Unidades requeridas: 130MID, 130QRO, ORIGEN, CIENFUEGOS, ESTELAR y cualquier otra unidad activa detectada por `Unidades_Negocio`.
