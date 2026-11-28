# SERVIDORES 6 — GATE 2
## CHAPUR Canonical Scope Design

**Estado:** DESIGN CONTRACT  
**Rama:** `Edarsahub_Desarrollo`  
**Produccion:** FUERA DE ALCANCE  
**SQL/DML/DDL:** NO AUTORIZADO EN ESTE GATE

## 1. Evidencia de entrada

Gate 1 certifico en READ_ONLY que:

- existen tres conexiones relacionadas con CHAPUR/ENTERPRISE;
- `CHAPUR BACKOFFICE` y `CHAPUR NORTE` no tienen `EmpresaID/empresa_id` canonico;
- no existe ninguna fila en `Unidades_Negocio` vinculada a esas conexiones;
- no existen empresas candidatas CHAPUR en `Sistema_Empresas`;
- no existen sucursales candidatas CHAPUR/NORTE en `Sistema_Sucursales`;
- la version `ENTERPRISE` existe y esta activa;
- `CHAPUR NORTE.visible_en_operaciones=false` ya fue certificado operacionalmente.

**Decision Gate 1:** `NO_MAPPING_FOUND`.

## 2. Principio arquitectonico

EDARSAHUB BOS conserva dos dimensiones separadas:

1. **Empresa / Unidad / Sucursal** = eje funcional y de autorizacion.
2. **Servidor / Conexion** = dimension tecnica de conectividad.

Servidores no se convierte en owner de Empresa, Sucursal o Unidad. Solo consume las relaciones canonicas existentes.

## 3. Fuentes canonicas obligatorias

| Concepto | Fuente canonica | Regla |
|---|---|---|
| Empresa | `dbo.Sistema_Empresas` | Reutilizar; no duplicar catalogo |
| Sucursal | `dbo.Sistema_Sucursales` | Debe pertenecer a Empresa canonica |
| Unidad | `dbo.Unidades_Negocio` | Debe tener codigo canonico y `server_id` |
| Conexion | `dbo.Servidores_Conexiones` | Dimension tecnica |
| Empresa desde Unidad | `resolver_empresa_id(unidad_codigo)` | Reutilizar helper |
| Sucursal desde Unidad/Server | `resolver_sucursal_id(server_id, sucursal_origen_id)` | Reutilizar helper |
| Contexto usuario | `backend/core/user_access_context.py` + RBAC SQL | Backend autoritativo |

No se permite una tabla paralela `Chapur_*`, ni mapping hardcodeado por nombre.

## 4. Contrato minimo para canonizar CHAPUR

La canonizacion de una conexion CHAPUR solo puede ocurrir cuando exista evidencia empresarial suficiente para crear o reutilizar, en este orden:

```text
Empresa canonica
  -> Sucursal canonica
    -> Unidad_Negocio canonica
      -> server_id = Servidores_Conexiones.id
```

Campos minimos funcionales:

### Empresa
- `CodigoEmpresa`: codigo estable de negocio, no derivado del nombre del servidor.
- `NombreEmpresa`.
- `NombreComercial`.
- `Activo`.

### Sucursal
- `EmpresaID` canonico.
- `CodigoSucursal`: estable dentro de la empresa.
- `NombreSucursal`.
- `Activo`.

### Unidad
- `codigo`: codigo canonico unico.
- `nombre`.
- `server_id`: UUID de `Servidores_Conexiones`.
- `sucursal_origen_id`: solo cuando el sistema origen realmente maneje multiples sucursales/instancias y exista evidencia.
- `system_type`.
- `activo`.

### Conexion
La conexion existente debe conservar su identidad. No crear una conexion nueva si ya existe.

## 5. Reglas fail-closed

La operacion debe detenerse si ocurre cualquiera de estas condiciones:

