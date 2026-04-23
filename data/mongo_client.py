"""
data/mongo_client.py

Responsabilidad única: abrir y cerrar la conexión a MongoDB Atlas.
Ningún otro módulo instancia MongoClient directamente.
"""

from pymongo import MongoClient
from pymongo.collection import Collection
from config.settings import settings


def get_collection() -> Collection:
    """
    Abre una conexión a MongoDB y retorna la colección principal.

    Uso típico (en repos y DAOs):
        col = get_collection()
        col.find({...})

    Nota: en Streamlit usar @st.cache_resource sobre esta función
    para reutilizar la conexión entre reruns.
    """
    settings.validate()

    client = MongoClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=settings.mongo_timeout_ms,
    )
    db = client[settings.mongo_db_name]
    col = db[settings.mongo_collection]

    # Índices garantizados al abrir la conexión
    for campo in settings.mongo_indices:
        col.create_index(campo)

    return col