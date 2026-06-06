# MATRIZ DE ROLES Y PERMISOS - EDARSA HUB v2
## Módulo Finanzas - Análisis Detallado
**Fecha:** Diciembre 2025  
**Estado:** PROPUESTA - Pendiente Aprobación  
**Autor:** Agente E1

---

## 1. PERFILES DEFINIDOS

| Perfil | Código | Descripción | Alcance Default |
|--------|--------|-------------|-----------------|
| **SuperAdmin** | `SUPERADMIN` | Control total del sistema, configuración global | GLOBAL |
| **Administrador Finanzas** | `ADMIN_FIN` | Gestión completa del módulo Finanzas | GLOBAL |
| **Tesorero** | `TESORERO` | Operaciones de caja, cuadres, depósitos | GLOBAL |
| **Cuentas por Pagar** | `CXP` | Gestión de facturas y pagos a proveedores | GLOBAL |
| **Auditor** | `AUDITOR` | Solo consulta, sin modificaciones | GLOBAL |
| **Operador de Sucursal** | `OP_SUC` | Operaciones limitadas a su sucursal asignada | SUCURSAL |

---

## 2. TIPOS DE PERMISO

| Tipo | Código | Descripción |
|------|--------|-------------|
| **Ver** | `VIEW` | Consultar información, listar, filtrar |
| **Editar** | `EDIT` | Modificar registros existentes |
| **Confirmar** | `CONFIRM` | Validar/guardar operaciones propias |
| **Autorizar** | `AUTHORIZE` | Aprobar operaciones de otros o acciones críticas |

---

## 3. MATRIZ DETALLADA POR MÓDULO

### 3.1 PROPINAS TPV

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| Propinas TPV | Ver tab Propinas | `PROPINAS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo - Solo visualización |
| Propinas TPV | Ver listado cuadre | `PROPINAS_CUADRE_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo - Información operativa |
| Propinas TPV | Filtrar por fecha/estado | `PROPINAS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo |
| Propinas TPV | Ver configuración % | `PROPINAS_CONFIG_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Bajo - Solo lectura |
| Propinas TPV | Editar % descuento | `PROPINAS_CONFIG_EDIT` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **ALTO** - Afecta cálculo de comisiones de todo el personal |
| Propinas TPV | Crear nueva config % | `PROPINAS_CONFIG_EDIT` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **ALTO** - Puede crear reglas por sucursal/empresa |
| Propinas TPV | Activar/desactivar config | `PROPINAS_CONFIG_AUTHORIZE` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **ALTO** - Cambia regla activa |
| Propinas TPV | Registrar pago propinas | `PROPINAS_PAGO_CONFIRM` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **MEDIO** - Afecta flujo de efectivo |
| Propinas TPV | Sincronizar desde origen | `PROPINAS_SYNC` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | Medio - Actualiza datos maestros |

**Nota:** `✅*` = Acceso limitado a registros de su sucursal asignada

---

