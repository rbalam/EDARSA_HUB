"""
Estado administrativo persistente del Scheduler runtime.

Responsabilidades:
- consultar pausas administrativas persistidas;
- solicitar pausa/reanudación mediante procedimiento SQL controlado.

No realiza INSERT/UPDATE directo.
No usa Sys_Scheduler_Jobs.
No define cron, intervalos ni catálogo de jobs.
"""

from typing import List

from core.config.edarsahub_sql import get_edarsahub_connection


class SchedulerPersistentStateRepository:
    """Repositorio SQL del estado administrativo runtime."""

    @staticmethod
    def set_paused(
        job_id: str,
        paused: bool,
    ) -> bool:
        normalized = str(job_id or "").strip()

        if not normalized:
            raise ValueError("job_id requerido")

        if len(normalized) > 100:
            raise ValueError(
                "job_id excede 100 caracteres"
            )

        conn = get_edarsahub_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                EXEC dbo.sp_Scheduler_SetAdministrativePause
                    @JobID = %s,
                    @PausadoAdministrativo = %s
                """,
                (
                    normalized,
                    1 if paused else 0,
                ),
            )

            conn.commit()
            return True

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    @staticmethod
    def get_paused_job_ids() -> List[str]:
        conn = get_edarsahub_connection()

        try:
            cursor = conn.cursor(as_dict=True)

            cursor.execute(
                """
                SELECT JobID
                FROM dbo.Sys_Scheduler_RuntimeState
                WHERE PausadoAdministrativo = 1
                ORDER BY JobID
                """
            )

            rows = cursor.fetchall() or []

            return [
                str(row["JobID"])
                for row in rows
                if row.get("JobID") is not None
            ]

        finally:
            conn.close()
