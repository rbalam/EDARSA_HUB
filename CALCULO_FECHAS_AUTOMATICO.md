# Cálculo Automático de Fechas de Consumo

## Descripción General

El sistema calcula automáticamente las fechas para el análisis de ventas y movimientos basándose en las fechas de los inventarios físicos seleccionados. La lógica varía según el tipo de sistema (MPRO o SoftRestaurant).

## Lógica por Tipo de Sistema

### ManagementPro (MPRO)

**Método:** Fechas exactas de inventarios

```
Fecha Inicio de Ventas = Fecha del Inventario Inicial
Fecha Fin de Ventas = Fecha del Inventario Final
```

**Ejemplo:**
```
Inventario Inicial: Folio SB-0000992 - 28/02/2026 14:30:00
Inventario Final: Folio SB-0000996 - 08/03/2026 16:45:00

Resultado:
Fecha Inicio de Ventas: 2026-02-28
Fecha Fin de Ventas: 2026-03-08
```

**Razón:** En MPRO, las ventas del período deben incluir completamente las fechas de los inventarios.

---

### SoftRestaurant

**Método:** Ajuste de ±1 segundo

```
Fecha Inicio de Ventas = Fecha del Inventario Inicial + 1 segundo
Fecha Fin de Ventas = Fecha del Inventario Final - 1 segundo
```

**Ejemplo:**
```
Inventario Inicial: Folio SB-0000992 - 28/02/2026 14:30:00
Inventario Final: Folio SB-0000996 - 08/03/2026 16:45:00

Resultado:
Fecha Inicio de Ventas: 2026-02-28 14:30:01
Fecha Fin de Ventas: 2026-03-08 16:44:59
```

**Razón:** En SoftRestaurant, se necesita excluir las ventas exactas del momento del inventario para evitar duplicaciones.

---

## Comportamiento en la Interfaz

### Campos Auto-Calculados

Los campos "Fecha Inicio de Ventas" y "Fecha Fin de Ventas" son **de solo lectura** y se calculan automáticamente cuando:

1. Seleccionas el **Inventario Inicial**
2. Seleccionas el **Inventario Final**

Los campos muestran un placeholder: *"Auto-calculado al seleccionar inventarios"*

### Indicadores Visuales

Junto a cada campo de fecha, aparece un texto explicativo:

- **MPRO:** *(Fecha inv. inicial)* / *(Fecha inv. final)*
- **SoftRestaurant:** *(Fecha inv. inicial + 1 seg)* / *(Fecha inv. final - 1 seg)*

### Proceso de Selección

```
1. Servidor → Se determina el tipo de sistema
2. Sucursal → Se filtran almacenes
3. Almacén → Se cargan inventarios disponibles
4. Inventario Inicial → Se guarda la fecha
5. Inventario Final → Se guarda la fecha y se calculan las fechas de ventas
```

---

## Configuración de Servidores

### Al Agregar un Servidor

Cuando agregas un nuevo servidor, verás una nota informativa:

```
┌─────────────────────────────────────────────────────┐
│ Cálculo automático de fechas de consumo:            │
│ • MPRO: Usa fechas exactas de inventarios inicial   │
│   y final                                            │
│ • SoftRestaurant: Fecha inicial +1 seg, fecha final │
│   -1 seg                                             │
└─────────────────────────────────────────────────────┘
```

### En la Tarjeta del Servidor

Cada servidor muestra su método de cálculo:

**MPRO:**
```
Cálculo de fechas:
📅 Fechas exactas de inventarios
```

**SoftRestaurant:**
```
Cálculo de fechas:
⏱️ Fecha inv. ±1 segundo
```

---

## Flujo Completo de Uso

### Paso 1: Configurar Servidor
```
1. Ve a "Servidores"
2. Agrega un servidor
3. Selecciona el tipo de sistema (MPRO o SoftRestaurant)
4. El método de cálculo se guarda automáticamente
```

### Paso 2: Generar Reporte
```
1. Ve a "Reportes"
2. Selecciona "Análisis Completo de Inventario"
3. Elige el Servidor
4. Elige Sucursal y Almacén
5. Selecciona Inventario Inicial
6. Selecciona Inventario Final
7. Las fechas se calculan automáticamente ✓
8. Genera el reporte
```

