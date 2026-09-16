# Cavas Corporativas - Gate 12E - Implementacion BOS Persona Link

## Decision
CavaSocios_Socios es membresia operativa, no identidad. La identidad transversal es Gobierno_Persona. El unico enlace nuevo permitido es PersonaID BIGINT NULL -> Gobierno_Persona(PersonaID). No se agrega ClienteID directo y no se crea Entidad_Catalogo.

## Evidencia previa
Gate 12C confirmo fisicamente Gobierno_Persona y Gobierno_PersonaVinculo. Gate 12D confirmo que CavaSocios_Socios no tiene enlace a Persona. La auditoria determinista Gate 12E encontro 2 socios actuales y 0 coincidencias unicas por email, telefono o combinacion email+telefono. Por tanto, no existe base para poblar PersonaID sin adivinar.

## Implementacion de este Gate
Se agrega una migracion idempotente y no destructiva que crea PersonaID nullable, FK a Gobierno_Persona e indice filtrado. No ejecuta backfill. Los dos socios existentes quedan explicitamente pendientes de conciliacion hasta que exista evidencia determinista.

## Lo que permanece intacto
- SocioID sigue siendo PK operacional.
- CavaSocios_Botellas, CavaSocios_Cargos y CavaSocios_Movimientos siguen relacionandose por SocioID.
- ClienteCRMID, NombreCompleto, Email y Telefono no se eliminan aun.
- No se toca Produccion.

## Etapa 2 - poblacion controlada
Solo se podra asignar PersonaID cuando una regla certificada produzca exactamente una PersonaID valida. Resultado sin match o ambiguo: PersonaID permanece NULL y se reporta para conciliacion. Matching parcial, fuzzy o por suposicion queda prohibido.

## Siguiente hito
Tras CERTIFIED + PASS de este Gate, ejecutar la migracion exclusivamente en Desarrollo mediante el writer/mecanismo canonico autorizado y luego hacer post-audit SQL de FK, indice, nullability y conteos. La ejecucion de DDL queda fuera de este job.
