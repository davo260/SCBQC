import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import time

# Variable global para el proceso de adquisición
proceso = None
canales_actuales = set()  # Lista de canales detectados

canales_actuales = set()

def actualizar_canales(directorio_prueba):
    """
    Actualiza la lista de canales en el menú desplegable periódicamente.
    """
    global canales_actuales
    nuevos_canales = set()
    
    if os.path.exists(directorio_prueba):
        for carpeta in os.listdir(directorio_prueba):
            ruta_carpeta = os.path.join(directorio_prueba, carpeta)
            if os.path.isdir(ruta_carpeta):
                nuevos_canales.add(carpeta)
    
    # Si hay canales nuevos, actualiza la lista
    if nuevos_canales != canales_actuales:
        lista_canales["values"] = list(nuevos_canales)
        canales_actuales = nuevos_canales
    
    ventana.after(2000, actualizar_canales, directorio_prueba)

def seleccionar_directorio():
    """
    Selecciona el directorio base para guardar los datos.
    """
    directorio = filedialog.askdirectory(title="Seleccionar Directorio de Prueba")
    if directorio:
        entrada_directorio.delete(0, tk.END)
        entrada_directorio.insert(0, directorio)
        actualizar_canales(directorio)  # Llamada a la función correcta


def mostrar_metricas():
    """
    Muestra las métricas del canal seleccionado
    """
    canal_seleccionado = lista_canales.get()
    directorio_prueba = os.path.join(
        entrada_directorio.get(), entrada_prueba.get()
    )

    if canal_seleccionado == "Selecciona un canal" or not canal_seleccionado:
        messagebox.showerror("Error", "Debes seleccionar un canal.")
        return

    ruta_metricas = os.path.join(
        directorio_prueba, canal_seleccionado, f"{canal_seleccionado}_metricas.txt"
    )

    if not os.path.exists(ruta_metricas):
        messagebox.showerror(
            "Error", f"No se encontraron métricas para el canal {canal_seleccionado}."
        )
        return

    # Mostrar métricas en una nueva ventana
    ventana_metricas = tk.Toplevel(ventana)
    ventana_metricas.title(f"Métricas: {canal_seleccionado}")
    ventana_metricas.geometry("600x400")

    texto_metricas = tk.Text(ventana_metricas, wrap=tk.WORD)
    texto_metricas.pack(expand=True, fill=tk.BOTH)

    with open(ruta_metricas, "r") as archivo:
        metricas_text = archivo.read()
        texto_metricas.insert(tk.END, metricas_text)

        # Extract and highlight pass/fail status
        if "Estado de Calidad del Canal" in metricas_text:
            estado = "Pasa" if "Pasa" in metricas_text else "No Pasa"
            estado_label = tk.Label(
                ventana_metricas,
                text=f"Estado: {estado}",
                font=("Open Sans", 14),
                fg="green" if estado == "Pasa" else "red",
            )
            estado_label.pack(pady=10)


def mostrar_grafica():
    """
    Muestra las gráficas del canal seleccionado.
    """
    canal_seleccionado = lista_canales.get()
    directorio_prueba = os.path.join(
        entrada_directorio.get(), entrada_prueba.get()
    )

    if canal_seleccionado == "Selecciona un canal" or not canal_seleccionado:
        messagebox.showerror("Error", "Debes seleccionar un canal.")
        return

    ruta_grafica = os.path.join(
        directorio_prueba, canal_seleccionado, f"{canal_seleccionado}_temperatura_vs_voltaje_scb.png"
    )

    if not os.path.exists(ruta_grafica):
        messagebox.showerror(
            "Error", f"No se encontraron gráficas para el canal {canal_seleccionado}."
        )
        return

    # Mostrar gráfica en una nueva ventana
    ventana_grafica = tk.Toplevel(ventana)
    ventana_grafica.title(f"Gráfica: {canal_seleccionado}")
    ventana_grafica.geometry("800x600")

    img_label = tk.Label(ventana_grafica)
    img_label.pack(fill=tk.BOTH, expand=True)

    # Mostrar la imagen utilizando PIL
    from PIL import Image, ImageTk

    img = Image.open(ruta_grafica)
    img = img.resize((800, 600), Image.ANTIALIAS)
    img_tk = ImageTk.PhotoImage(img)
    img_label.config(image=img_tk)
    img_label.image = img_tk

