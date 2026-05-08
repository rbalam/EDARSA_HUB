# PROTOCOLO GLOBAL DE CAMBIOS - EDARSA HUB
## Gobernanza Técnica y Control de Regresiones
## Versión: 1.0.0
## Fecha: 2026-04-19

---

# ⚠️ REGLA PRINCIPAL

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   "LO QUE YA FUNCIONA, NO SE ROMPE"                                          ║
║                                                                               ║
║   Todo cambio en EDARSA HUB debe ser:                                        ║
║   - Controlado                                                                ║
║   - Acotado                                                                   ║
║   - Probado                                                                   ║
║   - Documentado                                                               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# I. ALCANCE

Este protocolo es **OBLIGATORIO** para:
- Tablero Ejecutivo
- Auditoría de Compras
- Operaciones / Análisis
- Finanzas
- Compras
- RH
- Inventarios
- Comercial
- Cualquier módulo presente o futuro

---

# II. TIPOS DE CAMBIO PERMITIDOS

## 2.1 Cambio Controlado
- Solicitado explícitamente
- Con alcance definido
- Con módulo específico
- Con pruebas obligatorias

## 2.2 Hotfix
- Solo para errores críticos
- Con impacto acotado
- Con validación inmediata

## 2.3 Nueva Funcionalidad
- Sin afectar lógica existente
- Sin romper contratos actuales

## ❌ PROHIBIDO
- Cambios colaterales
- Cambios "de pasada"
- Refactors no solicitados
- Mover lógica funcional sin autorización

---

# III. PROTOCOLO OBLIGATORIO DE CAMBIO

## PASO 1: DEFINICIÓN DE ALCANCE

Antes de tocar código, definir:
- [ ] Módulo afectado
- [ ] KPIs o funciones afectadas
- [ ] Archivos involucrados
- [ ] Impacto esperado
- [ ] Módulos que NO deben afectarse

## PASO 2: SNAPSHOT OBLIGATORIO

Antes de modificar:
- [ ] Crear snapshot de archivos
- [ ] Registrar rutas
- [ ] Registrar estado actual

**SIN SNAPSHOT → NO SE PERMITE AVANZAR**

## PASO 3: AISLAMIENTO DEL CAMBIO

- [ ] Afectar SOLO lo necesario
- [ ] NO tocar lógica compartida sin análisis
- [ ] NO modificar helpers globales sin revisión

Si hay dependencia compartida → dividir lógica, NO modificar global.

## PASO 4: IMPLEMENTACIÓN

- [ ] Cambios mínimos
- [ ] Sin refactor decorativo
- [ ] Sin optimizaciones no solicitadas
- [ ] Respetar arquitectura existente

## PASO 5: PRUEBAS DE NO REGRESIÓN

### A) Módulo afectado
- [ ] Funciona correctamente

### B) Módulos críticos (siempre validar)
- [ ] Tablero Ejecutivo
- [ ] Auditoría Compras
- [ ] Operaciones / Análisis

### C) Validaciones mínimas
- [ ] Consolidado general
- [ ] Por unidad
- [ ] Por fechas
- [ ] Fuentes correctas
- [ ] Sin ceros falsos

### D) Si aplica
- [ ] Ventas del día
- [ ] Ventas acumuladas
- [ ] Comparativos
- [ ] Workflows
- [ ] Auditorías

**SI ALGO SE ROMPE → ROLLBACK INMEDIATO**

## PASO 6: VALIDACIÓN FUNCIONAL

- [ ] Resultados correctos
- [ ] Lógica intacta
- [ ] Sin alteraciones indirectas

## PASO 7: DOCUMENTACIÓN

- [ ] Qué se cambió
- [ ] Por qué se cambió
- [ ] Qué no se tocó
- [ ] Impacto
- [ ] Pruebas realizadas

Ubicación: `/app/docs/` o `/app/memory/`

## PASO 8: CIERRE

- [ ] Cambio completado
- [ ] Módulos validados
- [ ] No regresión confirmada

---

# IV. MÓDULOS BLINDADOS

Los siguientes módulos tienen **PROTECCIÓN ESPECIAL**:

