import pandas as pd

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO = "Plantilla billowshop proyecto.xlsx" 
HOJA_DATOS = "plantilla"      
COL_DESC_ORIGEN = "descripcion" 
COL_DESC_DESTINO = "descripcion_html"

# Palabras que fuerzan negrita (YA NO ESTÁ "MEDIDAS")
PALABRAS_CLAVE_TITULOS = [
    "CARACTERISTICAS", "CARACTERÍSTICAS", "MODELOS", 
    "ESPECIFICACIONES", "COMPATIBILIDAD", "IMPORTANTE", 
    "INCLUYE"
]

def aplicar_negritas(texto):
    if not isinstance(texto, str):
        return ""
    
    lineas = texto.split('\n')
    lineas_formateadas = []
    
    # Variable para saber si ya pasamos la primera línea
    es_primera_linea_con_texto = True
    
    for linea in lineas:
        linea_limpia = linea.strip()
        
        # Si la línea está vacía, pasa derecho
        if not linea_limpia:
            lineas_formateadas.append(linea)
            continue
        
        usar_negrita = False
        
        # --- REGLA 1: SIEMPRE NEGRITA A LA PRIMERA LÍNEA (EL TÍTULO) ---
        if es_primera_linea_con_texto:
            usar_negrita = True
            es_primera_linea_con_texto = False # Ya gastamos la bala de la primera línea
        
        # --- REGLA 2: LÓGICA PARA EL RESTO DEL TEXTO ---
        else:
            # A) Si es una palabra clave exacta (Ej: CARACTERISTICAS)
            if any(palabra in linea_limpia.upper() for palabra in PALABRAS_CLAVE_TITULOS):
                 if len(linea_limpia) < 50: # Evitar frases largas
                    usar_negrita = True

            # B) Si es un título en mayúsculas (Ej: MODELOS COMPATIBLES)
            elif linea_limpia.isupper() and len(linea_limpia) < 50:
                usar_negrita = True

            # --- VETOS (PROHIBICIONES) ---
            # Aquí aplicamos tus reglas de exclusión para que NO se ponga negrita
            
            # 1. Si tiene viñeta (•)
            if "•" in linea_limpia:
                usar_negrita = False
            
            # 2. Si tiene guion (-) 
            # (Nota: Como ya no estamos en la primera línea, aquí el guion anula la negrita)
            if "-" in linea_limpia:
                usar_negrita = False
                
            # 3. Si habla de MEDIDAS
            if "MEDIDAS" in linea_limpia.upper():
                usar_negrita = False

        # --- APLICAR EL HTML ---
        if usar_negrita:
            lineas_formateadas.append(f"<b>{linea_limpia}</b>")
        else:
            lineas_formateadas.append(linea_limpia)
            
    return "\n".join(lineas_formateadas)

def procesar_html():
    print("--- INICIANDO MAQUILLADOR V2 (CON RESTRICCIONES) ---")
    try:
        df = pd.read_excel(NOMBRE_ARCHIVO, sheet_name=HOJA_DATOS)
    except Exception as e:
        print(f"Error cargando archivo: {e}")
        return

    print("Procesando textos...")
    df[COL_DESC_DESTINO] = df[COL_DESC_ORIGEN].apply(aplicar_negritas)
    
    nombre_salida = "LISTO_CON_HTML_V2.xlsx"
    df.to_excel(nombre_salida, index=False)
    
    print(f"¡Listo! Archivo guardado: {nombre_salida}")
    print(f"Revisa la columna: {COL_DESC_DESTINO}")

if __name__ == "__main__":
    procesar_html()