# SERVIDORES 6 — GATE 3
## CHAPUR Business Identity Discovery

**Estado:** CLOSED — IDENTITY_UNRESOLVED  
**Modo:** READ_ONLY evidence consolidation  
**Produccion:** NO TOCADA

## 1. Objetivo

Determinar, sin heuristicas por nombre y sin escrituras, si las conexiones CHAPUR existentes pueden vincularse a una Empresa, Sucursal y Unidad canonicas de EDARSAHUB.

## 2. Evidencia consolidada

### CHAPUR BACKOFFICE
- conexion tecnica existente;
- tipo `API_LOCAL`;
- `system_type=ENTERPRISE`;
- base logica `CHAPUR`;
- version ENTERPRISE activa;
- `EmpresaID` ausente;
- `empresa_id` vacio;
- sin `Unidad_Negocio`;
- sin `Sistema_SucursalServidorMapeo`;
- sin configuracion relacional de sucursal;
- sin crosswalk de ventas sincronizadas a Empresa/Sucursal;
- `visible_en_operaciones=false`.

### CHAPUR NORTE
- conexion tecnica existente;
- tipo `API_LOCAL`;
- `system_type=ENTERPRISE`;
- base logica `CHAPUR`;
- version ENTERPRISE activa;
- `EmpresaID` ausente;
- `empresa_id` vacio;
- sin `Unidad_Negocio`;
- sin `Sistema_SucursalServidorMapeo`;
- sin configuracion relacional de sucursal;
- sin crosswalk de ventas sincronizadas a Empresa/Sucursal;
- `visible_en_operaciones=false` certificado operacionalmente.

### CHAPUR 58
- existe evidencia historica de una conexion creada como endpoint tecnico MPRO;
- la evidencia posterior no la encuentra como registro actual;
- no existe evidencia canonica que la vincule a Empresa, Sucursal o Unidad;
- no existe evidencia suficiente para declararla padre de BACKOFFICE o NORTE;
- su similitud nominal con CHAPUR no constituye identidad empresarial.

## 3. Evidencia negativa relevante

Las auditorias READ_ONLY historicas y actuales muestran:

- 0 empresas candidatas CHAPUR en `Sistema_Empresas`;
- 0 sucursales candidatas CHAPUR/NORTE en `Sistema_Sucursales`;
- 0 unidades vinculadas a las conexiones CHAPUR;
- 0 mappings canonicos de sucursal;
- 0 configuraciones relacionales de sucursal para los server_id CHAPUR;
- 0 filas de ventas sincronizadas que aporten `EmpresaID/SucursalID` para CHAPUR;
- 0 crosswalks de scope empresarial utilizables.

## 4. Decision

```text
BUSINESS_IDENTITY_RESOLVED = NO
CANONICAL_COMPANY_FOUND = NO
CANONICAL_BRANCH_FOUND = NO
CANONICAL_UNIT_FOUND = NO
CHAPUR58_PARENT_RELATION_PROVEN = NO
AUTO_MAPPING_ALLOWED = NO
```

Los nombres `CHAPUR`, `CHAPUR NORTE`, `CHAPUR BACKOFFICE` o `CHAPUR 58` no se usarán como prueba de identidad empresarial.

## 5. Estado operativo obligatorio

Hasta contar con evidencia empresarial externa o corporativa suficiente:

- CHAPUR BACKOFFICE permanece fuera de Operaciones;
- CHAPUR NORTE permanece fuera de Operaciones;
- no se crea Empresa CHAPUR;
- no se crea Sucursal CHAPUR/NORTE;
- no se crea Unidad CHAPUR;
- no se reactiva CHAPUR 58;
- no se crea mapping `Sistema_SucursalServidorMapeo`;
- no se asignan `EmpresaID` ni `empresa_id` por inferencia.

## 6. Evidencia necesaria para avanzar

El siguiente Gate solo puede abrirse cuando exista al menos una fuente empresarial autoritativa que permita determinar:

1. razon social o entidad empresarial real;
2. CodigoEmpresa que EDARSAHUB debe utilizar;
3. sucursal fisica u operativa real;
4. CodigoSucursal estable;
5. relacion entre BACKOFFICE y NORTE;
6. si ambos endpoints representan una sola sucursal, sucursales distintas o capas tecnicas de la misma operacion;
7. si CHAPUR 58 tiene alguna relacion vigente o debe permanecer solo como historial.

Fuentes aceptables:
- contrato o alta corporativa;
- catalogo administrativo autorizado;
- fuente maestra ERP/financiera;
- documentacion del proveedor/sistema validada por EDARSA;
- decision explicita de Direccion/Sistemas respaldada por evidencia.

## 7. Criterio de salida

Gate 3 queda cerrado con:

```text
STATUS=IDENTITY_UNRESOLVED
DECISION=NO_CANONICAL_BUSINESS_EVIDENCE
SAFE_STATE=CHAPUR_API_LOCAL_HIDDEN_FROM_OPERATIONS
```

El siguiente Gate permitido es **Gate 4 — Business Identity Intake & Approval**, no una migracion ni un writer automatico.
