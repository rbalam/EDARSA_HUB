# RESUMEN EJECUTIVO: Automatización de Análisis de Inventarios
## EDARSA HUB - CAB-003

**Fecha**: Diciembre 2025  
**Estado**: DISEÑO COMPLETO - PENDIENTE APROBACIÓN

---

## OBJETIVO EN UNA LÍNEA

Detectar automáticamente nuevos inventarios capturados y enviar análisis por almacén sin intervención manual.

---

## RESTRICCIONES CUMPLIDAS

| Restricción | Estado |
|-------------|--------|
| ❌ No crear tablas en SOFT/MPRO | ✅ Cumple - Solo EDARSA HUB |
| ❌ No modificar sistemas origen | ✅ Cumple - Solo SELECT |
| ❌ No alterar UI de Inventarios | ✅ Cumple - Módulo desacoplado |
| ❌ No romper lo existente | ✅ Cumple - Reutiliza sin modificar |
| ✅ Análisis idéntico al manual | ✅ Cumple - Misma lógica interna |
| ✅ Respetar RBAC | ✅ Cumple - Integrado |

---

## COMPONENTES NUEVOS (Todos desacoplados)

### Base de Datos EDARSA HUB (6 tablas)
1. `automatizacion_inventarios_config` - Configuración por servidor/sucursal/almacén
2. `automatizacion_inventarios_destinatarios` - Quién recibe qué
3. `automatizacion_inventarios_folios_procesados` - Control anti-duplicados
4. `automatizacion_inventarios_ejecuciones` - Bitácora de análisis
5. `automatizacion_inventarios_envios` - Registro de notificaciones
6. `automatizacion_inventarios_ultimo_folio_conocido` - Checkpoint de polling

### Backend (1 módulo nuevo)
```
/app/backend/modules/automatizacion/
├── detector.py    - Detecta nuevos folios
├── resolver.py    - Calcula inv inicial + destinatarios
├── generator.py   - Genera análisis (reutiliza existente)
├── exporter.py    - Excel/PDF (reutiliza existente)
├── notifier.py    - Email/WhatsApp
├── service.py     - Orquestador
├── scheduler.py   - Job periódico
└── routes.py      - Admin/Monitoreo
```

---

## FLUJO SIMPLIFICADO

```
Cada X minutos:
1. Detectar nuevos folios → ¿Ya procesado? → Si: saltar
2. Identificar contexto (servidor, sucursal, almacén)
3. Calcular inventario inicial según reglas
4. Generar análisis (misma lógica del menú)
5. Exportar Excel/PDF
6. Resolver destinatarios (jerarquía servidor→sucursal→almacén)
7. Enviar notificaciones
8. Registrar en bitácora
```

---

## REGLAS DE INVENTARIO INICIAL

| Sistema | Regla |
|---------|-------|
| SoftRestaurant | Primer inventario del MES ACTUAL |
| MPRO | Último inventario del MES ANTERIOR |

---

## JERARQUÍA DE DESTINATARIOS

```
SERVIDOR (recibe todo)
├── SUCURSAL (recibe de esa sucursal)
│   └── ALMACÉN (recibe solo de ese almacén)
```

Sin duplicados: Si gerencia@edarsa.com está a nivel servidor, no se repite.

---

## CANALES DE ENVÍO

| Canal | Campos | Tipos |
|-------|--------|-------|
| Email | email, tipo_envio_email | TO, CC, BCC |
| WhatsApp | telefono_whatsapp | Directo |

---

## PLAN DE IMPLEMENTACIÓN

| Fase | Duración | Entregable |
|------|----------|------------|
| 0. Preparación | 1-2 días | Tablas SQL, estructura |
| 1. Detección | 3-5 días | Detectar nuevos folios |
| 2. Generación | 3-5 días | Análisis idéntico al manual |
| 3. Notificaciones | 3-5 días | Email + WhatsApp |
| 4. Admin | 2-3 días | UI de configuración |
| 5. Piloto | 1 semana | 1 servidor de prueba |
| 6. Rollout | 2-3 semanas | Despliegue gradual |

**Total estimado**: 4-6 semanas

---

## RIESGOS PRINCIPALES

| Riesgo | Mitigación |
|--------|------------|
| Análisis diferente al manual | Tests de comparación, validación humana |
| Timeout SQL | Queries optimizadas, límites |
| Spam de emails | Control de frecuencia |
| Afectar módulo existente | 100% desacoplado, feature flag |

---

## ESTRATEGIA DE NO REGRESIÓN

1. **Aislamiento total**: Nuevo módulo en directorio separado
2. **Reutilización**: Invoca funciones existentes, NO las modifica
3. **Feature flag**: Se puede desactivar instantáneamente
4. **Tests**: Comparación byte-a-byte de Excel generado

---

## PERMISOS RBAC PROPUESTOS

| Permiso | Rol Sugerido |
|---------|--------------|
| `automatizacion.view` | Auditor |
| `automatizacion.config` | Admin Finanzas |
| `automatizacion.reprocesar` | Admin Finanzas |
| `automatizacion.admin` | SuperAdmin |

---

## DOCUMENTO COMPLETO

📄 `/app/docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_v1.md`

Contiene:
- 23 secciones detalladas
- Esquemas de tablas SQL
- Queries de detección
- Diagramas de flujo
- Plan por fases
- Matriz de riesgos

---

## SIGUIENTE PASO

**Se requiere aprobación del documento antes de proceder a implementación.**

Puntos a validar:
1. ¿El modelo de destinatarios cubre todos los casos?
2. ¿La frecuencia de polling (15 min default) es adecuada?
3. ¿Se incluye WhatsApp en Fase 1 o se posterga?
4. ¿Proveedor de email preferido (SMTP directo vs SendGrid)?

---

*Documento generado: Diciembre 2025*
