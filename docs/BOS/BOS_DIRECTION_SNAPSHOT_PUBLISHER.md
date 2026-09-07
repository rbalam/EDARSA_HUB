# BOS Direction Snapshot Publisher - Gate 4

## Objetivo
Convertir la evidencia read-only de Gate 3 en un snapshot JSON canonico y publicable para Direccion.

## Flujo
1. El collector lee exclusivamente los resultados terminales A-G definidos por el manifest.
2. El motor calcula porcentaje y certificacion desde evidencia.
3. El publisher agrega `generated_at_utc` recibido explicitamente.
4. El snapshot se normaliza a tipos JSON nativos antes de ser retornado.
5. El JSON se escribe de manera atomica al path indicado por el caller.

## Invariante de publicacion
El objeto retornado por `publish_direction_snapshot` debe ser semanticamente identico al JSON releido desde disco. Listas, objetos, numeros, booleanos y null usan tipos compatibles con JSON; no se exponen tuplas internas.

## Fail closed
Si faltan evidencias, el snapshot se publica con los gates faltantes y nunca inventa 100%. El publisher no convierte resultados parciales en certificaciones.

## I/O permitido
- Lectura: directorio local de resultados terminales.
- Escritura: un archivo JSON de snapshot en el path explicitamente proporcionado.
- Sin SQL, Mongo, red, Tablero Ejecutivo, Production ni mutacion del Worker.

## CLI
`backend/tools/publish_bos_direction_snapshot.py` recibe `--results-dir`, `--output-file` y `--generated-at-utc`. No contiene rutas de runtime hardcodeadas.

## Siguiente gate
Gate 5 debe conectar este publisher a ejecucion recurrente autorizada, conservar historico y exponer `latest` sin modificar el Tablero Ejecutivo congelado.
