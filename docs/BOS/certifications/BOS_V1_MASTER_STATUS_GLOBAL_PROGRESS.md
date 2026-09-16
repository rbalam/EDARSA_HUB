# BOS V1 - Master Status Global Progress

Evidence-only master status.

El Universal Worker debe completar este dossier usando el programa estrategico BOS V1 y resultados terminales reales.

## Reglas
- No inventar porcentaje.
- No inferir cierre por nombre de archivo.
- Solo aceptar gates cerrados con evidencia terminal compatible.
- No doble contar subgates y gate padre.
- Separar avance funcional, avance de certificacion y avance global.
- Documentar formula exacta de porcentaje.
- Si no hay pesos oficiales, ponderacion uniforme por gate obligatorio del programa.
- Gate C R3: validar contra su resultado terminal antes de marcarlo cerrado.

## Salida obligatoria
- program_scope
- weighting_method
- gates_total
- gates_complete
- gates_partial
- gates_blocked
- gates_not_started
- global_percent_complete
- certified_percent_complete
- functional_evidence_percent_complete
- blockers[]
- next_gate
- production_touched=false
