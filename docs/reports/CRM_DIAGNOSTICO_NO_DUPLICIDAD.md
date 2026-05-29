# DICTAMEN DE NO DUPLICIDAD - CRM ENTERPRISE EDARSAHUB
**Fase 1 - Gobierno y Arquitectura**

Este documento establece el diagnóstico oficial de las estructuras actuales en `EDARSAHUB SQL` para garantizar la Máxima 6 (No duplicar tablas), Máxima 7 (No duplicar entidades) y Máxima 8 (No duplicar catálogos).

## 1. ENTIDADES MAESTRAS EXISTENTES (NO DUPLICAR)
Las siguientes tablas ya existen en el ecosistema y se declaran como **Fuentes de Verdad Absoluta**. El CRM debe conectarse a ellas mediante llaves foráneas.

* **`Cliente_Catalogo`**: Actúa como el Maestro de Clientes (Identidad Jurídica/Fiscal). No se crearán nuevas tablas de clientes facturables.
* **`Venta_Cotizaciones` / `Venta_CotizacionesDetalle`**: Módulo blindado de cotizaciones oficiales con validez operativa. El CRM usará estas tablas, no creará copias.
* **`Venta_Pedidos` / `Venta_PedidosDetalle`**: Módulo blindado de pedidos oficiales. El CRM solo inyectará datos aquí tras la conversión de una oportunidad.
* **`Usuario_Catalogo` / `Usuario_Roles`**: El CRM respetará el RBAC actual. No existirá una tabla paralela de "vendedores", se usarán los usuarios del Hub.

## 2. NUEVAS ENTIDADES AUTORIZADAS PARA CREACIÓN (SÍ CREAR)
Tras el análisis de vacíos funcionales, se autoriza la creación de las siguientes estructuras exclusivas para la operativa del CRM en la Fase 2, asegurando que no colisionen con las maestras:

* **`CRM_Cuentas`**: Almacenará Prospectos y Cuentas Comerciales que aún no tienen peso fiscal (separando la paja del trigo antes de llegar a `Cliente_Catalogo`).
* **`CRM_ClientesSolicitudesAlta`**: Tabla de *staging* y workflow para aprobar el paso de un Prospecto (`CRM_Cuentas`) a un Cliente Real (`Cliente_Catalogo`).
* **`CRM_ClientesSolicitudesAltaHistorial`**: Auditoría obligatoria de los cambios de estado en las solicitudes.
* **`Venta_Remisiones` / `Venta_RemisionesDetalle`**: Extensión del flujo de ventas (Cotización -> Pedido -> Remisión) aprobada para el control de entregas.
* **`Venta_RemisionesHistorial`**: Bitácora de auditoría de remisiones.

## 3. CONCLUSIÓN Y REGLA DE DESARROLLO
El diagnóstico es favorable. El modelo base del CRM puede proceder a la **Fase 2** construyendo únicamente las 6 tablas autorizadas en la sección 2. Cualquier intento de replicar la información fiscal de los clientes o el detalle de los pedidos será bloqueado por arquitectura.
