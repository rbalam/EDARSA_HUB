# Control de Créditos del Proyecto - Edarsa Hub

## Resumen Actual
| Métrica | Valor |
|---------|-------|
| **Saldo Actual** | $3,479.31 |
| **Última Actualización** | 2026-03-27 (sesión actual) |

---

## Historial de Consumo (Esta Sesión)

| Fecha | Concepto | Créditos | Saldo Restante |
|-------|----------|----------|----------------|
| 2026-03-27 | Saldo Inicial Reportado | - | $3,479.31 |
| 2026-03-27 | Drill-down KPIs Comercial + División MPRO | ~5.00 | $3,474.31 |
| 2026-03-27 | Buscador Global Explorador BD | ~3.00 | $3,471.31 |
| 2026-03-27 | Reorganización Sidebar (SQL a Sistema) | ~0.50 | $3,470.81 |
| 2026-03-27 | Fix bug Inventarios (columna observaciones) | ~1.00 | $3,469.81 |
| 2026-03-27 | Fix bug Compras (selectedSucursal) | ~0.50 | $3,469.31 |

---

## REGLA OBLIGATORIA (Agente Rich)

**ANTES de cualquier cambio significativo:**
1. Preguntar saldo actual al usuario
2. Estimar costo de la tarea (usar históricos)
3. Esperar "LUZ VERDE" explícita para tareas > $5
4. Usar SUMAS y RESTAS simples (SIN IA para cálculos)
5. Reutilizar consultas SQL existentes cuando sea posible

---

## Estimaciones de Referencia

| Tipo de Tarea | Créditos Estimados |
|---------------|-------------------|
| Fix bug simple (1 archivo) | $0.50 - $1.00 |
| Fix bug medio (2-3 archivos) | $1.00 - $3.00 |
| Feature pequeña (UI only) | $2.00 - $5.00 |
| Feature mediana (Frontend + Backend) | $5.00 - $15.00 |
| Feature grande (Módulo completo) | $20.00 - $40.00 |
| Consulta SQL nueva | $0.50 - $2.00 |
| Reutilizar consulta existente | $0.00 |

---

## Tareas Pendientes (Con Estimación)

| Tarea | Créditos Est. | Prioridad |
|-------|---------------|-----------|
| Presupuestos (CRUD MongoDB) | $8.00 - $12.00 | P1 |
| Ventas sin inflación (% parametrizable) | $3.00 - $5.00 | P1 |
| Filtros grupo/zona/permisos | $5.00 - $8.00 | P1 |
| Exportación PDF | $5.00 - $8.00 | P2 |
| Módulo Rentabilidad (OpenTable) | $15.00 - $25.00 | P2 |

---

## Notas
- Los créditos son aproximados basados en complejidad de código
- Tareas que reutilizan código existente cuestan menos
- Bugfixes simples son los más económicos
