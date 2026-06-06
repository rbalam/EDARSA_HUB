# MÓDULO TABLAJERÍA - ESPECIFICACIÓN TÉCNICA COMPLETA

## Ubicación en Sistema
```
Operaciones > Producción / Transformación > Tablajería
```

---

## OBJETIVO

Diseñar e implementar de forma controlada el submódulo de TABLAJERÍA dentro de EDARSAHUB, permitiendo:
- Administrar plantillas de tablajería
- Recetas de transformación
- Órdenes de producción
- Rendimientos y mermas
- Costos
- Inventario afectado
- Autorizaciones
- Auditoría
- Sincronización desde servidores externos
- Captura directa en EDARSAHUB SQL

---

## MÁXIMAS OBLIGATORIAS

1. EDARSAHUB SQL Server es el cerebro del sistema
2. Nada crítico debe vivir en MongoDB
3. MongoDB no debe ser fuente de verdad para plantillas, órdenes, recetas, costos, inventarios, autorizaciones, usuarios, roles, permisos, auditoría ni contabilidad
4. Toda estructura nueva debe crearse en EDARSAHUB SQL siguiendo el patrón existente
5. Revisar diccionario actual antes de crear tablas/campos
6. Si existe tabla equivalente, extenderla, no duplicarla
7. Usar zona horaria México para FechaOperacion
8. Timestamps técnicos en UTC, fecha operativa en México
9. No usar `date.today()` sin timezone
10. No romper: Tablero Ejecutivo, Comercial, Compras, Finanzas, filtros, menús, tabs, navegación
11. Si hay riesgo transversal, detenerse y pedir autorización
12. No consultar servidores legacy en vivo para dashboards
13. Servidores legacy = fuentes de sincronización solamente
14. EDARSAHUB SQL = estructura canónica
15. Toda sincronización debe ser idempotente
16. Toda modificación sensible debe quedar auditada

---

## SERVIDORES EXTERNOS DE TABLAJERÍA

| Servidor | Sistema | Base de Datos | Usuario | Puerto | Estado |
|----------|---------|---------------|---------|--------|--------|
| CIENFUEGOS TABLAJERIA | SOFTRESTAURANT_PRO | Tablajeria | CFLectura | 1433 | Offline |
| MPRO TABLAJERIA | MPRO | tablajeria_mpro | <REDACTED_EDARSAHUB_SQL_USER> | 1433 | Offline |
| 130 MÉRIDA (Futuro) | Por definir | Por definir | Por definir | 1433 | Pendiente |
| LA ESTELAR | N/A - Captura directa | EDARSAHUB | N/A | N/A | Captura EDARSAHUB |

**Nota**: MPRO puede contener información de ORIGEN y QUERÉTARO (múltiples sucursales).

---

## MODALIDADES DE OPERACIÓN

### A) Sincronización desde Servidores Externos
- Cienfuegos
- MPRO Origen
- MPRO Querétaro
- Futuro 130 Mérida

### B) Captura Directa en EDARSAHUB
- La Estelar
- Cualquier unidad futura sin sistema externo

**Ambas modalidades alimentan las mismas tablas canónicas.**

---

## MENÚ PROPUESTO

```
Operaciones
 └── Producción / Transformación
      └── Tablajería
           ├── Dashboard
           ├── Plantillas de Tablajería
           ├── Recetas / Fórmulas de Transformación
           ├── Órdenes de Producción
           ├── Ejecución de Tablaje
           ├── Rendimientos y Mermas
           ├── Costeo de Derivados
           ├── Inventario Afectado
           ├── Autorizaciones
           ├── Auditoría
           ├── Sincronización
           └── Configuración
```

---

## FASES DE IMPLEMENTACIÓN

### FASE 0 — DIAGNÓSTICO PASIVO (NO MODIFICAR NADA)
1. Revisar estructura frontend de Operaciones
2. Revisar registro de menús y tabs
3. Revisar RBAC actual
4. Revisar tablas de usuarios, roles, permisos
5. Revisar tablas de inventario, compras, auditoría, workflow, contabilidad
6. Revisar Servidores_Conexiones
7. Buscar tablas de producción, transformación, recetas, inventario, almacenes, costos
8. Revisar catálogo SQL existente
9. Revisar estructura servidores externos (solo SELECT)
10. Generar reporte de hallazgos, riesgos y propuesta

