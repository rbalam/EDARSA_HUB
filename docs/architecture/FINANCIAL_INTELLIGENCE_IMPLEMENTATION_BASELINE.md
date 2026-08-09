# EDARSAHUB Financial Intelligence — Línea base de implementación

**Estado:** Diseño técnico inicial basado en auditoría del repositorio  
**Rama base auditada:** `Edarsahub_Desarrollo`  
**Commit base:** `6f82b39fead3a73667241e88e580f0ea8faf51e8`

## 1. Objetivo

Incorporar en EDARSAHUB una capacidad transversal de inteligencia financiera, cultura financiera y simulación de inversión para socios, accionistas y colaboradores, manteniendo separación estricta entre datos corporativos y portafolios personales.

## 2. Alcance inicial seguro

La primera entrega debe limitarse a:

- educación y cultura financiera;
- agregación de noticias y datos públicos verificables;
- análisis macroeconómico, geopolítico, sectorial y empresarial;
- watchlists personales;
- portafolios simulados;
- paper trading;
- alertas informativas;
- escenarios y explicaciones de riesgo;
- trazabilidad completa de fuentes y decisiones del modelo.

Quedan fuera de esta fase:

- custodia de fondos;
- recepción de depósitos;
- ejecución real de órdenes;
- administración automática de capital de terceros;
- recomendaciones individualizadas reguladas;
- almacenamiento de claves privadas;
- almacenamiento directo de secretos de brokers fuera del gestor canónico de secretos.

## 3. Hallazgos de arquitectura

### 3.1 RBAC existente

El repositorio dispone de un motor RBAC central en `backend/core/rbac` con dependencias FastAPI, servicio, repositorio, esquemas y auditoría.

Para este módulo se debe usar autorización SQL explícita y fail-closed. No se debe usar el flujo general que conserva bypass legacy para roles administrativos.

### 3.2 Separación de dominio

No se debe ampliar `backend/core` con lógica financiera de negocio. El módulo debe vivir en un dominio propietario y consumir únicamente contratos transversales estables.

Ruta propuesta, sujeta a validar patrones exactos adicionales antes de crear archivos ejecutables:

```text
backend/modules/financial_intelligence/
  routes/
  services/
  repositories/
  schemas/
  providers/
  risk/
  education/
  simulations/
  audit/
```

### 3.3 SQL como fuente única

Toda persistencia productiva debe usar EDARSAHUB SQL. Se prohíben MongoDB, stubs de Mongo como nueva dependencia, archivos como fuente productiva, caches paralelos no canónicos y conexiones live directas desde endpoints de usuario.

### 3.4 Scheduler

La ingesta y actualización de fuentes debe integrarse al scheduler central existente. No deben crearse cron scripts aislados ni procesos paralelos sin registro, estado, reintentos y bitácora canónica.

## 4. Subdominios

1. **Market Intelligence**: eventos macroeconómicos, geopolíticos, climáticos, energéticos, agrícolas, tecnológicos y empresariales.
2. **Source Registry**: catálogo de fuentes, confiabilidad, licencia, frecuencia, región y vigencia.
3. **Entity Resolution**: países, gobiernos, empresas, instrumentos, monedas, materias primas y sectores.
4. **Event Graph**: relaciones causales entre eventos, sectores y activos.
5. **Scenario Engine**: escenarios optimista, base, adverso y extremo.
6. **Risk Engine**: límites, concentración, liquidez, volatilidad, correlación y drawdown.
7. **Financial Education**: rutas educativas, evaluaciones y simulaciones.
8. **Personal Workspace**: watchlists, portafolios simulados y preferencias privadas.
9. **Audit and Explainability**: fuentes, versión de modelo, fecha, confianza, hipótesis e invalidadores.

## 5. Privacidad

Los datos personales de inversión deben quedar separados de la información laboral y corporativa.

Reglas mínimas:

- privacidad por defecto;
- acceso exclusivo del propietario salvo consentimiento explícito y auditable;
- ningún uso para evaluación laboral;
- cifrado de datos sensibles;
- exportación y eliminación controladas;
- soporte técnico sin acceso automático al contenido;
- alcance `OWNER` obligatorio para portafolios personales.

