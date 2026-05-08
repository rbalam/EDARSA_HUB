# DOCUMENTO DE CONSOLIDACIÓN FINAL
## CAB-003: Automatización de Análisis de Inventarios - VALIDACIÓN PARA IMPLEMENTACIÓN

**Versión**: 2.0 CONSOLIDADA  
**Fecha**: Diciembre 2025  
**Estado**: VALIDACIÓN FINAL ANTES DE IMPLEMENTACIÓN  
**Documentos Fuente**: v1.md, ADENDA_A.md, ADENDA_B.md, ADENDA_C.md

---

## PARTE 1: VALIDACIÓN DE LO EXISTENTE

### 1.1 Core Service Reutilizable

```
ESTADO: ✅ CORRECTO - SIN CAMBIOS REQUERIDOS

Definido en: ADENDA_A, sección 1

VALIDACIÓN:
- Extraer lógica de server.py:2363 a /core/inventory_analysis_core.py
- Endpoint existente y automatización usan el mismo core
- Test obligatorio de identicidad definido
- NO se duplica lógica

CONSISTENCIA CON OTROS DOCUMENTOS:
- v1.md menciona "REUTILIZAR LÓGICA INTERNA" (línea 208)
- ADENDA_A define la arquitectura exacta (líneas 35-73)
- No hay conflicto entre documentos

RIESGO: NINGUNO
```

### 1.2 Clave Única del Proceso

```
ESTADO: ✅ CORRECTO - CONSISTENTE

Definición FINAL (de ADENDA_B):
┌─────────────────────────────────────────────────────────────────────────┐
│  (sistema_origen, server_id, sucursal_id, almacen_id,                   │
│   folio_inventario, fecha_inventario)                                   │
│                                                                         │
│  + hash SHA256 de verificación                                          │
└─────────────────────────────────────────────────────────────────────────┘

VALIDACIÓN DE CONSISTENCIA:
- v1.md (línea 808): Sin sistema_origen (5 componentes) ← OBSOLETO
- ADENDA_A (línea 257): Sin sistema_origen (5 componentes) ← OBSOLETO
- ADENDA_B (línea 26): CON sistema_origen (6 componentes) ← VIGENTE ✅
- ADENDA_C (línea 40): Referencia clave de 6 componentes ← CONSISTENTE ✅

CONFLICTO DETECTADO: v1.md y ADENDA_A mencionan clave de 5 componentes.
RESOLUCIÓN: ADENDA_B corrige esto agregando sistema_origen.
VERSIÓN VIGENTE: 6 componentes (ADENDA_B es la más reciente).

RIESGO: BAJO - Solo requiere usar la definición de ADENDA_B consistentemente.
```

### 1.3 Control de Concurrencia

```
ESTADO: ✅ CORRECTO - MEJORADO EN ADENDA_B

EVOLUCIÓN:
- v1.md: No definido explícitamente
- ADENDA_A (línea 707): Timeout fijo de 5 min ← OBSOLETO
- ADENDA_B (línea 207): Heartbeat cada 30s + timeout 120s ← VIGENTE ✅

VALIDACIÓN:
- LockManager con heartbeat definido completamente en ADENDA_B
- Parámetros configurables (heartbeat_interval, heartbeat_timeout, max_process_time)
- Diagrama de secuencia incluido
- Manejo de proceso muerto vs proceso vivo

CONSISTENCIA CON ADENDA_C:
- ADENDA_C (línea 40) referencia "LockManager y heartbeat" como componente
  que NO se modifica ← CONSISTENTE ✅

RIESGO: NINGUNO - El heartbeat es una mejora que no afecta otros componentes.
```

### 1.4 Flujo de Automatización Extremo a Extremo

```
ESTADO: ✅ CORRECTO - EXTENDIDO EN ADENDA_C

FLUJO BASE (v1.md + ADENDA_A + ADENDA_B):
1. Scheduler detecta nuevos folios
2. Adquiere lock con heartbeat
3. Resuelve inventario inicial
4. Genera análisis (core service)
5. Exporta Excel
6. Resuelve destinatarios
7. Envía email
8. Registra en bitácora
9. Libera lock

EXTENSIÓN (ADENDA_C):
10. Persiste diferencias ← NUEVO
11. Crea tarea pendiente ← NUEVO
12. [FIN flujo síncrono]
13-19. Flujo asíncrono de justificación ← NUEVO

VALIDACIÓN:
- Los pasos 1-9 NO se modifican (ADENDA_C línea 31)
- Los pasos 10-11 se agregan AL FINAL
- El paso 10-11 está aislado (try/catch) para no afectar flujo base

CONSISTENCIA:
- ADENDA_C (línea 67-78): Diagrama muestra extensión, no modificación ✅
- ADENDA_C (línea 1293-1328): Código de aislamiento definido ✅

RIESGO: BAJO - Extensión aislada al final del flujo.
```

