# EDARSAHUB — Memoria permanente de errores corregidos
## Operaciones / Inventarios / Análisis / Compras / Auditoría

Estado: obligatorio para nuevos cambios en estos dominios.

## Propósito

Evitar la repetición de bugs de arquitectura, lógica, alcance, sincronización,
fuentes de datos, RBAC y diagnóstico ya resueltos durante EDARSAHUB V1.0.

Una corrección no se considera aprendida si solo quedó en un commit o chat.
Debe convertirse en invariante y prueba.

# 1. Fuente única de verdad

Inventarios físicos, movimientos, ventas y compras son dominios separados.

Cada uno conserva su fuente canónica y los reportes cruzan esas fuentes sin
crear una segunda verdad.

Prohibido:

- consultas POS LIVE desde dashboards/reportes;
- MongoDB como fallback;
- reconstrucciones paralelas;
- mocks productivos;
- tablas duplicadas;
- valores hardcodeados;
- usar backups como fuente.

# 2. SoftRestaurant single-tenant

Error histórico:
el frontend enviaba `sucursal=SoftRestaurant` y el backend aplicaba el filtro
literal sobre filas cuyo campo sucursal estaba vacío, produciendo 0 resultados.

Regla:

- determinar si el servidor es compartido mediante configuración canónica;
- si es single-tenant, `server_id` delimita la unidad;
- no usar el nombre del sistema como filtro funcional.

# 3. MPRO shared-server

Error histórico:
varias unidades comparten servidor y códigos de almacén.

Reglas:

- utilizar `sucursal_origen_id` de `dbo.Unidades_Negocio`;
- no mezclar ORIGEN/QRO u otras unidades del mismo servidor;
- header y detalle físico deben compartir el mismo scope;
- almacén sin sucursal no es identificador suficiente;
- `AC` es estado válido;
- `CA` es cancelado.

# 4. Llaves de inventario físico

Error histórico:
`server_id + folio` fue tratado como identidad suficiente.

Regla:

la identidad debe incorporar el contexto necesario de unidad, y en detalle
también almacén/producto.

Nunca volver a reducir una llave si permite colisiones entre unidades.

# 5. Snapshot ACTIVE / REPLACED

Error histórico:
se marcaba la fotografía previa como REPLACED antes de demostrar que la nueva
fotografía había quedado completa.

Resultado:
ante fallo POS o de insert, datos válidos podían quedar ocultos.

Reglas:

- snapshot nuevo es atómico;
- header sin detalle rechaza el snapshot;
- fallo de detalle provoca rollback;
- fallo parcial de headers provoca rollback;
- el snapshot previo permanece disponible;
- lectura puede recuperar REPLACED cuando no existe ACTIVE válido;
- preferencia normal: ACTIVE.

# 6. Productos con cantidad cero

Error histórico:
renglones válidos se eliminaban porque el algoritmo trataba cantidad cero como
ausencia.

Regla:

la pertenencia al inventario/catalogo es independiente del valor numérico.

Un SKU registrado con inventario 0 sigue siendo un SKU operativo y debe
participar en el análisis.

# 7. Restricciones históricas artificiales

No imponer ventanas arbitrarias como seis meses si la fuente canónica contiene
histórico válido requerido por el usuario.

Las ventanas de sincronización deben ser configurables y no convertirse en
reglas funcionales ocultas.

# 8. Movimientos

Error histórico:
MERGE construido contra columnas no existentes o semántica incorrecta terminó
en cero movimientos.

Reglas:

- inspeccionar esquema real;
- usar `core.inventarios.sync_movimientos_canonico`;
- resolver producto, almacén, sucursal y tipo;
- tipo de movimiento es DB-driven;
- SoftRestaurant debe resolver `idconcepto`;
- concepto desconocido queda pendiente;
- no inventar IDs;
- no descartar silenciosamente registros no resolubles.

# 9. Almacenes

MPRO:
un mismo `Al_Cve_Almacen` puede existir en distintas sucursales.

SoftRestaurant:
el campo origen `tipo` no equivale automáticamente al catálogo canónico de
tipos de almacén.

Regla:
no reinterpretar códigos origen como semántica EDARSAHUB sin mapping probado.

# 10. Inventario físico y presentaciones

El análisis debe distinguir:

- insumo;
- presentación;
- unidad base;
- rendimiento/conversión;
- almacén de bodega;
- almacén de consumo.

No comparar caja contra pieza sin normalizar.

No tratar códigos de presentación y de insumo como si fueran necesariamente
el mismo SKU operativo.

# 11. Análisis de Inventarios

Debe consumir:

- inventario físico canónico;
- movimientos canónicos;
- ventas canónicas del dominio Comercial;
- filtros corporativos;
- unidades canónicas.

No hacer consultas paralelas para obtener “mejores” números.

Inventario inicial/final:

- no deben ser el mismo folio;
- deben tener cronología válida;
- deben corresponder al scope seleccionado.

# 12. Auditoría Operativa de Compras

Fuente: EDARSAHUB SQL.

Prohibido consultar POS LIVE desde:

- cálculo de pedido;
- productos para captura;
- auditoría operativa;
- detalle de movimientos;
- análisis de compras.

Las implementaciones legacy LIVE permanecen deshabilitadas.

# 13. Fuentes de Auditoría de Compras

Inventario:
`Compras_Inventarios_Fisicos_Sync`
y `Compras_Inventarios_Fisicos_Detalle_Sync`.

Movimientos:
`Inventario_Movimientos`
y `Inventario_MovimientosDetalle`.

Pedidos/recepciones:
tablas canónicas de Compras.

