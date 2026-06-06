# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:36:02.057098
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: verificacion, CodigoRol, CodigoAccion, Permitido
- Filas: 15
- Preview (primeras 20 filas):
```
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'VER', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'EXPORTAR', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'CONFIGURAR', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'GESTIONAR', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'DIRECCION', 'CodigoAccion': 'VER', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'DIRECCION', 'CodigoAccion': 'EXPORTAR', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'GERENTE_OPS', 'CodigoAccion': 'VER', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'GERENTE_OPS', 'CodigoAccion': 'EXPORTAR', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'AUDITOR', 'CodigoAccion': 'VER', 'Permitido': True}
  {'verificacion': 'PERMISOS_RESTANTES', 'CodigoRol': 'VISOR', 'CodigoAccion': 'VER', 'Permitido': True}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   ROLLBACK: Eliminar permisos CRM de INTELIGENCIA_COMERCIAL
   
   Motivo: CRM y Portal de Inteligencia Comercial son módulos 
   distintos. No mezclar permisos sin matriz aprobada.
   ============================================================ */

-- Obtener IDs de roles CRM
DECLARE @CRM_ADMIN_ID INT = (SELECT RolID FROM Usuario_Roles WHERE CodigoRol = 'CRM_ADMIN');
DECLARE @CRM_EJEC_ID INT = (SELECT RolID FROM Usuario_Roles WHERE CodigoRol = 'CRM_EJEC');
DECLARE @CRM_AUDIT_ID INT = (SELECT RolID FROM Usuario_Roles WHERE CodigoRol = 'CRM_AUDIT');
DECLARE @ModuloID INT = 59; -- INTELIGENCIA_COMERCIAL

-- Eliminar permisos de CRM_ADMIN para INTELIGENCIA_COMERCIAL
DELETE FROM Usuario_PermisosRolModulo
WHERE RolID = @CRM_ADMIN_ID AND ModuloID = @ModuloID;

PRINT 'Eliminados permisos de CRM_ADMIN para INTELIGENCIA_COMERCIAL';

-- Eliminar permisos de CRM_EJEC para INTELIGENCIA_COMERCIAL
DELETE FROM Usuario_PermisosRolModulo
WHERE RolID = @CRM_EJEC_ID AND ModuloID = @ModuloID;

PRINT 'Eliminados permisos de CRM_EJEC para INTELIGENCIA_COMERCIAL';

-- Eliminar permisos de CRM_AUDIT para INTELIGENCIA_COMERCIAL
DELETE FROM Usuario_PermisosRolModulo
WHERE RolID = @CRM_AUDIT_ID AND ModuloID = @ModuloID;

PRINT 'Eliminados permisos de CRM_AUDIT para INTELIGENCIA_COMERCIAL';

-- Verificación
SELECT 
    'PERMISOS_RESTANTES' AS verificacion,
    r.CodigoRol,
    a.CodigoAccion,
    p.Permitido
FROM Usuario_PermisosRolModulo p
JOIN Usuario_Roles r ON p.RolID = r.RolID
JOIN Usuario_Acciones a ON p.AccionID = a.AccionID
WHERE p.ModuloID = @ModuloID
ORDER BY r.NivelJerarquia DESC, a.AccionID;

PRINT 'Rollback completado. Permisos CRM eliminados de INTELIGENCIA_COMERCIAL.';

```