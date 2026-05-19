# FIX: Catálogo SQL - Selector Servidores por Sistema/Proveedor

**Fecha:** 2026-05-19  
**Prioridad:** P0  
**Estado:** DIAGNÓSTICO COMPLETADO

---

## 1. Resumen del Bug

El selector "Servidor *" en Catálogo de Consultas SQL muestra **TODOS** los servidores independientemente del sistema de la consulta seleccionada.

**Comportamiento actual:**
- Al seleccionar consulta "SoftRestaurant Pro", el dropdown muestra: QRO LOCAL, ORIGEN LOCAL, ManagementPro, etc.
- Al seleccionar consulta "Enterprise", el dropdown muestra los mismos servidores MPRO.

**Comportamiento esperado:**
- SoftRestaurant Pro → Solo: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR
- Enterprise → Solo: CHAPUR NORTE, CHAPUR BACKOFFICE  
- MPRO → Solo: QRO LOCAL, ORIGEN LOCAL, ManagementPro, MPRO TABLAJERIA

---

## 2. Causa Raíz

### Problema 1: Desajuste de Códigos
Las consultas del catálogo tienen:
```javascript
"sistema": "SoftRestaurant"  // Código antiguo
```

Los servidores tienen:
```sql
system_type = 'SOFTRESTAURANT_PRO'  // Código canónico nuevo
```

### Problema 2: Mapeo Incompleto en Frontend

En `/app/frontend/src/pages/CatalogoConsultas.js` líneas 57-77:

```javascript
const serversDisponibles = useMemo(() => {
  if (!consultaSeleccionada) return servers;
  return servers.filter(s => {
    const sistemaConsulta = consultaSeleccionada.sistema?.toUpperCase();
    const sistemaServer = s.system_type?.toUpperCase();
    
    if (!sistemaConsulta) return true;  // ← PROBLEMA: Muestra todos si no tiene sistema
    
    // Mapeo incompleto - SOLO tiene SoftRestaurant y MPRO
    if (sistemaConsulta === 'SOFTRESTAURANT' && sistemaServer === 'SOFTRESTAURANT') return true;
    if (sistemaConsulta === 'MPRO' && sistemaServer === 'MPRO') return true;
    // FALTA: SOFTRESTAURANT_PRO, ENTERPRISE
    
    return sistemaServer === sistemaConsulta;  // Comparación directa (falla)
  });
}, [consultaSeleccionada, servers]);
```

---

## 3. Datos del Sistema

### Servidores en EDARSAHUB (system_type)

| Servidor | system_type | tipo_conexion |
|----------|-------------|---------------|
| 130° MERIDA | SOFTRESTAURANT_PRO | DATA_SOURCE |
| CIENFUEGOS | SOFTRESTAURANT_PRO | DATA_SOURCE |
| LA ESTELAR | SOFTRESTAURANT_PRO | DATA_SOURCE |
| CHAPUR NORTE | ENTERPRISE | API_LOCAL |
| CHAPUR BACKOFFICE | ENTERPRISE | API_LOCAL |
| 130° QRO LOCAL | MPRO | API_LOCAL |
| ORIGEN LOCAL | MPRO | API_LOCAL |
| ManagmentPro | MPRO | DATA_SOURCE |
| MPRO TABLAJERIA | MPRO | DATA_SOURCE |

### Consultas del Catálogo (sistema)

| Consulta | sistema |
|----------|---------|
| SR_VENTAS_* | SoftRestaurant |
| MPRO_VENTAS_* | MPRO |
| (nuevas) | Enterprise |
| (nuevas) | SOFTRESTAURANT_PRO |

---

## 4. Solución Propuesta

### Archivo a Modificar
`/app/frontend/src/pages/CatalogoConsultas.js`

### Lógica Corregida

