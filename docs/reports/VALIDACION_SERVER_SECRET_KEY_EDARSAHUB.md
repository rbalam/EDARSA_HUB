# VALIDACIÓN SERVER_SECRET_KEY - EDARSAHUB

**Fecha:** 2026-06-02  
**Estado:** PENDIENTE CONFIGURACIÓN  
**Documento:** Requisitos para ejecutar dry-run real de Sync_Sales

---

## 1. SITUACIÓN ACTUAL

### 1.1 Estado de SERVER_SECRET_KEY

```
SERVER_SECRET_KEY_STATUS= NO_CONFIGURADA
SERVER_SECRET_KEY_LENGTH= 0
```

**Impacto:** Todas las credenciales en `Servidores_Conexiones` están cifradas con esta clave. Sin ella, `decrypt_secret()` falla y no se puede conectar a ningún servidor POS.

### 1.2 Servidores Afectados

| Servidor | Tipo | Password | Requiere decrypt |
|----------|------|----------|------------------|
| CIENFUEGOS | DATA_SOURCE | ENCRYPTED | ✅ |
| 130° MERIDA | DATA_SOURCE | ENCRYPTED | ✅ |
| LA ESTELAR | DATA_SOURCE | ENCRYPTED | ✅ |
| ManagmentPro | DATA_SOURCE | ENCRYPTED | ✅ |
| MPRO TABLAJERIA | DATA_SOURCE | ENCRYPTED | ✅ |
| API ManagmentPro | API_LOCAL | N/A (usa api_key) | ✅ |

---

## 2. REGLAS DE SEGURIDAD

1. ❌ **No pedir** SERVER_SECRET_KEY por chat
2. ❌ **No imprimir** SERVER_SECRET_KEY en logs
3. ❌ **No guardar** SERVER_SECRET_KEY en código fuente
4. ❌ **No modificar** password_encrypted en la base de datos
5. ❌ **No re-cifrar** credenciales existentes
6. ❌ **No usar** password_encrypted como password real
7. ❌ **No ejecutar** --execute
8. ❌ **No ejecutar** dry-run real hasta validación OK

---

## 3. HERRAMIENTAS DE VALIDACIÓN CREADAS

### 3.1 validate_server_secret_key.py

**Ubicación:** `/app/backend/tools/validate_server_secret_key.py`

**Función:** Valida que SERVER_SECRET_KEY esté configurada y funcional.

**Uso:**
```bash
cd /app/backend
python tools/validate_server_secret_key.py
```

**Resultado esperado:**
```
RESULT=OK
SERVER_SECRET_KEY está configurada y funcional
```

### 3.2 test_sql_connection_from_servidores.py

**Ubicación:** `/app/backend/tools/test_sql_connection_from_servidores.py`

**Función:** Prueba conexión SQL usando credenciales descifradas.

**Uso:**
```bash
# Por unidad
python tools/test_sql_connection_from_servidores.py --unidad CIENFUEGOS

# Por servidor
python tools/test_sql_connection_from_servidores.py --server-name-like ManagmentPro
```

**Resultado esperado:**
```
RESULT=OK
SERVIDOR=CIENFUEGOS
Conexión exitosa - Puede proceder con dry-run
```

---

## 4. PROTOCOLO DE VALIDACIÓN

### Paso 1: Configurar SERVER_SECRET_KEY

Usar mecanismo seguro de Emergent para configurar la variable de entorno:

```bash
# NO ejecutar este comando directamente
# Usar la interfaz segura de Emergent para secretos
export SERVER_SECRET_KEY="<valor_seguro>"
```

### Paso 2: Validar configuración

```bash
cd /app/backend
python tools/validate_server_secret_key.py
```

Continuar **solo si** retorna `RESULT=OK`.

### Paso 3: Probar conexiones

```bash
# SoftRestaurant
python tools/test_sql_connection_from_servidores.py --unidad CIENFUEGOS

# MPRO
python tools/test_sql_connection_from_servidores.py --server-name-like ManagmentPro
```

Continuar **solo si** ambos retornan `RESULT=OK`.

### Paso 4: Ejecutar dry-runs

