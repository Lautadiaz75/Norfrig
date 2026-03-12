import pandas as pd
import re

# --- CONFIGURACIÓN ---
NOMBRE_ARCHIVO = "Plantilla billowshop proyecto.xlsx"

HOJA_DATOS = "plantilla"       # <--- AQUÍ PONES EL NOMBRE EXACTO DE LA PESTAÑA
HOJA_REF = "REFERENCIAS" 

# NOMBRES CORREGIDOS
COL_TITULO = "titulo"
COL_DESC = "descripcion"
COL_DESTINO = "marca_nueva"

def detective_seguro():
    print("--- INICIANDO ESCRIBANO PRECAVIDO ---")
    
    # 1. Cargar Archivos
    try:
        df = pd.read_excel(NOMBRE_ARCHIVO, sheet_name=HOJA_DATOS)
        df_ref = pd.read_excel(NOMBRE_ARCHIVO, sheet_name=HOJA_REF)
        
        # Limpiamos la lista de referencias (quitamos vacíos y espacios)
        marcas_validas = [str(x).strip() for x in df_ref.iloc[:, 0].dropna() if str(x).strip() != ""]
        print(f"Cargadas {len(marcas_validas)} marcas válidas desde REFERENCIAS.")
        
    except Exception as e:
        print(f"Error cargando el archivo: {e}")
        return

    resultados = []
    
    # Recorremos fila por fila
    for index, row in df.iterrows():
        titulo = str(row[COL_TITULO]).strip()
        desc = str(row[COL_DESC]).strip()
        
        marca_titulo = None
        marca_desc = None
        
        # --- ANÁLISIS 1: DESCRIPCIÓN (Busca "Marca: X") ---
        # Busca: palabra "Marca", opcionalmente dos puntos, espacios y la palabra siguiente.
        match = re.search(r'Marca:?\s*([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+)', desc, re.IGNORECASE)
        if match:
            posible_marca = match.group(1)
            # VERIFICACIÓN: ¿Está en nuestra lista aprobada?
            for m in marcas_validas:
                if m.lower() == posible_marca.lower():
                    marca_desc = m # Guardamos la marca con la mayúscula correcta de la lista
                    break
        
        # --- ANÁLISIS 2: TÍTULO (Solo si dice "ORIGINAL") ---
        if "original" in titulo.lower():
            # Buscamos cuál de las marcas válidas aparece en el título
            for m in marcas_validas:
                # Usamos \b para buscar la palabra exacta (que "Drean" no active "DreanNext")
                if re.search(r'\b' + re.escape(m) + r'\b', titulo, re.IGNORECASE):
                    marca_titulo = m
                    break
        
        # --- DECISIÓN FINAL (SEGURIDAD) ---
        marca_final = ""
        
        if marca_desc and marca_titulo:
            # Si encontró en los dos lados
            if marca_desc.lower() == marca_titulo.lower():
                marca_final = marca_desc # Coinciden perfectas
            else:
                marca_final = "" # CONFLICTO: Dice Drean en un lado y Whirlpool en otro -> Vacío
        
        elif marca_desc:
            marca_final = marca_desc # Ganó la descripción (muy confiable)
            
        elif marca_titulo:
            marca_final = marca_titulo # Ganó el título (porque decía Original)
            
        # Si no encontró nada, queda vacío ("")
        resultados.append(marca_final)

    # 3. Guardar
    df[COL_DESTINO] = resultados
    
    nombre_salida = "LISTO_CON_MARCAS.xlsx"
    df.to_excel(nombre_salida, index=False)
    print(f"¡Listo! Se generó '{nombre_salida}'.")
    print("Revisa la columna K. Las celdas vacías son para revisión manual.")

if __name__ == "__main__":
    detective_seguro()