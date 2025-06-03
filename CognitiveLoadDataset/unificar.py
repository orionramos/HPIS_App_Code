import os
import pandas as pd

# Ruta a la carpeta que contiene los archivos CSV
carpeta_csv = 'C:\HPIS_App_Code\CognitiveLoadDataset'  # <-- CAMBIA esto

# Lista para almacenar los DataFrames
dataframes = []

# Recorremos todos los archivos de la carpeta
for archivo in os.listdir(carpeta_csv):
    if archivo.endswith('.csv'):
        ruta_archivo = os.path.join(carpeta_csv, archivo)
        df = pd.read_csv(ruta_archivo)
        dataframes.append(df)

# Concatenamos todos los DataFrames
df_unificado = pd.concat(dataframes, ignore_index=True)

# Guardamos en un nuevo archivo CSV
df_unificado.to_csv('dataset_unificado.csv', index=False)

print("✅ Archivos unificados correctamente en 'dataset_unificado.csv'")
