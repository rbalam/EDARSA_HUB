# EDARSA HUB - Checklist de cierre Save to GitHub y Deploy seguro

## Objetivo

Cerrar primero **Save to GitHub** con un snapshot canónico, reproducible y sin secretos. El deploy a Producción es una fase posterior y no debe ejecutarse mientras el predeploy gate esté rojo.

---

## FASE 1: SAVE TO GITHUB

### 1.1 Estado funcional mínimo
- [ ] Login y RBAC sin regresiones críticas.
- [ ] Dashboard y navegación principal cargan.
- [ ] No hay errores críticos de backend/frontend conocidos sin registrar.

### 1.2 Snapshot canónico
- [ ] `Edarsahub_Desarrollo` contiene todos los cambios aprobados.
- [ ] `mirror/emergent-live` converge al mismo SHA.
- [ ] Registrar el SHA final de cierre para trazabilidad y rollback.
- [ ] No mezclar cambios nuevos una vez declarado el candidato de cierre.

### 1.3 Seguridad y saneamiento
- [ ] No versionar passwords, tokens, API keys ni secretos reales.
- [ ] No documentar credenciales reales de usuarios.
- [ ] Variables sensibles se suministran únicamente por el entorno/secret store autorizado.
- [ ] Revisar artefactos temporales, caches, dumps, archivos `.env` y salidas generadas.
- [ ] Confirmar hardening y controles RBAC/SQL-first vigentes.

### 1.4 Arquitectura de datos
- [ ] SQL canónica es la fuente de verdad para dominios productivos definidos.
- [ ] No introducir MongoDB como fuente, cache o fallback productivo.
- [ ] Conexiones externas respetan repositorios/resolvers canónicos y RBAC.
- [ ] No hardcodear credenciales, unidades o endpoints sensibles cuando exista configuración canónica.

### 1.5 Gate de cierre Save to GitHub
- [ ] Verificación de diff/estado Git.
- [ ] Checks deterministas del worker y módulos modificados.
- [ ] Backend y frontend ejecutan sus gates definidos para el candidato.
- [ ] Cualquier excepción o test dependiente del entorno queda explícitamente identificado; no ocultar fallos reales.
- [ ] `Edarsahub_Produccion` permanece intacta durante esta fase.

### 1.6 Criterio de cierre
Save to GitHub solo se declara **100%** cuando:

```text
DESARROLLO_SHA == MIRROR_SHA
secretos versionados = 0 conocidos
artefactos prohibidos = 0 conocidos
cambios pendientes de guardar = 0 conocidos
gate de cierre = PASS
SHA final registrado = YES
```

---

## FASE 2: PREDEPLOY

Solo después de cerrar Save to GitHub:

- [ ] Comparar candidato contra `Edarsahub_Produccion`.
- [ ] Revisar alcance completo de commits a promover.
- [ ] Identificar y certificar requisitos de seguridad (incluidos `SEC-001`/`SEC-002` si forman parte del contrato vigente).
- [ ] Confirmar migraciones SQL, compatibilidad y rollback.
- [ ] Ejecutar quality gate predeploy completo.
- [ ] Obtener `PASS / CERTIFIED` antes de promoción.

---

## FASE 3: DEPLOY

- [ ] Promover únicamente el SHA certificado.
- [ ] Configurar variables mediante el mecanismo seguro del entorno.
- [ ] Nunca copiar secretos desde documentación o código fuente.
- [ ] Verificar URL/servicio productivo y observabilidad.

---

## FASE 4: POST-DEPLOY

- [ ] HTTPS y aplicación cargan.
- [ ] Login/RBAC funcionan.
- [ ] Navegación y dashboards principales funcionan.
- [ ] Conectividad SQL canónica operativa.
- [ ] Smoke/E2E crítico PASS.
- [ ] Sin incremento anómalo de errores 5xx.
- [ ] Registrar SHA desplegado y evidencia de cierre.

---

## Rollback

Mantener siempre el SHA productivo anterior y el procedimiento de rollback del entorno. Un rollback no debe depender de credenciales escritas en este documento.
