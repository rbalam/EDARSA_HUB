# CIERRE Y BLINDAJE - AUDITORÍA DE COMPRAS EDARSA HUB
## Documento de Control de Cambios y Protección
## Fecha de Cierre: 2026-04-19
## Versión: 1.0.0 - CONGELADA

---

# ⚠️ ADVERTENCIA CRÍTICA

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   AUDITORÍA DE COMPRAS CERRADA Y BLINDADA                                    ║
║                                                                               ║
║   NO MODIFICAR SIN AUTORIZACIÓN EXPRESA Y CAMBIO CONTROLADO                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# I. RESUMEN EJECUTIVO

## Estado del Módulo
- **Estado**: ✅ ESTABLE, VALIDADO, CONGELADO FUNCIONALMENTE
- **Fecha de Cierre**: 2026-04-19
- **Funcionalidad Principal**: Detección y gestión de desviaciones en compras
- **Sistemas Integrados**: MPRO, SoftRestaurant, SAT/XML

---

# II. ALCANCE CERRADO

## Funcionalidades Incluidas
1. ✅ Detección automática de desviaciones de compra
2. ✅ Comparación compra vs factura
3. ✅ Comparación compra vs recepción
4. ✅ Validación de proveedores
5. ✅ Validación SAT/XML (cuando aplica)
6. ✅ Generación automática de auditorías
7. ✅ Workflows de aprobación/rechazo
8. ✅ Asignación de responsabilidades económicas
9. ✅ Estados de auditoría (pendiente, en proceso, cerrada)
10. ✅ Dashboard de KPIs de auditoría

---

# III. KPIs Y DEFINICIONES

## 3.1 Desviaciones de Compra
- **Definición**: Diferencia entre cantidad/precio pedido vs recibido/facturado
- **Umbral**: Configurable por categoría (default: 5%)
- **Acción**: Genera auditoría automática si supera umbral

## 3.2 Diferencias vs Factura
- **Definición**: Monto facturado ≠ monto de orden de compra
- **Validación**: Compara total OC vs total factura XML

## 3.3 Diferencias vs Recepción
- **Definición**: Cantidad recibida ≠ cantidad solicitada
- **Validación**: Por línea de producto

## 3.4 Auditorías Generadas
- **Estados**: PENDIENTE → EN_PROCESO → CERRADA/CANCELADA
- **Asignación**: Automática por responsable de almacén/compras

## 3.5 Responsabilidades Económicas
- **Cálculo**: Diferencia monetaria por responsable
- **Seguimiento**: Por período y acumulado

---

# IV. FUENTES DE DATOS

| Fuente | Tabla/Colección | Uso |
|--------|-----------------|-----|
| Órdenes de Compra | compras_ordenes | Base de comparación |
| Recepciones | compras_recepciones | Validación de cantidades |
| Facturas | compras_facturas | Validación de montos |
| XML SAT | facturas_xml | Validación fiscal |
| Proveedores | proveedores | Catálogo y validación |
| Auditorías | auditorias_compras | Registro de hallazgos |
| Workflows | workflows_compras | Flujos de aprobación |

---

# V. CONEXIONES

| Sistema | Tipo | Origen | Uso |
|---------|------|--------|-----|
| MongoDB | NoSQL | Local | Auditorías, workflows |
| SQL MPRO | SQL | Menú Servidores | Órdenes, recepciones |
| SoftRestaurant | SQL | Menú Servidores | Inventarios relacionados |

---

# VI. FILTROS

| Filtro | Valores | Comportamiento |
|--------|---------|----------------|
| Empresa | ID empresa | Filtra por contexto RBAC |
| Sucursal | ID sucursal | Filtra por ubicación |
| Proveedor | ID proveedor | Filtra por proveedor |
| Fecha inicio | YYYY-MM-DD | Rango de búsqueda |
| Fecha fin | YYYY-MM-DD | Rango de búsqueda |
| Estado | pendiente/proceso/cerrada | Estado de auditoría |
| Tipo | desviacion/faltante/excedente | Tipo de hallazgo |

