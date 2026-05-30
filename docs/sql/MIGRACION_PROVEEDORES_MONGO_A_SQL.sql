-- =============================================================================
-- SCRIPT: CREACIÓN TABLA PROVEEDORES CENTRAL + MIGRACIÓN MONGO → SQL
-- OBJETIVO: Establecer estructura SQL para proveedores y migrar datos de MongoDB
-- =============================================================================

-- 1. Asegura que la tabla SQL central esté lista
CREATE TABLE IF NOT EXISTS proveedores_central (
    id VARCHAR(100) PRIMARY KEY,
    nombre VARCHAR(255),
    contacto TEXT,
    estatus VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Script de Migración (Ejecutar desde tu backend tras leer de Mongo)
-- Nota: La lógica de migración debe ser: Leer Mongo -> Transformar -> Insertar SQL
INSERT INTO proveedores_central (id, nombre, contacto, estatus, created_at)
VALUES 
    -- Estos valores provendrán de la lectura previa de db.portal_suppliers
    ('ID_PROVEEDOR_1', 'Nombre Proveedor', 'Contacto', 'ACTIVO', NOW())
ON CONFLICT (id) DO NOTHING;
