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
