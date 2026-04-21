"""
extractor.py
Responsabilidad: Consumir la API REST de datos.gov.co y cargar
los registros en MongoDB. Usa upsert para evitar duplicados.
"""

import os
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv
from mongo_dao import MongoDAO

load_dotenv()

API_URL = os.getenv("API_URL", "https://www.datos.gov.co/resource/yb9r-2dsi.json")
PAGE_SIZE = 1000


def _generar_id_unico(registro: dict) -> str:
    clave = f"{registro.get('fecha_accidente','')}_{registro.get('hora_accidente','')}_{registro.get('sitio_exacto_accidente','')}"
    return hashlib.md5(clave.encode()).hexdigest()


def extraer_todos_los_datos() -> int:
    dao = MongoDAO()
    offset = 0
    total_procesados = 0

    print(f"[{datetime.now()}] Iniciando extracción de datos...")

    while True:
        params = {
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": "fecha_accidente ASC",
        }

        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            registros = response.json()
        except requests.RequestException as e:
            print(f"Error al consumir la API en offset {offset}: {e}")
            break

        if not registros:
            break

        for registro in registros:
            registro["_id"] = _generar_id_unico(registro)
            registro["cargado_en"] = datetime.utcnow()

            for campo in ["cant_heridos_en_sitio_accidente", "cant_muertos_en_sitio_accidente", "cantidad_accidentes"]:
                valor = registro.get(campo)
                try:
                    registro[campo] = int(valor) if valor is not None else 0
                except (ValueError, TypeError):
                    registro[campo] = 0

            try:
                registro["a_o_accidente"] = int(registro.get("a_o_accidente", 0))
            except (ValueError, TypeError):
                registro["a_o_accidente"] = 0

        dao.upsert_muchos(registros)
        total_procesados += len(registros)
        offset += PAGE_SIZE

        print(f"  → Procesados {total_procesados} registros...")

        if len(registros) < PAGE_SIZE:
            break

    print(f"[{datetime.now()}] Extracción completada. Total: {total_procesados} registros.")
    dao.cerrar()
    return total_procesados


if __name__ == "__main__":
    extraer_todos_los_datos()