---

## Casos de Uso

### Caso 1: Análisis Semanal (MPRO)

**Escenario:**
- Sistema: ManagementPro
- Período: Del lunes al domingo
- Inventario capturado lunes 6:00 AM y domingo 11:59 PM

**Configuración:**
```
Inventario Inicial: Lunes 01/01/2026 06:00:00
Inventario Final: Domingo 07/01/2026 23:59:00

Fechas calculadas:
Fecha Inicio: 2026-01-01 (incluye ventas desde las 6 AM)
Fecha Fin: 2026-01-07 (incluye ventas hasta las 11:59 PM)
```

**Resultado:** Incluye todas las ventas del período completo.

---

### Caso 2: Análisis Mensual (SoftRestaurant)

**Escenario:**
- Sistema: SoftRestaurant
- Período: Mes completo
- Inventario capturado el último día del mes anterior y último día del mes actual

**Configuración:**
```
Inventario Inicial: 31/12/2025 23:59:00
Inventario Final: 31/01/2026 23:59:00

Fechas calculadas:
Fecha Inicio: 2025-12-31 23:59:01 (excluye ventas de diciembre)
Fecha Fin: 2026-01-31 23:58:59 (excluye ventas del momento final)
```

**Resultado:** Solo incluye ventas de enero, sin traslapes.

---

## Validaciones del Sistema

El sistema valida que:

1. ✓ Se haya seleccionado un servidor
2. ✓ Se haya seleccionado una sucursal
3. ✓ Se haya seleccionado un almacén
4. ✓ Se haya seleccionado inventario inicial
5. ✓ Se haya seleccionado inventario final
6. ✓ Las fechas se hayan calculado correctamente

Si falta algún dato, se muestra un mensaje de error específico.

---

## Ventajas de este Método

### 1. Consistencia
- Elimina errores humanos al ingresar fechas manualmente
- Garantiza que las fechas correspondan exactamente a los inventarios

### 2. Precisión
- Respeta las diferencias entre sistemas
- Evita duplicaciones o omisiones de ventas

### 3. Facilidad de Uso
- El usuario solo selecciona inventarios
- No necesita calcular o recordar reglas de fechas

### 4. Auditable
- Queda registro de qué inventarios se usaron
- Las fechas son reproducibles

---

## Preguntas Frecuentes

### ¿Puedo cambiar las fechas manualmente?

No, las fechas son calculadas automáticamente y son de solo lectura. Esto garantiza la precisión del análisis.

### ¿Qué pasa si selecciono inventarios en orden inverso?

El sistema no valida el orden. Es responsabilidad del usuario seleccionar el inventario más antiguo como "inicial" y el más reciente como "final".

### ¿Funciona con otros sistemas además de MPRO y SoftRestaurant?

Actualmente solo soporta MPRO y SoftRestaurant. Para otros sistemas, se usa el método de MPRO por defecto.

### ¿Qué pasa si cambio de servidor después de seleccionar inventarios?

Los campos se reinician y debes volver a seleccionar sucursal, almacén e inventarios.

---

## Troubleshooting

### Problema: Las fechas no se calculan

**Solución:**
1. Verifica que hayas seleccionado ambos inventarios
2. Revisa que los inventarios tengan fechas válidas
3. Confirma que el servidor esté configurado correctamente

### Problema: Las fechas parecen incorrectas

**Solución:**
1. Verifica el tipo de sistema del servidor
2. Confirma que los inventarios seleccionados sean los correctos
3. Revisa el formato de fecha en la base de datos SQL

---

## Soporte Técnico

Para problemas relacionados con el cálculo de fechas:

1. Verifica los logs del backend
2. Confirma que la consulta SQL devuelva fechas con hora
3. Valida que el servidor tenga el `system_type` correcto en MongoDB

---

## Actualización Futura

### Próximas Mejoras

- [ ] Soporte para sistemas adicionales
- [ ] Configuración personalizada de ajuste de segundos
- [ ] Validación de orden de inventarios
- [ ] Previsualización del período de análisis
- [ ] Alertas si el período es muy largo o muy corto
