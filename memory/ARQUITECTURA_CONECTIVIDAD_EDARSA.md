# DIAGNÓSTICO DE ARQUITECTURA DE CONECTIVIDAD - EDARSA HUB

**Fecha:** 2026-04-23  
**Autor:** E1 Agent (Rol: Arquitecto de Soluciones)  
**Versión:** 1.1  
**Estado:** ✅ APROBADO POR USUARIO

---

## 0. DECISIONES APROBADAS

### Arquitectura Definitiva: AGENTES PUSH (Escenario C)
```
SQL local → Agente local → Push seguro HTTPS → EDARSA HUB → KPIs/tableros
```

### Aclaraciones Conceptuales (por usuario):
- **EDARSA HUB** es el cerebro central (plataforma + modelo de datos)
- **MongoDB** es componente de soporte (cache, logs, locks, KPIs), NO el cerebro
- **Cero dependencia estructural** de conexión SQL directa desde preview/cloud
- **VPN/Hamachi** solo como transición/contingencia, NO arquitectura definitiva

### Prioridad Operativa:
- **INMEDIATA:** Continuar Plan de Migración Fase 1 (Bloques 2, 3, 4...)
- **PARALELA:** Documentación de arquitectura de conectividad
- **POSTERIOR:** Diseño detallado del EDARSA Sync Agent

---

## 1. ANÁLISIS DE ESCENARIOS DE CONECTIVIDAD

### ESCENARIO A: Preview/Cloud conecta directo a SQL remoto

```
[Emergent Preview/Cloud] ──────TCP 1433────────> [SQL Server Cliente]
         │                                              │
    Internet público                           Red local cliente
    (IP dinámica Emergent)                    (firewall, NAT, DDNS)
```

**Evaluación técnica:**

| Criterio | Calificación | Justificación |
|----------|--------------|---------------|
| Estabilidad | ❌ BAJA | Depende de DDNS, firewall cliente, ISP, Hamachi |
| Seguridad | ❌ CRÍTICA | SQL expuesto a internet, credenciales en tránsito |
| Mantenimiento | ❌ ALTO | Cada cambio de IP/firewall rompe conexión |
| Escalabilidad | ❌ NULA | No escala a múltiples sucursales con redes distintas |
| Disponibilidad | ❌ BAJA | Una caída de red del cliente = tableros vacíos |

**Veredicto: NO RECOMENDADO** - Anti-patrón arquitectónico. Acopla el sistema a la infraestructura de red del cliente.

---

### ESCENARIO B: Servidor local expone API segura

```
[EDARSA HUB Cloud] <────HTTPS API────> [API Gateway Local] <────TCP 1433────> [SQL Server]
         │                                      │                                   │
    Emergent/AWS/VPS                    Red local cliente                   Red local cliente
    (IP fija, HTTPS)                    (Nginx/FastAPI local)              (sin exposición)
```

**Evaluación técnica:**

| Criterio | Calificación | Justificación |
|----------|--------------|---------------|
| Estabilidad | ✅ ALTA | API local estable, SQL nunca expuesto |
| Seguridad | ✅ ALTA | HTTPS, autenticación por token, SQL aislado |
| Mantenimiento | 🟡 MEDIO | Requiere mantener servicio local en cada sucursal |
| Escalabilidad | ✅ ALTA | Cada sucursal tiene su agente, HUB consolida |
| Disponibilidad | ✅ ALTA | Si cae red, agente local cachea y reintenta |

**Veredicto: RECOMENDADO para operaciones LIVE** - Patrón profesional tipo "Edge Computing".

---

### ESCENARIO C: Sincronización programada vía agentes

```
[EDARSA HUB Cloud] <────HTTPS POST────> [Agente Sync Local] ────SQL────> [SQL Server]
         │                                      │                              │
    Recibe datos                         Ejecuta queries              Red local cliente
    (push desde agente)                  según schedule
```

**Evaluación técnica:**

