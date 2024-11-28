"""
Script para realizar barridos de voltaje en canales del multiplexor ADG732,
adquiriendo mediciones de corriente, voltaje y temperatura. 
Guarda los resultados en una estructura organizada de carpetas.

Autor: Diego Alejandro Vera Ortega
Fecha: 18/11/2024
"""

import os
import time
import sys
import numpy as np
import pyvisa
from pymeasure.instruments.agilent import Agilent34450A
import RPi.GPIO as GPIO
from analisis_datos import procesar_y_guardar_datos

# Validación de argumentos de entrada
if len(sys.argv) != 4:
    print("Uso: python script.py <nombre_prueba> <directorio_base> <temp_threshold>")
    sys.exit(1)

nombre_prueba = sys.argv[1]
directorio_base = sys.argv[2]
temp_threshold = float(sys.argv[3])
directorio_prueba = os.path.join(directorio_base, nombre_prueba)

# Configuración de recursos
rm = pyvisa.ResourceManager()
fuente = rm.open_resource("USB0::10893::13058::MY61004672::0::INSTR")
amperimetro = Agilent34450A("USB0::2391::45848::MY53090070::0::INSTR")
voltimetro = Agilent34450A("USB::2391::45848::MY55490094::0::INSTR")

# Configuración inicial de instrumentos
amperimetro.nplc = 0.02
amperimetro.configure_current(current_range="AUTO", ac=False, resolution="DEF")
voltimetro.configure_voltage(voltage_range="AUTO", ac=False, resolution="DEF")

fuente.write("INST:SEL CH2")
fuente.write("VOLT 12")
fuente.write("CURR 0.1")
fuente.write("OUTP ON")
fuente.write("INST:SEL CH1")

# Configuración GPIO
gpio_a_pins = [10, 8, 7, 5, 3]
gpio_a_pins_mux2 = [29, 31, 33, 35, 37]
gpio_control_pins = [12, 11, 13]
gpio_control_pins_mux2 = [36, 38, 40]

GPIO.setmode(GPIO.BOARD)

for pin in gpio_a_pins + gpio_control_pins + gpio_a_pins_mux2 + gpio_control_pins_mux2:
    GPIO.setup(pin, GPIO.OUT)

for pin in gpio_control_pins + gpio_control_pins_mux2:
    GPIO.output(pin, GPIO.LOW)

# Mapeos de canales
canal_a_binario = {
    "s3": "00010", "s4": "00011", "s5": "00100", "s6": "00101", "s7": "00110",
    "s8": "00111", "s9": "01000", "s10": "01001", "s11": "01010", "s12": "01011",
    "s13": "01100", "s14": "01101", "s28": "11011", "s27": "11010", "s26": "11001",
    "s25": "11000", "s24": "10111", "s23": "10110", "s22": "10101", "s21": "10100",
    "s20": "10011", "s19": "10010", "s18": "10001", "s17": "10000"
}
canal_a_binario_mux2 = canal_a_binario.copy()

mapeo_sincronizado = {
    "s3": "s17", "s4": "s18", "s5": "s19", "s6": "s20", "s7": "s21",
    "s8": "s22", "s9": "s23", "s10": "s24", "s11": "s25", "s12": "s26",
    "s13": "s27", "s14": "s28", "s28": "s14", "s27": "s13", "s26": "s12",
    "s25": "s11", "s24": "s10", "s23": "s9", "s22": "s8", "s21": "s7",
    "s20": "s6", "s19": "s5", "s18": "s4", "s17": "s3"
}

nombre_canal = {
    "s3_s17": "pta1", "s4_s18": "ptb1", "s5_s19": "pta2", "s6_s20": "ptb2",
    "s7_s21": "pta3", "s8_s22": "ptb3", "s9_s23": "pta4", "s10_s24": "ptb4",
    "s11_s25": "pta5", "s12_s26": "ptb5", "s13_s27": "pta6", "s14_s28": "ptb6",
    "s28_s14": "pta7", "s27_s13": "ptb7", "s26_s12": "pta8", "s25_s11": "ptb8",
    "s24_s10": "pta9", "s23_s9": "ptb9", "s22_s8": "pta10", "s21_s7": "ptb10",
    "s20_s6": "pta11", "s19_s5": "ptb11", "s18_s4": "pta12", "s17_s3": "ptb12"
}

def seleccionar_entrada(switch):
    """
    Configura los pines del MUX1 para el canal dado.
    """
    valores_a = [int(x) for x in canal_a_binario[switch]]
    for pin, valor in zip(gpio_a_pins, valores_a):
        GPIO.output(pin, valor)

def seleccionar_entrada_mux2(switch):
    """
    Configura los pines del MUX2 para el canal dado.
    """
    valores_a = [int(x) for x in canal_a_binario_mux2[switch]]
    for pin, valor in zip(gpio_a_pins_mux2, valores_a):
        GPIO.output(pin, valor)

