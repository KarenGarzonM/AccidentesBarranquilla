"""
data/repositories/accidentes_repo.py

Responsabilidad: operaciones CRUD y consultas generales
sobre la colección de accidentes.

Las aggregations analíticas viven en analytics_repo.py.
"""

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from pymongo.collection import Collection


# ── Escritura ──────────────────────────────────────────────────────────────

def upsert_muchos(col: Collection, registros: list) -> None:
    operaciones = [
        UpdateOne({"_id": r["_id"]}, {"$set": r}, upsert=True)
        for r in registros
    ]
    try:
        col.bulk_write(operaciones, ordered=False)
    except BulkWriteError as e:
        print(f"Advertencia en bulk_write: {e.details.get('nInserted', 0)} insertados.")


def eliminar_todos(col: Collection) -> int:
    return col.delete_many({}).deleted_count


def insertar_muchos(col: Collection, registros: list) -> None:
    if registros:
        try:
            col.insert_many(registros, ordered=False)
        except Exception as e:
            print(f"Advertencia en insert_many: {e}")


# ── Lectura general ────────────────────────────────────────────────────────

def contar_total(col: Collection) -> int:
    return col.count_documents({})


def obtener_anios_disponibles(col: Collection) -> list:
    anios = col.distinct("a_o_accidente")
    return sorted([a for a in anios if isinstance(a, int) and a > 2000])


def obtener_gravedades(col: Collection) -> list:
    return sorted([g for g in col.distinct("gravedad_accidente") if g])


def obtener_clases(col: Collection) -> list:
    return sorted([c for c in col.distinct("clase_accidente") if c])


def obtener_documentos_paginados(
    col: Collection,
    pagina: int = 0,
    por_pagina: int = 50,
    anio: str = None,
    gravedad: str = None,
) -> list:
    campos = {
        "_id": 0,
        "fecha_accidente": 1,
        "hora_accidente": 1,
        "gravedad_accidente": 1,
        "clase_accidente": 1,
        "sitio_exacto_accidente": 1,
        "cant_heridos_en_sitio_accidente": 1,
        "cant_muertos_en_sitio_accidente": 1,
        "cantidad_accidentes": 1,
        "a_o_accidente": 1,
        "mes_accidente": 1,
        "dia_accidente": 1,
    }

    query = {}
    if anio and anio != "Todos":
        try:
            query["a_o_accidente"] = int(anio)
        except ValueError:
            pass
    if gravedad and gravedad != "Todas":
        query["gravedad_accidente"] = gravedad

    cursor = (
        col.find(query, campos)
        .sort("fecha_accidente", -1)
        .skip(pagina * por_pagina)
        .limit(por_pagina)
    )
    return list(cursor)


def contar_con_filtros(
    col: Collection,
    anio: str = None,
    gravedad: str = None,
) -> int:
    query = {}
    if anio and anio != "Todos":
        try:
            query["a_o_accidente"] = int(anio)
        except ValueError:
            pass
    if gravedad and gravedad != "Todas":
        query["gravedad_accidente"] = gravedad
    return col.count_documents(query)


def resumen_coleccion(col: Collection) -> dict:
    total = contar_total(col)
    anios = obtener_anios_disponibles(col)

    pipeline_heridos = [{"$group": {"_id": None, "total": {"$sum": {
        "$cond": [{"$isNumber": "$cant_heridos_en_sitio_accidente"},
                  "$cant_heridos_en_sitio_accidente", 0]
    }}}}]
    pipeline_muertos = [{"$group": {"_id": None, "total": {"$sum": {
        "$cond": [{"$isNumber": "$cant_muertos_en_sitio_accidente"},
                  "$cant_muertos_en_sitio_accidente", 0]
    }}}}]

    res_h = list(col.aggregate(pipeline_heridos))
    res_m = list(col.aggregate(pipeline_muertos))

    return {
        "total_documentos": total,
        "anios_cubiertos": f"{min(anios)} – {max(anios)}" if anios else "N/A",
        "total_heridos": res_h[0]["total"] if res_h else 0,
        "total_muertos": res_m[0]["total"] if res_m else 0,
    }