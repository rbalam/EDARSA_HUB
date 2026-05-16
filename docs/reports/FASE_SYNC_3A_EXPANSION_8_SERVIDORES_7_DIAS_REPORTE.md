# FASE SYNC-3A: Expansión Controlada de Sincronización Histórica
## Reporte de Ejecución - Últimos 7 Días

**Fecha:** 2026-05-16  
**Ejecutado por:** E1 Agent  
**Estado:** ✅ PARCIALMENTE COMPLETADO

---

## 1. RESUMEN EJECUTIVO

Se evaluaron los servidores candidatos para FASE SYNC-3A. Se actualizó MPRO (ManagmentPro) con el día 2026-05-15 agregando 1 registro histórico y 2 registros PorHora. Los servidores SoftRestaurant externos no pudieron sincronizarse debido a que las credenciales cifradas no son descifrables en el entorno de preview (falta `SERVER_SECRET_KEY`).

**IMPORTANTE:** El sistema de protección anti-$0 falso funcionó correctamente: NO se guardaron datos falsos cuando las fuentes no fueron accesibles.

---

## 2. ALCANCE EJECUTADO

| Aspecto | Valor |
|---------|-------|
| Rango temporal | 2026-05-08 a 2026-05-15 (7 días) |
| Ventana operativa | 13:00 - 11:00 (cruza medianoche) |
| NO ejecutado histórico 30 días | ✅ Confirmado |
| NO implementado scheduler | ✅ Confirmado |
| Fuente de configuración | EDARSAHUB SQL |
| Query MPRO con Fecha_Alta | ✅ Confirmado |

---

## 3. SERVIDORES CANDIDATOS

### 3.1 Evaluados desde EDARSAHUB SQL

| ID | Nombre | Sistema | Tipo | Estado |
|----|--------|---------|------|--------|
| a5547321-1139-4d2b-9d53-182ca737b6b6 | 130° MERIDA | SoftRestaurant | DATA_SOURCE | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS | SoftRestaurant | DATA_SOURCE | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| a5ff0e25-f029-43db-b634-d4ac814c904f | LA ESTELAR | SoftRestaurant | DATA_SOURCE | ⚠️ CREDENCIALES_NO_DESCIFRABLES |
| 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro | MPRO | DATA_SOURCE | ✅ SINCRONIZADO |

### 3.2 Excluidos con Motivo

| Nombre | Sistema | Motivo Exclusión |
|--------|---------|------------------|
| EDARSAHUB_SQL | EDARSA_HUB | DESTINO_NO_FUENTE |
| 130° QRO LOCAL | EDARSAHUB | DESTINO_NO_FUENTE |
| CHAPUR NORTE | SoftRestaurant Enterprise | PENDIENTE_VALIDACION_API_LOCAL_VENTAS |
| CHAPUR NORTE BACKOFICE | SoftRestaurant Enterprise | PENDIENTE_VALIDACION_API_LOCAL_VENTAS |
| ORIGEN LOCAL | EDARSAHUB | DESTINO_NO_FUENTE |
| HR2020 ESCRITURA | EDARSA_HUB | EXCLUIDO_ADMINISTRATIVO |
| PRUEBAS SOFTRESTAURANT | SoftRestaurant | EXCLUIDO_PRUEBAS |

---

## 4. SERVIDORES INCLUIDOS

### ManagmentPro (MPRO)

| Campo | Valor |
|-------|-------|
| ID | 1b230a06-ffaf-4c70-bd27-b1be3579dea6 |
| Sistema | MPRO |
| Host | 54.39.104.176:1433 |
| Database | CENTRAL2020 |
| Status | ✅ SINCRONIZADO |
| Query hora | `DATEPART(HOUR, Fecha_Alta)` |
| Filtro fecha | `CAST(Vn_Fecha AS DATE)` |
| Campo importe | `Vn_Precio_Neto_Importe` |

---

## 5. RESULTADOS SYNC

### 5.1 Sync_Ventas_Historicas

| Sistema | Registros | FechaMin | FechaMax | VentaTotal |
|---------|-----------|----------|----------|------------|
| MPRO | 9 | 2026-05-07 | 2026-05-15 | $1,666,270.37 |
| SoftRestaurant | 8 | 2026-05-07 | 2026-05-14 | $1,026,819.00 |

**Registro agregado:** 2026-05-15 (MPRO) - $18,273.99, 10 tickets

### 5.2 Sync_Ventas_PorHora

| Sistema | Registros | Servidores | FechaMin | FechaMax |
|---------|-----------|------------|----------|----------|
| MPRO | 89 | 1 | 2026-05-08 | 2026-05-15 |
| SoftRestaurant | 62 | 1 | 2026-05-08 | 2026-05-14 |

**Registros agregados:** 2 (MPRO 2026-05-15, horas 13 y 17)

### 5.3 Sync_Ventas_PorDiaSemana

| Sistema | Registros | Servidores |
|---------|-----------|------------|
| MPRO | 7 | 1 |
| SoftRestaurant | 7 | 1 |

---

## 6. VALIDACIÓN PORHORA VS HISTÓRICOS (MPRO)

