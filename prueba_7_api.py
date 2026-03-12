import requests
from fpdf import FPDF
import qrcode
import os

# --- 1. CONFIGURACIÓN ---
email_usuario = "REPLAVARROPASYHELADERAS@GMAIL.COM"
api_key_usuario = "8c184cebea624ceba0746246eb653db4" 

# RUTA DEL LOGO
ruta_logo = "logo.jpg" 

if not os.path.exists(ruta_logo):
    print(f"⚠️ ¡ATENCIÓN! Sigo sin encontrar el logo en:\n{ruta_logo}")

# Generar el QR temporal
qr = qrcode.QRCode(box_size=10, border=1)
qr.add_data('https://www.norfrig.com.ar')
qr.make(fit=True)
img_qr = qr.make_image(fill_color="black", back_color="white")
img_qr.save("qr_temporal.png")

url_autenticacion = "https://rest.contabilium.com/token"
datos_ingreso = {
    "grant_type": "client_credentials",
    "client_id": email_usuario,
    "client_secret": api_key_usuario
}

print("\n--- GENERADOR DE PLANILLAS DE ARMADO ---")
sku_ingresado = input("Ingresá el SKU del combo (ej. COM0001): ").strip().upper()

print("\n1. Conectando con el sistema...")
respuesta_auth = requests.post(url_autenticacion, data=datos_ingreso)

