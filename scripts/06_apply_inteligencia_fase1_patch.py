#!/usr/bin/env python3
"""
Aplica integración Fase 1 Inteligencia Comercial en EDARSAHUB.
Ejecutar desde la raíz del repo: python scripts/06_apply_inteligencia_fase1_patch.py
Hace backups .bak_inteligencia antes de modificar archivos.
"""
from pathlib import Path
import shutil

ROOT = Path.cwd()


def backup(path: Path):
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak_inteligencia")
        if not bak.exists():
            shutil.copy2(path, bak)


def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"OK ya aplicado: {path}")
        return
    if old not in text:
        raise RuntimeError(f"No encontré bloque esperado en {path}: {old[:120]}")
    backup(path)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"PATCH: {path}")


def append_after(path: Path, marker: str, addition: str):
    text = path.read_text(encoding="utf-8")
    if addition.strip() in text:
        print(f"OK ya aplicado: {path}")
        return
    if marker not in text:
        raise RuntimeError(f"No encontré marker en {path}: {marker[:120]}")
    backup(path)
    path.write_text(text.replace(marker, marker + addition, 1), encoding="utf-8")
    print(f"PATCH: {path}")


# 1) server.py: registrar router de inteligencia comercial después del router comercial
server = ROOT / "backend" / "server.py"
append_after(
    server,
    "api_router.include_router(comercial_router)\n",
    "\n# MÓDULO INTELIGENCIA COMERCIAL FASE 1: Dashboard SQL-first\nfrom modules.comercial.inteligencia_comercial_routes import router as inteligencia_comercial_router\napi_router.include_router(inteligencia_comercial_router)\n"
)

# 2) config.py: registrar job en configuración
config = ROOT / "backend" / "core" / "scheduler" / "config.py"
old_jobs = '''            "pedidos_detector": JobConfig(\n                job_id="pedidos_detector",\n                job_name="Pedidos Detector",\n                description="Detecta pedidos nuevos en MPro/Soft y dispara automatización operativa de compras",\n                enabled=pedidos_enabled,\n                interval_seconds=pedidos_interval,\n                batch_size=50,\n                timeout_seconds=300\n            )\n        }'''
new_jobs = '''            "pedidos_detector": JobConfig(\n                job_id="pedidos_detector",\n                job_name="Pedidos Detector",\n                description="Detecta pedidos nuevos en MPro/Soft y dispara automatización operativa de compras",\n                enabled=pedidos_enabled,\n                interval_seconds=pedidos_interval,\n                batch_size=50,\n                timeout_seconds=300\n            ),\n            "inteligencia_comercial_sync": JobConfig(\n                job_id="inteligencia_comercial_sync",\n                job_name="Inteligencia Comercial Sync Status",\n                description="Valida frescura de fuentes SQL para Portal de Inteligencia Comercial",\n                enabled=os.environ.get("SCHEDULER_INTELIGENCIA_COMERCIAL_ENABLED", "true").lower() == "true",\n                interval_seconds=int(os.environ.get("SCHEDULER_INTELIGENCIA_COMERCIAL_INTERVAL_SECONDS", "3600")),\n                batch_size=10,\n                timeout_seconds=180\n            )\n        }'''
replace_once(config, old_jobs, new_jobs)

# 3) scheduler_manager.py: imports, wrapper, registro y run now
manager = ROOT / "backend" / "core" / "scheduler" / "scheduler_manager.py"
append_after(
    manager,
    "from .jobs.pedidos_detector_job import create_pedidos_detector_job\n",
    "from .jobs.inteligencia_comercial_status_job import create_inteligencia_comercial_status_job\n"
)

append_after(
    manager,
    '''    async def _run_pedidos_detector_job(self):\n        """Wrapper async para ejecutar job de detección de pedidos."""\n        job_config = self.config.jobs.get("pedidos_detector")\n        if not job_config or not job_config.enabled:\n            return\n        \n        job = create_pedidos_detector_job(self.db, job_config)\n        await job.run()\n''',
    '''\n    async def _run_inteligencia_comercial_sync_job(self):\n        """Wrapper async para validar frescura de Inteligencia Comercial."""\n        job_config = self.config.jobs.get("inteligencia_comercial_sync")\n        if not job_config or not job_config.enabled:\n            return\n\n        job = create_inteligencia_comercial_status_job(self.db, job_config)\n        await job.run()\n'''
)

append_after(
    manager,
    '''            self._jobs["pedidos_detector"] = pedidos_config\n            logger.info(f"Job Pedidos Detector registrado: intervalo={pedidos_config.interval_seconds}s")\n''',
    '''\n        # Job Inteligencia Comercial Sync Status\n        inteligencia_config = self.config.jobs.get("inteligencia_comercial_sync")\n        if inteligencia_config and inteligencia_config.enabled:\n            if inteligencia_config.cron_expression:\n                trigger = CronTrigger.from_crontab(inteligencia_config.cron_expression)\n            else:\n                trigger = IntervalTrigger(seconds=inteligencia_config.interval_seconds)\n\n            self._scheduler.add_job(\n                self._run_inteligencia_comercial_sync_job,\n                trigger=trigger,\n                id="inteligencia_comercial_sync",\n                name="Inteligencia Comercial Sync Status",\n                replace_existing=True,\n                max_instances=1,\n                coalesce=True\n            )\n            self._jobs["inteligencia_comercial_sync"] = inteligencia_config\n            logger.info(f"Job Inteligencia Comercial registrado: intervalo={inteligencia_config.interval_seconds}s")\n'''
)

replace_once(
    manager,
    '''        elif job_id == "pedidos_detector":\n            await self._run_pedidos_detector_job()\n            return {"status": "executed", "job_id": job_id}\n        else:\n            return {"status": "error", "message": f"Job desconocido: {job_id}"}\n''',
    '''        elif job_id == "pedidos_detector":\n            await self._run_pedidos_detector_job()\n            return {"status": "executed", "job_id": job_id}\n        elif job_id == "inteligencia_comercial_sync":\n            await self._run_inteligencia_comercial_sync_job()\n            return {"status": "executed", "job_id": job_id}\n        else:\n            return {"status": "error", "message": f"Job desconocido: {job_id}"}\n'''
)

print("\nListo. Copia los archivos nuevos antes de ejecutar este patch si aún no existen:")
print("- backend/modules/comercial/inteligencia_comercial_routes.py")
print("- backend/core/scheduler/jobs/inteligencia_comercial_status_job.py")
