"""
mongo_dao.py
Responsabilidad: Toda la comunicación con MongoDB Atlas.
Ningún otro módulo toca pymongo directamente.
"""

import os
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv

load_dotenv()


class MongoDAO:
    COLECCION = "accidentes"

    def __init__(self):
        uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB_NAME", "accidentalidad_baq")

        if not uri:
            raise EnvironmentError(
                "No se encontró MONGO_URI. "
                "Crea un archivo .env con la variable MONGO_URI."
            )

        self._cliente = MongoClient(uri, serverSelectionTimeoutMS=10000)
        self._db = self._cliente[db_name]
        self._col = self._db[self.COLECCION]

        self._col.create_index("a_o_accidente")
        self._col.create_index("mes_accidente")
        self._col.create_index("gravedad_accidente")

    # ------------------------------------------------------------------ #
    #  ESCRITURA                                                           #
    # ------------------------------------------------------------------ #

    def upsert_muchos(self, registros: list) -> None:
        operaciones = [
            UpdateOne({"_id": r["_id"]}, {"$set": r}, upsert=True)
            for r in registros
        ]
        try:
            self._col.bulk_write(operaciones, ordered=False)
        except BulkWriteError as e:
            print(f"Advertencia en bulk_write: {e.details.get('nInserted', 0)} insertados.")

    def eliminar_todos(self) -> int:
        """Elimina todos los documentos de la colección. Retorna el conteo eliminado."""
        resultado = self._col.delete_many({})
        return resultado.deleted_count

    def insertar_muchos(self, registros: list) -> None:
        """Inserción directa sin upsert (usar tras eliminar_todos)."""
        if registros:
            try:
                self._col.insert_many(registros, ordered=False)
            except Exception as e:
                print(f"Advertencia en insert_many: {e}")

    # ------------------------------------------------------------------ #
    #  LECTURA GENERAL                                                     #
    # ------------------------------------------------------------------ #

    def contar_total(self) -> int:
        return self._col.count_documents({})

    def obtener_anios_disponibles(self) -> list:
        anios = self._col.distinct("a_o_accidente")
        return sorted([a for a in anios if isinstance(a, int) and a > 2000])

    def obtener_gravedades(self) -> list:
        return sorted([g for g in self._col.distinct("gravedad_accidente") if g])

    def obtener_clases(self) -> list:
        return sorted([c for c in self._col.distinct("clase_accidente") if c])

    def obtener_documentos_paginados(self, pagina: int = 0, por_pagina: int = 50,
                                      anio: str = None, gravedad: str = None) -> list:
        """Retorna documentos crudos de Mongo para la página de MongoDB."""
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

        # Filtros reales en Mongo
        query = {}
        if anio and anio != "Todos":
            try:
                query["a_o_accidente"] = int(anio)
            except ValueError:
                pass
        if gravedad and gravedad != "Todas":
            query["gravedad_accidente"] = gravedad

        cursor = (
            self._col.find(query, campos)
            .sort("fecha_accidente", -1)
            .skip(pagina * por_pagina)
            .limit(por_pagina)
        )
        return list(cursor)

    def contar_con_filtros(self, anio: str = None, gravedad: str = None) -> int:
        """Cuenta documentos aplicando los filtros de la página MongoDB."""
        query = {}
        if anio and anio != "Todos":
            try:
                query["a_o_accidente"] = int(anio)
            except ValueError:
                pass
        if gravedad and gravedad != "Todas":
            query["gravedad_accidente"] = gravedad
        return self._col.count_documents(query)

    def resumen_coleccion(self) -> dict:
        """Estadísticas rápidas para mostrar en la página principal y MongoDB."""
        total = self.contar_total()
        anios = self.obtener_anios_disponibles()

        # Convertir a int en la aggregation para evitar problemas con strings
        pipeline_heridos = [
            {
                "$group": {
                    "_id": None,
                    "total": {
                        "$sum": {
                            "$cond": [
                                {"$isNumber": "$cant_heridos_en_sitio_accidente"},
                                "$cant_heridos_en_sitio_accidente",
                                0
                            ]
                        }
                    }
                }
            }
        ]
        pipeline_muertos = [
            {
                "$group": {
                    "_id": None,
                    "total": {
                        "$sum": {
                            "$cond": [
                                {"$isNumber": "$cant_muertos_en_sitio_accidente"},
                                "$cant_muertos_en_sitio_accidente",
                                0
                            ]
                        }
                    }
                }
            }
        ]
        res_h = list(self._col.aggregate(pipeline_heridos))
        res_m = list(self._col.aggregate(pipeline_muertos))
        return {
            "total_documentos": total,
            "anios_cubiertos": f"{min(anios)} – {max(anios)}" if anios else "N/A",
            "total_heridos": res_h[0]["total"] if res_h else 0,
            "total_muertos": res_m[0]["total"] if res_m else 0,
        }

    # ------------------------------------------------------------------ #
    #  ANALÍTICA PARA GRÁFICOS                                            #
    # ------------------------------------------------------------------ #

    def accidentes_por_anio(self, filtros: dict = None) -> list:
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$a_o_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
            {"$sort": {"_id": 1}},
        ]
        return list(self._col.aggregate(pipeline))

    def accidentes_por_mes(self, filtros: dict = None) -> list:
        orden_meses = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December",
        ]
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$mes_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        ]
        resultados = list(self._col.aggregate(pipeline))
        resultados.sort(key=lambda x: orden_meses.index(x["_id"]) if x["_id"] in orden_meses else 99)
        return resultados

    def accidentes_por_tipo(self, filtros: dict = None) -> list:
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$clase_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
            {"$sort": {"total": -1}},
        ]
        return list(self._col.aggregate(pipeline))

    def accidentes_por_gravedad(self, filtros: dict = None) -> list:
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$gravedad_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
            {"$sort": {"total": -1}},
        ]
        return list(self._col.aggregate(pipeline))

    def accidentes_por_hora(self, filtros: dict = None) -> list:
        """
        Extrae la hora del campo hora_accidente.
        Soporta formatos: '14:30:00', '2:30:00 PM', '02:30 PM', etc.
        Se hace en Python para evitar pipelines frágiles en Mongo.
        """
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$hora_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        ]
        resultados = list(self._col.aggregate(pipeline))

        # Parsear hora en Python
        from collections import defaultdict
        conteo_por_hora = defaultdict(int)

        for r in resultados:
            hora_raw = r.get("_id") or ""
            hora_num = _parsear_hora(hora_raw)
            if hora_num is not None:
                conteo_por_hora[hora_num] += r["total"]

        return [{"_id": h, "total": conteo_por_hora[h]} for h in sorted(conteo_por_hora)]

    def maximos_victimas(self, filtros: dict = None) -> dict:
        pipeline_heridos = self._pipeline_base(filtros) + [
            {"$group": {"_id": None, "max_heridos": {"$max": "$cant_heridos_en_sitio_accidente"}}},
        ]
        pipeline_muertos = self._pipeline_base(filtros) + [
            {"$group": {"_id": None, "max_muertos": {"$max": "$cant_muertos_en_sitio_accidente"}}},
        ]
        res_h = list(self._col.aggregate(pipeline_heridos))
        res_m = list(self._col.aggregate(pipeline_muertos))
        return {
            "max_heridos": res_h[0]["max_heridos"] if res_h else 0,
            "max_muertos": res_m[0]["max_muertos"] if res_m else 0,
        }

    def top_sitios_peligrosos(self, top_n: int = 10, filtros: dict = None) -> list:
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$sitio_exacto_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
            {"$sort": {"total": -1}},
            {"$limit": top_n},
        ]
        return list(self._col.aggregate(pipeline))

    def accidentes_por_dia_semana(self, filtros: dict = None) -> list:
        pipeline = self._pipeline_base(filtros) + [
            {"$group": {"_id": "$dia_accidente", "total": {"$sum": "$cantidad_accidentes"}}},
        ]
        orden = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        resultados = list(self._col.aggregate(pipeline))
        resultados.sort(key=lambda x: orden.index(x["_id"]) if x["_id"] in orden else 99)
        return resultados

    # ------------------------------------------------------------------ #
    #  UTILIDADES INTERNAS                                                 #
    # ------------------------------------------------------------------ #

    def _pipeline_base(self, filtros: dict = None) -> list:
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

    def cerrar(self):
        self._cliente.close()


# ------------------------------------------------------------------ #
#  HELPER EXTERNO                                                      #
# ------------------------------------------------------------------ #

def _parsear_hora(hora_raw: str) -> int | None:
    """
    Convierte strings de hora a entero 0-23.
    Soporta todos estos formatos:
      '01:30:00:am'  → formato de la API (4 partes con : )
      '14:30:00'     → 24h sin am/pm
      '2:30:00 PM'   → 12h con espacio
      '02:30 PM'     → 12h corto con espacio
    """
    if not hora_raw or not isinstance(hora_raw, str):
        return None

    hora_raw = hora_raw.strip()
    upper = hora_raw.upper()

    # Detectar AM/PM (puede estar separado por ':' o por espacio)
    es_pm = upper.endswith("PM")
    es_am = upper.endswith("AM")

    # Quitar el indicador AM/PM (con o sin separador previo)
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