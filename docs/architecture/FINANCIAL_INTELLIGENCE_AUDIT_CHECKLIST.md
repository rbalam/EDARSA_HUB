# Checklist de auditoría — Financial Intelligence

Este checklist bloquea la creación de tablas, endpoints, jobs y componentes visibles hasta cerrar evidencia exacta.

## Backend

- [ ] Inventariar módulos y convenciones vigentes bajo `backend/modules`.
- [ ] Identificar el patrón canónico de `APIRouter`, registro en aplicación y versionado.
- [ ] Validar la dependencia de autenticación canónica.
- [ ] Validar `require_permission_explicit` o equivalente SQL explícito.
- [ ] Identificar repositorio SQL y manejo de transacciones.
- [ ] Confirmar bitácora canónica para lectura, escritura, simulación y acciones administrativas.
- [ ] Confirmar gestor canónico de secretos y conectores.

## SQL

- [ ] Inventariar tablas existentes relacionadas con noticias, eventos, alertas, portafolios, educación, IA y auditoría.
- [ ] Confirmar patrón de nombres, PK, FK, timestamps, vigencias y soft delete.
- [ ] Confirmar mecanismo real de migraciones y rollback.
- [ ] Validar alcances por empresa, unidad y propietario.
- [ ] Evitar tablas paralelas de usuarios, roles, permisos, unidades, empresas y conectores.

## Scheduler

- [ ] Identificar registry central de jobs.
- [ ] Confirmar estados, reintentos, lock SQL, timeout, bitácora y ejecución manual autorizada.
- [ ] Confirmar que no se requiere ampliar `backend/core` con lógica de dominio.
- [ ] Definir jobs de ingesta por proveedor, no scripts sueltos.

## Frontend

- [ ] Identificar patrón canónico de menú y rutas.
- [ ] Identificar componente de guardas por permiso.
- [ ] Identificar componentes reutilizables de dashboard, tablas, filtros, alertas y exportación.
- [ ] Definir navegación sin crear entradas sueltas ni duplicadas.
- [ ] Mantener cálculos de negocio en backend.

## Datos y proveedores

- [ ] Clasificar fuentes oficiales, regulatorias, bursátiles, empresariales, climáticas y periodísticas.
- [ ] Registrar licencia, latencia, cobertura, costo y límites de API.
- [ ] Definir política de confirmación cruzada y calidad.
- [ ] Definir retención de captura cruda y datos normalizados.
- [ ] Definir resolución de entidades e instrumentos.

## Privacidad y cumplimiento

- [ ] Dictamen sobre educación, análisis general, recomendaciones personalizadas y ejecución.
- [ ] Separación formal entre datos corporativos y personales.
- [ ] Alcance `OWNER` para portafolios personales.
- [ ] Consentimiento, exportación, eliminación y soporte sin acceso automático.
- [ ] Política de uso aceptable y advertencias de riesgo.

## Pruebas

- [ ] Unitarias de normalización, deduplicación, permisos y riesgo.
- [ ] Integración con SQL y scheduler.
- [ ] Contratos de proveedores.
- [ ] Backtesting sin look-ahead bias ni survivorship bias.
- [ ] Simulación de fuentes caídas y datos contradictorios.
- [ ] Pruebas RBAC negativas.
- [ ] Rollback verificado.

## Gate de implementación

No iniciar implementación ejecutable hasta completar el inventario exacto y documentar las decisiones de reutilización. Cada elemento nuevo debe indicar qué estructura existente reutiliza y por qué no duplica una fuente canónica.
