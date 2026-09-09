# RRR - GATE 0 - Contrato Canonico V1.0

## 1. Identidad
RRR significa Resena, Recompensa y Ranking. Es el dominio transversal de Loyalty, Reputation y Customer Engagement de EDARSAHUB BOS. No es solamente un programa de puntos ni una promocion temporal.

## 2. Objetivo de negocio
Convertir interacciones identificadas del cliente en conocimiento, recurrencia, fidelizacion, advocacy y valor economico incremental medible, conectando experiencia, comportamiento, recompensas, ranking, segmentacion y activacion de marketing.

## 3. North Star
Incremental Customer Value generado por RRR. El exito no se certifica por puntos emitidos, usuarios registrados o numero bruto de resenas. Debe medirse contra resultados economicos y de comportamiento, idealmente con cohortes/control cuando aplique.

## 4. Alcance V1.0
RRR V1.0 debe contemplar contratos para: identidad de cliente canonico; resenas propietarias; eventos elegibles; motor de reglas configurable; RRR Score; Reward Balance; Ranking; ledger auditable; recompensas/beneficios; segmentacion; activacion de marketing; Customer 360; analitica; atribucion; antifraude; reversas; expiracion; consentimiento; RBAC; auditoria; integracion con Comercial/CRM y capacidad de interoperar con Cavas Corporativas sin fusionar ambos dominios.

## 5. Fuera de alcance de GATE 0
No crear tablas ni columnas. No ejecutar DDL/DML. No modificar Production. No implementar UI/API. No inventar catalogos paralelos. No fijar pesos definitivos del score. No fijar nombres comerciales definitivos de tiers. No prometer integraciones externas no auditadas. No recompensar una resena por ser positiva.

## 6. Principios de arquitectura
1. SQL-first.
2. Cliente canonico unico: RRR no crea otro maestro de clientes.
3. Reusar empresas, unidades, usuarios, clientes, ventas, productos, roles, comunicaciones y demas maestros existentes cuando la auditoria confirme su contrato.
4. Sin Mongo como fuente ni cache canonica.
5. Sin hardcodes estructurales: reglas, vigencias, scores, niveles y beneficios deben ser configurables/versionables.
6. Frontend solo representa/administra; la autoridad y reglas criticas viven en backend/SQL segun corresponda.
7. Ledger antes que saldo mutable aislado: movimientos trazables, reversables e idempotentes.
8. Eventos pasan por validacion, elegibilidad y antifraude antes de generar valor.
9. RBAC backend y principio de menor privilegio.
10. Toda accion relevante debe ser auditable.
11. Production=false salvo autorizacion expresa posterior.
12. Fecha_operacion y contratos temporales canonicos se reutilizan donde el dominio comercial lo requiera.

## 7. Modelo conceptual
Cliente canonico -> evento/experiencia -> validacion -> resena o comportamiento -> rules engine -> score/reward ledger -> ranking/beneficio -> segmentacion -> activacion -> conversion/venta -> medicion incremental.

## 8. Separacion de conceptos
RRR Score = valor de relacion/clasificacion no necesariamente redimible. Reward Balance = valor disponible sujeto a reglas. Rank = nivel derivado de reglas/score. Estos conceptos no deben colapsarse en un unico campo de puntos.

## 9. Resenas
RRR debe soportar feedback propietario vinculado, cuando sea posible, a cliente + unidad + experiencia/transaccion + fecha. Puede incluir rating, dimensiones, comentario y NPS. Las recompensas no pueden depender de que la opinion sea positiva. La publicacion hacia plataformas externas debe tratarse como flujo separado y sujeto a sus politicas.

## 10. Recompensas
Las recompensas deben incentivar comportamientos estrategicos, no limitarse a gasto monetario. Deben poder considerar visita, recurrencia, reactivacion, feedback valido, referido convertido, cross-unit, engagement u otras reglas futuras, siempre configurables y auditables.

## 11. Ranking
El ranking debe ser derivado y versionable. Conceptualmente puede incorporar recency, frequency, monetary value, engagement, loyalty y advocacy. Los pesos definitivos quedan pendientes de simulacion con datos reales y decision de negocio.

## 12. Cavas Corporativas
RRR y Cavas son dominios separados que comparten identidad canonica y pueden interoperar mediante elegibilidad/beneficios. RRR no debe duplicar ni absorber el dominio Cavas.

## 13. Marketing
RRR debe habilitar segmentacion y triggers basados en comportamiento. Casos V1 objetivo: welcome, second visit, habit/frequency, level-up, at-risk, win-back, cross-unit y candidatos a programas premium cuando exista contrato de negocio. Debe existir medicion de conversion y atribucion; evitar atribuir automaticamente ventas que hubieran ocurrido sin la accion.

## 14. Antifraude minimo
El contrato debe contemplar duplicados, tickets cancelados/revertidos, multiples clientes por evento cuando no corresponda, auto-referidos, abuso de promociones, empleados, replay de eventos e idempotencia.

## 15. KPIs V1
Identificacion de clientes, participacion, tasa de resena, NPS cuando aplique, recurrencia, segunda visita, frecuencia, reactivacion, churn, ticket, margen incremental, LTV, redemption, costo de recompensa, liability, conversion de campanas y ROI incremental.

## 16. Gobierno y privacidad
Minimizacion de datos, consentimiento y preferencias de contacto cuando aplique, trazabilidad de cambios de reglas, segregacion de permisos, auditoria de movimientos y capacidad de explicar por que un cliente obtuvo/perdio score, balance, rank o beneficio.

## 17. Criterios de salida GATE 0
PASS solamente si: contrato canonico persistido; objetivo y alcance definidos; exclusiones definidas; principios de no duplicacion y SQL-first explicitos; Score/Balance/Rank separados; ledger y antifraude incluidos; integracion conceptual con Cliente/Comercial/CRM/Cavas definida; KPIs definidos; Production no tocada; no hubo DDL/DML; y existe plan exacto para GATE 1 READ_ONLY.

## 18. GATE 1 autorizado por este contrato
El siguiente gate sera exclusivamente READ_ONLY. Debe auditar el SQL y codigo real para producir matriz REUSE/EXTEND/CREATE/DO_NOT_TOUCH sobre clientes canonicos, CRM/contactos, ventas/tickets, empresas/unidades, productos, usuarios/RBAC, campanas/comunicaciones/notificaciones, Cavas, auditoria/configuracion y cualquier estructura ya existente relacionada con loyalty, puntos, rewards, reviews, NPS, referrals, rankings o segmentacion. No se autoriza crear schema hasta cerrar esa auditoria.

## 19. Definicion de 100% de RRR V1.0
100% significa alcance V1.0 implementado, integrado, probado y certificado con evidencia. No significa fin evolutivo de RRR.
