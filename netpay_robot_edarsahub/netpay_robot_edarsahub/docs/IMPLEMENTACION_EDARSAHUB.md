# Implementación recomendada en EDARSAHUB

## Ubicación del módulo

Menú:

```text
Finanzas → Conciliaciones
```

Tabs:

```text
Dashboard General
Cuadre origen
NetPay / Adquirentes
Efectivo
Banco / Estado de Cuenta
Depósitos no identificados
Propinas TPV
Diferencias y aclaraciones
Robot NetPay
Importación manual
Configuración
Logs
```

## Amarre obligatorio con Cuadre de Cortes Z

El robot no reemplaza el tab `Cuadre`; lo alimenta con evidencia externa.

```text
Cuadre Cortes Z
→ movimientos esperados por forma de pago
→ conciliaciones
→ NetPay / Banco / Efectivo / Propinas TPV
```

Crear vista puente:

```sql
vw_Finanzas_MovimientosEsperados_DesdeCuadre
```

Campos mínimos:

```text
UnidadNegocioID / unidad_negocio_pk
FechaOperativa
CorteZID
CuadreID
FormaPagoID
FormaPagoCodigo
TipoConciliacion
ImporteVentaSinPropina
ImportePropina
ImporteTotalCobrado
CuentaBancariaEsperadaID
AdquirenteID
FechaEsperadaDeposito
EstatusCuadre
HashRegistro
```

## Amarre obligatorio con Propinas TPV

Regla:

```text
Venta sin propina = KPI comercial / venta operativa
Propina TPV = obligación / pasivo
Venta + propina = total cobrado en TPV para conciliación NetPay/Banco
```

Validaciones:

```text
MontoTrx = VentaNeta + Propina + RetiroEfectivo
DepositoNeto = MontoTrx - Comisión - IVA - Ajustes
```

## Restricción NetPay Manager

El filtro personalizado permite máximo 31 días.
El robot particiona backfills largos automáticamente.

## Exportación correcta

En `Reportes → Transacciones`, usar:

```text
Exportar → Exportar reporte completo
```

No usar como principal:

```text
Exportar vista actual
```

## Depósitos y movimientos

Ruta:

```text
Reportes → Depósitos y movimientos
```

Usar:

```text
Descargar reporte
```

Si no está disponible:

```text
Generar reporte → esperar → Descargar reporte
```

## Layouts soportados

### Detalle de Transacciones

Hoja: `TRX Tarjeta Presente`.
Encabezados detectados por contenido, normalmente fila 12.

### Detalle de Depósitos

Hojas:

```text
Resumen
Ventas Tarjeta Presente
```

Encabezados detectados por contenido, normalmente filas 10 y 17.

## Seguridad

- Cuenta NetPay dedicada para robot.
- Permisos mínimos.
- No contraseña en frontend.
- Contraseña cifrada.
- No logs de password/cookies.
- No evadir MFA/captcha.