### FASE 1 — DISEÑO SQL CANÓNICO
Tablas propuestas:
- `Operaciones_Tablaje_Plantillas`
- `Operaciones_Tablaje_PlantillasDetalle`
- `Operaciones_Tablaje_PlantillasVersiones`
- `Operaciones_Tablaje_Ordenes`
- `Operaciones_Tablaje_OrdenesDetalle`
- `Operaciones_Tablaje_Rendimientos`
- `Operaciones_Tablaje_Mermas`
- `Operaciones_Tablaje_Costos`
- `Operaciones_Tablaje_SyncLog`
- `Operaciones_Tablaje_SyncErrores`
- `Operaciones_Tablaje_Autorizaciones`
- `Operaciones_Tablaje_Auditoria`
- `Operaciones_Tablaje_Documentos`
- `Operaciones_Tablaje_EventosContables`

### FASE 2 — CATÁLOGO SQL DE SINCRONIZACIÓN
Consultas SELECT-only para servidores externos

### FASE 3 — SINCRONIZACIÓN
Proceso idempotente legacy → EDARSAHUB SQL

### FASE 4 — CAPTURA DIRECTA EDARSAHUB
UI para captura de plantillas sin sistema externo

### FASE 5 — ÓRDENES DE TABLAJE
Flujo operativo completo

### FASE 6 — INVENTARIOS
Integración con inventarios existentes

### FASE 7 — COMPRAS Y AUDITORÍA
Integración lectura con Compras

### FASE 8 — AUTORIZACIONES
Integración con matriz de autorizaciones

### FASE 9 — CONTABILIDAD
Eventos contables (no pólizas definitivas en fase inicial)

### FASE 10 — FRONTEND
UI completa dentro de Operaciones

---

## CAMPOS MÍNIMOS - PLANTILLA

| Campo | Tipo | Descripción |
|-------|------|-------------|
| PlantillaID | UNIQUEIDENTIFIER | PK |
| EmpresaID | UNIQUEIDENTIFIER | FK |
| UnidadNegocioID | UNIQUEIDENTIFIER | FK |
| SucursalID | UNIQUEIDENTIFIER | FK |
| AlmacenOrigenID | INT | FK |
| AlmacenDestinoID | INT | FK |
| CodigoPlantilla | NVARCHAR(50) | Único |
| NombrePlantilla | NVARCHAR(200) | |
| TipoTransformacion | NVARCHAR(50) | |
| InsumoBaseID | INT | FK Producto |
| UnidadBaseID | INT | FK Unidad |
| CantidadBaseEstandar | DECIMAL(18,4) | |
| RendimientoEsperadoPorcentaje | DECIMAL(5,2) | |
| MermaEsperadaPorcentaje | DECIMAL(5,2) | |
| ReglaCosteo | NVARCHAR(50) | |
| OrigenPlantilla | NVARCHAR(50) | Tipo de origen |
| SistemaOrigen | NVARCHAR(50) | |
| ServidorOrigenID | INT | FK |
| BaseDatosOrigen | NVARCHAR(100) | |
| IDLegacyPlantilla | NVARCHAR(100) | ID en sistema origen |
| HashOrigen | NVARCHAR(64) | SHA256 para detectar cambios |
| VersionActual | INT | |
| Estatus | NVARCHAR(50) | |
| Activo | BIT | |
| FechaAltaUTC | DATETIME2 | |
| FechaModificacionUTC | DATETIME2 | |
| FechaSincronizacionUTC | DATETIME2 | |
| FechaOperacionMexico | DATE | |
| UsuarioAltaID | UNIQUEIDENTIFIER | FK |
| UsuarioModificacionID | UNIQUEIDENTIFIER | FK |

---

## TIPOS DE ORIGEN

