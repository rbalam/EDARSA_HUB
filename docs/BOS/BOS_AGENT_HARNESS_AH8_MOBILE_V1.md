# AH8 - Mobile V1

AH8 define Mobile como cliente/satelite gobernado por BOS. No crea una fuente de verdad paralela.

## Baseline de arquitectura
La implementacion movil futura recomendada es React Native + TypeScript con Expo dev builds/prebuild y ADR de escape cuando una capacidad nativa lo requiera. AH8 V1 no crea aun la app ni ejecuta builds.

## Offline write envelope
Contrato `edarsahub.bos-mobile-operation.v1`: operation_uuid, idempotency_key, user_id, installation_id, device_id, Empresa/Unidad, base_version, occurred_at_utc, payload_sha256 y operation_type.

## Autoridad del servidor
El servidor responde exclusivamente con ACCEPT, REJECT, CONFLICT, RETRY o REQUIRES_REVIEW. Mobile nunca resuelve por generic last-write-wins en finanzas, inventarios o dominios auditables.

## Seguridad futura obligatoria
Tokens en Keychain/Keystore; ningun secreto en SQLite. Minimizar PII, aplicar TTL, soportar revocacion de dispositivo y remote logout. Estas capacidades requieren gates posteriores de implementacion; este gate solo fija el contrato.

## Maximas
Sin backend/core nuevo, sin SQL/Mongo, sin red, sin app paralela, sin Production. BOS y RBAC backend siguen mandando.

## Siguiente gate
AH9 Control Plane debe observar y gobernar Agent Harness, gates, budgets, evidencia y estados sin crear un segundo origen de verdad.
