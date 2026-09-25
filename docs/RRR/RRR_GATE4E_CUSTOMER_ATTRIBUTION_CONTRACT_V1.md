# RRR Gate 4E - Customer Attribution Contract V1

## 1. Estado de evidencia
Gate4D dejo Customer360 V2 fisicamente desplegado y certificado 4/4. Gate4E R1-R4 fueron READ_ONLY. R1 demostro que `vw_RRR_ClienteActividadComercial` agrega `Venta_Encabezado` usando `FechaVenta` y `Total` sin filtro de estatus ni fecha operativa. R2 demostro que la verdad comercial vigente expone `fecha_operacion` y `ventas_sin_propina` mediante `vw_Comercial_KPIs_Diarios_v2_Runtime`; tambien mostro que `Venta_Encabezado` no tiene filas actuales. R3 encontro `Comercial_Inteligencia_VentasDetalleProducto` con aproximadamente 1.4M filas y semantica comercial rica (`fecha_operacion`, ticket/transaccion, importes, propina, cancelacion, `es_kpi_valido`) pero sin `ClienteID`. R3/R4 confirmaron que `RRR_Eventos` contiene `ClienteID`, `VentaID`, `SourceSystem`, `SourceKey` y `FechaOperacion`, pero esta vacio. R4 confirmo que `Venta_Cotizaciones`, `Venta_Encabezado`, `Venta_Pedidos`, `Venta_Remisiones` y `RRR_Eventos` tienen 0 filas como candidatos de puente.

## 2. Decision
Customer360 V2 NO debe considerarse semanticamente final para actividad comercial. No se autoriza una V3 que una clientes con ventas mediante coincidencias heuristicas de folio, fecha, importe, nombre, telefono, email o cualquier combinacion probabilistica. Primero debe existir una atribucion determinista y auditable cliente-venta.

## 3. Ownership canonico
- Cliente maestro: `dbo.Cliente_Catalogo.ClienteID`.
- Verdad comercial agregada: contratos canonicos de Comercial, con `fecha_operacion` y `ventas_sin_propina`.
- Detalle comercial candidato reutilizable: `dbo.Comercial_Inteligencia_VentasDetalleProducto`, sujeto a filtros canonicos (`activo`, `cancelado_origen`, `es_kpi_valido`) que deben certificarse antes de consumo RRR.
- Puente RRR de identidad/evento: `dbo.RRR_Eventos`; no es un segundo maestro de ventas ni un sustituto de Comercial.
- `Venta_Encabezado` no puede ser fuente runtime de Customer360 mientras permanezca sin poblacion y sin contrato de sincronizacion certificado.

## 4. Contrato minimo de atribucion
Toda actividad comercial atribuida a un cliente debe poder probar de forma determinista:
1. `ClienteID` canonico.
2. `SourceSystem` del origen comercial.
3. una clave de origen estable e idempotente (`SourceKey`) que identifique la venta/ticket/transaccion sin ambiguedad.
4. `FechaOperacion` Mexico proveniente del hecho comercial, no inferida desde `CreatedAt`.
5. referencia comercial (`VentaID` solo cuando exista mapeo real y certificado; nunca fabricarlo).
6. Empresa/Unidad/Sucursal segun relaciones oficiales cuando la fuente las provea.
7. evidencia de validez comercial y no cancelacion antes de computar actividad.
8. trazabilidad de reversa/cancelacion para retirar o compensar efectos RRR.

## 5. Regla de identidad
El mapeo cliente-venta debe originarse en captura explicita de identidad o en una relacion determinista ya registrada por el sistema fuente/adaptador. Quedan prohibidos como metodo canonico: fuzzy matching, nombre parecido, telefono parcial, email aproximado, importe+fecha, ticket cercano, IP/dispositivo o reglas no auditables.

## 6. Regla de monto
RRR no define una segunda verdad de ventas. Para KPI monetario, el valor comercial debe reconciliar con la semantica canonica `ventas_sin_propina`. Si se requiere importe por cliente/ticket, el adaptador/puente debe apuntar al hecho de detalle que permita reconstruir ese importe sin propina y excluir cancelaciones; no se copiara `ventas_sin_propina` a un nuevo maestro salvo snapshot/evento justificado y versionado.

## 7. Papel de RRR_Eventos
`RRR_Eventos` se usa como registro de atribucion/evento RRR cuando exista evidencia determinista. Debe conservar idempotencia por origen, estados de validacion/antifraude y `FechaOperacion`. No debe usarse para inventar una venta inexistente ni para sustituir el ledger comercial.

## 8. Customer360 V3 - condicion de entrada
No se autoriza modificar `vw_RRR_ClienteActividadComercial` hasta certificar un productor/adapter que genere atribuciones cliente-venta deterministas y una llave de join estable hacia el detalle comercial. Una futura V3 debera:
- partir de atribuciones certificadas;
- usar `FechaOperacion`;
- excluir hechos no validos/cancelados;
- calcular actividad por cliente sin propina;
- preservar un solo `ClienteID`;
- mantener Customer360 como read model, no tabla maestra mutable.

## 9. Siguiente gate obligatorio
Gate4E-R6 debe ser READ_ONLY y auditar el repositorio para localizar productores, adapters, endpoints, POS/Comandero/CRM o pipelines que ya capturen identidad de cliente junto con ticket/transaccion y puedan poblar `RRR_Eventos`. Debe clasificar cada candidato como REUSE / EXTEND / DO_NOT_USE. Si no existe ninguno, el siguiente paso sera disenar el adapter minimo; no crear DDL adicional por anticipado.

## 10. Prohibiciones
- No duplicar `Cliente_Catalogo`.
- No crear un nuevo maestro de ventas.
- No usar MongoDB como verdad.
- No hardcodear empresa/unidad/sucursal.
- No usar dashboards LIVE como fuente.
- No cambiar Customer360 V2 hasta completar el contrato de atribucion.
- No tocar Produccion.