| Criterio | Calificación | Justificación |
|----------|--------------|---------------|
| Estabilidad | ✅ MUY ALTA | Desacoplado, tolerante a fallos de red |
| Seguridad | ✅ MUY ALTA | Solo salida (outbound), sin puertos abiertos |
| Mantenimiento | ✅ BAJO | Agente ligero, auto-actualizable |
| Escalabilidad | ✅ MUY ALTA | N agentes → 1 HUB, arquitectura hub-and-spoke |
| Disponibilidad | ✅ MUY ALTA | Agente almacena local, sincroniza cuando puede |

**Veredicto: RECOMENDADO para consolidados/KPIs** - Patrón profesional tipo "ETL distribuido".

---

### ESCENARIO D: VPN/Hamachi hacia servidor EDARSA controlado

```
[Servidor EDARSA] <────VPN/Hamachi────> [SQL Server Cliente]
         │                                      │
    Servidor propio                      Red local cliente
    (en oficina EDARSA o VPS)           (cliente de VPN)
```

**Evaluación técnica:**

| Criterio | Calificación | Justificación |
|----------|--------------|---------------|
| Estabilidad | 🟡 MEDIA | Depende de estabilidad de VPN/Hamachi |
| Seguridad | 🟡 MEDIA | VPN cifra, pero Hamachi tiene limitaciones |
| Mantenimiento | 🟡 MEDIO | Requiere gestión de túneles por sucursal |
| Escalabilidad | ❌ BAJA | Hamachi tiene límites, VPN requiere gestión |
| Disponibilidad | 🟡 MEDIA | Si cae túnel, se pierde acceso |

**Veredicto: ACEPTABLE como transición** - Útil para migración, no como arquitectura final.

---

## 2. ARQUITECTURA RECOMENDADA

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EDARSA HUB (Cloud)                            │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   MongoDB    │  │   FastAPI    │  │   Frontend   │                  │
│  │  (Cerebro)   │  │   Backend    │  │    React     │                  │
│  │              │  │              │  │              │                  │
│  │ - kpis_comercial │ - Tableros    │ - Dashboards  │                  │
│  │ - server_status  │ - API REST    │ - Reportes    │                  │
│  │ - dashboard_cache│ - Schedulers  │ - Auditoría   │                  │
│  │ - sync_logs      │              │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│           ▲                ▲                                            │
│           │                │                                            │
│           │    ┌───────────┴───────────┐                               │
│           │    │   API de Recepción    │                               │
│           │    │   /api/sync/push      │                               │
│           │    │   (autenticada)       │                               │
│           │    └───────────┬───────────┘                               │
└───────────┼────────────────┼────────────────────────────────────────────┘
            │                │
            │     HTTPS (outbound desde agentes)
            │                │
┌───────────┼────────────────┼────────────────────────────────────────────┐
│           │                │         RED LOCAL CLIENTE                  │
│           │                ▼                                            │
│  ┌────────┴───────────────────────────────┐                            │
│  │         EDARSA SYNC AGENT              │                            │
│  │         (Python/Go ligero)             │                            │
│  │                                        │                            │
│  │  - Scheduler local (cada 5-15 min)     │                            │
│  │  - Queries a SQL local                 │                            │
│  │  - Cache local SQLite                  │                            │
│  │  - Push a HUB cuando hay conexión      │                            │
│  │  - Reintentos automáticos              │                            │
│  │  - Logs locales                        │                            │
│  └────────────────┬───────────────────────┘                            │
│                   │                                                     │
│                   │ TCP 1433 (red local)                               │
│                   ▼                                                     │
│  ┌────────────────────────────────────────┐                            │
│  │         SQL SERVER                     │                            │
│  │    (SoftRestaurant / MPRO)             │                            │
│  │                                        │                            │
│  │  - Sin exposición a internet           │                            │
│  │  - Solo acceso desde red local         │                            │
│  │  - Credenciales solo en agente local   │                            │
│  └────────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. COMPONENTES Y RESPONSABILIDADES

### 3.1 Qué vive en EDARSA HUB (Cloud) - CEREBRO CENTRAL

