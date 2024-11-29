# **Automatización del Control de Calidad para Tarjetas de Acondicionamiento de Señal (SCB)**

## **Descripción**
Este proyecto implementa un sistema automatizado para el control de calidad de tarjetas de acondicionamiento de señal (SCB) desarrolladas en el marco del experimento ATLAS en el CERN. La solución emplea una **Raspberry Pi 4** como unidad central de control y combina hardware, software y análisis de datos para garantizar la precisión y confiabilidad de las SCBs.

El sistema automatiza la adquisición de datos, realiza análisis en tiempo real y genera reportes gráficos y métricas clave para cada canal de la tarjeta. Este proyecto es parte de un esfuerzo más amplio para modernizar el monitoreo de calidad en experimentos de alta energía.

---

## **Características Principales**
- **Automatización Completa**: Control de fuentes, multímetros y multiplexores mediante SCPI y GPIO desde la Raspberry Pi 4.
- **Adquisición de Datos Multicanal**: Pruebas simultáneas en múltiples canales de las SCBs.
- **Análisis de Calidad**:
  - Cálculo de métricas como RMS error, desviación estándar, error máximo.
  - Validación de canales según umbrales definidos por el usuario.
- **Interfaz Gráfica (GUI)**: Herramienta desarrollada en Tkinter para gestionar pruebas, visualizar métricas y gráficos en tiempo real.
- **Integración Modular**: Scripts de adquisición, análisis y generación de gráficos diseñados para trabajar de manera independiente.

---

## **Requisitos del Sistema**

### **Hardware**
- Raspberry Pi 4.
- Fuente de alimentación **Keysight E36233A**.
- Multímetros **Agilent 34450A**.
- Multiplexor **ADG732BSUZ**.
- Tarjetas SCB bajo prueba.
- Componentes adicionales:
  - LEDs indicadores.
  - Resistencia de referencia para medición (Rv = 1000 Ω).

### **Software**
- Raspbian OS.
- Python 3.9 o superior.
- Dependencias de Python:
  - `numpy`
  - `matplotlib`
  - `pandas`
  - `tkinter`
  - `pyvisa`
  - `Pillow`
  - `Pymeasure`

Instala las dependencias con:
```bash
pip install -r requirements.txt
```

## **Estructura del proyecto** ##
```
├── VRB/
│   ├── scbqc.py                   # Interfaz gráfica (GUI) para gestionar pruebas.
│   ├── src/
│   │   ├── adquisicion_datos.py   # Script principal para adquisición de datos.
│   │   ├── analisis_datos.py      # Procesamiento y análisis de métricas.
│   │   └── utils.py               # Funciones auxiliares (generación de gráficos, etc.).
│   ├── logos/
│   │   ├── logo_atlas.png         # Logo del experimento ATLAS.
│   │   ├── logo_universidad.png   # Logo de la universidad.
│   ├── pruebas/
│   │   └── [nombre_prueba]/       # Resultados de cada prueba.
│   │       ├── PTA1/              # Datos de cada canal.
│   │       ├── PTA2/
│   │       └── combined_deltas.csv # Archivo combinado de métricas por prueba.
│   ├── README.md                  # Documentación del proyecto.
│   ├── requirements.txt           # Lista de dependencias.
│   └── setup.sh                   # Script para configuración inicial del entorno.
```
## **Uso**

### **1. Ejecución**
1. Enciende la Raspberry Pi y accede al escritorio.
2. Haz doble clic en el archivo `SCB Quality Control.exe` ubicado en el escritorio.
3. En la interfaz gráfica:
   - **Test Name**: Ingresa un nombre para la prueba (por ejemplo, `SCB_Test1`).
   - **Base Directory**: Selecciona o verifica la ruta base para guardar los resultados (por defecto, `/home/pi/Desktop/VRB/pruebas`).
   - **Temperature Threshold**: Ingresa un umbral de temperatura en °C (valor predeterminado: `2.0`).
   - **Channel**: Selecciona un canal para analizar resultados específicos (se llena automáticamente al iniciar la prueba).
4. Haz clic en `Start Acquisition` para iniciar el proceso.

### **2. Resultados**
- Una vez completado, los datos y métricas estarán disponibles en la carpeta:
 ``` /home/pi/Desktop/VRB/pruebas/[nombre_prueba]/```
- Resultados disponibles por canal:
- **Promedio del error**.
- **Error cuadrático medio (RMS)**.
- **Desviación estándar**.
- **Estado de calidad** (`Pass`/`No Pass`).
- Gráficas generadas automáticamente:
- **Temperatura vs Voltaje**.
- **Delta de Temperatura vs Temperatura VRB**.
- **Histograma de Deltas**.

---

## **Ejemplo de Ejecución**
1. Ingresa `SCB_Test1` como nombre de prueba.
2. Verifica o selecciona la ruta base como `/home/pi/Desktop/VRB/pruebas`.
3. Selecciona un umbral de temperatura de `2.0` °C.
4. Haz clic en `Start Acquisition` y observa:
 - Actualización en tiempo real de la tabla de resultados.
 - Gráficas generadas automáticamente en la carpeta de la prueba.

---

## **Contribución**
Si se requiere modificar o actualizar el sistema, sigue estos pasos directamente en la Raspberry Pi:

1. Accede al directorio del proyecto en la Raspberry Pi:
 ```bash
 cd /home/pi/Desktop/VRB
```
2. Accede al directorio del proyecto en la Raspberry Pi:
   - src/adquisicion_datos.py para ajustes en la adquisición.
   - src/analisis_datos.py para cambios en el análisis de métricas.
   - scbqc.py para modificar la interfaz gráfica.
     
3. Ejecuta la interfaz gráfica para probar los cambios:
    ```bash
    python3 scbqc.py
    ```
4. Guardar y documentar los cambios realizados.

## **Autor**
  - **Nombre** : Diego Alejandro Vera Ortega
  - **Correo Electrónico** : dalejandro.vera@javeriana.edu.co
  - **Universidad**: Pontificia Universidad Javeriana
