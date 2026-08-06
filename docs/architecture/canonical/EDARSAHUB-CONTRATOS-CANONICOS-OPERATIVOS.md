# EDARSAHUB — Contratos canónicos operativos

## Estado

Contrato operativo obligatorio para EDARSAHUB V1.0 y base de evolución para V1.2.

## Objetivo

Evitar auditorías repetitivas, hardcodes, fuentes paralelas, conexiones resueltas localmente y decisiones distintas entre módulos.

Este documento define cómo deben consumirse las fuentes y servicios canónicos de EDARSAHUB.

No sustituye a la base de datos ni se convierte en una fuente paralela de verdad.

La fuente de verdad permanece en SQL EDARSAHUB y en sus servicios y resolvers canónicos.

## Máxima obligatoria

Nunca adivines.

Primero se consulta este contrato.

Solo se realiza una nueva auditoría cuando:

1. el caso no está cubierto;
2. existe evidencia concreta de divergencia;
3. cambió el esquema;
4. cambió el contrato de un servicio canónico;
5. existe una migración formal;
6. se alcanzó un hito de auditoría integral;
7. una validación fail-closed detectó inconsistencia.

No se repetirán auditorías para redescubrir información ya confirmada y documentada aquí.

---

# 1. Unidades de negocio canónicas

La fuente canónica de unidades es:

`dbo.Unidades_Negocio`

Los módulos no deben mantener catálogos locales, listas hardcodeadas ni equivalencias propias.

## Unidades vigentes confirmadas

| Código canónico | Nombre canónico | Familia POS | Servidor canónico | Sucursal canónica |
|---|---|---|---|---|
| `130MID` | `130° MERIDA` | `SOFTRESTAURANT_PRO` | `a5547321-1139-4d2b-9d53-182ca737b6b6` | `DEFAULT` |
| `130QRO` | `130° QUERETARO` | `MPRO` | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | `0021` |
| `CIENFUEGOS` | `CIENFUEGOS` | `SOFTRESTAURANT_PRO` | `6d053c22-523e-48c0-b72b-96081e2d781b` | `DEFAULT` |
| `ESTELAR` | `LA ESTELAR` | `SOFTRESTAURANT_PRO` | `a5ff0e25-f029-43db-b634-d4ac814c904f` | `DEFAULT` |
| `ORIGEN` | `ORIGEN` | `MPRO` | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | `0023` |

## Regla de consumo

Los identificadores anteriores son una fotografía documental del contrato confirmado.

El código no debe hardcodearlos.

El código debe resolverlos desde:

- `dbo.Unidades_Negocio`;
- `dbo.Servidores_Conexiones`;
- `list_pos_runtime_contexts()`;
- componentes canónicos de alcance y filtros.

---

# 2. Servidores y conexiones

La fuente canónica de servidores es:

`dbo.Servidores_Conexiones`

La relación canónica es:

`Unidades_Negocio.server_id -> Servidores_Conexiones.id`

El resolver obligatorio para contexto POS es:

`backend/core/connections/pos_runtime_resolver.py`

Función canónica:

`list_pos_runtime_contexts()`

## Prohibiciones

- No consultar `Servidores_Conexiones` directamente desde jobs de dominio cuando exista resolver canónico.
- No descifrar credenciales dentro de jobs, rutas o servicios funcionales.
- No imprimir host, usuario, contraseña, token o cadena completa de conexión.
- No crear resolvers paralelos.
- No mantener alias locales como `id AS ServerID` para ocultar contratos incorrectos.
- No usar MongoDB para resolver unidades, servidores o conexiones.
- No usar conexiones POS live desde dashboards o endpoints de usuario.
- No hardcodear servidores, puertos, bases, usuarios o sistemas POS.

---

# 3. Contrato canónico POS por unidad

La unidad de iteración es:

`PosRuntimeContext`

No se debe iterar primero por una lista genérica de servidores y luego reconstruir unidades o sucursales.

## SoftRestaurant

Para unidades `SOFTRESTAURANT_PRO`:

- el contexto canónico identifica unidad y servidor;
- la sucursal comercial canónica confirmada es `DEFAULT`;
- debe resolverse desde la fuente comercial canónica del servidor;
- no debe inventarse desde nombre, código o posición;
- si un servidor SoftRestaurant presenta más de una sucursal comercial, el proceso debe detenerse fail-closed hasta resolver el contrato.

## ManagementPro

Para unidades MPRO:

- usar `context.server_id`;
- usar `context.sucursal_origen_id`;
- conservar ceros iniciales;
- `130QRO` utiliza `0021`;
- `ORIGEN` utiliza `0023`;
- no convertir el identificador canónico a entero para consultas o persistencia.

