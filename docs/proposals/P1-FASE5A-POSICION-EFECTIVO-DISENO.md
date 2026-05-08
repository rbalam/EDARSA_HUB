# P1-FASE5A — Posición de Efectivo (DISEÑO DETALLADO)

## PROPUESTA TÉCNICA

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-05 |
| **Versión** | 1.0 |
| **Estado** | PROPUESTA - PENDIENTE AUTORIZACIÓN |
| **Prioridad** | P1 |
| **Padre** | P1-FASE5 Dashboard Finanzas/Tesorería Consolidado |

---

## 1. ¿QUÉ SIGNIFICA "EFECTIVO DISPONIBLE" EN EDARSAHUB?

### 1.1 Definición Funcional

**Efectivo disponible** = Recursos líquidos que la empresa puede usar inmediatamente.

### 1.2 Componentes identificados

| Componente | Fuente actual | Estado |
|------------|---------------|--------|
| **Saldos bancarios** | Captura manual (tabla vacía) | ⚠️ Sin datos |
| **Efectivo en caja (pendiente depositar)** | `Finanzas_CortesCaja.TotalEfectivo WHERE DepositadoEfectivo = 0` | ✅ Datos reales |
| **Efectivo ya depositado** | `Finanzas_CortesCaja.TotalEfectivo WHERE DepositadoEfectivo = 1` | ✅ Datos (todos en 0) |
| **Depósitos registrados** | `Finanzas_Depositos` | ⚠️ Sin datos |

### 1.3 Datos reales encontrados en EDARSAHUB

**Efectivo pendiente de depositar por unidad (histórico acumulado):**

| Unidad | Cortes | Efectivo Total | Pendiente | Depositado |
|--------|--------|----------------|-----------|------------|
| 130° MÉRIDA | 726 | $36,079,474.54 | $36,079,474.54 | $0.00 |
| 130° QUERÉTARO | 719 | $87,152,852.00 | $87,152,852.00 | $0.00 |
| CIENFUEGOS | 858 | $16,688,853.17 | $16,688,853.17 | $0.00 |
| LA ESTELAR | 316 | $6,999,069.61 | $6,999,069.61 | $0.00 |
| ORIGEN | 1,303 | $45,353,496.28 | $45,353,496.28 | $0.00 |
| **TOTAL** | **3,922** | **$192,273,745.60** | **$192,273,745.60** | **$0.00** |

**Nota crítica**: Todos los cortes tienen `DepositadoEfectivo = 0`, lo que indica que el proceso de registro de depósitos no se ha implementado operativamente.

### 1.4 Conclusión sobre "Efectivo disponible"

Para **Subfase 5A**, efectivo disponible se define como:

```
efectivo_disponible = saldo_bancario_total + efectivo_pendiente_depositar
```

Donde:
- `saldo_bancario_total` = Captura manual inicial (no existe fuente automática)
- `efectivo_pendiente_depositar` = Cálculo desde `Finanzas_CortesCaja`

---

## 2. ¿CUÁL SERÁ LA FUENTE INICIAL DE DATOS?

### 2.1 Fuentes disponibles

| Fuente | Estado | Uso en 5A |
|--------|--------|-----------|
| Captura manual | Requiere UI | ✅ Para saldos bancarios iniciales |
| Importación Excel | Requiere desarrollo | ⏸️ Fase posterior |
| Carga desde estados de cuenta | Requiere parser | ⏸️ Fase posterior |
| API bancaria | No existe | ⏸️ Fase futura |
| Cálculo desde `Finanzas_CortesCaja` | ✅ Disponible | ✅ Para efectivo pendiente |
| Cálculo desde `Finanzas_Depositos` | Sin datos | ⚠️ Tabla vacía |

### 2.2 Estrategia propuesta para 5A

| Componente | Fuente | Estrategia |
|------------|--------|------------|
| Saldo bancario | Manual | UI de captura de saldo inicial por cuenta |
| Efectivo en caja | Cálculo | Query a `Finanzas_CortesCaja` |
| Depósitos pendientes | Cálculo | Query a `Finanzas_CortesCaja` WHERE `DepositadoEfectivo = 0` |

