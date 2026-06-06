-- app/docs/sql/catalogos_maestros_universales.sql

-- ============================================================================
-- 1. CAPA DE PERSONAL: MATRIZ DE ROLES Y CONTROL DE ACCESO (ENTERPRISE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hub_roles_operativos (
    id_rol VARCHAR(16) PRIMARY KEY, -- CAJERO, MESERO, CAPITAN, GARROTERO, GERENTE
    nombre_rol VARCHAR(32) NOT NULL,
    permite_cancelar INT DEFAULT 0, -- Control paramétrico estricto de caja
    permite_reabrir_mesas INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hub_personal_sucursal (
    id_empleado VARCHAR(32) PRIMARY KEY,
    nombre_completo VARCHAR(64) NOT NULL,
    id_rol VARCHAR(16) NOT NULL,
    enterprise_payroll_id VARCHAR(64), -- Enlace directo a tu ERP de Nómina
    softrestaurant_user_id VARCHAR(32), -- Mapeo para no duplicar en el salón
    estado_activo INT DEFAULT 1,
    FOREIGN KEY (id_rol) REFERENCES hub_roles_operativos(id_rol)
);

-- ============================================================================
-- 2. CAPA DE INVENTARIOS: INSUMOS, PRESENTACIONES Y DOSIFICACIÓN (MOPRO)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hub_insumos_materia_prima (
    id_insumo VARCHAR(32) PRIMARY KEY, -- ALPH-INS-001
    nombre_insumo VARCHAR(64) NOT NULL,
    unidad_medida_base VARCHAR(12) NOT NULL, -- GRAMOS, MILILITROS, PIEZAS
    mopro_item_id VARCHAR(64), -- Conector único con el catálogo de Mopro
    sap_material_code VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS hub_presentaciones_compra (
    id_presentacion VARCHAR(32) PRIMARY KEY,
    id_insumo VARCHAR(32) NOT NULL,
    nombre_presentacion VARCHAR(48) NOT NULL, -- CAJA, SACK_25KG, BOTELLA_750ML
    factor_conversion_a_base DECIMAL(12, 4) NOT NULL, -- Ej: Botella a mililitros = 750.0000
    FOREIGN KEY (id_insumo) REFERENCES hub_insumos_materia_prima(id_insumo)
);

-- ============================================================================
-- 3. CAPA COMERCIAL: PRODUCTOS DE VENTA FINALES (SOFT RESTAURANT / PORTAL)
-- ============================================================================
CREATE TABLE IF NOT EXISTS hub_productos_venta (
    id_producto VARCHAR(32) PRIMARY KEY, -- ALPH-PROD-001
    nombre_comercial VARCHAR(64) NOT NULL,
    unidad_negocio VARCHAR(24) NOT NULL, -- BARRA, COCINA_PARRILLA, REPOSTERIA
    precio_publico DECIMAL(10, 2) NOT NULL,
    categoria_push VARCHAR(24) DEFAULT 'NINGUNA', -- BAJA_ROTACION, TEMPORADA, CAUSA
    softrestaurant_product_id VARCHAR(64), -- Enlace de folio a Soft Restaurant
    estado_venta INT DEFAULT 1
);

-- Tabla puente de explosión de recetas (El mapa elástico de descuento)
CREATE TABLE IF NOT EXISTS hub_recetas_explosion (
    id_producto VARCHAR(32),
    id_insumo VARCHAR(32),
    cantidad_requerida_base DECIMAL(12, 4) NOT NULL, -- Cantidad exacta en gramos/ml
    es_critico INT DEFAULT 0, -- 1 = Bloqueo duro, 0 = Flexible / Permite Negativos
    PRIMARY KEY (id_producto, id_insumo),
    FOREIGN KEY (id_producto) REFERENCES hub_productos_venta(id_producto),
    FOREIGN KEY (id_insumo) REFERENCES hub_insumos_materia_prima(id_insumo)
);
