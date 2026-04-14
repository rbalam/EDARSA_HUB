# EDARSA HUB - Product Requirements Document

## Descripción General
Sistema de gestión empresarial para EDARSA que integra múltiples módulos: Cuentas por Pagar (CxP), Tesorería, Portal de Proveedores, y administración de catálogos conectados a bases de datos SQL Server externas (MPRO y SoftRestaurant).

## Arquitectura
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + Python
- **Bases de Datos**: 
  - MongoDB (datos de aplicación)
  - SQL Server (múltiples instancias: MPRO y SoftRestaurant on-premise)

## Módulos Implementados

### 1. Portal de Proveedores ✅
- **Login**: Maquetado pixel-perfect según mockup
- **Dashboard**: UI completada con filtros por Sistema/Unidad
- **Backend**: Consultas SQL adaptativas para MPRO (`Cuenta_X_Pagar`) y SoftRestaurant (`compras` + `pagosproveedores` via `idcompra`)
- **Filtros**: Servidores con `visible_en_operaciones=True` únicamente

### 2. Cuentas por Pagar (CxP)
- Visualización de facturas pendientes desde múltiples BD
- Integración con MPRO y SoftRestaurant

### 3. Tesorería
- Gestión de fichas de depósito
- Carga de archivos

---

## Changelog

### 2025-12-XX
- Reducción de tamaño de botones de filtro en Dashboard Portal Proveedores
- CSS: `text-xs`, `px-3 py-1.5`, `rounded-md`, `gap-1.5`

### Sesiones Anteriores
- Maquetación pixel-perfect de LoginPage.jsx para Portal de Proveedores
- Corrección de consultas SQL en portal_proveedores.py
- Filtrado de servidores SQL por `visible_en_operaciones`
- Colores dinámicos: Azul (#F5F9FF) para MPRO, Violeta (#FAF8FF) para SoftRestaurant

---

## Backlog Priorizado

### P0 (Urgente)
- ~~Ajuste de tamaño de fuentes en Dashboard Portal~~ ✅

### P1 (Alta Prioridad)
- Integración de OCR para fichas de depósito en Tesorería
- Lógica de selección de facturas en CxP + cálculo "Total a Pagar"
- Módulo Finanzas - Conciliación bancaria
- Integración real con catálogos SQL al autorizar "Solicitud de Alta"
- Reportes de colaboradores por empresa

### P2 (Media Prioridad)
- Exportación a Excel de CxP
- Dashboard de KPIs financieros
- Integración con módulo de nómina

### Deuda Técnica
- 125 tests legacy con errores (BLOQUEADO por usuario)
- Variables de estado huérfanas en Usuarios.js
- Expiración rápida de tokens JWT

---

## Credenciales de Prueba
- **Portal Proveedores**: RFC `EAR201118NG2` / Contraseña `Proveedor123!`

## Notas Críticas
- El cliente evalúa basándose estrictamente en capturas de pantalla (pixel-perfect)
- Timeouts de SQL Server esperados en ambiente Preview
- No modificar lógica de otras páginas sin solicitud explícita
