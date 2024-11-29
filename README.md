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
