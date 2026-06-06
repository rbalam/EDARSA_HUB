# CENTRO DE CONTROL EDARSA - Endpoints y Notificaciones

## Estado: IMPLEMENTACIÓN COMPLETADA CON WEBSOCKET, EMAIL Y WHATSAPP

La pantalla React del Centro de Control EDARSA ha sido implementada completamente según el wireframe, incluyendo notificaciones multicanal.

---

## ENDPOINTS EXISTENTES (FUNCIONANDO)

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/api/centro-control/ping` | GET | ✅ OK |
| `/api/centro-control/estado` | GET | ✅ OK |
| `/api/centro-control/salud` | GET | ✅ OK |
| `/api/centro-control/salud/resumen` | GET | ✅ OK |
| `/api/centro-control/regresiones` | POST | ✅ OK |
| `/api/centro-control/regresiones/{modulo}` | GET | ✅ OK |
| `/api/centro-control/fuentes` | GET | ✅ OK |
| `/api/centro-control/alertas` | GET | ✅ OK |
| `/api/centro-control/alertas/acknowledge` | POST | ✅ OK |
| `/api/centro-control/jobs` | GET | ✅ OK |
| `/api/centro-control/bitacora` | GET | ✅ OK |
| `/api/centro-control/bitacora` | POST | ✅ OK |
| `/api/centro-control/metricas` | GET | ✅ OK |
| `/api/centro-control/historial` | GET | ✅ OK |
| `/api/centro-control/matriz-resolucion` | GET | ✅ OK |
| `/api/centro-control/ws` | WebSocket | ✅ OK |
| `/api/centro-control/ws/status` | GET | ✅ OK |
| `/api/centro-control/notificar/test` | POST | ✅ OK |
| `/api/centro-control/notificar/alerta-critica` | POST | ✅ OK |
| `/api/centro-control/email/config` | GET | ✅ OK |
| `/api/centro-control/email/test` | POST | ✅ OK |
| `/api/centro-control/email/alerta-critica` | POST | ✅ OK |
| `/api/centro-control/whatsapp/config` | GET | ✅ OK |
| `/api/centro-control/whatsapp/test` | POST | ✅ OK |
| `/api/centro-control/whatsapp/alerta-critica` | POST | ✅ OK |
| `/api/centro-control/notificaciones/config` | GET | ✅ OK |

---

## SISTEMA DE NOTIFICACIONES MULTICANAL

### Canales Disponibles
1. **WebSocket** - Notificaciones instantáneas en el dashboard
2. **Email (SMTP)** - Correos electrónicos via mail.edarsa.com.mx
3. **WhatsApp (Twilio)** - Mensajes WhatsApp via Twilio

### Flujo Automático para Alertas Críticas
Cuando se crea una alerta con `severidad: "critical"`:
1. Se envía notificación WebSocket instantánea a todos los clientes conectados
2. Se envía email a todos los destinatarios en `ALERT_EMAIL_TO`
3. Se envía WhatsApp a todos los números en `ALERT_WHATSAPP_TO`

### Configuración (.env)
```bash
# Email SMTP
EMAIL_HOST=mail.edarsa.com.mx
EMAIL_PORT=587
EMAIL_USER=notificaciones@edarsa.com.mx
EMAIL_PASSWORD=xxxxx
EMAIL_ENABLED=true
ALERT_EMAIL_TO=destinatario1@edarsa.com.mx,destinatario2@edarsa.com.mx

# WhatsApp Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886
WHATSAPP_ENABLED=true
ALERT_WHATSAPP_TO=+521234567890,+521234567891
```

### Nota sobre WhatsApp Sandbox
Para usar WhatsApp con el Sandbox de Twilio:
1. Los destinatarios deben enviar primero "join <sandbox-keyword>" al +1 (415) 523-8886
2. Para producción, se requiere WhatsApp Business API aprobado

---

## WEBSOCKET: NOTIFICACIONES EN TIEMPO REAL

### Conexión
```javascript
const ws = new WebSocket('wss://host/api/centro-control/ws');
```

### Tipos de Mensaje Recibidos
| Tipo | Descripción | Acción UI |
|------|-------------|-----------|
| `conexion_establecida` | Confirmación de conexión | Toast success |
| `heartbeat` | Ping cada 30s | Silent |
| `alerta_critica` | Alerta severidad crítica | Toast error + sonido + cambio a tab alertas |
| `alerta_nueva` | Nueva alerta cualquier severidad | Toast warning |
| `estado_cambio` | Cambio estado del sistema | Refresh datos |
| `fuente_caida` | Fuente de datos caída | Toast error |

### Indicador Visual
- Badge "Live" verde cuando conectado
- Badge "Reconectando..." amarillo durante reconexión
- Badge "Offline" rojo cuando desconectado con botón de reconexión

---

## DATOS MOCK TEMPORALES EN FRONTEND

### 1. Módulos Blindados (línea ~460)
```javascript
const modulosBlindados = [
  { id: 'tablero_ejecutivo', nombre: 'Tablero Ejecutivo', fecha_cierre: '2026-04-19', documento: 'CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md' },
  { id: 'auditoria_compras', nombre: 'Auditoría de Compras', fecha_cierre: '2026-04-19', documento: 'CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md' },
  { id: 'operaciones_analisis', nombre: 'Operaciones / Análisis', fecha_cierre: '2026-04-19', documento: 'CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md' }
];
```

**Endpoint sugerido:** `GET /api/centro-control/blindaje/modulos`

---

## ENDPOINTS OPCIONALES PARA FUTURO

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/api/centro-control/blindaje/modulos` | GET | Lista de módulos blindados |
| `/api/centro-control/blindaje/protocolo` | GET | Protocolo global de cambios |
| `/api/centro-control/cambios` | GET | Historial de cambios/deploys |
| `/api/centro-control/modulos/{id}/checks` | GET | Checks específicos de un módulo |

---

## ARCHIVOS DE REFERENCIA

- `/app/frontend/src/pages/CentroControl.jsx` - UI ejecutiva (960+ líneas)
- `/app/backend/core/centro_control/routes.py` - API endpoints
- `/app/backend/core/centro_control/email_notifications.py` - Servicio email
- `/app/backend/core/centro_control/whatsapp_notifications.py` - Servicio WhatsApp
- `/app/backend/core/centro_control/websocket.py` - WebSocket manager
