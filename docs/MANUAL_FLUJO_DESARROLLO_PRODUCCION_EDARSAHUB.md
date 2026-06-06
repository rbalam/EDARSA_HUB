# MANUAL DE OPERACIONES
# Flujo de Desarrollo y Producción
## EDARSAHUB - Sistema Empresarial

---

**Versión:** 1.0  
**Fecha:** Junio 2026  
**Autor:** Equipo de Desarrollo EDARSAHUB

---

## ÍNDICE

1. [Introducción](#1-introducción)
2. [Conceptos Fundamentales](#2-conceptos-fundamentales)
3. [Arquitectura de Branches](#3-arquitectura-de-branches)
4. [Configuración Correcta](#4-configuración-correcta)
5. [Flujo de Trabajo Diario](#5-flujo-de-trabajo-diario)
6. [Guía: Save to GitHub](#6-guía-save-to-github)
7. [Guía: Pull Request + Merge](#7-guía-pull-request--merge)
8. [Guía: Redeploy](#8-guía-redeploy)
9. [Escenarios y Resultados](#9-escenarios-y-resultados)
10. [Resolución de Problemas](#10-resolución-de-problemas)
11. [Checklist Rápido](#11-checklist-rápido)

---

## 1. INTRODUCCIÓN

### 1.1 Propósito del Manual

Este manual describe el proceso correcto para desarrollar, probar y publicar cambios en el sistema EDARSAHUB, asegurando que:

- Los usuarios finales **nunca** vean código con errores
- Los desarrolladores puedan trabajar libremente sin afectar producción
- Existan respaldos adecuados del código
- El proceso de publicación sea controlado y seguro

### 1.2 Problema que Resuelve

**Situación anterior (incorrecta):**
- Los cambios en desarrollo iban directo a producción
- Los usuarios veían errores diariamente
- No había proceso de revisión antes de publicar

**Situación correcta (con este manual):**
- Los cambios se prueban antes de publicar
- Los usuarios solo ven código estable
- Existe un proceso de aprobación controlado

---

## 2. CONCEPTOS FUNDAMENTALES

### 2.1 ¿Qué es un Branch (Rama)?

Un **branch** es una versión separada del código. Permite trabajar en cambios sin afectar otras versiones.

| Branch | Propósito |
|--------|-----------|
| `Edarsahub_Desarrollo` | Donde se escribe y prueba código nuevo |
| `Edarsahub_Produccion` | Código estable que ven los usuarios |

### 2.2 ¿Qué es Save to GitHub?

**Save to GitHub** es una función de Emergent (Code Server) que:
- Guarda tus cambios en GitHub
- Solo afecta el branch de **Desarrollo**
- **NO** afecta Producción
- **NO** actualiza la página web de usuarios

### 2.3 ¿Qué es Pull Request?

**Pull Request (PR)** es una solicitud en GitHub para:
- Revisar cambios antes de aprobarlos
- Pasar código de un branch a otro
- En nuestro caso: de Desarrollo → Producción

**Importante:** Un Pull Request por sí solo **NO** pasa el código. Es solo una solicitud.

### 2.4 ¿Qué es Merge?

**Merge** es la aprobación de un Pull Request:
- Confirma que los cambios son correctos
- Copia el código de Desarrollo a Producción
- Activa el deploy automático

### 2.5 ¿Qué es Deploy?

**Deploy** es publicar el código en el servidor web:
- Ocurre **automáticamente** después del Merge
- Actualiza la página web que ven los usuarios
- No requiere acción manual normalmente

### 2.6 ¿Qué es Redeploy?

**Redeploy** es volver a publicar el código:
- Se usa cuando el deploy automático falla
- **NO** cambia el código, solo lo vuelve a publicar
- Es un "Plan B", no es obligatorio siempre

---

## 3. ARQUITECTURA DE BRANCHES

### 3.1 Estructura de Branches

```
GitHub (github.com/rbalam/EDARSA_HUB)
│
├── Edarsahub_Desarrollo
│   └── Código en desarrollo (puede tener errores)
│
├── Edarsahub_Produccion
│   └── Código estable (lo que ven usuarios)
│
└── main (legacy)
    └── Branch antiguo, no usar
```

### 3.2 Flujo de Código entre Branches

```
Edarsahub_Desarrollo ──────────────────────► Edarsahub_Produccion
                         │
                         │
                    Pull Request
                         +
                       Merge
```

### 3.3 Reglas de los Branches

| Regla | Descripción |
|-------|-------------|
| Desarrollo es para trabajar | Aquí se escriben y prueban cambios |
| Producción es intocable | NUNCA editar directamente |
| Solo Merge actualiza Producción | Los cambios llegan solo por Pull Request + Merge |

---

## 4. CONFIGURACIÓN CORRECTA

### 4.1 Code Server (Emergent)

| Configuración | Valor Correcto |
|---------------|----------------|
| Branch activo | `Edarsahub_Desarrollo` |
| Propósito | Desarrollo y pruebas |

**Verificar:** En la esquina inferior izquierda debe decir `Edarsahub_Desarrollo`

### 4.2 GitHub

| Configuración | Valor Correcto |
|---------------|----------------|
| Branch de desarrollo | `Edarsahub_Desarrollo` |
| Branch de producción | `Edarsahub_Produccion` |

### 4.3 Hosting (Página Web)

| Configuración | Valor Correcto |
|---------------|----------------|
| Production Branch | `Edarsahub_Produccion` |
| Auto Deploy | Habilitado |

**Importante:** Si tu hosting usa `Edarsahub_Desarrollo` para producción, cámbialo a `Edarsahub_Produccion`.

---

## 5. FLUJO DE TRABAJO DIARIO

### 5.1 Diagrama General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  FASE 1: DESARROLLO                                                      │
│  ══════════════════                                                      │
│                                                                          │
│  1. Abrir Emergent (Code Server)                                         │
│  2. Verificar branch: Edarsahub_Desarrollo                               │
│  3. Escribir código                                                      │
│  4. Guardar cambios locales (Ctrl+S)                                     │
│  5. Probar en Preview                                                    │
│  6. Repetir hasta que funcione                                           │
│                                                                          │
│  FASE 2: RESPALDO                                                        │
│  ════════════════                                                        │
│                                                                          │
│  7. Click en "Save to GitHub"                                            │
│  8. Verificar que se guardó correctamente                                │
│                                                                          │
│  FASE 3: PUBLICACIÓN (cuando el módulo está listo)                       │
│  ════════════════════════════════════════════════                        │
│                                                                          │
│  9. Ir a GitHub.com                                                      │
│  10. Crear Pull Request                                                  │
│  11. Revisar cambios                                                     │
│  12. Click en Merge                                                      │
│  13. Esperar deploy automático (2-5 minutos)                             │
│  14. Verificar página web de producción                                  │
│                                                                          │
│  FASE 4: CONTINGENCIA (solo si hay problemas)                            │
│  ════════════════════════════════════════════                            │
│                                                                          │
│  15. Si no se actualizó: hacer Redeploy manual                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Resumen de Fases

| Fase | Cuándo | Dónde | Frecuencia |
|------|--------|-------|------------|
| Desarrollo | Todos los días | Emergent | Continuo |
| Respaldo | Al terminar cambios | Emergent → GitHub | Varias veces al día |
| Publicación | Al terminar módulo | GitHub | Cuando esté listo |
| Contingencia | Solo si falla deploy | Hosting | Rara vez |

---

## 6. GUÍA: SAVE TO GITHUB

### 6.1 ¿Qué hace Save to GitHub?

- Guarda tu código en GitHub
- Solo actualiza `Edarsahub_Desarrollo`
- **NO** afecta producción
- **NO** actualiza la página web de usuarios

### 6.2 Pasos

1. **En Emergent**, localiza el botón "Save to GitHub" (generalmente en el chat o menú)
2. **Click** en "Save to GitHub"
3. **Espera** a que termine (puede tomar unos segundos)
4. **Verifica** que no haya errores

### 6.3 ¿Cuándo usarlo?

| Situación | ¿Usar Save to GitHub? |
|-----------|----------------------|
| Terminaste una función | ✅ Sí |
| Vas a cerrar Emergent | ✅ Sí |
| Quieres respaldar tu trabajo | ✅ Sí |
| Quieres actualizar producción | ❌ No (usa Pull Request) |

### 6.4 Resultado

```
ANTES:
  GitHub/Edarsahub_Desarrollo: Código viejo

DESPUÉS:
  GitHub/Edarsahub_Desarrollo: Tu código nuevo
  GitHub/Edarsahub_Produccion: Sin cambios (igual que antes)
  Página web usuarios: Sin cambios (igual que antes)
```

---

## 7. GUÍA: PULL REQUEST + MERGE

### 7.1 ¿Qué hace Pull Request + Merge?

- Pasa código de Desarrollo a Producción
- Activa deploy automático
- Actualiza la página web de usuarios

### 7.2 Pasos Detallados

#### Paso 1: Ir a GitHub
```
Abrir navegador → github.com/rbalam/EDARSA_HUB
```

#### Paso 2: Ir a Pull Requests
```
Click en la pestaña "Pull requests" (arriba)
```

#### Paso 3: Crear nuevo Pull Request
```
Click en botón verde "New pull request"
```

#### Paso 4: Seleccionar branches
```
base: Edarsahub_Produccion    ←    compare: Edarsahub_Desarrollo
      (destino)                         (origen)
```

**Importante:** Verifica que diga:
- base: `Edarsahub_Produccion`
- compare: `Edarsahub_Desarrollo`

#### Paso 5: Crear el Pull Request
```
Click en botón verde "Create pull request"
```

#### Paso 6: Agregar descripción (opcional)
```
Escribe qué cambios incluye este Pull Request
Ejemplo: "Nuevo módulo de reportes de ventas"
```

#### Paso 7: Hacer Merge
```
Click en botón verde "Merge pull request"
```

#### Paso 8: Confirmar Merge
```
Click en "Confirm merge"
```

#### Paso 9: Verificar
```
Esperar 2-5 minutos
Abrir tu página web de producción
Verificar que los cambios estén visibles
```

### 7.3 Diagrama del Proceso

```
GitHub.com
    │
    ├── Pull requests (pestaña)
    │       │
    │       └── New pull request (botón)
    │               │
    │               ├── base: Edarsahub_Produccion
    │               └── compare: Edarsahub_Desarrollo
    │                       │
    │                       └── Create pull request
    │                               │
    │                               └── Merge pull request
    │                                       │
    │                                       └── Confirm merge
    │                                               │
    │                                               ▼
    │                                         DEPLOY
    │                                        AUTOMÁTICO
    │                                               │
    │                                               ▼
    │                                        Página Web
    │                                        Actualizada
```

### 7.4 ¿Cuándo usarlo?

| Situación | ¿Usar Pull Request + Merge? |
|-----------|----------------------------|
| Módulo terminado y probado | ✅ Sí |
| Corrección de bug urgente | ✅ Sí |
| Código a medio terminar | ❌ No |
| Solo quieres respaldar | ❌ No (usa Save to GitHub) |

---

## 8. GUÍA: REDEPLOY

### 8.1 ¿Qué hace Redeploy?

- Vuelve a publicar el código que ya está en Producción
- **NO** pasa código nuevo
- **NO** cambia nada, solo "reinicia" la publicación

### 8.2 ¿Cuándo usarlo?

| Situación | ¿Usar Redeploy? |
|-----------|-----------------|
| Deploy automático falló | ✅ Sí |
| Página no se actualizó después de Merge | ✅ Sí |
| Cambiaste variables de entorno | ✅ Sí |
| Página web está lenta o caída | ✅ Sí |
| Quieres pasar código nuevo | ❌ No (usa Pull Request) |

### 8.3 Dónde hacer Redeploy

El Redeploy se hace en tu servicio de hosting:

| Hosting | Dónde encontrar Redeploy |
|---------|--------------------------|
| Vercel | Dashboard → Proyecto → Deployments → Redeploy |
| Railway | Dashboard → Proyecto → Deployments → Redeploy |
| Render | Dashboard → Proyecto → Manual Deploy |
| Netlify | Dashboard → Proyecto → Deploys → Trigger deploy |

### 8.4 Pasos Generales

1. **Ir** a tu servicio de hosting
2. **Buscar** sección de Deployments
3. **Click** en Redeploy o similar
4. **Esperar** a que termine
5. **Verificar** que la página funcione

---

## 9. ESCENARIOS Y RESULTADOS

### 9.1 Tabla de Escenarios

| # | Acción | ¿Usuarios ven cambios? | Explicación |
|---|--------|------------------------|-------------|
| 1 | Solo Save to GitHub | ❌ NO | Solo guarda en Desarrollo |
| 2 | Solo Redeploy | ❌ NO | Producción no tiene cambios |
| 3 | Solo Pull Request (sin Merge) | ❌ NO | Falta aprobar |
| 4 | Pull Request + Merge | ✅ SÍ | Deploy automático |
| 5 | Pull Request + Merge + Redeploy | ✅ SÍ | Igual que #4, Redeploy es extra |

### 9.2 Escenario Detallado: Solo Save to GitHub

```
Acción: Save to GitHub
Resultado:
  - Edarsahub_Desarrollo: ✅ Actualizado
  - Edarsahub_Produccion: ❌ Sin cambios
  - Página web usuarios: ❌ Sin cambios
```

### 9.3 Escenario Detallado: Solo Redeploy

```
Acción: Redeploy (sin Pull Request previo)
Resultado:
  - Edarsahub_Desarrollo: (no se toca)
  - Edarsahub_Produccion: (no se toca)
  - Página web usuarios: ❌ Misma versión que antes
```

### 9.4 Escenario Detallado: Pull Request + Merge

```
Acción: Pull Request + Merge
Resultado:
  - Edarsahub_Desarrollo: (no se toca)
  - Edarsahub_Produccion: ✅ Recibe código de Desarrollo
  - Página web usuarios: ✅ Se actualiza automáticamente
```

---

## 10. RESOLUCIÓN DE PROBLEMAS

### 10.1 La página no se actualizó después del Merge

**Causas posibles:**
1. El deploy automático está procesando (esperar 5 minutos)
2. El deploy automático falló
3. Caché del navegador

**Soluciones:**
1. Esperar 5 minutos y refrescar
2. Hacer Redeploy manual
3. Limpiar caché del navegador (Ctrl+Shift+R)

### 10.2 Hay conflictos en el Pull Request

**Causa:** El mismo archivo fue modificado en ambos branches

**Solución:**
1. GitHub mostrará los conflictos
2. Elegir qué versión del código mantener
3. Marcar como resuelto
4. Completar el Merge

### 10.3 El código en producción tiene errores

**Solución inmediata:**
1. Identificar el error
2. Corregir en Desarrollo
3. Save to GitHub
4. Pull Request + Merge con la corrección

**Solución alternativa (rollback):**
1. En el hosting, buscar deployment anterior
2. Hacer rollback a versión anterior
3. Corregir el error en Desarrollo
4. Volver a hacer Pull Request + Merge

### 10.4 No puedo ver el branch de Producción en Emergent

**Explicación:** Esto es NORMAL y CORRECTO. Emergent trabaja en Desarrollo, no en Producción.

**Si necesitas ver Producción:**
1. Ir a GitHub.com
2. Cambiar al branch Edarsahub_Produccion
3. Navegar los archivos

---

## 11. CHECKLIST RÁPIDO

### 11.1 Checklist Diario (Desarrollo)

- [ ] Verificar que estoy en branch `Edarsahub_Desarrollo`
- [ ] Escribir código
- [ ] Probar en Preview
- [ ] Save to GitHub antes de cerrar

### 11.2 Checklist de Publicación

- [ ] Código probado y funcionando en Preview
- [ ] Save to GitHub realizado
- [ ] Ir a GitHub.com
- [ ] Crear Pull Request (Desarrollo → Producción)
- [ ] Revisar cambios
- [ ] Hacer Merge
- [ ] Esperar 2-5 minutos
- [ ] Verificar página web de producción
- [ ] Si no funciona: hacer Redeploy

### 11.3 Checklist de Emergencia

- [ ] Identificar el problema
- [ ] Si es código: corregir → Save → Pull Request → Merge
- [ ] Si es deploy: hacer Redeploy
- [ ] Si es grave: hacer rollback en el hosting
- [ ] Verificar que todo funcione

---

## ANEXO A: GLOSARIO

| Término | Definición |
|---------|------------|
| Branch | Versión separada del código |
| Commit | Guardar cambios con un mensaje |
| Deploy | Publicar código en el servidor |
| Merge | Aprobar y unir cambios |
| Pull Request | Solicitud para revisar y aprobar cambios |
| Redeploy | Volver a publicar el código |
| Rollback | Volver a una versión anterior |

---

## ANEXO B: URLS IMPORTANTES

| Recurso | URL |
|---------|-----|
| Repositorio GitHub | https://github.com/rbalam/EDARSA_HUB |
| Pull Requests | https://github.com/rbalam/EDARSA_HUB/pulls |
| Preview Emergent | https://erp-crm-enterprise-1.preview.emergentagent.com |

---

## ANEXO C: CONTACTO

Para dudas sobre este manual o el proceso de desarrollo, contactar al equipo de desarrollo.

---

**Fin del Manual**

*Documento generado el 3 de Junio de 2026*
