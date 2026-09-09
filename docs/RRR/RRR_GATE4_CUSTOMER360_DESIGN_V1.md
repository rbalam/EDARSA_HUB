# RRR GATE 4 - Customer 360 Design V1

## Fuente de evidencia
RRR-GATE4A-CUSTOMER360-READONLY-AUDIT-20260909: CERTIFIED_READ_ONLY, PASS, 100%, production_touched=false.

## Decisión principal
Customer 360 NO será un nuevo maestro de clientes. La raíz continúa siendo dbo.Cliente_Catalogo(ClienteID int). Customer 360 será una capa de lectura/servicio compuesta por vistas y backend.

## REUSE
- dbo.Cliente_Catalogo: identidad, razón social/nombre comercial, email/teléfono principal, sector, tamaño, riesgo, flags comerciales y fecha de interacción.
- dbo.Cliente_Contactos: contactos secundarios/principal.
- dbo.Cliente_Direcciones y Cliente_UsuariosPortal: drill-down, no columnas duplicadas en Customer360.
- dbo.Venta_Encabezado: VentaID, ClienteID, FechaVenta, Total y estado comercial.
- dbo.RRR_ScoreHistorial: último score por ClienteID.
- dbo.RRR_RankingHistorial: último rank por ClienteID.
- dbo.RRR_Eventos: actividad/engagement RRR por ClienteID.
- dbo.RRR_LedgerMovimientos: fuente de verdad de reward balance, pero no se expondrá saldo hasta certificar semántica neta de EARN/REDEEM/REVERSAL/EXPIRE/ADJUST.
- dbo.CRM_Cuentas: interoperabilidad CRM por ClienteID; no reemplaza Cliente_Catalogo.
- dbo.CRM_PostventaEncuestas: CSAT/comentarios vía CuentaID/TicketID.
- Cavas: interoperabilidad posterior sin fusionar dominios.

## CREATE mínimo
1. dbo.vw_RRR_ClienteActividadComercial: agregación por ClienteID de número de ventas, primera/última venta y ventas acumuladas desde Venta_Encabezado.
2. dbo.vw_RRR_ClienteScoreActual: último ScoreHistorial por ClienteID usando CalculadoAtUtc/ScoreID como desempate.
3. dbo.vw_RRR_ClienteRankingActual: último RankingHistorial vigente/reciente por ClienteID usando CalculadoAtUtc/RankingID como desempate.
4. dbo.vw_RRR_Customer360: composición 1 fila por ClienteID entre Cliente_Catalogo + actividad comercial + Score actual + Rank actual.

## No crear todavía
- tabla Customer360 materializada;
- tabla duplicada de cliente/contacto/dirección;
- balance mutable;
- vista de balance con signos/reversas inventados;
- snapshots de segmentación;
- copia de encuestas CRM.

## Contrato de salida vw_RRR_Customer360
- ClienteID
- CodigoCliente
- RazonSocial
- NombreComercial
- EmailPrincipal
- TelefonoPrincipal
- SectorID
- TamanoClienteID
- RiesgoCuentaID
- EsProspecto
- EsPartner
- EsCuentaEstrategica
- FechaUltimaInteraccion
- FechaPrimeraVenta
- FechaUltimaVenta
- VentasCount
- VentasTotal
- ScoreRRR
- ScoreModeloVersion
- ScoreCalculadoAtUtc
- RankCode
- RankModeloVersion
- RankCalculadoAtUtc

## Reward Balance
Customer 360 debe mostrar Reward Balance cuando exista el contrato de engine. Gate 4 no debe asumir que REVERSAL siempre suma/resta de forma fija: debe resolver el movimiento original. Se habilitará vw_RRR_ClienteBalance después de certificar la semántica de ledger en un subgate específico.

## Customer 360 API
Backend debe consultar las vistas; frontend solo pinta. Endpoint objetivo posterior: GET /api/rrr/customers/{cliente_id}/360. RBAC backend obligatorio.

## Criterio para pasar a implementación
Validar que el SQL propuesto usa únicamente columnas certificadas, que cada vista devuelve una fila por ClienteID y que no altera tablas existentes. Después ejecutar vistas en no-Production y post-auditar.
