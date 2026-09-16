# Cavas Corporativas - Gate 12C - Alineacion BOS Entidad / Roles

## Decision corregida
El Gate 12B propuso como posibilidad futura agregar ClienteID a CavaSocios_Socios. Gate 12C corrige esa direccion antes de implementarla: no se agregara una relacion directa nueva a Cliente_Catalogo si la arquitectura BOS vigente ya dispone de una identidad transversal reutilizable.

## Principio BOS
Una persona o entidad de negocio debe tener una sola identidad transversal. Cliente, proveedor, socio, usuario u otros conceptos operativos no deben convertirse en identidades paralelas; deben expresarse como roles/vinculos hacia los dominios que correspondan.

## Arquitectura observada en repositorio
- Gobierno_Persona esta documentada como identidad transversal.
- Gobierno_PersonaVinculo enlaza esa identidad mediante FK tipadas a maestros existentes como Usuario_Catalogo, Cliente_Catalogo, Proveedor_Catalogo y contactos.
- Gobierno_PersonaEmpresaRol modela roles corporativos y permanece separado de RBAC.
- Por tanto, la arquitectura existente es parcialmente BOS: ya existe identidad transversal, pero Cliente/Proveedor siguen siendo maestros de dominio enlazados y no simples filas del catalogo de roles corporativos.

## Contrato para Cavas
1. CavaSocios_Socios no es una identidad maestra; es una membresia/rol operativo de Cava.
2. SocioID se conserva como PK operacional y como destino de las FK de Botellas, Cargos y Movimientos.
3. La identidad humana del socio debe resolver a Gobierno_Persona cuando exista y este certificado como canonico en SQL runtime.
4. Cliente_Catalogo puede seguir siendo un maestro comercial legacy/canonico del dominio cliente, pero no debe convertirse en una segunda identidad de la persona. Su enlace debe pasar por Gobierno_PersonaVinculo.
5. No agregar ClienteID directamente a CavaSocios_Socios en este Gate.
6. No crear Entidad_Catalogo paralelo.
7. No eliminar ClienteCRMID, NombreCompleto, Email o Telefono aun; quedan como legado de transicion hasta tener cobertura y consumidores migrados.
8. Estado de cliente y estado de membresia Cava son conceptos distintos y no deben colapsarse.

## Relacion objetivo
Gobierno_Persona (identidad transversal)
  -> Gobierno_PersonaVinculo -> Cliente_Catalogo / Usuario_Catalogo / Proveedor_Catalogo cuando aplique
  -> membresia Cava (CavaSocios_Socios) mediante una unica relacion canonica a definir solo si no existe ya fisicamente
  -> CavaSocios_Botellas / Cargos / Movimientos continuan por SocioID

## Regla de no duplicacion
Antes de crear PersonaID o cualquier nueva FK en CavaSocios_Socios, el siguiente Gate debe demostrar con sys.columns/sys.foreign_keys que no existe ya una relacion reutilizable. Si existe, se reutiliza. Si no existe, la unica extension permitida sera una FK directa a la identidad transversal Gobierno_Persona, no otra FK redundante a Cliente_Catalogo.

## Roles
Cliente/proveedor/socio no deben confundirse con RBAC. RBAC controla permisos de acceso al sistema. Los roles/vinculos BOS describen la relacion de una identidad con dominios de negocio. Gobierno_PersonaEmpresaRol actualmente cubre roles corporativos; Gate 12C no asume que ya cubra SOCIO_CAVA. Si el catalogo de roles no contiene esa semantica, debe marcarse EXTEND o NOT_DETERMINABLE y no inventarse durante este Gate.

## Compatibilidad legacy
- ClienteCRMID uniqueidentifier no se castea a ClienteID int ni a PersonaID bigint.
- NombreCompleto/Email/Telefono permanecen fisicamente durante la transicion.
- No dual-write silencioso.
- No cambios a Botellas/Cargos/Movimientos.

## Condicion para un Gate 12D de implementacion
Solo autorizar DDL/codigo cuando se certifique: existencia y esquema runtime de Gobierno_Persona y Gobierno_PersonaVinculo; ausencia/presencia de relacion CavaSocios->Persona; semantica disponible para rol SOCIO_CAVA o extension necesaria; estrategia determinista para vincular los 2 socios existentes sin adivinar identidad; y cero duplicacion de fuentes de verdad.