---

## 3. ¿CÓMO SE POBLARÁ `Finanzas_Cat_CuentasBancarias`?

### 3.1 Estado actual

- **Registros**: 0
- **Estructura**: Lista (ver sección 6)

### 3.2 Estrategia de población

**OPCIÓN A (Recomendada para 5A)**: Captura manual desde UI

1. Crear formulario en el Dashboard para "Alta de cuenta bancaria"
2. Usuario captura: Banco, Número de cuenta, CLABE, Alias, Empresa
3. Se guarda en `Finanzas_Cat_CuentasBancarias`
4. Requiere permiso `finanzas.cuentas_bancarias.manage`

**OPCIÓN B**: Carga masiva por script SQL (requiere autorización DBA)

```sql
INSERT INTO Finanzas_Cat_CuentasBancarias (EmpresaID, BancoID, NumeroCuenta, CLABE, Alias, Moneda)
VALUES 
(1, 2, '0123456789', '012345678901234567', 'BBVA Principal', 'MXN'),
(1, 5, '9876543210', '072345678901234567', 'Banorte Operativo', 'MXN');
```

**OPCIÓN C**: Importación Excel (fase posterior)

### 3.3 Recomendación

Para **Subfase 5A**:
- Implementar **OPCIÓN A** (UI de alta manual)
- No permitir eliminar cuentas (solo desactivar)
- Requiere al menos 1 cuenta para mostrar posición de efectivo

---

## 4. ¿POR QUÉ SE NECESITA CREAR `Finanzas_SaldosBancarios`?

### 4.1 Análisis de tablas existentes

| Tabla | ¿Guarda saldos bancarios? | Veredicto |
|-------|---------------------------|-----------|
| `Finanzas_Cat_CuentasBancarias` | NO (solo catálogo) | ❌ |
| `Finanzas_Depositos` | NO (solo depósitos) | ❌ |
| `Finanzas_Pagos` | NO (solo pagos) | ❌ |
| `Finanzas_CortesCaja` | NO (solo cortes de caja) | ❌ |
| `Finanzas_KPIs_Historico` | Tiene `flujo_efectivo_neto` pero no saldos | ❌ |

**Conclusión**: NO existe tabla equivalente para guardar saldos bancarios.

### 4.2 Propuesta de tabla `Finanzas_SaldosBancarios`

**Propósito**: Registrar el saldo de cada cuenta bancaria en una fecha específica.

**Características**:
- **Periodicidad**: Saldo diario o al menos semanal
- **Tipo de saldo**: Saldo actual capturado (no calculado)
- **Responsable**: Usuario autorizado captura o importa
- **Histórico**: Se conserva para análisis de tendencias

### 4.3 Campos propuestos

| Campo | Tipo | Descripción | PK | FK | NULL |
|-------|------|-------------|----|----|------|
| `SaldoBancarioID` | `bigint IDENTITY` | Identificador único | ✅ | - | NO |
| `CuentaBancariaID` | `int` | Referencia a cuenta | - | ✅ → `Finanzas_Cat_CuentasBancarias` | NO |
| `FechaSaldo` | `date` | Fecha del saldo | - | - | NO |
| `SaldoInicial` | `decimal(18,2)` | Saldo al inicio del día | - | - | NO |
| `SaldoFinal` | `decimal(18,2)` | Saldo al cierre del día | - | - | YES |
| `Moneda` | `varchar(3)` | MXN, USD, etc. | - | - | NO |
| `TipoCambio` | `decimal(10,4)` | Si es moneda extranjera | - | - | YES |
| `FuenteDatos` | `varchar(20)` | 'MANUAL', 'IMPORTACION', 'API' | - | - | NO |
| `Observaciones` | `varchar(500)` | Notas opcionales | - | - | YES |
| `Activo` | `bit` | Registro activo | - | - | NO |
| `UsuarioCreacionID` | `int` | Quién capturó | - | ✅ → `Usuario_Catalogo` | NO |
| `FechaCreacion` | `datetime2` | Cuándo se capturó | - | - | NO |
| `UsuarioModificacionID` | `int` | Última modificación | - | ✅ → `Usuario_Catalogo` | YES |
| `FechaModificacion` | `datetime2` | Fecha modificación | - | - | YES |

