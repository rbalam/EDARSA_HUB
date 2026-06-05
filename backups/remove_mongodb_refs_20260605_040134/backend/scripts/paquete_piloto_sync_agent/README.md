# PAQUETE DE EJECUCIÓN EXTERNA: PILOTO SYNC AGENT
# ================================================
# Versión: 1.0
# Fecha: 2026-04-23

## CONTENIDO DEL PAQUETE

```
paquete_piloto_sync_agent/
├── README.md                 # Este archivo
├── GUIA_PILOTO.md           # Guía paso a paso detallada
├── CHECKLIST_PILOTO.md      # Checklist para completar durante ejecución
├── sync_agent_piloto.py     # Script del agente
├── config_template.yaml     # Template de configuración
└── requirements.txt         # Dependencias Python
```

## INICIO RÁPIDO

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Copiar y editar configuración
cp config_template.yaml config.yaml
# Editar config.yaml con datos reales

# 3. Probar autenticación
python sync_agent_piloto.py --config config.yaml --test-only

# 4. Ejecutar sincronización
python sync_agent_piloto.py --config config.yaml
```

## DOCUMENTACIÓN COMPLETA

Ver `GUIA_PILOTO.md` para instrucciones detalladas.

## CHECKLIST

Usar `CHECKLIST_PILOTO.md` para documentar las 5 ejecuciones requeridas.

## SOPORTE

Para problemas, contactar al equipo de desarrollo con:
- Logs generados
- Reportes JSON
- Descripción del error
