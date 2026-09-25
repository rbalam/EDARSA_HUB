# BOS Direction - Gate 7 E2E R3

## Causa exacta corregida
R2 exigía que `EDARSAHUB_ROOT` existiera como variable exportada. El Worker canónico no requiere eso: sus componentes resuelven `ROOT` con `os.environ.get("EDARSAHUB_ROOT", "/app")`. R3 alinea únicamente la precondición del test con ese contrato y usa `/app` cuando la variable no está definida.

## Contrato E2E sin cambios
- siete gates formales A-G;
- evidencia ausente/no certificada no suma avance;
- `certified_gate_count + missing_or_uncertified_gate_count = 7`;
- evidencia real copiada a staging temporal;
- tres ciclos consecutivos;
- histórico y `latest` consistentes;
- porcentaje derivado exclusivamente del motor formal;
- `program_certified=true` sólo con 7/7.

## Seguridad
No toca Production, SQL, Mongo, Tablero Ejecutivo, Worker, Supervisor, watchdog ni cron del host.