def ejecutar_script():
    """
    Ejecuta el script de adquisición de datos.
    """
    global proceso
    if proceso is None:
        directorio_base = entrada_directorio.get()
        prueba = entrada_prueba.get()
        threshold_temp = entrada_umbral.get()  # Get threshold from the user

        if not directorio_base or not os.path.exists(directorio_base):
            messagebox.showerror("Error", "Debe seleccionar un directorio base válido.")
            return
        if not prueba:
            messagebox.showerror("Error", "Debe ingresar el nombre de la prueba.")
            return

        directorio_prueba = os.path.join(directorio_base, prueba)
        if not os.path.exists(directorio_prueba):
            os.makedirs(directorio_prueba)

        # Ejecuta el script como un proceso separado, pasando el threshold como argumento
        proceso = subprocess.Popen(
            ["python3", "/home/davo/Desktop/VRB/src/adquisicion_datos.py", prueba, directorio_prueba, threshold_temp]
        )
        label_estado.config(text="Ejecutando el script...", fg="green")
        ventana.after(1000, verificar_proceso)
        actualizar_canales(directorio_prueba)
    else:
        messagebox.showinfo("Información", "El script ya está en ejecución.")


def verificar_proceso():
    """
    Verifica si el proceso sigue ejecutándose y actualiza la interfaz.
    """
    global proceso
    if proceso and proceso.poll() is None:  # Proceso en ejecución
        ventana.after(1000, verificar_proceso)
    else:  # Proceso finalizado
        proceso = None
        label_estado.config(text="Script finalizado.", fg="red")

def detener_script():
    """
    Detiene el proceso de adquisición.
    """
    global proceso
    if proceso is not None:
        proceso.terminate()
        proceso = None
        label_estado.config(text="Script detenido.", fg="red")
    else:
        messagebox.showinfo("Información", "No hay ningún script en ejecución.")

def seleccionar_directorio():
    """
    Selecciona el directorio base para guardar los datos.
    """
    directorio = filedialog.askdirectory(title="Seleccionar Directorio de Prueba")
    if directorio:
        entrada_directorio.delete(0, tk.END)
        entrada_directorio.insert(0, directorio)
        actualizar_canales(directorio)

# Botón para mostrar métricas y gráficas del canal seleccionado
def mostrar_metricas_y_graficas():
    """
    Muestra las métricas y las gráficas (temperatura vs voltaje y delta vs temperatura VRB) 
    del canal seleccionado.
    """
    canal_seleccionado = lista_canales.get()
    directorio_prueba = os.path.join(
        entrada_directorio.get(), entrada_prueba.get()
    )

    if canal_seleccionado == "Selecciona un canal" or not canal_seleccionado:
        messagebox.showerror("Error", "Debes seleccionar un canal.")
        return

    # Ruta de las métricas y gráficas
    ruta_metricas = os.path.join(
        directorio_prueba, canal_seleccionado, f"{canal_seleccionado}_metricas.txt"
    )
    ruta_grafica_temperatura = os.path.join(
        directorio_prueba, canal_seleccionado, f"{canal_seleccionado}_temperatura_vs_voltaje_scb.png"
    )
    ruta_grafica_delta = os.path.join(
        directorio_prueba, canal_seleccionado, f"{canal_seleccionado}_delta_vs_temperatura_vrb.png"
    )

    if not os.path.exists(ruta_metricas):
        messagebox.showerror(
            "Error", f"No se encontraron métricas para el canal {canal_seleccionado}."
        )
        return

    if not os.path.exists(ruta_grafica_temperatura):
        messagebox.showerror(
            "Error", f"No se encontró la gráfica de temperatura vs voltaje SCB para el canal {canal_seleccionado}."
        )
        return

    if not os.path.exists(ruta_grafica_delta):
        messagebox.showerror(
            "Error", f"No se encontró la gráfica de delta vs temperatura VRB para el canal {canal_seleccionado}."
        )
        return

    # Mostrar métricas en una nueva ventana
    ventana_metricas = tk.Toplevel(ventana)
    ventana_metricas.title(f"Resultados: {canal_seleccionado}")
    ventana_metricas.geometry("800x800")

    # Texto para métricas
    frame_metricas = tk.Frame(ventana_metricas)
    frame_metricas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    texto_metricas = tk.Text(frame_metricas, wrap=tk.WORD, height=10)
    texto_metricas.pack(fill=tk.BOTH, expand=True)

    with open(ruta_metricas, "r") as archivo:
        texto_metricas.insert(tk.END, archivo.read())

    # Mostrar gráficas
    from PIL import Image, ImageTk

    frame_graficas = tk.Frame(ventana_metricas)
    frame_graficas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Primera gráfica: Temperatura vs Voltaje SCB
    img_temperatura = Image.open(ruta_grafica_temperatura)
    img_temperatura = img_temperatura.resize((350, 250), Image.ANTIALIAS)
    img_temperatura_tk = ImageTk.PhotoImage(img_temperatura)

    label_grafica_temperatura = tk.Label(frame_graficas, image=img_temperatura_tk)
    label_grafica_temperatura.image = img_temperatura_tk  # Mantener referencia
    label_grafica_temperatura.pack(side=tk.LEFT, padx=10)

    # Segunda gráfica: Delta vs Temperatura VRB
    img_delta = Image.open(ruta_grafica_delta)
    img_delta = img_delta.resize((350, 250), Image.ANTIALIAS)
    img_delta_tk = ImageTk.PhotoImage(img_delta)

    label_grafica_delta = tk.Label(frame_graficas, image=img_delta_tk)
    label_grafica_delta.image = img_delta_tk  # Mantener referencia
    label_grafica_delta.pack(side=tk.RIGHT, padx=10)

    # Botón para cerrar la ventana
    boton_cerrar = tk.Button(
        ventana_metricas, text="Cerrar", command=ventana_metricas.destroy
    )
    boton_cerrar.pack(pady=5)