| Código | Descripción |
|--------|-------------|
| LEGACY_CIENFUEGOS_TABLAJERIA | Sincronizado desde Cienfuegos |
| LEGACY_MPRO_TABLAJERIA | Sincronizado desde MPRO |
| LEGACY_130_MERIDA_TABLAJERIA | Sincronizado desde 130 Mérida |
| CAPTURA_DIRECTA_EDARSAHUB | Capturado en EDARSAHUB |
| IMPORTACION_EXCEL | Importado desde Excel |
| API_EXTERNA | Recibido por API |

---

## ESTATUS DE PLANTILLA

| Estatus | Descripción |
|---------|-------------|
| BORRADOR | En edición |
| SINCRONIZADA | Recién importada |
| PENDIENTE_VALIDACION | Requiere revisión |
| VALIDADA | Revisada y aprobada |
| PUBLICADA | Lista para uso operativo |
| OBSERVADA | Con observaciones |
| INACTIVA | Desactivada |
| REEMPLAZADA | Sustituida por nueva versión |

---

## PERMISOS RBAC

| Permiso | Descripción |
|---------|-------------|
| TABLAJERIA_VER | Ver módulo |
| TABLAJERIA_CREAR_PLANTILLA | Crear plantillas |
| TABLAJERIA_EDITAR_PLANTILLA | Editar plantillas |
| TABLAJERIA_PUBLICAR_PLANTILLA | Publicar plantillas |
| TABLAJERIA_CREAR_ORDEN | Crear órdenes |
| TABLAJERIA_EJECUTAR_ORDEN | Ejecutar órdenes |
| TABLAJERIA_CERRAR_ORDEN | Cerrar órdenes |
| TABLAJERIA_CANCELAR_ORDEN | Cancelar órdenes |
| TABLAJERIA_AUTORIZAR_MERMA | Autorizar mermas fuera de tolerancia |
| TABLAJERIA_VER_COSTOS | Ver información de costos |
| TABLAJERIA_EDITAR_COSTOS | Modificar costos |
| TABLAJERIA_VER_AUDITORIA | Ver auditoría |
| TABLAJERIA_REPROCESAR_SYNC | Reprocesar sincronización |
| TABLAJERIA_CONFIGURAR_SYNC | Configurar sincronización |
| TABLAJERIA_EXPORTAR | Exportar datos |

---

## EVENTOS CONTABLES

| Evento | Descripción |
|--------|-------------|
| TABLAJE_CONSUMO_INSUMO_BASE | Baja de insumo principal |
| TABLAJE_ALTA_DERIVADOS | Alta de productos derivados |
| TABLAJE_REGISTRO_MERMA | Registro de merma |
| TABLAJE_AJUSTE_COSTO | Ajuste de costo |
| TABLAJE_VARIACION_RENDIMIENTO | Variación vs esperado |
| TABLAJE_CANCELACION | Cancelación de orden |
| TABLAJE_REVERSION | Reversión de operación |

---

## VALIDACIÓN DE NO REGRESIÓN

Antes de entregar cualquier fase:
- [ ] Login funciona
- [ ] Menú Operaciones funciona
- [ ] Inventarios no se rompe
- [ ] Compras no se rompe
- [ ] Finanzas no se rompe
- [ ] Comercial no se toca
- [ ] Tablero Ejecutivo no se toca
- [ ] Servidores existentes visibles
- [ ] Filtros existentes funcionan
- [ ] RBAC funciona
- [ ] No hay secretos expuestos
- [ ] No hay consultas live en dashboards
- [ ] EDARSAHUB SQL es fuente de verdad

---

## CRITERIO DE ÉXITO

El módulo de Tablajería debe permitir que **Cienfuegos, MPRO Origen, MPRO Querétaro, futuro 130 Mérida y La Estelar** operen bajo una misma arquitectura canónica en EDARSAHUB SQL, sin depender de MongoDB, sin romper módulos existentes y dejando preparado el camino para inventario, compras, costos, márgenes, auditoría, autorizaciones y contabilidad.

---

*Especificación Técnica - Módulo Tablajería*
*Última actualización: 2026-05-23*
