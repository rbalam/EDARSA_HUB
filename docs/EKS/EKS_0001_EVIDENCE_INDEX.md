# Índice de evidencia — EKS_0001

## Identificación

- Auditoría: `EKS_0001`
- Fecha UTC: `20260803T163201Z`
- Rama origen: `Edarsahub_Desarrollo`
- Commit origen: `68b65124cb00198c90447120d551716bd73a42da`
- Secretos reales detectados: ninguno
- Clasificación: evidencia generada almacenada fuera de Git

## Almacenamiento

- Tipo: volumen local montado
- Paquete: `/data/db/EDARSAHUB-AUDIT-EVIDENCE/2026/EKS_0001/EKS_0001_20260803T163201Z.tgz`
- Manifiesto: `/data/db/EDARSAHUB-AUDIT-EVIDENCE/2026/EKS_0001/manifest_20260803T163201Z.json`
- Checksums: `/data/db/EDARSAHUB-AUDIT-EVIDENCE/2026/EKS_0001/checksums_20260803T163201Z.sha256`
- Respaldo externo adicional confirmado: **no**

## Integridad

- SHA-256 del paquete: `a8e586c9d164f30c098b3a01945ad99ff43dc5614aad3a50a8e73c6c20626f24`
- SHA-256 del manifiesto: `455af8c9768214c69d19173718d65b64d57295df79ce640a4ed4397ade87dcd6`
- SHA-256 de checksums: `ccb9c738e60ca0a304b8eac5a1bdf1970503d9b98614f1c45294416eb118aa1a`
- Tamaño del paquete: `2561804` bytes
- Archivos archivados: `8`

## Contenido archivado

- `docs/EKS/EKS_0001_DUPLICADOS_CANDIDATOS.md`
- `docs/EKS/EKS_0001_FUENTES_CURADAS.json`
- `docs/EKS/EKS_0001_FUENTES_CURADAS.md`
- `docs/EKS/EKS_0001_INVENTARIO.json`
- `docs/EKS/EKS_0001_INVENTARIO_MAESTRO.md`
- `docs/EKS/EKS_0001_BRECHAS_DE_FUENTES.md`
- `docs/EKS/EKS_0001_COLA_CONSOLIDACION.md`
- `docs/EKS/EKS_0001_MATRIZ_CONSOLIDACION.md`

## Recuperación

```bash
sha256sum "/data/db/EDARSAHUB-AUDIT-EVIDENCE/2026/EKS_0001/EKS_0001_20260803T163201Z.tgz"
tar -xzf "/data/db/EDARSAHUB-AUDIT-EVIDENCE/2026/EKS_0001/EKS_0001_20260803T163201Z.tgz"
cd "EKS_0001"
sha256sum -c checksums.sha256
```

## Política

La evidencia no forma parte del runtime ni del código de EDARSAHUB.
El repositorio conserva este índice y la documentación canónica mantenible.

El volumen montado permite recuperación local, pero debe existir además una
copia en almacenamiento externo respaldado para garantizar conservación ante
pérdida total de la infraestructura.
