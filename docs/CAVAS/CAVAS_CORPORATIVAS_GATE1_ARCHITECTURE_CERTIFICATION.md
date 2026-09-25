# Cavas Corporativas - Gate 1 Architecture Certification

## Alcance
Certificacion formal de la arquitectura ya congelada. Este documento no modifica el diseño ni autoriza DDL/DML.

## Invariantes congeladas
1. SQL Server es la fuente canonica del dominio.
2. No se introduce Mongo como fuente, cache o persistencia nueva.
3. Cava fisica, asignacion, contrato, membresia, socio, botella y movimiento son identidades/eventos distintos y no se conflan.
4. La identidad de personas/clientes reutiliza `Cliente_Catalogo`; no se crea un maestro paralelo de entidades.
5. Los productos reutilizan el catalogo comercial canonico cuando existe y usan Catalogo Extendido cuando no existe, sin crear `Productos_Cava` ni duplicar producto por nombre.
6. Consumo observado en Cava no es venta, ingreso, ticket ni unidad comercial salvo existencia de transaccion comercial real.
7. Botellas propias del socio se controlan por custodia/inventario de Cavas y no consumen inventario del POS.
8. Beneficios/operaciones corporativas son backend-authoritative; el frontend solo consume contratos canonicos.
9. RBAC reutiliza el esquema SQL canonico existente; no se crea un RBAC paralelo.
10. El dominio es multiempresa y multiunidad y reutiliza contexto corporativo/unidad existente.
11. Cavas no depende de forma especifica de SoftRestaurant, MPRO u otro POS/ERP; las integraciones externas llegan por contratos/adaptadores canonicos.
12. Produccion no se modifica dentro de este gate.

## Evidencia de implementacion posterior que debe seguir siendo compatible
- `backend/modules/cavas_corporativas/domain.py`
- `backend/modules/cavas_corporativas/repository.py`
- `backend/modules/cavas_corporativas/service.py`
- `backend/modules/cavas_corporativas/routes.py`
- tests del dominio Cavas Corporativas

## Criterio terminal
Gate 1 queda formalmente certificado solo si el Worker devuelve `CERTIFIED`, `percent_complete=100`, `quality_gate=PASS`, `tests=PASS`, sin blockers y `production_touched=false`.
