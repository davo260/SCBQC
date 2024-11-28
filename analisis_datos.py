"""
Script para procesar datos de mediciones, calcular métricas de error, 
y generar gráficos de resultados. Los datos se guardan en archivos CSV
y se crean carpetas organizadas para cada canal.

Autor: Diego Alejandro Vera Ortega
Fecha: 18/11/2024
"""

import os
import matplotlib.pyplot as plt
import csv
import numpy as np
import math
import pandas as pd

def validar_canal(delta_temperaturas, threshold_temp):
 """
    Valida el canal basado en el error RMS y un umbral.

    Parameters:
    - delta_temperaturas: Lista o array de deltas de temperatura (VRB - SCB).
    - threshold_temp: Umbral para la validación del error RMS.

    Returns:
    - True si el canal pasa el umbral, False en caso contrario.
    """
    # Calculate RMS error
    rms_error = np.sqrt(np.mean(delta_temperaturas ** 2))
    return rms_error <= threshold_temp


def procesar_y_guardar_datos(datos, directorio_canal, canal_descriptivo, temp_threshold, directorio_base_csv):

    """
    Procesa los datos recibidos, guarda en un archivo CSV y genera gráficas.
    También calcula y guarda métricas de error.

    Parameters:
    - datos: Diccionario con los datos medidos.
    - directorio_canal: Ruta del directorio donde guardar los resultados del canal.
    - canal_descriptivo: Nombre descriptivo del canal.
    - temp_threshold: Umbral para la validación del error RMS.
    - directorio_base_csv: Ruta base para el archivo combinado de deltas.

    """
    if not os.path.exists(directorio_canal):
        os.makedirs(directorio_canal)

    # Variables para gráficos y métricas
    delta_temp = []
    sum_squared_errors = 0


    # Cálculo del delta de temperatura
    for voltaje, corriente, voltaje_scb, temp_scb, temp_vrb in zip(
        datos["voltajes"], datos["corrientes"], datos["voltaje_scb"],
        datos["temperatura_scb"], datos["temperatura_vrb"]
    ):
        delta_t = temp_vrb - temp_scb  # Calcular delta de temperatura
        delta_temp.append(delta_t)
        sum_squared_errors += delta_t ** 2
    
    #Calculo del RMSD

    rmsd = math.sqrt(sum_squared_errors/len(delta_temp))

    #Validacion del canal
    pasa_calidad = rmsd <= temp_threshold 
    
    # Convertir delta_temp a un array de NumPy para cálculos rápidos
    delta_temp = np.array(delta_temp)

    # Cálculos de métricas
    promedio_error = np.mean(delta_temp)
    promedio_error_abs = np.mean(np.abs(delta_temp))
    desviacion_estandar = np.std(delta_temp)  # Desviación estándar del error
    error_cuadratico_medio = np.sqrt(np.mean(delta_temp ** 2))  # RMSE
    error_maximo = np.max(np.abs(delta_temp))  # Error máximo

    # Guardar métricas en un archivo
    nombre_archivo_metricas = os.path.join(
     directorio_canal, f"{canal_descriptivo}_metricas.csv"
    )
    with open(nombre_archivo_metricas, mode='w') as archivo_metricas:
        archivo_metricas.write(f"Promedio del Error: {promedio_error:.3f} °C\n")
        archivo_metricas.write(f"Promedio Absoluto del Error: {promedio_error_abs:.3f} °C\n")
        archivo_metricas.write(f"Error Máximo: {error_maximo:.3f} °C\n")
        archivo_metricas.write(f"Desviación Estándar del Error: {desviacion_estandar:.3f} °C\n")
        archivo_metricas.write(f"Error Cuadrático Medio (RMSD): {error_cuadratico_medio:.3f} °C\n")
        archivo_metricas.write(f"Estado de Calidad del Canal: {'Pass' if validar_canal(delta_temp, datos['threshold_temp']) else 'No Pass'}\n")

    # Guardar los datos en un archivo CSV
    nombre_archivo_csv = os.path.join(directorio_canal, f"{canal_descriptivo}_datos.csv")
    with open(nombre_archivo_csv, mode='w', newline='') as archivo_csv:
        writer = csv.writer(archivo_csv)
        writer.writerow([
            "Voltaje (V)", "Corriente (µA)", "Voltaje SCB (V)",
            "Temperatura SCB (°C)", "Temperatura VRB (°C)", "Delta Temperatura (°C)"
        ])
        for voltaje, corriente, voltaje_scb, temp_scb, temp_vrb, delta_t in zip(
            datos["voltajes"], datos["corrientes"], datos["voltaje_scb"],
            datos["temperatura_scb"], datos["temperatura_vrb"], delta_temp
        ):
            writer.writerow([voltaje, corriente, voltaje_scb, temp_scb, temp_vrb, delta_t])

    # Guardar delta y temperatura VRB en un archivo CSV combinado
    ruta_csv_combinado = os.path.join(directorio_base_csv, "combined_deltas.csv")
    if not os.path.exists(ruta_csv_combinado):
        with open(ruta_csv_combinado, mode='w', newline='') as archivo_csv:
            writer = csv.writer(archivo_csv)
            writer.writerow(["Temperatura VRB"] + [canal_descriptivo])
        for temp_vrb, delta_t in zip(datos["temperatura_vrb"], delta_temp):
            writer.writerow([temp_vrb, delta_t])
    else:
    # Si el archivo ya existe, agregar una nueva columna con el delta del nuevo canal
        df = pd.read_csv(ruta_csv_combinado)
        df[canal_descriptivo] = delta_temp
        df.to_csv(ruta_csv_combinado, index=False)

    # Generar gráficas
    generar_graficas(datos, delta_temp, directorio_canal, canal_descriptivo)

    print(f"Datos, gráficas y métricas guardados para {canal_descriptivo} en {directorio_canal}")


