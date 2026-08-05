# ADR — Capacidad instalada histórica y crecimiento ajustado

## Estado

Propuesto para EDARSAHUB V1.0/V1.2.

## Problema

Las ventas absolutas no permiten distinguir entre crecimiento orgánico y crecimiento provocado por una ampliación de capacidad instalada.

Las unidades 130MID y ORIGEN han tenido cambios de capacidad de atención. El motor analítico no deberá atribuir automáticamente sus ventas incrementales a mayor demanda, productividad o desempeño.

## Decisión

EDARSAHUB incorporará un contrato histórico, canónico y atómico de capacidad instalada por unidad de negocio y vigencia.

La capacidad instalada será una variable causal obligatoria para proyecciones, comparativos, presupuestos, backtesting y explicaciones de variaciones.

La implementación permanecerá dentro del dominio Comercial/Operaciones o en una capa de plataforma especializada. No se agregará lógica funcional al core.

## Fuentes auditadas

- dbo.Sistema_Capacidades: catálogo de capacidades técnicas del sistema; no representa capacidad física.
- dbo.Sync_Mesas: estructura operacional válida para mesas, capacidad, comensales, ocupación y rotación, pero actualmente sin registros.
- dbo.Comercial_KPIs_Diarios_v2: fuente multianual diaria desde 2016.
- dbo.Sync_Sales: fuente intradía reciente.
- dbo.Comercial_Inteligencia_VentasDetalleProducto: fuente reciente de producto y mezcla Alimentos/Bebidas.

## Contrato canónico propuesto

### Entidad principal

Nombre lógico: CapacidadInstaladaHistorial.

Campos mínimos:

- capacidad_historial_id
- unidad_negocio_id
- tipo_recurso_codigo
- recurso_id opcional
- fecha_inicio_vigencia
- fecha_fin_vigencia opcional
- cantidad_fisica
- capacidad_nominal
- capacidad_efectiva
- unidad_medida
- horario_o_turno_codigo opcional
- area_codigo opcional
- motivo_cambio_codigo
- evento_negocio_id opcional
- fuente_tipo
- fuente_referencia
- observaciones
- activo
- version
- creado_en
- creado_por
- actualizado_en
- actualizado_por

### Tipos de recurso extensibles

- MESA
- ASIENTO
- AFORO_PAX
- AREA_COMEDOR_M2
- AREA_TERRAZA_M2
- AREA_PRIVADO_M2
- BARRA_ASIENTOS
- COCINA_CUBIERTOS_HORA
- CAJAS
- HABITACIONES
- CAMAS
- LINEAS_PRODUCCION
- POSICIONES_RACK

Los tipos no se codificarán como columnas ni condicionales de dominio dentro del core.

## Reglas temporales

1. Cada registro tendrá vigencia efectiva.
2. No se sobrescribirá la historia anterior.
3. No podrán existir vigencias superpuestas para la misma unidad, tipo de recurso y recurso.
4. Fecha_fin_vigencia nula significará vigencia abierta.
5. La capacidad efectiva podrá ser menor que la nominal por cierres parciales, áreas no operativas, horarios o restricciones.
6. Toda corrección deberá conservar trazabilidad y versión.

## Métricas derivadas obligatorias

- ventas por mesa disponible
- ventas por asiento disponible
- ventas por PAX de capacidad
- PAX por asiento
- ocupación o utilización
- rotación de mesas
- ventas por hora-capacidad
- productividad por franja operativa
- crecimiento observado
- crecimiento atribuible a capacidad
- crecimiento orgánico ajustado
- efecto ticket o precio
- efecto mezcla Alimentos/Bebidas

## Descomposición analítica

El crecimiento observado deberá explicarse, cuando existan datos suficientes, mediante:

crecimiento observado = efecto capacidad + efecto utilización + efecto rotación + efecto ticket/precio + efecto mezcla + efecto demanda/calendario + residual.

No deberá presentarse el residual como causa confirmada.

## Proyecciones

Las proyecciones deberán considerar la capacidad efectiva correspondiente al periodo proyectado.

Para periodos futuros con ampliaciones aprobadas se utilizará la capacidad futura con fecha efectiva. Para escenarios hipotéticos se utilizará una capa de simulación separada y nunca se alterará la historia real.

## Mismo periodo y periodo completo

El contrato temporal canónico deberá soportar:

- MISMO_PERIODO: compara horas, días, meses o años equivalentes transcurridos.
- PERIODO_COMPLETO: proyecta el cierre total del día, mes, año o periodo especial.

La misma semántica deberá aplicarse a Comercial, Finanzas, Operaciones y RH.

## Integración con eventos del negocio

Los cambios de capacidad podrán vincularse con eventos como:

- apertura
- ampliación
- remodelación
- cierre parcial
- reapertura
- reducción de aforo
- cambio de horario
- incorporación o retiro de área
- cambio de cocina o cuello de botella operativo

## V1.0

- Documentar el contrato.
- Identificar fechas y magnitudes reales de cambios de 130MID y ORIGEN.
- Preparar puntos de extensión sin crecer el core.
- No estimar mesas o asientos a partir de ventas.
- No aplicar ajustes de capacidad sin datos auditables.

## V1.2

- Implementar catálogo histórico y administración.
- Integrar sincronización de Sync_Mesas.
- Incorporar backtesting ajustado por capacidad.
- Incorporar simulaciones de expansión.
- Incorporar explicación causal y ROI de ampliaciones.

## Prohibiciones

- No reutilizar dbo.Sistema_Capacidades para capacidad física.
- No usar Sync_Mesas como historia mientras permanezca vacía.
- No asumir cuatro personas por mesa.
- No inferir capacidad instalada únicamente desde tickets, PAX o ventas.
- No calcular ajustes de capacidad en frontend.
- No duplicar fuentes de verdad.
- No agregar un megamotor transversal al core.

## Criterio de aceptación

Una comparación o proyección que involucre periodos con distinta capacidad deberá mostrar:

1. capacidad de cada periodo;
2. cambio absoluto y porcentual de capacidad;
3. crecimiento observado;
4. crecimiento normalizado;
5. efecto atribuible a capacidad;
6. crecimiento orgánico estimado;
7. nivel de confianza y calidad de datos.