### 4.4 Índices propuestos

```sql
-- PK
PRIMARY KEY (SaldoBancarioID)

-- Índice único para evitar duplicados
UNIQUE INDEX IX_SaldoBancario_CuentaFecha 
    ON Finanzas_SaldosBancarios (CuentaBancariaID, FechaSaldo)

-- Índice para consultas por fecha
INDEX IX_SaldoBancario_Fecha 
    ON Finanzas_SaldosBancarios (FechaSaldo)
```

### 4.5 Alternativa: NO crear tabla nueva

Si no se autoriza crear tabla, el saldo bancario quedaría como:
- Campo adicional en `Finanzas_Cat_CuentasBancarias`: `SaldoActual`, `FechaSaldo`
- Limitación: Sin histórico de saldos

---

## 5. DICCIONARIO ACTUAL VERIFICADO

Se verificó en EDARSAHUB que **NO existe tabla equivalente** para saldos bancarios.

Las columnas con "Saldo" encontradas son:
- `Finanzas_KPIs_Historico.cxp_saldo_pendiente` → Saldo de CxP, no bancario
- `propinas_tpv_control.saldo_corte` → Saldo de propinas
- `RH_Prestamos.SaldoActual` → Saldo de préstamos
- `RH_Vacaciones_Saldos` → Saldos de vacaciones
- `Venta_Encabezado.SaldoPendiente` → Saldo de ventas

**Ninguna es para saldos bancarios.**

---

## 6. MODELO DE DATOS PROPUESTO PARA 5A

### 6.1 Tabla existente a usar: `Finanzas_Cat_CuentasBancarias`

| Campo | Tipo | PK | FK | NULL | Descripción |
|-------|------|----|----|------|-------------|
| `CuentaBancariaID` | `int IDENTITY` | ✅ | - | NO | Identificador |
| `EmpresaID` | `int` | - | ✅ → Empresa | YES | Empresa dueña |
| `BancoID` | `int` | - | ✅ → `Global_Cat_Bancos` | YES | Banco |
| `NumeroCuenta` | `varchar(20)` | - | - | NO | Número de cuenta |
| `CLABE` | `varchar(18)` | - | - | YES | CLABE interbancaria |
| `Alias` | `varchar(50)` | - | - | NO | Nombre corto |
| `Moneda` | `varchar(3)` | - | - | NO | Default 'MXN' |
| `EsCuentaPrincipal` | `bit` | - | - | NO | Default 0 |
| `Activo` | `bit` | - | - | NO | Default 1 |
| `FechaAlta` | `datetime2` | - | - | NO | Default GETDATE() |

### 6.2 Tabla nueva propuesta: `Finanzas_SaldosBancarios`

(Ver sección 4.3)

### 6.3 Tabla existente a consultar: `Finanzas_CortesCaja`

Campos relevantes para efectivo:
- `TotalEfectivo`
- `DepositadoEfectivo`
- `UnidadNegocioID`
- `UnidadNegocioNombre`
- `FechaCorte`

---

## 7. REGLAS DE CÁLCULO

### 7.1 Efectivo disponible

```
efectivo_disponible = saldo_bancario_total + efectivo_pendiente_depositar
```

### 7.2 Saldo bancario total

```sql
SELECT SUM(sb.SaldoFinal)
FROM Finanzas_SaldosBancarios sb
INNER JOIN Finanzas_Cat_CuentasBancarias cb ON sb.CuentaBancariaID = cb.CuentaBancariaID
WHERE sb.FechaSaldo = (
    SELECT MAX(FechaSaldo) 
    FROM Finanzas_SaldosBancarios 
    WHERE CuentaBancariaID = sb.CuentaBancariaID
)
AND cb.Activo = 1
```