- no existe evidencia empresarial para decidir Empresa;
- hay mas de una Empresa plausible;
- no existe CodigoEmpresa estable;
- la Sucursal no puede resolverse univocamente;
- se intenta usar el nombre `CHAPUR NORTE` como prueba de identidad empresarial;
- se intenta asignar `EmpresaID` directamente a la conexion sin Unidad/Sucursal canonica;
- se intenta activar `visible_en_operaciones=true` antes de que la Unidad sea resoluble por los helpers canonicos;
- se intenta crear catalogos, tablas puente o IDs hardcodeados;
- el usuario no tiene permiso administrativo explicito del dominio;
- cualquier write no puede auditarse e invertirse.

## 6. Idempotencia

La futura alta debe ser idempotente:

- buscar Empresa por su clave canonica antes de insertar;
- buscar Sucursal por Empresa + CodigoSucursal;
- buscar Unidad por `codigo` y validar que el `server_id` coincida;
- si la entidad ya existe con los mismos datos, retornar `NO_CHANGE`;
- si existe con datos incompatibles, retornar `CONFLICT` y no sobrescribir silenciosamente;
- nunca crear una segunda conexion para resolver un conflicto de scope.

## 7. RBAC

La autorizacion se resuelve en backend.

- Servidores mantiene su permiso funcional vigente.
- La alta/modificacion de Empresa/Sucursal/Unidad requiere permisos explicitos del dominio correspondiente.
- No confiar en IDs enviados por frontend como autorizacion.
- Tras la canonizacion, el acceso se deriva de los contextos RBAC existentes de Empresa/Unidad/Sucursal.
- Compatibilidad con `allowed_servers` se conserva mientras exista; no se elimina en este Gate.

## 8. Auditoria

Toda futura mutacion debe registrar al menos:

- usuario;
- timestamp UTC;
- empresa/sucursal/unidad afectadas;
- conexion afectada;
- estado anterior;
- estado posterior;
- motivo;
- resultado;
- correlation/job id.

Los secretos de conexion no forman parte del evento de auditoria.

## 9. Secuencia futura de alta

1. Discovery empresarial READ_ONLY.
2. Resolver identidad legal/comercial de Empresa con evidencia.
3. Resolver Sucursal real.
4. Proponer codigo canonico de Unidad.
5. Validar no duplicidad en los tres catalogos.
6. Aprobar RBAC.
7. Crear/reutilizar Empresa.
8. Crear/reutilizar Sucursal.
9. Crear/reutilizar Unidad enlazada al `server_id` existente.
10. Ejecutar `resolver_empresa_id` y `resolver_sucursal_id` como post-check.
11. Solo si ambos resuelven de forma univoca, evaluar habilitar `visible_en_operaciones`.
12. Post-audit READ_ONLY.

## 10. Decision especifica para CHAPUR hoy

Con la evidencia actual **NO esta autorizada ninguna alta fisica**.

Faltan como minimo:

- identidad empresarial real que deba representar EDARSAHUB;
- CodigoEmpresa canonico;
- sucursal real y CodigoSucursal;
- decision de si `CHAPUR BACKOFFICE` y `CHAPUR NORTE` representan la misma empresa/sucursal, dos sucursales o solo dos endpoints tecnicos;
- codigo canonico de Unidad;
- significado real de `CHAPUR 58` respecto de las dos conexiones API_LOCAL.

Hasta resolver esos datos:

- `CHAPUR NORTE.visible_en_operaciones=false` debe permanecer;
- `CHAPUR BACKOFFICE.visible_en_operaciones=false` debe permanecer;
- no deben existir Unidades CHAPUR inventadas;
- no debe inferirse Empresa/Sucursal por texto del nombre.

## 11. Criterio de salida de Gate 2

Gate 2 queda aprobado cuando este contrato permanece alineado con arquitectura y no introduce implementacion fisica.

El siguiente Gate permitido es:

**Gate 3 — CHAPUR Business Identity Discovery (READ_ONLY / evidence gathering).**

Gate 3 debe buscar evidencia real de identidad empresarial y sucursal fuera de heuristicas de nombres, sin escribir datos.
