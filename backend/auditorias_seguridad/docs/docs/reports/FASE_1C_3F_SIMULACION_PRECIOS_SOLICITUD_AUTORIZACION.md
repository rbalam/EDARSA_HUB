# FASE 1C-3F - Simulación de Precios y Flujo de Autorización

## Resumen Ejecutivo

**Fecha**: 24 Mayo 2026
**Estado**: ✅ COMPLETADO

Se implementó el sistema de simulación de precios y flujo de solicitud/autorización de cambios de precio para el módulo Costos y Márgenes.

---

## 1. Tablas Creadas en EDARSAHUB SQL

### Comercial_SolicitudesCambioPrecio
Tabla principal de solicitudes de cambio de precio.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| SolicitudID | UNIQUEIDENTIFIER | PK |
| FolioSolicitud | VARCHAR(50) | Folio único SCP-YYYYMMDDHHMMSS-XXXX |
| ProductoID, ServerID | UNIQUEIDENTIFIER | Referencia al producto |
| PrecioActual, PrecioSolicitado | DECIMAL(18,4) | Precios |
| CostoActual | DECIMAL(18,4) | Costo al momento de solicitud |
| MargenActual*, MargenSolicitado* | DECIMAL | Márgenes calculados |
| Motivo, Justificacion | NVARCHAR | Documentación |
| Estatus | VARCHAR(20) | Estado del workflow |
| SolicitanteUsuarioID, AutorizadorUsuarioID, ModificadorUsuarioID | UNIQUEIDENTIFIER | Usuarios del flujo |
| FechaSolicitud, FechaAutorizacion, FechaAplicacion | DATETIME2 | Timestamps |

### Comercial_SolicitudesCambioPrecioHistorial
Historial de acciones para auditoría.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| HistorialID | UNIQUEIDENTIFIER | PK |
| SolicitudID | UNIQUEIDENTIFIER | FK |
| Accion | VARCHAR(50) | CREAR, ENVIAR, APROBAR, etc. |
| EstatusAnterior, EstatusNuevo | VARCHAR(20) | Transición |
| UsuarioID, UsuarioEmail | VARCHAR | Usuario que ejecutó |
| Comentario | NVARCHAR(MAX) | Notas |
| FechaAccion | DATETIME2 | Timestamp |

### Comercial_SimulacionesPrecios
Simulaciones guardadas (opcional).

---

## 2. Flujo de Estados

```
BORRADOR → SOLICITADA → EN_REVISION → APROBADA → APLICADA
                   ↘              ↘
                  CANCELADA    RECHAZADA
```

### Transiciones Válidas

| Estado Actual | Transiciones Permitidas |
|---------------|------------------------|
| BORRADOR | SOLICITADA, CANCELADA |
| SOLICITADA | EN_REVISION, CANCELADA |
| EN_REVISION | APROBADA, RECHAZADA, SOLICITADA (devolver) |
| APROBADA | APLICADA, ERROR_APLICACION, CANCELADA |
| RECHAZADA | (terminal) |
| CANCELADA | (terminal) |
| APLICADA | (terminal) |

---

## 3. Roles del Proceso

| Rol | Acciones Permitidas |
|-----|---------------------|
| **Solicitante** | Crear, Editar borrador, Enviar, Cancelar propia |
| **Autorizador** | Revisar, Aprobar, Rechazar |
| **Modificador** | Aplicar cambio autorizado |
| **Auditor** | Ver historial |

### Mapeo de Roles

| Rol Sistema | Permisos |
|-------------|----------|
| SuperAdministrador | Todos |
| Administrador | Todos |
| Gerente | Simular, Solicitar, Ver, Aprobar, Rechazar |
| Supervisor | Simular, Solicitar, Ver, Aprobar, Rechazar |
| Comercial | Simular, Solicitar, Ver |
| Usuario | Ver |

---

