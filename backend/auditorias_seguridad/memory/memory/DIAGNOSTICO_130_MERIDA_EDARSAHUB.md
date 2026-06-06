# DIAGNÓSTICO PASIVO — Existencia de 130 MERIDA en EDARSAHUB

**Fecha:** 14-Mayo-2026  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Solicitado por:** Usuario

---

## 1. Resultado de Unidades_Negocio

| Campo | Valor |
|-------|-------|
| id | `19E076FB-C6DE-4EA5-84AB-1CAA9E86082C` |
| codigo | `130MID` ✅ |
| nombre | `130° MERIDA` |
| server_id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| sucursal_origen_id | `NULL` |
| system_type | `SoftRestaurant` |
| activo | `True` |
| orden | `1` |
| fuente | `EDARSAHUB` |

**RESULTADO:** ✅ **130MID EXISTE** en Unidades_Negocio

---

## 2. Resultado de Sistema_Empresas

| Campo | Valor |
|-------|-------|
| EmpresaID | `5` |
| CodigoEmpresa | `130MID` ✅ |
| NombreEmpresa | `130 MID` |
| NombreComercial | `130 Grados Mérida S.A. de C.V.` |
| RFC | `NULL` |
| Activo | `True` |
| FechaAlta | `2026-05-08 20:06:32` |
| CreatedBy | `MIGRACION_FASE_A2` |

**RESULTADO:** ✅ **130MID EXISTE** en Sistema_Empresas

### Todas las empresas en Sistema_Empresas:
| ID | Código | Nombre | Razón Social |
|----|--------|--------|--------------|
| 5 | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. |
| 2 | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. |
| 3 | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. |
| 4 | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. |
| 1 | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. |

---

## 3. Resultado de Servidores_Conexiones

| Campo | Valor |
|-------|-------|
| id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| mongodb_id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| nombre | `130° MERIDA` |
| host | `130mid.ddns.net` |
| database | `softrestaurant10` |
| system_type | `SoftRestaurant` |
| activo | `True` |
| visible_en_operaciones | `True` |

**RESULTADO:** ✅ **130MID EXISTE** en Servidores_Conexiones

---

## 4. Resultado de Sistema_Sucursales

No se encontró tabla específica de sucursales relacionada con empresas. Las sucursales se manejan:
- En `RH_Cat_Sucursales` (Recursos Humanos)
- En el campo `sucursales` (JSON) dentro de `Servidores_Conexiones`
- En el campo `sucursal_origen_id` de `Unidades_Negocio` (NULL para 130MID)

---

## 5. Resultado de Usuario_EmpresasAsignacion

**RESULTADO:** ⚠️ **SIN ASIGNACIONES**

La tabla `Usuario_EmpresasAsignacion` está **VACÍA**. No hay ningún usuario asignado a ninguna empresa.

**Estructura de la tabla:**
- UsuarioEmpresaAsignacionID (bigint)
- UsuarioID (int)
- EmpresaID (int)
- EsPrincipal (bit)
- FechaInicio/FechaFin (datetime2)
- Activo (bit)
- Campos de auditoría

---

## 6. Resultado de server_registry para 130MID

### `list_unidades_negocio()`
```
✅ 130MID: 130° MERIDA (server_id: a5547321-1139-4d2b-9d53-182ca737b6b6)
✅ 130QRO: 130° QUERETARO (server_id: 1b230a06-ffaf-4c70-bd27-b1be3579dea6)
```

### `get_server_by_unidad_codigo('130MID')`
```
✅ Encontrado:
   system_type: SoftRestaurant
   config_origin: EDARSAHUB_SQL
```

### `get_server_by_id('a5547321-...')`
```
✅ Encontrado:
   id: a5547321-1139-4d2b-9d53-182ca737b6b6
   name: 130° MERIDA
   system_type: SoftRestaurant
   config_origin: EDARSAHUB_SQL
```

---

## 7. Conclusión

| Pregunta | Respuesta |
|----------|-----------|
| ¿130 MERIDA existe como unidad de negocio? | ✅ **SÍ** (código: 130MID) |
| ¿130 MERIDA existe como empresa? | ✅ **SÍ** (EmpresaID: 5, código: 130MID) |
| ¿130 MERIDA existe como servidor/conexión? | ✅ **SÍ** (id: a5547321-...) |
| ¿Hay diferencia entre empresa y unidad? | **SÍ** - Son tablas separadas pero con mismo código |
| ¿El sistema usa Unidades_Negocio pero no Sistema_Empresas? | **PARCIAL** - `server_registry` usa `Unidades_Negocio` |
| ¿Falta crear la empresa? | **NO** - Ya existe |
| ¿Hay código distinto? | **NO** - Ambas usan `130MID` |
| ¿Hay riesgo de duplicar? | **NO** - Ya está correctamente registrada |

### Hallazgo Adicional

`Usuario_EmpresasAsignacion` está **VACÍA**, lo cual significa que:
- Ningún usuario tiene empresas asignadas formalmente
- El sistema actual probablemente no usa esta tabla para permisos
- Los permisos se manejan por otro mecanismo (RBAC MongoDB, roles, etc.)

---

## 8. Propuesta de Corrección

**NO SE REQUIERE CORRECCIÓN** para 130 MERIDA.

La unidad, empresa y servidor existen correctamente en EDARSAHUB con:
- Código canónico: `130MID`
- Nombre: `130° MERIDA` (Unidades_Negocio y Servidores_Conexiones)
- Nombre: `130 MID` (Sistema_Empresas)
- Sistema: SoftRestaurant

---

## 9. Confirmación de No Modificación

- ✅ **NO se modificó** ninguna tabla en EDARSAHUB
- ✅ **NO se ejecutó** ningún INSERT/UPDATE/DELETE
- ✅ **NO se modificó** ningún archivo de código
- ✅ Diagnóstico 100% pasivo (solo SELECTs)

---

## 10. Recomendación

**Continuar con FASE T3.4-B2** (DDL para `tipos_movimiento`) sin necesidad de crear registros nuevos para 130 MERIDA.

La empresa 130MID está correctamente configurada en todas las tablas necesarias de EDARSAHUB.

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)
