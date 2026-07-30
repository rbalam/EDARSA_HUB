# Auditoría de proyecciones e histórico comercial

Fecha: 2026-07-30  
Rama auditada: `Edarsahub_Desarrollo`  
Commit base auditado: `776269f7afe090790e0c89c6ce08ce71064e626c`

## Objetivo

Recuperar el algoritmo existente de proyección de ventas y determinar si la historia comercial de las cinco unidades está certificada desde su primer día disponible de operación.

Unidades: `130MID`, `130QRO`, `ORIGEN`, `CIENFUEGOS`, `ESTELAR`.

## Resultado ejecutivo

### Proyecciones

Estado: **PARCIALMENTE IMPLEMENTADO / NO CERTIFICADO PARA V1.0**.

Existe una implementación nueva y compartida en:

- `backend/modules/comercial_v2/periodos.py`
- `backend/modules/comercial_v2/periodos_routes.py`
- `backend/tests/test_comercial_v2_periodos.py`

El contrato declara que Ejecutivo, Comercial e Inteligencia deben consumir la misma semántica. Sin embargo, la integración efectiva encontrada está concentrada en `frontend/src/pages/TableroEjecutivo.js`; no se encontró evidencia equivalente de consumo en las otras dos superficies.

#### Proyección diaria actual

Método implementado:

1. Consulta los 35 días anteriores.
2. Selecciona hasta tres fechas con el mismo día de semana.
3. Calcula su promedio.
4. Devuelve `max(venta_actual, promedio_días_equivalentes)`.
5. Asigna nivel de confianza según número de muestras.

Limitaciones:

- No utiliza curva intradía ni porcentaje real de avance de la jornada operativa.
- No utiliza ventas por hora.
- No utiliza hora de corte efectiva por unidad.
- Puede devolver una proyección igual al promedio histórico aun al inicio del día.
- No tiene pruebas de integración con datos reales POS.

#### Proyección mensual actual

Método implementado:

1. Conserva ventas reales acumuladas.
2. Agrupa días completos por día de semana.
3. Proyecta fechas pendientes con el promedio del mismo día de semana.
4. Si faltan muestras del mes, usa días equivalentes recientes de hasta 120 días previos.
5. Expone detalle, método y nivel de confianza.

Fortalezas:

- No inventa proyección para meses cerrados.
- Separa ventas reales y ventas pendientes proyectadas.
- Tiene pruebas unitarias básicas.

Limitaciones:

- La consulta marca todas las filas históricas como `completo=True`; no existe una prueba explícita de cierre operativo por fecha.
- La vista consultada es `vw_Comercial_KPIs_Diarios_v2_Runtime`; debe verificarse que `ventas_total` corresponda al KPI sin propina aprobado.
- No incluye estacionalidad intermensual, tendencia ponderada ni eventos.
- No hay validación cruzada contra valores POS reales.

#### Proyección anual

Estado: **NO IMPLEMENTADA EN EL CONTRATO V2 ACTUAL**.

Los únicos artefactos encontrados son scripts legacy/documentales que anualizan linealmente a 365 días y escriben sobre tablas históricas distintas. No deben adoptarse como solución canónica.

### Código legacy conflictivo

`frontend/src/pages/TableroEjecutivo.js` conserva un fallback de proyección mensual en frontend:

`(ventas / días_transcurridos) * días_proyectables`

También conserva una excepción hardcodeada para enero de 30 días. Aunque el contrato dinámico puede sobrescribir el valor, esta fórmula paralela sigue presente y contradice la regla de que el frontend solo presenta.

Conclusión: la proyección todavía tiene dos caminos potenciales y debe eliminarse el cálculo frontend una vez que el contrato backend esté certificado.

## Histórico comercial

Estado: **NO CERTIFICADO DESDE EL PRIMER DÍA DE OPERACIÓN**.

La evidencia SQL histórica disponible en el repositorio demuestra que, al 2026-06-30:

- `vw_Comercial_KPIs_Diarios_v2_Runtime` tenía 31 días en el rango auditado.
- `Sync_Sales` e Inteligencia Detalle solo tenían 8 días globales.
- `Sync_PAX_Detalle` no tenía filas en ese rango.
- Todas las unidades mostraban diferencias materiales entre KPI runtime y fuentes de detalle.

La auditoría existente cubre únicamente 2026-05-30 a 2026-06-29. No demuestra la fecha mínima real de operación de cada POS ni la continuidad completa hasta el presente.