### 1.5 Modelo de Destinatarios

```
ESTADO: ✅ CORRECTO - NO HAY CONFLICTO CON TAREAS

Definido en: v1.md (líneas 677-795) y ADENDA_A (líneas 455-684)

VALIDACIÓN:
- Acumulación jerárquica con deduplicación
- Nivel más específico gana en caso de duplicado
- Resuelve destinatarios para EMAIL y WhatsApp

RELACIÓN CON TAREAS (ADENDA_C):
- Destinatarios: Para ENVÍO de análisis (email)
- Tareas: Para SEGUIMIENTO de diferencias (asignado a responsable almacén)
- Son conceptos INDEPENDIENTES que no se solapan

Destinatario ≠ Responsable de tarea
- Destinatario = quien recibe el email del análisis
- Responsable = quien justifica las diferencias (encargado del almacén)

RIESGO: NINGUNO - Son flujos independientes.
```

### 1.6 Desacoplamiento del Frontend

```
ESTADO: ✅ CORRECTO - MANTENIDO

Declarado en: ADENDA_A (líneas 944-1099), ADENDA_C (línea 1282)

VALIDACIÓN:
- ADENDA_A declara: "100% backend, cero cambios en frontend"
- ADENDA_C confirma: "Fase 1.5 = backend only"
- Fase 2 = UI (posterior, separada)

ARCHIVOS PROTEGIDOS:
- /app/frontend/src/pages/Reportes.js → NO MODIFICAR
- /app/frontend/src/pages/Finanzas.js → NO MODIFICAR
- Cualquier archivo en /app/frontend/ → NO MODIFICAR

RIESGO: NINGUNO si se respeta esta regla.
```

### 1.7 RBAC

```
ESTADO: ⚠️ REQUIERE INTEGRACIÓN CUIDADOSA

RBAC EXISTENTE (v1.md, líneas 1252-1283):
- automatizacion.view
- automatizacion.config
- automatizacion.reprocesar
- automatizacion.admin

RBAC NUEVO (ADENDA_C, líneas 886-936):
- justificaciones.view
- justificaciones.edit
- justificaciones.review
- justificaciones.admin
- actividades.view
- actividades.edit
- actividades.close
- actividades.admin

VALIDACIÓN:
- No hay solapamiento de nombres
- Usan prefijos distintos (automatizacion.*, justificaciones.*, actividades.*)
- Ambos reutilizan funciones de core/security.py

AJUSTE MENOR REQUERIDO:
- Documentar claramente que hay 3 módulos de permisos:
  1. automatizacion.* (para config y bitácora)
  2. justificaciones.* (para tareas y justificaciones)
  3. actividades.* (para actividades correctivas)

RIESGO: BAJO - Solo consolidar nomenclatura.
```

### 1.8 Resumen de Validación Parte 1

```
┌─────────────────────────────────────┬──────────────────┬─────────────────────┐
│ Componente                          │ Estado           │ Acción              │
├─────────────────────────────────────┼──────────────────┼─────────────────────┤
│ Core Service                        │ ✅ Correcto      │ Sin cambios         │
│ Clave Única                         │ ✅ Correcto      │ Usar 6 componentes  │
│ Concurrencia (heartbeat)            │ ✅ Correcto      │ Sin cambios         │
│ Flujo de automatización             │ ✅ Correcto      │ Solo extender       │
│ Modelo de destinatarios             │ ✅ Correcto      │ Sin conflicto       │
│ Desacoplamiento frontend            │ ✅ Correcto      │ Mantener            │
│ RBAC                                │ ⚠️ Ajuste menor  │ Consolidar permisos │
└─────────────────────────────────────┴──────────────────┴─────────────────────┘
```

---

## PARTE 2: INTEGRACIÓN DE TAREAS

### 2.1 Confirmación: Cada Análisis Genera una Tarea

```
REGLA CONFIRMADA:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   1 ANÁLISIS PROCESADO = 1 TAREA PENDIENTE CREADA                          │
│                                                                             │
│   Además del envío por correo, SIEMPRE se genera una tarea.                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Secuencia:
1. Análisis generado exitosamente
2. Excel exportado
3. Email enviado a destinatarios
4. Diferencias persistidas en BD
5. Tarea creada para seguimiento

Excepción: Si el análisis falla, NO se crea tarea.
```

### 2.2 Vinculación con Clave Única

