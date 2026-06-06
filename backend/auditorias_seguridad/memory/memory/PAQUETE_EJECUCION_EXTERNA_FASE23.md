# FASE 2.3 - PAQUETE DE EJECUCIÓN EXTERNA

**Fecha:** 2026-04-23  
**Versión:** 1.0  
**Estado:** LISTO PARA EJECUCIÓN EN AMBIENTE CON CONECTIVIDAD  
**Prerequisito:** Ambiente con acceso a orígenes SQL configurados en menú de Servidores

---

## 1. ARCHIVOS/SCRIPTS A MOVER O EJECUTAR

### 1.1 Archivos Obligatorios

| Archivo | Propósito | Ubicación Original |
|---------|-----------|-------------------|
| `carga_historica_fase23.py` | Script principal de carga | `/app/backend/scripts/` |
| `kpis_repository.py` | Funciones UPSERT idempotente | `/app/backend/modules/comercial/` |
| `db.py` | Funciones de conexión SQL | `/app/backend/core/` |

### 1.2 Estructura de Carpetas Requerida

```
ejecucion_fase23/
├── scripts/
│   └── carga_historica_fase23.py
├── modules/
│   └── comercial/
│       ├── __init__.py
│       ├── kpis_repository.py
│       └── queries/
│           ├── __init__.py
│           ├── softrestaurant.py
│           └── mpro.py
├── core/
│   ├── __init__.py
│   └── db.py
├── requirements.txt
├── .env
├── precheck_conectividad.py
└── README_EJECUCION.md
```

### 1.3 Comando para Empaquetar

```bash
# Ejecutar desde /app/backend
mkdir -p /tmp/ejecucion_fase23/{scripts,modules/comercial/queries,core}

# Copiar archivos
cp scripts/carga_historica_fase23.py /tmp/ejecucion_fase23/scripts/
cp modules/comercial/kpis_repository.py /tmp/ejecucion_fase23/modules/comercial/
cp modules/comercial/queries/*.py /tmp/ejecucion_fase23/modules/comercial/queries/
cp core/db.py /tmp/ejecucion_fase23/core/

# Crear __init__.py vacíos
touch /tmp/ejecucion_fase23/modules/__init__.py
touch /tmp/ejecucion_fase23/modules/comercial/__init__.py
touch /tmp/ejecucion_fase23/modules/comercial/queries/__init__.py
touch /tmp/ejecucion_fase23/core/__init__.py

# Comprimir
cd /tmp && tar -czvf ejecucion_fase23.tar.gz ejecucion_fase23/
```

---

## 2. DEPENDENCIAS NECESARIAS

### 2.1 requirements.txt

```
pymongo>=4.0.0
motor>=3.0.0
pymssql>=2.2.0
python-dotenv>=1.0.0
```

### 2.2 Instalación

```bash
pip install -r requirements.txt
```

### 2.3 Dependencias del Sistema (Linux)

```bash
# Para pymssql (conexión SQL Server)
apt-get install freetds-dev freetds-bin
```

### 2.3 Dependencias del Sistema (Windows)

```
# pymssql se instala directamente con pip
# No requiere dependencias adicionales
```

---

## 3. VARIABLES/CONFIGURACIÓN REQUERIDAS

### 3.1 Archivo .env

```bash
# MongoDB - EDARSA HUB
MONGO_URL=mongodb://usuario:password@host:27017/edarsa_hub
DB_NAME=edarsa_hub

# Opcional: Configuración de logging
LOG_LEVEL=INFO
```

### 3.2 Variables de Entorno Alternativas

```bash
export MONGO_URL="mongodb://usuario:password@host:27017/edarsa_hub"
export DB_NAME="edarsa_hub"
```

### 3.3 Configuración de Servidores SQL

**NO se requiere configuración adicional.**  
Los servidores SQL se leen directamente de la colección `servers` en MongoDB (menú de Servidores de EDARSA HUB).

---

## 4. PASO A PASO DE EJECUCIÓN

### 4.1 Pre-Ejecución (Obligatorio)

```bash
# 1. Verificar conectividad a MongoDB
python3 -c "
from pymongo import MongoClient
import os
client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'edarsa_hub')]
print('MongoDB OK - Servidores:', db.servers.count_documents({}))
print('KPIs actuales:', db.kpis_comercial.count_documents({}))
"

# 2. Ejecutar PRECHECK de conectividad (ver sección 7)
python3 precheck_conectividad.py

# 3. Verificar que hay servidores elegibles
# Si elegibles = 0, NO CONTINUAR
```

