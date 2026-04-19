# EDARSA HUB - Product Requirements Document

## Visión General
Sistema ERP operativo centralizado para EDARSA, actuando como "el cerebro" de operaciones de compras, inventarios, auditorías y flujos de aprobación.

## Estado Actual: FASE 2D - Automatizaciones Operativas de Compras (COMPLETO)

### Implementado
- [x] RBAC Avanzado con control granular de permisos
- [x] Auditorías Programadas (Scheduler completo)
- [x] UI reorganizada: "Automatizaciones" con Tabs (Programadas, Operativas, Historial)
- [x] Notificaciones: Twilio WhatsApp + Neubox SMTP Email
- [x] **Automatización Operativa de Compras - FASE 1**:
  - Detección automática de pedidos
  - Cálculo ventana 15 días
  - Búsqueda inventario inicial más cercano
  - Validación inventario final (PENDIENTE_INVENTARIO_FISICO si no existe)
  - Cálculo auditoría (consumo, días inventario, estado, recomendación)
  - Flujo autorización: EN_REVISION_GERENCIA → PENDIENTE_TESORERIA → APROBADO/RECHAZADO
  - Endpoints Gerencia/Tesorería con acciones por rol
  - UI completa con acciones diferenciadas por rol
  - Bitácora de cambios

### Estados del Flujo (EXACTOS)
1. PEDIDO_DETECTADO
2. PENDIENTE_INVENTARIO_FISICO (sin inv. final → detiene flujo, notifica)
3. AUDITORIA_EN_PROCESO
4. EN_REVISION_GERENCIA
5. PENDIENTE_TESORERIA
6. APROBADO / RECHAZADO

### Lógica de Cálculo
- `dias_inventario = existencia_fisica / consumo_promedio`
- Estados: CRITICO (≤0), FALTANTE (<objetivo), OPTIMO (±20%), SOBRANTE (>objetivo)
- Recomendaciones: URGENTE, COMPRAR, NO_COMPRAR, REVISAR
- `pedido_optimo = (dias_objetivo * consumo) - existencia_fisica`

### Endpoints Implementados
- `POST /api/v2/automatizaciones/operativas/compras/procesar`
- `GET /api/v2/automatizaciones/operativas/compras`
- `GET /api/v2/automatizaciones/operativas/compras/{id}`
- `GET /api/v2/automatizaciones/operativas/compras/kpis`
- `POST /api/v2/automatizaciones/operativas/compras/{id}/gerencia` (aprobar/rechazar/ajuste)
- `POST /api/v2/automatizaciones/operativas/compras/{id}/tesoreria` (aprobar/rechazar)
- `POST /api/v2/automatizaciones/operativas/compras/{id}/dias-objetivo`
- `GET /api/v2/automatizaciones/operativas/compras/{id}/bitacora`

## Bloqueado
- **SQL Server Local (ORIGEN/130QRO)**: Timeout en conexiones locales. Documento diagnóstico creado: `DIAGNOSTICO_SQL_SUCURSALES.docx`. Requiere resolución por equipo de infraestructura local.

## Backlog P0 (Próximo)
- Trigger automático desde módulo Compras al capturar pedido en MPro
- Integración real con nómina/ERP (bloqueado por SQL Server local)

## Backlog P1
- Reportes financieros avanzados
- Meta Cloud API para WhatsApp (migración de Twilio)
- Panel administración RBAC en frontend
- Alertas en tiempo real por fallo de job

## Principio Arquitectónico
**EDARSA HUB = EL CEREBRO**
- Toda lógica vive en EDARSA HUB
- Toda tabla, cache, bitácora se crea en EDARSA HUB / MongoDB
- MPro y Soft solo son fuentes de datos (lectura)
- No delegar inteligencia a sistemas externos

## Arquitectura de Archivos Clave
```
/app/backend/
├── modules/
│   └── fase2_operativo/
│       ├── services/
│       │   └── automatizacion_compras_service.py  # Lógica principal
│       └── routes/
│           └── automatizacion_compras_routes.py   # Endpoints API
├── core/
│   └── communications/
│       └── providers/
│           ├── email_smtp_provider.py   # Neubox SMTP
│           └── whatsapp_provider.py     # Twilio
/app/frontend/
└── src/
    └── components/
        └── TabOperativasCompras.jsx     # UI Operativas
```

## Colecciones MongoDB
- `automatizaciones_operativas_compras`: Registro principal de automatizaciones
- `automatizaciones_bitacora`: Log de eventos y cambios
- `pedidos_procesados_automatizacion`: Control de pedidos ya procesados
- `inventarios_fisicos_procesados`: Cache de inventarios físicos

---
*Última actualización: 19/04/2026*