# Configuración de la ventana principal
ventana = tk.Tk()
ventana.title("SCB Control de calidad")
ventana.geometry("600x400")

# Etiqueta de título
label_titulo = tk.Label(
    ventana, text="Control de calidad SCB", font=("Open Sans", 16)
)
label_titulo.pack(pady=10)

# Entrada para el nombre de la prueba
frame_prueba = tk.Frame(ventana)
frame_prueba.pack(pady=5, fill=tk.X, padx=10)

label_prueba = tk.Label(frame_prueba, text="Nombre de la Prueba:")
label_prueba.pack(side=tk.LEFT, padx=5)

entrada_prueba = tk.Entry(frame_prueba)
entrada_prueba.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Selección del directorio base
frame_directorio = tk.Frame(ventana)
frame_directorio.pack(pady=5, fill=tk.X, padx=10)

label_directorio = tk.Label(frame_directorio, text="Directorio Base:")
label_directorio.pack(side=tk.LEFT, padx=5)

entrada_directorio = tk.Entry(frame_directorio)
entrada_directorio.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Entrada para el umbral de temperatura
frame_umbral = tk.Frame(ventana)
frame_umbral.pack(pady=5, fill=tk.X, padx=10)

label_umbral = tk.Label(frame_umbral, text="Umbral de Temperatura (°C):")
label_umbral.pack(side=tk.LEFT, padx=5)

entrada_umbral = tk.Entry(frame_umbral)
entrada_umbral.insert(0, "2.0")  # Default threshold value
entrada_umbral.pack(side=tk.LEFT, fill=tk.X, expand=True)


boton_directorio = tk.Button(
    frame_directorio, text="Seleccionar", command=seleccionar_directorio
)
boton_directorio.pack(side=tk.LEFT, padx=5)

# Menú desplegable para seleccionar canal
frame_canales = tk.Frame(ventana)
frame_canales.pack(pady=5, fill=tk.X, padx=10)

label_canales = tk.Label(frame_canales, text="Canal:")
label_canales.pack(side=tk.LEFT, padx=5)

lista_canales = ttk.Combobox(frame_canales, state="readonly")
lista_canales.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Botón para ejecutar el script
boton_ejecutar = tk.Button(
    ventana, text="Iniciar Adquisición", command=ejecutar_script, font=("Open Sans", 12)
)
boton_ejecutar.pack(pady=10)

# Botón para detener el script
boton_detener = tk.Button(
    ventana, text="Detener Adquisición", command=detener_script, font=("Open Sans", 12)
)
boton_detener.pack(pady=10)

# Botón para mostrar métricas y gráficas
boton_mostrar_resultados = tk.Button(
    frame_canales, text="Mostrar Resultados", command=mostrar_metricas_y_graficas
)
boton_mostrar_resultados.pack(side=tk.LEFT, padx=5)


label_estado = tk.Label(ventana, text="Estado: Inactivo", font=("Open Sans", 10), fg="red")
label_estado.pack(pady=10)

# Inicia el bucle principal de la interfaz
ventana.mainloop()