### 7.3 Saldo por banco

```sql
SELECT 
    b.NombreBanco,
    SUM(sb.SaldoFinal) as SaldoTotal
FROM Finanzas_SaldosBancarios sb
INNER JOIN Finanzas_Cat_CuentasBancarias cb ON sb.CuentaBancariaID = cb.CuentaBancariaID
INNER JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
WHERE sb.FechaSaldo = @FechaConsulta
AND cb.Activo = 1
GROUP BY b.BancoID, b.NombreBanco
```

### 7.4 Saldo por cuenta

```sql
SELECT 
    cb.Alias,
    cb.NumeroCuenta,
    b.NombreCorto as Banco,
    sb.SaldoFinal,
    sb.FechaSaldo
FROM Finanzas_Cat_CuentasBancarias cb
LEFT JOIN (
    SELECT CuentaBancariaID, SaldoFinal, FechaSaldo,
           ROW_NUMBER() OVER (PARTITION BY CuentaBancariaID ORDER BY FechaSaldo DESC) as rn
    FROM Finanzas_SaldosBancarios
) sb ON cb.CuentaBancariaID = sb.CuentaBancariaID AND sb.rn = 1
INNER JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
WHERE cb.Activo = 1
```

### 7.5 Efectivo pendiente de depositar (caja)

```sql
SELECT 
    UnidadNegocioNombre,
    SUM(TotalEfectivo) as EfectivoPendiente
FROM Finanzas_CortesCaja
WHERE DepositadoEfectivo = 0
  AND Activo = 1
  AND EsDemo = 0
  AND FechaCorte BETWEEN @FechaInicio AND @FechaFin
GROUP BY UnidadNegocioID, UnidadNegocioNombre
```

### 7.6 Flujo neto preliminar (solo efectivo)

```
flujo_neto_efectivo = efectivo_depositado_periodo - retiros_periodo
```

**Nota**: En 5A solo se calcula posición, no flujo completo (eso es 5D).

---

## 8. ENDPOINTS PROPUESTOS

### 8.1 Dashboard principal de posición de efectivo

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v2/finanzas/posicion-efectivo` |
| **Parámetros** | `unidad_negocio_id` (opcional), `fecha` (opcional, default hoy) |
| **Permisos** | `finanzas.posicion.view` |
| **Fuente** | EDARSAHUB |

**Respuesta**:
```json
{
  "fecha_consulta": "2026-05-05",
  "efectivo_disponible_total": 1500000.00,
  "saldo_bancario_total": 1200000.00,
  "efectivo_pendiente_depositar": 300000.00,
  "saldos_por_banco": [
    {"banco": "BBVA", "saldo": 800000.00},
    {"banco": "Banorte", "saldo": 400000.00}
  ],
  "saldos_por_cuenta": [
    {"cuenta": "BBVA Principal", "numero": "****6789", "saldo": 800000.00, "fecha_saldo": "2026-05-05"},
    {"cuenta": "Banorte Operativo", "numero": "****3210", "saldo": 400000.00, "fecha_saldo": "2026-05-04"}
  ],
  "efectivo_por_unidad": [
    {"unidad": "CIENFUEGOS", "efectivo_pendiente": 150000.00},
    {"unidad": "LA ESTELAR", "efectivo_pendiente": 150000.00}
  ],
  "alertas": [
    {"tipo": "SALDO_DESACTUALIZADO", "mensaje": "Cuenta Banorte sin actualizar hace 2 días"}
  ],
  "_fuente": "EDARSAHUB",
  "_fecha_calculo": "2026-05-05T22:30:00"
}
```

### 8.2 CRUD de cuentas bancarias

| Ruta | Método | Propósito | Permisos |
|------|--------|-----------|----------|
| `GET /api/v2/finanzas/cuentas-bancarias` | GET | Listar cuentas | `finanzas.cuentas_bancarias.view` |
| `POST /api/v2/finanzas/cuentas-bancarias` | POST | Crear cuenta | `finanzas.cuentas_bancarias.manage` |
| `PUT /api/v2/finanzas/cuentas-bancarias/{id}` | PUT | Editar cuenta | `finanzas.cuentas_bancarias.manage` |
| `DELETE /api/v2/finanzas/cuentas-bancarias/{id}` | DELETE | Desactivar cuenta | `finanzas.cuentas_bancarias.manage` |

### 8.3 Captura de saldos

| Ruta | Método | Propósito | Permisos |
|------|--------|-----------|----------|
| `GET /api/v2/finanzas/saldos-bancarios` | GET | Listar saldos | `finanzas.saldos.view` |
| `POST /api/v2/finanzas/saldos-bancarios` | POST | Capturar saldo | `finanzas.saldos.manage` |
| `GET /api/v2/finanzas/saldos-bancarios/historial` | GET | Historial de saldos | `finanzas.saldos.view` |

---

## 9. FRONTEND PROPUESTO

### 9.1 Componentes

```
/app/frontend/src/components/finanzas-dashboard/
├── PosicionEfectivo.jsx          # Widget principal
├── TarjetasKPI.jsx               # Tarjetas de resumen
├── TablaCuentasBancarias.jsx     # Lista de cuentas
├── FormularioCuenta.jsx          # Alta/edición de cuenta
├── FormularioSaldo.jsx           # Captura de saldo
├── AlertasSaldo.jsx              # Alertas por desactualización
└── hooks/
    └── usePosicionEfectivo.js    # Hook de datos
