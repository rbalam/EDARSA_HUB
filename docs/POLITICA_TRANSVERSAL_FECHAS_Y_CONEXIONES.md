# POLÍTICA TRANSVERSAL: Fechas y Conexiones SQL

## Fecha de vigencia: 2026-04-19
## Aplica a: Todos los módulos de EDARSA HUB

---

## 1. POLÍTICA DE RANGOS DE FECHA

### 1.1 Regla General
**PROHIBIDO** construir filtros de fecha manualmente en módulos.
**OBLIGATORIO** usar el helper centralizado `DateFilterPolicy`.

### 1.2 Helper Autorizado

```python
from core.utils.date_filters import (
    DateFilterPolicy,
    to_yyyymmdd_range,
    is_valid_range,
    get_month_range,
    adjust_future_month
)
```

### 1.3 Uso Correcto

```python
# ✅ CORRECTO: Validar antes de usar
if not is_valid_range(fecha_ini, fecha_fin):
    logging.error(f"Rango inválido: {fecha_ini} > {fecha_fin}")
    return []

# ✅ CORRECTO: Convertir con helper
fi, ff = to_yyyymmdd_range(fecha_ini, fecha_fin)

# ✅ CORRECTO: Ajustar meses futuros
year, month = adjust_future_month(year, month)
```

```python
# ❌ INCORRECTO: Conversión manual
fi = fecha_ini.replace('-', '')
ff = fecha_fin.replace('-', '')

# ❌ INCORRECTO: Sin validación
WHERE fecha >= '{fi}' AND fecha <= '{ff}'
```

### 1.4 Formato para SQL Server

| Tipo de columna | Formato | Helper |
|-----------------|---------|--------|
| datetime | YYYY-MM-DD | `to_iso()` |
| string/int YYYYMMDD | YYYYMMDD | `to_yyyymmdd()` |

### 1.5 Validaciones Obligatorias

1. **Antes de ejecutar query**: Validar que `fecha_ini <= fecha_fin`
2. **Meses futuros**: Ajustar automáticamente al mes actual
3. **Años futuros**: Ajustar automáticamente al año actual

---

## 2. POLÍTICA DE CREDENCIALES SQL

### 2.1 Fuente Autoritativa
**ÚNICA fuente de credenciales**: MongoDB (colección `servers`)

### 2.2 Prohibiciones

| Prohibido | Ejemplo |
|-----------|---------|
| Hardcodear credenciales | `password = 'Edarsa2018$'` |
| Duplicar en .env | `MPRO_PASS=...` |
| Exponer al frontend | `response.password` |
| Loggear passwords | `logging.info(f"pwd={password}")` |

### 2.3 Acceso Autorizado

```python
# ✅ CORRECTO: Desde MongoDB vía parámetro server
def get_kpis(server, ...):
    result = execute_sql_query(
        server['host'], 
        server['port'], 
        server['database'],
        server['username'], 
        server['password'],  # Viene de MongoDB
        query
    )
```

```python
# ✅ CORRECTO: Vía ServerConnectionManager
from core.server_connection_manager import get_server_config
config = get_server_config(server_id)
```

### 2.4 Info Segura (para frontend/logs)

```python
from core.server_connection_manager import get_safe_server_info
safe_info = get_safe_server_info(server_id)
# Retorna: {id, name, host, port, database, system_type}
# NO retorna: password
```

---

## 3. CREDENCIALES LEGACY IDENTIFICADAS

Las siguientes credenciales hardcodeadas deben migrarse a MongoDB:

| Archivo | Ubicación | Status |
|---------|-----------|--------|
| `modules/finanzas/repository_cortes_z.py` | SOFTREST_SERVERS, MPRO_SERVERS | PENDIENTE |
| `scripts/validacion_propinas_tpv.py` | SERVER_CONFIG | PENDIENTE |
| `core/auditoria.py` | EDARSA_HUB_SQL | PENDIENTE |

### Plan de Migración (P1)
1. Agregar variables de entorno como fallback temporal
2. Migrar configuración a MongoDB `servers`
3. Eliminar valores hardcodeados
4. Mantener backward compatibility

---

## 4. ESTRUCTURA DE HELPERS

```
/app/backend/core/
├── utils/
│   ├── __init__.py
│   └── date_filters.py      # DateFilterPolicy
├── server_connection_manager.py  # ServerConnectionManager
├── db.py                     # execute_sql_query
└── pool.py                   # Connection pooling
```

---

## 5. CHECKLIST PARA NUEVOS DESARROLLOS

### Antes de implementar queries SQL:
- [ ] ¿Usé `is_valid_range()` para validar fechas?
- [ ] ¿Usé `to_yyyymmdd_range()` para convertir fechas?
- [ ] ¿Las credenciales vienen de MongoDB (parámetro `server`)?
- [ ] ¿No hay passwords en logs ni responses?
- [ ] ¿Manejé el caso de error de conexión sin retornar $0 silencioso?

### Antes de merge:
- [ ] ¿Grep no encuentra credenciales hardcodeadas en mi código?
- [ ] ¿El helper de fechas está siendo usado?
- [ ] ¿Los tests pasan con rangos de fecha válidos e inválidos?

---

## 6. CONTACTO

Para consultas sobre esta política:
- Revisar `/app/docs/DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md`
- Revisar código en `/app/backend/core/utils/date_filters.py`
