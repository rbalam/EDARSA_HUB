# EDARSAHUB BOS — Primary Industries Gate 1 Canonical Domain Design

Estado: CANONICAL DESIGN — NO IMPLEMENTATION

## 1. Principios obligatorios

- EDARSAHUB SQL Server es el cerebro y fuente canonica.
- No Mongo como fuente operativa o de verdad.
- No LIVE para dashboards/reportes administrativos.
- No hardcodear IDs de empresa, unidad, especie, raza, reglas geneticas, reglas contractuales, porcentajes ni aliases.
- No crecer backend/core salvo infraestructura genuinamente transversal.
- No duplicar clientes, proveedores, productos, inventarios, documentos, Finanzas, CRM, RH, RBAC ni workflows.
- Toda capacidad nueva debe pasar por REUTILIZAR / EXTENDER / HUECO_REAL antes de materializar estructuras.
- Este documento define dominio y ownership; no autoriza DDL, DML, endpoints, frontend ni cambios productivos.

## 2. Evidencia Gate 0 y Gate 1 R1

### 2.1 Gate 0B — SQL delta certificado

Gate 0B certifico:
- cero objetos SQL especificos para animal, equino, reproduccion, genetica, semen, inseminacion, embrion, gestacion, pedigree o genealogia;
- seis objetos contractuales relacionados:
  - CavasCorporativas_Convenios
  - CavasCorporativas_ConvenioUnidades
  - CRM_Cat_EstatusContrato
  - CRM_Contratos
  - RH_Cat_TiposContrato
  - RH_Contratos
- infraestructura reusable existente para:
  - Cliente_Catalogo
  - Proveedor_Catalogo
  - Producto_Catalogo
  - Inventario_Almacenes
  - Inventario_Existencias
  - Inventario_Movimientos
  - ActivoFijo_Activos
  - Gobierno_Documento
  - Finanzas_CuentasPorPagar
  - Usuario_Autorizaciones

### 2.2 Gate 1 R1 — repository contract audit

R1 escaneo backend/modules, backend/database y docs:
- scanned_files=1119
- matched_files=96
- skipped_sensitive=344
- status=PASS
- files_changed=[]
- production_touched=false

R1 encontro referencias documentales y contractuales existentes, pero no una implementacion Primary de reproduction/genetics ni partnerships/contracts. Coincidencias aisladas como "semen" en documentos Hospitality no constituyen ownership funcional del dominio.

## 3. Bounded context: Primary Reproduction & Genetics

### 3.1 Owns

Este bounded context posee exclusivamente la semantica biologica y reproductiva de animales:

- Animal
- Especie
- Raza
- Linaje / genealogia / pedigree
- Rol reproductivo
- Semental
- Hembra reproductora
- Donante
- Receptora
- Evento reproductivo
- Monta natural
- Inseminacion artificial
- Transferencia embrionaria
- Diagnostico reproductivo
- Gestacion
- Parto
- Camada / nacimiento
- Descendencia
- Material genetico
- Lote genetico
- Pajuela / dosis
- Embrion
- Calidad y certificacion genetica
- Resultado reproductivo

### 3.2 No owns

No posee:
- inventario fisico canonico;
- producto maestro;
- cliente/proveedor maestro;
- documentos canonicos;
- activos/maquinaria;
- CxP/CxC/pagos/contabilidad;
- contratos laborales;
- contratos comerciales CRM;
- RBAC;
- scheduler.

## 4. Bounded context: Primary Partnerships & Contracts

### 4.1 Owns

Posee la semantica productiva de relaciones entre partes cuando no es laboral ni CRM:

- AcuerdoProductivo
- ParteAcuerdo
- RolParte
- UnidadProductivaRelacionada
- Aportacion
- ReglaParticipacion
- ReglaCosto
- ReglaIngreso
- ReglaProduccion
- ReglaLiquidacion
- PeriodoLiquidacion
- LiquidacionProductiva
- EvidenciaLiquidacion
- EstadoAcuerdo

