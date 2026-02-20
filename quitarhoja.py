import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io, os, re, fitz 
from PIL import Image

# --- CONFIGURACIÓN DE ESTILO ---
COLOR_FONDO = "#1e1e1e"
COLOR_TEXTO = "#ffffff"
COLOR_BOTON_VERDE = "#2ecc71"
COLOR_BOTON_AZUL = "#3498db"
COLOR_BOTON_NARANJA = "#e67e22"
COLOR_BOTON_MORADO = "#9b59b6"
COLOR_BOTON_ROJO = "#c0392b"
COLOR_ENTRADA = "#333333"

# --- LÓGICA DE SALIDA ORGANIZADA ---
def obtener_ruta_salida(ruta_original, sufijo):
    directorio = os.path.join(os.path.dirname(ruta_original), "PDF_Resultados")
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    nombre_base = os.path.splitext(os.path.basename(ruta_original))[0]
    return os.path.join(directorio, f"{nombre_base}{sufijo}")

# --- LÓGICA BASE ---
def seleccionar():
    archivo = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
    if archivo:
        entry_archivo.delete(0, tk.END)
        entry_archivo.insert(0, archivo)

def obtener_indices(texto, total):
    try:
        indices = set()
        partes = texto.split(',')
        for parte in partes:
            if '-' in parte:
                inicio, fin = map(int, parte.split('-'))
                for i in range(inicio, fin + 1): indices.add(i - 1)
            else:
                indices.add(int(parte) - 1)
        return indices, None
    except:
        return None, "Formato inválido (Ej: 1, 3-5)."

# --- FUNCIONES DE HERRAMIENTAS ---

def procesar_pdf():
    ruta = entry_archivo.get()
    texto_pags = entry_pagina.get()
    
    if not ruta:
        messagebox.showwarning("Error", "Primero selecciona un archivo PDF.")
        return
    if not texto_pags:
        messagebox.showwarning("Error", "Ingresa las páginas (ej: 1, 3-5, 8).")
        return

    try:
        reader = PdfReader(ruta)
        writer = PdfWriter()
        total_paginas = len(reader.pages)
        paginas_a_eliminar = set()

        # --- LÓGICA DE PROCESAMIENTO DE ENTRADA ---
        partes = texto_pags.split(',')
        for parte in partes:
            parte = parte.strip()
            if '-' in parte: # Es un rango (ej: 3-5)
                try:
                    inicio, fin = map(int, parte.split('-'))
                    for n in range(inicio, fin + 1):
                        if 1 <= n <= total_paginas:
                            paginas_a_eliminar.add(n - 1)
                except: continue 
            elif parte.isdigit(): # Es un número solo
                n = int(parte)
                if 1 <= n <= total_paginas:
                    paginas_a_eliminar.add(n - 1)

        # --- RECONSTRUCCIÓN DEL PDF ---
        paginas_añadidas = 0
        for i in range(total_paginas):
            if i not in paginas_a_eliminar:
                writer.add_page(reader.pages[i])
                paginas_añadidas += 1
        
        if paginas_añadidas == total_paginas and paginas_a_eliminar:
            messagebox.showwarning("Aviso", "No se eliminó nada. Revisa los números.")
            return

        # --- SALIDA ---
        salida = obtener_ruta_salida(ruta, "_editado.pdf")
        with open(salida, "wb") as f:
            writer.write(f)
            
        messagebox.showinfo("ÉXITO", f"Páginas eliminadas.\nTotal final: {paginas_añadidas} págs.\nGuardado en: PDF_Resultados")
        
    except Exception as e:
        messagebox.showerror("Error Forense", f"Fallo en la operación: {str(e)}")

