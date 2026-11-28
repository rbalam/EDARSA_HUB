# EDARSAHUB BOS — R8B-2
## Diseño técnico de snapshots mensuales de costos de recetas

Estado: PROPUESTA PENDIENTE DE CERTIFICACIÓN.

### Principios
SQL Server EDARSAHUB es la fuente canónica.
No duplicar catálogos, Scheduler, Workers ni servicios.
No modificar Producción sin autorización.

### Identidad
Definir la clave mensual mediante unidad de negocio,
producto canónico y período YYYYMM.

Validar previamente si ServerID debe formar parte
de la identidad para evitar colisiones entre orígenes.

### Persistencia
Reutilizar Comercial_RecetasSnapshot y
Comercial_RecetasSnapshotDetalle.

Requerimientos:
- Cabecera y detalles en una transacción.
- Unicidad mensual por identidad certificada.
- Integridad referencial entre ambas tablas.
- Inmutabilidad de cierres históricos.
- Correcciones versionadas y auditadas.
- Reintentos idempotentes.

### Cálculos
Variación mensual:
(CostoActual / CostoMesAnterior - 1) * 100.

Variación acumulada:
(CostoActual / CostoBaseFija - 1) * 100.

Ejemplo:
100 -> 110 -> 121 = 21% acumulado.

Denominador cero o desconocido:
resultado NO_DEFINIDO.

### Datos históricos
No reconstruir períodos con precios actuales.
Los períodos sin evidencia histórica se clasifican
NO_RECONSTRUIBLE.

### Operación
Reutilizar Scheduler, locks SQL y bitácoras existentes.
Verificar independencia del despliegue respecto
a la aplicación web.

### Alertas
Umbrales configurables.
Deduplicación por unidad, producto, período,
regla y versión de regla.

### Seguridad
RBAC corporativo y mínimo privilegio.
HRLectura permanece exclusivamente de lectura.

### Condiciones previas a implementación
Certificar identidad, datos históricos, restricciones,
migraciones reversibles, concurrencia, permisos,
Scheduler y pruebas de aceptación.

Este documento no autoriza implementar cambios.
