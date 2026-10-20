# SERVIDORES 6 — GATE 4
## CHAPUR Business Identity Intake & Approval

**Estado:** CONTRACT_READY — AWAITING_BUSINESS_EVIDENCE  
**Produccion:** FUERA DE ALCANCE  
**Mutaciones SQL:** NO AUTORIZADAS EN ESTE GATE

## 1. Proposito

Definir el contrato gobernado mediante el cual una identidad empresarial real puede ser propuesta y aprobada antes de canonizar CHAPUR en Empresa -> Sucursal -> Unidad -> Conexion.

Gate 4 no crea Empresa, Sucursal, Unidad, mappings ni conexiones.

## 2. Precondicion

Gate 3 cerro con:

```text
BUSINESS_IDENTITY_RESOLVED=NO
CANONICAL_COMPANY_FOUND=NO
CANONICAL_BRANCH_FOUND=NO
CANONICAL_UNIT_FOUND=NO
CHAPUR58_PARENT_RELATION_PROVEN=NO
AUTO_MAPPING_ALLOWED=NO
```

Por tanto, cualquier intake debe aportar evidencia nueva; repetir nombres tecnicos no satisface la precondicion.

## 3. Payload minimo de intake

Una propuesta debe contener:

- `legal_entity_name`: razon social o entidad empresarial real;
- `commercial_name`: nombre comercial;
- `empresa_code_proposed`: CodigoEmpresa estable propuesto;
- `branch_name`: sucursal fisica/operativa real;
- `branch_code_proposed`: CodigoSucursal estable propuesto;
- `unit_code_proposed`: codigo canonico de Unidad;
- `unit_name_proposed`;
- `connection_ids`: UUIDs existentes que se propone vincular;
- `endpoint_roles`: rol de cada conexion (por ejemplo backoffice, sucursal, integracion), sustentado por evidencia;
- `chapur58_disposition`: `HISTORICAL_ONLY`, `RELATED` o `UNRESOLVED`; nunca inferido;
- `evidence_refs`: referencias a fuentes empresariales autoritativas;
- `requested_by`;
- `business_justification`.

No se admiten passwords, tokens, API keys ni secretos en el intake.

## 4. Evidencia aceptable

Al menos una referencia debe provenir de una fuente empresarial autoritativa:

- contrato/alta corporativa;
- catalogo administrativo autorizado;
- ERP o fuente maestra financiera;
- documentacion validada del proveedor;
- decision formal de Direccion/Sistemas con soporte documental.

Los nombres de conexiones, URLs, puertos, database_name o coincidencias de texto no constituyen por si solos evidencia empresarial.

## 5. Estados

```text
DRAFT
  -> SUBMITTED
    -> EVIDENCE_VALIDATED
      -> APPROVED
        -> READY_FOR_CANONICALIZATION
```

Salidas negativas:

```text
REJECTED
NEEDS_EVIDENCE
CONFLICT
CANCELLED
```

No existe transicion automatica de `SUBMITTED` a `APPROVED`.

## 6. Separacion de funciones

- solicitante: propone identidad y aporta evidencia;
- validador: comprueba que la evidencia corresponde a la entidad/sucursal propuesta;
- aprobador: autoriza la identidad empresarial;
- ejecutor tecnico futuro: materializa exclusivamente la propuesta aprobada.

Una misma accion no debe autoaprobarse por poseer permisos acumulados cuando el flujo exija etapas distintas.

## 7. RBAC

El backend es autoritativo.

- lectura de Servidores: permiso vigente de lectura;
- cambios de conexion: permisos explicitos `SERVIDORES_CREAR/EDITAR` segun corresponda;
- Empresa/Sucursal/Unidad deben usar permisos de su dominio canonico cuando ese writer exista;
- si no existe permiso explicito para una etapa, la operacion falla cerrada;
- IDs recibidos del frontend no equivalen a autorizacion.

Gate 4 no introduce permisos nuevos sin auditoria RBAC previa.

## 8. Validaciones antes de aprobar

1. Empresa propuesta no contradice una Empresa canonica existente.
2. CodigoEmpresa es estable y no esta ocupado por otra identidad.
3. Sucursal pertenece univocamente a la Empresa.
4. CodigoSucursal no colisiona dentro de la Empresa.
5. Unidad propuesta no duplica una Unidad existente.
6. Cada `connection_id` existe y conserva su identidad tecnica.
7. Ninguna conexion queda asignada a dos scopes incompatibles.
8. BACKOFFICE y NORTE tienen roles explicitamente definidos o quedan `UNRESOLVED`.
9. CHAPUR 58 no se reactiva por este flujo.
10. La propuesta no habilita `visible_en_operaciones`.

Cualquier ambiguedad produce `NEEDS_EVIDENCE` o `CONFLICT`.

## 9. Idempotencia

La misma propuesta, evidencia y scope aprobados deben producir el mismo fingerprint logico.

Un reintento:
- no crea duplicados;
- no genera nuevos IDs empresariales por conveniencia;
- no cambia conexiones existentes;
- retorna el estado vigente si no hay diferencia material.

## 10. Auditoria minima

Registrar:
- correlation/intake id;
- solicitante;
- validador;
- aprobador;
- timestamps UTC;
- fingerprint de la propuesta;
- referencias de evidencia, no secretos;
- estado anterior/posterior;
- motivo de rechazo/conflicto si aplica.

## 11. Salida hacia el writer

Solo `READY_FOR_CANONICALIZATION` puede alimentar un futuro Gate de escritura.

El writer futuro debe:
1. ejecutar pre-audit READ_ONLY;
2. reutilizar Empresa/Sucursal/Unidad si ya existen y coinciden;
3. crear solo entidades aprobadas que realmente falten;
4. enlazar la Unidad al `server_id` existente;
5. ejecutar resolvers canonicos como post-check;
6. dejar `visible_en_operaciones=false`;
7. requerir un Gate separado para habilitar Operaciones.

## 12. Estado CHAPUR actual

Mientras no exista intake aprobado:

```text
CHAPUR_BACKOFFICE=HIDDEN_FROM_OPERATIONS
CHAPUR_NORTE=HIDDEN_FROM_OPERATIONS
CHAPUR58=DO_NOT_REACTIVATE
CANONICALIZATION=BLOCKED
REASON=BUSINESS_EVIDENCE_REQUIRED
```

## 13. Criterio de salida

Gate 4 se considera tecnicamente preparado cuando este contrato pasa controles del repositorio.

La ejecucion empresarial permanece bloqueada hasta recibir evidencia autoritativa suficiente.

Siguiente Gate condicionado:
**Gate 5 — Canonicalization Writer Design**, solo despues de `READY_FOR_CANONICALIZATION`.