### 3.2 TESORERÍA / CUADRE Z

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| Tesorería | Ver tab Tesorería | `TESORERIA_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo - Solo visualización |
| Tesorería | Ver cortes pendientes | `TESORERIA_CORTES_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo - Información operativa |
| Tesorería | Ver cuadres registrados | `TESORERIA_CUADRES_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo |
| Tesorería | Filtrar por fecha/sucursal | `TESORERIA_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo |
| Tesorería | Iniciar cuadre (abrir modal) | `TESORERIA_CUADRE_EDIT` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅* | Global/Sucursal | Medio - Inicia proceso de validación |
| Tesorería | Capturar conteo efectivo | `TESORERIA_CUADRE_EDIT` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅* | Global/Sucursal | Medio - Datos sensibles de arqueo |
| Tesorería | Capturar ficha depósito | `TESORERIA_CUADRE_EDIT` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅* | Global/Sucursal | Medio - Referencia bancaria |
| Tesorería | Guardar cuadre | `TESORERIA_CUADRE_CONFIRM` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **ALTO** - Confirma conciliación oficial |
| Tesorería | Ajustar cuadre existente | `TESORERIA_CUADRE_EDIT` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **ALTO** - Modifica registro validado |
| Tesorería | Autorizar cuadre con descuadre | `TESORERIA_CUADRE_AUTHORIZE` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **CRÍTICO** - Acepta diferencias de caja |
| Tesorería | Reabrir cuadre cerrado | `TESORERIA_CUADRE_AUTHORIZE` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Global | **CRÍTICO** - Rompe integridad del cierre |
| Tesorería | Ver resumen general | `TESORERIA_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Bajo |

**Notas:**
- `✅*` = Solo cortes/cuadres de su sucursal asignada
- Operador de Sucursal puede INICIAR y CAPTURAR pero NO puede GUARDAR el cuadre final (requiere Tesorero)
- Descuadres mayores a tolerancia requieren AUTORIZACIÓN de Admin Finanzas

---

### 3.3 CUENTAS POR PAGAR (CxP)

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| CxP | Ver tab CxP | `CXP_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | Global/Sucursal | Bajo - Solo visualización |
| CxP | Ver listado facturas | `CXP_FACTURAS_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | Global/Sucursal | Bajo |
| CxP | Filtrar por proveedor/fecha | `CXP_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | Global/Sucursal | Bajo |
| CxP | Buscar por nombre/RFC/clave | `CXP_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅* | Global/Sucursal | Bajo |
| CxP | Ver resumen antigüedad | `CXP_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Bajo |
| CxP | Exportar CSV | `CXP_EXPORT` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Medio - Datos sensibles de proveedores |
| CxP | Marcar factura para pago | `CXP_PAGO_EDIT` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | Global | **MEDIO** - Propone salida de efectivo |
| CxP | Desmarcar factura | `CXP_PAGO_EDIT` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | Global | Medio - Modifica propuesta de pago |
| CxP | Pago masivo (todas vencidas) | `CXP_PAGO_MASIVO` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | Global | **ALTO** - Compromete flujo de caja masivamente |
| CxP | Autorizar pago | `CXP_PAGO_AUTHORIZE` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **CRÍTICO** - Libera fondos reales |
| CxP | Confirmar pago ejecutado | `CXP_PAGO_CONFIRM` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **ALTO** - Cierra ciclo de pago |
| CxP | Ver estado de cuenta proveedor | `CXP_ESTADO_CUENTA_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Bajo - Futuro módulo |

**Notas:**
- `✅*` = Solo facturas de proveedores que surten a su sucursal
- Marcar ≠ Autorizar ≠ Confirmar (separación de responsabilidades)
- Pago masivo requiere perfil CxP o superior (no Tesorero)

---

### 3.4 CONTROL DE INGRESOS

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| Ingresos | Ver tab Control Ingresos | `INGRESOS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo |
| Ingresos | Ver cortes de caja | `INGRESOS_CORTES_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅* | Global/Sucursal | Bajo |
| Ingresos | Ver saldos por depositar | `INGRESOS_SALDOS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Medio - Info sensible de caja |
| Ingresos | Marcar depósito efectivo | `INGRESOS_DEPOSITO_CONFIRM` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **ALTO** - Confirma entrada bancaria |
| Ingresos | Marcar depósito tarjetas | `INGRESOS_DEPOSITO_CONFIRM` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Global | **ALTO** - Confirma dispersión NetPay |
| Ingresos | Ver configuración comisiones | `INGRESOS_CONFIG_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Bajo |

---

### 3.5 PRESUPUESTOS

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| Presupuestos | Ver tab Presupuestos | `PRESUPUESTOS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Bajo |
| Presupuestos | Ver listado presupuestos | `PRESUPUESTOS_VIEW` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global | Bajo |
| Presupuestos | Crear presupuesto | `PRESUPUESTOS_EDIT` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **ALTO** - Define metas financieras |
| Presupuestos | Editar presupuesto | `PRESUPUESTOS_EDIT` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global | **ALTO** |
| Presupuestos | Eliminar presupuesto | `PRESUPUESTOS_DELETE` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Global | **CRÍTICO** - Pérdida de histórico |

---

### 3.6 DASHBOARD FINANZAS

