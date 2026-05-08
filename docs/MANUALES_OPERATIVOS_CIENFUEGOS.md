# Manuales Operativos - Modelo Cienfuegos

**Fecha implementación:** 2026-04-19  
**Módulo:** `modules/manuales_operativos`  
**Estado:** OPERATIVO ✅

## Descripción

Sistema de generación automática de documentación operativa cuando los procesos llegan a estados finales (COMPLETADA, CERRADO, APROBADO, RECHAZADO).

Los manuales se generan en **formato Cienfuegos**, el estándar de EDARSA para documentación operativa.

## Principio Rector

**EDARSA HUB es el cerebro del sistema.**

Los manuales se generan desde:
- Datos reales del proceso
- Historial/bitácora de eventos
- Decisiones tomadas (autorizaciones)
- Usuarios involucrados

**NO son manuales genéricos.** Cada manual es único basado en la ejecución real.

## Estructura del Manual (Modelo Cienfuegos)

1. **Nombre del proceso**
2. **Objetivo**
3. **Alcance**
4. **Responsables** (con acciones y fechas)
5. **Procedimiento paso a paso** (basado en eventos reales de bitácora)
6. **Políticas/reglas aplicadas**
7. **Evidencia generada**
8. **Observaciones y áreas de mejora**
9. **Métricas del proceso**

## Colección MongoDB

```javascript
db.manuales_operativos
{
  "id": "uuid",
  "modulo": "compras",
  "proceso_id": "uuid",
  "proceso_tipo": "auditoria_compras",
  "empresa_id": "uuid",
  "empresa_nombre": "string",
  "sucursal_id": "uuid",
  "sucursal_nombre": "string",
  "nombre_proceso": "Auditoría Operativa de Compras - Sucursal Centro",
  "formato": "cienfuegos",
  "contenido": {
    "nombre_proceso": "...",
    "objetivo": "...",
    "alcance": "...",
    "responsables": [...],
    "procedimiento": [...],
    "politicas": [...],
    "evidencias": [...],
    "observaciones": [...],
    "areas_mejora": [...],
    "metricas": {...}
  },
  "estado_proceso_final": "APROBADO",
  "generado_por": "sistema",
  "created_at": "date",
  "version": 1,
  "activo": true
}
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/manuales-operativos` | Lista manuales con filtros |
| GET | `/api/manuales-operativos/{id}` | Obtiene manual por ID |
| GET | `/api/manuales-operativos/proceso/{proceso_id}` | Manual de un proceso |
| GET | `/api/manuales-operativos/{id}/exportar` | Exporta en texto plano |
| POST | `/api/manuales-operativos/generar/{proceso_id}?modulo=compras` | Genera manual bajo demanda |

## Trigger Automático

El manual se genera automáticamente cuando un proceso cambia a:
- `APROBADO`
- `RECHAZADO`
- `COMPLETADA`
- `CERRADO`
- `FINALIZADO`

### Integración en Servicio de Compras

```python
# En automatizacion_compras_service.py
if accion == "aprobar":
    # ... actualizar estado ...
    self._generar_manual_operativo(automatizacion_id)  # <-- TRIGGER
```

## Archivos del Módulo

```
/app/backend/modules/manuales_operativos/
├── __init__.py
├── schemas.py      # Modelos Pydantic
├── service.py      # Lógica de generación
├── routes.py       # Endpoints API
└── triggers.py     # Funciones trigger (sync/async)
```

## Uso

### Consultar manuales
```bash
curl "$API/api/manuales-operativos" -H "Authorization: Bearer $TOKEN"
```

### Exportar a texto
```bash
curl "$API/api/manuales-operativos/{id}/exportar" -H "Authorization: Bearer $TOKEN"
```

### Generar manualmente
```bash
curl -X POST "$API/api/manuales-operativos/generar/{proceso_id}?modulo=compras" \
  -H "Authorization: Bearer $TOKEN"
```

## Módulos Soportados

- [x] **Compras** (Auditoría Operativa)
- [ ] Operaciones (pendiente)
- [ ] Finanzas (pendiente)
- [ ] Comercial (pendiente)
- [ ] RH (pendiente)

## Mapeo de Eventos a Pasos Operativos

Los eventos de bitácora se convierten automáticamente a pasos del procedimiento:

| Evento | Paso Operativo |
|--------|----------------|
| CREADA | Se inició el proceso de auditoría operativa |
| PENDIENTE_INVENTARIO | Se detectó que falta inventario físico |
| INVENTARIO_CAPTURADO | Se capturó el inventario físico requerido |
| AUDITORIA_COMPLETADA | Se completó el análisis de auditoría |
| ENVIADA_GERENCIA | Se envió a gerencia para revisión |
| APROBADA_GERENCIA | Gerencia aprobó la auditoría |
| ENVIADA_TESORERIA | Se envió a tesorería para autorización |
| APROBADA_TESORERIA | Tesorería autorizó el pago |
| COMPLETADA | El proceso se completó exitosamente |

## Próximos Pasos

1. Agregar generadores para otros módulos (Operaciones, Finanzas)
2. Implementar exportación a PDF
3. Dashboard de manuales en frontend
4. Búsqueda full-text en manuales