```bash
# SoftRestaurant
python tools/sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run

# MPRO
python tools/sync_sales_dry_run.py --unidad 130QRO --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
python tools/sync_sales_dry_run.py --unidad ORIGEN --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run
```

---

## 5. CONFIGURACIÓN DE UNIDADES

### 5.1 SoftRestaurant (CIENFUEGOS, 130MID, ESTELAR)

| Unidad | Servidor | Host | Database |
|--------|----------|------|----------|
| CIENFUEGOS | CIENFUEGOS | servercienfuegos.ddns.net,6669 | softrestaurant95pro |
| 130MID | 130° MERIDA | 130mid.ddns.net | softrestaurant10 |
| ESTELAR | LA ESTELAR | serverestelar.ddns.net,6969 | softrestaurant12 |

### 5.2 MPRO (130QRO, ORIGEN)

| Unidad | Servidor | Host | Database | Sucursal |
|--------|----------|------|----------|----------|
| 130QRO | ManagmentPro | 54.39.104.176:1433 | CENTRAL2020 | 0021 |
| ORIGEN | ManagmentPro | 54.39.104.176:1433 | CENTRAL2020 | 0023 |

**Nota:** Ambas unidades MPRO usan el mismo servidor `ManagmentPro` con base `CENTRAL2020`, diferenciándose por `sucursal_origen_id`.

---

## 6. SERVIDORES LEGACY/ALTERNATIVOS (NO USAR)

| Servidor | Tipo | Estado | Motivo |
|----------|------|--------|--------|
| 130° QRO LOCAL | API_LOCAL | ❌ | Puerto :4 incorrecto, sin credenciales SQL |
| ORIGEN LOCAL | API_LOCAL | ❌ | Puerto :4 incorrecto, sin credenciales SQL |
| API ManagmentPro | API_LOCAL | ⏸️ | Usa API, no SQL directo |

Estos servidores **no deben modificarse automáticamente**. Se requiere documentación clara antes de usarlos.

---

## 7. CHECKLIST ANTES DE DRY-RUN REAL

- [ ] SERVER_SECRET_KEY configurada en entorno
- [ ] `validate_server_secret_key.py` retorna `RESULT=OK`
- [ ] `test_sql_connection_from_servidores.py --unidad CIENFUEGOS` retorna `RESULT=OK`
- [ ] `test_sql_connection_from_servidores.py --server-name-like ManagmentPro` retorna `RESULT=OK`
- [ ] Sync_Sales tiene 0 registros (estado limpio)
- [ ] Comercial_KPIs_Diarios_v2 no será modificado

---

## 8. RESULTADO ESPERADO POST-VALIDACIÓN

Cuando SERVER_SECRET_KEY esté configurada correctamente:

```
$ python tools/validate_server_secret_key.py
=============================================================
VALIDACIÓN SERVER_SECRET_KEY
=============================================================

1. VARIABLE DE ENTORNO
----------------------------------------
   STATUS: CONFIGURADA
   LENGTH: 44

2. FORMATO
----------------------------------------
   STATUS: FORMATO_OK
   LENGTH_OK: 44 >= 32

3. DECRYPT_SECRET
----------------------------------------
   IMPORT: OK
   FUNCTION: DISPONIBLE

4. DESCIFRADO REAL
----------------------------------------
   SERVIDOR_PRUEBA: CIENFUEGOS
   PASSWORD_ENCRYPTED_LENGTH: 88
   DECRYPT_STATUS: OK
   DECRYPTED_LENGTH: 12

=============================================================
RESULT=OK
SERVER_SECRET_KEY está configurada y funcional
Puede proceder con dry-run real
=============================================================
```

---

## 9. PRÓXIMOS PASOS

1. **Acción P0:** Configurar SERVER_SECRET_KEY usando mecanismo seguro de Emergent
2. **Validación:** Ejecutar protocolo de validación (sección 4)
3. **Dry-run:** Ejecutar dry-runs de CIENFUEGOS, 130QRO y ORIGEN
4. **Reporte:** Generar reporte de resultados

---

**Documento generado automáticamente | Agente E1 | 2026-06-02**
