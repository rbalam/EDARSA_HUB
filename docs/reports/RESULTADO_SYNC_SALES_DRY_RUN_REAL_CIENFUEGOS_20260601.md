# RESULTADO: Sync_Sales Dry-Run Real - CIENFUEGOS 2026-06-01

**Fecha de Ejecución:** 2026-06-02 20:47:42  
**Ejecutado por:** Agente E1  
**Tipo:** DRY-RUN (sin inserción de datos)

---

## 1. UNIDAD USADA

| Campo | Valor |
|-------|-------|
| **Código** | CIENFUEGOS |
| **Nombre** | CIENFUEGOS |
| **ID Unidad** | b06ee652-0370-4267-b0a8-da6fc39b590a |

---

## 2. SERVER ID USADO

| Campo | Valor |
|-------|-------|
| **Server ID** | 6d053c22-523e-48c0-b72b-96081e2d781b |

---

## 3. SERVIDOR ORIGEN USADO

| Campo | Valor |
|-------|-------|
| **Nombre** | CIENFUEGOS |
| **Host** | servercienfuegos.ddns.net,6669\nationalsoft |
| **IP Resuelta** | 189.162.155.142 |
| **Puerto** | 6669 |
| **Instancia** | nationalsoft |

---

## 4. BASE ORIGEN

| Campo | Valor |
|-------|-------|
| **Database** | softrestaurant95pro |
| **Sistema** | SOFTRESTAURANT_PRO |

---

## 5. USUARIO

| Campo | Valor |
|-------|-------|
| **Estado** | USUARIO_CONFIGURADO |
| **Nombre** | CFLectura (según Servidores_Conexiones) |

*Nota: El valor real del usuario no se muestra por seguridad.*

---

## 6. ESTADO DE CONEXIÓN

| Campo | Valor |
|-------|-------|
| **Status** | ❌ NO CONECTADO |
| **Error** | `Adaptive Server is unavailable or does not exist` |
| **Causa** | El servidor DDNS no es accesible desde el entorno de preview |

### Detalle Técnico

```
DB-Lib error message 20009, severity 9:
Unable to connect: Adaptive Server is unavailable or does not exist 
(servercienfuegos.ddns.net,6669)
```

**Nota:** Este es el comportamiento ESPERADO cuando se ejecuta desde un entorno que no tiene acceso a la red corporativa donde está el servidor SoftRestaurant.

---

## 7. REGISTROS LEÍDOS

| Campo | Valor |
|-------|-------|
| **Total** | 0 |
| **Motivo** | No se pudo conectar al servidor origen |

---

## 8. REGISTROS QUE INSERTARÍA

| Campo | Valor |
|-------|-------|
| **Nuevos** | 0 |

---

## 9. DUPLICADOS DETECTADOS

| Campo | Valor |
|-------|-------|
| **Duplicados** | 0 |

*No se detectaron duplicados porque no hubo registros extraídos.*

---

## 10. MUESTRA ANONIMIZADA (5 registros)

**N/A** - No se extrajeron registros debido a la falta de conectividad.

---

## 11. JSON ITEMS VÁLIDO

| Campo | Valor |
|-------|-------|
| **Válidos** | 0 |
| **Nulos** | 0 |
| **Inválidos** | 0 |

*No se pudo validar porque no hubo registros extraídos.*

---

## 12. CONFIRMACIÓN: Sync_Sales NO CAMBIÓ

| Campo | Antes | Después | Cambio |
|-------|-------|---------|--------|
| **Registros** | 0 | 0 | ✅ SIN CAMBIOS |
| **Fecha mínima** | NULL | NULL | ✅ SIN CAMBIOS |
| **Fecha máxima** | NULL | NULL | ✅ SIN CAMBIOS |
| **Última modificación** | NULL | NULL | ✅ SIN CAMBIOS |

**Verificación SQL:**
```sql
SELECT COUNT(*) AS registros FROM dbo.Sync_Sales;
-- Resultado: 0 (antes y después)
```

---

## 13. CONFIRMACIÓN: Comercial_KPIs_Diarios_v2 NO CAMBIÓ

| Campo | Antes | Después | Cambio |
|-------|-------|---------|--------|
| **Registros** | 3,376 | 3,376 | ✅ SIN CAMBIOS |

**Verificación SQL:**
```sql
SELECT COUNT(*) AS total FROM Comercial_KPIs_Diarios_v2;
-- Resultado: 3376 (antes y después)
```

---

## 14. RECOMENDACIÓN

### ⚠️ NO EJECUTAR --execute DESDE ESTE ENTORNO

**Motivo:** El entorno de preview no tiene acceso de red al servidor SoftRestaurant CIENFUEGOS.

### Acciones Requeridas para Ejecutar Correctamente:

1. **Ejecutar desde servidor con acceso a red corporativa:**
   - El servidor SoftRestaurant usa DNS dinámico (DDNS)
   - Solo es accesible desde la red interna o VPN

2. **Verificar SERVER_SECRET_KEY:**
   - El warning indica que la clave de descifrado no está configurada
   - En el entorno correcto, configurar: `export SERVER_SECRET_KEY=...`

3. **Comando a ejecutar (desde servidor con acceso):**
   ```bash
   cd /app/backend
   python tools/sync_sales_dry_run.py \
     --unidad CIENFUEGOS \
     --fecha-inicio 2026-06-01 \
     --fecha-fin 2026-06-01 \
     --dry-run \
     --output /app/docs/reports/DRY_RUN_REAL.json
   ```

4. **Si el dry-run es exitoso, aprobar ejecución real:**
   - El script actual no implementa `--execute` intencionalmente
   - La inserción real debe hacerse con el job oficial `sync_comercial_edarsahub.py`

---

## RESUMEN EJECUTIVO

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Script funcional | ✅ | Usa patrón correcto de Servidores_Conexiones |
| Credenciales configuradas | ✅ | Usuario y password encontrados en BD |
| Conectividad a POS | ❌ | Requiere ejecución desde red corporativa |
| Sync_Sales sin cambios | ✅ | Verificado antes/después |
| KPIs sin cambios | ✅ | Verificado antes/después |
| Recomendación | ⏸️ PAUSAR | Re-ejecutar desde entorno con acceso a red |

---

## ARCHIVOS GENERADOS

| Archivo | Descripción |
|---------|-------------|
| `/app/docs/reports/DRY_RUN_CIENFUEGOS_20260601_REAL.json` | Reporte JSON del dry-run |
| `/app/docs/reports/RESULTADO_SYNC_SALES_DRY_RUN_REAL_CIENFUEGOS_20260601.md` | Este documento |

---

**Agente E1 | 2026-06-02**
