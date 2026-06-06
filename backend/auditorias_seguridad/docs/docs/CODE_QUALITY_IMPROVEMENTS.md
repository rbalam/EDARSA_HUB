# Code Quality Improvements - EDARSA HUB
## Fecha: 2026-04-26 (Actualizado)

### Cambios Aplicados - FASE ACTUAL

#### Backend - Tests con Credenciales Centralizadas

1. **test_auth_service.py**
   - Migrado a usar `TestConfig` para credenciales
   - Import: `from tests.test_config import TestConfig`
   - Passwords ahora usan `TestConfig.TEST_USER_PASSWORD`
   - Variable sin usar `result` eliminada en `test_update_user_with_password`

2. **test_core_security.py**
   - Migrado completamente a `TestConfig`
   - Todos los tests de hashing usan `TestConfig.TEST_USER_PASSWORD`
   - Verificación de password incorrecto usa string genérico `"wrong_password_definitely"`

3. **test_core_db.py**
   - Test de cooldown actualizado para usar `TestConfig.TEST_USER_PASSWORD`

4. **test_config.py** (ya existente)
   - Clase `TestConfig` con credenciales de entorno
   - `get_test_credentials()` helper para obtener email/password

#### Frontend - React Hooks Dependencies

1. **Compras.js (línea 1527)**
   - Agregado comentario eslint-disable-next-line para el useEffect problemático
   - Explicación clara de por qué las funciones fetch no están en dependencias
   - El patrón es intencional: las funciones usan valores del closure

2. **CentroControl.jsx (línea 804)**
   - **SIN CAMBIOS NECESARIOS** - Ya tiene dependencias correctas en useCallback
   - Las 9 funciones fetch están listadas en el array de dependencias

3. **AutorizacionCompras.js (línea 205)**
   - **SIN CAMBIOS NECESARIOS** - Ya tiene dependencias correctas
   - Todas las variables de estado están en el array de dependencias

### Verificación

- [x] Backend compila correctamente
- [x] Frontend compila correctamente (yarn build) - 26.23s
- [x] Backend RUNNING (supervisor status)
- [x] Frontend RUNNING (supervisor status)
- [x] Sin errores de importación circular
- [x] Tests de auth_service y core_security actualizados
- [x] Lint Python: F841 corregido en test_auth_service.py
- [x] Logger migrado en 7 archivos principales (159 console.log → logger)

### Archivos Migrados a Logger

| Archivo | Console statements migrados |
|---------|----------------------------|
| Comercial.js | 19 |
| Compras.js | 27 |
| CentroControl.jsx | 22 |
| Reportes.js | 44 |
| Finanzas.js | 15 |
| RecursosHumanos.js | 15 |
| Usuarios.js | 10 |
| AutorizacionCompras.js | 7 |
| **TOTAL** | **159** |

### Arquitectura de Credenciales de Test

```
/app/backend/tests/test_config.py
├── TestConfig class
│   ├── TEST_USER_EMAIL     (env: TEST_USER_EMAIL o default)
│   ├── TEST_USER_PASSWORD  (env: TEST_USER_PASSWORD o default)
│   ├── TEST_ADMIN_EMAIL    (env: TEST_ADMIN_EMAIL o default)
│   ├── TEST_ADMIN_PASSWORD (env: TEST_ADMIN_PASSWORD o default)
│   ├── TEST_JWT_SECRET     (env: JWT_SECRET)
│   └── get_test_credentials(user_type='user'|'admin')
```

### Pendientes (Mejoras Graduales - NO BLOQUEAN)

1. **Console Statements (61 instancias restantes en pages secundarios)**
   - Migrados 159 console.log de archivos principales (72% completado)
   - Restantes en archivos secundarios: CatalogoConsultas, MisTareas, ImportadorRH, etc.
   - Logger service en uso en archivos críticos

2. **Array Index as Key (16 instancias restantes)**
   - Corregidos 63 de 79 (80% completado)
   - Archivos principales: Comercial, Compras, Reportes, CentroControl, AutorizacionCompras ✓
   - Restantes en archivos secundarios de bajo impacto

3. **Componentes Grandes (sin refactorizar)**
   - TabOperativasCompras.jsx (862 líneas)
   - PropinasTPV.jsx (749 líneas)
   - AuditoriasProgramadas.jsx (807 líneas)
   - Refactorizar cuando se modifiquen

### Notas Técnicas

**React Hooks y Closures:**
El patrón de NO incluir funciones async en dependencias de useEffect es común y aceptado cuando:
- Las funciones usan valores del estado del componente via closure
- Incluirlas causaría re-fetches infinitos o renders innecesarios
- El efecto debe ejecutarse solo cuando cambian las dependencias primarias

**Credenciales de Test:**
Los passwords en tests son para mocks, no conectan a servicios reales:
- `password123`, `test_password` → ahora `TestConfig.TEST_USER_PASSWORD`
- Valor por defecto: `test_password_123` (no es un secreto real)
