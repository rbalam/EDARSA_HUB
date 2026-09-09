# COA Gate 2 - Dossier Canonico de Modelo

Fecha de corte: 2026-09-08

## Estado

Gate 2A y Gate 2B fueron ejecutados por el Universal Worker en modo READ_ONLY_SQL y certificados al 100%. Produccion no fue tocada.

Evidencia vinculante:
- worker_queue/results/coa-gate2a-sql-canonical-audit-v1-20260908.json
- worker_queue/results/coa-gate2b-targeted-canonical-audit-v1-20260908.json

## Regla arquitectonica

COA no debe crear duplicados de empresas, unidades, usuarios, clientes, proveedores, colaboradores, documentos fiscales, nominas, dispersiones, recibos, pagos ni catalogos existentes. COA debe operar como capa de orquestacion administrativa y trazabilidad sobre entidades canonicas ya existentes.

La auditoria Gate 2B encontro cero objetos cuyo nombre comience con COA. Por lo tanto no existe hoy un agregado SQL COA que deba preservarse o migrarse.

## Matriz REUTILIZAR

| Dominio COA | Objeto canonico | Decision | Uso |
|---|---|---|---|
| Proveedores | dbo.Proveedor_Catalogo | REUTILIZAR | Maestro canonico de proveedor; no duplicar proveedor en COA |
| Contactos proveedor | dbo.Proveedor_Contactos | REUTILIZAR | Contactos asociados a ProveedorID |
| Documentos proveedor | dbo.Proveedor_Documentos | REUTILIZAR | Documentacion del proveedor con FK a Proveedor_Catalogo |
| Clientes | dbo.Cliente_Catalogo | REUTILIZAR | Maestro canonico de cliente |
| Empresas | dbo.Sistema_Empresas | REUTILIZAR | Empresa canonica ya referenciada por Usuario_EmpresasAsignacion |
| Usuarios | dbo.Usuario_Catalogo | REUTILIZAR | Identidad y auditoria de usuarios |
| Asignacion empresa-usuario | dbo.Usuario_EmpresasAsignacion | REUTILIZAR | Scope empresarial del usuario |
| Unidades de negocio | dbo.Unidades_Negocio | REUTILIZAR | Unidad canonica ya referenciada por Finanzas_CxP |
| Sucursales RH | dbo.RH_Cat_Sucursales | REUTILIZAR | Sucursal operativa/fiscal en procesos RH |
| CFDI/documentos fiscales | dbo.Compras_DocumentosFiscales | REUTILIZAR | Documento fiscal canonico relacionado con proveedor y sucursal |
| Relaciones fiscales | dbo.Compras_DocumentosFiscalesRelaciones | REUTILIZAR | Relaciones entre documentos fiscales |
| Comprobaciones | dbo.Finanzas_ComprobacionesDocumentos | REUTILIZAR | Vinculacion de comprobaciones con DocumentoFiscalID |
| Pagos | dbo.Finanzas_Pagos | REUTILIZAR | Pago financiero canonico cuando aplique |
| Decision de pago CxP | dbo.Finanzas_CxP_DecisionesPago | REUTILIZAR | Decision financiera canonica; COA no la sustituye |
| Cola de origen de pagos | dbo.Finanzas_CxP_PagosOrigenQueue | REUTILIZAR | Evidencia/estado de envio de pagos de origen cuando corresponda |
| Nomina | dbo.RH_Nomina | REUTILIZAR | Encabezado de nomina canonico |
| Detalle nomina | dbo.RH_Nomina_Detalle | REUTILIZAR | Conceptos por nomina |
| Dispersion nomina | dbo.RH_Nomina_Dispersion | REUTILIZAR | Dispersion por colaborador, banco, periodo y nomina |
| Recibos nomina | dbo.RH_Nomina_Recibos | REUTILIZAR | Recibos ligados a NominaID |
| Expediente colaborador | dbo.RH_Colaboradores_Expediente | REUTILIZAR | Colaborador canonico |
| Documentos colaborador | dbo.RH_Colaboradores_Documentos | REUTILIZAR | Documentacion de colaborador |
| Contratos RH | dbo.RH_Contratos | REUTILIZAR | Contrato laboral canonico |
| Flujo nomina-sucursal | dbo.RH_Flujo_Nomina_Sucursal | REUTILIZAR | Relacion de flujo, sucursal y periodo |
| Notificaciones | dbo.Operativo_Notificaciones_Log | REUTILIZAR COMO INFRAESTRUCTURA | Registro transversal de notificaciones, no como agregado COA |
| Documentos generados | dbo.Operativo_DocumentosGenerados | REUTILIZAR COMO INFRAESTRUCTURA | Documento generado transversal si el contrato funcional coincide |
| Tareas | dbo.CRM_Tareas | REUTILIZAR SOLO SI EL CONTRATO ES COMPATIBLE | No convertir automaticamente tareas CRM en expedientes COA |
| Contratos comerciales | dbo.CRM_Contratos | REUTILIZAR SOLO COMO REFERENCIA | Contratos CRM no son el motor de reglas COA |