| Componente | Responsabilidad |
|------------|-----------------|
| **EDARSA HUB** | Cerebro central: plataforma, modelo de datos, gobernanza |
| **MongoDB** | Soporte: cache (dashboard_cache), logs, locks, KPIs (kpis_comercial) |
| **FastAPI** | API REST, tableros, reportes, recepción de sync |
| **Schedulers** | Orquestación de trabajos, alertas, reconciliación |
| **Frontend** | Dashboards, auditoría, administración |

**ACLARACIÓN (por usuario):** MongoDB es componente de soporte, NO el cerebro. El cerebro es EDARSA HUB como plataforma integral.

**EDARSA HUB NO debe:**
- Conectar directamente a SQL remotos
- Depender de conectividad a redes de clientes
- Almacenar credenciales SQL de clientes

### 3.2 Qué vive en red local del cliente

| Componente | Responsabilidad |
|------------|-----------------|
| **EDARSA Sync Agent** | Extrae datos de SQL local, envía a HUB |
| **Cache local (SQLite)** | Almacena datos si no hay conexión a HUB |
| **Configuración** | Credenciales SQL (solo local), server_id, API key |

**El agente local:**
- Es un servicio ligero (Python/Go) que corre 24/7
- Tiene scheduler propio (cada 5-15 min para SYNC-S)
- Solo hace conexiones salientes (outbound HTTPS)
- No requiere puertos abiertos en firewall del cliente
- Puede correr en la misma máquina del SQL o en otra

---

## 4. FLUJOS DE DATOS

### 4.1 Flujo SYNC-S (Corto, cada 15 min)

```
1. Agente local ejecuta query de ventas del día
2. Agente empaqueta resultado como JSON
3. Agente hace POST a https://hub.edarsa.com/api/sync/push
4. HUB valida API key y server_id
5. HUB ejecuta UPSERT en kpis_comercial
6. HUB actualiza server_status.last_sync
7. Agente registra sync exitoso en log local
```

### 4.2 Flujo SYNC-N (Nocturno, 3:00 AM)

```
1. Agente local ejecuta queries de cierre del día
2. Agente incluye flag "periodo_cerrado: true"
3. POST a HUB con datos consolidados
4. HUB marca kpis_comercial.estado_periodo = "CERRADO"
5. HUB puede ejecutar reconciliación si hay diferencias
```

### 4.3 Flujo LIVE-C (Consulta en tiempo real)

```
Opción A (Recomendada): HUB lee de kpis_comercial más reciente
Opción B (Si se requiere): HUB hace request al agente vía API local
```

---

## 5. POR QUÉ NO CONVIENE CONEXIÓN SQL DIRECTA DESDE PREVIEW/CLOUD

| Razón | Explicación |
|-------|-------------|
| **Firewall del cliente** | Cada sucursal tiene su propia configuración de red |
| **IPs dinámicas** | DDNS y Hamachi no garantizan estabilidad |
| **Seguridad** | Exponer SQL a internet es un riesgo crítico |
| **Latencia** | Queries SQL pesadas sobre internet = lento |
| **Disponibilidad** | Si cae red del cliente, tableros se rompen |
| **Escalabilidad** | No escala a 10+ sucursales con redes distintas |
| **Mantenimiento** | Cada cambio de red requiere reconfigurar HUB |
| **Responsabilidad** | EDARSA no debe depender de IT del cliente |

---

## 6. MANEJO DE SINCRONIZACIÓN, CACHE, LOGS Y REINTENTOS

### 6.1 Sincronización

```python
# Pseudocódigo del agente local
class EdarsaSyncAgent:
    def sync_short(self):
        try:
            data = self.query_ventas_dia()
            response = self.push_to_hub(data)
            if response.status == 200:
                self.log_success("SYNC-S")
            else:
                self.queue_for_retry(data)
        except ConnectionError:
            self.save_to_local_cache(data)
            self.schedule_retry(minutes=5)
```

### 6.2 Cache (HUB)

- `kpis_comercial`: Datos consolidados por día (fuente de verdad)
- `dashboard_cache`: Cache temporal para consultas frecuentes (TTL 5 min)
- `server_status`: Estado de conexión por servidor

