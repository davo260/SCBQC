from pymeasure.instruments.agilent import Agilent34450A
import pyvisa
import time
import RPi.GPIO as GPIO
import os
from analisis_datos import procesar_y_guardar_datos
import math
import numpy as np
import sys


if len(sys.argv) !=4:
    sys.exit(1)    
nombre_prueba = sys.argv[1]
directorio_base = sys.argv[2]
temp_threshold = float(sys.argv[3])

directorio_prueba = os.path.join(directorio_base, nombre_prueba)

# Configuración de recursos
rm = pyvisa.ResourceManager()
fuente = rm.open_resource("USB0::10893::13058::MY61004672::0::INSTR")  # Identificador USB fuente E36233A
amperimetro = Agilent34450A("USB0::2391::45848::MY53090070::0::INSTR")  # Amperímetro
voltimetro = Agilent34450A("USB::2391::45848::MY55490094::0::INSTR")  # Voltímetro

# Configuración del amperímetro y voltímetro
amperimetro.nplc = 0.02
amperimetro.configure_current(current_range='AUTO', ac=False, resolution='DEF')
voltimetro.configure_voltage(voltage_range='AUTO', ac=False, resolution='DEF')

# Configuración Canal 2 para salida fija de 12V 
fuente.write('INST:SEL CH2')  # Selecciona el canal 2
fuente.write('VOLT 12')  # Configura el voltaje a 12V en canal 2
fuente.write('CURR 0.1')  # Configura la corriente máxima hasta 0.1
fuente.write('OUTP ON')  # Enciende la fuente

fuente.write('INST:SEL CH1') # Selecciona el canal 1 de la Keysight E3233A

# Configuración GPIO
GPIO.setmode(GPIO.BOARD)
gpio_a_pins = [10, 8, 7, 5, 3]  # Pines A4 a A0 para MUX1
gpio_a_pins_mux2 = [29, 31, 33, 35, 37]  # Pines A4 a A0 para MUX2
gpio_control_pins = [12, 11, 13]  # Pines CS, WR, EN para MUX1
gpio_control_pins_mux2 = [36, 38, 40]  # Pines CS, WR, EN para MUX2

# Configuración de pines como salida
for pin in gpio_a_pins + gpio_control_pins + gpio_a_pins_mux2 + gpio_control_pins_mux2:
    GPIO.setup(pin, GPIO.OUT)

# Inicializar pines de control en bajo
for pin in gpio_control_pins + gpio_control_pins_mux2:
    GPIO.output(pin, GPIO.LOW)

# Mapeos de canales
canal_a_binario = {
    "s3": '00010', "s4": '00011', "s5": '00100', "s6": '00101', "s7": '00110',
    "s8": '00111', "s9": '01000', "s10": '01001', "s11": '01010', "s12": '01011',
    "s13": '01100', "s14": '01101', "s28": '11011', "s27": '11010', "s26": '11001',
    "s25": '11000', "s24": '10111', "s23": '10110', "s22": '10101', "s21": '10100',
    "s20": '10011', "s19": '10010', "s18": '10001', "s17": '10000'
}
canal_a_binario_mux2 = canal_a_binario.copy()

# Mapeo sincronizado y descriptivo de canales
mapeo_sincronizado = {
    "s3": "s17", "s4": "s18", "s5": "s19", "s6": "s20", "s7": "s21",
    "s8": "s22", "s9": "s23", "s10": "s24", "s11": "s25", "s12": "s26",
    "s13": "s27", "s14": "s28", "s28": "s14", "s27": "s13", "s26": "s12",
    "s25": "s11", "s24": "s10", "s23": "s9", "s22": "s8", "s21": "s7",
    "s20": "s6", "s19": "s5", "s18": "s4", "s17": "s3"
}
nombre_canal = {
    "s3_s17": "PTA1", "s4_s18": "PTB1", "s5_s19": "PTA2", "s6_s20": "PTB2",
    "s7_s21": "PTA3", "s8_s22": "PTB3", "s9_s23": "PTA4", "s10_s24": "PTB4",
    "s11_s25": "PTA5", "s12_s26": "PTB5", "s13_s27": "PTA6", "s14_s28": "PTB6",
    "s28_s14": "PTA7", "s27_s13": "PTB7", "s26_s12": "PTA8", "s25_s11": "PTB8",
    "s24_s10": "PTA9", "s23_s9": "PTB9", "s22_s8": "PTA10", "s21_s7": "PTB10",
    "s20_s6": "PTA11", "s19_s5": "PTB11", "s18_s4": "PTA12", "s17_s3": "PTB12"
}

# Funciones de control de MUX y fuente
def seleccionar_entrada(switch):
    valores_a = [int(x) for x in canal_a_binario[switch]]
    for pin, valor in zip(gpio_a_pins, valores_a):
        GPIO.output(pin, valor)

def seleccionar_entrada_mux2(switch):
    valores_a = [int(x) for x in canal_a_binario_mux2[switch]]
    for pin, valor in zip(gpio_a_pins_mux2, valores_a):
        GPIO.output(pin, valor)

def corriente_a_temperatura(I_out):
    R_SCB1 = (1000 * 0.79932) / I_out * 1000  # Ohmios
    return R_SCB1

def convertir_resistencia_a_temperatura(resistencia):
    "funcion de transferencia para resistencia a temperatura desde las notas de las SCB design "
    temperatura = ((-24536.24) + (0.02350289 * resistencia * 100) + (0.000000001034084 * (resistencia * 100) ** 2)) / 100 \
        if resistencia > 10e3 else \
       ((-24564.58) + (0.02353718 * resistencia * 100) + (0.000000001027502 * (resistencia * 100) ** 2)) / 100
    return temperatura