## Objetos que NO deben reutilizarse como motor de comisiones COA

Las siguientes estructuras pertenecen a otros dominios y no constituyen reglas de comision administrativa COA:
- dbo.Finanzas_PropinasConfig
- dbo.Finanzas_ConfiguracionTPV_Sucursal
- columnas de comision en cortes, adquirentes, NetPay o TPV
- dbo.Comercial_ReglasPrecio
- dbo.Comercial_CostosMargenesConfiguracion

Sus patrones de vigencia, scope o auditoria pueden servir como referencia tecnica, pero sus porcentajes, defaults y semantica no deben heredarse.

## Motor de comisiones COA - contrato obligatorio

La comision administrativa NO es fija. El 6.5% es solamente una posible regla comercial vigente para determinados casos. No existe porcentaje default hardcodeado.

El futuro motor debe resolver reglas configurables y auditables mediante condiciones como:
- empresa
- unidad de negocio
- cliente
- proveedor
- tipo de operacion
- tipo de servicio
- contrato o convenio
- rango de monto
- moneda cuando aplique
- fecha de vigencia
- negociacion especial
- excepcion autorizada
- prioridad explicita

La base de calculo tambien debe ser configurable y declarativa. No se asumira subtotal, total, IVA incluido o excluido hasta que una regla vigente lo especifique.

La resolucion debe ser deterministica. Una regla mas especifica puede prevalecer sobre una general solo mediante prioridad/specificidad declarada y auditable.

## HUECOS_REALES comprobados

La evidencia Gate 2B retorno cero objetos COA%, por lo que los siguientes conceptos no tienen hoy un agregado SQL COA identificado y requieren modelado propio en un gate posterior:

1. Expediente administrativo COA transversal que agrupe una operacion sin duplicar el documento, proveedor, cliente, nomina o pago canonico.
2. Eventos/etapas del expediente COA para trazabilidad de recepcion, envio, validacion, timbrado, comprobacion y cierre.
3. Vinculos polimorficos controlados entre expediente COA y entidades canonicas existentes.
4. Motor de reglas de comision administrativa configurable, versionado, con vigencias, prioridad, scope y base de calculo.
5. Evidencia de regla aplicada por operacion para reproducibilidad historica del calculo.
6. Registro de excepciones y negociaciones especiales con autorizacion y motivo.
7. Enlaces de mensajeria/documentos de entrada y salida del flujo administrativo cuando no exista una entidad transversal canonica compatible.

## EXTENDER - criterio

No se deben agregar columnas COA a tablas maestras solo por conveniencia. La extension preferida sera mediante nuevas relaciones COA hacia las PK canonicas. Solo se autoriza ALTER sobre una tabla existente si una auditoria posterior demuestra que el atributo es realmente transversal al dominio propietario de esa tabla.

## Modelo minimo propuesto para el siguiente gate

El siguiente gate debe generar DDL MINIMO, aun sin ejecutarlo, para los agregados faltantes. Nombres tentativos sujetos a validacion final de convenciones SQL:

- COA_Expedientes
- COA_ExpedienteEventos
- COA_ExpedienteReferencias
- COA_ReglasComision
- COA_ReglasComisionCondiciones o representacion normalizada equivalente
- COA_ComisionAplicada
- COA_ExcepcionesRegla

No se autoriza crear una tabla COA_Proveedores, COA_Clientes, COA_Usuarios, COA_Nominas, COA_Pagos o COA_DocumentosFiscales.

## Facturacion

COA debe orquestar el expediente y la trazabilidad. Cuando el flujo corresponda a CFDI/documento fiscal existente se debe referenciar Compras_DocumentosFiscales o el objeto fiscal canonico que aplique segun el sentido de la operacion. El expediente COA no sustituye al documento fiscal.

## Nomina

COA no debe recrear nomina. Debe referenciar RH_Nomina, RH_Nomina_Dispersion y RH_Nomina_Recibos. El flujo administrativo de envio/recepcion de archivos y comprobantes se modela como trazabilidad del expediente COA.

## Estado de Gate 2

Gate 2A: CERTIFIED_READ_ONLY 100%.
Gate 2B: CERTIFIED_READ_ONLY 100%.
Gate 2C: este dossier consolida la decision arquitectonica. No contiene ni ejecuta DDL.