Ventas/consumos comerciales:
fuente comercial canónica vigente.

Nunca sustituir estas fuentes por queries LIVE o tablas paralelas.

# 14. Fórmulas de Auditoría

La fórmula solo es válida después de normalizar unidades y conversiones.

No asumir:

- pieza == caja;
- presentación == insumo;
- un código idéntico implica misma unidad de medida.

Cualquier cruce de faltante/sobrante debe considerar descripción,
presentación, unidad y conversión.

# 15. Captura provisional

Un inventario manual/provisional es una captura explícita distinta del
inventario sincronizado.

Debe conservar:

- origen;
- usuario;
- fecha;
- estado;
- trazabilidad.

No debe sobrescribir silenciosamente el inventario físico canónico.

# 16. RBAC

Todo:

- menú;
- tab;
- botón;
- ejecución;
- lectura;
- configuración;
- eliminación;
- aprobación;

requiere permiso backend y visibilidad frontend derivada.

SUPERADMIN debe tener al menos el acceso efectivo de ADMINISTRADOR.

# 17. Menú Operaciones / Inventarios

El menú se deriva del catálogo canónico.

No usar arrays o rutas frontend como fuente de autoridad.

Menú, capability, ruta y permiso deben representar el mismo objeto funcional.

No crear entradas duplicadas para resolver problemas de visibilidad.

# 18. MongoDB

No MongoDB productivo en estos dominios.

Pero una coincidencia textual `mongo`, un comentario, una columna histórica,
un stub o documentación antigua NO prueba dependencia runtime.

Clasificar antes de modificar.

No volver a ejecutar auditorías masivas sin nueva evidencia positiva.

# 19. Diagnóstico

Orden obligatorio:

1. reproducir;
2. trazar endpoint;
3. servicio;
4. repositorio;
5. tabla/vista;
6. filtros;
7. scope;
8. proceso;
9. causa;
10. cambio mínimo;
11. test de regresión.

No proponer patch antes de cerrar la evidencia.

# 20. Git / agentes

- no `git add .`;
- no reset global;
- no stash global;
- no `--no-verify`;
- preservar cambios ajenos;
- worktree registrado;
- claim activo;
- Validator antes de commit;
- integrator para Desarrollo;
- validar remote HEAD antes de push;
- outputs reproducibles en `/tmp/edarsahub-agents/<agent>/outputs/`.

# Criterio de reapertura

Una decisión histórica documentada solo se reabre cuando existe evidencia
positiva nueva:

- cambio de esquema;
- cambio de linaje;
- nuevo runtime;
- nuevo driver;
- nueva fuente;
- test que demuestra regresión;
- requisito de negocio explícitamente modificado.

Un grep, comentario o nombre legacy no basta.

# 21. INSUMOS Y PRESENTACIONES

## Error corregido

Tratar insumo y presentación como si fueran siempre la misma entidad física y
la misma unidad de medida.

Esto genera falsos faltantes y sobrantes.

Ejemplo operativo:

- compra: 1 caja;
- conversión: 24 piezas;
- receta/consumo: piezas.

## Regla

Antes de comparar inventario, compra, movimiento o consumo resolver:

1. código de presentación;
2. código de insumo;
3. unidad de compra;
4. unidad base;
5. factor de conversión;
6. rendimiento;
7. almacén origen;
8. almacén de consumo.

Nunca comparar directamente caja contra pieza.

Nunca asumir que códigos diferentes significan productos diferentes ni que
códigos iguales garantizan la misma presentación.

# 22. NO PARCHEAR A CIEGAS

Antes de modificar código debe existir evidencia exacta:

1. error reproducido;
2. traceback/log;
3. archivo;
4. línea o función;
5. endpoint;
6. servicio;
7. repositorio;
8. tabla/vista;
9. filtros;
10. scope;
11. causa probable demostrable.

No entregar patches basados solamente en una hipótesis razonable.

Si la evidencia no está cerrada:
AUDITAR PRIMERO.

Después del patch:

- test específico;
- regresión;
- compile;
- diff check;
- validación runtime cuando corresponda.

# 23. SCRIPTS ABORTADOS Y ESTADO PARCIAL

## Error operativo corregido

Asumir que un script que termina por `set -e` o una excepción no dejó cambios.

Esa suposición es incorrecta.

Todo paso terminado antes del abort conserva sus efectos:

- archivos;
- staging;
- ramas;
- worktrees;
- claims;
- migraciones;
- SQL confirmado;
- reinicios;
- cambios de proceso.

## Regla

Después de cualquier abort:

1. no repetir automáticamente el script;
2. no hacer reset para acomodar el estado al script;
3. auditar HEAD;
4. auditar index;
5. auditar working tree;
6. auditar claims/worktrees;
7. auditar SQL/procesos si fueron tocados;
8. identificar el último paso realmente completado;
9. continuar desde ese estado real.

Las precondiciones del siguiente script deben reflejar la realidad actual y no
el estado que esperaba el script anterior.

# 24. MONGO — BACKUPS HISTÓRICOS

Durante la auditoría global se encontró un import directo de `pymongo` en:

- `backend/auditorias_p5/backup_p5_07_auth_sql_only_20260606_062908/core/security.py`

Se demostró que pertenece a un backup histórico de auditoría y no al módulo
productivo actual.

Clasificación:

`CODIGO_LEGACY_BACKUP_NO_RUNTIME`

Regla permanente:

- no confundir backup versionado con runtime;
- no eliminarlo solo por contener Mongo;
- no copiar su fallback al código productivo;
- no reabrir auditoría sin nuevo consumidor/import runtime;
- validar linaje exacto antes de declarar una dependencia.
