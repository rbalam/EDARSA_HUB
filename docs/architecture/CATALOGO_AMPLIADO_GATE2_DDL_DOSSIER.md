# Catalogo Ampliado / Gobierno Corporativo - Gate 2 DDL Dossier

Gate 1 R4 quedo CERTIFIED_READ_ONLY al 100%. Gate 2 persiste diseno SQL y NO ejecuta SQL.

## Reutilizar
Sistema_Empresas, Usuario_Catalogo, Cliente_Catalogo, Proveedor_Catalogo, Cliente_Contactos y Proveedor_Contactos.

## Crear
11 tablas: Gobierno_EmpresaConfiguracion, Gobierno_Persona, Gobierno_PersonaVinculo, Gobierno_RolCorporativoCatalogo, Gobierno_PersonaEmpresaRol, Gobierno_TipoDocumento, Gobierno_Documento, Gobierno_DocumentoVersion, Gobierno_DocumentoMovimiento, Gobierno_AlertaRegla y Gobierno_AlertaEvento.

Gobierno_Persona es la identidad transversal y Gobierno_PersonaVinculo usa FK tipadas a maestros existentes. Roles corporativos permanecen separados de RBAC. Documentos aportan versionado, hash, OCR, vigencia y kardex sin copiar automaticamente documentos de otros dominios. Alertas modelan regla/evento pero no sustituyen motores canonicos de tareas/notificaciones.

La migracion es idempotente por OBJECT_ID y fail-closed si faltan maestros canonicos. No contiene semillas ni DML de negocio. El siguiente paso es preflight READ_ONLY fijando el blob SHA exacto antes de ejecutar en Desarrollo. Production=false.