### 4.2 Backup (Obligatorio)

```bash
# Crear backup de kpis_comercial ANTES de la carga
mongodump \
  --uri="$MONGO_URL" \
  --db=edarsa_hub \
  --collection=kpis_comercial \
  --out=/backup/pre_fase23_$(date +%Y%m%d_%H%M%S)

# Verificar backup
ls -la /backup/pre_fase23_*/edarsa_hub/
```

### 4.3 Ejecución de Carga

```bash
# Ejecutar carga histórica
cd /ruta/a/ejecucion_fase23
python3 scripts/carga_historica_fase23.py

# El script genera bitácora automáticamente en /tmp/carga_historica_*.json
```

### 4.4 Monitoreo Durante Ejecución

```bash
# En otra terminal, monitorear progreso
watch -n 30 "python3 -c \"
from pymongo import MongoClient
import os
client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'edarsa_hub')]
total = db.kpis_comercial.count_documents({})
nuevos = db.kpis_comercial.count_documents({'created_by': 'carga_historica_fase23'})
print(f'Total: {total}, Nuevos: {nuevos}')
\""
```

### 4.5 Post-Ejecución

```bash
# 1. Revisar bitácora generada
cat /tmp/carga_historica_*.json | python3 -m json.tool

# 2. Ejecutar validaciones (ver sección 6)
python3 -c "..." # Ver scripts de validación
```

---

## 5. PASO A PASO DE ROLLBACK

### 5.1 Rollback Total (Eliminar TODA la carga)

```bash
# OPCIÓN A: Desde MongoDB shell
mongosh "$MONGO_URL" --eval "
  // Verificar cuántos se eliminarán
  const count = db.kpis_comercial.countDocuments({created_by: 'carga_historica_fase23'});
  print('Documentos a eliminar:', count);
  
  // Confirmar antes de ejecutar
  // db.kpis_comercial.deleteMany({created_by: 'carga_historica_fase23'});
"

# OPCIÓN B: Desde Python
python3 -c "
from pymongo import MongoClient
import os
client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'edarsa_hub')]

# Verificar
count = db.kpis_comercial.count_documents({'created_by': 'carga_historica_fase23'})
print(f'Documentos a eliminar: {count}')

# Confirmar y ejecutar
confirm = input('¿Confirmar rollback? (si/no): ')
if confirm.lower() == 'si':
    result = db.kpis_comercial.delete_many({'created_by': 'carga_historica_fase23'})
    print(f'Eliminados: {result.deleted_count}')
else:
    print('Rollback cancelado')
"
```

### 5.2 Rollback Parcial (Por Servidor)

```bash
# Eliminar solo registros de un servidor específico
python3 -c "
from pymongo import MongoClient
import os
client = MongoClient(os.environ.get('MONGO_URL'))
db = client[os.environ.get('DB_NAME', 'edarsa_hub')]

SERVER_ID = 'UUID_DEL_SERVIDOR_A_ELIMINAR'

count = db.kpis_comercial.count_documents({
    'created_by': 'carga_historica_fase23',
    'server_id': SERVER_ID
})
print(f'Documentos a eliminar del servidor {SERVER_ID}: {count}')

# db.kpis_comercial.delete_many({
#     'created_by': 'carga_historica_fase23',
#     'server_id': SERVER_ID
# })
"
```

### 5.3 Rollback desde Backup

```bash
# Restaurar colección completa desde backup
mongorestore \
  --uri="$MONGO_URL" \
  --db=edarsa_hub \
  --collection=kpis_comercial \
  --drop \
  /backup/pre_fase23_YYYYMMDD_HHMMSS/edarsa_hub/kpis_comercial.bson
```

---

## 6. VALIDACIONES POST-CARGA

### 6.1 Script de Validación Completo

