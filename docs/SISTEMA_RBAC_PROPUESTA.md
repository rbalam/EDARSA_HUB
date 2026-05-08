# SISTEMA RBAC - EDARSA HUB
## Roles, Permisos y Alcances Multi-nivel

**Fecha:** Diciembre 2025  
**Estado:** PROPUESTA TÉCNICA - Pendiente Aprobación  
**Autor:** Arquitecto de Software Senior

---

## 1. RESUMEN EJECUTIVO

### Objetivo
Implementar un sistema de control de acceso granular que soporte:

| Nivel | Descripción | Ejemplo |
|-------|-------------|---------|
| **GLOBAL** | Todas las empresas y sucursales | SuperAdmin |
| **GRUPO** | Solo empresas de un grupo específico | Auditor de "Restaurantes Premium" |
| **EMPRESA** | Solo una empresa específica | Contador de MPRO |
| **SUCURSAL** | Solo sucursales específicas | Operador de Cienfuegos |

### Principios de Diseño
1. **Granularidad**: Permisos atómicos (VIEW ≠ EDIT ≠ CONFIRM ≠ AUTHORIZE)
2. **Herencia**: Global > Grupo > Empresa > Sucursal
3. **Auditable**: Toda acción queda registrada con usuario, rol, permiso y alcance
4. **No invasivo**: Se integra sin romper funcionalidad existente
5. **SQL Server**: Toda persistencia en EDARSA HUB (MongoDB solo caché)

---

## 2. MODELO DE DATOS

### 2.1 Diagrama de Entidades

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     roles       │     │    permisos     │     │  rol_permisos   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │     │ rol_id       FK │
│ codigo          │     │ codigo          │     │ permiso_id   FK │
│ nombre          │     │ modulo          │     │ activo          │
│ descripcion     │     │ accion          │     └────────┬────────┘
│ nivel_jerarquia │     │ descripcion     │              │
│ activo          │     │ nivel_riesgo    │              │
└────────┬────────┘     │ activo          │              │
         │              └─────────────────┘              │
         │                                               │
         ▼                                               │
┌─────────────────┐                                      │
│  usuarios_roles │◄─────────────────────────────────────┘
├─────────────────┤
│ usuario_id   FK │     ┌─────────────────┐
│ rol_id       FK │     │ grupos_empresas │
│ fecha_asignacion│     ├─────────────────┤
│ asignado_por    │     │ id              │
│ activo          │     │ codigo          │
└────────┬────────┘     │ nombre          │
         │              │ descripcion     │
         │              │ activo          │
         ▼              └────────┬────────┘
┌─────────────────┐              │
│ usuarios_alcance│              ▼
├─────────────────┤     ┌─────────────────┐
│ id              │     │ grupo_empresas  │
│ usuario_id   FK │     ├─────────────────┤
│ tipo_alcance    │     │ grupo_id     FK │
│ grupo_id     FK │     │ empresa_id   FK │
│ empresa_id   FK │     │ activo          │
│ sucursal_id  FK │     └─────────────────┘
│ activo          │
└─────────────────┘
```

### 2.2 Scripts SQL

```sql
-- ============================================================================
-- EDARSA HUB - SISTEMA RBAC (Roles, Permisos, Alcances)
-- ============================================================================

-- ============================================
-- TABLA: roles
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'roles')
BEGIN
    CREATE TABLE roles (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        codigo              NVARCHAR(50)        NOT NULL UNIQUE,
        nombre              NVARCHAR(100)       NOT NULL,
        descripcion         NVARCHAR(500)       NULL,
        nivel_jerarquia     INT                 NOT NULL DEFAULT 100,
            -- 1 = SuperAdmin (máximo)
            -- 10 = Admin Finanzas
            -- 20 = Tesorero / CxP
            -- 50 = Auditor
            -- 100 = Operador (mínimo)
        es_sistema          BIT                 NOT NULL DEFAULT 0,
            -- 1 = Rol del sistema (no editable)
        activo              BIT                 NOT NULL DEFAULT 1,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE(),
        updated_at          DATETIME            NULL
    );

    -- Roles base del sistema
    INSERT INTO roles (codigo, nombre, descripcion, nivel_jerarquia, es_sistema) VALUES
    ('SUPERADMIN', 'SuperAdmin', 'Control total del sistema', 1, 1),
    ('ADMIN_FIN', 'Administrador Finanzas', 'Gestión completa del módulo Finanzas', 10, 1),
    ('TESORERO', 'Tesorero', 'Operaciones de tesorería y cuadres', 20, 1),
    ('CXP', 'Cuentas por Pagar', 'Gestión de facturas y pagos', 20, 1),
    ('AUDITOR', 'Auditor', 'Solo lectura en todos los módulos', 50, 1),
    ('OP_SUCURSAL', 'Operador de Sucursal', 'Operaciones limitadas a su sucursal', 100, 1);

    PRINT 'Tabla roles creada con datos iniciales';
