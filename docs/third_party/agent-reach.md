# Agent-Reach incorporado en EDARSAHUB

## Procedencia

- Proyecto original: Panniantong/Agent-Reach
- Repositorio original: https://github.com/Panniantong/Agent-Reach
- Rama externa importada: main
- Commit externo importado: 71c541577238d87057af496e9588504e552f8952
- Ruta interna: third_party/agent-reach
- Metodo de incorporacion: snapshot versionado mediante git fetch y git read-tree
- Licencia declarada por el proyecto: MIT

## Objetivo dentro de EDARSA BOS

Agent-Reach se incorpora como componente externo para adquirir evidencia de
inteligencia competitiva desde redes sociales, sitios web, videos, RSS y otras
fuentes publicas.

Su codigo queda almacenado fisicamente dentro de EDARSAHUB para evitar una
dependencia operativa del repositorio externo.

## Limites arquitectonicos

Agent-Reach no constituye una fuente canonica de:

- ventas;
- costos;
- informacion financiera;
- presupuestos;
- indicadores internos;
- decisiones aprobadas por Direccion.

La informacion recopilada debera conservarse como evidencia externa,
normalizarse y analizarse mediante componentes propios de EDARSA BOS.

## Reglas obligatorias

1. No almacenar cookies, tokens, sesiones o credenciales en Git.
2. No ejecutar Agent-Reach dentro del proceso principal del backend.
3. Ejecutarlo posteriormente como worker o servicio aislado.
4. No concederle escritura directa sobre tablas canonicas.
5. Conservar URL, plataforma, competidor, fecha y trazabilidad.
6. Separar hechos observados, inferencias, hipotesis y recomendaciones.
7. Auditar dependencias antes de habilitarlo operativamente.
8. Respetar restricciones y limites de cada plataforma.
9. Toda actualizacion futura debe registrar el nuevo commit externo importado.
