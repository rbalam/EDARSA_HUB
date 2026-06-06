# FASE 3D — Validación Real de Conectividad SQL/API con Secretos Cifrados

**Fecha:** 25 de Abril de 2026  
**Status:** COMPLETADA  
**Autor:** Sistema EDARSA HUB

---

## 1. Resumen Ejecutivo

La FASE 3D validó que los módulos de EDARSA HUB pueden conectarse correctamente a servidores externos usando passwords cifrados con Fernet (`enc:v1:...`) que son descifrados internamente por `secret_manager`/`server_registry`.

### Resultados Globales

| Métrica | Valor |
|---------|-------|
| Servidores probados | 8 |
| Descifrado OK | 8/8 (100%) |
| Conectividad OK | 5/8 |
| Source Unreachable (red/VPN) | 3/8 |
| Auth Failed | 0/8 |
| Secret Decryption Error | 0/8 |
| Secretos expuestos | 0 |

---

## 2. Objetivo

Confirmar que EDARSA HUB puede:
1. Descifrar passwords internamente antes de conectar
2. Conectar a servidores SQL externos (SoftRestaurant, MPRO)
3. No usar `enc:v1:...` como password directo en pyodbc
4. No exponer secretos en logs, responses ni documentos
5. Clasificar correctamente errores de red vs errores de cifrado

---

## 3. Inventario de Servidores Probados

| ID | Nombre | System Type | Host | Secret Status | Conectividad |
|----|--------|-------------|------|---------------|--------------|
| A5547321... | 130° MERIDA | SOFTRESTAURANT | 130mid.ddns.net | ENCRYPTED | SUCCESS |
| 6D053C22... | CIENFUEGOS | SOFTRESTAURANT | servercienfuegos.ddns | ENCRYPTED | SOURCE_UNREACHABLE |
| 6D859026... | CIENFUEGOS TABLAJERIA | SOFTRESTAURANT | servercienfuegos.ddns | ENCRYPTED | SOURCE_UNREACHABLE |
| B5175237... | HR2020 ESCRITURA | MANAGEMENTPRO | 54.39.104.176 | ENCRYPTED | SUCCESS |
| A5FF0E25... | LA ESTELAR | SOFTRESTAURANT | serverestelar.ddns.net | ENCRYPTED | SOURCE_UNREACHABLE |
| 1B230A06... | ManagmentPro | MANAGEMENTPRO | 54.39.104.176 | ENCRYPTED | SUCCESS |
| D1D8C70F... | MPRO TABLAJERIA | MANAGEMENTPRO | 54.39.104.176 | ENCRYPTED | SUCCESS |
| D8425038... | PRUEBAS SOFTRESTAURANT | SOFTRESTAURANT | 54.39.104.176\SOFTREST | ENCRYPTED | SUCCESS |

**Nota:** Los servidores CIENFUEGOS, CIENFUEGOS TABLAJERIA y LA ESTELAR usan hosts externos (ddns.net) que no son alcanzables desde el ambiente preview sin VPN. Esto es un problema de red, NO de cifrado.

---

## 4. Validación Secret Manager

```
SECRET_MANAGER STATUS
=====================
configured: True
fingerprint: d60eba8b
valid_format: True
issues: []
encryption_available: True
```

**Resultado:** Secret Manager operativo y listo para descifrar.

---

## 5. Validación Server Registry

| Server ID | Secret Status | Decrypt OK | Response Public Safe |
|-----------|---------------|------------|----------------------|
| A5547321... | ENCRYPTED | ✓ | ✓ |
| 6D053C22... | ENCRYPTED | ✓ | ✓ |
| 6D859026... | ENCRYPTED | ✓ | ✓ |
| B5175237... | ENCRYPTED | ✓ | ✓ |
| A5FF0E25... | ENCRYPTED | ✓ | ✓ |
| 1B230A06... | ENCRYPTED | ✓ | ✓ |
| D1D8C70F... | ENCRYPTED | ✓ | ✓ |
| D8425038... | ENCRYPTED | ✓ | ✓ |

**Resultado:** Todos los servidores descifran correctamente y las responses públicas no exponen secretos.

---

## 6. Script de Validación

**Archivo:** `/app/backend/scripts/validate_encrypted_server_connectivity.py`

### Uso

```bash
# Dry-run (solo inventario)
python validate_encrypted_server_connectivity.py --dry-run

# Ejecutar pruebas
python validate_encrypted_server_connectivity.py --run

# Filtrar por tipo
python validate_encrypted_server_connectivity.py --run --system-type SOFTRESTAURANT

# Incluir CORE
python validate_encrypted_server_connectivity.py --run --include-core
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--dry-run` | Solo inventario, no ejecutar pruebas |
| `--run` | Ejecutar pruebas de conectividad |
| `--server-id <id>` | Probar solo un servidor específico |
| `--system-type <type>` | Filtrar por SOFTRESTAURANT\|MANAGEMENTPRO\|API |
| `--timeout <seconds>` | Timeout de conexión (default: 10) |
| `--include-inactive` | Incluir servidores inactivos |
| `--include-core` | Incluir servidores CORE |

### Reporte

**Archivo:** `/app/docs/reports/encrypted_connectivity_validation_report.json`

---

## 7. Resultado Conectividad SQL

### SoftRestaurant

| Servidor | Resultado | Observación |
|----------|-----------|-------------|
| 130° MERIDA | SUCCESS | Conectó en 774ms |
| PRUEBAS SOFTRESTAURANT | SUCCESS | Conectó en 352ms |
| CIENFUEGOS | SOURCE_UNREACHABLE | Host ddns.net no alcanzable |
| CIENFUEGOS TABLAJERIA | SOURCE_UNREACHABLE | Host ddns.net no alcanzable |
| LA ESTELAR | SOURCE_UNREACHABLE | Host ddns.net no alcanzable |