```
RELACIÓN TAREA ↔ ANÁLISIS:

La tarea está ligada a la clave única a través de:

┌────────────────────────────────────────────────────────────────────────────┐
│ folios_procesados (análisis)                                               │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ procesado_id (PK, UNIQUEIDENTIFIER)                                    │ │
│ │ sistema_origen                                                         │ │
│ │ server_id                                                              │ │
│ │ sucursal_id                                                            │ │
│ │ almacen_id                                                             │ │
│ │ folio_inventario                                                       │ │
│ │ fecha_inventario                                                       │ │
│ │ hash_verificacion (UNIQUE)                                             │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│                           │ 1:1 (FK UNIQUE)                                │
│                           ▼                                                │
│ tareas_analisis_inventario (tarea)                                         │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ tarea_id (PK, UNIQUEIDENTIFIER)                                        │ │
│ │ analisis_id (FK → procesado_id, UNIQUE)  ← GARANTIZA 1:1               │ │
│ │ sistema_origen (denormalizado para queries)                            │ │
│ │ server_id (denormalizado)                                              │ │
│ │ sucursal_id (denormalizado)                                            │ │
│ │ almacen_id (denormalizado)                                             │ │
│ │ folio_inventario (denormalizado)                                       │ │
│ │ fecha_inventario (denormalizado)                                       │ │
│ │ ...                                                                    │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘

GARANTÍA ANTI-DUPLICADOS:
- analisis_id es FK UNIQUE → Solo puede existir 1 tarea por análisis
- El análisis ya tiene protección hash → No se duplica el análisis
- Por transitividad → No se duplica la tarea
```

### 2.3 Asignación de Responsable

```
REGLA DE ASIGNACIÓN:

El responsable de la tarea es el ENCARGADO DEL ALMACÉN.

Lógica de resolución (a implementar):
1. Buscar en configuración de automatización:
   - automatizacion_inventarios_config.responsable_default por almacén
   
2. Si no existe, buscar en configuración de usuarios:
   - Usuarios con rol "Encargado Almacén" y allowed_almacenes que incluya este almacén
   
3. Si no existe, asignar:
   - responsable_almacen_id = NULL
   - Esto generará alerta al admin para configurar

CAMPOS EN TAREA:
- responsable_almacen_id: Email del encargado
- responsable_almacen_nombre: Nombre para mostrar
```

### 2.4 Integración con Usuarios, Roles y Permisos

```
VALIDACIÓN DE ACCESO A TAREA:

La tarea hereda el modelo de seguridad existente:

1. Verificar acceso al servidor:
   user_has_server_access(usuario, tarea.server_id)
   
2. Verificar acceso a sucursal:
   tarea.sucursal_id in usuario.allowed_sucursales[tarea.server_id]
   
3. Verificar acceso a almacén (si aplica restricción):
   tarea.almacen_id in usuario.allowed_almacenes[tarea.server_id]

REUTILIZACIÓN:
- Mismas funciones de core/security.py
- Misma estructura de permisos en usuario (allowed_servers, allowed_sucursales)
```

### 2.5 Estructura de Tareas: ¿Existe o es Nueva?

```
ANÁLISIS DE ESTRUCTURA EXISTENTE:

Revisé el codebase actual. NO existe un sistema de tareas genérico.
El módulo de automatización de inventarios será el primero en usar tareas.

DECISIÓN: CREAR ESTRUCTURA NUEVA EN EDARSA HUB

Justificación:
1. No hay estructura reutilizable existente
2. Las tablas serán específicas para análisis de inventarios
3. Diseño permite futuras extensiones sin afectar lo existente

TABLAS NUEVAS (todas en EDARSA HUB SQL Server):
- tareas_analisis_inventario (definida en ADENDA_C, 3.2)
- analisis_diferencias (definida en ADENDA_C, 3.3)
- catalogo_tipos_justificacion (definida en ADENDA_C, 3.1)
- configuracion_umbrales_diferencias (definida en ADENDA_C, 3.7)
```

---

## PARTE 3: INTEGRACIÓN DEL FLUJO DE JUSTIFICACIÓN

### 3.1 Capacidades del Encargado

```
EL ENCARGADO DEL ALMACÉN PUEDE:

1. Ver sus tareas pendientes
   GET /api/justificaciones/tareas?responsable={email}

2. Ver detalle de diferencias de una tarea
   GET /api/justificaciones/tareas/{tarea_id}/diferencias

3. Justificar cada diferencia relevante
   POST /api/justificaciones/diferencias/{diferencia_id}/justificar
   Body: {
     tipo_justificacion: "MOP",  // Catálogo cerrado
     comentario: "Merma por cocción normal"  // Opcional excepto si tipo=OTRO
   }

4. Modificar justificación (solo antes de enviar a revisión)
   PUT /api/justificaciones/{justificacion_id}

5. Enviar tarea a revisión
   POST /api/justificaciones/tareas/{tarea_id}/enviar-revision
   
6. Marcar como "sin diferencias relevantes" (caso especial)
   POST /api/justificaciones/tareas/{tarea_id}/sin-diferencias

RESTRICCIONES:
- Solo puede justificar diferencias de SU almacén
- Solo si la tarea está en estado PENDIENTE o EN_PROCESO
- No puede aprobar ni rechazar (eso es del auditor)
```