```python
# validar_post_carga.py
import os
from pymongo import MongoClient

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

print("=" * 60)
print("VALIDACIONES POST-CARGA FASE 2.3")
print("=" * 60)

# 1. DUPLICADOS (CRÍTICO)
pipeline = [
    {"$group": {
        "_id": {
            "server_id": "$server_id",
            "empresa_id": "$empresa_id",
            "sucursal_id": "$sucursal_id",
            "fecha": "$fecha"
        },
        "count": {"$sum": 1}
    }},
    {"$match": {"count": {"$gt": 1}}}
]
duplicados = list(db.kpis_comercial.aggregate(pipeline))
print(f"\n1. DUPLICADOS: {len(duplicados)}")
print(f"   Resultado: {'✅ PASS' if len(duplicados) == 0 else '❌ FAIL - REQUIERE ROLLBACK'}")

# 2. CONTEO TOTAL
total = db.kpis_comercial.count_documents({})
nuevos = db.kpis_comercial.count_documents({"created_by": "carga_historica_fase23"})
originales = total - nuevos
print(f"\n2. CONTEO:")
print(f"   Total documentos: {total}")
print(f"   Nuevos (carga): {nuevos}")
print(f"   Originales: {originales}")
print(f"   Resultado: {'✅ PASS' if originales >= 38 else '❌ FAIL - Originales afectados'}")

# 3. RANGO DE FECHAS
min_doc = db.kpis_comercial.find_one(sort=[("fecha", 1)])
max_doc = db.kpis_comercial.find_one(sort=[("fecha", -1)])
print(f"\n3. RANGO DE FECHAS:")
print(f"   Mínima: {min_doc.get('fecha') if min_doc else 'N/A'}")
print(f"   Máxima: {max_doc.get('fecha') if max_doc else 'N/A'}")

# 4. POR SERVIDOR
print(f"\n4. DOCUMENTOS POR SERVIDOR (nuevos):")
pipeline_srv = [
    {"$match": {"created_by": "carga_historica_fase23"}},
    {"$group": {"_id": "$server_id", "count": {"$sum": 1}}}
]
for srv in db.kpis_comercial.aggregate(pipeline_srv):
    print(f"   {srv['_id']}: {srv['count']}")

# 5. POR ESTADO
print(f"\n5. DOCUMENTOS POR ESTADO:")
pipeline_estado = [
    {"$group": {"_id": "$estado_periodo", "count": {"$sum": 1}}}
]
for e in db.kpis_comercial.aggregate(pipeline_estado):
    print(f"   {e['_id']}: {e['count']}")

# 6. IDEMPOTENCIA
print(f"\n6. TEST IDEMPOTENCIA:")
print(f"   (Re-ejecutar script y verificar que duplicados sigue = 0)")

# DICTAMEN
print("\n" + "=" * 60)
if len(duplicados) == 0 and originales >= 38:
    print("DICTAMEN: ✅ VALIDACIÓN EXITOSA")
else:
    print("DICTAMEN: ❌ VALIDACIÓN FALLIDA - REQUIERE ACCIÓN")
print("=" * 60)

client.close()
```

### 6.2 Checklist Manual

| # | Validación | Criterio | Resultado |
|---|------------|----------|-----------|
| 1 | Duplicados = 0 | Exactamente 0 | ⬜ |
| 2 | Originales intactos | >= 38 documentos | ⬜ |
| 3 | Rango 24 meses | Desde ~2024-04 hasta ~2026-04 | ⬜ |
| 4 | Cobertura servidores | >= 1 servidor con datos | ⬜ |
| 5 | Estados correctos | Históricos en CERRADO | ⬜ |
| 6 | Tablero responde | `/api/comercial/tablero-ejecutivo` OK | ⬜ |
| 7 | Idempotencia | Re-ejecución no duplica | ⬜ |

---

## 7. CÓMO EJECUTAR PRECHECK EN AMBIENTE EXTERNO

### 7.1 Script de Precheck