---

# 4. Filtros canónicos

Todos los módulos, dashboards, reportes, exports, drilldowns y satélites deben consumir un objeto de filtros canónico.

Los filtros no deben recalcularse de manera independiente en frontend, rutas, repositorios o jobs.

## Dimensiones mínimas

- empresa;
- unidad de negocio;
- grupo de unidades;
- sucursal;
- sistema de origen;
- fecha operativa;
- periodo operativo;
- zona horaria efectiva;
- turno o franja;
- estado;
- alcance organizacional;
- usuario y permisos efectivos.

## Modos de comparación

El contrato debe soportar dos modos explícitos:

### Mismo periodo

Compara exactamente el mismo tramo transcurrido:

- mismas horas;
- mismos días;
- mismos meses;
- mismos años parciales;
- mismo avance operativo.

### Periodo completo

Proyecta o compara contra el cierre completo:

- día operativo completo;
- mes completo;
- año completo;
- presupuesto completo;
- periodo completo equivalente.

Esta regla aplica transversalmente a:

- Comercial;
- Finanzas;
- Compras;
- Gastos;
- Operaciones;
- Recursos Humanos;
- Nóminas;
- Impuestos;
- Comisiones;
- presupuestos;
- proyecciones;
- comparativos;
- backtesting.

---

# 5. Fechas canónicas

## Comercial

La fecha principal es:

`fecha_operativa`

No se debe sustituir por `CAST(fecha AS date)` ni por medianoche civil sin validar horarios operativos.

## Compras, gastos, finanzas y contabilidad

Deben conservarse las fechas fuente inmutables, por ejemplo:

- fecha_documento;
- fecha_factura;
- fecha_recepcion;
- fecha_vencimiento;
- fecha_pago;
- fecha_contable;
- fecha_bancaria.

Además, debe existir atribución operativa canónica mediante:

- `fecha_operativa`; o
- `periodo_operativo`.

Las fechas fuente nunca deben sobrescribirse.

---

# 6. Zona horaria

La zona horaria debe resolverse con identificadores IANA.

Precedencia:

1. unidad de negocio;
2. empresa;
3. plataforma.

No se permiten offsets fijos como fuente de configuración.

Todos los jobs, cierres, fechas operativas, reportes y schedulers deben utilizar la zona efectiva de la unidad.

---

# 7. Usuarios, roles, permisos y RBAC

Toda autorización debe consumir el RBAC canónico existente.

## Reglas

- `SUPERADMIN >= ADMINISTRADOR`.
- Ningún módulo admin puede otorgar más acceso a ADMINISTRADOR que a SUPERADMIN.
- No hardcodear nombres de roles en frontend, rutas o servicios.
- No crear comprobaciones paralelas de permisos.
- No duplicar usuarios, roles, permisos o alcances.
- No usar MongoDB como fuente nueva o primaria.
- Los permisos deben aplicarse también a acciones, no solo a menús.
- Toda denegación debe ser fail-closed.
- Las solicitudes de permisos deben integrarse con el flujo contextual de autorizaciones.
- Una misma persona no debe aprobar dos veces etapas equivalentes cuando tiene permisos acumulados.
- El alcance por empresa, unidad y objeto debe resolverse de forma canónica.

## Flujo contextual

Un usuario bloqueado podrá solicitar autorización desde:

- menú;
- tab;
- botón;
- tabla;
- card;
- acción contextual;
- documento;
- operación sensible.

La autorización debe conservar:

- solicitante;
- aprobador;
- permiso solicitado;
- objeto;
- alcance;
- motivo;
- estado;
- fecha;
- valor anterior;
- valor nuevo;
- bitácora.

---

# 8. Fuentes comerciales canónicas

## KPI diario

Fuente canónica confirmada:

`dbo.Comercial_KPIs_Diarios_v2`

Para valores visibles de venta:

`ventas_sin_propina`

Regla vigente:

- SoftRestaurant: `ventas_total` incluye propina.
- MPRO: `ventas_total = ventas_sin_propina`.
- Para reportes visibles se usa `ventas_sin_propina`.

## Detalle comercial

Fuente confirmada:

`dbo.Comercial_Inteligencia_VentasDetalleProducto`

Contiene:

- fecha_operacion;
- fecha_hora;
- ticket;
- producto;
- familia;
- importe;
- PAX;
- unidad;
- sistema de origen.

## Venta del día

Es una excepción operacional controlada.

No debe utilizarse en Inteligencia Comercial histórica.

Objetivo arquitectónico:

- eliminar conexiones live directas;
- sincronizar a fuente canónica frecuente;
- aceptar aproximadamente cinco minutos de retraso cuando preserve consistencia.