END
GO

-- ============================================
-- TABLA: permisos
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'permisos')
BEGIN
    CREATE TABLE permisos (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        codigo              NVARCHAR(100)       NOT NULL UNIQUE,
        modulo              NVARCHAR(50)        NOT NULL,
        accion              NVARCHAR(20)        NOT NULL,
            -- VIEW, EDIT, CONFIRM, AUTHORIZE
        nombre              NVARCHAR(200)       NOT NULL,
        descripcion         NVARCHAR(500)       NULL,
        nivel_riesgo        NVARCHAR(20)        NULL,
            -- BAJO, MEDIO, ALTO, CRITICO
        requiere_alcance    BIT                 NOT NULL DEFAULT 1,
            -- 1 = Se evalúa alcance (empresa/sucursal)
            -- 0 = Permiso global (ej: ver dashboard)
        activo              BIT                 NOT NULL DEFAULT 1,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE()
    );

    -- Permisos de FINANZAS
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('FINANZAS_TAB_VER', 'FINANZAS', 'VIEW', 'Ver tab Finanzas', 'BAJO', 0);

    -- Permisos de TESORERÍA
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('TESORERIA_VER', 'TESORERIA', 'VIEW', 'Ver módulo Tesorería', 'BAJO', 1),
    ('TESORERIA_INICIAR_CUADRE', 'TESORERIA', 'EDIT', 'Iniciar cuadre de caja', 'MEDIO', 1),
    ('TESORERIA_GUARDAR_CUADRE', 'TESORERIA', 'CONFIRM', 'Guardar cuadre de caja', 'ALTO', 1),
    ('TESORERIA_AJUSTAR_CUADRE', 'TESORERIA', 'EDIT', 'Ajustar cuadre existente', 'ALTO', 1),
    ('TESORERIA_AUTORIZAR_DESCUADRE', 'TESORERIA', 'AUTHORIZE', 'Autorizar cuadre con descuadre', 'CRITICO', 1);

    -- Permisos de PROPINAS
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('PROPINAS_VER', 'PROPINAS', 'VIEW', 'Ver módulo Propinas', 'BAJO', 1),
    ('PROPINAS_CUADRE_VER', 'PROPINAS', 'VIEW', 'Ver cuadre de propinas', 'BAJO', 1),
    ('PROPINAS_CUADRE_CONFIRMAR', 'PROPINAS', 'CONFIRM', 'Confirmar pago de propinas', 'ALTO', 1),
    ('PROPINAS_CONFIG_VER', 'PROPINAS', 'VIEW', 'Ver configuración de propinas', 'BAJO', 0),
    ('PROPINAS_CONFIG_EDITAR', 'PROPINAS', 'EDIT', 'Editar % de descuento propinas', 'ALTO', 0);

    -- Permisos de CXP
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('CXP_VER', 'CXP', 'VIEW', 'Ver módulo Cuentas por Pagar', 'BAJO', 1),
    ('CXP_FILTRAR', 'CXP', 'VIEW', 'Filtrar facturas', 'BAJO', 1),
    ('CXP_MARCAR_PAGAR', 'CXP', 'EDIT', 'Marcar factura para pago', 'MEDIO', 1),
    ('CXP_PAGO_MASIVO', 'CXP', 'EDIT', 'Marcar todas vencidas (pago masivo)', 'ALTO', 1),
    ('CXP_AUTORIZAR_PAGO', 'CXP', 'AUTHORIZE', 'Autorizar pago de facturas', 'CRITICO', 1),
    ('CXP_EXPORTAR', 'CXP', 'VIEW', 'Exportar datos de CxP', 'MEDIO', 1);

    -- Permisos de PRESUPUESTOS
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('PRESUPUESTO_VER', 'PRESUPUESTOS', 'VIEW', 'Ver presupuestos', 'BAJO', 1),
    ('PRESUPUESTO_CREAR', 'PRESUPUESTOS', 'EDIT', 'Crear presupuesto', 'ALTO', 1),
    ('PRESUPUESTO_EDITAR', 'PRESUPUESTOS', 'EDIT', 'Editar presupuesto', 'ALTO', 1),
    ('PRESUPUESTO_ELIMINAR', 'PRESUPUESTOS', 'AUTHORIZE', 'Eliminar presupuesto', 'CRITICO', 1);

    -- Permisos de DASHBOARD / REPORTES
    INSERT INTO permisos (codigo, modulo, accion, nombre, nivel_riesgo, requiere_alcance) VALUES
    ('DASHBOARD_FINANZAS_VER', 'DASHBOARD', 'VIEW', 'Ver dashboard de Finanzas', 'BAJO', 0),
    ('REPORTES_FINANZAS_VER', 'REPORTES', 'VIEW', 'Ver reportes financieros', 'BAJO', 1),
    ('REPORTES_FINANZAS_EXPORTAR', 'REPORTES', 'VIEW', 'Exportar reportes financieros', 'MEDIO', 1);

    PRINT 'Tabla permisos creada con datos iniciales';