```javascript
const serversDisponibles = useMemo(() => {
  if (!consultaSeleccionada) return servers;
  
  return servers.filter(s => {
    // Normalizar códigos a mayúsculas y trim
    const sistemaConsulta = (consultaSeleccionada.sistema || '').toUpperCase().trim();
    const sistemaServer = (s.system_type || '').toUpperCase().trim();
    
    // Si la consulta no tiene sistema, mostrar todos
    if (!sistemaConsulta) return true;
    
    // MAPEO CANÓNICO: consulta.sistema → server.system_type
    // Grupo SoftRestaurant
    if (
      (sistemaConsulta === 'SOFTRESTAURANT' || 
       sistemaConsulta === 'SOFTRESTAURANT_PRO' ||
       sistemaConsulta === 'SOFT_RESTAURANT' ||
       sistemaConsulta === 'SR') &&
      (sistemaServer === 'SOFTRESTAURANT' ||
       sistemaServer === 'SOFTRESTAURANT_PRO' ||
       sistemaServer === 'SOFT_RESTAURANT')
    ) {
      return true;
    }
    
    // Grupo Enterprise
    if (
      (sistemaConsulta === 'ENTERPRISE' ||
       sistemaConsulta === 'SOFRESATAURANT_ENTER') &&
      (sistemaServer === 'ENTERPRISE' ||
       sistemaServer === 'SOFRESATAURANT_ENTER')
    ) {
      return true;
    }
    
    // Grupo MPRO
    if (
      (sistemaConsulta === 'MPRO' ||
       sistemaConsulta === 'MANAGEMENTPRO' ||
       sistemaConsulta === 'MANAGMENTPRO') &&
      (sistemaServer === 'MPRO' ||
       sistemaServer === 'MANAGEMENTPRO' ||
       sistemaServer === 'MANAGMENTPRO')
    ) {
      return true;
    }
    
    // Comparación directa como fallback
    return sistemaServer === sistemaConsulta;
  });
}, [consultaSeleccionada, servers]);
```

### Adicional: Limpiar servidor al cambiar consulta

En `useCatalogoConsultasData.js`, modificar `seleccionarConsulta`:

```javascript
const seleccionarConsulta = useCallback((consulta) => {
  setConsultaSeleccionada(consulta);
  setServerSeleccionado('__NONE__');  // ← LIMPIAR selección anterior
  // ... resto del código
}, []);
```

---

## 5. Validaciones Requeridas

### A) SoftRestaurant Pro
1. Seleccionar consulta "SR_VENTAS_DIA"
2. Dropdown muestra: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR, PRUEBAS SOFTRESTAURANT
3. NO muestra: QRO LOCAL, ORIGEN LOCAL, ManagementPro, CHAPUR

### B) Enterprise
1. Seleccionar consulta Enterprise
2. Dropdown muestra: CHAPUR NORTE, CHAPUR BACKOFFICE
3. NO muestra: SoftRestaurant ni MPRO

### C) MPRO
1. Seleccionar consulta MPRO
2. Dropdown muestra: 130° QRO LOCAL, ORIGEN LOCAL, ManagmentPro, MPRO TABLAJERIA
3. NO muestra: SoftRestaurant ni Enterprise

### D) Cambio de consulta
1. Seleccionar consulta MPRO, elegir servidor QRO LOCAL
2. Cambiar a consulta SoftRestaurant
3. Servidor se limpia automáticamente
4. Dropdown muestra solo servidores SoftRestaurant

---

## 6. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/CatalogoConsultas.js` | Corregir `serversDisponibles` |
| `/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js` | Limpiar servidor en `seleccionarConsulta` |

---

## 7. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Romper otras pantallas | Solo modifica Catálogo SQL |
| Romper consultas existentes | Mapeo incluye códigos legacy |
| Perder servidor seleccionado | Comportamiento deseado |

---

## 8. No Regresión

- [ ] Catálogo SQL carga sin error
- [ ] Explorador BD carga sin error
- [ ] Catálogos del Sistema carga sin error
- [ ] Tablero Ejecutivo carga
- [ ] Comercial carga

---

## 9. Backout Plan

Revertir cambios en:
- `CatalogoConsultas.js` líneas 57-77
- `useCatalogoConsultasData.js` función `seleccionarConsulta`

---

*Diagnóstico completado: 2026-05-19*
