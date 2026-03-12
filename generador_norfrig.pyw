import os
import sys
import subprocess

# --- 1. PRE-INSTALACIÓN AUTOMÁTICA ---
# Si a la compu le falta alguna librería, Python la descarga e instala sola en silencio.
def instalar_dependencias():
    paquetes = {'requests': 'requests', 'fpdf': 'fpdf', 'qrcode': 'qrcode', 'PIL': 'Pillow'}
    for modulo, paquete in paquetes.items():
        try:
            __import__(modulo)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

instalar_dependencias()

import tkinter as tk
from tkinter import messagebox
import requests
from fpdf import FPDF
import qrcode
import json
import threading

# --- 2. RUTAS Y CONFIGURACIÓN ---
dir_base = os.path.dirname(os.path.abspath(__file__))
archivo_creds = os.path.join(dir_base, "config_norfrig.json")
ruta_logo = os.path.join(dir_base, "logo.jpg")
ruta_qr = os.path.join(dir_base, "qr_norfrig.png")

# Creamos la carpeta inteligente en el Escritorio del usuario actual
carpeta_destino = os.path.join(os.path.expanduser("~"), "Desktop", "Planillas Norfrig")
os.makedirs(carpeta_destino, exist_ok=True)

# --- 3. GESTIÓN DE CREDENCIALES ---
def cargar_credenciales():
    if os.path.exists(archivo_creds):
        with open(archivo_creds, 'r') as f:
            return json.load(f)
    return None

def guardar_credenciales(email, api_key):
    with open(archivo_creds, 'w') as f:
        json.dump({"email": email, "api_key": api_key}, f)

# --- 4. LA LÓGICA DEL PDF (El motor) ---
def iniciar_generacion(sku, email, api_key, btn, lbl):
    btn.config(state=tk.DISABLED, text="Generando...")
    lbl.config(text="Conectando con Contabilium...", fg="blue")
    
    def tarea():
        try:
            # Archivo final
            nombre_archivo = f"{sku}.pdf"
            ruta_pdf = os.path.join(carpeta_destino, nombre_archivo)
            
            # Detector de duplicados
            if os.path.exists(ruta_pdf):
                respuesta = messagebox.askyesno("Archivo Existente", f"La planilla {sku} ya existe en el escritorio.\n¿Querés sobreescribirla?")
                if not respuesta:
                    lbl.config(text="Operación cancelada.", fg="orange")
                    return

            # Autenticación
            url_auth = "https://rest.contabilium.com/token"
            datos = {"grant_type": "client_credentials", "client_id": email, "client_secret": api_key}
            res_auth = requests.post(url_auth, data=datos)
            
            if res_auth.status_code != 200:
                lbl.config(text="Error de conexión.", fg="red")
                messagebox.showerror("Error", "Credenciales inválidas. Borrá el archivo config_norfrig.json y volvé a intentar.")
                return
                
            token = res_auth.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Buscando el combo
            lbl.config(text=f"Buscando {sku}...")
            res_combo = requests.get(f"https://rest.contabilium.com/api/conceptos/getbycodigo?codigo={sku}", headers=headers)
            
            if res_combo.status_code != 200:
                lbl.config(text="SKU no encontrado.", fg="red")
                messagebox.showerror("Error", f"No se encontró el combo '{sku}'.")
                return
                
            datos_combo = res_combo.json()
            nombre_combo = datos_combo["Nombre"]
            items_hijos = datos_combo.get("Items", [])
            
            if not items_hijos:
                lbl.config(text="Combo vacío.", fg="red")
                messagebox.showwarning("Atención", "El combo existe pero no tiene artículos.")
                return
            
            lbl.config(text="Descargando artículos...")
            lista_impresion = []
            total_piezas = 0
            
            for item in items_hijos:
                cod_hijo = item["Codigo"]
                cant_hijo = int(item["Cantidad"])
                total_piezas += cant_hijo
                
                res_hijo = requests.get(f"https://rest.contabilium.com/api/conceptos/getbycodigo?codigo={cod_hijo}", headers=headers)
                nombre_hijo = res_hijo.json()["Nombre"] if res_hijo.status_code == 200 else "Nombre no encontrado"
                lista_impresion.append({"sku": cod_hijo, "nombre": nombre_hijo, "cantidad": cant_hijo})
                
            # Generar QR fijo si no existe
            if not os.path.exists(ruta_qr):
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data('https://www.norfrig.com.ar')
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                img_qr.save(ruta_qr)
                
            lbl.config(text="Armando PDF...")
            
            class PDFNorfrig(FPDF):
                def header(self):
                    if self.page_no() == 1:
                        if os.path.exists(ruta_logo):
                            self.image(ruta_logo, 140, 10, 60)
                        self.set_y(35)
                        self.set_font('Arial', 'B', 14)
                        self.cell(0, 8, "¡Hola!", ln=True)
                        self.set_font('Arial', '', 12)
                        self.multi_cell(0, 6, "Queremos darte la tranquilidad de que tu pedido fue armado y revisado ítem por ítem antes de ser embalado. Si necesitás ayuda o tuviste algún inconveniente con el producto que recibiste, ponete en contacto con nosotros para que te ayudemos a resolverlo. ¡Muchas gracias por tu compra!")
                        self.ln(12)
                    else:
                        self.ln(15)
                    
                def footer(self):
                    if hasattr(self, 'items_impresos') and hasattr(self, 'total_items'):
                        if self.items_impresos < self.total_items:
                            self.set_y(-57) 
                            self.set_font('Arial', 'BI', 10) 
                            self.cell(0, 5, "Continúa en la siguiente página --->", align='R')
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
                    if os.path.exists(ruta_qr):
                        self.image(ruta_qr, x=172, y=y_actual, w=28)
                    self.set_xy(105, y_actual + 29)
                    self.set_font('Arial', 'B', 11)
                    self.cell(95, 6, "www.norfrig.com.ar", ln=1, align='R')

            pdf = PDFNorfrig()
            pdf.items_impresos = 0
            pdf.total_items = len(lista_impresion)
            pdf.set_auto_page_break(auto=True, margin=55) 
            pdf.add_page()
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(30, 12, "SKU", border=1, align='C')
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(60, 12, sku, border=1, align='C')
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(70, 12, "CANTIDAD DE PIEZAS:", border=1, align='R')
            pdf.set_font('Arial', '', 16)
            pdf.cell(30, 12, str(total_piezas), border=1, align='C')
            pdf.ln(12)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.multi_cell(190, 8, nombre_combo, border=1, align='C')
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(40, 8, "SKU", border=1, align='C', fill=True)
            pdf.cell(20, 8, "CANT.", border=1, align='C', fill=True)
            pdf.cell(110, 8, "ITEM / DESCRIPCION", border=1, align='C', fill=True)
            pdf.cell(20, 8, "LISTO", border=1, align='C', fill=True)
            pdf.ln(8)
            
            pdf.set_font('Arial', '', 10) 
            
            for item in lista_impresion:
                sku_seguro = item['sku'][:18] + '...' if len(item['sku']) > 18 else item['sku']
                nombre_seguro = item['nombre'][:50] + '...' if len(item['nombre']) > 50 else item['nombre']
                pdf.cell(40, 10, sku_seguro, border=1, align='C')
                pdf.cell(20, 10, f"{item['cantidad']}x", border=1, align='C')
                pdf.cell(110, 10, nombre_seguro, border=1, align='L')
                pdf.cell(20, 10, "", border=1, align='C')
                pdf.ln(10)
                pdf.items_impresos += 1
                
            pdf.output(ruta_pdf)
                
            lbl.config(text=f"¡{nombre_archivo} guardado en el Escritorio!", fg="green")
            
            # Abrir el PDF automáticamente (funciona en Windows)
            os.startfile(ruta_pdf)
            
        except Exception as e:
            lbl.config(text="Error inesperado.", fg="red")
            messagebox.showerror("Error", f"Detalle:\n{str(e)}")
            
        finally:
            btn.config(state=tk.NORMAL, text="GENERAR PLANILLA")

    threading.Thread(target=tarea).start()

