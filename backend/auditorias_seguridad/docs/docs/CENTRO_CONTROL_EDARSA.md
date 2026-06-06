# CENTRO DE CONTROL EDARSA
## Módulo Central de Monitoreo, Estabilidad y Control Técnico

**Versión:** 2.0.0  
**Fecha:** 2026-04-19  
**Autor:** Arquitectura EDARSA HUB  
**Estado:** ACTIVO - MONITOREO CONTINUO  
**Tipo:** Control Directivo/Técnico (NO Operativo)

---

## 1. VISIÓN EJECUTIVA

### Objetivo Principal
Pasar de **REACCIONAR** a **PREVENIR**. El Centro de Control EDARSA es el módulo central que permite a Dirección y al equipo técnico ver en segundos:
- Estado general del sistema
- Salud de cada módulo
- Alertas de regresión
- Conectividad de fuentes
- Estado de jobs y automatizaciones
- Bitácora de cambios
- Métricas de estabilidad

### Problema que Resuelve
Antes del Centro de Control, los errores se detectaban cuando un usuario reportaba problemas (ej: ventas en $0). Ahora, el sistema detecta automáticamente anomalías y alerta **ANTES** de que afecten la operación.

### Alcance
Este módulo es de **control técnico/directivo**, NO operativo. No procesa transacciones de negocio, sino que monitorea la salud y estabilidad del sistema completo.

---

## 2. COMPONENTES INTEGRADOS

### 2.1 Estado General del Sistema
Vista consolidada de todos los componentes en un solo endpoint.

### 2.2 Salud por Módulo
Monitoreo individual de cada módulo crítico:
- Tablero Ejecutivo
- Auditoría de Compras
- Operaciones / Análisis
- Finanzas
- Compras
- RH

### 2.3 Alertas de Regresión
Sistema automático que detecta regresiones en módulos críticos:
- Ventas en $0 con unidades online
- Fuentes mal configuradas
- ConnectionResolver no operativo
- Servicios no disponibles

### 2.4 Conectividad de Fuentes
Estado en tiempo real de todas las fuentes de datos:
- MongoDB (EDARSA HUB)
- SQL Servers (desde menú Servidores)
- APIs locales MPRO

### 2.5 Jobs y Automatizaciones
Integración con el scheduler del sistema:
- Estado del scheduler (running/stopped)
- Lista de jobs registrados
- Próximas ejecuciones
- Historial de ejecuciones

### 2.6 Bitácora de Cambios
Registro centralizado de:
- Cambios de código (`cambio_codigo`)
- Deploys (`deploy`)
- Cambios de configuración (`config`)
- Incidentes (`incidente`)
- Hotfixes (`hotfix`)

### 2.7 Métricas de Estabilidad
Indicadores clave:
- Uptime del monitoreo
- Checks ejecutados y tasa de éxito
- Alertas generadas vs reconocidas
- Score de estabilidad (0-100)

---

## 3. API ENDPOINTS

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/centro-control/ping` | GET | Health check (sin auth) |
| `/api/centro-control/estado` | GET | Estado general consolidado |
| `/api/centro-control/salud` | GET | Reporte completo de salud |
| `/api/centro-control/salud/resumen` | GET | KPIs ejecutivos |
| `/api/centro-control/regresiones` | POST | Ejecutar checks de regresión |
| `/api/centro-control/regresiones/{modulo}` | GET | Checks de un módulo |
| `/api/centro-control/fuentes` | GET | Estado de fuentes de datos |
| `/api/centro-control/alertas` | GET | Alertas activas |
| `/api/centro-control/alertas/acknowledge` | POST | Reconocer una alerta |
| `/api/centro-control/jobs` | GET | Estado de jobs/automatizaciones |
| `/api/centro-control/bitacora` | GET | Bitácora de cambios |
| `/api/centro-control/bitacora` | POST | Registrar cambio en bitácora |
| `/api/centro-control/metricas` | GET | Métricas de estabilidad |
| `/api/centro-control/historial` | GET | Historial de eventos |
| `/api/centro-control/matriz-resolucion` | GET | Documentación de arquitectura |

---

## 4. INTERFAZ DE USUARIO

### Ubicación
- **Menú:** Sistema → Centro de Control
- **URL:** `/centro-control`

### Tabs Disponibles
1. **Vista General** - Resumen de módulos, fuentes y alertas
2. **Módulos** - Estado detallado de cada módulo
3. **Fuentes** - Lista de todas las fuentes de datos
4. **Alertas** - Gestión de alertas activas
5. **Historial** - Eventos del sistema
6. **Jobs** - Jobs y automatizaciones
7. **Bitácora** - Registro de cambios
8. **Métricas** - Indicadores de estabilidad
9. **Arquitectura** - Matriz de resolución de conexiones

---

## 5. ACCESO Y PERMISOS

### Roles Autorizados
- **Administrador** - Acceso completo
- **Supervisor** - Acceso completo
- **Director** - Acceso completo (lectura)

### Restricciones
Este módulo NO es accesible para roles operativos como Usuario o Gerente de sucursal.

### 4.2 Acciones Disponibles

#### Ejecutar Checks de Regresión
```bash
# Desde el dashboard
Botón "Ejecutar Checks"

