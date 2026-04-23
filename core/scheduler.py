"""
core/scheduler.py

Responsabilidad: programar la actualización automática de datos
usando APScheduler. Se importa desde app.py al arrancar Streamlit.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import settings
from data.extractors.api_extractor import extraer_todos_los_datos

_scheduler = None


def iniciar_scheduler() -> None:
    """
    Arranca el scheduler en segundo plano.
    El intervalo se lee desde settings.scheduler_interval_hours (default 24h).
    El guard _scheduler evita instancias duplicadas entre reruns de Streamlit.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        extraer_todos_los_datos,
        trigger="interval",
        hours=settings.scheduler_interval_hours,
        id="actualizar_datos",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    print(f"Scheduler iniciado: actualización cada {settings.scheduler_interval_hours}h.")


def detener_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)