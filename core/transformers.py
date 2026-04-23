"""
core/transformers.py

Responsabilidad: convertir resultados de MongoDB en DataFrames
listos para graficar. No toca la BD ni Streamlit directamente.
"""

import pandas as pd

MESES_ES = {
    "January": "Enero",   "February": "Febrero", "March": "Marzo",
    "April": "Abril",     "May": "Mayo",          "June": "Junio",
    "July": "Julio",      "August": "Agosto",     "September": "Septiembre",
    "October": "Octubre", "November": "Noviembre","December": "Diciembre",
}

DIAS_ES = {
    "Mon": "Lunes", "Tue": "Martes",   "Wed": "Miércoles",
    "Thu": "Jueves","Fri": "Viernes",  "Sat": "Sábado", "Sun": "Domingo",
}


def a_dataframe(
    lista: list,
    col_id: str = "_id",
    col_valor: str = "total",
) -> pd.DataFrame:
    if not lista:
        return pd.DataFrame(columns=[col_id, col_valor])
    df = pd.DataFrame(lista)
    df.rename(columns={"_id": col_id}, inplace=True)
    return df


def preparar_por_mes(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Mes")
    df["Mes"] = df["Mes"].map(MESES_ES).fillna(df["Mes"])
    return df


def preparar_por_anio(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Año")
    df = df[df["Año"] > 2000]
    df["Año"] = df["Año"].astype(str)
    return df


def preparar_por_tipo(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Tipo")
    return df[df["Tipo"].notna() & (df["Tipo"] != "")]


def preparar_por_gravedad(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Gravedad")
    return df[df["Gravedad"].notna() & (df["Gravedad"] != "")]


def preparar_por_hora(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Hora")
    df = df.dropna(subset=["Hora"])
    todas_horas = pd.DataFrame({"Hora": list(range(24))})
    df = todas_horas.merge(df, on="Hora", how="left").fillna(0)
    df["total"] = df["total"].astype(int)
    df["Etiqueta"] = df["Hora"].apply(lambda h: f"{int(h):02d}:00")
    return df


def preparar_por_dia(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Día")
    df["Día"] = df["Día"].map(DIAS_ES).fillna(df["Día"])
    return df


def preparar_top_sitios(data: list) -> pd.DataFrame:
    df = a_dataframe(data, col_id="Sitio")
    df = df[df["Sitio"].notna() & (df["Sitio"] != "")]
    return df.head(10)