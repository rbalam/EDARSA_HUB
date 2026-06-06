# PAQUETE DE EJECUCIÓN EXTERNA: PILOTO SYNC AGENT

**Fecha**: 2026-04-23  
**Versión**: 1.0  
**Estado**: LISTO PARA EJECUCIÓN POR USUARIO

---

## 1. UBICACIÓN DEL PAQUETE

```
/app/backend/scripts/paquete_piloto_sync_agent.tar.gz
```

**Tamaño**: ~10 KB

---

## 2. CONTENIDO DEL PAQUETE

| Archivo | Propósito |
|---------|-----------|
| `README.md` | Inicio rápido |
| `GUIA_PILOTO.md` | Guía paso a paso detallada |
| `CHECKLIST_PILOTO.md` | Checklist para documentar ejecuciones |
| `sync_agent_piloto.py` | Script del agente piloto |
| `config_template.yaml` | Template de configuración |
| `requirements.txt` | Dependencias Python |

---

## 3. PASOS PREVIOS OBLIGATORIOS (en HUB)

Antes de ejecutar el piloto, el usuario debe:

### 3.1 Registrar servidor SoftRestaurant real

Si no existe en HUB:
1. Acceder a EDARSA HUB como admin
2. Ir a Menú Servidores > Agregar Servidor
3. Completar datos del servidor SR real:
   - Nombre descriptivo
   - Tipo: SoftRestaurant
   - Host/Puerto/BD/Usuario/Password
4. Guardar y copiar el **Server ID** (UUID)

### 3.2 Generar token de agente

```bash
# Desde máquina con acceso a HUB
HUB_URL="https://erp-crm-enterprise-1.preview.emergentagent.com"
USER_EMAIL="admin@edarsa.com"
USER_PASSWORD="EDARSA2025"
SERVER_ID="<UUID_DEL_SERVIDOR_REAL>"

# Obtener token de usuario
USER_TOKEN=$(curl -s -X POST "$HUB_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# Generar token de agente
curl -s -X POST "$HUB_URL/api/admin/agents/generate-token" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"server_id\": \"$SERVER_ID\", \"agent_id\": \"agent-sr-piloto-001\"}"
```

**Guardar la respuesta completa (especialmente el `token`).**

---

## 4. EJECUCIÓN DEL PILOTO (en máquina local)

### 4.1 Descargar y descomprimir paquete

```bash
# Copiar paquete a máquina local (o descargarlo de HUB)
tar -xzvf paquete_piloto_sync_agent.tar.gz
cd paquete_piloto_sync_agent
```

### 4.2 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4.3 Crear configuración

```bash
cp config_template.yaml config.yaml
# Editar config.yaml con:
# - agent_id del paso 3.2
# - hub_url de HUB
# - hub_token del paso 3.2
# - server_id del paso 3.1
# - credenciales SQL del servidor SR
```

### 4.4 Probar autenticación

```bash
python sync_agent_piloto.py --config config.yaml --test-only
```

**Debe mostrar**: `✅ Autenticación OK`

### 4.5 Ejecutar sincronizaciones

```bash
# Ejecución 1: Datos del día actual
python sync_agent_piloto.py --config config.yaml

# Ejecución 2: Misma fecha (validar SKIP)
python sync_agent_piloto.py --config config.yaml

# Ejecución 3: Fecha diferente
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22

# Ejecución 4: Misma fecha (validar SKIP)
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22

# Ejecución 5: Validación final
python sync_agent_piloto.py --config config.yaml
```

---

## 5. CRITERIOS DE ÉXITO

| Criterio | Cómo validar |
|----------|--------------|
| Auth OK | `--test-only` pasa sin error |
| SQL OK | Conecta y extrae datos |
| POST OK | `status: OK` en respuesta |
| UPSERT OK | `INSERT: 1` primera vez |
| Idempotencia OK | `SKIP: 1` en repetición |
| Heartbeat OK | Sin errores |

---

## 6. EVIDENCIA A ENTREGAR

Al completar las 5 ejecuciones:

1. **CHECKLIST_PILOTO.md** completada
2. **5 archivos de log** (sync_agent_piloto_*.log)
3. **5 archivos de reporte** (reporte_piloto_*.json)
4. **Resumen ejecutivo** con:
   - Servidor piloto (nombre, ID)
   - Resultados de cada ejecución
   - Confirmación de idempotencia
   - Dictamen: PILOTO EXITOSO / CON OBSERVACIONES / FALLIDO

---

## 7. SIGUIENTE PASO DESPUÉS DEL PILOTO

Si **PILOTO EXITOSO**:
- Usuario informa resultados
- Agente documenta cierre de Fase 1
- Se autoriza planificación de Fase 2

Si **PILOTO CON OBSERVACIONES**:
- Analizar problemas
- Iterar hasta resolver
- Repetir validación

Si **PILOTO FALLIDO**:
- Documentar causa raíz
- Definir plan de corrección
- NO avanzar a Fase 2

---

## 8. NOTAS IMPORTANTES

1. **El piloto NO es ejecutable desde el ambiente preview** (sin conectividad SQL)
2. El usuario debe ejecutar desde una máquina con acceso al SQL Server SR
3. Todo lo que entre al HUB desde el piloto tiene `source.is_pilot: true`
4. Para eliminar datos del piloto: `db.kpis_comercial.deleteMany({"source.is_pilot": true})`

---

## APROBACIÓN

| Aspecto | Estado |
|---------|--------|
| Script piloto listo | ✅ |
| Template configuración | ✅ |
| Guía paso a paso | ✅ |
| Checklist de validación | ✅ |
| Endpoints HUB funcionales | ✅ |
| Paquete empaquetado | ✅ |

**PAQUETE LISTO PARA ENTREGA**

---

**Firmado**: Agente E1  
**Fecha**: 2026-04-23
