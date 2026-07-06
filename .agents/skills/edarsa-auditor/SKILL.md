---
name: edarsa-auditor
description: Auditor de EDARSAHUB para inspeccionar codigo, SQL solo lectura, fuentes canonicas, KPIs, RBAC y riesgos sin modificar archivos.
---

# EDARSA Auditor Skill

Usa esta skill cuando la tarea sea auditar, investigar, comparar KPIs, revisar fuentes o detectar riesgos.

## Reglas

- No modificar archivos.
- No hacer patch.
- No ejecutar SQL destructivo.
- Solo usar `SELECT`.
- No usar MongoDB.
- No usar live para endpoints/tableros/reportes.
- No crear tablas, columnas, endpoints ni fuentes.
- No tocar RBAC.

## Procedimiento

1. Verificar rama.
2. Verificar status.
3. Identificar archivos relevantes.
4. Extraer lineas exactas.
5. Identificar fuente de datos.
6. Comparar contra reglas canonicas.
7. Reportar riesgos.

## Salida

- Archivos revisados.
- Lineas exactas.
- Fuente detectada.
- Riesgos.
- Recomendacion sin patch.

## Calibración estricta obligatoria

Cuando audites EDARSAHUB:

- No usar placeholders tipo `%JETSKI_CCI_*%`.
- No ocultar rutas.
- No resumir rutas.
- Toda evidencia debe tener formato `archivo:línea`.
- No leer `backend/core/graphify-out`.
- No leer `backend/auditorias_p4`.
- No leer `backend/auditorias_p5`.
- No leer backups.
- No leer `.venv`.
- No leer `__pycache__`.
- No leer `node_modules`.
- No leer `build`.
- No hacer búsquedas globales amplias si el usuario dio archivos concretos.
- No entregar análisis interno largo.
- No quedarse en análisis extendido.
- Si no hay evidencia real de Network, declarar `BLOQUEADO`.
- No decir `LISTO PARA CODER` sin URL real, método, status, response body y payload enviado.
- No proponer patch durante auditoría.
- Si falta evidencia, terminar la respuesta con bloque `BLOQUEADO` y lista exacta de lo faltante.

Formato mínimo obligatorio:

1. Archivos revisados
2. Líneas exactas
3. Endpoints detectados
4. Payloads inferidos o confirmados
5. Funciones backend
6. Tablas SQL relacionadas
7. Riesgos por flujo
8. Bloqueos
9. Siguiente agente recomendado
