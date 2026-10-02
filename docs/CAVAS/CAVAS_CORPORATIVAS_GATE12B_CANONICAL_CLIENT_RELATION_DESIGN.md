# Cavas Corporativas - Gate 12B - Diseno de relacion canonica Cliente <-> Socio

## Estado
DOCUMENTO DE DISENO CONTROLADO. NO IMPLEMENTA DDL, DML NI CAMBIOS FUNCIONALES.

## Evidencia base obligatoria
Gate 12A certifico que CavaSocios_Socios usa SocioID uniqueidentifier como PK; contiene ClienteCRMID uniqueidentifier nullable e indice IX_CavaSocios_Socios_ClienteCRM; Cliente_Catalogo usa ClienteID int como PK; no existe FK directa entre ambas tablas; Email/Telefono/Activo se solapan con EmailPrincipal/TelefonoPrincipal/Activo; y Botellas, Cargos y Movimientos dependen de CavaSocios_Socios.SocioID.

## Decision arquitectonica
1. Cliente_Catalogo permanece como unica identidad maestra de cliente.
2. CavaSocios_Socios permanece como extension de membresia Cava y conserva SocioID como PK.
3. ClienteCRMID es legado y NO se debe convertir/castear a ClienteID: uniqueidentifier e int son dominios incompatibles.
4. Si la auditoria de este Gate confirma que no existe en CavaSocios_Socios otra columna int reutilizable ni una FK canonica existente, el Gate 12C podra agregar una unica columna nullable ClienteID int a CavaSocios_Socios con FK a Cliente_Catalogo(ClienteID). Esa columna sera la relacion canonica nueva.
5. ClienteCRMID, NombreCompleto, Email y Telefono se conservan durante la transicion. No se eliminan ni renombran en Gate 12C.
6. Botellas, Cargos y Movimientos siguen apuntando a SocioID. No deben migrarse a ClienteID porque representan operaciones de membresia Cava, no identidad maestra.

## Estrategia de poblacion
- Prohibido inferir ClienteID por casting, truncado, hash o coincidencia parcial.
- El backfill de ClienteID solo puede usar un crosswalk fisico y verificable entre ClienteCRMID y Cliente_Catalogo, si este Gate identifica uno.
- Si no existe crosswalk determinista, los registros quedan ClienteID NULL y pasan a conciliacion controlada posterior; no se inventan correspondencias por nombre/email/telefono sin un Gate especifico de matching y reglas aprobadas.
- Antes de imponer NOT NULL o unicidad se requiere cobertura 100% de socios que deban estar ligados a cliente y cero conflictos.

## Lectura durante transicion
- Identidad canónica: si ClienteID no es NULL, resolver nombre/contacto/activo desde Cliente_Catalogo.
- Campos legacy de CavaSocios_Socios quedan solo como compatibilidad y evidencia historica durante la transicion.
- No usar ClienteCRMID como fuente maestra una vez exista ClienteID validado.
- No modificar semantica de Activo/Estatus de membresia: Cliente_Catalogo.Activo representa estado del cliente; CavaSocios_Socios.Activo/Estatus representa membresia Cava.

## Escritura durante transicion
- Altas nuevas de socio deben requerir/obtener ClienteID canonico cuando Gate 12C lo implemente.
- Email/Telefono/NombreCompleto no deben convertirse en una segunda fuente maestra; cualquier compatibilidad temporal debe ser explicitamente derivada o mantenida sin autoridad funcional.
- No dual-write silencioso sin pruebas y contrato explicito.

## Dependencias preservadas
CavaSocios_Botellas.SocioID -> CavaSocios_Socios.SocioID
CavaSocios_Cargos.SocioID -> CavaSocios_Socios.SocioID
CavaSocios_Movimientos.SocioID -> CavaSocios_Socios.SocioID
Estas relaciones no cambian en Gate 12C.

## Gate 12C futuro - orden de implementacion permitido
A. Preflight de esquema y datos.
B. Si y solo si no existe relacion reutilizable: ADD ClienteID int NULL.
C. Crear indice para ClienteID si el plan de ejecucion lo justifica.
D. Crear FK ClienteID -> Cliente_Catalogo(ClienteID), inicialmente manteniendo nullable.
E. Backfill exclusivamente con crosswalk certificado.
F. Validar cobertura, duplicidades y orfandad.
G. Cambiar repositorio/servicio para resolver identidad desde ClienteID sin tocar SocioID de operaciones.
H. Mantener ClienteCRMID/NombreCompleto/Email/Telefono; su deprecacion/eliminacion queda fuera de Gate 12C.
I. E2E y rollback.

## Rollback
Como ClienteID se introduce nullable y las FK operativas permanecen sobre SocioID, un rollback funcional puede dejar de consumir ClienteID sin perder Botellas, Cargos o Movimientos. Cualquier DDL de rollback se definira y probara en Gate 12C; este Gate no lo ejecuta.

## Criterios para autorizar Gate 12C
- Confirmacion fisica de que no existe una columna ClienteID int reutilizable en CavaSocios_Socios.
- Determinacion de existencia/ausencia de crosswalk ClienteCRMID -> ClienteID.
- Cero propuesta de cast GUID->int.
- Plan de backfill determinista o estado explicito NO_DETERMINABLE para filas sin mapeo.
- Preservacion de las tres FK operativas por SocioID.
- Email/Telefono/NombreCompleto/ClienteCRMID permanecen fisicamente.
- Produccion no tocada.