Por tanto, no se puede certificar desde GitHub solamente que la historia esté completa desde el primer día disponible de operación. Se requiere consulta SELECT en:

- EDARSAHUB canónico.
- SoftRestaurant para `130MID`, `CIENFUEGOS`, `ESTELAR`.
- MPRO para `130QRO`, `ORIGEN`.

## Matriz de certificación requerida

| Unidad | Sistema | Primera fecha POS | Primera fecha KPI V2 | Última fecha cerrada | Días faltantes | Duplicados | Estado |
|---|---|---:|---:|---:|---:|---:|---|
| 130MID | SoftRestaurant | pendiente | pendiente | pendiente | pendiente | pendiente | NO CERTIFICADO |
| 130QRO | MPRO | pendiente | pendiente | pendiente | pendiente | pendiente | NO CERTIFICADO |
| ORIGEN | MPRO | pendiente | pendiente | pendiente | pendiente | pendiente | NO CERTIFICADO |
| CIENFUEGOS | SoftRestaurant | pendiente | pendiente | pendiente | pendiente | pendiente | NO CERTIFICADO |
| ESTELAR | SoftRestaurant | pendiente | pendiente | pendiente | pendiente | pendiente | NO CERTIFICADO |

## Hallazgos prioritarios

1. La proyección mensual V2 es la base correcta, pero aún no está certificada con datos reales.
2. La proyección diaria no es intradía; es un promedio de días equivalentes con piso en venta real.
3. No existe proyección anual canónica V2.
4. Tablero Ejecutivo mantiene cálculo de proyección en frontend.
5. No se encontró evidencia de que Comercial e Inteligencia consuman `periodos/contrato`.
6. La historia detallada y `Sync_Sales` estuvo incompleta frente al KPI runtime.
7. No existe certificación vigente de primera fecha POS, continuidad diaria y última fecha cerrada por unidad.

## Camino crítico aprobado

### Fase A — Certificación histórica de solo lectura

Ejecutar una auditoría SELECT que determine por unidad:

- `MIN(fecha_operacion)` y `MAX(fecha_operacion)`.
- número de días naturales y días con datos.
- huecos de calendario.
- duplicados por unidad/fecha.
- ventas con IVA y sin propina.
- propinas separadas.
- tickets y PAX.
- comparación KPI V2 contra POS en fechas de muestra.

Criterio de cierre: ninguna unidad se certifica hasta que la fecha mínima POS y la fecha mínima EDARSAHUB sean compatibles o exista una excepción documentada.

### Fase B — Unificación de contrato

- Comercial, Ejecutivo e Inteligencia deben consumir el mismo endpoint backend.
- Eliminar fórmulas de proyección del frontend.
- Confirmar semántica de `ventas_total` y `ventas_sin_propina`.
- No usar fuentes LIVE salvo overlay autorizado para ventas del día.

### Fase C — Proyección diaria V1.0

Construir proyección intradía por unidad usando:

- fecha_operacion.
- ventana operativa efectiva.
- curva acumulada histórica por intervalos horarios.
- últimos días equivalentes.
- venta real abierta.
- nivel de confianza y degradación segura sin base.

### Fase D — Proyección mensual V1.0

Conservar el modelo por día de semana, añadiendo:

- exclusión explícita de días incompletos.
- ponderación de historia reciente.
- control de unidades con poca historia.
- pruebas contra meses cerrados conocidos.

### Fase E — Proyección anual

Implementar únicamente después de certificar historia mensual suficiente. Debe combinar meses cerrados, mes actual proyectado y estacionalidad mensual; no usar anualización lineal de 365 días como modelo final.

## Criterio de aceptación final

Para los mismos filtros, unidad, periodo y corte:

- Comercial = Ejecutivo = Inteligencia.
- Diferencia monetaria = 0.00.
- Diferencia tickets = 0.
- Diferencia PAX = 0.
- Propinas separadas.
- Ventas con IVA y sin propina.
- Fecha_operacion como eje temporal.
- Proyección proveniente exclusivamente del backend canónico.

## Decisión

El frente de proyecciones e histórico comercial permanece **ABIERTO**. La siguiente acción correcta es ejecutar la auditoría SQL/POS de solo lectura y usar sus resultados para completar la matriz de certificación antes de modificar el algoritmo.