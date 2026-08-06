# Roles y jerarquía

| ID | Código | Nombre | Nivel | Activo |
| --- | --- | --- | --- | --- |
| 6 | SUPERADMIN | SuperAdministrador | 100 | True |
| 1 | ADMIN | Administrador | 90 | True |
| 14 | CRM_ADMIN | CRM_Administrador | 90 | False |
| 17 | ADMIN_COMERCIAL | Administrador Comercial | 85 | True |
| 10 | DIRECCION | Dirección | 80 | True |
| 16 | CRM_AUDIT | CRM_Auditor | 70 | False |
| 22 | GERENTE | Gerente | 70 | False |
| 11 | GERENTE_OPS | Gerente Operaciones | 60 | True |
| 18 | GERENTE_UNIDAD | Gerente de Unidad | 55 | True |
| 15 | CRM_EJEC | CRM_Ejecutivo | 50 | False |
| 7 | SUPERVISOR | Supervisor | 50 | True |
| 21 | CONFIGURADOR_COMERCIAL | Configurador Comercial | 45 | True |
| 19 | ANALISTA_COMERCIAL | Analista Comercial | 40 | True |
| 13 | AUDITOR | Auditor | 30 | True |
| 12 | OPERADOR | Operador | 20 | True |
| 25 | PRUEBA_RBAC_SQL | PRUEBA_RBAC_SQL | 10 | True |
| 26 | ROL_PRUEBA_SATELITES | Rol Prueba Satélites (Solo Lectura) | 10 | True |
| 8 | USUARIO | Usuario | 10 | False |
| 20 | VISOR_COMERCIAL | Visor Comercial | 10 | True |
| 9 | VISOR | Visor | 5 | True |
| 3 | COMPRAS | Compras | 0 | False |
| 39 | COORDINADOR_GENERAL_SISTEMAS_2 | Coordinador General Sistemas Region 784 Suroeste | 0 | False |
| 38 | COORDINADOR_GENERAL_SISTEMAS_R | Coordinador General Sistemas Region 784 Norte | 0 | False |
| 2 | GERENCIA | Gerencia | 0 | True |
| 36 | GERENTE_REGION_OPER_761_NORTE | Gerente Region Oper 761 Norte | 0 | False |
| 37 | GERENTE_REGION_OPER_761_SUROES | Gerente Region Oper 761 Suroeste | 0 | False |
| 34 | QA_COLISION_1785416742 | QA Colision 1785416742 | 0 | False |
| 35 | QA_COLISION_1785416742B_DISTIN | QA Colision 1785416742b distinto | 0 | False |
| 30 | QA_PRUEBA_SUFIJO | QA Prueba Sufijo | 0 | False |
| 28 | ROL_DE_PRUEBA_CON_NOMBRE_EXTRE | Rol Renombrado Con Otro Nombre También Muy Largo Que Antes Rompía | 0 | False |
| 29 | ROL_DE_PRUEBA_TESTING_NOMBRE_E | Rol Renombrado Con Otro Nombre Largo Y Acentós Extra Test | 0 | False |
| 5 | TESORERIA | Tesoreria | 0 | True |
| 4 | VENTAS | Ventas | 0 | False |

## Máxima jerárquica

SUPERADMIN debe tener al menos todos los permisos efectivos disponibles para ADMINISTRADOR y roles inferiores, salvo una restricción empresarial explícita y documentada.
