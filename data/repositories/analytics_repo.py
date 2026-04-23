"""
data/repositories/analytics_repo.py

Responsabilidad: aggregations analíticas sobre la colección de accidentes.
Todas las funciones reciben col: Collection y un dict opcional de filtros.
"""

from collections import defaultdict
from pymongo.collection import Collection


# ── Utilidad interna ───────────────────────────────────────────────────────

def _pipeline_base(filtros: dict = None) -> list:
    """Construye el $match inicial según los filtros activos."""
    if not filtros:
        return []

    match = {}
    if filtros.get("anios"):
        match["a_o_accidente"] = {"$in": filtros["anios"]}
    if filtros.get("gravedad"):
        match["gravedad_accidente"] = {"$in": filtros["gravedad"]}
    if filtros.get("clase"):
        match["clase_accidente"] = {"$in": filtros["clase"]}

    return [{"$match": match}] if match else []


def _parsear_hora(hora_raw: str) -> int | None:
    """
    Convierte strings de hora a entero 0-23.
    Soporta: '01:30:00:am', '14:30:00', '2:30:00 PM', '02:30 PM'.
    """
    if not hora_raw or not isinstance(hora_raw, str):
        return None

    hora_raw = hora_raw.strip()
    upper = hora_raw.upper()

    es_pm = upper.endswith("PM")
    es_am = upper.endswith("AM")

    for sufijo in [":AM", ":PM", " AM", " PM"]:
        if upper.endswith(sufijo):
            hora_raw = hora_raw[: -len(sufijo)].strip()
            break

    partes = hora_raw.split(":")
    if not partes:
        return None

    try:
        h = int(partes[0])
    except ValueError:
        return None

    if es_pm and h != 12:
        h += 12
    elif es_am and h == 12:
        h = 0

    return h if 0 <= h <= 23 else None


# ── Queries analíticas ─────────────────────────────────────────────────────

def accidentes_por_anio(col: Collection, filtros: dict = None) -> list:
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$a_o_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        {"$sort": {"_id": 1}},
    ]
    return list(col.aggregate(pipeline))


def accidentes_por_mes(col: Collection, filtros: dict = None) -> list:
    orden = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$mes_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
    ]
    resultados = list(col.aggregate(pipeline))
    resultados.sort(
        key=lambda x: orden.index(x["_id"]) if x["_id"] in orden else 99
    )
    return resultados


def accidentes_por_tipo(col: Collection, filtros: dict = None) -> list:
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$clase_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        {"$sort": {"total": -1}},
    ]
    return list(col.aggregate(pipeline))


def accidentes_por_gravedad(col: Collection, filtros: dict = None) -> list:
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$gravedad_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        {"$sort": {"total": -1}},
    ]
    return list(col.aggregate(pipeline))


def accidentes_por_hora(col: Collection, filtros: dict = None) -> list:
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$hora_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
    ]
    resultados = list(col.aggregate(pipeline))

    conteo = defaultdict(int)
    for r in resultados:
        h = _parsear_hora(r.get("_id") or "")
        if h is not None:
            conteo[h] += r["total"]

    return [{"_id": h, "total": conteo[h]} for h in sorted(conteo)]


def accidentes_por_dia_semana(col: Collection, filtros: dict = None) -> list:
    orden = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$dia_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
    ]
    resultados = list(col.aggregate(pipeline))
    resultados.sort(
        key=lambda x: orden.index(x["_id"]) if x["_id"] in orden else 99
    )
    return resultados


def top_sitios_peligrosos(
    col: Collection, top_n: int = 10, filtros: dict = None
) -> list:
    pipeline = _pipeline_base(filtros) + [
        {"$group": {"_id": "$sitio_exacto_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        {"$sort": {"total": -1}},
        {"$limit": top_n},
    ]
    return list(col.aggregate(pipeline))


def maximos_victimas(col: Collection, filtros: dict = None) -> dict:
    pipeline_h = _pipeline_base(filtros) + [
        {"$group": {"_id": None, "max_heridos": {"$max": "$cant_heridos_en_sitio_accidente"}}},
    ]
    pipeline_m = _pipeline_base(filtros) + [
        {"$group": {"_id": None, "max_muertos": {"$max": "$cant_muertos_en_sitio_accidente"}}},
    ]
    res_h = list(col.aggregate(pipeline_h))
    res_m = list(col.aggregate(pipeline_m))
    return {
        "max_heridos": res_h[0]["max_heridos"] if res_h else 0,
        "max_muertos": res_m[0]["max_muertos"] if res_m else 0,
    }