### 3.2 Justificación con Catálogo Cerrado

```
CATÁLOGO DE TIPOS DE JUSTIFICACIÓN (9 tipos):

┌──────┬────────────────────────┬─────────────────────────────────────────────┐
│ Cód  │ Tipo                   │ Requiere Comentario Obligatorio             │
├──────┼────────────────────────┼─────────────────────────────────────────────┤
│ MOP  │ MERMA_OPERATIVA        │ NO                                          │
│ ECP  │ ERROR_CAPTURA          │ NO                                          │
│ DRC  │ DIFERENCIA_RECETA      │ NO                                          │
│ ANR  │ AJUSTE_NO_REGISTRADO   │ NO                                          │
│ RPD  │ ROBO_PERDIDA           │ NO                                          │
│ TNA  │ TRASPASO_NO_APLICADO   │ NO                                          │
│ CAD  │ CADUCIDAD              │ NO                                          │
│ DAÑ  │ DAÑO_FISICO            │ NO                                          │
│ OTR  │ OTRO                   │ SÍ - OBLIGATORIO                            │
└──────┴────────────────────────┴─────────────────────────────────────────────┘

VALIDACIÓN EN BACKEND:
if tipo_justificacion == 'OTR' and (not comentario or len(comentario) < 10):
    raise ValidationError("Tipo OTRO requiere comentario de al menos 10 caracteres")
```

### 3.3 Evolución de Estados de la Tarea

```
TRANSICIONES DE ESTADO FORMALES:

PENDIENTE
    │
    │ Encargado abre tarea o registra primera justificación
    ▼
EN_PROCESO
    │
    ├─────────────────────────────────────────┐
    │ Todas diferencias relevantes            │ Encargado marca
    │ justificadas + envía a revisión         │ "sin diferencias"
    ▼                                         ▼
JUSTIFICADO                            SIN_DIFERENCIAS ─────┐
    │                                        │              │
    │ Auditor abre para revisar              │ (Cerrado)    │
    ▼                                        │              │
EN_REVISION_AUDITOR                          │              │
    │                                        │              │
    ├───────────────────────┐                │              │
    │ Todas aprobadas       │ Al menos       │              │
    │                       │ 1 rechazada    │              │
    ▼                       ▼                │              │
VALIDADO               OBSERVADO             │              │
    │                       │                │              │
    │ (Cerrado OK)          │ Actividades    │              │
    │                       │ correctivas    │              │
    │                       │ creadas        │              │
    │                       ▼                │              │
    │              [Actividades se resuelven]│              │
    │                       │                │              │
    │                       │ Todas cerradas │              │
    │                       ▼                │              │
    │                   CERRADO ◄────────────┘              │
    │                       │                               │
    └───────────────────────┼───────────────────────────────┘
                            │
                            ▼
                    [FIN DEL PROCESO]
```

### 3.4 Capacidades del Auditor

```
EL AUDITOR PUEDE:

1. Ver tareas pendientes de revisión (en su alcance)
   GET /api/justificaciones/revision/pendientes

2. Ver detalle de tarea con todas las diferencias y justificaciones
   GET /api/justificaciones/tareas/{tarea_id}

3. Aprobar o rechazar cada justificación individualmente
   POST /api/justificaciones/revision/{justificacion_id}
   Body: {
     decision: "APROBADA" | "RECHAZADA",
     comentario_auditor: "Justificación insuficiente, requiere evidencia"
   }

4. Aprobar o rechazar todas en bloque
   POST /api/justificaciones/revision/tareas/{tarea_id}/bloque
   Body: {
     decision: "APROBADA",  // Aplica a todas
     comentario_general: "Revisión OK"
   }

5. Ver actividades correctivas generadas
   GET /api/actividades?tarea_id={tarea_id}

6. Cerrar actividades correctivas resueltas
   POST /api/actividades/{actividad_id}/cerrar
   Body: {
     comentario_cierre: "Resolución validada"
   }

RESTRICCIONES:
- Solo puede revisar tareas en estado JUSTIFICADO o EN_REVISION_AUDITOR
- Solo tareas dentro de su alcance (servidor/sucursal)
- No puede modificar justificaciones (solo aprobar/rechazar)
```

---

