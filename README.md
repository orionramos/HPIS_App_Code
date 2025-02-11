# Proyecto HPIS

Este repositorio contiene los archivos necesarios para la interacción entre un servidor WebSocket, un ESP32 y una aplicación Unity dentro del sistema HPIS.

## Archivos incluidos

### 1. `Controlserver.py`

Este script implementa el servidor WebSocket en Python. Se encarga de recibir datos del ESP32, gestionar la información de la aplicación de control (`HPISControl.py`) y enviar los datos adecuados a la aplicación Unity.

### 2. `HPISControl.py`

Este archivo es el cliente que permite a los usuarios seleccionar un participante, una estrategia de HRI y una actividad. Luego, envía estos datos al servidor WebSocket y gestiona la interacción paso a paso durante la ejecución de la actividad.

### 3. `ClientUnitySimulation.py`

Simula el cliente Unity para recibir datos del servidor WebSocket y visualizar la información procesada.

### 4. `ClienteESP32.py`

Simula el cliente ESP32 enviando datos de frecuencia cardíaca y señales EMG al servidor WebSocket, y recibe la señal GT en respuesta.

### 5. `requirements.txt`

Contiene la lista de bibliotecas necesarias para ejecutar los scripts en este repositorio.

### 6. `install_requirements.py`

Script que instala automáticamente todas las dependencias listadas en `requirements.txt`.

## Instalación y ejecución

### 1. Instalación de dependencias

Antes de ejecutar los scripts, asegúrate de instalar todas las dependencias ejecutando:

con:

```bash
pip install -r requirements.txt
```

### 2. Uso de los scripts

- **Iniciar el servidor WebSocket:**
  ```bash
  python Controlserver.py
  ```
- **Ejecutar la aplicación de control:**
  ```bash
  python HPISControl.py
  ```
- **Simular la conexión de Unity:**
  ```bash
  python ClientUnitySimulation.py
  ```
- **Simular la conexión del ESP32:**
  ```bash
  python ClienteESP32.py
  ```

## Notas adicionales

- Asegúrate de estar conectado a la misma red que el servidor.
- Configura la IP y puerto del servidor WebSocket correctamente en cada cliente si es necesario.
- El ESP32 real debería sustituir al script `ClienteESP32.py` en un entorno de prueba real.

---

**Autor:** Orion