def generar_graficas(datos, delta_temp, directorio_canal, canal_descriptivo):
    """
    Genera las gráficas de los datos y las guarda en el directorio correspondiente.
    Parameters:
    - datos: Diccionario con los datos medidos.
    - delta_temp: Array de deltas de temperatura (VRB - SCB).
    - directorio_canal: Ruta del directorio donde guardar las gráficas.
    - canal_descriptivo: Nombre descriptivo del canal.
    """
    # Gráfica de Temperatura SCB y VRB vs Voltaje SCB
    plt.figure()
    plt.plot(datos["voltaje_scb"], datos["temperatura_scb"], label="Temperatura SCB")
    plt.plot(datos["voltaje_scb"], datos["temperatura_vrb"], label="Temperatura VRB")
    plt.xlabel("Voltaje SCB (V)")
    plt.ylabel("Temperatura (°C)")
    plt.title(f"Temperatura SCB y VRB vs Voltaje SCB para {canal_descriptivo}")
    plt.legend()
    plt.grid()

    nombre_imagen_combinada = os.path.join(
        directorio_canal, f"{canal_descriptivo}_temperatura_vs_voltaje_scb.png"
    )
    plt.savefig(nombre_imagen_combinada)
    plt.close()
<
    # Gráfica del delta de temperatura vs temperatura VRB
    plt.figure()
    plt.plot(datos["temperatura_vrb"], delta_temp, label="Delta de Temperatura (VRB - SCB)")
    plt.xlabel("Temperatura VRB (°C)")
    plt.ylabel("Δ Temperatura (°C)")
    plt.title(f"Δ Temperatura vs Temperatura VRB para {canal_descriptivo}")
    plt.legend()
    plt.grid()

    nombre_imagen_delta = os.path.join(
        directorio_canal, f"{canal_descriptivo}_delta_vs_temperatura_vrb.png"
    )
    plt.savefig(nombre_imagen_delta)
    plt.close()

    # Gráfica de histograma del delta de temperatura
    plt.figure()
    plt.hist(delta_temp, bins=20, edgecolor='black')
    plt.xlabel("Δ Temperatura (°C)")
    plt.ylabel("Frecuencia")
    plt.title(f"Histograma de Δ Temperatura para {canal_descriptivo}")
    plt.grid()

    nombre_imagen_histograma = os.path.join(
        directorio_canal, f"{canal_descriptivo}_histograma_delta_temperatura.png"
    )
    plt.savefig(nombre_imagen_histograma)
    plt.close()
