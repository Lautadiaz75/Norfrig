import pandas as pd

# ASEGURATE DE QUE ESTE NOMBRE SEA EL CORRECTO
ARCHIVO = "Plantilla billowshop proyecto.xlsx" 
HOJA = "plantilla"

try:
    df = pd.read_excel(ARCHIVO, sheet_name=HOJA)
    print("--- NOMBRES EXACTOS DE TUS COLUMNAS ---")
    print(list(df.columns))
    print("---------------------------------------")
except Exception as e:
    print(e)