## PARTE 4: ACCIONES DERIVADAS (ACTIVIDADES CORRECTIVAS)

### 4.1 Generación Automática de Actividades

```
REGLA: Si auditor RECHAZA una justificación, se genera automáticamente
       una ACTIVIDAD CORRECTIVA.

TRIGGER:
- Auditor ejecuta: POST /api/justificaciones/revision/{id}
- Con decision = "RECHAZADA"

ACCIÓN AUTOMÁTICA:
crear_actividad_correctiva(
    revision_id = {id de la revisión recién creada},
    analisis_id = {id del análisis},
    diferencia_id = {id de la diferencia},
    tarea_id = {id de la tarea},
    motivo_rechazo = {comentario del auditor},
    responsable_asignado = {encargado del almacén de la tarea},
    prioridad = calcular_prioridad(valor_diferencia),
    fecha_limite = calcular_fecha_limite(dias_config)
)
```

### 4.2 Estructura de Actividad Correctiva

```
CAMPOS DE LA ACTIVIDAD:

Identificación:
- actividad_id (PK)
- revision_id (FK) → Quién la generó
- analisis_id (FK) → Análisis origen
- diferencia_id (FK) → Diferencia específica
- tarea_id (FK) → Tarea padre

Contexto del problema:
- codigo_insumo
- nombre_insumo
- cantidad_diferencia
- valor_diferencia
- motivo_rechazo (del auditor)

Asignación:
- responsable_asignado_id (email)
- responsable_asignado_nombre
- prioridad (ALTA/MEDIA/BAJA)
- fecha_limite

Estado y resolución:
- estado (ABIERTA → EN_PROCESO → RESUELTA → CERRADA)
- descripcion_resolucion (qué hizo el responsable)
- fecha_aceptacion
- fecha_resolucion
- auditor_cierre_id (quién cerró)
- fecha_cierre
- comentario_cierre
```

### 4.3 Flujo de Actividad Correctiva

```
ABIERTA
    │
    │ Responsable acepta trabajar en ella
    │ POST /api/actividades/{id}/aceptar
    ▼
EN_PROCESO
    │
    │ Responsable documenta lo que hizo
    │ POST /api/actividades/{id}/resolver
    │ Body: { descripcion_resolucion: "Se investigó y..." }
    ▼
RESUELTA
    │
    │ Auditor valida la resolución
    │ POST /api/actividades/{id}/cerrar
    │ Body: { comentario_cierre: "Resolución aceptada" }
    ▼
CERRADA

NOTA: Si todas las actividades de una tarea se cierran,
      la tarea cambia de OBSERVADO → CERRADO automáticamente.
```

### 4.4 Integración con Ecosistema Existente

```
LAS ACTIVIDADES CORRECTIVAS:

1. Usan el mismo modelo de usuarios
   - responsable_asignado_id = user.email
   
2. Usan el mismo modelo de permisos
   - actividades.view → Ver mis actividades
   - actividades.edit → Actualizar estado
   - actividades.close → Cerrar (solo auditor)
   
3. Usan el mismo alcance RBAC
   - Un usuario solo ve actividades de su servidor/sucursal/almacén
   
4. Se almacenan en EDARSA HUB
   - Misma BD que el resto de automatización

NO SE CREA SISTEMA PARALELO.
```

---

## PARTE 5: FLUJO FINAL CONSOLIDADO