```

### 9.2 Tarjetas KPI (5A)

| KPI | Descripción | Color |
|-----|-------------|-------|
| Efectivo Disponible Total | Suma de banco + caja | Verde/Azul |
| Saldo Bancario Total | Suma de todas las cuentas | Azul |
| Efectivo Pendiente Depositar | Caja sin depositar | Amarillo |
| Cuentas Activas | Número de cuentas | Neutro |

### 9.3 Filtros

| Filtro | Tipo | Valores |
|--------|------|---------|
| Unidad de negocio | Select | Todas / CIENFUEGOS / LA ESTELAR / etc. |
| Fecha | Date picker | Default: hoy |
| Banco | Select | Todos / BBVA / Banorte / etc. |

### 9.4 Estados vacíos

| Escenario | Mensaje |
|-----------|---------|
| Sin cuentas bancarias | "No hay cuentas bancarias configuradas. Configure al menos una cuenta para ver la posición de efectivo." + Botón [Agregar cuenta] |
| Sin saldos capturados | "Las cuentas bancarias no tienen saldos registrados. Capture el saldo actual para ver la posición de efectivo." + Botón [Capturar saldo] |
| Sin permisos | "No tiene permisos para ver la posición de efectivo." |

### 9.5 Permisos por rol

| Rol | Ver posición | Gestionar cuentas | Capturar saldos |
|-----|--------------|-------------------|-----------------|
| SuperAdministrador | ✅ | ✅ | ✅ |
| Director Finanzas | ✅ | ✅ | ✅ |
| Contador | ✅ | ❌ | ✅ |
| Tesorero | ✅ | ❌ | ✅ |
| Gerente Unidad | ✅ (solo su unidad) | ❌ | ❌ |

---

## 10. ESTRATEGIA PARA TABLAS VACÍAS

### 10.1 `Finanzas_Cat_CuentasBancarias` (0 registros)

| Estrategia | Descripción | Recomendación |
|------------|-------------|---------------|
| Carga manual por UI | Usuario agrega cuentas una a una | ✅ **Recomendado para 5A** |
| Script SQL inicial | DBA ejecuta INSERT con datos reales | Requiere autorización |
| Importación Excel | Cargar archivo con cuentas | Fase posterior |

**Para 5A**: Implementar UI de alta manual. Dashboard muestra mensaje vacío hasta que haya al menos 1 cuenta.

### 10.2 `Finanzas_Depositos` (0 registros)

**NO se usa en 5A**. Los depósitos se calculan desde `Finanzas_CortesCaja.DepositadoEfectivo`.

Esta tabla se usará en fases posteriores para conciliación.

### 10.3 `Finanzas_Pagos` (0 registros)

**NO se usa en 5A**. Esto es para egresos (Subfase 5C).

### 10.4 `RH_Nomina` (0 registros)

**NO se usa en 5A**. Esto es para obligaciones recurrentes (Subfase 5E).

---

## 11. ¿5A PERMITE CARGA MANUAL O SOLO LECTURA?

### Recomendación

**5A DEBE PERMITIR CARGA MANUAL** de:

1. **Cuentas bancarias**: Alta/edición/desactivación
2. **Saldos bancarios**: Captura diaria/semanal del saldo

**Justificación**: Sin carga manual no hay datos para mostrar. No existe fuente automática de saldos bancarios.

### Flujo propuesto

```
1. Usuario con permiso accede a Posición de Efectivo
2. Sistema detecta 0 cuentas → Muestra estado vacío + botón [Agregar cuenta]
3. Usuario agrega cuenta bancaria (BBVA, número, alias)
4. Sistema detecta cuenta sin saldo → Muestra alerta + botón [Capturar saldo]
5. Usuario captura saldo inicial ($1,200,000)
6. Sistema muestra posición de efectivo con el saldo capturado
```

---

## 12. ¿SE REQUIERE IMPORTACIÓN EXCEL EN 5A?

### Respuesta: NO para 5A

| Funcionalidad | 5A | Fase posterior |
|---------------|-----|----------------|
| Captura manual de cuentas | ✅ | - |
| Captura manual de saldos | ✅ | - |
| Importación Excel de cuentas | ❌ | 5A+ o 5B |
| Importación Excel de saldos | ❌ | 5A+ o 5B |
| Importación de estados de cuenta | ❌ | 5F o posterior |
| API bancaria | ❌ | Fase futura |

---

## 13. PRUEBAS OBLIGATORIAS

| # | Prueba | Criterio |
|---|--------|----------|
| 1 | Dashboard carga sin cuentas | Muestra estado vacío claro |
| 2 | Alta de cuenta bancaria | Se guarda correctamente en BD |
| 3 | Captura de saldo | Se guarda con fecha y usuario |
| 4 | Cálculo de efectivo disponible | Suma correcta de banco + caja |
| 5 | Filtro por unidad de negocio | Datos filtrados correctamente |
| 6 | Alerta de saldo desactualizado | Se muestra si saldo > 3 días |
| 7 | Permisos RBAC | Usuarios sin permiso no ven/editan |
| 8 | No regresión Cuadre Cortes Z | Endpoint sucursales funciona |
| 9 | No regresión CxP | No se toca |
| 10 | No regresión Comercial V2 | 5 unidades, ventas correctas |
| 11 | No regresión Tablero Ejecutivo | Sin cambios |
| 12 | Sin datos demo | Solo datos reales |

---

## 14. CRITERIOS DE ACEPTACIÓN

| # | Criterio | Obligatorio |
|---|----------|-------------|
| 1 | Endpoint `/api/v2/finanzas/posicion-efectivo` responde correctamente | ✅ |
| 2 | Widget de posición de efectivo visible en Dashboard | ✅ |
| 3 | Usuario puede agregar cuenta bancaria | ✅ |
| 4 | Usuario puede capturar saldo | ✅ |
| 5 | KPI "Efectivo Disponible Total" calculado correctamente | ✅ |
| 6 | KPI "Saldo Bancario Total" calculado correctamente | ✅ |
| 7 | KPI "Efectivo Pendiente Depositar" desde Finanzas_CortesCaja | ✅ |
| 8 | Estado vacío claro si no hay cuentas | ✅ |
| 9 | Alertas si saldo desactualizado | ✅ |
| 10 | Sin regresión en módulos existentes | ✅ |

---

## 15. ROLLBACK

### Backend

```bash
# Revertir endpoints
git checkout -- /app/backend/modules/finanzas/dashboard_v2.py
git checkout -- /app/backend/modules/finanzas/posicion_efectivo.py

