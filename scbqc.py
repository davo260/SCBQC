"""
Interfaz gráfica para el control de calidad de las tarjetas de acondicionamiento de señal (SCB).
Permite ejecutar scripts de adquisición, mostrar resultados, y gestionar métricas y gráficos.

Autor: Diego Alejandro Vera Ortega
Fecha: 18/11/2024
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import time
from PIL import Image, ImageTk
import pandas as pd
import csv
import matplotlib.pyplot as plt

# Variable global para el proceso de adquisición
proceso = None
canales_actuales = set()  # Lista de canales detectados

def actualizar_canales_prueba():
    """
    Actualiza la lista de canales en el menú desplegable para la prueba seleccionada.
    """
    global canales_actuales
    directorio_base = entrada_directorio.get()
    prueba = entrada_prueba.get()
    nuevos_canales = set()

    if directorio_base and prueba:
        directorio_prueba = os.path.join(directorio_base, prueba)
        if os.path.exists(directorio_prueba):
            for carpeta in os.listdir(directorio_prueba):
                ruta_carpeta = os.path.join(directorio_prueba, carpeta)
                if os.path.isdir(ruta_carpeta) and carpeta.startswith("PT"):
                    nuevos_canales.add(carpeta)
    
    # Si hay canales nuevos, actualiza la lista
    if nuevos_canales != canales_actuales:
        lista_canales["values"] = sorted(list(nuevos_canales))
        canales_actuales = sorted(nuevos_canales, key=lambda x: (x[:3], int(x[3:])))
    else:
        lista_canales["values"] = sorted(list(canales_actuales))

    ventana.after(5000, actualizar_canales_prueba)  # Actualiza cada 5 segundos

def seleccionar_directorio():
    """
    Selecciona el directorio base para guardar los datos.
    """
    directorio = filedialog.askdirectory(title="Select Test Directory")
    if directorio:
        entrada_directorio.delete(0, tk.END)
        entrada_directorio.insert(0, directorio)
        actualizar_canales_prueba()

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
            messagebox.showerror("Error", "You must select a valid base directory.")
            return
        if not prueba:
            messagebox.showerror("Error", "You must enter the test name.")
            return

        directorio_prueba = os.path.join(directorio_base, prueba)
        if not os.path.exists(directorio_prueba):
            os.makedirs(directorio_prueba)

        # Ejecuta el script como un proceso separado, pasando el threshold como argumento
        proceso = subprocess.Popen(
            ["python3", "/home/davo/Desktop/VRB/src/adquisicion_datos.py", prueba, directorio_prueba, threshold_temp]
        )
        label_estado.config(text="Executing the script...", fg="green")
        ventana.after(1000, verificar_proceso)
    else:
        messagebox.showinfo("Information", "The script is already running.")

def verificar_proceso():
    """
    Verifica si el proceso sigue ejecutándose y actualiza la interfaz.
    """
    global proceso
    mostrar_metricas_y_graficas()  # Mostrar métricas parciales
    if proceso and proceso.poll() is None:  # Proceso en ejecución
        ventana.after(1000, verificar_proceso)
    else:  # Proceso finalizado
        proceso = None
        label_estado.config(text="Script finished.", fg="red")
        actualizar_canales_prueba()
        mostrar_metricas_y_graficas()

def detener_script():
    """
    Detiene el proceso de adquisición.
    """
    global proceso
    if proceso is not None:
        proceso.terminate()
        proceso = None
        label_estado.config(text="Script stopped.", fg="red")
        actualizar_canales_prueba()
    else:
        messagebox.showinfo("Información", "No script is currently running.")

def mostrar_metricas_y_graficas():
    """
    Muestra las métricas y llena la tabla de resultados automáticamente.
    También genera un archivo CSV con todas las temperaturas VRB y deltas de temperatura de todos los canales.
    """
    directorio_prueba = os.path.join(
        entrada_directorio.get(), entrada_prueba.get()
    )

    # Limpiar la tabla antes de llenarla nuevamente
    for item in tabla_resultados.get_children():
        tabla_resultados.delete(item)

    # Diccionario para almacenar Temperatura VRB y deltas de temperatura
    datos_combinados = {
        "Temperatura VRB": []
    }

    # Lista para almacenar todos los deltas de temperatura
    todos_los_deltas = []

    # Leer métricas de todos los canales y llenar la tabla
    for canal in sorted(canales_actuales, key=lambda x: (x[:3], int(x[3:]))):
        ruta_metricas_csv = os.path.join(
            directorio_prueba, canal, f"{canal}_metricas.csv"
        )

        if not os.path.exists(ruta_metricas_csv):
            continue

        # Leer métricas del archivo CSV y llenar la tabla
        try:
            with open(ruta_metricas_csv, 'r') as archivo_metricas:
                lineas = archivo_metricas.readlines()
                promedio_error = float(lineas[0].split(":")[1].strip().replace(',', '').replace('°C', '').strip())
                promedio_error_abs = float(lineas[1].split(":")[1].strip().replace(',', '').replace('°C', '').strip())
                error_maximo = float(lineas[2].split(":")[1].strip().replace(',', '').replace('°C', '').strip())
                desviacion_estandar = float(lineas[3].split(":")[1].strip().replace(',', '').replace('°C', '').strip())
                error_cuadratico_medio = float(lineas[4].split(":")[1].strip().replace(',', '').replace('°C', '').strip())
                estado_calidad = lineas[5].split(":")[1].strip()

            # Insertar los datos en la tabla
            color = 'green' if estado_calidad.lower() == 'pass' else 'red'
            tabla_resultados.insert("", "end", values=(
                canal, estado_calidad, error_cuadratico_medio, desviacion_estandar, error_maximo
            ), tags=(estado_calidad,))
            tabla_resultados.tag_configure('Pass', foreground='green')
            tabla_resultados.tag_configure('Fail', foreground='red')
            tabla_resultados.tag_configure('No Pass', foreground='red')

            # Agregar delta_temp al listado de todos los deltas
            delta_temp = [float(line.strip().split(":")[1]) for line in lineas if "Delta Temperatura" in line]
            todos_los_deltas.extend(delta_temp)

            # Agregar temperatura VRB y delta al diccionario de datos combinados
            if "Temperatura VRB" not in datos_combinados or not datos_combinados["Temperatura VRB"]:
                datos_combinados["Temperatura VRB"] = delta_temp  # Asumiendo que VRB es consistente en cada archivo
            if len(datos_combinados["Temperatura VRB"]) == 0:
                datos_combinados["Temperatura VRB"] = delta_temp  # Usar solo la primera columna VRB como referencia
            else:
                datos_combinados[canal] = delta_temp if len(delta_temp) == len(datos_combinados["Temperatura VRB"]) else [None] * len(datos_combinados["Temperatura VRB"])
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read metrics for channel {canal}: {e}")
            return

    # Guardar los datos combinados en un archivo CSV
    ruta_csv_combinado = os.path.join(directorio_prueba, "combined_deltas.csv")
    df_combinado = pd.DataFrame(datos_combinados)
    df_combinado.to_csv(ruta_csv_combinado, index=False)

    # Guardar los datos combinados en un archivo CSV
    ruta_csv_combinado = os.path.join(directorio_prueba, "combined_deltas.csv")
    df_combinado = pd.DataFrame(datos_combinados)
    df_combinado.to_csv(ruta_csv_combinado, index=False)

    # Graficar todos los deltas de temperatura al finalizar
    if todos_los_deltas:
        fig, ax = plt.subplots()
        ax.plot(todos_los_deltas, label="Delta Temperatures")
        ax.set_xlabel("Index")
        ax.set_ylabel("Delta Temperature (°C)")
        ax.set_title("Delta Temperatures for All Channels")
        ax.legend()
        ax.grid()

        # Integrar la gráfica en la interfaz de Tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=frame_principal)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Configuración de la ventana principal
ventana = tk.Tk()
ventana.title("SCB Quality Control")
ventana.geometry("1200x800")

# Logo en la parte superior izquierda
frame_logo = tk.Frame(ventana)
frame_logo.pack(side=tk.TOP, anchor="w", padx=10, pady=10)

# Logo ATLAS
logo_atlas = Image.open("/home/davo/Desktop/VRB/logo/ATLAS logo default transparent RGBHEX 300ppi.png")  # Ruta al logo de ATLAS
logo_atlas = logo_atlas.resize((250, 100), Image.LANCZOS)
logo_atlas_tk = ImageTk.PhotoImage(logo_atlas)
label_logo_atlas = tk.Label(frame_logo, image=logo_atlas_tk)
label_logo_atlas.image = logo_atlas_tk
label_logo_atlas.pack(side=tk.LEFT)

# Logo Universidad
logo_uni = Image.open("/home/davo/Desktop/VRB/logo/LogoPUJ.png")  # Ruta al logo de la universidad
logo_uni = logo_uni.resize((100, 100), Image.LANCZOS)
logo_uni_tk = ImageTk.PhotoImage(logo_uni)
label_logo_uni = tk.Label(frame_logo, image=logo_uni_tk)
label_logo_uni.image = logo_uni_tk
label_logo_uni.pack(side=tk.LEFT, padx=10)

# Etiqueta de título
label_titulo = tk.Label(
    frame_logo, text="Quality Control for the Signal Conditioning Board", font=("Open Sans", 23)
)
label_titulo.pack(side=tk.LEFT, padx=20)

# Frame principal que contiene parámetros y explicación
frame_principal = tk.Frame(ventana)
frame_principal.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Frame para parámetros de entrada
frame_parametros = tk.Frame(frame_principal)
frame_parametros.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10, anchor="n")

# Entrada para el nombre de la prueba
frame_prueba = tk.Frame(frame_parametros)
frame_prueba.pack(pady=5, fill=tk.X)

label_prueba = tk.Label(frame_prueba, text="Test Name:")
label_prueba.pack(side=tk.LEFT, padx=5)

entrada_prueba = tk.Entry(frame_prueba)
entrada_prueba.pack(side=tk.LEFT, fill=tk.X, expand=True)
entrada_prueba.bind("<KeyRelease>", lambda event: actualizar_canales_prueba())

# Selección del directorio base
frame_directorio = tk.Frame(frame_parametros)
frame_directorio.pack(pady=5, fill=tk.X)

label_directorio = tk.Label(frame_directorio, text="Base Directory:")
label_directorio.pack(side=tk.LEFT, padx=5)

entrada_directorio = tk.Entry(frame_directorio)
entrada_directorio.pack(side=tk.LEFT, fill=tk.X, expand=True)
entrada_directorio.bind("<KeyRelease>", lambda event: actualizar_canales_prueba())

# Entrada para el umbral de temperatura
frame_umbral = tk.Frame(frame_parametros)
frame_umbral.pack(pady=5, fill=tk.X)

label_umbral = tk.Label(frame_umbral, text="Temperature Threshold (°C):")
label_umbral.pack(side=tk.LEFT, padx=5)

entrada_umbral = tk.Entry(frame_umbral)
entrada_umbral.insert(0, "2.0")  # Default threshold value
entrada_umbral.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Menú desplegable para seleccionar canal
frame_canales = tk.Frame(frame_parametros)
frame_canales.pack(pady=5, fill=tk.X)

label_canales = tk.Label(frame_canales, text="Channel:")
label_canales.pack(side=tk.LEFT, padx=5)

lista_canales = ttk.Combobox(frame_canales, state="readonly")
lista_canales.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Botón para seleccionar directorio
boton_directorio = tk.Button(
    frame_directorio, text="Select", command=seleccionar_directorio
)
boton_directorio.pack(side=tk.LEFT, padx=5)

# Explicación de cada parámetro
frame_explicacion = tk.Frame(frame_principal)
frame_explicacion.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10, anchor="n")

label_explicacion = tk.Label(
    frame_explicacion, text="Explanation of Parameters:", font=("Open Sans", 14)
)
label_explicacion.pack(anchor="n", pady=10)

explicacion_texto = (
    "Test Name: Name to identify the quality test.\n"
    "Base Directory: Path where the test results will be saved.\n"
    "Temperature Threshold: Limit value for temperature during data acquisition.\n"
    "Channel: Select the channel to view the results."
)

label_explicacion_texto = tk.Label(
    frame_explicacion, text=explicacion_texto, font=("Open Sans", 12), justify="left"
)
label_explicacion_texto.pack(anchor="n")

# Botones para ejecutar y detener el script
frame_botones = tk.Frame(frame_parametros)
frame_botones.pack(pady=10, fill=tk.X)

boton_ejecutar = tk.Button(
    frame_botones, text="Start Acquisition", command=ejecutar_script, font=("Open Sans", 12)
)
boton_ejecutar.pack(side=tk.LEFT, padx=5, pady=5)

boton_detener = tk.Button(
    frame_botones, text="Stop Acquisition", command=detener_script, font=("Open Sans", 12)
)
boton_detener.pack(side=tk.LEFT, padx=5, pady=5)

# Estado del proceso
label_estado = tk.Label(ventana, text="Status: Inactive", font=("Open Sans", 12), fg="red")
label_estado.pack(pady=10)

# Tabla para mostrar resultados
frame_tabla_resultados = tk.Frame(ventana)
frame_tabla_resultados.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10)

label_tabla_resultados = tk.Label(frame_tabla_resultados, text="Test Results:")
label_tabla_resultados.pack(side=tk.TOP, pady=5)

columns = ("Channel", "Test Result", "Error (RMS °C)", "STDV (°C)", "Maximum Error (°C)")
tabla_resultados = ttk.Treeview(frame_tabla_resultados, columns=columns, show="headings", style="Custom.Treeview")
for col in columns:
    tabla_resultados.heading(col, text=col, anchor='center')
    tabla_resultados.column(col, minwidth=150, width=200, anchor='center')
tabla_resultados.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Estilo personalizado para la tabla
style = ttk.Style()
style.configure("Custom.Treeview", 
                background="#f0f0f0", 
                foreground="black", 
                rowheight=25, 
                fieldbackground="#e0e0e0")
style.map('Custom.Treeview', 
           background=[('selected', '#4caf50')],
           foreground=[('selected', 'white')])

# Inicia el bucle principal de la interfaz
ventana.mainloop()