### ManagementPro (MPRO)

| Servidor | Resultado | Observación |
|----------|-----------|-------------|
| ManagmentPro | SUCCESS | Conectó en 329ms |
| HR2020 ESCRITURA | SUCCESS | Conectó en 321ms |
| MPRO TABLAJERIA | SUCCESS | Conectó en 338ms |

**Conclusión:** Todos los servidores con host alcanzable conectan correctamente usando passwords descifrados.

---

## 8. Resultado APIs

No hay servidores tipo API con api_key cifrada activos en este momento. Validación parcial: la lógica de descifrado de api_key está implementada en el script.

---

## 9. Resultado Comercial

| Endpoint | Sistema | Server | Resultado |
|----------|---------|--------|-----------|
| Tablero Ejecutivo | Mixto | Todos | SUCCESS (5 unidades) |
| Dashboard | SoftRestaurant | 130° MERIDA | SUCCESS |
| Dashboard | MPRO | ManagmentPro | NO_DATA (conexión OK) |

**Evidencia:**
```
Comercial - Dashboard 130° MERIDA:
  source_status: SUCCESS
  source_message: Datos obtenidos correctamente de 130° MERIDA

Comercial - Dashboard ManagmentPro:
  source_status: NO_DATA
  source_message: Conexión exitosa a ManagmentPro pero no hay datos
```

---

## 10. Resultado Compras

Los endpoints de Compras están comentados/deshabilitados en routes.py según documentación. Las funciones de conexión SQL en el módulo usan `decrypt_server_secrets()` correctamente según FASE 3C.2.

**Status:** Validación estructural OK. Endpoints no disponibles para prueba.

---

## 11. Resultado Finanzas / Propinas TPV

| Endpoint | Resultado | Evidencia |
|----------|-----------|-----------|
| Dashboard Finanzas | SUCCESS | Keys: periodo, mensaje, kpis, presupuestos |
| Propinas TPV | SUCCESS | fuente: "SQL Server EDARSA HUB" |

**Evidencia:**
```
Dashboard Finanzas:
  Status: SUCCESS
  Keys: ['periodo', 'mensaje', 'kpis', 'presupuestos', 'por_sucursal']

Propinas TPV:
  Status: SUCCESS
  fuente: "SQL Server EDARSA HUB"
  total: 0 (sin datos pero conexión OK)
```

---

## 12. Resultado Operaciones / Inventarios

Los endpoints de inventarios usan mongodb_id legacy. Validación estructural confirma que el código usa `decrypt_server_secrets()` para conexiones SQL.

**Status:** Validación estructural OK.

---

## 13. Errores Clasificados

| Estado | Significado | Conteo |
|--------|-------------|--------|
| SUCCESS | Conectó y query respondió | 5 |
| NO_DATA | Query OK pero sin registros | 0 |
| SOURCE_UNREACHABLE | Red/VPN/Firewall | 3 |
| AUTH_FAILED | Login incorrecto | 0 |
| SECRET_DECRYPTION_ERROR | Error descifrando | 0 |
| QUERY_ERROR | Conectó pero query falló | 0 |
| CONFIGURATION_MISSING | Falta config | 0 |
| SKIPPED | Inactivo/CORE excluido | 0 |

---

## 14. No Exposición de Secretos

### Validaciones

| Verificación | Resultado |
|--------------|-----------|
| `/api/servers` no devuelve password | ✓ |
| `/api/servers` no devuelve api_key | ✓ |
| `/api/servers` no devuelve password_encrypted | ✓ |
| `/api/servers` no devuelve api_key_encrypted | ✓ |
| `/api/servers` devuelve password_configured | ✓ |
| `/api/servers` devuelve api_key_configured | ✓ |
| Logs backend sin secretos | ✓ |
| Reporte JSON sin secretos | ✓ |
| Script no imprime secretos | ✓ |

---

## 15. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| Servidores externos no alcanzables | Documentados como SOURCE_UNREACHABLE, requieren VPN en producción |
| Endpoints Compras deshabilitados | Estructura de código validada, habilitar cuando sea necesario |
| Módulos legacy usando mongodb_id | Migración gradual a SQL id en curso |

---

## 16. Pendientes

- P1: Validar conectividad en ambiente de producción con VPN
- P2: Habilitar endpoints de Compras cuando sea necesario
- P3: Migrar endpoints de inventarios a usar SQL id

---

## 17. Archivos Creados/Modificados

| Archivo | Acción |
|---------|--------|
| `/app/backend/scripts/validate_encrypted_server_connectivity.py` | Creado |
| `/app/docs/reports/encrypted_connectivity_validation_report.json` | Generado |
| `/app/docs/FASE_3D_VALIDACION_CONECTIVIDAD_SECRETOS_CIFRADOS.md` | Creado |

---

## 18. Conclusión

La FASE 3D se completó exitosamente:

- ✅ 8/8 servidores descifran passwords correctamente
- ✅ 5/8 servidores conectan (3 inaccesibles por red)
- ✅ 0 errores de descifrado
- ✅ 0 errores de autenticación
- ✅ Comercial funciona con secretos cifrados
- ✅ Finanzas funciona con secretos cifrados
- ✅ No se exponen secretos en logs/responses
- ✅ No se usa `enc:v1:` como password final
- ✅ Backend compila y corre
- ✅ Documentación completa

**Estado final:** Los módulos de EDARSA HUB pueden conectarse correctamente a servidores externos usando passwords cifrados que son descifrados internamente por secret_manager.