# Reiniciar
sudo supervisorctl restart backend
```

### Frontend

```bash
# Revertir componentes
git checkout -- /app/frontend/src/components/finanzas-dashboard/

# Reiniciar
sudo supervisorctl restart frontend
```

### Base de datos (si se creó tabla)

```sql
-- Solo si se autoriza rollback destructivo
-- DROP TABLE Finanzas_SaldosBancarios;
```

**Tiempo estimado**: < 5 minutos

---

## 16. REGLAS DE NO REGRESIÓN

| Módulo | Verificación | Método |
|--------|--------------|--------|
| Cuadre de Cortes Z | 4 sucursales operativas | Endpoint `/api/finanzas/tesoreria/sucursales` |
| CxP | No se toca, solo lectura | No se modifica código |
| Comercial V2 | 5 unidades, ventas correctas | Endpoint V2 dashboard |
| Tablero Ejecutivo | Sin cambios | No se modifica |
| Compras | Sin cambios | No se modifica |
| Propinas TPV | Sin cambios | No se modifica |
| Auth/RBAC | Sin cambios | No se modifica |

---

## RESUMEN EJECUTIVO

### Lo que se propone para 5A

1. **Endpoint** `/api/v2/finanzas/posicion-efectivo`
2. **Widget** `PosicionEfectivo.jsx` en Dashboard Finanzas
3. **CRUD** de cuentas bancarias (UI)
4. **Captura manual** de saldos bancarios
5. **Cálculo** de efectivo pendiente desde `Finanzas_CortesCaja`

### Tablas a usar

| Tabla | Acción |
|-------|--------|
| `Finanzas_Cat_CuentasBancarias` | Poblar con UI |
| `Global_Cat_Bancos` | Solo lectura (5 registros) |
| `Finanzas_CortesCaja` | Solo lectura (3,992 registros) |

### Tabla nueva propuesta

| Tabla | Justificación |
|-------|---------------|
| `Finanzas_SaldosBancarios` | NO existe equivalente para guardar saldos por fecha |

### KPIs de 5A

1. Efectivo disponible total
2. Saldo bancario total
3. Saldo por banco
4. Saldo por cuenta
5. Efectivo pendiente depositar
6. Alertas por saldo desactualizado

### Fuera de alcance de 5A

- Importación Excel
- API bancaria
- Conciliación bancaria
- Flujo proyectado
- Egresos
- CxP (solo lectura)

---

## AUTORIZACIÓN SOLICITADA

### Para Subfase 5A:

1. ✅ Crear endpoint `/api/v2/finanzas/posicion-efectivo`
2. ✅ Crear CRUD `/api/v2/finanzas/cuentas-bancarias`
3. ✅ Crear CRUD `/api/v2/finanzas/saldos-bancarios`
4. ✅ Crear componente `PosicionEfectivo.jsx`
5. ✅ Usar `Finanzas_Cat_CuentasBancarias` (poblar por UI)
6. ✅ Consultar `Finanzas_CortesCaja` (solo lectura)
7. ❓ **¿Autorizar creación de tabla `Finanzas_SaldosBancarios` en EDARSAHUB?**

### NO se solicita:

- ❌ Modificar CxP
- ❌ Modificar Cuadre Cortes Z
- ❌ Modificar Comercial
- ❌ Modificar Tablero Ejecutivo
- ❌ Importación Excel (fase posterior)
- ❌ Crear otras tablas

---

**ESTADO**: ⏳ PROPUESTA TÉCNICA 5A - PENDIENTE AUTORIZACIÓN

*Documento: P1-FASE5A-POSICION-EFECTIVO-DISENO.md*  
*Fecha: 2026-05-05 v1.0*
