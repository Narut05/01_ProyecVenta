import os
from glob import glob
import numpy as np
import pandas as pd

def extrac_transform_data ():
    # ==============================================================================
    # 1. CONFIGURACIÓN DE RUTAS Y BÚSQUEDA DE ARCHIVOS
    # ==============================================================================
    carpeta_fact = "fact"
    patron_archivos = os.path.join(carpeta_fact, "Vta*.xlsx")
    archivos_excel = glob(patron_archivos)

    # ==============================================================================
    # 2. INGESTA Y CONSOLIDACIÓN DE DATOS
    # ==============================================================================
    df_venta = pd.concat(
        [pd.read_excel(archivo) for archivo in archivos_excel], ignore_index=True
    )
    dim_calendar = pd.read_excel(r"dim\dim_calendar_final.xlsx")

    # Identificar columnas de calendario (excluyendo la clave de cruce)
    cols = dim_calendar.columns.drop("Fecha")

    # ==============================================================================
    # 3. AGREGACIÓN TEMPORAL Y CREACIÓN DE LLAVES
    # ==============================================================================
    df_venta_01 = (
        df_venta.groupby(["DivArea", "Codigo Local", "Fecha"])
        .agg(Venta=("_VtaNeta", "sum"))
        .reset_index()
    )

    df_venta_01["llave"] = (
        df_venta_01["Codigo Local"] + "-" + df_venta_01["DivArea"]
    )

    # ==============================================================================
    # 4. ENRIQUECIMIENTO DE LA SERIE (MERGE & DATA QUALITY)
    # ==============================================================================
    df_venta_02 = df_venta_01.merge(dim_calendar, on="Fecha", how="left")
    df_venta_03 = df_venta_02.fillna(0)

    # Optimización de tipos de datos para las banderas del calendario
    df_venta_03[cols] = df_venta_03[cols].astype(int)

    # ==============================================================================
    # 5. FORMATEO DE COLUMNAS PARA MODELADO DE SERIES DE TIEMPO
    # ==============================================================================
    columnas_a_renombrar = {
        "Fecha": "ds",
        "Venta": "y",
    }
    df_venta_03.rename(columns=columnas_a_renombrar, inplace=True)

    # ==============================================================================
    # 6. ALMACENAMIENTO
    # ==============================================================================
    df_venta_03.to_parquet("files/fact_ventas_predict.parquet")