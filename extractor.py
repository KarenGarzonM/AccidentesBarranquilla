"""
extractor.py
Responsabilidad: Consumir la API REST de datos.gov.co y cargar
los registros en MongoDB.
- extraer_todos_los_datos(): upsert incremental (no borra datos previos)
- recargar_todos_los_datos(): borra la colección y vuelve a insertar todo
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


def _normalizar_registro(registro: dict) -> dict:
    """
    Limpia y tipifica los campos numéricos de un registro.
    La API devuelve valores como "1.0" (string con decimal),
    por eso se hace float() antes de int().
    """
    registro["_id"] = _generar_id_unico(registro)
    registro["cargado_en"] = datetime.utcnow()

    for campo in ["cant_heridos_en_sitio_accidente", "cant_muertos_en_sitio_accidente", "cantidad_accidentes"]:
        valor = registro.get(campo)
        try:
            registro[campo] = int(float(valor)) if valor is not None else 0
        except (ValueError, TypeError):
            registro[campo] = 0

    try:
        registro["a_o_accidente"] = int(float(registro.get("a_o_accidente", 0)))
    except (ValueError, TypeError):
        registro["a_o_accidente"] = 0

    return registro


def _descargar_todos(callback=None) -> list:
    """
    Descarga todos los registros de la API con paginación.
    `callback(total_descargados)` se llama tras cada página si se proporciona.
    """
    offset = 0
    todos = []

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

        todos.extend([_normalizar_registro(r) for r in registros])
        offset += PAGE_SIZE

        if callback:
            callback(len(todos))

        print(f"  → Descargados {len(todos)} registros...")

        if len(registros) < PAGE_SIZE:
            break

    return todos


def extraer_todos_los_datos(callback=None) -> int:
    """Modo incremental: upsert (no elimina datos previos)."""
    dao = MongoDAO()
    print(f"[{datetime.now()}] Iniciando extracción incremental...")

    registros = _descargar_todos(callback)

    if registros:
        dao.upsert_muchos(registros)

    print(f"[{datetime.now()}] Extracción completada. Total: {len(registros)} registros.")
    dao.cerrar()
    return len(registros)


def recargar_todos_los_datos(callback=None) -> int:
    """
    Modo recarga completa: elimina TODO lo que hay en MongoDB
    e inserta los datos frescos de la API. Evita duplicados por diseño.
    """
    dao = MongoDAO()
    print(f"[{datetime.now()}] Iniciando recarga completa...")

    # 1. Descargar primero (si falla, no borramos nada)
    registros = _descargar_todos(callback)

    if not registros:
        print("No se obtuvieron registros de la API. Abortando recarga.")
        dao.cerrar()
        return 0

    # 2. Borrar colección existente
    eliminados = dao.eliminar_todos()
    print(f"  → {eliminados} documentos eliminados de MongoDB.")

    # 3. Insertar los nuevos
    dao.insertar_muchos(registros)
    print(f"[{datetime.now()}] Recarga completada. {len(registros)} registros insertados.")

    dao.cerrar()
    return len(registros)


if __name__ == "__main__":
    recargar_todos_los_datos()