Casos cubiertos:
- aparceria
- medieria
- arrendamiento rural
- ganado a porcentaje
- engorda por contrato
- agricultura por contrato
- produccion por contrato
- integracion avicola
- integracion porcina
- custodia/pension animal
- uso compartido de maquinaria
- asociaciones productivas
- cooperativas
- cesion o uso de sementales
- acuerdos de genetica/reproduccion

### 4.2 No owns

No posee:
- RH_Contratos;
- CRM_Contratos;
- CavasCorporativas_Convenios;
- contabilidad;
- CxP/CxC;
- pagos;
- terceros maestros;
- inventarios;
- documentos;
- RBAC.

## 5. Clasificacion canonica de capacidades

| Capacidad | Clasificacion | Ownership |
|---|---|---|
| Animal | HUECO_REAL | Primary Reproduction & Genetics |
| Especie | HUECO_REAL | Primary Reproduction & Genetics |
| Raza | HUECO_REAL | Primary Reproduction & Genetics |
| Pedigree/genealogia | HUECO_REAL | Primary Reproduction & Genetics |
| Reproduccion animal | HUECO_REAL | Primary Reproduction & Genetics |
| Semen/pajuelas | HUECO_REAL semantico + REUTILIZAR inventario | Primary + Inventarios |
| Embriones | HUECO_REAL semantico + REUTILIZAR inventario cuando exista existencia fisica | Primary + Inventarios |
| Inseminacion | HUECO_REAL | Primary Reproduction & Genetics |
| Gestacion/parto | HUECO_REAL | Primary Reproduction & Genetics |
| Aparceria | HUECO_REAL | Primary Partnerships & Contracts |
| Medieria | HUECO_REAL | Primary Partnerships & Contracts |
| Arrendamiento rural | HUECO_REAL | Primary Partnerships & Contracts |
| Participacion productiva | HUECO_REAL | Primary Partnerships & Contracts |
| Liquidacion productiva | HUECO_REAL semantico + EXTENDER integracion Finanzas | Primary + Finanzas |
| Contratos laborales | REUTILIZAR | RH |
| Contratos comerciales | EXTENDER por referencia, no apropiarse | CRM |
| Convenios Cavas | REUTILIZAR solo en Cavas | Cavas Corporativas |
| Clientes | REUTILIZAR | CRM/Comercial |
| Proveedores | REUTILIZAR | Proveedores |
| Productos | REUTILIZAR | Catalogo/Comercial |
| Inventarios | REUTILIZAR | Inventarios |
| Activos/maquinaria | REUTILIZAR | Activos |
| Documentos | REUTILIZAR | Gobierno/Documentos |
| CxP/CxC/pagos | REUTILIZAR | Finanzas |
| Autorizaciones/RBAC | REUTILIZAR | Sistema |

## 6. Modelo conceptual de Reproduction & Genetics

### 6.1 Animal

Animal representa el individuo biologico trazable.

Relaciones conceptuales:
- empresa/unidad mediante IDs canonicos;
- especie;
- raza;
- sexo;
- fecha de nacimiento;
- identificadores externos;
- estado biologico/productivo;
- unidad productiva;
- padre/madre cuando aplique;
- documentos/evidencias por referencia canonica.

No se modela como Producto_Catalogo.

### 6.2 Especie y Raza

Catalogos del dominio Primary, configurables y no hardcodeados.

Regla:
- una raza pertenece a una especie;
- no asumir bovino/equino/porcino en codigo;
- permitir extensibilidad a ovinos, caprinos, aves, acuicultura u otras especies.

### 6.3 Genealogia

La genealogia debe expresarse mediante relaciones Animal -> progenitores y/o registros genealogicos certificados.

Debe permitir:
- pedigree conocido/desconocido;
- fuente de evidencia;
- grado de certeza;
- documento certificador;
- linajes externos sin duplicar terceros.

### 6.4 Material genetico

