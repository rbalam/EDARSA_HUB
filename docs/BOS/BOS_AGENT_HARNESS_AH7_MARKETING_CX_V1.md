# AH7 - Marketing + CX V1

AH7 incorpora Marketing/CX como consumidor gobernado del BOS Agent Harness, no como plataforma paralela.

## Customer360
`dbo.Cliente_Catalogo` permanece como customer master canonico. Customer360 es una vista/contrato compuesto sobre Cliente, CRM y RRR; no materializa una segunda copia maestra.

Fuentes V1 declaradas: Cliente_Catalogo, Cliente_Contactos, Cliente_Direcciones, Cliente_UsuariosPortal, CRM_Cuentas, CRM_PostventaEncuestas, RRR_Eventos, RRR_LedgerMovimientos, RRR_ScoreHistorial y RRR_RankingHistorial.

## Activacion
La activacion produce `edarsahub.bos-marketing-activation.v1` y exige: customer_id, Empresa/Unidad, purpose, legal basis, consentimiento, canal aprobado, scope, budget, quiet hours y no-opt-out. Es un envelope, no un send.

## Communications
AH7 no crea otro motor de mensajeria. El envelope marca `communications_executor_required=true` y `direct_send_allowed=false`. El envio real queda para el executor Communications bajo policy/gates posteriores.

## Persistencia
AH1 no encontro objetos dedicados de marketing/campaign/consent. AH7 no crea SQL por anticipado. Una persistencia futura requiere discovery/gate separado y justificacion canonica.

## Maximas
Sin backend/core nuevo, sin Mongo, sin red, sin sends reales, sin bypass RBAC, sin Production.

## Siguiente gate
AH8 Mobile debe consumir BOS mediante contratos/API y nunca convertirse en fuente canonica de clientes, inventarios, dinero ni decisiones auditables.