END
GO

-- ============================================
-- TABLA: rol_permisos (Relación M:N)
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'rol_permisos')
BEGIN
    CREATE TABLE rol_permisos (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        rol_id              INT                 NOT NULL,
        permiso_id          INT                 NOT NULL,
        activo              BIT                 NOT NULL DEFAULT 1,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT FK_rol_permisos_rol FOREIGN KEY (rol_id) REFERENCES roles(id),
        CONSTRAINT FK_rol_permisos_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id),
        CONSTRAINT UQ_rol_permiso UNIQUE (rol_id, permiso_id)
    );

    -- Asignar permisos a SuperAdmin (TODOS)
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'SUPERADMIN';

    -- Asignar permisos a Admin Finanzas
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'ADMIN_FIN'
      AND p.codigo NOT IN ('PRESUPUESTO_ELIMINAR');

    -- Asignar permisos a Tesorero
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'TESORERO'
      AND p.codigo IN (
          'FINANZAS_TAB_VER',
          'TESORERIA_VER', 'TESORERIA_INICIAR_CUADRE', 'TESORERIA_GUARDAR_CUADRE', 'TESORERIA_AJUSTAR_CUADRE',
          'PROPINAS_VER', 'PROPINAS_CUADRE_VER', 'PROPINAS_CUADRE_CONFIRMAR', 'PROPINAS_CONFIG_VER',
          'CXP_VER', 'CXP_FILTRAR', 'CXP_MARCAR_PAGAR',
          'DASHBOARD_FINANZAS_VER', 'REPORTES_FINANZAS_VER'
      );

    -- Asignar permisos a CxP
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'CXP'
      AND p.codigo IN (
          'FINANZAS_TAB_VER',
          'CXP_VER', 'CXP_FILTRAR', 'CXP_MARCAR_PAGAR', 'CXP_PAGO_MASIVO', 'CXP_EXPORTAR',
          'DASHBOARD_FINANZAS_VER'
      );

    -- Asignar permisos a Auditor (solo VIEW)
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'AUDITOR'
      AND p.accion = 'VIEW';

    -- Asignar permisos a Operador de Sucursal
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.codigo = 'OP_SUCURSAL'
      AND p.codigo IN (
          'FINANZAS_TAB_VER',
          'TESORERIA_VER', 'TESORERIA_INICIAR_CUADRE',
          'PROPINAS_VER', 'PROPINAS_CUADRE_VER',
          'CXP_VER', 'CXP_FILTRAR'
      );

    PRINT 'Tabla rol_permisos creada con asignaciones iniciales';
END
GO

-- ============================================
-- TABLA: grupos_empresas
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'grupos_empresas')
BEGIN
    CREATE TABLE grupos_empresas (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        codigo              NVARCHAR(50)        NOT NULL UNIQUE,
        nombre              NVARCHAR(100)       NOT NULL,
        descripcion         NVARCHAR(500)       NULL,
        activo              BIT                 NOT NULL DEFAULT 1,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE(),
        updated_at          DATETIME            NULL
    );

    -- Grupos de ejemplo
    INSERT INTO grupos_empresas (codigo, nombre, descripcion) VALUES
    ('SOFTREST', 'SoftRestaurant', 'Empresas que usan SoftRestaurant'),
    ('MPRO', 'MPRO', 'Empresas que usan MPRO'),
    ('PREMIUM', 'Restaurantes Premium', 'Restaurantes de alta gama');

    PRINT 'Tabla grupos_empresas creada con datos iniciales';
END
GO

-- ============================================
-- TABLA: grupo_empresas_detalle (Relación Grupo-Empresa)
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'grupo_empresas_detalle')
BEGIN
    CREATE TABLE grupo_empresas_detalle (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        grupo_id            INT                 NOT NULL,
        empresa_id          NVARCHAR(50)        NOT NULL,
            -- Referencia a tabla de empresas existente
        activo              BIT                 NOT NULL DEFAULT 1,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT FK_grupo_empresas_grupo FOREIGN KEY (grupo_id) REFERENCES grupos_empresas(id),
        CONSTRAINT UQ_grupo_empresa UNIQUE (grupo_id, empresa_id)
    );

    PRINT 'Tabla grupo_empresas_detalle creada';
END
GO