### 6.3 Cache (Agente Local)

- SQLite con tabla `pending_syncs`
- Si no hay conexión a HUB, acumula datos
- Cuando hay conexión, envía en orden FIFO

### 6.4 Logs

| Ubicación | Contenido |
|-----------|-----------|
| HUB: `scheduler_job_log` | Syncs recibidos, errores, estadísticas |
| HUB: `sync_reception_log` | Detalle de cada push recibido |
| Agente: archivo local | Queries ejecutadas, intentos de sync |

### 6.5 Reintentos

```
Intento 1: Inmediato
Intento 2: +5 minutos
Intento 3: +15 minutos
Intento 4: +1 hora
Intento 5+: Cada 4 horas hasta éxito
```

---

## 7. RIESGOS POR OPCIÓN

| Opción | Riesgo Principal | Probabilidad | Mitigación |
|--------|------------------|--------------|------------|
| **A: SQL directo** | Caída por firewall/red | ALTA | NO USAR |
| **B: API local** | Requiere servicio en cada sucursal | MEDIA | Docker/instalador simple |
| **C: Agentes push** | Agente deja de funcionar | BAJA | Monitoreo, auto-restart |
| **D: VPN** | Túnel inestable | MEDIA | Solo como transición |

---

## 8. SOBRE AMBIENTE DE PRODUCCIÓN

### ¿Se requiere producción separada?

**SÍ**, pero no por la razón que parece.

| Aspecto | Preview | Producción |
|---------|---------|------------|
| **Propósito** | Desarrollo, pruebas | Operación real |
| **Conectividad SQL** | NO debe tener | NO debe tener |
| **Recibe syncs** | Solo pruebas | Syncs reales de agentes |
| **Datos** | De prueba | Reales |
| **Disponibilidad** | Best-effort | 99.9% SLA |
| **Dominio** | preview.emergentagent.com | hub.edarsa.com (propio) |

### ¿Producción conectaría directo a SQL?

**NO.** La arquitectura es la misma:
- Producción recibe datos de agentes locales vía API
- Producción NO conecta a SQL remotos
- Los agentes viven en red del cliente, no en producción

---

## 9. RECOMENDACIÓN FINAL

### Arquitectura Recomendada: ESCENARIO C (Agentes Push) + B (API local opcional)

```
┌─────────────────────────────────────────────────────┐
│                   EDARSA HUB                        │
│            (AWS/VPS con dominio propio)             │
│                                                     │
│  - Recibe syncs de agentes (HTTPS POST)            │
│  - NO conecta a SQL externos                        │
│  - Consolida en MongoDB (kpis_comercial)           │
│  - Sirve tableros desde datos consolidados          │
└─────────────────────────────────────────────────────┘
                          ▲
                          │ HTTPS (outbound)
                          │
┌─────────────────────────┴───────────────────────────┐
│              EDARSA SYNC AGENT                      │
│         (1 por sucursal/servidor SQL)               │
│                                                     │
│  - Corre en red local del cliente                  │
│  - Queries SQL cada 15 min                         │
│  - Push a HUB cuando hay conexión                  │
│  - Cache local si no hay conexión                  │
│  - Sin puertos abiertos (solo salida)              │
└─────────────────────────────────────────────────────┘
```

### Justificación

1. **Desacople total** de red del cliente
2. **Seguridad** - SQL nunca expuesto, solo outbound HTTPS
3. **Escalabilidad** - N sucursales con mismo patrón
4. **Resiliencia** - Agente cachea si no hay conexión
5. **Mantenimiento** - Agente auto-actualizable vía HUB
6. **Profesional** - Patrón usado por Datadog, Elastic, Prometheus

### Próximo Paso Inmediato

1. **Diseñar el EDARSA Sync Agent** (microservicio Python ligero)
2. **Crear endpoint `/api/sync/push`** en HUB para recibir datos
3. **Documentar formato de payload** para el push
4. **Crear instalador/Docker** del agente para sucursales

---

**¿APRUEBA ESTA ARQUITECTURA PARA PROCEDER CON EL DISEÑO DEL AGENTE?**
