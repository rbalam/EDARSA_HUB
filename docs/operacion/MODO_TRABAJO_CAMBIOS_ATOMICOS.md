# Máxima de Oro — Cambios Atómicos y Base Estable

**Proyecto:** EDARSAHUB
**Vigencia:** permanente
**Prioridad:** máxima arquitectónica y operativa

## 1. Principio central

EDARSAHUB se desarrolla mediante cambios pequeños, aislados, reversibles,
verificables y asociados a un único objetivo funcional.

Queda prohibido mezclar en un mismo bloque de trabajo cambios de Comercial,
Finanzas, Auth, Scheduler, navegación, auditorías, infraestructura u otros
dominios independientes.

## 2. Base estable obligatoria

Antes de iniciar cualquier objetivo:

1. Confirmar la rama autorizada.
2. Confirmar el HEAD esperado.
3. Confirmar que el workspace esté limpio.
4. Registrar un punto exacto de recuperación.
5. Detenerse ante cambios inesperados, divergencias o archivos ajenos al alcance.

Un recovery, stash o worktree es un banco de recuperación. Nunca debe aplicarse
completo sobre la base estable sin clasificación y validación archivo por archivo.

## 3. Una tarea y un alcance

Cada intervención debe declarar:

- objetivo único;
- archivos permitidos;
- archivos prohibidos;
- fuente de verdad;
- pruebas de aceptación;
- acciones expresamente no autorizadas.

No se incorporarán archivos temporales, respaldos, salidas de herramientas,
credenciales, dumps, parches históricos o artefactos de diagnóstico al commit
funcional.

## 4. Recuperar antes de reinventar

Cuando una función operaba correctamente antes de una regresión:

1. identificar la última versión funcional;
2. comparar únicamente los cambios posteriores;
3. restaurar el comportamiento validado;
4. evitar crear fórmulas, endpoints, tablas o lógica paralela;
5. modificar solo la causa demostrada de la regresión.

La versión funcional anterior prevalece sobre una nueva implementación no
demostrada.

## 5. Evidencia antes del cambio

Ningún agente debe parchar por intuición.

Antes de modificar:

- inspeccionar el código real;
- identificar el contrato vigente;
- identificar la fuente canónica;
- mostrar evidencia exacta de la causa;
- comprobar que no existe otra implementación funcional.

## 6. Validación por dominio

Cada bloque debe validarse antes de pasar al siguiente:

- backend: compilación y pruebas específicas;
- frontend: build con `yarn`;
- contratos: igualdad entre consumidores;
- RBAC: permisos efectivos;
- datos: consultas solo SELECT cuando estén autorizadas;
- funcionalidad: validación visible por el usuario.

Si una validación falla, no se amplía el alcance.

## 7. Publicación controlada

Commit, push, deploy, DDL y DML requieren autorización expresa.

Los commits deben ser:

- pequeños;
- coherentes;
- centrados en un solo objetivo;
- sin archivos ajenos;
- reversibles;
- acompañados por evidencia de validación.

## 8. Protección de funcionalidad existente

Una corrección no puede sacrificar funciones ya aprobadas.

Antes y después del cambio se deben verificar las rutas críticas relacionadas.
En Comercial, Ejecutivo e Inteligencia, una diferencia para los mismos filtros
significa que el cambio no es aceptable.

## 9. Regla de detención

El agente debe detener la modificación y reportar cuando encuentre:

- workspace sucio no esperado;
- rama o HEAD incorrectos;
- alcance que crece hacia otro dominio;
- fuentes paralelas;
- lógica duplicada;
- conflicto entre recuperación y versión vigente;
- necesidad de SQL no autorizada;
- falta de evidencia suficiente.

Detenerse de forma segura es preferible a introducir una regresión.

## 10. Flujo obligatorio

1. Auditar.
2. Delimitar.
3. Respaldar.
4. Modificar mínimamente.
5. Validar.
6. Presentar evidencia.
7. Obtener aceptación funcional.
8. Commit y push únicamente con autorización.
9. Iniciar el siguiente objetivo desde una base limpia.

Esta máxima tiene precedencia sobre la velocidad, la conveniencia y los cambios
masivos.