-- ============================================
-- TABLA: usuarios_roles
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuarios_roles')
BEGIN
    CREATE TABLE usuarios_roles (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        usuario_id          NVARCHAR(50)        NOT NULL,
            -- Referencia a tabla users de MongoDB (sincronizado)
        rol_id              INT                 NOT NULL,
        fecha_asignacion    DATETIME            NOT NULL DEFAULT GETDATE(),
        asignado_por        NVARCHAR(50)        NULL,
        fecha_expiracion    DATETIME            NULL,
            -- NULL = Sin expiración
        activo              BIT                 NOT NULL DEFAULT 1,
        
        CONSTRAINT FK_usuarios_roles_rol FOREIGN KEY (rol_id) REFERENCES roles(id),
        CONSTRAINT UQ_usuario_rol UNIQUE (usuario_id, rol_id)
    );

    CREATE INDEX IX_usuarios_roles_usuario ON usuarios_roles (usuario_id, activo);

    PRINT 'Tabla usuarios_roles creada';
END
GO

-- ============================================
-- TABLA: usuarios_alcance
-- ============================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuarios_alcance')
BEGIN
    CREATE TABLE usuarios_alcance (
        id                  INT IDENTITY(1,1)   PRIMARY KEY,
        usuario_id          NVARCHAR(50)        NOT NULL,
        tipo_alcance        NVARCHAR(20)        NOT NULL,
            -- GLOBAL, GRUPO, EMPRESA, SUCURSAL
        grupo_id            INT                 NULL,
            -- Solo si tipo_alcance = 'GRUPO'
        empresa_id          NVARCHAR(50)        NULL,
            -- Solo si tipo_alcance = 'EMPRESA' o 'SUCURSAL'
        sucursal_id         NVARCHAR(50)        NULL,
            -- Solo si tipo_alcance = 'SUCURSAL'
        activo              BIT                 NOT NULL DEFAULT 1,
        asignado_por        NVARCHAR(50)        NULL,
        created_at          DATETIME            NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT FK_usuarios_alcance_grupo FOREIGN KEY (grupo_id) REFERENCES grupos_empresas(id),
        CONSTRAINT CK_tipo_alcance CHECK (tipo_alcance IN ('GLOBAL', 'GRUPO', 'EMPRESA', 'SUCURSAL'))
    );

    CREATE INDEX IX_usuarios_alcance_usuario ON usuarios_alcance (usuario_id, activo);
    CREATE INDEX IX_usuarios_alcance_tipo ON usuarios_alcance (tipo_alcance, grupo_id, empresa_id, sucursal_id);

    PRINT 'Tabla usuarios_alcance creada';
END
GO
```

---

## 3. MATRIZ DE ROLES Y PERMISOS

### 3.1 Permisos por Rol

| Permiso | SuperAdmin | Admin Fin | Tesorero | CxP | Auditor | Op. Suc | Alcance |
|---------|:----------:|:---------:|:--------:|:---:|:-------:|:-------:|---------|
| **FINANZAS** |
| FINANZAS_TAB_VER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Global |
| **TESORERÍA** |
| TESORERIA_VER | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | Alcance |
| TESORERIA_INICIAR_CUADRE | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | Alcance |
| TESORERIA_GUARDAR_CUADRE | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Alcance |
| TESORERIA_AJUSTAR_CUADRE | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Alcance |
| TESORERIA_AUTORIZAR_DESCUADRE | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Alcance |
| **PROPINAS** |
| PROPINAS_VER | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | Alcance |
| PROPINAS_CUADRE_VER | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | Alcance |
| PROPINAS_CUADRE_CONFIRMAR | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Alcance |
| PROPINAS_CONFIG_VER | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Global |
| PROPINAS_CONFIG_EDITAR | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Global |
| **CXP** |
| CXP_VER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Alcance |
| CXP_FILTRAR | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Alcance |
| CXP_MARCAR_PAGAR | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | Alcance |
| CXP_PAGO_MASIVO | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | Alcance |
| CXP_AUTORIZAR_PAGO | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Alcance |
| CXP_EXPORTAR | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Alcance |
| **PRESUPUESTOS** |
| PRESUPUESTO_VER | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Alcance |
| PRESUPUESTO_CREAR | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Alcance |
| PRESUPUESTO_EDITAR | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | Alcance |
| PRESUPUESTO_ELIMINAR | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Alcance |
| **DASHBOARD** |
| DASHBOARD_FINANZAS_VER | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Global |
| REPORTES_FINANZAS_VER | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Alcance |
| REPORTES_FINANZAS_EXPORTAR | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Alcance |

### 3.2 Alcances por Rol

| Rol | Alcance Default | Alcances Permitidos |
|-----|-----------------|---------------------|
| SuperAdmin | GLOBAL | GLOBAL |
| Admin Finanzas | GLOBAL | GLOBAL, GRUPO, EMPRESA |
| Tesorero | EMPRESA | GRUPO, EMPRESA, SUCURSAL |
| CxP | EMPRESA | GRUPO, EMPRESA |
| Auditor | GLOBAL | GLOBAL, GRUPO, EMPRESA |
| Op. Sucursal | SUCURSAL | SUCURSAL (solo asignadas) |

---

## 4. REGLAS DE EVALUACIÓN DE PERMISOS

### 4.1 Algoritmo de Evaluación

```
FUNCIÓN verificar_acceso(usuario, permiso, entidad):
    
    1. OBTENER roles del usuario activos
       SI no tiene roles → RECHAZAR
    
    2. PARA CADA rol:
       a. VERIFICAR si rol tiene el permiso
       b. SI tiene permiso:
          - SI permiso.requiere_alcance = FALSE → PERMITIR
          - SI permiso.requiere_alcance = TRUE:
            c. OBTENER alcances del usuario
            d. EVALUAR alcance vs entidad:
               - GLOBAL → PERMITIR
               - GRUPO → VERIFICAR entidad.empresa en grupo
               - EMPRESA → VERIFICAR entidad.empresa = alcance.empresa
               - SUCURSAL → VERIFICAR entidad.sucursal = alcance.sucursal
    
    3. SI ningún rol permite → RECHAZAR
