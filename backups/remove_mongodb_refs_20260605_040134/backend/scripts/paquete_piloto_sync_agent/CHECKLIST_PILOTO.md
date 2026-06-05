# ============================================================================
# CHECKLIST DE EJECUCIÓN - PILOTO SYNC AGENT
# ============================================================================
#
# Completar esta checklist durante la ejecución del piloto.
# Marcar con [x] cuando esté completo.
#
# ============================================================================

## PREREQUISITOS

- [ ] Python 3.9+ instalado
- [ ] Dependencias instaladas (pymssql, requests, pyyaml)
- [ ] Acceso SQL al servidor SoftRestaurant verificado
- [ ] Acceso a internet para conectar a HUB

## CONFIGURACIÓN

- [ ] Servidor SoftRestaurant registrado en HUB
  - Nombre: _______________________
  - ID: ___________________________

- [ ] Token de agente generado
  - Agent ID: _____________________
  - Fecha generación: _____________
  - Expira: _______________________

- [ ] Archivo config.yaml creado y completado
  - [ ] agent_id configurado
  - [ ] hub_url configurado
  - [ ] hub_token configurado
  - [ ] server_id configurado
  - [ ] sql_local completo

## TEST DE AUTENTICACIÓN

- [ ] Ejecutado: `python sync_agent_piloto.py --config config.yaml --test-only`
- [ ] Resultado: ✅ OK / ❌ ERROR
- [ ] Si error, motivo: _______________

## EJECUCIÓN 1 (Primera corrida)

- [ ] Fecha/hora: ___________________
- [ ] Fecha datos: __________________
- [ ] Comando: `python sync_agent_piloto.py --config config.yaml`

Resultados:
- [ ] Config cargada: ✅ / ❌
- [ ] Auth HUB: ✅ / ❌
- [ ] SQL conectado: ✅ / ❌
- [ ] Extracción: ✅ / ❌
- [ ] KPIs enviados: ✅ / ❌
- [ ] Heartbeat: ✅ / ❌

Acción UPSERT:
- INSERT: ___
- UPDATE: ___
- SKIP: ___
- REJECTED: ___

KPIs extraídos:
- Ventas: $___________
- PAX: ___
- Cheques: ___

Archivos generados:
- Log: _______________________________
- Reporte: ___________________________

## EJECUCIÓN 2 (Validar idempotencia)

- [ ] Fecha/hora: ___________________
- [ ] Fecha datos: __________________ (MISMA que ejecución 1)

Resultados:
- [ ] Todos los checks: ✅

Acción UPSERT:
- INSERT: ___ (debe ser 0)
- UPDATE: ___ (debe ser 0)
- SKIP: ___ (debe ser 1) ⬅️ IMPORTANTE
- REJECTED: ___

- [ ] ¿SKIP = 1? ✅ IDEMPOTENCIA CONFIRMADA / ❌ PROBLEMA

## EJECUCIÓN 3 (Fecha diferente)

- [ ] Fecha/hora: ___________________
- [ ] Fecha datos: __________________ (fecha DIFERENTE)
- [ ] Comando: `python sync_agent_piloto.py --config config.yaml --fecha YYYY-MM-DD`

Acción UPSERT:
- INSERT: ___ (debe ser 1)
- UPDATE: ___
- SKIP: ___
- REJECTED: ___

## EJECUCIÓN 4 (Idempotencia fecha diferente)

- [ ] Fecha/hora: ___________________
- [ ] Fecha datos: __________________ (MISMA que ejecución 3)

Acción UPSERT:
- INSERT: ___ (debe ser 0)
- SKIP: ___ (debe ser 1) ⬅️ IMPORTANTE

- [ ] ¿SKIP = 1? ✅ IDEMPOTENCIA CONFIRMADA / ❌ PROBLEMA

## EJECUCIÓN 5 (Validación final)

- [ ] Fecha/hora: ___________________
- [ ] Fecha datos: __________________

Acción UPSERT:
- INSERT: ___
- UPDATE: ___
- SKIP: ___
- REJECTED: ___

Resultado: ✅ OK / ❌ ERROR

## RESUMEN FINAL

| Ejecución | Fecha Datos | Acción Principal | Status |
|-----------|-------------|------------------|--------|
| 1 | | INSERT | |
| 2 | | SKIP | |
| 3 | | INSERT | |
| 4 | | SKIP | |
| 5 | | | |

Total errores: ___
Total INSERTs: ___
Total SKIPs: ___

## DICTAMEN DEL PILOTO

- [ ] ✅ PILOTO EXITOSO - Todas las ejecuciones OK, idempotencia confirmada
- [ ] ⚠️ PILOTO CON OBSERVACIONES - Explicar: _________________________
- [ ] ❌ PILOTO FALLIDO - Motivo: ____________________________________

## ARCHIVOS A ENTREGAR

- [ ] Esta checklist completada
- [ ] 5 archivos de log (.log)
- [ ] 5 archivos de reporte (.json)
- [ ] Screenshot de kpis_comercial en HUB (opcional)

## NOTAS Y OBSERVACIONES

___________________________________________________________________
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________

## FIRMA

Ejecutado por: _________________________
Fecha: ________________________________