def Temperature(R_SCB):
    """
    Calcula la temperatura a partir de la resistencia R_SCB usando la ecuación proporcionada.
    """
    A = 3.9083E-3
    B = -5.775E-7
    C = -4.183E-12
    R0 = 10000  # Resistencia base en ohmios

    if R_SCB < R0:
        # Resolver ecuación de cuarto grado
        C4 = C * R0
        C3 = -C * R0 * 100
        C2 = B * R0
        C1 = A * R0
        C0 = R0 - R_SCB
        # Resolver el polinomio
        coeficientes = [C4, C3, C2, C1, C0]
    else:
        # Resolver ecuación de segundo grado
        C2 = B * R0
        C1 = A * R0
        C0 = R0 - R_SCB
        # Resolver el polinomio
        coeficientes = [C2, C1, C0]

    # Encontrar las raíces reales del polinomio
    raices = np.roots(coeficientes)
    # Filtrar solo las raíces reales
    raices_reales = [r for r in raices if np.isreal(r)]
    # Retornar la raíz física (temperatura), usualmente la más baja
    return np.real(raices_reales[1]) if raices_reales else None


#def calcular_temperatura_teorica(vin):

    #R_scbt = (59.948)/(12- vin)
    #temperatura_teorica = Temperature(R_scbt) #convertir_resistencia_a_temperatura(1000*R_scbt)
    #return temperatura_teorica

def rampa_voltaje_e36233a_por_canal(amperimetro, voltimetro, fuente, mapeo_sincronizado, directorio_prueba, inicio, fin, paso, tiempo_espera, Rv=1000, Vref=7.9932e-01):
    """
    Función para enviar la rampa de voltaje a través de cada canal del multiplexor ADG732,
    sincronizando la selección entre MUX1 y MUX2, y midiendo la corriente, voltaje y temperatura de salida.
    """
    if not os.path.exists(directorio_prueba):
        raise ValueError(f"El direcotrio base {directorio_prueba} no existe. Debe ser creado")
    for switch_mux1, switch_mux2 in mapeo_sincronizado.items():
        # Inicializar listas para almacenar datos por canal
        voltajes, corrientes, voltajes_scb = [], [], []
        temperatura_scb, temperatura_vrb, temperatura_teorica = [], [], []

        canal_descriptivo = nombre_canal.get(f"{switch_mux1}_{switch_mux2}",f"{switch_mux1}_{switch_mux2}")
        directorio_canal = os.path.join(directorio_prueba, canal_descriptivo)
        if not os.path.exists(directorio_canal):
            os.makedirs(directorio_canal)

        seleccionar_entrada(switch_mux1)  # Configura MUX1
        seleccionar_entrada_mux2(switch_mux2)  # Configura MUX2 de forma sincronizada
        print(f"Configurando MUX1 en {switch_mux1} y MUX2 en {switch_mux2}")

        # Configuración inicial de la fuente
        fuente.write("INST:SEL CH1")
        fuente.write(f"VOLT {inicio}")
        fuente.write("OUTP ON")
        voltaje = inicio

        while voltaje <= fin:
            fuente.write(f"VOLT {voltaje}")
            time.sleep(tiempo_espera)

            try:
                # Lectura de corriente y voltaje
                corriente = amperimetro.current * 1000000
                voltaje_scb = voltimetro.voltage
                
                #temperatura teorica 
                #temp_teorica = calcular_temperatura_teorica(vin=voltaje)

                # Calcular temperatura de VRB
                R_scb1 = corriente_a_temperatura(corriente)
                temperatura_vrb_actual= Temperature(R_scb1)
                     
                # Calcular temperaturas SCB 
                R_pt = Rv / ((voltaje_scb / Vref) - 1)
                temperatura_scb_actual = Temperature(R_pt)#convertir_resistencia_a_temperatura(R_pt)

                    

                # Verificación de valores
                #print(f"Voltaje de salida: {voltaje_salida} V, Resistencia VRB calculada: {R_pt} kohm")

                    
                # Almacenar los datos
                voltajes.append(voltaje)
                corrientes.append(corriente)
                voltajes_scb.append(voltaje_scb)
                temperatura_scb.append(temperatura_scb_actual)
                temperatura_vrb.append(temperatura_vrb_actual)
                #temperatura_teorica.append(temp_teorica)

                # Imprimir la lectura actual
                #print(f"Voltaje: {voltaje} V, Corriente: {corriente} uA, Voltaje de salida: {voltaje_salida} V")
                print(f"Temperatura SCB: {temperatura_scb_actual} °C, Temperatura VRB: {temperatura_vrb_actual} °C, Voltaje SCB: {voltaje_scb}, Corriente: {corriente}")

            except Exception as e:
                    print(f"Error al medir la corriente o voltaje: {e}")

            voltaje += paso

            # Apagar la salida de la fuente al terminar la rampa para este par de switches
            #fuente.write("INST:SEL CH1")
            #fuente.write("OUTP OFF")

        #obtengo el nombre del canal ej: s3_s17 = PTA1   
        

        datos = {

            "voltajes": voltajes,
            "corrientes": corrientes, # type: ignore
            "voltaje_scb": voltajes_scb,
            "temperatura_scb" : temperatura_scb,
            "temperatura_vrb" : temperatura_vrb,
            "threshold_temp" : temp_threshold,
        }

        #print(f"datos para {canal_descriptivo}: {datos}")    
    
        procesar_y_guardar_datos(datos, directorio_canal,canal_descriptivo, temp_threshold)


    GPIO.cleanup()



rampa_voltaje_e36233a_por_canal(amperimetro, voltimetro, fuente, mapeo_sincronizado, directorio_base,  inicio=3.386, fin=7.586, paso=0.076, tiempo_espera=1.5, Rv=1.00e4, Vref=7.9932e-01)