```

### 4.2 Orden de Prioridad

```
1. Rol (¿tiene el permiso?)
   ↓
2. Permiso (¿requiere alcance?)
   ↓
3. Alcance (GLOBAL > GRUPO > EMPRESA > SUCURSAL)
   ↓
4. Entidad (¿está dentro del alcance?)
```

### 4.3 Resolución de Conflictos

| Escenario | Resolución |
|-----------|------------|
| Usuario con 2 roles, uno permite y otro no | **PERMITE** (OR lógico) |
| Usuario con alcance GLOBAL y SUCURSAL | Se usa **GLOBAL** (más permisivo) |
| Usuario sin alcance asignado | Se asume **NINGUNO** (rechaza todo con alcance) |
| Permiso sin `requiere_alcance` | Se evalúa solo el permiso |

---

## 5. EJEMPLOS PRÁCTICOS

### 5.1 Usuario con Acceso GLOBAL

```sql
-- SuperAdmin: Mario García
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_001', (SELECT id FROM roles WHERE codigo = 'SUPERADMIN'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance)
VALUES ('usr_001', 'GLOBAL');

-- Resultado: Acceso total a todo el sistema
```

### 5.2 Usuario con Acceso a GRUPO de Empresas

```sql
-- Auditor del Grupo MPRO: Ana López
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_002', (SELECT id FROM roles WHERE codigo = 'AUDITOR'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance, grupo_id)
VALUES ('usr_002', 'GRUPO', (SELECT id FROM grupos_empresas WHERE codigo = 'MPRO'));

-- Resultado: Solo lectura en empresas del grupo MPRO
-- Si intenta ver Tesorería de La Estelar (SoftRestaurant) → RECHAZADO
```

### 5.3 Usuario con Acceso a una EMPRESA

```sql
-- Contador de empresa específica: Carlos Ruiz
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_003', (SELECT id FROM roles WHERE codigo = 'CXP'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance, empresa_id)
VALUES ('usr_003', 'EMPRESA', 'EMP_CIENFUEGOS');

-- Resultado: Puede ver y marcar pagos solo de Cienfuegos
-- Si intenta pago masivo de La Estelar → RECHAZADO
```

### 5.4 Usuario con Acceso a SUCURSAL

```sql
-- Operador de sucursal: Laura Méndez
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_004', (SELECT id FROM roles WHERE codigo = 'OP_SUCURSAL'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance, empresa_id, sucursal_id)
VALUES ('usr_004', 'SUCURSAL', 'EMP_CIENFUEGOS', 'SUC_CF_001');

-- Resultado: Solo puede ver e iniciar cuadres de su sucursal
-- Guardar cuadre → RECHAZADO (no tiene permiso TESORERIA_GUARDAR_CUADRE)
```

### 5.5 Usuario que puede VER pero no AUTORIZAR

```sql
-- Tesorero: Pedro Sánchez
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_005', (SELECT id FROM roles WHERE codigo = 'TESORERO'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance, grupo_id)
VALUES ('usr_005', 'GRUPO', (SELECT id FROM grupos_empresas WHERE codigo = 'SOFTREST'));

-- Puede: Ver, iniciar, guardar, ajustar cuadres de SoftRestaurant
-- NO puede: Autorizar descuadres (no tiene TESORERIA_AUTORIZAR_DESCUADRE)
-- NO puede: Pago masivo CxP (no tiene CXP_PAGO_MASIVO)
```

### 5.6 Usuario que puede AUTORIZAR solo en su GRUPO

```sql
-- Admin Finanzas del Grupo MPRO: Roberto Díaz
INSERT INTO usuarios_roles (usuario_id, rol_id)
VALUES ('usr_006', (SELECT id FROM roles WHERE codigo = 'ADMIN_FIN'));