| Fecha | Histórica | PorHora | Diferencia | Status |
|-------|-----------|---------|------------|--------|
| 2026-05-07 | $98,938.00 | $0.00 | $98,938.00 | ⚠️ Sin PorHora |
| 2026-05-08 | $230,443.79 | $230,443.79 | $0.00 | ✅ |
| 2026-05-09 | $340,786.53 | $340,786.53 | $0.00 | ✅ |
| 2026-05-10 | $400,476.13 | $400,476.14 | -$0.01 | ✅ (redondeo) |
| 2026-05-11 | $87,490.41 | $87,490.42 | -$0.01 | ✅ (redondeo) |
| 2026-05-12 | $117,376.50 | $117,376.50 | $0.00 | ✅ |
| 2026-05-13 | $122,498.51 | $122,498.51 | $0.00 | ✅ |
| 2026-05-14 | $249,986.51 | $249,986.51 | $0.00 | ✅ |
| 2026-05-15 | $18,273.99 | $18,273.99 | $0.00 | ✅ |

**Nota:** 2026-05-07 no tiene PorHora porque está fuera del rango de FASE SYNC-2C (últimos 7 días desde 2026-05-08).

---

## 7. DISTRIBUCIÓN PORHORA MPRO

| Fecha | Num Horas | Hora Min | Hora Max |
|-------|-----------|----------|----------|
| 2026-05-08 | 14 | 0 | 23 |
| 2026-05-09 | 13 | 0 | 23 |
| 2026-05-10 | 13 | 9 | 21 |
| 2026-05-11 | 10 | 13 | 23 |
| 2026-05-12 | 12 | 0 | 23 |
| 2026-05-13 | 12 | 0 | 23 |
| 2026-05-14 | 13 | 0 | 23 |
| 2026-05-15 | 2 | 13 | 17 |

✅ **Distribución horaria correcta** - No todo concentrado en hora 0

---

## 8. PROTECCIÓN ANTI-$0 FALSO

**FUNCIONÓ CORRECTAMENTE**

Cuando los servidores SoftRestaurant no fueron accesibles:
- NO se guardaron registros con $0
- Se registró `SOURCE_FAILED` como status
- Se documentó el error sin corromper datos existentes

```
WARNING:[SYNC-VENTAS] a5547321-1139-4d2b-9d53-182ca737b6b6/2026-05-08: Fuente falló - NO guardando $0
WARNING:[SYNC-VENTAS] 6d053c22-523e-48c0-b72b-96081e2d781b/2026-05-08: Fuente falló - NO guardando $0
WARNING:[SYNC-VENTAS] a5ff0e25-f029-43db-b634-d4ac814c904f/2026-05-08: Fuente falló - NO guardando $0
```

---

## 9. PROBLEMAS IDENTIFICADOS

### 9.1 Credenciales No Descifrables

**Causa:** La variable de entorno `SERVER_SECRET_KEY` no está configurada en el entorno de preview.

**Impacto:** Los servidores SoftRestaurant externos (130° MERIDA, CIENFUEGOS, LA ESTELAR) no pueden sincronizarse porque sus contraseñas están cifradas.

**Solución:** Configurar `SERVER_SECRET_KEY` en el entorno de producción.

### 9.2 Día 2026-05-07 Sin PorHora

**Causa:** El rango de FASE SYNC-2C empezó en 2026-05-08.

**Impacto:** El registro de 2026-05-07 tiene Histórica pero no PorHora.

**Solución:** Pendiente como P2 separado.

---

## 10. VALIDACIONES CUMPLIDAS

| Validación | Resultado |
|------------|-----------|
| Fuente EDARSAHUB SQL | ✅ |
| NO 30 días | ✅ |
| NO scheduler | ✅ |
| Ventana 13:00-11:00 | ✅ |
| NO uso de 03:00 | ✅ |
| MPRO usa Fecha_Alta | ✅ |
| Anti-$0 falso | ✅ |
| UPSERT idempotente | ✅ |
| No exposición de secrets | ✅ |

---

## 11. NO REGRESIÓN

| Componente | Estado |
|------------|--------|
| Sync_Ventas_Historicas existente | ✅ No afectado |
| Sync_Ventas_PorHora existente | ✅ No afectado |
| Sync_Ventas_PorDiaSemana existente | ✅ No afectado |
| SoftRestaurant existente | ✅ No modificado |
| Backend | ✅ Operativo |
| Login | ✅ Operativo |

---

## 12. ARCHIVOS MODIFICADOS

Ninguno. La lógica existente en `/app/backend/modules/sync_historicos/` ya soporta la expansión.

---

## 13. RECOMENDACIONES

### P0 - Crítico
1. **Configurar `SERVER_SECRET_KEY`** en entorno de producción para habilitar descifrado de credenciales

### P1 - Alta
2. Sincronizar servidores SoftRestaurant (130° MERIDA, CIENFUEGOS, LA ESTELAR) una vez resuelto P0
3. Completar PorHora para 2026-05-07

### P2 - Media
4. Validar si CHAPUR NORTE/BACKOFICE soportan query de ventas vía API_LOCAL
5. Implementar scheduler automático para sync diario

---

## 14. CONCLUSIÓN

**FASE SYNC-3A PARCIALMENTE COMPLETADA**

- ✅ MPRO actualizado con 2026-05-15
- ✅ Protección anti-$0 funcionó correctamente
- ✅ Distribución horaria MPRO correcta
- ✅ No se corrompieron datos existentes
- ⚠️ SoftRestaurant externos pendientes (credenciales)
- ⚠️ 2026-05-07 pendiente (P2)

El sistema está preparado para sincronización completa una vez configurada `SERVER_SECRET_KEY` en producción.

---

*Documento generado por E1 Agent*  
*Fecha: 2026-05-16*
