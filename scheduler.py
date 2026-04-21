"""
scheduler.py
Responsabilidad: Programar la actualización automática de datos
usando APScheduler. Se importa desde app.py al arrancar Streamlit.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from extractor import extraer_todos_los_datos

_scheduler = None


def iniciar_scheduler(intervalo_horas: int = 24):
    """
    Arranca el scheduler en segundo plano.
    Se ejecuta una vez al iniciar la app y luego cada `intervalo_horas`.
    Streamlit puede llamar a esta función múltiples veces; el guard
    `_scheduler` evita instancias duplicadas.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return  # Ya está corriendo

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        extraer_todos_los_datos,
        trigger="interval",
        hours=intervalo_horas,
        id="actualizar_datos",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    print(f"Scheduler iniciado: actualización cada {intervalo_horas}h.")


def detener_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