INSERT INTO usuarios_alcance (usuario_id, tipo_alcance, grupo_id)
VALUES ('usr_006', 'GRUPO', (SELECT id FROM grupos_empresas WHERE codigo = 'MPRO'));

-- Puede: Autorizar pagos CxP, autorizar descuadres, editar config propinas
-- SOLO en empresas del grupo MPRO
-- Si intenta autorizar pago de La Estelar → RECHAZADO
```

---

## 6. IMPLEMENTACIÓN TÉCNICA

### 6.1 Backend (Python/FastAPI)

```python
# /app/backend/core/rbac.py

from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TipoAlcance(Enum):
    GLOBAL = "GLOBAL"
    GRUPO = "GRUPO"
    EMPRESA = "EMPRESA"
    SUCURSAL = "SUCURSAL"

class ServicioRBAC:
    """
    Servicio de control de acceso basado en roles.
    Evalúa permisos considerando rol + alcance.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._cache_permisos = {}
        self._cache_alcances = {}
    
    async def verificar_permiso(
        self,
        usuario_id: str,
        permiso_codigo: str,
        empresa_id: Optional[str] = None,
        sucursal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica si un usuario tiene un permiso específico.
        
        Returns:
            {
                'permitido': bool,
                'motivo': str,
                'alcance_aplicado': str,
                'rol_usado': str
            }
        """
        try:
            # 1. Obtener roles del usuario
            roles = await self._obtener_roles_usuario(usuario_id)
            if not roles:
                return {
                    'permitido': False,
                    'motivo': 'Usuario sin roles asignados',
                    'alcance_aplicado': None,
                    'rol_usado': None
                }
            
            # 2. Verificar si algún rol tiene el permiso
            for rol in roles:
                tiene_permiso = await self._rol_tiene_permiso(rol['id'], permiso_codigo)
                if not tiene_permiso:
                    continue
                
                # 3. Obtener info del permiso
                permiso = await self._obtener_permiso(permiso_codigo)
                if not permiso:
                    continue
                
                # 4. Si no requiere alcance, permitir
                if not permiso['requiere_alcance']:
                    return {
                        'permitido': True,
                        'motivo': 'Permiso global (sin alcance)',
                        'alcance_aplicado': 'GLOBAL',
                        'rol_usado': rol['codigo']
                    }
                
                # 5. Evaluar alcance
                alcances = await self._obtener_alcances_usuario(usuario_id)
                resultado_alcance = await self._evaluar_alcance(
                    alcances, empresa_id, sucursal_id
                )
                
                if resultado_alcance['permitido']:
                    return {
                        'permitido': True,
                        'motivo': f"Permiso válido con alcance {resultado_alcance['tipo']}",
                        'alcance_aplicado': resultado_alcance['tipo'],
                        'rol_usado': rol['codigo']
                    }
            
            return {
                'permitido': False,
                'motivo': 'Sin permiso o fuera de alcance',
                'alcance_aplicado': None,
                'rol_usado': None
            }
            
        except Exception as e:
            logger.error(f"Error verificando permiso: {e}")
            return {
                'permitido': False,
                'motivo': f'Error interno: {e}',
                'alcance_aplicado': None,
                'rol_usado': None
            }
    
    async def _evaluar_alcance(
        self,
        alcances: List[Dict],
        empresa_id: Optional[str],
        sucursal_id: Optional[str]
    ) -> Dict:
        """Evalúa si los alcances del usuario cubren la entidad."""
        
        for alcance in alcances:
            tipo = alcance['tipo_alcance']
            
            # GLOBAL permite todo
            if tipo == 'GLOBAL':
                return {'permitido': True, 'tipo': 'GLOBAL'}
            
            # GRUPO: verificar si empresa está en el grupo
            if tipo == 'GRUPO' and empresa_id:
                if await self._empresa_en_grupo(empresa_id, alcance['grupo_id']):
                    return {'permitido': True, 'tipo': 'GRUPO'}
            
            # EMPRESA: verificar match exacto
            if tipo == 'EMPRESA' and empresa_id:
                if alcance['empresa_id'] == empresa_id:
                    return {'permitido': True, 'tipo': 'EMPRESA'}
            
            # SUCURSAL: verificar match exacto
            if tipo == 'SUCURSAL' and sucursal_id:
                if alcance['sucursal_id'] == sucursal_id:
                    return {'permitido': True, 'tipo': 'SUCURSAL'}
        
        return {'permitido': False, 'tipo': None}
    
    async def obtener_permisos_usuario(
        self,
        usuario_id: str
    ) -> List[str]:
        """Retorna lista de códigos de permisos del usuario."""
        query = """
        SELECT DISTINCT p.codigo
        FROM permisos p
        INNER JOIN rol_permisos rp ON p.id = rp.permiso_id
        INNER JOIN usuarios_roles ur ON rp.rol_id = ur.rol_id
        WHERE ur.usuario_id = ?
          AND ur.activo = 1
          AND rp.activo = 1
          AND p.activo = 1
          AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
        """
        # ... implementación
        pass
    
    async def obtener_alcance_efectivo(
        self,
        usuario_id: str
    ) -> Dict:
        """
        Retorna el alcance efectivo del usuario.
        Usado para filtrar datos en queries.
        """
        alcances = await self._obtener_alcances_usuario(usuario_id)
        
        # Determinar alcance más amplio
        for alcance in alcances:
            if alcance['tipo_alcance'] == 'GLOBAL':
                return {
                    'tipo': 'GLOBAL',
                    'empresas': None,  # Todas
                    'sucursales': None  # Todas
                }
        
        # Recolectar empresas y sucursales permitidas
        empresas = set()
        sucursales = set()
        
        for alcance in alcances:
            if alcance['tipo_alcance'] == 'GRUPO':
                empresas_grupo = await self._obtener_empresas_grupo(alcance['grupo_id'])
                empresas.update(empresas_grupo)
            elif alcance['tipo_alcance'] == 'EMPRESA':
                empresas.add(alcance['empresa_id'])
            elif alcance['tipo_alcance'] == 'SUCURSAL':
                sucursales.add(alcance['sucursal_id'])
                if alcance.get('empresa_id'):
                    empresas.add(alcance['empresa_id'])
        
        return {
            'tipo': 'RESTRINGIDO',
            'empresas': list(empresas) if empresas else None,
            'sucursales': list(sucursales) if sucursales else None
        }