## 4. Endpoints Implementados

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/costos-margenes/simulacion` | Simular precio |
| POST | `/api/costos-margenes/solicitudes-precio` | Crear solicitud |
| GET | `/api/costos-margenes/solicitudes-precio` | Listar solicitudes |
| GET | `/api/costos-margenes/solicitudes-precio/{id}` | Obtener detalle |
| POST | `/api/costos-margenes/solicitudes-precio/{id}/enviar` | Enviar a revisión |
| POST | `/api/costos-margenes/solicitudes-precio/{id}/aprobar` | Aprobar |
| POST | `/api/costos-margenes/solicitudes-precio/{id}/rechazar` | Rechazar |
| POST | `/api/costos-margenes/solicitudes-precio/{id}/aplicar` | Marcar como aplicado |
| GET | `/api/costos-margenes/solicitudes-precio/{id}/historial` | Ver historial |

---

## 5. Simulación de Precios

### Request
```json
{
  "producto_id": "UUID",
  "server_id": "UUID",
  "precio_nuevo": 190.00
}
```

### Response
```json
{
  "producto_id": "...",
  "nombre_producto": "COC JESSE JAMES",
  "precio_actual": 172.22,
  "precio_simulado": 190.00,
  "margen_actual_porcentaje": 0.0,
  "margen_simulado_porcentaje": 100.0,
  "variacion_pesos": 17.78,
  "variacion_porcentaje": 10.33,
  "recomendacion": "AUMENTAR",
  "source_type": "EDARSAHUB_SQL"
}
```

### Recomendaciones
| Código | Significado |
|--------|-------------|
| MANTENER | Sin cambio |
| AUMENTAR | Mejora margen |
| REDUCIR | Reduce margen |
| REVISAR_COSTO | Variación > 15% |
| MARGEN_BAJO | < objetivo |
| MARGEN_NEGATIVO | Precio < costo |
| SIN_DATOS | Sin costo disponible |

---

## 6. Prueba del Flujo Completo

```
1. CREAR...      ✅ SCP-20260524214319-88DA
2. ENVIAR...     ✅ BORRADOR → SOLICITADA
3. APROBAR...    ✅ EN_REVISION → APROBADA
4. APLICAR...    ✅ APLICADA
5. HISTORIAL...  Total: 5 acciones
     [CREAR]   (inicio) → BORRADOR
     [ENVIAR]  BORRADOR → SOLICITADA
     [REVISAR] SOLICITADA → EN_REVISION
     [APROBAR] EN_REVISION → APROBADA
     [APLICAR] APROBADA → APLICADA
```

---

## 7. Auditoría

Cada acción registra:
- Usuario que ejecutó
- Email del usuario
- Timestamp
- Estado anterior y nuevo
- Comentarios
- IP de origen

---

## 8. Validaciones

| Validación | Estado |
|------------|--------|
| Login funciona | ✅ |
| Simulación calcula correctamente | ✅ |
| Simulación NO modifica precio oficial | ✅ |
| Solicitud se crea en BORRADOR | ✅ |
| Flujo completo funciona | ✅ |
| Historial se registra | ✅ |
| RBAC activo | ✅ |
| NO-LIVE confirmado | ✅ |
| Sin MongoDB | ✅ |

---

## 9. Archivos Creados/Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/costos_margenes/schemas_precios.py` | Nuevo - Schemas Pydantic |
| `/app/backend/modules/costos_margenes/repository_precios.py` | Nuevo - Lógica de BD |
| `/app/backend/modules/costos_margenes/routes_precios.py` | Nuevo - Endpoints |
| `/app/backend/server.py` | Modificado - Registro de router |

---

## 10. Restricciones Cumplidas

| Restricción | Estado |
|-------------|--------|
| ❌ No modifica precios oficiales | ✅ Cumplido |
| ❌ No sincroniza hacia SoftRestaurant/MPRO | ✅ Cumplido |
| ❌ No crea job nocturno | ✅ Cumplido |
| ❌ No modifica recetas | ✅ Cumplido |
| ❌ No modifica costos | ✅ Cumplido |
| ❌ No usa MongoDB | ✅ Cumplido |
| ❌ No usa conexiones live | ✅ Cumplido |

---

## 11. Nota Importante

**El endpoint `/aplicar` solo REGISTRA la aplicación en EDARSAHUB.**

La sincronización del precio hacia el sistema origen (SoftRestaurant/MPRO) se realizará en una fase posterior con diseño específico de sincronización bidireccional.

---

## 12. Recomendación

✅ FASE 1C-3F completada exitosamente.

**Próximos pasos sugeridos:**
1. Implementar Frontend para simulación y solicitudes
2. Diseñar sincronización de precios hacia origen (fase futura)
3. Configurar job nocturno (después de definir reglas y alertas)
