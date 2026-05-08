# REPORTE FINAL CORREGIDO: Carga Controlada a Staging
## EDARSA HUB - Abril 2026 (Versión Ajustada)

---

## ⚠️ AJUSTE DE CRITERIO APLICADO

**Fecha**: Abril 2026
**Cambio**: Se excluyó la fuente **MPro_HR2020** del proceso de importación por criterio oficial.

| Fuente | Estado | Motivo |
|--------|--------|--------|
| MPro_CENTRAL2020 | ✅ VÁLIDA | Fuente principal autorizada |
| Excel_Cienfuegos | ✅ VÁLIDA | Fuente complementaria de apoyo |
| MPro_HR2020 | ❌ **EXCLUIDA** | Descartada por criterio oficial |

---

## RESUMEN EJECUTIVO OFICIAL

### Totales Corregidos (Sin MPro_HR2020)

| Métrica | Cantidad |
|---------|----------|
| **Total registros válidos en staging** | **532** |
| **Candidatos a aprobación** (clasificación 'nuevo') | **466** |
| **Incompletos** (sin CURP/RFC) | **66** |
| Duplicados probables | **0** |
| Registros excluidos (MPro_HR2020) | 39 |

### Por Fuente Válida

| Fuente | Total | Con CURP | Con RFC | Candidatos | Incompletos |
|--------|-------|----------|---------|------------|-------------|
| MPro_CENTRAL2020 | 476 | 476 (100%) | 455 (96%) | **466** | 10 |
| Excel_Cienfuegos | 56 | 0 (0%) | 0 (0%) | 0 | 56 |
| **TOTAL VÁLIDO** | **532** | **476 (90%)** | **455 (86%)** | **466** | **66** |

---

## DISTRIBUCIÓN POR EMPRESA (Solo MPro_CENTRAL2020)

| Sucursal | Razón Social | Total | Listos para Aprobación |
|----------|--------------|-------|------------------------|
| 130° QUERETARO | QUEYUKA | 208 | 206 |
| ORIGEN | SIBARITAS RESTAURANTEROS | 156 | 150 |
| 130° TULUM | 130 TULUM | 40 | 39 |
| CIEN FUEGOS | DESARROLLOS AMARILLOS DE LA PENINSULA | 28 | 28 |
| XCANATUN | CERVEZA PATITO PENINSULAR | 16 | 15 |
| MECA | MECA OPERADORA RESTAURANTERA | 14 | 14 |
| GARCIA LAVIN | CERVEZA PATITO PENINSULAR | 11 | 11 |
| EDARSA | EMPRESA DE AUTOMATIZACION DE RESTAURANTES | 3 | 3 |
| **TOTAL CENTRAL2020** | | **476** | **466** |

---

## IMPACTO DE EXCLUSIÓN DE MPro_HR2020

### Registros Excluidos

| Métrica | Cantidad |
|---------|----------|
| Total registros excluidos | 39 |
| Eran duplicados de CENTRAL2020 | 29 |
| Eran únicos de HR2020 | 9 |
| Incompletos | 1 |

### Tratamiento Aplicado

- **Método**: Marcados con `Estado = 'Excluido'`
- **Trazabilidad**: Conservados en staging para auditoría
- **Filtrado**: Excluidos automáticamente en consultas con `WHERE Estado != 'Excluido'`
- **Observaciones**: Actualizadas con motivo de exclusión

### Justificación del Tratamiento

Se eligió marcar como **Excluido** en lugar de eliminar físicamente para:
1. Mantener trazabilidad histórica completa
2. Permitir auditoría futura
3. Documentar que la fuente fue procesada pero descartada por criterio
4. No perder información en caso de cambio de criterio

---

## REGLA OBLIGATORIA ESTABLECIDA

```
A partir de Abril 2026:
- MPro_HR2020 NO es fuente válida para el proceso de importación
- Solo se consideran: MPro_CENTRAL2020 (principal) + Excel (complementaria)
- Los 39 registros de HR2020 quedan excluidos del flujo de aprobación
```

---

## PRÓXIMOS PASOS AUTORIZADOS

1. **P0**: Revisión de 66 registros incompletos (Excel sin CURP/RFC)
2. **P1**: Implementar lógica de "Aprobación" para los 466 candidatos de CENTRAL2020
3. **P1**: UI para visualizar y aprobar registros en staging

---

*Reporte corregido: 2026-04-12*
*Ajuste: Exclusión de MPro_HR2020 por criterio oficial*
