# BOS Status Engine Contract

## Objetivo
El status para Direccion debe derivarse de evidencia verificable y no de porcentajes manuales.

## Regla de certificacion
Un milestone solo cuenta como completado cuando al menos una evidencia autorizada cumple simultaneamente: status INTEGRATED, certification CERTIFIED, work_completion COMPLETE, quality_gate PASS, percent_complete 100, production_touched false y blockers vacio.

PENDING_AUDIT_EVIDENCE, BLOCKED, NOT_CERTIFIED, resultados parciales o evidencia faltante no cuentan como completados.

## Porcentajes
El porcentaje de un frente es la proporcion ponderada de milestones certificados. El porcentaje global es la proporcion ponderada de todos los milestones certificados. El programa solo puede marcarse CERTIFIED cuando todos los frentes y todos sus milestones requeridos estan certificados.

## Separacion de responsabilidades
Este motor no lee GitHub, SQL, Mongo, red, archivos ni variables de entorno. Recibe evidencia ya obtenida por un adaptador autorizado. Esto permite probar la aritmetica y las reglas de gobierno de forma determinista.

## Siguiente gate
Crear un manifest canónico de milestones BOS V1.0 y un adaptador read-only que recolecte los resultados autorizados y produzca el snapshot ejecutivo vivo.
