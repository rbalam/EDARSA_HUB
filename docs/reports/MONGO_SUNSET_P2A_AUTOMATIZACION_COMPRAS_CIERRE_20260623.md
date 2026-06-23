# EDARSAHUB – Mongo Sunset / SQL-First
## Cierre P2A Automatización Compras – 23-Jun-2026

- Archivo migrado: `backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py`
- Runtime Mongo eliminado en este archivo.
- Tablas SQL usadas:
  - `Operativo_TareasCompras`
  - `Operativo_BitacoraCompras`
  - `Operativo_PedidosProcesados`
  - `Scheduler_BitacoraJobs`
  - `Usuario_Catalogo`
- Validación:
  - `python3 -m py_compile backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py` = OK

Pendiente P2:
- `sla_routes.py`
- `notificaciones_routes.py`
- `documentos_routes.py`
