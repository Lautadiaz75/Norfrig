import pandas as pd
import os

# --- 1. CONFIGURACIÓN ---
archivo_excel = "Preguntas.xlsx"

if not os.path.exists(archivo_excel):
    print(f"⚠️ ¡ATENCIÓN! No encuentro el archivo: {archivo_excel}")
    exit()

print("1. Leyendo y limpiando los datos de las preguntas...")
df = pd.read_excel(archivo_excel)
df.columns = df.columns.str.strip().str.lower()

col_nro = [col for col in df.columns if 'nro' in col or 'numero' in col][0]
col_titulo = [col for col in df.columns if 'titulo' in col or 'título' in col][0]
col_pregunta = [col for col in df.columns if 'texto de la pregunta' in col or 'pregunta' in col][0]
col_compra = [col for col in df.columns if 'compra' in col or 'venta' in col][0]

df['venta_generada'] = df[col_compra].astype(str).str.lower().apply(lambda x: 1 if 'si' in x or 'sí' in x else 0)

print("2. Calculando Métricas Generales...")
metricas = df.groupby([col_nro, col_titulo]).agg(
    total_preguntas=(col_nro, 'count'),
    total_ventas=('venta_generada', 'sum')
).reset_index()

metricas['conversion_%'] = round((metricas['total_ventas'] / metricas['total_preguntas']) * 100, 2)

print("3. Analizando la INTENCIÓN de las preguntas...")

# --- DICCIONARIOS DE CATEGORÍAS ---
cat_compatibilidad = ['sirve', 'modelo', 'compatible', 'andará', 'va', 'le va', 'reemplazo']
cat_envios_pagos = ['envio', 'envío', 'gratis', 'costo', 'llega', 'cuánto', 'cuanto', 'precio', 'pagar', 'mandan']
cat_stock_retiro = ['tenes', 'tenés', 'tienen', 'stock', 'retirar', 'local', 'factura', 'compra', 'compro']
cat_tecnicas = ['medida', 'medidas', 'largo', 'ancho', 'peso', 'hp', 'watts', 'voltaje', 'trae', 'viene']

def clasificar_pregunta(texto):
    if pd.isna(texto): return "Otro"
    texto = str(texto).lower()
    
    puntos = {
        "Compatibilidad": sum(1 for p in cat_compatibilidad if p in texto),
        "Envíos/Pagos": sum(1 for p in cat_envios_pagos if p in texto),
        "Stock/Ventas": sum(1 for p in cat_stock_retiro if p in texto),
        "Dudas Técnicas": sum(1 for p in cat_tecnicas if p in texto)
    }
    
    if all(v == 0 for v in puntos.values()):
        return "Otro"
    
    return max(puntos, key=puntos.get)

df['categoria_pregunta'] = df[col_pregunta].apply(clasificar_pregunta)

# --- NUEVO: GUARDAR LAS PREGUNTAS "OTRO" AGRUPADAS EN UN TXT ---
print("Generando registro de preguntas no clasificadas...")
preguntas_otro = df[df['categoria_pregunta'] == 'Otro']

# Agrupamos las preguntas no clasificadas por publicación
preguntas_agrupadas = preguntas_otro.groupby([col_nro, col_titulo])

with open("Preguntas_no_clasificadas.txt", "w", encoding="utf-8") as f:
    f.write("--- PREGUNTAS SIN CLASIFICAR (CATEGORÍA 'OTRO') ---\n")
    f.write("Buscá patrones acá para agregar a los diccionarios del código.\n")
    f.write("============================================================\n\n")
    
    # Iteramos por cada grupo (cada publicación)
    for (nro, titulo), grupo in preguntas_agrupadas:
        f.write(f"🛒 PUB: {nro} | {titulo}\n")
        f.write(f"Total sin clasificar: {len(grupo)}\n")
        f.write("-" * 60 + "\n")
        
        # Escribimos todas las preguntas de esa publicación como una lista
        for pregunta in grupo[col_pregunta]:
            f.write(f" 🔸 {pregunta}\n")
            
        f.write("\n============================================================\n\n")

# --- 4. AGRUPACIÓN Y PORCENTAJES ---
clasificacion = df.groupby([col_nro, 'categoria_pregunta']).size().unstack(fill_value=0).reset_index()

columnas_cats = [col for col in clasificacion.columns if col != col_nro]
clasificacion['total_cats'] = clasificacion[columnas_cats].sum(axis=1)

for col in columnas_cats:
    clasificacion[f'% {col}'] = round((clasificacion[col] / clasificacion['total_cats']) * 100, 1)

columnas_porcentajes = [col_nro] + [col for col in clasificacion.columns if '%' in col]
clasificacion_final = clasificacion[columnas_porcentajes]

# --- 5. UNIMOS TODO Y EXPORTAMOS ---
reporte_final = pd.merge(metricas, clasificacion_final, on=col_nro)
reporte_final = reporte_final.sort_values(by='total_preguntas', ascending=False)

print("4. Exportando el reporte final a Excel...")
nombre_reporte = "Auditoria_Intencion_Norfrig.xlsx"

with pd.ExcelWriter(nombre_reporte, engine='openpyxl') as writer:
    reporte_final.to_excel(writer, sheet_name='Análisis de Intención', index=False)
    
    pub_compatibilidad = reporte_final[reporte_final.get('% Compatibilidad', 0) > 50]
    pub_compatibilidad.to_excel(writer, sheet_name='Faltan Modelos Compatibles', index=False)

print(f"\n🎉 ¡LISTO! Tenés tu Excel '{nombre_reporte}' y tu bloc de notas 'Preguntas_no_clasificadas.txt'.")