if respuesta_auth.status_code == 200:
    mi_token = respuesta_auth.json()["access_token"]
    headers_seguros = {"Authorization": f"Bearer {mi_token}"}
    
    sku_combo = sku_ingresado
    print(f"2. Buscando el combo: {sku_combo}")
    url_combo = f"https://rest.contabilium.com/api/conceptos/getbycodigo?codigo={sku_combo}"
    
    respuesta_combo = requests.get(url_combo, headers=headers_seguros)
    
    if respuesta_combo.status_code == 200:
        datos_combo = respuesta_combo.json()
        nombre_combo = datos_combo["Nombre"]
        items_hijos = datos_combo["Items"]
        
        print("\n3. Extrayendo componentes...")
        lista_final_impresion = []
        total_piezas = 0
        
        for item in items_hijos:
            codigo_hijo = item["Codigo"]
            cantidad_hijo = int(item["Cantidad"])
            total_piezas += cantidad_hijo
            
            url_hijo = f"https://rest.contabilium.com/api/conceptos/getbycodigo?codigo={codigo_hijo}"
            respuesta_hijo = requests.get(url_hijo, headers=headers_seguros)
            
            if respuesta_hijo.status_code == 200:
                nombre_hijo = respuesta_hijo.json()["Nombre"]
            else:
                nombre_hijo = "Nombre no encontrado"
            
            lista_final_impresion.append({
                "sku": codigo_hijo, 
                "nombre": nombre_hijo,
                "cantidad": cantidad_hijo
            })
            print(f"[ ] {cantidad_hijo}x | SKU: {codigo_hijo}")
            
        print("\n4. Diseñando el PDF...")
        
        class PDFNorfrig(FPDF):
            def header(self):
                if self.page_no() == 1:
                    if os.path.exists(ruta_logo):
                        self.image(ruta_logo, 140, 10, 60)
                    
                    self.set_y(35)
                    self.set_font('Arial', 'B', 14)
                    self.cell(0, 8, "¡Hola!", ln=True)
                    self.set_font('Arial', '', 12)
                    texto = "Queremos darte la tranquilidad de que tu pedido fue armado y revisado ítem por ítem antes de ser embalado. Si necesitás ayuda o tuviste algún inconveniente con el producto que recibiste, ponete en contacto con nosotros para que te ayudemos a resolverlo. ¡Muchas gracias por tu compra!"
                    self.multi_cell(0, 6, texto)
                    self.ln(12)
                else:
                    self.ln(15)
                
            def footer(self):
                # ¡LA MAGIA DE LA FLECHA!
                # Verificamos si faltan ítems por imprimir antes de cerrar la página
                if hasattr(self, 'items_impresos') and hasattr(self, 'total_items'):
                    if self.items_impresos < self.total_items:
                        self.set_y(-57) # Lo ponemos un poquito por encima del footer normal
                        self.set_font('Arial', 'BI', 10) # Negrita y cursiva
                        self.cell(0, 5, "Continúa en la siguiente página --->", align='R')

                # Empieza el Footer normal
                self.set_y(-50) 
                
                self.set_font('Arial', 'B', 14)
                self.cell(95, 7, "¡CONTACTANOS!", ln=0)
                self.cell(95, 7, "¡SEGUINOS!", ln=1, align='R')
                
                y_actual = self.get_y()
                
                self.set_font('Arial', 'B', 11)
                self.cell(95, 6, "info@norfrig.com.ar", ln=1)
                self.set_font('Arial', '', 11)
                self.cell(95, 6, "Humboldt 2359, CABA", ln=1)
                self.cell(95, 6, "(011) 15-4024-4542", ln=1)
                self.cell(95, 6, "(011) 4774-5315 / (011) 4827-2871", ln=1)
                
                self.image('qr_temporal.png', x=172, y=y_actual, w=28)
                
                self.set_xy(105, y_actual + 29)
                self.set_font('Arial', 'B', 11)
                self.cell(95, 6, "www.norfrig.com.ar", ln=1, align='R')

        # --- CREACIÓN DEL DOCUMENTO ---
        pdf = PDFNorfrig()
        
        # Inicializamos los contadores para la lógica de la flecha
        pdf.items_impresos = 0
        pdf.total_items = len(lista_final_impresion)
        
        pdf.set_auto_page_break(auto=True, margin=55) 
        
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(30, 12, "SKU", border=1, align='C')
        pdf.set_font('Arial', 'B', 16)
        
        nombre_combo_seguro = nombre_combo[:65] + '...' if len(nombre_combo) > 65 else nombre_combo
        
        pdf.cell(60, 12, sku_combo, border=1, align='C')
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(70, 12, "CANTIDAD DE PIEZAS:", border=1, align='R')
        pdf.set_font('Arial', '', 16)
        pdf.cell(30, 12, str(total_piezas), border=1, align='C')
        pdf.ln(12)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(190, 10, nombre_combo_seguro, border=1, align='C')
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(40, 8, "SKU", border=1, align='C', fill=True)
        pdf.cell(20, 8, "CANT.", border=1, align='C', fill=True)
        pdf.cell(110, 8, "ITEM / DESCRIPCION", border=1, align='C', fill=True)
        pdf.cell(20, 8, "LISTO", border=1, align='C', fill=True)
        pdf.ln(8)
        
        pdf.set_font('Arial', '', 10) 
        
        for item in lista_final_impresion:
            sku_seguro = item['sku'][:18] + '...' if len(item['sku']) > 18 else item['sku']
            nombre_seguro = item['nombre'][:50] + '...' if len(item['nombre']) > 50 else item['nombre']
            
            pdf.cell(40, 10, sku_seguro, border=1, align='C')
            pdf.cell(20, 10, f"{item['cantidad']}x", border=1, align='C')
            pdf.cell(110, 10, nombre_seguro, border=1, align='L')
            pdf.cell(20, 10, "", border=1, align='C')
            pdf.ln(10)
            
            # Sumamos 1 al contador cada vez que se imprime una fila con éxito
            pdf.items_impresos += 1
            
        nombre_archivo = f"{sku_combo}.pdf"
        pdf.output(nombre_archivo)
        
        if os.path.exists("qr_temporal.png"):
            os.remove("qr_temporal.png")
            
        print(f"\n✅ ¡Éxito total! Tu planilla lista para imprimir se guardó como: {nombre_archivo}")

    else:
        print(f"❌ Error al buscar el combo '{sku_combo}'. Revisa si está bien escrito.")
else:
    print("❌ Error en la autenticación con Contabilium.")