| Módulo | Documento de Blindaje |
|--------|----------------------|
| Tablero Ejecutivo | `CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md` |
| Auditoría Compras | `CIERRE_Y_BLINDAJE_AUDITORIA_COMPRAS.md` |
| Operaciones/Análisis | `CIERRE_Y_BLINDAJE_OPERACIONES_ANALISIS.md` |

### Para módulos blindados:

**PROHIBIDO:**
- Modificar lógica sin instrucción directa
- Cambiar fuentes
- Cambiar conexiones
- Cambiar KPIs
- Cambiar filtros
- Cambiar reglas de negocio

**CUALQUIER cambio requiere:**
- Autorización explícita
- Pruebas completas
- Documentación previa y posterior

---

# V. CHECKLIST DE RIESGO

## Semáforo de Riesgo

| Tipo de Cambio | Riesgo | Protocolo |
|----------------|--------|-----------|
| UI cosmético | 🟢 BAJO | Prueba visual |
| Nuevo endpoint independiente | 🟢 BAJO | Prueba funcional |
| Modificar filtros | 🟡 MEDIO | Validar módulo |
| Modificar queries | 🔴 ALTO | Protocolo completo |
| Modificar conexiones | 🔴 ALTO | Protocolo completo |
| Modificar fuentes | 🔴 ALTO | Protocolo completo |
| Modificar KPIs | 🔴 CRÍTICO | Autorización + Protocolo |
| Tocar módulo blindado | 🔴 CRÍTICO | Autorización + Protocolo |

---

# VI. REGLAS DE FUENTES DE DATOS

1. NO mezclar fuentes
2. NO cambiar origen sin autorización
3. NO usar fallback silencioso
4. NO devolver $0 por error técnico

**Siempre distinguir:**
- Dato real
- Dato parcial
- Error de fuente

---

# VII. REGLAS DE CONEXIONES

1. Usar SIEMPRE resolver central (`connection_resolver.py`)
2. NO usar conexiones hardcodeadas
3. NO duplicar lógica de conexión
4. Respetar menú de Servidores SQL

---

# VIII. REGLAS DE ERRORES

**PROHIBIDO:**
- Ocultar errores
- Convertir errores en ceros

**OBLIGATORIO:**
- Status técnico: ok / partial / error
- Trazabilidad completa

---

# IX. REGLAS DE EMERGENT (CRÍTICA)

**NO volver a hacer:**
- ❌ "Arreglé esto y de paso moví…"
- ❌ "Optimicé esto sin pedirlo…"
- ❌ "Aproveché para refactorizar…"
- ❌ "Cambié la fuente porque se veía mejor…"

**ESO QUEDA PROHIBIDO.**

---

# X. CHECKLIST RÁPIDO PRE-CAMBIO

```
□ ¿Está definido el alcance exacto?
□ ¿Hay snapshot de archivos?
□ ¿El cambio está aislado?
□ ¿Toca módulo blindado? → Requiere autorización
□ ¿Toca queries/conexiones/fuentes? → Riesgo ALTO
□ ¿Hay pruebas de no regresión preparadas?
□ ¿Se documentará el cambio?

SI ALGUNA RESPUESTA ES "NO" → NO PROCEDER
```

---

# XI. CHECKLIST RÁPIDO POST-CAMBIO

```
□ Módulo afectado funciona correctamente
□ Tablero Ejecutivo sigue OK
□ Auditoría Compras sigue OK
□ Operaciones/Análisis sigue OK
□ No hay ceros falsos
□ Fuentes son las correctas
□ Cambio documentado
```

---

# XII. CONSECUENCIAS DE INCUMPLIMIENTO

1. Regresión detectada → Rollback inmediato
2. Cambio no documentado → Revisión obligatoria
3. Módulo blindado tocado sin autorización → Escalamiento

---

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   PROTOCOLO GLOBAL DE CAMBIOS ACTIVADO                                       ║
║                                                                               ║
║   Ningún módulo se modifica sin control, pruebas y documentación.            ║
║   Módulos críticos blindados contra regresiones.                             ║
║                                                                               ║
║   Versión: 1.0.0 | Fecha: 2026-04-19                                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```
