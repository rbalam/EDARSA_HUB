# EDARSAHUB — RBAC Gap Analysis Mongo vs SQL (solo lectura)

Fecha: 2026-06-07T19:27:00

## Estado

✅ Solo lectura. No se borró/modificó Mongo ni SQL. No se migró RBAC en bloque.

## Fuentes Mongo

### roles
- edarsa_hub.rbac_roles: **6** docs
- edarsa_hub.roles: **4** docs
- edarsa_hub.sec_roles: **5** docs
### permisos
- edarsa_hub.rbac_permisos: **43** docs
- edarsa_hub.sec_permisos_catalogo: **90** docs
- edarsa_hub.permisos_catalogos: **8** docs
- test_database.sec_permisos_catalogo: **89** docs
### asignaciones
- edarsa_hub.rbac_usuarios_roles: **72** docs

## Fuentes SQL

### roles
- dbo.Sistema_RBAC_Roles: **6** rows
- dbo.Usuario_Roles: **22** rows
### permisos
- dbo.RBAC_Permisos: **9** rows
- dbo.Sistema_RBAC_Permisos: **5** rows
- dbo.Usuario_PermisosRolModulo: **459** rows
- dbo.Sistema_Modulos: **28** rows
### asignaciones
- dbo.Usuario_PermisosRolModulo: **459** rows
- dbo.Usuario_Roles: **22** rows

## Resumen global

- CUBIERTO_EN_SQL: **7**
- POSIBLE_FALTANTE_SQL: **162**
- SQL_EVOLUCIONADO_NO_EXISTIA_EN_MONGO: **52**

## Roles

- CUBIERTO_EN_SQL: **7**
- POSIBLE_FALTANTE_SQL: **6**
- SQL_EVOLUCIONADO_NO_EXISTIA_EN_MONGO: **15**

## Permisos

- POSIBLE_FALTANTE_SQL: **140**
- SQL_EVOLUCIONADO_NO_EXISTIA_EN_MONGO: **37**

## Asignaciones usuario-rol

- POSIBLE_FALTANTE_SQL: **16**

## Ejemplos POSIBLE_FALTANTE_SQL (en Mongo, no en SQL)

| Tipo | Key | Mongo source | Mongo nombre |
|---|---|---|---|
| ROL | administrador_de_usuarios | edarsa_hub.sec_roles | Administrador de Usuarios |
| ROL | gerente_ops | edarsa_hub.rbac_roles | GERENTE_OPS |
| ROL | gestor_de_sistema | edarsa_hub.sec_roles | Gestor de Sistema |
| ROL | visor_de_administracion | edarsa_hub.sec_roles | Visor de Administración |
| ROL | visor_de_estructura_organizacional | edarsa_hub.sec_roles | Visor de Estructura Organizacional |
| ROL | visor_del_sistema | edarsa_hub.sec_roles | Visor del Sistema |
| PERMISO | 69e75f79e288072c3af9ed91 | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e760abe288072c3af9ee41 | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e760bae288072c3af9ee52 | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e760cfe288072c3af9ee65 | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e765afe288072c3afa0e48 | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e7661ae288072c3afa163d | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e76628e288072c3afa176d | edarsa_hub.permisos_catalogos | - |
| PERMISO | 69e90ae4f646e5db59dd5c47 | edarsa_hub.permisos_catalogos | - |
| PERMISO | auditoria_auditoria_informes_crear | edarsa_hub.sec_permisos_catalogo | AUDITORIA_INFORMES_CREAR |
| PERMISO | auditoria_auditoria_informes_gestionar | edarsa_hub.sec_permisos_catalogo | AUDITORIA_INFORMES_GESTIONAR |
| PERMISO | auditoria_auditoria_informes_ver | edarsa_hub.sec_permisos_catalogo | AUDITORIA_INFORMES_VER |
| PERMISO | auditoria_auditoria_programar | edarsa_hub.sec_permisos_catalogo | AUDITORIA_PROGRAMAR |
| PERMISO | auditorias_auditoria_gestionar | edarsa_hub.rbac_permisos | AUDITORIA_GESTIONAR |
| PERMISO | auditorias_auditoria_programar | edarsa_hub.rbac_permisos | AUDITORIA_PROGRAMAR |
| PERMISO | auditorias_auditoria_ver | edarsa_hub.rbac_permisos | AUDITORIA_VER |
| PERMISO | auth_rbac_admin | edarsa_hub.rbac_permisos | RBAC_ADMIN |
| PERMISO | auth_roles_gestionar | edarsa_hub.rbac_permisos | ROLES_GESTIONAR |
| PERMISO | auth_roles_ver | edarsa_hub.rbac_permisos | ROLES_VER |
| PERMISO | auth_usuarios_gestionar | edarsa_hub.rbac_permisos | USUARIOS_GESTIONAR |
| PERMISO | auth_usuarios_ver | edarsa_hub.rbac_permisos | USUARIOS_VER |
| PERMISO | cargos_cargos_aplicar | edarsa_hub.rbac_permisos | CARGOS_APLICAR |
| PERMISO | cargos_cargos_autorizar | edarsa_hub.rbac_permisos | CARGOS_AUTORIZAR |
| PERMISO | cargos_cargos_cancelar | edarsa_hub.rbac_permisos | CARGOS_CANCELAR |
| PERMISO | cargos_cargos_crear | edarsa_hub.rbac_permisos | CARGOS_CREAR |
| PERMISO | cargos_cargos_rechazar | edarsa_hub.rbac_permisos | CARGOS_RECHAZAR |
| PERMISO | cargos_cargos_revertir | edarsa_hub.rbac_permisos | CARGOS_REVERTIR |
| PERMISO | cargos_cargos_ver | edarsa_hub.rbac_permisos | CARGOS_VER |
| PERMISO | comercial_comercial_dashboard_ver | edarsa_hub.sec_permisos_catalogo | COMERCIAL_DASHBOARD_VER |
| PERMISO | comercial_comercial_metas_editar | edarsa_hub.sec_permisos_catalogo | COMERCIAL_METAS_EDITAR |
| PERMISO | comercial_comercial_metas_ver | edarsa_hub.sec_permisos_catalogo | COMERCIAL_METAS_VER |
| PERMISO | comercial_comercial_pax_ver | edarsa_hub.sec_permisos_catalogo | COMERCIAL_PAX_VER |
| PERMISO | comercial_comercial_tablero_ver | edarsa_hub.sec_permisos_catalogo | COMERCIAL_TABLERO_VER |
| PERMISO | comercial_comercial_ticket_ver | edarsa_hub.sec_permisos_catalogo | COMERCIAL_TICKET_VER |
| PERMISO | comercial_comercial_ventas_exportar | edarsa_hub.sec_permisos_catalogo | COMERCIAL_VENTAS_EXPORTAR |

## Criterio

```text
CUBIERTO_EN_SQL: existe en ambos → candidato a borrado futuro con respaldo.
POSIBLE_FALTANTE_SQL: en Mongo, no en SQL → revisar manual; NO migrar en bloque.
SQL_EVOLUCIONADO_NO_EXISTIA_EN_MONGO: en SQL, no en Mongo → sin acción.
```