---

# 9. Capacidad instalada

La capacidad instalada es una variable causal obligatoria.

No debe inferirse únicamente desde:

- ventas;
- tickets;
- PAX;
- crecimiento histórico.

Debe modelarse por vigencia y considerar:

- mesas;
- asientos;
- aforo;
- áreas;
- horarios;
- capacidad nominal;
- capacidad efectiva;
- fecha efectiva de cambio.

Las proyecciones deben separar:

- efecto capacidad;
- utilización;
- rotación;
- ticket o precio;
- mezcla;
- demanda;
- calendario;
- residual.

El residual no debe presentarse como causa confirmada.

---

# 10. Regla de reutilización

Antes de crear cualquier:

- tabla;
- columna;
- vista;
- job;
- sync;
- servicio;
- endpoint;
- resolver;
- helper;
- archivo;
- contrato;
- catálogo;

debe revisarse este documento y los componentes canónicos registrados.

Orden obligatorio:

1. reutilizar;
2. componer;
3. extender;
4. refactorizar mínimamente;
5. crear solo ante brecha demostrada.

Toda excepción debe quedar sustentada con evidencia y documentada.

---

# 11. Core mínimo

No crecer más `backend/core` en la medida de lo posible.

Toda capacidad nueva debe implementarse primero:

1. en el dominio propietario; o
2. en una capa de plataforma y composición.

Solo pueden elevarse a core:

- contratos mínimos;
- protocolos estables;
- tipos verdaderamente transversales;
- validaciones puras;
- mecanismos sin lógica específica de dominio.

La refactorización amplia de estructuras existentes queda preferentemente para V1.2.

V1.0 permanece enfocada en estabilidad y operación.

---

# 12. Performance y mantenibilidad

## Reglas obligatorias

- No crear archivos monolíticos.
- No duplicar consultas pesadas.
- No repetir resolución de contexto por registro.
- Resolver contexto una vez por unidad o lote.
- Evitar consultas N+1.
- Usar operaciones por lotes.
- Aplicar índices según filtros reales.
- No ejecutar escaneos completos sin justificación.
- Limitar columnas recuperadas.
- Mantener archivos pequeños y especializados.
- Mantener contratos tipados.
- Medir duración, filas procesadas y errores.
- Preparar pruebas de carga.
- Revisar cache y procesos asíncronos.
- No mezclar cálculo de negocio en frontend.

---

## Transformaciones estructurales de código

Las modificaciones estructurales de código deben realizarse con herramientas conscientes de la sintaxis del lenguaje.

Para Python se utilizarán, según corresponda:

- AST para análisis estructural;
- CST o herramienta equivalente cuando deba preservarse formato y comentarios;
- rangos exactos obtenidos desde el parser;
- transformaciones por nodos;
- validación posterior del árbol sintáctico;
- compilación;
- pruebas unitarias o de contrato;
- revisión del diff completo.

Queda prohibido utilizar expresiones regulares para:

- modificar firmas de métodos o funciones;
- eliminar o mover métodos;
- sustituir bloques anidados;
- alterar indentación estructural;
- reconstruir bucles, condicionales o manejadores de excepciones;
- cambiar flujo de ejecución;
- transformar imports de forma estructural;
- aplicar refactorizaciones sobre código Python.

Las expresiones regulares solo podrán utilizarse para búsquedas simples, validación de formatos controlados o extracción no estructural cuando no interpreten la sintaxis ni modifiquen el flujo del programa.

Una coincidencia textual no constituye evidencia suficiente para aplicar una transformación estructural.

Ante cualquier diferencia entre el patrón esperado y el archivo real, el proceso deberá detenerse fail-closed y auditar el árbol sintáctico exacto antes de continuar.

# 13. Uso obligatorio de este documento

Antes de iniciar una auditoría técnica sobre:

- unidades;
- servidores;
- conexiones;
- sucursales;
- filtros;
- fechas;
- usuarios;
- roles;
- permisos;
- RBAC;
- fuentes comerciales;
- capacidad instalada;

se debe consultar primero este documento.

No se repetirá una auditoría ya cubierta salvo evidencia concreta de cambio o contradicción.

Cuando cambie un contrato canónico, este documento debe actualizarse en el mismo cambio o commit que formaliza la nueva decisión.

## Resultado esperado

EDARSAHUB debe operar con:

- una sola fuente de verdad;
- contratos previsibles;
- menos auditorías repetidas;
- menos hardcodes;
- menor acoplamiento;
- mejor performance;
- cambios más pequeños;
- menor riesgo;
- trazabilidad completa.