MaterialGenetico contiene identidad biologica y procedencia.

Ejemplos:
- semen;
- pajuela/dosis;
- embrion;
- otro material reproductivo configurable.

MaterialGenetico NO sustituye Inventario_Existencias.

Separacion obligatoria:

MaterialGenetico
-> LoteGenetico
-> referencia a Producto_Catalogo cuando exista item comercializable
-> referencia a Inventario_Existencias / Inventario_Movimientos para stock fisico
-> referencia a Animal donante/origen

### 6.5 Servicio reproductivo

EventoReproductivo modela:
- tipo de servicio;
- hembra;
- semental o material genetico;
- tecnico/colaborador;
- fecha operativa;
- unidad productiva;
- metodo;
- diagnostico;
- resultado;
- evidencias;
- autorizaciones cuando aplique.

## 7. Lifecycle reproductivo conceptual

Animal reproductor:
ACTIVO -> EN_SERVICIO -> RETIRADO

Material genetico:
GENERADO/RECIBIDO -> CALIFICADO -> DISPONIBLE -> RESERVADO -> UTILIZADO/VENDIDO -> AGOTADO/DESECHADO

Servicio reproductivo:
PROGRAMADO -> REALIZADO -> EN_SEGUIMIENTO -> CONFIRMADO_NO_CONFIRMADO -> CERRADO

Gestacion:
SOSPECHA -> CONFIRMADA -> EN_CURSO -> PARTO/ABORTO/PERDIDA -> CERRADA

Nacimiento:
REGISTRADO -> IDENTIFICADO -> VINCULADO_GENEALOGICAMENTE

Estados exactos se parametrizan en Gate 2; no hardcodearlos en implementacion.

## 8. Modelo conceptual de Partnerships & Contracts

### 8.1 AcuerdoProductivo

Representa la relacion productiva operativa.

Puede referenciar opcionalmente:
- CRM_Contratos.ContratoID si existe contrato comercial asociado;
- Gobierno_Documento para instrumento firmado;
- Cliente_Catalogo o Proveedor_Catalogo segun naturaleza de la parte;
- empresa/unidad canonica;
- unidad productiva.

No reutilizar RH_Contratos.

### 8.2 ParteAcuerdo

Una parte puede ser:
- empresa interna;
- cliente;
- proveedor;
- productor;
- propietario;
- persona/organizacion reconocida por el modelo canonico de terceros.

No crear catalogo paralelo de terceros si el tercero ya existe.

### 8.3 Aportaciones

Tipos configurables:
- tierra;
- animales;
- capital;
- insumos;
- maquinaria;
- mano de obra;
- infraestructura;
- genetica;
- servicios.

Cada aportacion debe poder tener:
- periodo;
- unidad;
- cantidad;
- valuacion;
- moneda canonica;
- evidencia;
- responsable.

### 8.4 Reglas de participacion

Debe soportar:
- porcentaje fijo;
- porcentaje por produccion;
- porcentaje por utilidad;
- renta fija;
- renta fija + variable;
- reparto por unidades fisicas;
- formulas parametrizadas.

Prohibido hardcodear porcentajes en codigo.

### 8.5 Liquidacion productiva

Primary calcula la base productiva:
- produccion atribuible;
- costos atribuibles;
- aportaciones;
- reglas contractuales;
- resultado de reparto.

Finanzas conserva ownership de:
- obligacion financiera;
- CxP/CxC;
- pago;
- contabilizacion;
- moneda/tipo de cambio canonico;
- impuestos.

Primary emite la base de liquidacion; Finanzas materializa la obligacion economica segun contrato canonico.

## 9. Integracion con Inventarios

Reproduction & Genetics reutiliza:
- Inventario_Almacenes
- Inventario_Existencias
- Inventario_Movimientos
- Inventario_MovimientosDetalle
- Inventario_TipoMovimiento

No crear:
- Primary_Inventario
- Genetics_Inventario
- Semen_Existencias paralelo
- Embrion_Existencias paralelo

