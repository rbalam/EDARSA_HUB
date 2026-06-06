# ADENDA TÉCNICA C: Flujo de Justificación y Aprobación de Diferencias
## EDARSA HUB - CAB-003 - Adenda C

**Versión**: 1.3  
**Fecha**: Diciembre 2025  
**Estado**: DISEÑO - PENDIENTE APROBACIÓN  
**Referencia**: Extensión del flujo de automatización con justificación y auditoría

---

## ÍNDICE

1. [Impacto en el Diseño Actual](#1-impacto-en-el-diseño-actual)
2. [Modelo Funcional Completo](#2-modelo-funcional-completo)
3. [Propuesta de Tablas](#3-propuesta-de-tablas)
4. [Integración con Tarea Existente](#4-integración-con-tarea-existente)
5. [Integración con RBAC](#5-integración-con-rbac)
6. [Flujo Orquestado Actualizado](#6-flujo-orquestado-actualizado)
7. [Estrategia Anti-Duplicados](#7-estrategia-anti-duplicados)
8. [Riesgos de Regresión](#8-riesgos-de-regresión)
9. [Plan de Fases Actualizado](#9-plan-de-fases-actualizado)
10. [Validación de No Ruptura](#10-validación-de-no-ruptura)

---

## 1. IMPACTO EN EL DISEÑO ACTUAL

### 1.1 Componentes Afectados vs No Afectados

```
COMPONENTES QUE NO SE MODIFICAN (Fase 1 intacta):
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✓ Core Service de Análisis (inventory_analysis_core.py)                    │
│ ✓ Detector de nuevos folios (detector.py)                                  │
│ ✓ Generador de análisis (generator.py)                                     │
│ ✓ Exportador Excel/PDF (exporter.py)                                       │
│ ✓ Notificador Email (notifier.py)                                          │
│ ✓ LockManager y heartbeat (lock_manager.py)                                │
│ ✓ Clave única: (sistema_origen, server_id, sucursal_id, almacen_id,        │
│                 folio, fecha)                                               │
│ ✓ Tablas de control de folios procesados                                   │
│ ✓ Tablas de destinatarios                                                  │
│ ✓ Scheduler y ciclo de automatización                                      │
│ ✓ Frontend existente (Reportes.js, etc.)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

COMPONENTES NUEVOS (Fase 1.5):
┌─────────────────────────────────────────────────────────────────────────────┐
│ + Sistema de Tareas Pendientes                                              │
│ + Módulo de Justificaciones                                                 │
│ + Módulo de Revisión/Auditoría                                              │
│ + Módulo de Actividades Correctivas                                         │
│ + Catálogo de Tipos de Justificación                                        │
│ + Endpoints de gestión (backend only)                                       │
└─────────────────────────────────────────────────────────────────────────────┘

COMPONENTE EXTENDIDO (mínimamente):
┌─────────────────────────────────────────────────────────────────────────────┐
│ ~ service.py (orquestador): Agregar paso de creación de tarea              │
│   SOLO al final del flujo exitoso, después de enviar notificaciones        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Principio de Extensión

```
REGLA: El flujo de Fase 1 se EXTIENDE, no se modifica.

Fase 1 (existente):
  Detectar → Procesar → Generar → Exportar → Notificar → [FIN]

Fase 1 + Fase 1.5:
  Detectar → Procesar → Generar → Exportar → Notificar → CREAR TAREA → [FIN]
                                                              ↓
                                              [Flujo asíncrono de justificación]
                                                              ↓
                                              Justificar → Revisar → Cerrar/Acción
```

### 1.3 Relación entre Entidades

```
                    ┌─────────────────────────────────┐
                    │   ANÁLISIS DE INVENTARIO        │
                    │   (folios_procesados)           │
                    │   - sistema_origen              │
                    │   - server_id                   │
                    │   - folio                       │
                    │   - fecha                       │
                    └─────────────┬───────────────────┘
                                  │ 1:1
                                  ▼
                    ┌─────────────────────────────────┐
                    │   TAREA ANÁLISIS INVENTARIO     │
                    │   (tareas_analisis_inventario)  │
                    │   - tarea_id                    │
                    │   - analisis_id (FK)            │
                    │   - responsable_almacen         │
                    │   - estado                      │
                    └─────────────┬───────────────────┘
                                  │ 1:N
                                  ▼
                    ┌─────────────────────────────────┐
                    │   DIFERENCIAS DEL ANÁLISIS      │
                    │   (analisis_diferencias)        │
                    │   - diferencia_id               │
                    │   - analisis_id (FK)            │
                    │   - codigo_insumo               │
                    │   - cantidad_diferencia         │
                    │   - valor_diferencia            │
                    └─────────────┬───────────────────┘
                                  │ 1:1 (opcional)
                                  ▼
                    ┌─────────────────────────────────┐
                    │   JUSTIFICACIÓN                 │
                    │   (justificaciones_inventario)  │
                    │   - justificacion_id            │
                    │   - diferencia_id (FK)          │
                    │   - tipo_justificacion (FK)     │
                    │   - comentario                  │
                    │   - usuario_justifica           │
                    └─────────────┬───────────────────┘
                                  │ 1:1
                                  ▼
                    ┌─────────────────────────────────┐
                    │   REVISIÓN AUDITOR              │
                    │   (revisiones_auditor)          │
                    │   - revision_id                 │
                    │   - justificacion_id (FK)       │
                    │   - decision (APROBADA/RECHAZADA)│
                    │   - auditor                     │
                    │   - comentario_auditor          │
                    └─────────────┬───────────────────┘
                                  │ 0:1 (si rechazada)
                                  ▼
                    ┌─────────────────────────────────┐
                    │   ACTIVIDAD CORRECTIVA          │
                    │   (actividades_correctivas)     │
                    │   - actividad_id                │
                    │   - revision_id (FK)            │
                    │   - motivo_rechazo              │
                    │   - responsable_asignado        │
                    │   - estado                      │
                    └─────────────────────────────────┘
```

---

## 2. MODELO FUNCIONAL COMPLETO

### 2.1 Máquina de Estados de la Tarea

```
                            ┌─────────────────┐
                            │    PENDIENTE    │
                            │                 │
                            │ Tarea creada,   │
                            │ sin acción      │
                            └────────┬────────┘
                                     │
                                     │ Encargado abre la tarea
                                     ▼
                            ┌─────────────────┐
                            │   EN_PROCESO    │
                            │                 │
                            │ Encargado       │
                            │ justificando    │
                            └────────┬────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    │ Todas las diferencias          │ Marca "sin diferencias
                    │ relevantes justificadas        │ relevantes"
                    │                                 │
                    ▼                                 ▼
           ┌─────────────────┐              ┌─────────────────┐
           │   JUSTIFICADO   │              │ SIN_DIFERENCIAS │
           │                 │              │                 │
           │ Listo para      │              │ Cerrado sin     │
           │ revisión        │              │ justificaciones │
           └────────┬────────┘              └─────────────────┘
                    │
                    │ Auditor inicia revisión
                    ▼
           ┌─────────────────┐
           │ EN_REVISION_    │
           │ AUDITOR         │
           │                 │
           │ Auditor         │
           │ revisando       │
           └────────┬────────┘
                    │
       ┌────────────┴────────────┐
       │                         │
       │ Todas aprobadas         │ Al menos 1 rechazada
       │                         │
       ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│    VALIDADO     │      │    OBSERVADO    │
│                 │      │                 │
│ Cerrado OK      │      │ Genera acciones │
│ sin hallazgos   │      │ correctivas     │
└─────────────────┘      └────────┬────────┘
                                  │
                                  │ Todas las acciones
                                  │ correctivas cerradas
                                  ▼
                         ┌─────────────────┐
                         │    CERRADO      │
                         │                 │
                         │ Proceso         │
                         │ completado      │
                         └─────────────────┘
```

### 2.2 Catálogo de Tipos de Justificación

```
CATÁLOGO CERRADO (no modificable por usuarios normales):

┌──────┬────────────────────────┬──────────────────────────────────────────┐
│ Cód  │ Tipo                   │ Descripción                              │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ MOP  │ MERMA_OPERATIVA        │ Pérdida normal por operación (cocción,   │
│      │                        │ evaporación, limpieza)                   │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ ECP  │ ERROR_CAPTURA          │ Error al registrar inventario físico     │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ DRC  │ DIFERENCIA_RECETA      │ Variación por uso diferente a receta     │
│      │                        │ estándar                                 │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ ANR  │ AJUSTE_NO_REGISTRADO   │ Movimiento de almacén no capturado en    │
│      │                        │ sistema                                  │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ RPD  │ ROBO_PERDIDA           │ Faltante por sustracción o pérdida       │
│      │                        │ identificada                             │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ TNA  │ TRASPASO_NO_APLICADO   │ Traspaso entre almacenes pendiente de    │
│      │                        │ registro                                 │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ CAD  │ CADUCIDAD              │ Producto dado de baja por caducidad      │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ DAÑ  │ DAÑO_FISICO            │ Producto dañado o en mal estado          │
├──────┼────────────────────────┼──────────────────────────────────────────┤
│ OTR  │ OTRO                   │ Otro motivo (comentario OBLIGATORIO)     │
└──────┴────────────────────────┴──────────────────────────────────────────┘

Reglas:
- El catálogo es administrable solo por rol Administrador
- Si tipo = 'OTRO', el campo comentario es OBLIGATORIO
- Cada tipo puede tener configuración de "requiere_evidencia" (futuro)
```

### 2.3 Reglas de Diferencias Relevantes

```
¿Qué diferencias requieren justificación?

REGLA CONFIGURABLE POR SERVIDOR/ALMACÉN:

1. UMBRAL DE CANTIDAD:
   - diferencia_cantidad_abs >= umbral_cantidad (ej: 0.5 unidades)
   
2. UMBRAL DE VALOR:
   - diferencia_valor_abs >= umbral_valor (ej: $50 MXN)

3. UMBRAL PORCENTUAL:
   - diferencia_porcentaje >= umbral_porcentaje (ej: 5%)

EJEMPLO DE CONFIGURACIÓN:
┌──────────────────┬─────────────┬─────────────┬────────────────┐
│ Almacén          │ Umbral Qty  │ Umbral $    │ Umbral %       │
├──────────────────┼─────────────┼─────────────┼────────────────┤
│ COCINA           │ 0.5         │ 50.00       │ 5%             │
│ BAR              │ 0.25        │ 100.00      │ 3%             │
│ ALMACÉN GENERAL  │ 1.0         │ 200.00      │ 10%            │
└──────────────────┴─────────────┴─────────────┴────────────────┘

LÓGICA:
Si (diff_qty >= umbral_qty) OR (diff_valor >= umbral_valor) OR (diff_pct >= umbral_pct):
    → REQUIERE JUSTIFICACIÓN
Sino:
    → DIFERENCIA MENOR (no requiere justificación)
```

### 2.4 Flujo de Justificación (Encargado)

```python
# Pseudocódigo del proceso de justificación

async def justificar_diferencia(
    diferencia_id: str,
    tipo_justificacion: str,
    comentario: Optional[str],
    usuario: str
) -> JustificacionResult:
    """
    Registra justificación de una diferencia.
    
    Validaciones:
    1. Usuario tiene permiso sobre este almacén
    2. La diferencia pertenece a una tarea EN_PROCESO
    3. No existe justificación previa para esta diferencia
    4. Si tipo='OTRO', comentario es obligatorio
    """
    
    # 1. Validar permisos
    if not usuario_puede_justificar(usuario, diferencia_id):
        raise PermissionDenied("No tiene permiso para justificar")
    
    # 2. Validar estado de la tarea
    tarea = obtener_tarea_de_diferencia(diferencia_id)
    if tarea.estado not in ('PENDIENTE', 'EN_PROCESO'):
        raise InvalidStateError("La tarea no está en estado válido para justificar")
    
    # 3. Validar tipo de justificación
    if tipo_justificacion == 'OTRO' and not comentario:
        raise ValidationError("Comentario obligatorio para tipo OTRO")
    
    # 4. Registrar justificación
    justificacion = crear_justificacion(
        diferencia_id=diferencia_id,
        tipo_justificacion=tipo_justificacion,
        comentario=comentario,
        usuario_justifica=usuario,
        fecha_justificacion=datetime.utcnow()
    )
    
    # 5. Actualizar estado de tarea si primera justificación
    if tarea.estado == 'PENDIENTE':
        actualizar_estado_tarea(tarea.id, 'EN_PROCESO')
    
    # 6. Verificar si todas las diferencias relevantes están justificadas
    if todas_diferencias_justificadas(tarea.id):
        # Notificar o sugerir cambio a JUSTIFICADO
        pass
    
    return justificacion
```

### 2.5 Flujo de Revisión (Auditor)

```python
# Pseudocódigo del proceso de revisión

async def revisar_justificacion(
    justificacion_id: str,
    decision: str,  # 'APROBADA' o 'RECHAZADA'
    comentario_auditor: Optional[str],
    auditor: str
) -> RevisionResult:
    """
    Registra decisión del auditor sobre una justificación.
    
    Si RECHAZADA:
    - Genera automáticamente una Actividad Correctiva
    """
    
    # 1. Validar permisos de auditor
    if not usuario_es_auditor(auditor):
        raise PermissionDenied("Solo auditores pueden revisar")
    
    # 2. Validar estado
    tarea = obtener_tarea_de_justificacion(justificacion_id)
    if tarea.estado not in ('JUSTIFICADO', 'EN_REVISION_AUDITOR'):
        raise InvalidStateError("La tarea no está lista para revisión")
    
    # 3. Registrar revisión
    revision = crear_revision(
        justificacion_id=justificacion_id,
        decision=decision,
        comentario_auditor=comentario_auditor,
        auditor=auditor,
        fecha_revision=datetime.utcnow()
    )
    
    # 4. Si rechazada, crear actividad correctiva
    if decision == 'RECHAZADA':
        crear_actividad_correctiva(
            revision_id=revision.id,
            motivo_rechazo=comentario_auditor,
            responsable_asignado=obtener_responsable_almacen(tarea),
            prioridad=calcular_prioridad(justificacion_id)
        )
    
    # 5. Actualizar estado de tarea si todas revisadas
    if todas_justificaciones_revisadas(tarea.id):
        if alguna_rechazada(tarea.id):
            actualizar_estado_tarea(tarea.id, 'OBSERVADO')
        else:
            actualizar_estado_tarea(tarea.id, 'VALIDADO')
    
    return revision


async def revisar_en_bloque(
    tarea_id: str,
    decision: str,  # 'APROBAR_TODAS' o decisiones individuales
    comentario_general: Optional[str],
    auditor: str
) -> List[RevisionResult]:
    """
    Revisa todas las justificaciones de una tarea en bloque.
    """
    justificaciones = obtener_justificaciones_pendientes(tarea_id)
    resultados = []
    
    for just in justificaciones:
        resultado = await revisar_justificacion(
            justificacion_id=just.id,
            decision=decision,
            comentario_auditor=comentario_general,
            auditor=auditor
        )
        resultados.append(resultado)
    
    return resultados
```

### 2.6 Actividades Correctivas

```
ESTADOS DE ACTIVIDAD CORRECTIVA:

┌─────────────────┐
│     ABIERTA     │ ← Creada automáticamente al rechazar
└────────┬────────┘
         │
         │ Responsable acepta
         ▼
┌─────────────────┐
│   EN_PROCESO    │
└────────┬────────┘
         │
         │ Responsable documenta resolución
         ▼
┌─────────────────┐
│    RESUELTA     │
└────────┬────────┘
         │
         │ Auditor valida resolución
         ▼
┌─────────────────┐
│    CERRADA      │
└─────────────────┘


CAMPOS DE ACTIVIDAD CORRECTIVA:
- actividad_id (PK)
- revision_id (FK) → Revisión que la generó
- analisis_id (FK) → Análisis origen
- diferencia_id (FK) → Diferencia específica
- motivo_rechazo (TEXT)
- responsable_asignado (VARCHAR) → Usuario responsable
- prioridad (ENUM: ALTA, MEDIA, BAJA)
- fecha_limite (DATE, opcional)
- estado (ENUM)
- descripcion_resolucion (TEXT)
- fecha_resolucion (DATETIME)
- auditor_cierre (VARCHAR)
- fecha_cierre (DATETIME)
- comentario_cierre (TEXT)
```

---

## 3. PROPUESTA DE TABLAS

### 3.1 Tabla: `catalogo_tipos_justificacion`

```
Propósito: Catálogo cerrado de tipos de justificación

Campos:
- tipo_id (PK, VARCHAR(10))           Ej: 'MOP', 'ECP'
- nombre (VARCHAR(50), NOT NULL)      Ej: 'MERMA_OPERATIVA'
- descripcion (VARCHAR(500))
- requiere_comentario (BIT, DEFAULT 0)
- requiere_evidencia (BIT, DEFAULT 0)  -- Para futuro
- activo (BIT, DEFAULT 1)
- orden_visualizacion (INT)
- created_at (DATETIME2)
- updated_at (DATETIME2)

Constraints:
- PK: tipo_id
- UNIQUE: nombre

Datos iniciales: Los 9 tipos definidos en sección 2.2
```

### 3.2 Tabla: `tareas_analisis_inventario`

```
Propósito: Tarea pendiente generada por cada análisis

Campos:
- tarea_id (PK, UNIQUEIDENTIFIER)
- analisis_id (FK → folios_procesados.procesado_id, UNIQUE)
- sistema_origen (VARCHAR(20), NOT NULL)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50))
- almacen_id (VARCHAR(50), NOT NULL)
- almacen_nombre (VARCHAR(200))
- folio_inventario (VARCHAR(50), NOT NULL)
- fecha_inventario (DATE, NOT NULL)
- responsable_almacen_id (VARCHAR(100))  -- email del encargado
- responsable_almacen_nombre (VARCHAR(200))
- estado (VARCHAR(30), NOT NULL)
  CHECK IN ('PENDIENTE', 'EN_PROCESO', 'JUSTIFICADO', 
            'EN_REVISION_AUDITOR', 'VALIDADO', 'OBSERVADO', 
            'SIN_DIFERENCIAS', 'CERRADO')
- total_diferencias (INT)
- diferencias_relevantes (INT)
- diferencias_justificadas (INT)
- diferencias_aprobadas (INT)
- diferencias_rechazadas (INT)
- fecha_limite_justificacion (DATE)
- fecha_creacion (DATETIME2, NOT NULL)
- fecha_inicio_justificacion (DATETIME2)
- fecha_fin_justificacion (DATETIME2)
- fecha_inicio_revision (DATETIME2)
- fecha_fin_revision (DATETIME2)
- fecha_cierre (DATETIME2)
- created_by (VARCHAR(100))
- updated_at (DATETIME2)
- updated_by (VARCHAR(100))

Constraints:
- PK: tarea_id
- FK: analisis_id → folios_procesados
- UNIQUE: analisis_id (1:1 con análisis)

Índices:
- IX_tareas_estado_fecha (estado, fecha_creacion)
- IX_tareas_responsable (responsable_almacen_id, estado)
- IX_tareas_server_suc (server_id, sucursal_id, estado)
```

### 3.3 Tabla: `analisis_diferencias`

```
Propósito: Diferencias detectadas en cada análisis (persistidas)

Campos:
- diferencia_id (PK, UNIQUEIDENTIFIER)
- analisis_id (FK → folios_procesados.procesado_id)
- tarea_id (FK → tareas_analisis_inventario.tarea_id)
- codigo_insumo (VARCHAR(50), NOT NULL)
- nombre_insumo (VARCHAR(200))
- unidad_medida (VARCHAR(20))
- categoria (VARCHAR(100))
- familia (VARCHAR(100))
- inv_inicial_qty (DECIMAL(18,4))
- movimientos_qty (DECIMAL(18,4))
- ventas_qty (DECIMAL(18,4))
- inv_teorico_qty (DECIMAL(18,4))
- inv_final_qty (DECIMAL(18,4))
- diferencia_qty (DECIMAL(18,4), NOT NULL)
- diferencia_valor (DECIMAL(18,2))
- diferencia_porcentaje (DECIMAL(10,4))
- es_diferencia_relevante (BIT, NOT NULL)  -- Según umbrales
- requiere_justificacion (BIT, NOT NULL)
- estado_justificacion (VARCHAR(20))
  CHECK IN ('PENDIENTE', 'JUSTIFICADA', 'APROBADA', 'RECHAZADA', 'NO_REQUERIDA')
- created_at (DATETIME2)

Constraints:
- PK: diferencia_id
- FK: analisis_id → folios_procesados
- FK: tarea_id → tareas_analisis_inventario

Índices:
- IX_diferencias_analisis (analisis_id)
- IX_diferencias_tarea (tarea_id, es_diferencia_relevante)
- IX_diferencias_estado (estado_justificacion)
```

### 3.4 Tabla: `justificaciones_inventario`

```
Propósito: Justificaciones capturadas por el encargado

Campos:
- justificacion_id (PK, UNIQUEIDENTIFIER)
- diferencia_id (FK → analisis_diferencias.diferencia_id, UNIQUE)
- tarea_id (FK → tareas_analisis_inventario.tarea_id)
- tipo_justificacion_id (FK → catalogo_tipos_justificacion.tipo_id)
- comentario (NVARCHAR(1000))
- usuario_justifica (VARCHAR(100), NOT NULL)
- nombre_usuario_justifica (VARCHAR(200))
- fecha_justificacion (DATETIME2, NOT NULL)
- evidencia_adjunta (BIT, DEFAULT 0)  -- Para futuro
- evidencia_path (VARCHAR(500))       -- Para futuro
- estado_revision (VARCHAR(20), DEFAULT 'PENDIENTE')
  CHECK IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')
- created_at (DATETIME2)
- updated_at (DATETIME2)

Constraints:
- PK: justificacion_id
- FK: diferencia_id → analisis_diferencias
- FK: tarea_id → tareas_analisis_inventario
- FK: tipo_justificacion_id → catalogo_tipos_justificacion
- UNIQUE: diferencia_id (1:1 con diferencia)

Índices:
- IX_justificaciones_tarea (tarea_id, estado_revision)
- IX_justificaciones_tipo (tipo_justificacion_id)
- IX_justificaciones_usuario (usuario_justifica, fecha_justificacion)
```

### 3.5 Tabla: `revisiones_auditor`

```
Propósito: Decisiones del auditor sobre justificaciones

Campos:
- revision_id (PK, UNIQUEIDENTIFIER)
- justificacion_id (FK → justificaciones_inventario.justificacion_id, UNIQUE)
- tarea_id (FK → tareas_analisis_inventario.tarea_id)
- decision (VARCHAR(20), NOT NULL)
  CHECK IN ('APROBADA', 'RECHAZADA')
- comentario_auditor (NVARCHAR(1000))
- auditor_id (VARCHAR(100), NOT NULL)
- auditor_nombre (VARCHAR(200))
- fecha_revision (DATETIME2, NOT NULL)
- revision_en_bloque (BIT, DEFAULT 0)  -- Si fue parte de revisión masiva
- created_at (DATETIME2)

Constraints:
- PK: revision_id
- FK: justificacion_id → justificaciones_inventario
- FK: tarea_id → tareas_analisis_inventario
- UNIQUE: justificacion_id (1:1)

Índices:
- IX_revisiones_tarea (tarea_id, decision)
- IX_revisiones_auditor (auditor_id, fecha_revision)
```

### 3.6 Tabla: `actividades_correctivas`

```
Propósito: Acciones correctivas por justificaciones rechazadas

Campos:
- actividad_id (PK, UNIQUEIDENTIFIER)
- revision_id (FK → revisiones_auditor.revision_id)
- analisis_id (FK → folios_procesados.procesado_id)
- diferencia_id (FK → analisis_diferencias.diferencia_id)
- tarea_id (FK → tareas_analisis_inventario.tarea_id)
- codigo_insumo (VARCHAR(50))
- nombre_insumo (VARCHAR(200))
- cantidad_diferencia (DECIMAL(18,4))
- valor_diferencia (DECIMAL(18,2))
- motivo_rechazo (NVARCHAR(1000), NOT NULL)
- responsable_asignado_id (VARCHAR(100), NOT NULL)
- responsable_asignado_nombre (VARCHAR(200))
- prioridad (VARCHAR(10), DEFAULT 'MEDIA')
  CHECK IN ('ALTA', 'MEDIA', 'BAJA')
- fecha_limite (DATE)
- estado (VARCHAR(20), NOT NULL, DEFAULT 'ABIERTA')
  CHECK IN ('ABIERTA', 'EN_PROCESO', 'RESUELTA', 'CERRADA')
- descripcion_resolucion (NVARCHAR(2000))
- fecha_aceptacion (DATETIME2)
- fecha_resolucion (DATETIME2)
- auditor_cierre_id (VARCHAR(100))
- auditor_cierre_nombre (VARCHAR(200))
- fecha_cierre (DATETIME2)
- comentario_cierre (NVARCHAR(1000))
- created_at (DATETIME2)
- updated_at (DATETIME2)

Constraints:
- PK: actividad_id
- FK: revision_id → revisiones_auditor
- FK: analisis_id → folios_procesados
- FK: diferencia_id → analisis_diferencias
- FK: tarea_id → tareas_analisis_inventario

Índices:
- IX_actividades_estado (estado, prioridad)
- IX_actividades_responsable (responsable_asignado_id, estado)
- IX_actividades_tarea (tarea_id)
- IX_actividades_fecha_limite (fecha_limite, estado)
```

### 3.7 Tabla: `configuracion_umbrales_diferencias`

```
Propósito: Umbrales configurables para diferencias relevantes

Campos:
- config_id (PK, UNIQUEIDENTIFIER)
- server_id (VARCHAR(50), NOT NULL)
- sucursal_id (VARCHAR(50))  -- NULL = aplica a todo el servidor
- almacen_id (VARCHAR(50))   -- NULL = aplica a toda la sucursal
- umbral_cantidad (DECIMAL(18,4), DEFAULT 0.5)
- umbral_valor (DECIMAL(18,2), DEFAULT 50.00)
- umbral_porcentaje (DECIMAL(5,2), DEFAULT 5.00)
- dias_limite_justificacion (INT, DEFAULT 3)
- activo (BIT, DEFAULT 1)
- created_at (DATETIME2)
- created_by (VARCHAR(100))
- updated_at (DATETIME2)
- updated_by (VARCHAR(100))

Constraints:
- PK: config_id
- UNIQUE: (server_id, sucursal_id, almacen_id)

Índices:
- IX_umbrales_server (server_id, sucursal_id, almacen_id)
```

### 3.8 Diagrama de Relaciones

```
┌──────────────────────────┐
│ folios_procesados        │
│ (análisis ejecutado)     │
└─────────────┬────────────┘
              │ 1
              │
              │ 1
              ▼
┌──────────────────────────┐
│ tareas_analisis_inv      │◄──────────────────────────────────┐
└─────────────┬────────────┘                                   │
              │ 1                                               │
              │                                                 │
              │ N                                               │
              ▼                                                 │
┌──────────────────────────┐      ┌──────────────────────────┐ │
│ analisis_diferencias     │      │ catalogo_tipos_just      │ │
└─────────────┬────────────┘      └──────────────────────────┘ │
              │ 1                            ▲                  │
              │                              │ N                │
              │ 0..1                         │                  │
              ▼                              │                  │
┌──────────────────────────┐                 │                  │
│ justificaciones_inv      │─────────────────┘                  │
└─────────────┬────────────┘                                    │
              │ 1                                               │
              │                                                 │
              │ 0..1                                            │
              ▼                                                 │
┌──────────────────────────┐                                    │
│ revisiones_auditor       │                                    │
└─────────────┬────────────┘                                    │
              │ 1                                               │
              │                                                 │
              │ 0..1 (si RECHAZADA)                             │
              ▼                                                 │
┌──────────────────────────┐                                    │
│ actividades_correctivas  │────────────────────────────────────┘
└──────────────────────────┘
```

---

## 4. INTEGRACIÓN CON TAREA EXISTENTE

### 4.1 Punto de Extensión en service.py

```python
# En el orquestador de Fase 1, DESPUÉS de notificar

async def procesar_folio(
    servidor: dict,
    folio_nuevo: FolioDetectado
) -> ProcessResult:
    """
    Flujo completo de procesamiento.
    EXTENDIDO con creación de tarea.
    """
    
    # ... código existente de Fase 1 ...
    
    # 1. Adquirir lock (existente)
    # 2. Resolver inventario inicial (existente)
    # 3. Generar análisis (existente)
    # 4. Exportar Excel (existente)
    # 5. Enviar notificaciones (existente)
    
    # === EXTENSIÓN FASE 1.5 ===
    # 6. Persistir diferencias del análisis
    diferencias = await persistir_diferencias_analisis(
        analisis_id=procesado_id,
        data=resultado_analisis.data,
        umbrales=obtener_umbrales(servidor.id, sucursal_id, almacen_id)
    )
    
    # 7. Crear tarea pendiente
    tarea = await crear_tarea_analisis(
        analisis_id=procesado_id,
        sistema_origen=sistema_origen,
        servidor=servidor,
        sucursal_id=sucursal_id,
        almacen_id=almacen_id,
        folio=folio_nuevo.folio,
        fecha=folio_nuevo.fecha,
        diferencias=diferencias,
        responsable=obtener_responsable_almacen(servidor.id, almacen_id)
    )
    
    # 8. Liberar lock (existente)
    
    return ProcessResult(
        exito=True,
        tarea_id=tarea.tarea_id
    )
```

### 4.2 Creación de Tarea

```python
async def crear_tarea_analisis(
    analisis_id: str,
    sistema_origen: str,
    servidor: dict,
    sucursal_id: Optional[str],
    almacen_id: str,
    folio: str,
    fecha: str,
    diferencias: List[Diferencia],
    responsable: Optional[Responsable]
) -> TareaAnalisis:
    """
    Crea tarea pendiente para el análisis procesado.
    """
    
    # Calcular estadísticas
    total = len(diferencias)
    relevantes = len([d for d in diferencias if d.es_relevante])
    
    # Determinar estado inicial
    estado_inicial = 'PENDIENTE' if relevantes > 0 else 'SIN_DIFERENCIAS'
    
    tarea = TareaAnalisis(
        tarea_id=str(uuid.uuid4()),
        analisis_id=analisis_id,
        sistema_origen=sistema_origen,
        server_id=servidor['id'],
        sucursal_id=sucursal_id,
        almacen_id=almacen_id,
        almacen_nombre=servidor.get('almacen_nombre', ''),
        folio_inventario=folio,
        fecha_inventario=fecha,
        responsable_almacen_id=responsable.email if responsable else None,
        responsable_almacen_nombre=responsable.nombre if responsable else None,
        estado=estado_inicial,
        total_diferencias=total,
        diferencias_relevantes=relevantes,
        diferencias_justificadas=0,
        diferencias_aprobadas=0,
        diferencias_rechazadas=0,
        fecha_limite_justificacion=calcular_fecha_limite(fecha),
        fecha_creacion=datetime.utcnow(),
        created_by='AUTOMATICO'
    )
    
    await guardar_tarea(tarea)
    
    return tarea
```

### 4.3 Relación Tarea ↔ Análisis

```
REGLA: 1 Análisis = 1 Tarea

- El análisis se identifica por: procesado_id en folios_procesados
- La tarea referencia al análisis vía: analisis_id (FK, UNIQUE)
- Las diferencias se persisten vinculadas a ambos
- La clave única sigue siendo:
  (sistema_origen, server_id, sucursal_id, almacen_id, folio, fecha)
```

---

## 5. INTEGRACIÓN CON RBAC

### 5.1 Nuevos Permisos Requeridos

```
MÓDULO: justificaciones

┌────────────────────────────┬──────────────────────────────────────────────┐
│ Permiso                    │ Descripción                                  │
├────────────────────────────┼──────────────────────────────────────────────┤
│ justificaciones.view       │ Ver tareas y diferencias de su alcance      │
│ justificaciones.edit       │ Capturar justificaciones                     │
│ justificaciones.review     │ Revisar y aprobar/rechazar (solo auditor)   │
│ justificaciones.admin      │ Administrar catálogos y umbrales            │
└────────────────────────────┴──────────────────────────────────────────────┘

MÓDULO: actividades

┌────────────────────────────┬──────────────────────────────────────────────┐
│ Permiso                    │ Descripción                                  │
├────────────────────────────┼──────────────────────────────────────────────┤
│ actividades.view           │ Ver actividades correctivas asignadas       │
│ actividades.edit           │ Actualizar estado y resolución              │
│ actividades.close          │ Cerrar actividades (solo auditor)           │
│ actividades.admin          │ Ver todas, reasignar, etc.                  │
└────────────────────────────┴──────────────────────────────────────────────┘
```

### 5.2 Matriz de Permisos por Rol

```
┌──────────────────────┬───────────────────────────────────────────────────────────┐
│ Rol                  │ Permisos                                                  │
├──────────────────────┼───────────────────────────────────────────────────────────┤
│ Encargado Almacén    │ justificaciones.view (su almacén)                        │
│                      │ justificaciones.edit (su almacén)                        │
│                      │ actividades.view (sus actividades)                       │
│                      │ actividades.edit (sus actividades)                       │
├──────────────────────┼───────────────────────────────────────────────────────────┤
│ Supervisor Sucursal  │ justificaciones.view (su sucursal)                       │
│                      │ justificaciones.edit (su sucursal, backup)               │
│                      │ actividades.view (su sucursal)                           │
│                      │ actividades.edit (su sucursal)                           │
├──────────────────────┼───────────────────────────────────────────────────────────┤
│ Auditor              │ justificaciones.view (su alcance)                        │
│                      │ justificaciones.review                                    │
│                      │ actividades.view (su alcance)                            │
│                      │ actividades.close                                         │
├──────────────────────┼───────────────────────────────────────────────────────────┤
│ Administrador        │ * (todos los permisos)                                   │
│                      │ justificaciones.admin                                     │
│                      │ actividades.admin                                         │
└──────────────────────┴───────────────────────────────────────────────────────────┘
```

### 5.3 Validación de Alcance

```python
def validar_acceso_tarea(usuario: dict, tarea: TareaAnalisis) -> bool:
    """
    Valida que el usuario puede acceder a esta tarea.
    Reutiliza la lógica existente de RBAC.
    """
    
    # Administrador: acceso total
    if usuario.get('role') == 'Administrador':
        return True
    
    # Verificar acceso al servidor
    if not user_has_server_access(usuario, tarea.server_id):
        return False
    
    # Verificar acceso a la sucursal
    allowed_sucursales = usuario.get('allowed_sucursales', {})
    if tarea.server_id in allowed_sucursales:
        if tarea.sucursal_id not in allowed_sucursales[tarea.server_id]:
            return False
    
    # Verificar acceso al almacén (si hay restricción)
    allowed_almacenes = usuario.get('allowed_almacenes', {})
    if tarea.server_id in allowed_almacenes:
        if tarea.almacen_id not in allowed_almacenes[tarea.server_id]:
            return False
    
    return True
```

### 5.4 Flujo de Permisos por Acción

```
JUSTIFICAR:
1. Usuario tiene permiso justificaciones.edit
2. Usuario tiene alcance sobre el almacén de la tarea
3. La tarea está en estado PENDIENTE o EN_PROCESO

REVISAR:
1. Usuario tiene permiso justificaciones.review
2. Usuario tiene alcance sobre la sucursal/servidor
3. La tarea está en estado JUSTIFICADO o EN_REVISION_AUDITOR

CERRAR ACTIVIDAD:
1. Usuario tiene permiso actividades.close
2. Usuario tiene alcance sobre la actividad
3. La actividad está en estado RESUELTA
```

---

## 6. FLUJO ORQUESTADO ACTUALIZADO

### 6.1 Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUJO ORQUESTADO COMPLETO (Fase 1 + 1.5)                 │
└─────────────────────────────────────────────────────────────────────────────┘

FASE 1 (Automatización - Síncrono):
════════════════════════════════════

    ┌──────────────────┐
    │  SCHEDULER       │
    │  (Cada 15 min)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Detectar nuevos  │
    │ folios           │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Adquirir lock    │
    │ (heartbeat)      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Resolver inv     │
    │ inicial          │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Generar análisis │
    │ (core service)   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Exportar Excel   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Enviar email     │
    │ (destinatarios)  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ PERSISTIR        │  ← NUEVO
    │ DIFERENCIAS      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ CREAR TAREA      │  ← NUEVO
    │ PENDIENTE        │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Liberar lock     │
    └──────────────────┘


FASE 1.5 (Justificación - Asíncrono, Backend):
══════════════════════════════════════════════

    ┌──────────────────┐
    │ TAREA PENDIENTE  │
    │ (espera acción)  │
    └────────┬─────────┘
             │
             │ Encargado inicia
             ▼
    ┌──────────────────┐
    │ EN_PROCESO       │
    │                  │
    │ Encargado        │
    │ justifica cada   │
    │ diferencia       │
    └────────┬─────────┘
             │
             │ Todas justificadas
             ▼
    ┌──────────────────┐
    │ JUSTIFICADO      │
    │ (listo revisión) │
    └────────┬─────────┘
             │
             │ Auditor revisa
             ▼
    ┌──────────────────┐
    │ EN_REVISION_     │
    │ AUDITOR          │
    └────────┬─────────┘
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
┌────────────┐ ┌────────────┐
│ Todas      │ │ Alguna     │
│ aprobadas  │ │ rechazada  │
└─────┬──────┘ └─────┬──────┘
      │              │
      ▼              ▼
┌────────────┐ ┌────────────┐
│ VALIDADO   │ │ OBSERVADO  │
│            │ │            │
│ Sin        │ │ Genera     │
│ hallazgos  │ │ actividades│
└────────────┘ └─────┬──────┘
                     │
                     │ Actividades resueltas y cerradas
                     ▼
              ┌────────────┐
              │ CERRADO    │
              │            │
              │ Proceso    │
              │ completo   │
              └────────────┘
```

### 6.2 Endpoints de Fase 1.5 (Backend Only)

```
TAREAS:
────────────────────────────────────────────────────────────────────
GET  /api/justificaciones/tareas
     → Lista tareas según alcance del usuario
     
GET  /api/justificaciones/tareas/{tarea_id}
     → Detalle de tarea con diferencias

POST /api/justificaciones/tareas/{tarea_id}/iniciar
     → Cambia estado PENDIENTE → EN_PROCESO

POST /api/justificaciones/tareas/{tarea_id}/sin-diferencias
     → Marca como SIN_DIFERENCIAS (requiere confirmación)

POST /api/justificaciones/tareas/{tarea_id}/enviar-revision
     → Cambia estado a JUSTIFICADO (valida que todo esté justificado)


JUSTIFICACIONES:
────────────────────────────────────────────────────────────────────
GET  /api/justificaciones/tareas/{tarea_id}/diferencias
     → Lista diferencias de una tarea

POST /api/justificaciones/diferencias/{diferencia_id}/justificar
     Body: {tipo_justificacion, comentario}
     → Registra justificación

PUT  /api/justificaciones/{justificacion_id}
     → Actualiza justificación (solo antes de revisión)


REVISIÓN:
────────────────────────────────────────────────────────────────────
GET  /api/justificaciones/revision/pendientes
     → Lista tareas pendientes de revisión (para auditor)

POST /api/justificaciones/revision/{justificacion_id}
     Body: {decision, comentario_auditor}
     → Registra decisión

POST /api/justificaciones/revision/tareas/{tarea_id}/bloque
     Body: {decision, comentario_general}
     → Revisa todas las justificaciones en bloque


ACTIVIDADES CORRECTIVAS:
────────────────────────────────────────────────────────────────────
GET  /api/actividades/mis-actividades
     → Lista actividades del usuario

GET  /api/actividades/{actividad_id}
     → Detalle de actividad

POST /api/actividades/{actividad_id}/aceptar
     → Cambia ABIERTA → EN_PROCESO

POST /api/actividades/{actividad_id}/resolver
     Body: {descripcion_resolucion}
     → Cambia EN_PROCESO → RESUELTA

POST /api/actividades/{actividad_id}/cerrar
     Body: {comentario_cierre}
     → Cambia RESUELTA → CERRADA (solo auditor)


CATÁLOGOS:
────────────────────────────────────────────────────────────────────
GET  /api/justificaciones/catalogo/tipos
     → Lista tipos de justificación activos

GET  /api/justificaciones/configuracion/umbrales/{server_id}
     → Obtiene umbrales configurados

PUT  /api/justificaciones/configuracion/umbrales
     Body: {server_id, sucursal_id, almacen_id, umbrales}
     → Configura umbrales (solo admin)


INFORMES:
────────────────────────────────────────────────────────────────────
GET  /api/justificaciones/informe/{tarea_id}
     → Genera informe completo de auditoría

GET  /api/justificaciones/informe/{tarea_id}/pdf
     → Descarga informe en PDF
```

---

## 7. ESTRATEGIA ANTI-DUPLICADOS

### 7.1 Nivel Tarea

```
REGLA: 1 análisis = 1 tarea

- analisis_id es FK UNIQUE en tareas_analisis_inventario
- No puede existir más de una tarea para el mismo análisis
- El análisis ya tiene su propia protección anti-duplicados (hash)
```

### 7.2 Nivel Justificación

```
REGLA: 1 diferencia = máximo 1 justificación

- diferencia_id es FK UNIQUE en justificaciones_inventario
- Antes de insertar, verificar que no existe justificación previa
- Si existe, rechazar con error claro
```

### 7.3 Nivel Revisión

```
REGLA: 1 justificación = máximo 1 revisión

- justificacion_id es FK UNIQUE en revisiones_auditor
- Doble validación:
  1. Constraint de BD
  2. Verificación en código antes de insertar
```

### 7.4 Nivel Actividad Correctiva

```
REGLA: 1 revisión rechazada = 1 actividad

- revision_id es FK en actividades_correctivas
- Solo se crea si decision = 'RECHAZADA'
- Creación automática e inmediata al rechazar
```

---

## 8. RIESGOS DE REGRESIÓN

### 8.1 Análisis de Riesgos

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        MATRIZ DE RIESGOS DE REGRESIÓN                      │
├──────┬─────────────────────────────┬──────────┬─────────┬──────────────────┤
│ ID   │ Riesgo                      │ Prob.    │ Impacto │ Mitigación       │
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-01│ Modificar flujo Fase 1      │ BAJA     │ ALTO    │ Solo AGREGAR paso│
│      │                             │          │         │ al final, no     │
│      │                             │          │         │ modificar pasos  │
│      │                             │          │         │ existentes       │
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-02│ Afectar performance del     │ MEDIA    │ MEDIO   │ Persistir difs   │
│      │ ciclo de automatización     │          │         │ en batch, no     │
│      │                             │          │         │ uno por uno      │
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-03│ Romper análisis existente   │ MUY BAJA │ ALTO    │ Core service     │
│      │                             │          │         │ no se modifica   │
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-04│ Conflicto con RBAC actual   │ BAJA     │ MEDIO   │ Extender permisos│
│      │                             │          │         │ no reemplazar    │
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-05│ Impacto en UI de Reportes   │ NULO     │ N/A     │ Sin cambios en   │
│      │                             │          │         │ frontend Fase 1.5│
├──────┼─────────────────────────────┼──────────┼─────────┼──────────────────┤
│ RR-06│ Falla al crear tarea rompe  │ MEDIA    │ MEDIO   │ Try/catch en paso│
│      │ el flujo completo           │          │         │ de tarea, log    │
│      │                             │          │         │ error, continuar │
└──────┴─────────────────────────────┴──────────┴─────────┴──────────────────┘
```

### 8.2 Estrategia de Aislamiento

```python
# La creación de tarea está aislada del flujo principal

async def procesar_folio(servidor, folio_nuevo):
    """
    El flujo principal (Fase 1) es INDEPENDIENTE de la tarea.
    Si falla la tarea, el análisis y notificación ya se completaron.
    """
    
    try:
        # === FASE 1 (Crítica - ya probada) ===
        resultado = await ejecutar_flujo_fase_1(servidor, folio_nuevo)
        
        if not resultado.exito:
            return resultado
        
        # === FASE 1.5 (Extensión - aislada) ===
        try:
            tarea = await crear_tarea_con_diferencias(
                analisis_id=resultado.procesado_id,
                diferencias=resultado.diferencias
            )
            resultado.tarea_id = tarea.tarea_id
            
        except Exception as e:
            # Error en tarea NO afecta el resultado del análisis
            logging.error(f"Error creando tarea (no crítico): {e}")
            resultado.tarea_id = None
            resultado.warning = "Análisis exitoso pero tarea no creada"
            # NO lanzar excepción - el análisis fue exitoso
        
        return resultado
        
    except Exception as e:
        # Error en Fase 1 - esto sí es crítico
        raise
```

### 8.3 Pruebas de No Regresión

```
CHECKLIST OBLIGATORIO ANTES DE DEPLOY:

□ Test E2E: Ciclo Fase 1 funciona igual que antes
  - Detecta folios
  - Genera análisis
  - Exporta Excel
  - Envía email
  - Resultado IDÉNTICO a versión anterior

□ Test unitario: crear_tarea_con_diferencias
  - Crea tarea correctamente
  - Persiste diferencias correctamente
  - Calcula umbrales correctamente

□ Test de aislamiento: Fallo en tarea no rompe ciclo
  - Simular error en BD al crear tarea
  - Verificar que el análisis se completó

□ Test de permisos: RBAC funciona correctamente
  - Encargado solo ve sus tareas
  - Auditor puede revisar
  - Administrador ve todo
```

---

## 9. PLAN DE FASES ACTUALIZADO

### 9.1 Estructura de Fases

```
FASE 1: Automatización Base (YA APROBADA)
═══════════════════════════════════════════
- Detección de folios
- Generación de análisis
- Exportación Excel
- Envío de email
- Control de duplicados y concurrencia
Duración: ~6 semanas

FASE 1.5: Justificación y Auditoría (NUEVA)
═══════════════════════════════════════════
- Persistencia de diferencias
- Creación de tarea pendiente
- Endpoints de justificación
- Endpoints de revisión
- Actividades correctivas
- Catálogos y configuración
Duración: ~3-4 semanas

FASE 2: UI y WhatsApp (POSTERIOR)
═══════════════════════════════════════════
- UI de tareas pendientes
- UI de justificación
- UI de revisión auditor
- Dashboard de actividades
- Integración WhatsApp
Duración: ~4-5 semanas
```

### 9.2 Detalle de Fase 1.5

```
FASE 1.5A: Persistencia (1 semana)
──────────────────────────────────
□ Crear tablas SQL en EDARSA HUB:
  - catalogo_tipos_justificacion
  - tareas_analisis_inventario
  - analisis_diferencias
  - configuracion_umbrales_diferencias
□ Cargar datos iniciales del catálogo
□ Configurar umbrales por defecto
□ Tests de inserción y consulta

FASE 1.5B: Extensión del Orquestador (1 semana)
───────────────────────────────────────────────
□ Modificar service.py:
  - Agregar persistir_diferencias_analisis()
  - Agregar crear_tarea_analisis()
□ Implementar cálculo de umbrales
□ Implementar asignación de responsable
□ Tests de integración
□ Validar que Fase 1 no se afecta

FASE 1.5C: Justificación (1 semana)
───────────────────────────────────
□ Crear tablas:
  - justificaciones_inventario
□ Implementar endpoints:
  - GET /tareas
  - GET /tareas/{id}
  - POST /diferencias/{id}/justificar
  - PUT /justificaciones/{id}
  - POST /tareas/{id}/enviar-revision
□ Implementar validaciones de estado
□ Tests unitarios y de API

FASE 1.5D: Revisión y Actividades (1 semana)
────────────────────────────────────────────
□ Crear tablas:
  - revisiones_auditor
  - actividades_correctivas
□ Implementar endpoints:
  - GET /revision/pendientes
  - POST /revision/{id}
  - POST /revision/tareas/{id}/bloque
  - GET /actividades/*
  - POST /actividades/{id}/aceptar
  - POST /actividades/{id}/resolver
  - POST /actividades/{id}/cerrar
□ Implementar generación automática de actividades
□ Tests completos

FASE 1.5E: Integración RBAC (2-3 días)
──────────────────────────────────────
□ Definir nuevos permisos
□ Asignar permisos a roles existentes
□ Implementar validación de acceso en todos los endpoints
□ Tests de autorización
```

### 9.3 Cronograma Visual Actualizado

```
Semana 1-6:    FASE 1 (Automatización Base)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ 0 │ 1A │ 1B │ 1C │ 1D │ 1E-1F │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Semana 7-10:   FASE 1.5 (Justificación - Backend)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ 1.5A │ 1.5B │ 1.5C │ 1.5D │ 1.5E │
│ SQL  │ Orq. │ Just │ Rev  │ RBAC │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAUSA: Validación y estabilización - 1-2 semanas]

Semana 13-17:  FASE 2 (UI + WhatsApp)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ UI Tareas │ UI Just │ UI Rev │ Dashboard │ WA │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 9.4 Dependencias entre Fases

```
FASE 1 ─────────────────┐
(Automatización)        │
                        ▼
                 ┌─────────────┐
                 │  FASE 1.5   │
                 │ (Justific.) │
                 └──────┬──────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     ┌─────────────┐         ┌─────────────┐
     │   FASE 2A   │         │   FASE 2B   │
     │   (UI)      │         │ (WhatsApp)  │
     └─────────────┘         └─────────────┘

Notas:
- Fase 1.5 requiere Fase 1 completada
- Fase 2A (UI) requiere Fase 1.5 completada
- Fase 2B (WhatsApp) puede hacerse en paralelo a UI
```

---

## 10. VALIDACIÓN DE NO RUPTURA

### 10.1 Checklist de Validación

```
ANTES DE APROBAR DISEÑO:
══════════════════════════

✓ ¿El Core Service de análisis se modifica?
  → NO. Se usa tal cual.

✓ ¿El detector de folios se modifica?
  → NO. Funciona igual.

✓ ¿El LockManager se modifica?
  → NO. Se reutiliza sin cambios.

✓ ¿La clave única cambia?
  → NO. Sigue siendo (sistema_origen, server_id, sucursal_id, 
    almacen_id, folio, fecha).

✓ ¿Los endpoints existentes se modifican?
  → NO. Se agregan nuevos endpoints.

✓ ¿El frontend se modifica en Fase 1.5?
  → NO. Es 100% backend.

✓ ¿Las tablas existentes se modifican?
  → NO. Se agregan tablas nuevas.

✓ ¿El flujo de Fase 1 se interrumpe si Fase 1.5 falla?
  → NO. La tarea es un paso aislado al final.

✓ ¿El RBAC existente se reemplaza?
  → NO. Se extiende con nuevos permisos.
```

### 10.2 Garantía de Compatibilidad

```
DECLARACIÓN FORMAL:

1. El flujo de Fase 1 (automatización) funciona IDÉNTICO
   con o sin Fase 1.5.

2. Si se desactiva Fase 1.5, el sistema vuelve al comportamiento
   de Fase 1 pura (análisis + notificación, sin tareas).

3. Todas las tablas nuevas son ADICIONALES, no reemplazan
   estructuras existentes.

4. Todos los endpoints nuevos tienen prefijos distintos
   (/api/justificaciones/, /api/actividades/).

5. El frontend actual NO se toca en Fase 1.5.
```

### 10.3 Feature Flag

```python
# Configuración para activar/desactivar Fase 1.5

FASE_1_5_ACTIVA = os.environ.get('FASE_1_5_ACTIVA', 'false').lower() == 'true'

async def procesar_folio(servidor, folio_nuevo):
    # ... flujo Fase 1 ...
    
    if FASE_1_5_ACTIVA:
        # Crear tarea y persistir diferencias
        await crear_tarea_con_diferencias(...)
    
    # ... fin ...
```

---

## RESUMEN DE ADENDA C

### Elementos Incorporados

| Elemento | Estado |
|----------|--------|
| Modelo funcional de justificación | ✅ Definido |
| Catálogo de tipos de justificación | ✅ Definido (9 tipos) |
| Flujo de revisión por auditor | ✅ Definido |
| Actividades correctivas | ✅ Definido |
| 8 tablas propuestas | ✅ Diseñadas |
| Integración con tarea existente | ✅ Definida |
| Integración con RBAC | ✅ Definida (4 permisos nuevos) |
| Estrategia anti-duplicados | ✅ Definida |
| Riesgos de regresión | ✅ Analizados |
| Plan de Fase 1.5 | ✅ Definido (~4 semanas) |
| Validación de no ruptura | ✅ Confirmada |

### Documentos de Referencia

| Documento | Contenido |
|-----------|-----------|
| ARQUITECTURA_v1.md | Diseño principal |
| ADENDA_A.md | Core Service, clave única, destinatarios |
| ADENDA_B.md | Sistema origen en clave, heartbeat |
| **ADENDA_C.md** | **Justificación y auditoría (este doc)** |

---

## SIGUIENTE PASO

**¿Se aprueba la Adenda C para proceder con implementación?**

Puntos de confirmación:
1. ¿El catálogo de 9 tipos de justificación es suficiente?
2. ¿Los umbrales configurables son correctos?
3. ¿La máquina de estados de la tarea está completa?
4. ¿El plan de Fase 1.5 (~4 semanas) es aceptable?

---

*Adenda CAB-003-C - Diciembre 2025*
