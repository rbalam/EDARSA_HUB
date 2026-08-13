/*
Rollback de 023 NO debe ejecutarse de forma genérica.

La consolidación repunta FKs y elimina 39 registros legacy.
Para rollback completo se requiere restaurar exactamente:
- filas originales de Inventario_Almacenes 1..39;
- Compras_Recepciones que originalmente apuntaban a cada legacy;
- Inventario_Movimientos / Existencias si existieran;
- mantener snapshot previo.

Usar únicamente snapshot/auditoría generada antes de migrate.
No ejecutar este archivo automáticamente.
*/

THROW 52999,
'Rollback 023 requiere restauración desde snapshot exacto; ejecución automática bloqueada.',
1;
