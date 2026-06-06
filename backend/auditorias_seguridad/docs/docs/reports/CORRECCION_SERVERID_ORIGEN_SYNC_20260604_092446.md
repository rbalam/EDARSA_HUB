# CORRECCIÓN SERVERID EN ORIGEN SYNC

Archivo: /app/backend/modules/compras/sync_service.py
Backup: /app/backend/modules/compras/sync_service.py.backup_no_serverid_origen_20260604_092446

## Validación sintaxis
```text
OK py_compile
```

## Búsqueda ServerID en SELECT origen
```text
575:                    USING (SELECT %s AS AlmacenID) AS source ON target.AlmacenID = source.AlmacenID AND target.ServerID = %s
```

## Referencias ServerID restantes
```text
3:# ServerID, OrigenSistema, id_empresa e id_unidad_negocio NO existen ni deben leerse desde SoftRestaurant/MPRO.
575:                    USING (SELECT %s AS AlmacenID) AS source ON target.AlmacenID = source.AlmacenID AND target.ServerID = %s
656:            WHERE ServerID = %s AND EsActual = 1
697:    Llave MERGE: ServerID + OrigenSistema + Folio (encabezado), + CodigoProducto (detalle)
800:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema AND target.Folio = source.Folio
825:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema 
864:    Llave MERGE: ServerID + OrigenSistema + FolioPedido (enc), + CodigoProducto (det)
942:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema AND target.FolioPedido = source.FolioPedido
967:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema 
1006:    Llave MERGE: ServerID + OrigenSistema + FolioOrden (enc), + CodigoProducto (det)
1084:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema AND target.FolioOrden = source.FolioOrden
1109:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema 
1148:    Llave MERGE: ServerID + OrigenSistema + FolioRecepcion (enc), + CodigoProducto (det)
1226:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema AND target.FolioRecepcion = source.FolioRecepcion
1251:                    ON target.ServerID = source.ServerID AND target.OrigenSistema = source.OrigenSistema 
```