```python
# precheck_conectividad.py
# Copiar este archivo al ambiente de ejecución

import os
import sys
from pymongo import MongoClient
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')

print("=" * 70)
print("PRECHECK DE CONECTIVIDAD - FASE 2.3")
print(f"Fecha: {datetime.now()}")
print("=" * 70)

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

servidores = list(db.servers.find({
    "system_type": {"$in": ["SoftRestaurant", "MPRO"]}
}))

print(f"\nServidores a verificar: {len(servidores)}\n")

elegibles = 0
resultados = []

for srv in servidores:
    nombre = srv.get('name', 'SIN NOMBRE')
    tipo = srv.get('system_type', '?')
    host = srv.get('host', '')
    port = srv.get('port', '')
    database = srv.get('database', '')
    username = srv.get('username', '')
    password = srv.get('password', '')
    
    estado = "PENDIENTE"
    observacion = ""
    
    if host and port and database and username and password:
        # Intentar conexión
        try:
            # Importar desde el paquete local
            sys.path.insert(0, '.')
            from core.db import execute_sql_query
            
            result = execute_sql_query(
                host, port, database, username, password,
                "SELECT 1 as test",
                timeout=15
            )
            
            if result is not None:
                estado = "OK"
                elegibles += 1
                observacion = "Conexión exitosa"
            else:
                estado = "SIN_DATOS"
                observacion = "Query sin respuesta"
                
        except Exception as e:
            estado = "FAIL"
            error = str(e).lower()
            if "timeout" in error:
                observacion = "Timeout - no accesible"
            elif "login" in error or "password" in error:
                observacion = "Error autenticación"
            else:
                observacion = str(e)[:50]
    else:
        estado = "INCOMPLETO"
        observacion = "Configuración incompleta"
    
    print(f"[{tipo}] {nombre}: {estado}")
    print(f"        {observacion}")
    print(f"        Host: {host}:{port}")
    
    resultados.append({
        "servidor": nombre,
        "tipo": tipo,
        "estado": estado,
        "elegible": estado == "OK"
    })

print("\n" + "=" * 70)
print(f"RESUMEN: {elegibles}/{len(servidores)} servidores elegibles")
print("=" * 70)

if elegibles == len(servidores):
    print("\n✅ RECOMENDACIÓN: EJECUTAR CARGA TOTAL")
elif elegibles > 0:
    print(f"\n🟡 RECOMENDACIÓN: EJECUTAR CARGA PARCIAL ({elegibles} servidores)")
else:
    print("\n❌ RECOMENDACIÓN: NO EJECUTAR - Sin servidores accesibles")

client.close()
```

### 7.2 Ejecución del Precheck

```bash
# Desde el ambiente con conectividad
cd /ruta/a/ejecucion_fase23
python3 precheck_conectividad.py
```

---

## 8. CRITERIO DE ÉXITO / PARCIAL / ROLLBACK

### 8.1 Criterio de ÉXITO TOTAL

| Condición | Requerido |
|-----------|-----------|
| Duplicados | = 0 |
| Errores de script | = 0 |
| Servidores procesados | 8/8 |
| Registros originales | >= 38 (intactos) |
| Rango de fechas | ~24 meses cubiertos |
| Tablero ejecutivo | Responde con datos |

**Dictamen**: `FASE 2.3 COMPLETADA EXITOSAMENTE`

### 8.2 Criterio de ÉXITO PARCIAL

| Condición | Valor |
|-----------|-------|
| Duplicados | = 0 |
| Errores de script | = 0 |
| Servidores procesados | < 8 (al menos 1) |
| Servidores pendientes | Documentados |

**Dictamen**: `FASE 2.3 COMPLETADA CON OBSERVACIONES`
- Documentar servidores no procesados
- Programar reintento para servidores faltantes

### 8.3 Criterio de ROLLBACK

| Condición | Acción |
|-----------|--------|
| Duplicados > 0 | ROLLBACK INMEDIATO |
| Error de integridad | ROLLBACK INMEDIATO |
| Originales afectados | ROLLBACK INMEDIATO |
| Corrupción de datos | ROLLBACK desde backup |

**Dictamen**: `FASE 2.3 NO APROBADA - ROLLBACK EJECUTADO`

---

## 9. RESUMEN DE COMANDOS RÁPIDOS

```bash
# 1. PRECHECK
python3 precheck_conectividad.py

# 2. BACKUP
mongodump --uri="$MONGO_URL" --db=edarsa_hub --collection=kpis_comercial --out=/backup/pre_fase23

# 3. EJECUTAR CARGA
python3 scripts/carga_historica_fase23.py

# 4. VALIDAR
python3 validar_post_carga.py

# 5. ROLLBACK (si necesario)
mongosh "$MONGO_URL" --eval "db.kpis_comercial.deleteMany({created_by: 'carga_historica_fase23'})"
```

---

**Este paquete está listo para ser ejecutado en cualquier ambiente con conectividad a los orígenes SQL.**

Firma: E1 Agent  
Fecha: 2026-04-23
