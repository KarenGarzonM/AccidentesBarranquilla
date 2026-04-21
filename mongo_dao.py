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

    def obtener_documentos_paginados(self, pagina: int = 0, por_pagina: int = 50) -> list:
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
        cursor = (
            self._col.find({}, campos)
            .sort("fecha_accidente", -1)
            .skip(pagina * por_pagina)
            .limit(por_pagina)
        )
        return list(cursor)

    def resumen_coleccion(self) -> dict:
        """Estadísticas rápidas para mostrar en la página de MongoDB."""
        total = self.contar_total()
        anios = self.obtener_anios_disponibles()
        pipeline_heridos = [
            {"$group": {"_id": None, "total": {"$sum": "$cant_heridos_en_sitio_accidente"}}}
        ]
        pipeline_muertos = [
            {"$group": {"_id": None, "total": {"$sum": "$cant_muertos_en_sitio_accidente"}}}
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
        pipeline = self._pipeline_base(filtros) + [
            {
                "$addFields": {
                    "hora_num": {
                        "$let": {
                            "vars": {"partes": {"$split": ["$hora_accidente", ":"]}},
                            "in": {
                                "$cond": {
                                    "if": {"$eq": [{"$toLower": {"$arrayElemAt": ["$$partes", 3]}}, "pm"]},
                                    "then": {
                                        "$cond": {
                                            "if": {"$eq": [{"$toInt": {"$arrayElemAt": ["$$partes", 0]}}, 12]},
                                            "then": 12,
                                            "else": {"$add": [{"$toInt": {"$arrayElemAt": ["$$partes", 0]}}, 12]},
                                        }
                                    },
                                    "else": {
                                        "$cond": {
                                            "if": {"$eq": [{"$toInt": {"$arrayElemAt": ["$$partes", 0]}}, 12]},
                                            "then": 0,
                                            "else": {"$toInt": {"$arrayElemAt": ["$$partes", 0]}},
                                        }
                                    },
                                }
                            },
                        }
                    }
                }
            },
            {"$group": {"_id": "$hora_num", "total": {"$sum": "$cantidad_accidentes"}}},
            {"$sort": {"_id": 1}},
        ]
        return list(self._col.aggregate(pipeline))

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