| Módulo | Acción | Permiso Requerido | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Sucursal | Alcance | Riesgo si NO se controla |
|--------|--------|-------------------|:----------:|:---------:|:--------:|:---:|:-------:|:------------:|---------|--------------------------|
| Dashboard | Ver tab Dashboard | `FINANZAS_DASHBOARD_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Bajo - KPIs consolidados |
| Dashboard | Filtrar por periodo | `FINANZAS_DASHBOARD_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Bajo |
| Dashboard | Ver alertas sobregiro | `FINANZAS_ALERTAS_VIEW` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global | Bajo |

---

## 4. RESUMEN DE PERMISOS POR PERFIL

### SuperAdmin
- Acceso total a todos los módulos y acciones
- Único que puede: reabrir cuadres cerrados, eliminar presupuestos

### Administrador Finanzas
- Gestión completa del módulo Finanzas
- Puede autorizar: cuadres con descuadre, pagos CxP
- Puede editar: configuración de propinas, presupuestos

### Tesorero
- Operaciones de caja y conciliación
- Puede: guardar cuadres, confirmar depósitos, marcar pagos individuales
- NO puede: autorizar pagos CxP, editar config propinas, pago masivo

### Cuentas por Pagar
- Gestión especializada de facturas y proveedores
- Puede: marcar pagos, pago masivo, exportar
- NO puede: cuadres, depósitos, configuraciones

### Auditor
- Solo lectura en todos los módulos
- NO puede: modificar, confirmar ni autorizar nada
- Acceso global para revisión

### Operador de Sucursal
- Acceso limitado a SU sucursal asignada
- Puede ver: cortes, cuadres, facturas de su sucursal
- Puede iniciar: cuadres (pero NO guardar solo)
- NO puede: acciones globales, configuraciones, autorizaciones

---

## 5. MATRIZ DE RIESGOS

| Nivel | Acciones | Consecuencia sin control |
|-------|----------|--------------------------|
| **CRÍTICO** | Autorizar cuadre con descuadre, Reabrir cuadre, Autorizar pago CxP, Eliminar presupuesto | Pérdida financiera directa, fraude, integridad comprometida |
| **ALTO** | Guardar cuadre, Pago masivo, Editar % propinas, Confirmar pago, Crear presupuesto | Errores en flujo de caja, cálculos incorrectos de nómina |
| **MEDIO** | Marcar pago individual, Registrar pago propinas, Exportar CSV, Iniciar cuadre | Propuestas erróneas, fuga de información |
| **BAJO** | Ver tabs, filtrar, consultar | Exposición de información (controlado por alcance sucursal) |

---

## 6. REGLAS DE NEGOCIO ADICIONALES

1. **Separación de funciones**: Quien marca pago ≠ quien autoriza ≠ quien confirma
2. **Alcance por sucursal**: Operador solo ve/opera sobre su sucursal asignada
3. **Tolerancia de descuadre**: Si diferencia > $50 MXN → requiere `AUTHORIZE`
4. **Auditoría**: Toda acción EDIT/CONFIRM/AUTHORIZE debe registrar usuario, fecha, IP
5. **Escalamiento**: Operador puede INICIAR cuadre pero Tesorero debe GUARDAR

---

## 7. IMPLEMENTACIÓN SUGERIDA

### Backend
```python
# Decorador de permisos
@require_permission("CXP_PAGO_AUTHORIZE")
async def autorizar_pago(factura_id: str, current_user: dict):
    ...

# Filtro por alcance
@filter_by_scope("sucursal")  # Aplica automáticamente si perfil es OP_SUC
async def listar_facturas(current_user: dict):
    ...
```

### Frontend
```javascript
// Ocultar botón si no tiene permiso
{hasPermission('CXP_PAGO_AUTHORIZE') && (
  <Button onClick={autorizarPago}>Autorizar Pago</Button>
)}

// Filtrar tabs visibles
const tabsVisibles = tabs.filter(t => hasPermission(t.permiso));
```

---

## 8. PENDIENTE APROBACIÓN

- [ ] Perfiles definidos correctamente
- [ ] Matriz de permisos por acción
- [ ] Alcances (global vs sucursal)
- [ ] Niveles de riesgo
- [ ] Reglas de negocio adicionales

**Siguiente paso:** Aprobación del usuario antes de implementar.