# --- 5. INTERFACES GRÁFICAS ---

def abrir_app_principal(email, api_key):
    ventana_principal = tk.Tk()
    ventana_principal.title("Norfrig - Generador de Planillas")
    ventana_principal.geometry("450x250")
    ventana_principal.resizable(False, False)
    
    tk.Label(ventana_principal, text="Generador de Planillas", font=("Arial", 16, "bold")).pack(pady=(20, 10))
    tk.Label(ventana_principal, text="SKU del combo (Ej: COM0001):", font=("Arial", 10)).pack()
    
    entrada_sku = tk.Entry(ventana_principal, font=("Arial", 14), justify="center", width=15)
    entrada_sku.pack(pady=10)
    
    lbl_estado = tk.Label(ventana_principal, text="Listo.", font=("Arial", 9), fg="gray")
    
    def procesar(event=None):
        sku = entrada_sku.get().strip().upper()
        if sku:
            entrada_sku.delete(0, tk.END)
            iniciar_generacion(sku, email, api_key, btn_generar, lbl_estado)
        else:
            messagebox.showwarning("Atención", "Ingresá un SKU.")

    btn_generar = tk.Button(ventana_principal, text="GENERAR PLANILLA", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", cursor="hand2", command=procesar)
    btn_generar.pack(pady=5, fill=tk.X, padx=40)
    
    lbl_estado.pack(side=tk.BOTTOM, pady=10)
    ventana_principal.bind('<Return>', procesar)
    ventana_principal.mainloop()

def abrir_login():
    ventana_login = tk.Tk()
    ventana_login.title("Bienvenido a Norfrig")
    ventana_login.geometry("350x250")
    ventana_login.resizable(False, False)
    
    tk.Label(ventana_login, text="Configuración Inicial", font=("Arial", 14, "bold")).pack(pady=15)
    
    tk.Label(ventana_login, text="Email de Contabilium:").pack()
    entrada_email = tk.Entry(ventana_login, width=35)
    entrada_email.pack(pady=5)
    
    tk.Label(ventana_login, text="API Key:").pack()
    entrada_api = tk.Entry(ventana_login, width=35, show="*") # Oculta la API key con asteriscos
    entrada_api.pack(pady=5)
    
    def guardar_y_continuar():
        email = entrada_email.get().strip()
        api_key = entrada_api.get().strip()
        
        if email and api_key:
            guardar_credenciales(email, api_key)
            ventana_login.destroy()
            abrir_app_principal(email, api_key)
        else:
            messagebox.showwarning("Error", "Completá ambos campos.")
            
    tk.Button(ventana_login, text="Guardar y Entrar", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=guardar_y_continuar).pack(pady=20)
    ventana_login.mainloop()

# --- 6. ARRANQUE DEL PROGRAMA ---
credenciales = cargar_credenciales()

if credenciales:
    # Si ya existe el archivo JSON, entra directo
    abrir_app_principal(credenciales['email'], credenciales['api_key'])
else:
    # Si es la primera vez, pide los datos
    abrir_login()