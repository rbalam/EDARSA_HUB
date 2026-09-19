"""Job canonico del scheduler para alertas de Catalogo Ampliado."""

import asyncio


async def execute_catalogo_ampliado_alertas(batch_size: int = 50) -> dict:
    from modules.catalogo_ampliado import alert_service

    planned = await asyncio.to_thread(alert_service.planificar_alertas)
    dispatched = await asyncio.to_thread(alert_service.despachar_alertas, batch_size)
    return {
        "planned": int((planned or {}).get("planned", 0)),
        "processed": int((dispatched or {}).get("processed", 0)),
        "items": (dispatched or {}).get("items", []),
    }
