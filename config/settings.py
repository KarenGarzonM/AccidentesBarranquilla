"""
config/settings.py

Fuente única de verdad para toda la configuración del proyecto.
Centraliza variables de entorno y constantes que antes estaban
dispersas en mongo_dao.py y extractor.py.

Uso:
    from config.settings import settings
    uri = settings.mongo_uri
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # ── MongoDB ────────────────────────────────────────────────────────────
    mongo_uri: str = field(
        default_factory=lambda: os.getenv("MONGO_URI", "")
    )
    mongo_db_name: str = field(
        default_factory=lambda: os.getenv("MONGO_DB_NAME", "accidentalidad_baq")
    )
    mongo_collection: str = "accidentes"
    mongo_timeout_ms: int = 10_000

    # Índices que se crean al inicializar la conexión
    mongo_indices: tuple = ("a_o_accidente", "mes_accidente", "gravedad_accidente")

    # ── API externa ────────────────────────────────────────────────────────
    api_url: str = field(
        default_factory=lambda: os.getenv(
            "API_URL",
            "https://www.datos.gov.co/resource/yb9r-2dsi.json",
        )
    )
    api_page_size: int = 1_000
    api_timeout_s: int = 30

    # ── Scheduler ─────────────────────────────────────────────────────────
    scheduler_interval_hours: int = 24

    # ── UI / Streamlit ─────────────────────────────────────────────────────
    app_title: str = "Accidentalidad Barranquilla"
    app_icon: str = "🚦"
    default_page_size: int = 50

    def validate(self) -> None:
        """
        Valida que las variables críticas estén presentes.
        Lanza EnvironmentError con un mensaje claro si falta algo.
        """
        if not self.mongo_uri:
            raise EnvironmentError(
                "No se encontró MONGO_URI. "
                "Crea un archivo .env con la variable MONGO_URI=<tu-conexión>."
            )


# Instancia global — importar esta en lugar de instanciar Settings() localmente.
settings = Settings()