La identidad genetica y la existencia fisica son conceptos distintos enlazados.

## 10. Integracion con Activos

Maquinaria, tanques criogenicos, equipos, remolques, vehiculos y equipos de reproduccion deben reutilizar ActivoFijo_Activos y capacidades relacionadas.

Primary solo agrega contexto operacional:
- actividad;
- unidad productiva;
- evento reproductivo;
- consumo/uso;
- evidencia.

## 11. Integracion con Documentos

Reutilizar Gobierno_Documento / Version / Movimiento para:
- pedigree;
- certificado sanitario;
- certificado genetico;
- contrato firmado;
- convenio;
- autorizacion;
- evidencia de laboratorio.

Primary conserva referencias, no repositorio documental paralelo.

## 12. Integracion con RBAC y autorizaciones

Reutilizar Usuario_Autorizaciones y capacidades RBAC existentes.

Casos candidatos a autorizacion:
- venta/cesion de material genetico;
- uso de semental restringido;
- anulacion de evento reproductivo;
- ajuste de genealogia certificada;
- cierre de liquidacion contractual;
- excepcion contractual;
- movimiento de inventario sensible.

Gate 2 debe mapear acciones/permisos existentes antes de crear nuevos codigos.

## 13. Integracion con Logistics

Primary debe emitir necesidades logisticas, no crear TMS paralelo.

Casos:
- traslado de animales;
- semen;
- embriones;
- cadena de frio/criogenia;
- recepcion;
- cuarentena;
- documentos sanitarios;
- POD/evidencia;
- GPS.

La logistica debe referenciar IDs canonicos del objeto biologico/material y del inventario cuando aplique.

## 14. Eventos de dominio conceptuales

Solo contrato conceptual para evaluar en Gate 2:

- PRIMARY_ANIMAL_REGISTERED
- PRIMARY_ANIMAL_TRANSFERRED
- PRIMARY_GENETIC_MATERIAL_CREATED
- PRIMARY_GENETIC_MATERIAL_RECEIVED
- PRIMARY_REPRODUCTIVE_SERVICE_SCHEDULED
- PRIMARY_REPRODUCTIVE_SERVICE_COMPLETED
- PRIMARY_PREGNANCY_CONFIRMED
- PRIMARY_BIRTH_RECORDED
- PRIMARY_PRODUCTIVE_AGREEMENT_CREATED
- PRIMARY_PRODUCTIVE_AGREEMENT_APPROVED
- PRIMARY_PRODUCTIVE_SETTLEMENT_CALCULATED
- PRIMARY_PRODUCTIVE_SETTLEMENT_APPROVED

No crear event bus ni scheduler paralelo.

## 15. Fronteras que no deben cruzarse

- Primary no modifica ownership de CRM_Contratos.
- Primary no modifica ownership de RH_Contratos.
- Primary no modifica ownership de CavasCorporativas_Convenios.
- Primary no duplica terceros.
- Primary no duplica inventarios.
- Primary no duplica documentos.
- Primary no duplica Finanzas.
- Primary no duplica RBAC.
- Primary no crea scheduler paralelo.
- Primary no usa Mongo como verdad.
- Primary no introduce LIVE en reporting administrativo.
- Primary no hardcodea especies, razas, porcentajes ni reglas.

## 16. Gate de salida

Gate 1 queda semanticamente completo cuando este documento sea materializado sin cambios fuera de docs/ARCHITECTURE y pase git_diff_check.

El siguiente Gate permitido sera Gate 2 — Data & Integration Architecture.

Gate 2 debera:
- definir esquemas conceptuales y relaciones fisicas propuestas;
- decidir FK fisica vs referencia logica canonica;
- definir integracion con Inventarios, Finanzas, CRM, Documentos, Activos, RBAC y Logistics;
- definir idempotencia, auditoria, fechas operativas, timezone, moneda e idioma;
- decidir catalogos configurables;
- no ejecutar DDL ni DML.