### 5.1 Flujo Completo de Extremo a Extremo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO CONSOLIDADO                               │
│                    Detección → Cierre (10 pasos)                            │
└─────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║ FASE 1: AUTOMATIZACIÓN (SÍNCRONO, CADA 15 MIN)                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│ 1. DETECCIÓN DE INVENTARIO                                                │
├───────────────────────────────────────────────────────────────────────────┤
│ • Scheduler se activa cada 15 minutos                                     │
│ • Query a SOFT/MPRO buscando nuevos folios                                │
│ • Compara con ultimo_folio_conocido por almacén                           │
│ • Si encuentra nuevo → continúa, si no → espera siguiente ciclo           │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 2. CONTROL DE DUPLICADOS Y CONCURRENCIA                                   │
├───────────────────────────────────────────────────────────────────────────┤
│ • Calcular hash: SHA256(sistema_origen|server|suc|alm|folio|fecha)        │
│ • Intentar INSERT atómico en folios_procesados                            │
│ • Si ya existe → saltar (ya procesado)                                    │
│ • Si INSERT OK → lock adquirido, iniciar heartbeat                        │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 3. RESOLUCIÓN DE INVENTARIO INICIAL                                       │
├───────────────────────────────────────────────────────────────────────────┤
│ • SOFT: Primer inventario del MES ACTUAL                                  │
│ • MPRO: Último inventario del MES ANTERIOR                                │
│ • Si no existe inv inicial → error, notificar admin, saltar               │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 4. GENERACIÓN DE ANÁLISIS                                                 │
├───────────────────────────────────────────────────────────────────────────┤
│ • Invocar InventoryAnalysisCore.generar_analisis()                        │
│ • IDÉNTICO al endpoint /reports/inventory-analysis                        │
│ • Resultado: lista de productos con diferencias                           │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 5. EXPORTACIÓN DE ARCHIVOS                                                │
├───────────────────────────────────────────────────────────────────────────┤
│ • Generar Excel (IDÉNTICO al menú manual)                                 │
│ • Generar PDF (opcional, según config)                                    │
│ • Guardar en /app/storage/automatizacion/YYYY/MM/                         │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 6. RESOLUCIÓN DE DESTINATARIOS Y ENVÍO                                    │
├───────────────────────────────────────────────────────────────────────────┤
│ • Resolver destinatarios: servidor → sucursal → almacén                   │
│ • Acumular con deduplicación (nivel más específico gana)                  │
│ • Enviar email con Excel adjunto a cada destinatario                      │
│ • Registrar cada envío en tabla de envíos                                 │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 7. PERSISTENCIA DE DIFERENCIAS Y CREACIÓN DE TAREA                        │
├───────────────────────────────────────────────────────────────────────────┤
│ • Persistir cada diferencia en analisis_diferencias                       │
│ • Marcar diferencias relevantes según umbrales                            │
│ • Crear tarea en tareas_analisis_inventario                               │
│ • Asignar responsable (encargado del almacén)                             │
│ • Estado inicial: PENDIENTE o SIN_DIFERENCIAS                             │
│ [Este paso está aislado: si falla, el análisis ya se envió]               │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 8. LIBERACIÓN DE LOCK Y FIN DE FASE 1                                     │
├───────────────────────────────────────────────────────────────────────────┤
│ • Detener heartbeat                                                       │
│ • Actualizar estado en folios_procesados → EXITOSO                        │
│ • Registrar en bitácora                                                   │
│ [FIN DEL FLUJO SÍNCRONO]                                                  │
└───────────────────────────────────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║ FASE 1.5: JUSTIFICACIÓN Y AUDITORÍA (ASÍNCRONO, BAJO DEMANDA)             ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│ 9. JUSTIFICACIÓN POR ENCARGADO                                            │
├───────────────────────────────────────────────────────────────────────────┤
│ • Encargado ve su tarea PENDIENTE                                         │
│ • Abre la tarea → estado cambia a EN_PROCESO                              │
│ • Por cada diferencia relevante:                                          │
│   - Selecciona tipo de justificación (catálogo cerrado)                   │
│   - Agrega comentario (obligatorio si tipo=OTRO)                          │
│ • Al completar todas → envía a revisión                                   │
│ • Estado: JUSTIFICADO                                                     │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 10. REVISIÓN Y APROBACIÓN POR AUDITOR                                     │
├───────────────────────────────────────────────────────────────────────────┤
│ • Auditor ve tarea en estado JUSTIFICADO                                  │
│ • Estado cambia a EN_REVISION_AUDITOR                                     │
│ • Por cada justificación:                                                 │
│   - APRUEBA: justificación aceptada                                       │
│   - RECHAZA: genera ACTIVIDAD CORRECTIVA automáticamente                  │
│ • Si todas aprobadas → estado: VALIDADO (cerrado OK)                      │
│ • Si alguna rechazada → estado: OBSERVADO                                 │
└────────────────────────────────────────┬──────────────────────────────────┘
                                         │
                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 11. ACTIVIDADES CORRECTIVAS (SI APLICA)                                   │
├───────────────────────────────────────────────────────────────────────────┤
│ • Por cada justificación rechazada:                                       │
│   - Se crea actividad correctiva automáticamente                          │
│   - Asignada al encargado del almacén                                     │
│   - Estado: ABIERTA                                                       │
│ • Encargado resuelve cada actividad:                                      │
│   - Documenta acciones tomadas                                            │
│   - Estado: RESUELTA                                                      │
│ • Auditor cierra actividades:                                             │
│   - Valida resolución                                                     │
│   - Estado: CERRADA                                                       │
│ • Cuando todas las actividades están CERRADAS:                            │
│   - Tarea cambia de OBSERVADO → CERRADO                                   │
└───────────────────────────────────────────────────────────────────────────┘

                                    [FIN]
```

---

## PARTE 6: IMPACTO Y RIESGO

### 6.1 Impacto en Arquitectura

```
IMPACTO: BAJO

