# EDARSAHUB BOS - Core Slimming / Modularization Policy V1

## Decision
`backend/core` queda congelado para crecimiento funcional nuevo. El objetivo es adelgazar y desacoplar el Core mediante refactorizacion y modularizacion progresivas, sin un big-bang y sin cambiar comportamiento por el solo hecho de mover archivos.

## Regla ejecutable
El Worker Universal debe rechazar por defecto cualquier accion `write_file` cuyo destino sea un archivo inexistente bajo `backend/core/**`. Las modificaciones controladas de archivos existentes siguen permitidas con las protecciones normales del Worker.

No existe bypass ordinario. Si en el futuro se demuestra que una nueva pieza es verdaderamente transversal y debe vivir en Core, la excepcion requiere un gate explicito que cambie conscientemente esta politica y sus pruebas. No se autoriza que una tarea funcional se auto-conceda una excepcion.

## Donde debe vivir codigo nuevo
1. Logica de un dominio: en el modulo/dominio correspondiente.
2. Integraciones/proveedores/adaptadores: fuera del Core, siguiendo las convenciones ya existentes auditadas del repositorio.
3. Agent Harness, Marketing/CX y Mobile: fuera de `backend/core`; la ubicacion exacta se fija despues de auditar la estructura actual para no crear otra convencion paralela.
4. Core conserva solamente contratos e infraestructura realmente transversales que ya existan mientras se ejecuta su extraccion gradual.

## Refactorizacion progresiva del Core
Antes de mover codigo existente: construir grafo de imports/dependencias; medir consumidores; clasificar cada pieza como KEEP_CORE / EXTRACT_DOMAIN / EXTRACT_PLATFORM / ADAPTER / LEGACY_REMOVE; identificar ciclos y side effects; definir contrato publico y pruebas de caracterizacion.

Cada extraccion se hace en gate pequeno: pruebas del comportamiento actual; nueva ubicacion fuera del Core; compatibilidad temporal si es necesaria; migracion de consumidores; regresion; evidencia de imports restantes; retirar facade/legacy solo cuando consumidores=0.

## Prohibiciones
No refactor big-bang. No mover archivos masivamente por limpieza estetica. No duplicar implementaciones. No crear fuentes canonicas nuevas sin auditoria. No introducir Mongo. No debilitar RBAC/policies. No crear otro pseudo-Core llamado shared/common/utils sin frontera explicita.

## Agent Harness
AH2-AH12 deben cumplir esta politica. Ningun componente nuevo del Agent Registry, Skill Registry, Planner, Router, Red Team, Marketing/CX o Mobile puede agregarse como archivo nuevo bajo `backend/core`. Los adaptadores existentes en Core pueden seguir funcionando mientras se planifica su extraccion compatible.

## Criterios de aceptacion
Nueva funcionalidad en `backend/core/**` => Worker DENY. Edicion/refactor controlado de archivo Core existente => permitido bajo hashes, paths, tests y gates normales. Archivo nuevo fuera de Core => no bloqueado por esta politica. Tests del guard en PASS. Production untouched.

## Objetivo de largo plazo
Core pequeno, estable y aburrido: contratos transversales minimos. Dominios, agentes, integraciones y experiencias evolucionan fuera de Core con fronteras explicitas.