---

# VII. REGLAS DE NEGOCIO

## 7.1 Reglas de Detección
1. Si diferencia cantidad > umbral% → genera auditoría
2. Si diferencia precio > umbral% → genera auditoría
3. Si factura no coincide con OC → genera auditoría
4. Si proveedor no validado SAT → alerta

## 7.2 Reglas de Workflow
1. Auditoría generada → notifica a responsable
2. 48h sin acción → escala a supervisor
3. Cierre requiere evidencia/justificación

## 7.3 Reglas PROHIBIDAS de Modificar
- Umbral de detección sin autorización
- Lógica de comparación OC vs Factura
- Asignación automática de responsables
- Cálculo de responsabilidad económica

---

# VIII. PARAMETRIZACIONES

| Parámetro | Valor Default | Configurable |
|-----------|---------------|--------------|
| Umbral cantidad | 5% | Sí, por categoría |
| Umbral precio | 3% | Sí, por categoría |
| Tiempo escalamiento | 48h | Sí |
| Auto-cierre inactivo | 30 días | Sí |

---

# IX. FLUJOS

```
ORDEN COMPRA → RECEPCIÓN → COMPARACIÓN AUTOMÁTICA
                               ↓
                    ¿Desviación > Umbral?
                         ↓           ↓
                        SÍ           NO
                         ↓            ↓
                 GENERA AUDITORÍA   FIN
                         ↓
              ASIGNA RESPONSABLE
                         ↓
              WORKFLOW RESOLUCIÓN
                         ↓
                 CIERRE + EVIDENCIA
```

---

# X. ARCHIVOS CRÍTICOS

| Archivo | Función | Criticidad |
|---------|---------|------------|
| `/app/backend/modules/compras/auditoria_service.py` | Lógica de auditoría | 🔴 CRÍTICO |
| `/app/backend/modules/compras/comparacion_service.py` | Comparaciones | 🔴 CRÍTICO |
| `/app/backend/modules/compras/routes.py` | Endpoints | 🟡 ALTO |
| `/app/frontend/src/pages/Compras.js` | UI auditoría | 🟡 ALTO |

---

# XI. CASOS DE PRUEBA BASE

## Prueba 1: Detección de Desviación
```
INPUT: OC con 100 unidades, Recepción con 90 unidades
ESPERADO: Auditoría generada por faltante 10%
```

## Prueba 2: Diferencia de Precio
```
INPUT: OC $1000, Factura $1100
ESPERADO: Auditoría generada por diferencia 10%
```

## Prueba 3: Workflow Completo
```
INPUT: Auditoría pendiente
ESPERADO: Notificación → Acción → Cierre con evidencia
```

---

# XII. RIESGOS CONOCIDOS

| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| XML SAT no disponible | Validación diferida | ✅ |
| Proveedor sin RFC | Alerta pero no bloquea | ✅ |
| Recepción parcial | Auditoría por diferencia | ✅ |

---

# XIII. REGLA DE NO MODIFICACIÓN

```
CUALQUIER MODIFICACIÓN REQUIERE:
1. Solicitud explícita documentada
2. Análisis de impacto
3. Snapshot previo
4. Pruebas de no regresión
5. Validación de workflows
6. Actualización documental
7. Aprobación formal

PROHIBIDO:
- Cambiar umbrales sin autorización
- Modificar lógica de comparación
- Alterar flujos de workflow
- Cambiar asignación de responsables
```

---

```
╔═══════════════════════════════════════════════════════════════╗
║  AUDITORÍA DE COMPRAS - CERRADA Y BLINDADA                   ║
║  Versión: 1.0.0 | Fecha: 2026-04-19                          ║
║  NO MODIFICAR SIN AUTORIZACIÓN                               ║
╚═══════════════════════════════════════════════════════════════╝
```