```

### 6.2 Frontend (React)

```javascript
// /app/frontend/src/hooks/usePermissions.js

import { createContext, useContext, useState, useEffect } from 'react';

const PermissionsContext = createContext(null);

export function PermissionsProvider({ children }) {
  const [permisos, setPermisos] = useState([]);
  const [alcance, setAlcance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cargar permisos al login
    const cargarPermisos = async () => {
      try {
        const response = await fetch('/api/auth/permisos');
        const data = await response.json();
        setPermisos(data.permisos || []);
        setAlcance(data.alcance || null);
      } catch (error) {
        console.error('Error cargando permisos:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarPermisos();
  }, []);

  const tienePermiso = (codigo) => {
    return permisos.includes(codigo);
  };

  const puedeVer = (modulo) => {
    return tienePermiso(`${modulo}_VER`);
  };

  const puedeEditar = (modulo) => {
    const editPermisos = permisos.filter(p => 
      p.startsWith(modulo) && 
      (p.includes('EDIT') || p.includes('CREAR') || p.includes('MARCAR'))
    );
    return editPermisos.length > 0;
  };

  const puedeAutorizar = (modulo) => {
    const authPermisos = permisos.filter(p => 
      p.startsWith(modulo) && p.includes('AUTORIZAR')
    );
    return authPermisos.length > 0;
  };

  return (
    <PermissionsContext.Provider value={{
      permisos,
      alcance,
      loading,
      tienePermiso,
      puedeVer,
      puedeEditar,
      puedeAutorizar
    }}>
      {children}
    </PermissionsContext.Provider>
  );
}

export const usePermissions = () => useContext(PermissionsContext);

// Uso en componentes:
// const { tienePermiso, puedeAutorizar } = usePermissions();
// {tienePermiso('CXP_AUTORIZAR_PAGO') && <Button>Autorizar Pago</Button>}
```

### 6.3 Middleware de Protección

```python
# /app/backend/core/middleware_rbac.py

from functools import wraps
from fastapi import HTTPException, Request
from core.rbac import ServicioRBAC, servicio_rbac
from core.auditoria import servicio_auditoria, AccionAuditoria, ModuloAuditoria, ResultadoAuditoria

def requiere_permiso(
    permiso: str,
    modulo: ModuloAuditoria = None,
    nivel_riesgo: str = None
):
    """
    Decorador para proteger endpoints con RBAC.
    
    Uso:
        @requiere_permiso('CXP_AUTORIZAR_PAGO', ModuloAuditoria.CXP, 'CRITICO')
        async def autorizar_pago(factura_id: str, current_user: dict):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="No autenticado")
            
            # Extraer empresa/sucursal del request o kwargs
            empresa_id = kwargs.get('empresa_id') or (request.query_params.get('empresa_id') if request else None)
            sucursal_id = kwargs.get('sucursal_id') or (request.query_params.get('sucursal_id') if request else None)
            
            # Verificar permiso
            resultado = await servicio_rbac.verificar_permiso(
                usuario_id=current_user['user_id'],
                permiso_codigo=permiso,
                empresa_id=empresa_id,
                sucursal_id=sucursal_id
            )
            
            if not resultado['permitido']:
                # Registrar intento rechazado
                await servicio_auditoria.registrar(
                    usuario=current_user,
                    request=request,
                    modulo=modulo or ModuloAuditoria.SISTEMA,
                    entidad='acceso',
                    accion=AccionAuditoria.VIEW,
                    registro_id=permiso,
                    resultado=ResultadoAuditoria.RECHAZADO,
                    motivo=resultado['motivo'],
                    nivel_riesgo=nivel_riesgo
                )
                
                raise HTTPException(
                    status_code=403,
                    detail=f"Acceso denegado: {resultado['motivo']}"
                )
            
            # Ejecutar función
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

---

## 7. INTEGRACIÓN CON AUDITORÍA

### 7.1 Datos Capturados en Auditoría

Cada acción auditada incluirá:

| Campo | Fuente |
|-------|--------|
| `usuario_id` | Token JWT |
| `usuario_email` | Token JWT |
| `rol_usado` | Resultado de RBAC |
| `permiso_aplicado` | Código del permiso verificado |
| `alcance_aplicado` | GLOBAL / GRUPO / EMPRESA / SUCURSAL |
| `empresa_id` | Contexto de la operación |
| `sucursal_id` | Contexto de la operación |
| `accion` | VIEW / EDIT / CONFIRM / AUTHORIZE |
| `resultado` | OK / ERROR / RECHAZADO |

### 7.2 Ejemplo de Registro Completo

```json
{
  "id": 1234,
  "created_at": "2025-12-15T10:30:00",
  "usuario_id": "usr_006",
  "usuario_email": "roberto.diaz@edarsa.com",
  "session_id": "sess_abc123",
  "ip_origen": "192.168.1.100",
  
  "empresa_id": "EMP_ORIGEN",
  "sucursal_id": null,
  "origen_sistema": "EDARSA_HUB",
  
  "modulo": "CXP",
  "entidad": "factura",
  "entidad_origen": "cuentas_por_pagar",
  "accion": "AUTHORIZE",
  
  "registro_id": "FAC_2025_0001",
  "registro_folio": "A-1234",
  
  "campo_modificado": "estado_pago",
  "valor_anterior": "PENDIENTE",
  "valor_nuevo": "AUTORIZADO",
  
  "resultado": "OK",
  "motivo": null,
  "nivel_riesgo": "CRITICO",
  
  "rol_usado": "ADMIN_FIN",
  "permiso_aplicado": "CXP_AUTORIZAR_PAGO",
  "alcance_aplicado": "GRUPO"
}
```

---

## 8. PLAN DE IMPLEMENTACIÓN (Controlado)

### Fase 0: Tablas Base (1 día)
- [ ] Crear tablas RBAC en SQL Server EDARSA HUB
- [ ] Insertar roles y permisos base
- [ ] Verificar integridad

### Fase 1: Backend Core (2 días)
- [ ] Crear `/app/backend/core/rbac.py`
- [ ] Crear middleware de protección
- [ ] Integrar con auditoría existente

### Fase 2: Sincronización Usuarios (1 día)
- [ ] Sincronizar usuarios de MongoDB → SQL Server
- [ ] Asignar roles iniciales según perfil actual
- [ ] Asignar alcances según empresa/sucursal actual

### Fase 3: Protección de Endpoints (3 días)
- [ ] Tesorería: Proteger cuadres
- [ ] CxP: Proteger pagos y autorizaciones
- [ ] Propinas: Proteger configuración

### Fase 4: Frontend (2 días)
- [ ] Hook `usePermissions`
- [ ] Ocultar/deshabilitar botones según permisos
- [ ] Filtrar datos según alcance

### Fase 5: Validación (1 día)
- [ ] Pruebas con usuarios de diferentes roles
- [ ] Verificar auditoría completa
- [ ] Confirmar no regresión

---

## 9. APROBACIÓN REQUERIDA

### Modelo de Datos
- [ ] Tablas propuestas (roles, permisos, alcances, grupos)
- [ ] Relaciones entre tablas
- [ ] Datos iniciales (roles y permisos base)

### Matriz de Permisos
- [ ] Permisos por módulo
- [ ] Asignación por rol
- [ ] Niveles de riesgo

### Reglas de Evaluación
- [ ] Algoritmo de verificación
- [ ] Orden de prioridad
- [ ] Resolución de conflictos

### Alcances
- [ ] 4 niveles (GLOBAL, GRUPO, EMPRESA, SUCURSAL)
- [ ] Grupos de empresas

---

**¿Apruebas esta propuesta técnica para proceder con la implementación controlada?**