Componentes existentes que NO se modifican:
- /app/backend/server.py (solo se importa el core service)
- /app/backend/core/* (se reutiliza sin cambios)
- /app/backend/modules/finanzas/*
- /app/backend/modules/compras/*
- /app/frontend/* (NINGÚN cambio)

Componentes nuevos que se AGREGAN:
- /app/backend/core/inventory_analysis_core.py (extrae lógica)
- /app/backend/modules/automatizacion/* (módulo nuevo)
- /app/backend/modules/justificaciones/* (módulo nuevo)

Principio: EXTENSIÓN, no modificación.
```

### 6.2 Impacto en Tablas

```
TABLAS NUEVAS EN EDARSA HUB (14 tablas):

Fase 1 (Automatización):
1. automatizacion_inventarios_config
2. automatizacion_inventarios_destinatarios
3. automatizacion_inventarios_folios_procesados
4. automatizacion_inventarios_ejecuciones
5. automatizacion_inventarios_envios
6. automatizacion_inventarios_ultimo_folio_conocido

Fase 1.5 (Justificación):
7. catalogo_tipos_justificacion
8. tareas_analisis_inventario
9. analisis_diferencias
10. justificaciones_inventario
11. revisiones_auditor
12. actividades_correctivas
13. configuracion_umbrales_diferencias

TABLAS EXISTENTES QUE NO SE MODIFICAN:
- Todas las tablas en SOFT/MPRO
- Todas las tablas existentes en EDARSA HUB
- Colecciones en MongoDB (solo cache temporal nuevo)
```

### 6.3 Impacto en RBAC

```
PERMISOS NUEVOS (12 permisos):

Módulo automatizacion:
- automatizacion.view
- automatizacion.config
- automatizacion.reprocesar
- automatizacion.admin

Módulo justificaciones:
- justificaciones.view
- justificaciones.edit
- justificaciones.review
- justificaciones.admin

Módulo actividades:
- actividades.view
- actividades.edit
- actividades.close
- actividades.admin

PERMISOS EXISTENTES: Sin cambios.
```

### 6.4 Impacto en Procesos Existentes

```
PROCESOS QUE NO SE AFECTAN:

1. Generación manual de análisis de inventarios
   - El usuario sigue usando el menú de Reportes > Análisis
   - Misma lógica, mismo resultado
   
2. Módulo de Finanzas / CxP
   - Completamente independiente
   
3. Módulo de Tesorería / Cuadre Z
   - Completamente independiente
   
4. Autenticación y roles
   - Solo se agregan nuevos permisos
   - Los existentes no cambian

IMPACTO: NULO en procesos existentes.
```

### 6.5 Riesgos de Regresión y Mitigación

```
┌────────┬─────────────────────────────────────────┬──────────┬──────────────────────────────┐
│ ID     │ Riesgo                                  │ Prob.    │ Mitigación                   │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-01  │ Extracción del core rompe endpoint      │ BAJA     │ Test de identicidad          │
│        │ existente                               │          │ obligatorio                  │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-02  │ Heartbeat consume recursos excesivos    │ BAJA     │ Intervalo configurable,      │
│        │                                         │          │ monitoreo de BD              │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-03  │ Creación de tarea falla y rompe flujo   │ MEDIA    │ Try/catch aislado, el        │
│        │                                         │          │ análisis ya se envió         │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-04  │ Nuevos permisos conflictúan con RBAC    │ BAJA     │ Prefijos distintos,          │
│        │                                         │          │ tests de autorización        │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-05  │ Performance del ciclo se degrada        │ MEDIA    │ Persistir diferencias en     │
│        │                                         │          │ batch, no uno por uno        │
├────────┼─────────────────────────────────────────┼──────────┼──────────────────────────────┤
│ RR-06  │ Timeout en queries a SQL Server origen  │ ALTA     │ Timeouts configurables,      │
│        │                                         │          │ reintentos, logs             │
└────────┴─────────────────────────────────────────┴──────────┴──────────────────────────────┘
```

---

## PARTE 7: AJUSTE DE FASES

### 7.1 Plan de Fases Consolidado

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                       PLAN DE FASES DEFINITIVO                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

FASE 0: PREPARACIÓN (1-2 días)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Crear tablas de Fase 1 en EDARSA HUB (6 tablas)
□ Crear estructura /modules/automatizacion/
□ Configurar APScheduler básico
□ Tests de conexión

FASE 1: AUTOMATIZACIÓN BASE (5-6 semanas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fase 1A: Core Service (1 semana)
- Extraer lógica a inventory_analysis_core.py
- Modificar endpoint para usar core
- Test de identicidad

Fase 1B: Detección y Procesamiento (1-2 semanas)
- Implementar detector de folios
- Implementar LockManager con heartbeat
- Implementar resolución de inv inicial
- Control de duplicados

Fase 1C: Exportación y Email (1-2 semanas)
- Implementar generación de análisis (usa core)
- Implementar exportación Excel
- Implementar resolución de destinatarios
- Implementar envío de email
- Registrar en bitácora

Fase 1D: Integración y Piloto (1 semana)
- Integrar scheduler completo
- Endpoints de administración
- Feature flag por servidor
- Piloto en 1 servidor

Fase 1E: Rollout Fase 1 (1 semana)
- Activar gradualmente
- Monitoreo
- Ajustes

[VALIDACIÓN: Fase 1 funciona completa antes de continuar]


FASE 1.5: JUSTIFICACIÓN Y AUDITORÍA - BACKEND (3-4 semanas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fase 1.5A: Persistencia y Tareas (1 semana)
- Crear tablas de Fase 1.5 (7 tablas)
- Cargar catálogo de tipos
- Configurar umbrales por defecto
- Extender service.py para crear tarea
- Test: Fase 1 sigue funcionando

Fase 1.5B: Justificación (1 semana)
- Endpoints de tareas
- Endpoints de justificación
- Validaciones de estado
- Tests de API

Fase 1.5C: Revisión y Actividades (1 semana)
- Endpoints de revisión
- Generación automática de actividades
- Endpoints de actividades
- Transiciones de estado

Fase 1.5D: RBAC y Validación (3-5 días)
- Integrar nuevos permisos
- Validación de acceso en todos los endpoints
- Tests de autorización
- Piloto con usuario real

[VALIDACIÓN: Fase 1.5 funciona completa]


FASE 2: UI Y WHATSAPP (4-5 semanas, POSTERIOR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fase 2A: UI de Tareas (2 semanas)
- Pantalla de mis tareas
- Detalle de tarea
- Formulario de justificación

Fase 2B: UI de Revisión (1 semana)
- Pantalla de tareas para auditor
- Formulario de aprobación/rechazo
- Dashboard de actividades

Fase 2C: WhatsApp (1-2 semanas)
- Integración con proveedor
- Envío de notificaciones
- Configuración de destinatarios WA
```

### 7.2 Cronograma Visual

```
Semana    1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16+
          │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
FASE 0    █───┘
FASE 1    └───█───█───█───█───█───█───┘
                                       │
                                       ▼ [Validación]
FASE 1.5                               └───█───█───█───█───┘
                                                           │
                                                           ▼ [Validación]
FASE 2                                                     └───█───█───█───█───█
```

---

## RESPUESTA FINAL

### ¿Es Seguro Iniciar Fase 0 Sin Riesgo de Regresión?

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ✅ SÍ, ES SEGURO INICIAR FASE 0                                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

JUSTIFICACIÓN:

1. FASE 0 SOLO CREA INFRAESTRUCTURA
   - Tablas nuevas en EDARSA HUB (no afecta existentes)
   - Directorio nuevo /modules/automatizacion/
   - Scheduler básico (no ejecuta nada real)

2. NO MODIFICA CÓDIGO EXISTENTE
   - No toca server.py (aún)
   - No toca frontend
   - No toca sistemas origen

3. TODO ES NUEVO Y DESACOPLADO
   - Si falla, se puede eliminar sin impacto
   - Feature flag permite desactivar

4. VALIDACIONES DEFINIDAS
   - Cada fase tiene validación antes de continuar
   - Tests de identicidad para el core service

CONDICIONES PARA MANTENER SEGURIDAD:

□ Seguir el principio de EXTENSIÓN, no modificación
□ Usar feature flags para activar/desactivar
□ Ejecutar tests de identicidad antes de modificar endpoint
□ Mantener try/catch aislado en pasos nuevos
□ No modificar NINGÚN archivo en /app/frontend/ hasta Fase 2
□ No crear tablas en SOFT/MPRO
```

---

## CHECKLIST DE IMPLEMENTACIÓN SEGURA

```
ANTES DE CADA FASE:
□ Revisar este documento de consolidación
□ Confirmar que componentes "intocables" no se modifican
□ Tener plan de rollback

DURANTE IMPLEMENTACIÓN:
□ Un cambio a la vez
□ Test después de cada cambio
□ Commits pequeños y atómicos

DESPUÉS DE CADA SUBFASE:
□ Verificar que funcionalidad existente sigue igual
□ Ejecutar tests de regresión
□ Documentar cualquier ajuste
```

---

**FIN DEL DOCUMENTO DE CONSOLIDACIÓN**

*Este documento reemplaza la necesidad de consultar los 4 documentos fuente
por separado. Contiene todo lo necesario para iniciar implementación segura.*

*CAB-003 Consolidación Final - Diciembre 2025*