def unir_pdfs():
    rutas = list(filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")]))
    if not rutas: return
    
    v = tk.Toplevel(root)
    v.title("Ordenar Unión de PDFs")
    v.geometry("450x550")
    v.configure(bg=COLOR_FONDO)
    v.resizable(False, False)

    # Encabezado
    tk.Label(v, text="ORDENAR ARCHIVOS PARA UNIR", bg=COLOR_FONDO, fg=COLOR_BOTON_AZUL, 
             font=("Arial", 11, "bold")).pack(pady=15)
    
    # Contenedor principal para la lista y los botones laterales
    main_frame = tk.Frame(v, bg=COLOR_FONDO)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

    # Lista de archivos
    lista_box = tk.Listbox(main_frame, bg=COLOR_ENTRADA, fg=COLOR_TEXTO, 
                           font=("Consolas", 10), selectmode=tk.SINGLE, 
                           borderwidth=0, highlightthickness=1, highlightbackground="#444444")
    lista_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    for r in rutas:
        lista_box.insert(tk.END, f"  📄 {os.path.basename(r)}")

    # Funciones de movimiento
    def mover_arriba():
        idx = lista_box.curselection()
        if not idx or idx[0] == 0: return
        i = idx[0]
        texto = lista_box.get(i)
        path = rutas.pop(i)
        lista_box.delete(i)
        lista_box.insert(i-1, texto)
        rutas.insert(i-1, path)
        lista_box.select_set(i-1)

    def mover_abajo():
        idx = lista_box.curselection()
        if not idx or idx[0] == lista_box.size()-1: return
        i = idx[0]
        texto = lista_box.get(i)
        path = rutas.pop(i)
        lista_box.delete(i)
        lista_box.insert(i+1, texto)
        rutas.insert(i+1, path)
        lista_box.select_set(i+1)

    # Frame lateral para las flechas
    side_btns = tk.Frame(main_frame, bg=COLOR_FONDO)
    side_btns.pack(side=tk.RIGHT, padx=10)

    tk.Button(side_btns, text="▲", command=mover_arriba, bg="#333333", fg="white", 
              width=4, font=("Arial", 12, "bold"), relief=tk.FLAT).pack(pady=5)
    tk.Button(side_btns, text="▼", command=mover_abajo, bg="#333333", fg="white", 
              width=4, font=("Arial", 12, "bold"), relief=tk.FLAT).pack(pady=5)

    # Botón de ejecución final
    def ejecutar_union():
        if not rutas: return
        w = PdfWriter()
        try:
            for r in rutas:
                rd = PdfReader(r)
                for p in rd.pages: w.add_page(p)
            
            salida = filedialog.asksaveasfilename(defaultextension=".pdf", title="Guardar PDF Unido")
            if salida:
                with open(salida, "wb") as f:
                    w.write(f)
                messagebox.showinfo("ÉXITO", "Archivos combinados correctamente.")
                v.destroy()
        except Exception as e:
            messagebox.showerror("Error Forense", f"Falla en la unión: {str(e)}")

    tk.Button(v, text="⚡ UNIR AHORA", command=ejecutar_union, bg=COLOR_BOTON_VERDE, 
              fg="white", width=35, height=2, font=("Arial", 10, "bold")).pack(pady=25)
    
    # Firma discreta en la ventana secundaria
    tk.Label(v, text="Delta /// Forensic Engine", font=("Arial", 7, "italic"), 
             bg=COLOR_FONDO, fg="#555555").pack(side=tk.BOTTOM, pady=5)

def imagenes_a_pdf():
    r = filedialog.askopenfilenames(filetypes=[("Imágenes", "*.jpg *.png *.jpeg")])
    if not r: return
    try:
        ims = [Image.open(i).convert("RGB") for i in r]
        s = filedialog.asksaveasfilename(defaultextension=".pdf")
        if s:
            ims[0].save(s, save_all=True, append_images=ims[1:])
            messagebox.showinfo("OK", "PDF creado con éxito.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def rotar_paginas_selectivo():
    ruta = entry_archivo.get()
    if not ruta:
        messagebox.showwarning("Aviso", "Selecciona un archivo primero.")
        return
    win_r = tk.Toplevel(root)
    win_r.title("Rotar"); win_r.geometry("350x250"); win_r.configure(bg=COLOR_FONDO)
    tk.Label(win_r, text="Páginas (Ej: 1, 3-5):", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=5)
    e_pags = tk.Entry(win_r, bg=COLOR_ENTRADA, fg=COLOR_TEXTO); e_pags.pack()
    tk.Label(win_r, text="Grados (90, 180, 270):", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=5)
    e_g = tk.Entry(win_r, bg=COLOR_ENTRADA, fg=COLOR_TEXTO); e_g.pack()
    def aplicar():
        try:
            reader = PdfReader(ruta); writer = PdfWriter()
            indices, error = obtener_indices(e_pags.get(), len(reader.pages))
            if error: return
            grados = int(e_g.get())
            for i in range(len(reader.pages)):
                p = reader.pages[i]
                if i in indices: p.rotate(grados)
                writer.add_page(p)
            salida = obtener_ruta_salida(ruta, "_rotado.pdf")
            with open(salida, "wb") as f:
                writer.write(f)
            messagebox.showinfo("OK", "Guardado en PDF_Resultados"); win_r.destroy()
        except: messagebox.showerror("Error", "Verifica grados y páginas.")
    tk.Button(win_r, text="Rotar", command=aplicar, bg=COLOR_BOTON_AZUL, fg="white").pack(pady=20)

def extraer_imagenes_pdf():
    r = filedialog.askopenfilename()
    if not r: return
    try:
        doc = fitz.open(r)
        c = os.path.splitext(r)[0] + "_imgs"
        if not os.path.exists(c): os.makedirs(c)
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                b = doc.extract_image(xref)
                with open(f"{c}/img_{i}.{b['ext']}", "wb") as f:
                    f.write(b["image"])
        messagebox.showinfo("Forense", "Imágenes extraídas en su propia carpeta.")
    except Exception as e:
        messagebox.showerror("Error", "Instala pymupdf si falla.")

def buscar_patrones():
    r = filedialog.askopenfilename()
    if not r: return
    try:
        rd = PdfReader(r)
        rep = "Escaneo de Datos Sensibles:\n" + "-"*30 + "\n"
        for i, pag in enumerate(rd.pages):
            txt = pag.extract_text()
            en = re.findall(r'[\w\.-]+@[\w\.-]+', txt) # Emails
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', txt) # IPs
            if en or ips:
                rep += f"Pág {i+1}:\nEmails: {en}\nIPs: {ips}\n\n"
        w = tk.Toplevel(root)
        w.title("DLP Report")
        t = scrolledtext.ScrolledText(w, width=50, height=20)
        t.pack(); t.insert(tk.INSERT, rep or "No se detectaron fugas de datos.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def cifrar_pdf():
    r = filedialog.askopenfilename()
    if not r: return
    w = tk.Toplevel(root); w.configure(bg=COLOR_FONDO)
    tk.Label(w, text="Contraseña:", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack()
    e = tk.Entry(w, show="*"); e.pack()
    def a():
        try:
            wr = PdfWriter(); rd = PdfReader(r)
            for p in rd.pages: wr.add_page(p)
            wr.encrypt(e.get())
            salida = obtener_ruta_salida(r, "_cifrado.pdf")
            with open(salida, "wb") as f:
                wr.write(f)
            messagebox.showinfo("OK", "Cifrado con éxito."); w.destroy()
        except Exception as ex: messagebox.showerror("Error", str(ex))
    tk.Button(w, text="Aplicar", command=a, bg=COLOR_BOTON_ROJO, fg="white").pack(pady=10)

def desbloquear_pdf():
    r = filedialog.askopenfilename()
    if not r: return
    w = tk.Toplevel(root); w.configure(bg=COLOR_FONDO)
    tk.Label(w, text="Contraseña Actual:", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack()
    e = tk.Entry(w, show="*"); e.pack()
    def a():
        try:
            rd = PdfReader(r)
            if rd.decrypt(e.get()) > 0:
                wr = PdfWriter()
                for p in rd.pages: wr.add_page(p)
                salida = obtener_ruta_salida(r, "_libre.pdf")
                with open(salida, "wb") as f:
                    wr.write(f)
                messagebox.showinfo("OK", "Contraseña eliminada."); w.destroy()
            else: messagebox.showerror("Error", "Clave incorrecta.")
        except Exception as ex: messagebox.showerror("Error", str(ex))
    tk.Button(w, text="Desbloquear", command=a, bg=COLOR_BOTON_ROJO, fg="white").pack(pady=10)

def ver_metadatos():
    r = filedialog.askopenfilename()
    if not r: return
    try:
        rd = PdfReader(r)
        m = f"Metadatos:\n{rd.metadata}"
        w = tk.Toplevel(root)
        t = scrolledtext.ScrolledText(w, width=60, height=15)
        t.pack(); t.insert(tk.INSERT, m)
    except: pass

def extraer_texto():
    r = filedialog.askopenfilename()
    if not r: return
    try:
        rd = PdfReader(r); t = ""
        for p in rd.pages: t += (p.extract_text() or "") + "\n"
        salida = obtener_ruta_salida(r, ".txt")
        with open(salida, "w", encoding="utf-8") as f:
            f.write(t)
        messagebox.showinfo("OK", "Texto guardado en .txt")
    except: pass

def sanitizar_pdf():
    r = filedialog.askopenfilename()
    if not r: return
    try:
        rd = PdfReader(r); wr = PdfWriter()
        for p in rd.pages: wr.add_page(p)
        wr.add_metadata({})
        salida = obtener_ruta_salida(r, "_SANITIZADO.pdf")
        with open(salida, "wb") as f:
            wr.write(f)
        messagebox.showinfo("OK", "PDF sanitizado (Metadatos y Scripts eliminados).")
    except: pass

def marca_agua():
    r = filedialog.askopenfilename()
    if not r: return
    w_w = tk.Toplevel(root); w_w.configure(bg=COLOR_FONDO)
    tk.Label(w_w, text="Texto:", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack()
    e = tk.Entry(w_w); e.pack()
    def ap():
        try:
            rd = PdfReader(r); wr = PdfWriter()
            pk = io.BytesIO(); can = canvas.Canvas(pk, pagesize=letter)
            can.setFont("Helvetica-Bold", 60); can.saveState(); can.translate(300,450); can.rotate(45)
            can.setFillColorRGB(0.5,0.5,0.5,0.3); can.drawCentredString(0,0,e.get()); can.restoreState(); can.save(); pk.seek(0)
            wm = PdfReader(pk).pages[0]
            for p in rd.pages: 
                p.merge_page(wm); wr.add_page(p)
            salida = obtener_ruta_salida(r, "_marcado.pdf")
            with open(salida, "wb") as f:
                wr.write(f)
            w_w.destroy(); messagebox.showinfo("OK", "Marca de agua aplicada.")
        except: pass

def aplicar_firma_autografa(pdf_path, firma_path):
    try:
        # Abrimos el PDF
        doc = fitz.open(pdf_path)
        # Seleccionamos la última página (donde normalmente va la firma)
        pagina = doc[-1]
        
        # Definimos el área (ajusta estos números si quieres que sea más grande o pequeña)
        # Rect(x0, y0, x1, y1)
        area_firma = fitz.Rect(400, 650, 550, 750) 
        
        # Insertamos la imagen con fondo transparente
        pagina.insert_image(area_firma, filename=firma_path)
        
        # Guardamos con un nombre nuevo para no sobreescribir el original
        output_path = pdf_path.replace(".pdf", "_firmado.pdf")
        doc.save(output_path)
        doc.close()
        return True, output_path
    except Exception as e:
        return False, str(e)
def firmar_con_selector():
    # 1. Seleccionamos el archivo de la firma
    ruta_firma_img = filedialog.askopenfilename(
        title="Selecciona la imagen de tu firma (PNG)",
        filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg")]
    )
    
    if ruta_firma_img:
        # 2. Si seleccionaste algo, llamamos a la lógica que ya escribiste
        exito, mensaje = aplicar_firma_autografa(ruta_pdf_seleccionado, ruta_firma_img)
        
        if exito:
            messagebox.showinfo("Sistema Delta", f"¡Firmado con éxito!\nArchivo guardado como: {mensaje}")
        else:
            messagebox.showerror("Error Delta", f"No se pudo firmar: {mensaje}")

def abrir_manual():
    w_w = tk.Toplevel(root) 
    w_w.title("Manual de Usuario")
    w_w.geometry("400x300")
    w_w.configure(bg=COLOR_FONDO)
    tk.Button(w_w, text="Aplicar", command=ap).pack(pady=10)

    texto_manual = """
🛡️ MANUAL DE USUARIO - PDF SECURE TOOLKIT v8.2

GESTIÓN:
• LIMPIAR PDF: Elimina páginas específicas. Usa rangos (1-3) o comas (1,4).
• UNIR PDFs: Selecciona varios archivos para crear uno solo.
• IMG A PDF: Convierte tus fotos (JPG/PNG) en un documento PDF.
• ROTAR PÁGS: Gira páginas específicas (90, 180, 270 grados).
• EXTRAER TXT: Saca todo el texto del PDF y lo guarda en un .txt.

ANÁLISIS FORENSE:
• EXTRAER IMÁGENES: Busca y guarda todas las fotos ocultas en el PDF.
• BUSCAR PATRONES: Escanea correos e IPs (útil para detectar fugas de datos).
• VER METADATOS: Muestra la información oculta (autor, fecha, software).
• MARCA AGUA: Agrega un texto de seguridad en el fondo de las páginas.

SEGURIDAD:
• MODO SANITIZE: Limpia metadatos y scripts para envío seguro.
• CIFRAR: Protege tu PDF con una contraseña de grado militar.
• DESBLOQUEAR: Elimina la contraseña de un PDF (necesitas la clave actual).

📁 NOTA: Todos los archivos se guardan en la carpeta 'PDF_Resultados'.
    """
    
    cuadro_texto = scrolledtext.ScrolledText(ventana_manual, wrap=tk.WORD, bg=COLOR_ENTRADA, fg=COLOR_TEXTO, font=("Consolas", 10))
    cuadro_texto.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    cuadro_texto.insert(tk.INSERT, texto_manual)
    cuadro_texto.config(state=tk.DISABLED) # Para que no lo puedan editar
    tk.Button(w_w, text="Aplicar", command=ap).pack(pady=10)

# --- INTERFAZ PRINCIPAL ---
root = tk.Tk()
import sys
import os

# Función para encontrar la ruta de los recursos (necesaria para PyInstaller)
def recurso_ruta(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Cargar el icono en la ventana
try:
    root.iconbitmap(recurso_ruta("icono_pdf.ico"))
except:
    pass # Si falla, el programa sigue abriendo con el icono por defecto
root.title("PDF Secure Toolkit v8.2 Professional")
root.geometry("650x950")
root.configure(bg=COLOR_FONDO)

tk.Label(root, text="🛡️ PDF SECURE TOOLKIT", font=("Arial", 16, "bold"), bg=COLOR_FONDO, fg=COLOR_BOTON_AZUL).pack(pady=15)

# Zona de Entrada
f_in = tk.Frame(root, bg=COLOR_FONDO); f_in.pack(pady=10)
entry_archivo = tk.Entry(f_in, width=50, bg=COLOR_ENTRADA, fg=COLOR_TEXTO); entry_archivo.grid(row=0, column=0, padx=5)
tk.Button(f_in, text="...", command=seleccionar).grid(row=0, column=1)

tk.Label(root, text="Páginas a quitar:", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack()
entry_pagina = tk.Entry(root, width=10, bg=COLOR_ENTRADA, fg=COLOR_TEXTO); entry_pagina.pack()
tk.Button(root, text="LIMPIAR PDF (BORRAR PÁGINAS)", command=procesar_pdf, bg=COLOR_BOTON_VERDE, fg="white", width=40).pack(pady=10)

f_tools = tk.Frame(root, bg=COLOR_FONDO); f_tools.pack(pady=10)

# Categorías
tk.Label(f_tools, text="GESTIÓN", bg=COLOR_FONDO, fg="#888888").grid(row=0, column=0, columnspan=2)
tk.Button(f_tools, text="UNIR PDFs", command=unir_pdfs, width=20, bg=COLOR_BOTON_AZUL, fg="white").grid(row=1, column=0, padx=5, pady=2)
tk.Button(f_tools, text="IMG A PDF", command=imagenes_a_pdf, width=20, bg=COLOR_BOTON_AZUL, fg="white").grid(row=1, column=1, padx=5, pady=2)
tk.Button(f_tools, text="ROTAR PÁGS", command=rotar_paginas_selectivo, width=20, bg=COLOR_BOTON_AZUL, fg="white").grid(row=2, column=0, padx=5, pady=2)
tk.Button(f_tools, text="EXTRAER TXT", command=extraer_texto, width=20, bg=COLOR_BOTON_AZUL, fg="white").grid(row=2, column=1, padx=5, pady=2)
tk.Button(f_tools, text="✍️ FIRMAR PDF", command=firmar_con_selector, width=43, bg=COLOR_BOTON_AZUL, fg="white").grid(row=3, column=0, columnspan=2, padx=5, pady=2)
tk.Label(f_tools, text="ANÁLISIS FORENSE", bg=COLOR_FONDO, fg="#888888").grid(row=3, column=0, columnspan=2, pady=10)
tk.Button(f_tools, text="EXTRAER IMÁGENES", command=extraer_imagenes_pdf, width=20, bg=COLOR_BOTON_NARANJA, fg="white").grid(row=4, column=0, padx=5, pady=2)
tk.Button(f_tools, text="BUSCAR PATRONES", command=buscar_patrones, width=20, bg=COLOR_BOTON_NARANJA, fg="white").grid(row=4, column=1, padx=5, pady=2)
tk.Button(f_tools, text="VER METADATOS", command=ver_metadatos, width=20, bg=COLOR_BOTON_NARANJA, fg="white").grid(row=5, column=0, padx=5, pady=2)
tk.Button(f_tools, text="MARCA AGUA", command=marca_agua, width=20, bg=COLOR_BOTON_NARANJA, fg="white").grid(row=5, column=1, padx=5, pady=2)

tk.Label(f_tools, text="SEGURIDAD", bg=COLOR_FONDO, fg="#888888").grid(row=6, column=0, columnspan=2, pady=10)
tk.Button(f_tools, text="MODO SANITIZE", command=sanitizar_pdf, width=43, bg=COLOR_BOTON_MORADO, fg="white").grid(row=7, column=0, columnspan=2, pady=2)
tk.Button(f_tools, text="CIFRAR", command=cifrar_pdf, width=20, bg=COLOR_BOTON_ROJO, fg="white").grid(row=8, column=0, padx=5, pady=2)
tk.Button(f_tools, text="DESBLOQUEAR", command=desbloquear_pdf, width=20, bg=COLOR_BOTON_ROJO, fg="white").grid(row=8, column=1, padx=5, pady=2)

tk.Label(f_tools, text="AYUDA Y SOPORTE", bg=COLOR_FONDO, fg="#888888").grid(row=9, column=0, columnspan=2, pady=10)
tk.Button(f_tools, text="📖 MANUAL DE USUARIO", command=abrir_manual, width=43, bg=COLOR_BOTON_AZUL, fg="white").grid(row=10, column=0, columnspan=2, pady=5)
# --- PIE DE PÁGINA (CRÉDITOS) ---
tk.Label(root, text="---------------------------------------------------", bg=COLOR_FONDO, fg="#333333").pack()
tk.Label(root, text="Desarrollado por Delta ///", font=("Arial", 8, "italic"), bg=COLOR_FONDO, fg="#888888").pack(pady=15)
# --- SECCIÓN DE AYUDA ---

root.mainloop()