## 6. Matriz RBAC inicial

Los códigos definitivos deben incorporarse al catálogo canónico existente, sin tablas ni fuentes paralelas.

```text
FIN_INTELLIGENCE_VER
FIN_INTELLIGENCE_CONFIGURAR
FIN_FUENTES_VER
FIN_FUENTES_GESTIONAR
FIN_EVENTOS_VER
FIN_EVENTOS_VALIDAR
FIN_ANALISIS_GENERAR
FIN_ANALISIS_VER
FIN_ESCENARIOS_GENERAR
FIN_RIESGO_VER
FIN_RIESGO_CONFIGURAR
FIN_EDUCACION_VER
FIN_EDUCACION_GESTIONAR
FIN_WATCHLIST_PERSONAL_GESTIONAR
FIN_PORTAFOLIO_SIMULADO_GESTIONAR
FIN_PAPER_TRADING_USAR
FIN_ALERTAS_PERSONALES_GESTIONAR
FIN_MODELOS_CONFIGURAR
FIN_AUDITORIA_VER
FIN_CUMPLIMIENTO_REVISAR
FIN_KILL_SWITCH_EJECUTAR
```

Cada endpoint debe usar permiso explícito, contexto efectivo de usuario y alcance. El frontend solo deriva visibilidad; la validación obligatoria permanece en backend.

## 7. Flujo de datos

```text
Fuente externa
  -> conector registrado
  -> captura cruda inmutable
  -> normalización
  -> validación y deduplicación
  -> resolución de entidades
  -> clasificación del evento
  -> relaciones causales
  -> escenarios
  -> evaluación de riesgo
  -> salida explicable
  -> alerta o simulación
```

## 8. Reglas de calidad

- Nunca adivinar datos faltantes.
- Mostrar fecha, zona horaria y vigencia de cada dato.
- Diferenciar hecho, estimación, opinión y rumor.
- Confirmar eventos críticos con fuentes independientes.
- No generar señales ejecutables con datos inconsistentes.
- Registrar versión del modelo y parámetros.
- Conservar evidencia reproducible.
- Medir posteriormente el resultado de cada hipótesis.
- No garantizar rendimientos.

## 9. Fases

### Fase 0 — Auditoría y contratos

- completar inventario de tablas, permisos, scheduler, conectores, bitácoras y componentes frontend reutilizables;
- identificar fuente canónica para catálogos y secretos;
- validar patrón de migraciones;
- documentar cumplimiento y privacidad.

### Fase 1 — Cultura financiera e inteligencia informativa

- catálogo de fuentes;
- ingesta de eventos;
- feed validado;
- explicaciones educativas;
- watchlists;
- alertas informativas.

### Fase 2 — Simulación

- portafolios simulados;
- paper trading;
- benchmarks;
- escenarios;
- backtesting con prevención de sesgos.

### Fase 3 — Personalización controlada

- perfil de riesgo;
- propuestas no ejecutables;
- revisión jurídica y de cumplimiento.

### Fase 4 — Integración con intermediarios

Solo después de dictamen jurídico, seguridad, contratos, pruebas de resiliencia y aprobación formal.

## 10. Criterios de aceptación de la siguiente entrega

Antes de crear tablas o endpoints se debe entregar:

1. inventario exacto de estructuras reutilizables;
2. mapa de permisos y alcances existentes;
3. patrón real de migración SQL;
4. punto de registro de routers;
5. punto de registro de scheduler/jobs;
6. patrón frontend de menú y rutas;
7. decisión documentada sobre privacidad de portafolios personales;
8. modelo de fuentes y licenciamiento;
9. análisis regulatorio aplicable;
10. plan de pruebas y rollback.

## 11. Restricciones obligatorias

- No MongoDB.
- No hardcodes de negocio.
- No conexiones live desde dashboards de usuario.
- No duplicar tablas, jobs, catálogos ni servicios existentes.
- No agregar menú, tab, botón, endpoint o proceso sin RBAC y auditoría.
- No tocar producción desde esta línea base.
- Todo cambio posterior debe ser incremental, reversible y validado.
