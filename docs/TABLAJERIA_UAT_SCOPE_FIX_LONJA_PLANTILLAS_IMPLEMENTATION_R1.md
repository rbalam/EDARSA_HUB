# EDARSAHUB BOS - Tablajerias UAT Scope Fix Lonja + Plantillas Implementation R1

Estado: implementation scaffold en Desarrollo.

Produccion: NO tocada.
SQL: NO ejecutado.
Deploy: NO ejecutado.

## Hallazgos UAT bloqueantes

1. No se pueden seleccionar unidades de negocio.
2. No se pueden seleccionar lonjas individualmente.
3. Las lonjas deben listarse disponibles/no procesadas desde almacen.
4. Se requiere una orden por lonja.
5. Los derivados deben precargarse desde plantilla.
6. Todo corte requiere doble control kg/pz.
7. Si hay gramaje definido, chef captura piezas y sistema calcula kg/g.
8. SKU pieza entra con costo cero.
9. SKU kg/gr recibe costo prorrateado.
10. SKU con costo fijo no participa en prorrateo.
11. Plantillas deben poder crearse, editarse, duplicarse, versionarse e inactivarse.

## Implementacion requerida

Backend:
- Agregar endpoints de contextos operativos sin hardcodear unidad.
- Agregar endpoint de lonjas disponibles/no procesadas.
- Agregar POST/PUT/DUPLICAR/INACTIVAR plantillas.
- Mantener version historica: plantilla publicada no se sobrescribe, se duplica/versiona.

Schemas:
- Agregar sku_kg_codigo, sku_pieza_codigo, gramaje_por_pieza_gramos, piezas_reales, costo_fijo, costo_fijo_unitario, prorratea_costo, lonja_id, almacen_origen_id, almacen_destino_id.

SQL versionado:
- Agregar tabla/columnas de lonjas disponibles y doble control sin ejecutar automaticamente.

Frontend:
- Exponer seleccion de unidad/contexto operativo.
- Exponer seleccion de lonja individual.
- Exponer creacion/edicion/duplicado/inactivacion de plantillas.

## Criterio de cierre

UAT no puede pasar hasta que estos puntos queden implementados y reprobados en Preview/Desarrollo.