# Via API
curl -X POST "{{API_URL}}/api/centro-control/regresiones" \
  -H "Authorization: Bearer {{TOKEN}}"
```

#### Reconocer Alerta
```bash
curl -X POST "{{API_URL}}/api/centro-control/alertas/acknowledge" \
  -H "Authorization: Bearer {{TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"alert_id": "ALRT-20260419-0001"}'
```

### 4.3 Auto-Refresh
El dashboard puede configurarse para actualización automática cada 60 segundos mediante el botón "Auto ON/OFF".

---

## 5. INTEGRACIÓN CON ARQUITECTURA

### Conexión con ConnectionResolver
El Centro de Control utiliza el `ConnectionResolver` para:
1. Validar que esté correctamente configurado
2. Documentar la matriz de resolución
3. Detectar si hay discrepancias en las fuentes

### Módulos Blindados Monitoreados
Los siguientes módulos tienen checks automáticos:
- **Tablero Ejecutivo** - Ventas, comparativos, fuentes
- **Auditoría de Compras** - (Próximo)
- **Operaciones / Análisis** - (Próximo)

---

## 6. ALERTAS AUTOMÁTICAS

### Condiciones que Generan Alerta

| Condición | Severidad | Alerta Generada |
|-----------|-----------|-----------------|
| Ventas acumuladas = $0 con unidades online | CRITICAL | "Regresión detectada: ventas_acumuladas" |
| ConnectionResolver no inicializado | CRITICAL | "Regresión detectada: conexiones_resolver" |
| Matriz de resolución incompleta | HIGH | "Regresión detectada: fuentes_correctas" |
| MongoDB no responde | CRITICAL | "Fuente caída: MongoDB" |
| SQL Server no responde | HIGH | "Fuente caída: {servidor}" |

### Flujo de Alertas
```
1. Check detecta anomalía
     ↓
2. Se crea alerta con severidad
     ↓
3. Alerta aparece en dashboard
     ↓
4. Usuario reconoce alerta
     ↓
5. Se registra en historial
```

---

## 7. MANTENIMIENTO

### Limpieza de Historial
El sistema mantiene:
- Últimos 200 eventos en memoria
- Últimas 50 alertas activas

Las alertas reconocidas más antiguas de 7 días se eliminan automáticamente.

### Logs
```bash
# Ver logs del Centro de Control
tail -f /var/log/supervisor/backend.*.log | grep "CENTRO CONTROL"
```

---

## 8. TROUBLESHOOTING

### Problema: Dashboard no carga
1. Verificar que el backend esté corriendo
2. Verificar token de autenticación
3. Revisar logs: `tail -n 100 /var/log/supervisor/backend.err.log`

### Problema: Checks de regresión fallan
1. Verificar conexión a MongoDB
2. Verificar configuración de servidores SQL
3. Revisar logs del regression_checker

### Problema: Alertas no se generan
1. Verificar que los checks se ejecuten correctamente
2. Revisar el archivo `alerts.py` para verificar condiciones

---

## 9. ROADMAP

### Fase 1 (Actual)
- [x] Health Checker básico
- [x] Regression Checker para Tablero Ejecutivo
- [x] Dashboard UI
- [x] Sistema de alertas básico

### Fase 2 (Próxima)
- [ ] Checks de regresión para Compras
- [ ] Checks de regresión para Operaciones
- [ ] Notificaciones por email/WhatsApp
- [ ] Métricas históricas

### Fase 3 (Futuro)
- [ ] Machine Learning para detección de anomalías
- [ ] Predicción de fallas
- [ ] Integración con sistemas de tickets

---

## 10. CONTACTO Y SOPORTE

Para modificaciones al Centro de Control, seguir el **PROTOCOLO GLOBAL DE CAMBIOS EDARSA**:

1. Crear Snapshot del estado actual
2. Aislar cambios en branch separado
3. Implementar cambios mínimos
4. Ejecutar pruebas de no regresión
5. Obtener autorización

**Documentación relacionada:**
- `/app/docs/PROTOCOLO_GLOBAL_CAMBIOS_EDARSA.md`
- `/app/docs/ARQUITECTURA_CONEXIONES_RESOLVER.md`
- `/app/docs/CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md`