def corriente_a_temperatura(corriente):
    """
    Calcula la resistencia VRB a partir de la corriente medida.
    """
    resistencia = (1000 * 0.79932) / corriente * 1000
    return resistencia

def convertir_resistencia_a_temperatura(resistencia):
    """
    Convierte una resistencia medida en temperatura usando una ecuación de transferencia.
    """
    if resistencia > 10e3:
        temperatura = ((-24536.24) + (0.02350289 * resistencia * 100) +
                       (0.000000001034084 * (resistencia * 100) ** 2)) / 100
    else:
        temperatura = ((-24564.58) + (0.02353718 * resistencia * 100) +
                       (0.000000001027502 * (resistencia * 100) ** 2)) / 100
    return temperatura

def temperature(r_scb):
    """
    Calcula la temperatura a partir de la resistencia r_scb usando la ecuación proporcionada.
    """
    a = 3.9083e-3
    b = -5.775e-7
    c = -4.183e-12
    r0 = 10000  # Resistencia base en ohmios

    if r_scb < r0:
        # Resolver ecuación de cuarto grado
        c4 = c * r0
        c3 = -c * r0 * 100
        c2 = b * r0
        c1 = a * r0
        c0 = r0 - r_scb
        coeficientes = [c4, c3, c2, c1, c0]
    else:
        # Resolver ecuación de segundo grado
        c2 = b * r0
        c1 = a * r0
        c0 = r0 - r_scb
        coeficientes = [c2, c1, c0]

    # Encontrar las raíces reales del polinomio
    raices = np.roots(coeficientes)
    raices_reales = [r for r in raices if np.isreal(r)]

    # Retornar la raíz física (temperatura), usualmente la más baja
    return np.real(raices_reales[1]) if raices_reales else None


def rampa_voltaje_e36233a_por_canal(
    amperimetro, voltimetro, fuente, mapeo_sincronizado, directorio_prueba,
    inicio, fin, paso, tiempo_espera, rv=1000, vref=0.79932
):
    """
    Función para enviar una rampa de voltaje a través de cada canal del multiplexor ADG732,
    sincronizando la selección entre MUX1 y MUX2, y midiendo la corriente, voltaje y temperatura.
    Los datos generados se procesan y guardan en la estructura de carpetas especificada.
    """
    if not os.path.exists(directorio_prueba):
        raise ValueError(f"El directorio base {directorio_prueba} no existe. Debe ser creado")

    for switch_mux1, switch_mux2 in mapeo_sincronizado.items():
        tiempo_inicio = time.time()
        voltajes, corrientes, voltajes_scb = [], [], []
        temperaturas_scb, temperaturas_vrb = [], []

        canal_descriptivo = nombre_canal.get(f"{switch_mux1}_{switch_mux2}", f"{switch_mux1}_{switch_mux2}")
        directorio_canal = os.path.join(directorio_prueba, canal_descriptivo)
        os.makedirs(directorio_canal, exist_ok=True)

        seleccionar_entrada(switch_mux1)
        seleccionar_entrada_mux2(switch_mux2)
        print(f"Configurando MUX1 en {switch_mux1} y MUX2 en {switch_mux2}")

        fuente.write("INST:SEL CH1")
        fuente.write(f"VOLT {inicio}")
        fuente.write("OUTP ON")
        voltaje = inicio

        while voltaje <= fin:
            fuente.write(f"VOLT {voltaje}")
            time.sleep(tiempo_espera)

            try:
                corriente = amperimetro.current * 1e6
                voltaje_scb = voltimetro.voltage

                r_scb1 = corriente_a_temperatura(corriente)
                temperatura_vrb_actual = temperature(r_scb1)

                r_pt = rv / ((voltaje_scb / vref) - 1)
                temperatura_scb_actual = temperature(r_pt)

                voltajes.append(voltaje)
                corrientes.append(corriente)
                voltajes_scb.append(voltaje_scb)
                temperaturas_scb.append(temperatura_scb_actual)
                temperaturas_vrb.append(temperatura_vrb_actual)

            except Exception as e:
                print(f"Error al medir corriente o voltaje: {e}")

            voltaje += paso

        tiempo_fin = time.time()
        tiempo_demora = tiempo_fin - tiempo_inicio
        print(f"Tiempo de demora para el canal {switch_mux1}_{switch_mux2}: {tiempo_demora} segundos")

        datos = {
            "voltajes": voltajes,
            "corrientes": corrientes,
            "voltajes_scb": voltajes_scb,
            "temperaturas_scb": temperaturas_scb,
            "temperaturas_vrb": temperaturas_vrb,
            "threshold_temp": temp_threshold,
        }

        procesar_y_guardar_datos(datos, directorio_canal, canal_descriptivo, temp_threshold, directorio_base)

    GPIO.cleanup()


# Ejecución principal
rampa_voltaje_e36233a_por_canal(
    amperimetro, voltimetro, fuente, mapeo_sincronizado, directorio_prueba,
    inicio=3.286, fin=7.586, paso=0.080, tiempo_espera=1.5, rv=1000, vref=0.79932
)
