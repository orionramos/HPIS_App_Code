# Importa las bibliotecas necesarias
import asyncio  # Biblioteca para manejar tareas asíncronas
import json  # Biblioteca para manejar datos en formato JSON
import socket
import time  # Biblioteca para medir el tiempo
from websockets.asyncio.server import serve  # Función para crear un servidor WebSocket
import os

# Diccionario para gestionar múltiples clientes conectados
clients = {
    "esp32": None,          # Cliente ESP32, encargado de enviar datos de sensores
    "HPISControl": None,    # Cliente HPISControl, envía datos de actividad
    "Unity_receiver": None, # Cliente Unity, encargado de recibir y mostrar datos en la interfaz
    "HRControl": None
}

# Variables globales que se actualizan con los datos recibidos de los clientes
datos_globales = {
    "EMGA_counter": 0,   # Contador de señales EMG (actividad muscular)
    "EMGB_counter": 0,   # Contador de señales EMG (actividad muscular)
    "Heart_Rate": 0,     # Frecuencia cardíaca
    "actividad": 0,      # Actividad actual seleccionada
    "paso_actividad": 0, # Paso específico dentro de la actividad
    "HRI_strategy": 0,   # Estrategia de interacción humano-robot utilizada
    "GT": 0,             # Mensaje GT que se envía al ESP32
    "tiempo": 0          # Tiempo transcurrido (se actualiza automáticamente)
}

# Variable global para controlar el tiempo desde que se conecta HPISControl
hp_control_start_time = None

# Función asíncrona para enviar datos actualizados a Unity de manera constante.
# Cada vez que se envían, se actualiza la variable "tiempo" en el JSON.
async def enviar_datos_a_unity():
    global hp_control_start_time
    while True:
        # Si HPISControl está conectado, actualiza el tiempo transcurrido
        if hp_control_start_time is not None:
            datos_globales["tiempo"] = time.time() - hp_control_start_time

        if clients["Unity_receiver"]:
            try:
                await clients["Unity_receiver"].send(json.dumps(datos_globales))
                print(f">>> Datos enviados a Unity: {datos_globales}")
            except Exception as e:
                print(f"Error enviando a Unity: {e}")
                clients["Unity_receiver"] = None
        await asyncio.sleep(0.3)

# Función asíncrona para enviar el mensaje GT al ESP32 periódicamente
async def enviar_gt_a_esp32():
    while True:
        if clients["esp32"]:
            try:
                datos_esp32 = {"type": "GT", "GT": datos_globales["GT"]}
                await clients["esp32"].send(json.dumps(datos_esp32))
                print(f">>> GT enviado a ESP32: {datos_esp32}")
            except Exception as e:
                print(f"Error enviando GT a ESP32: {e}")
                clients["esp32"] = None
        await asyncio.sleep(0.5)

# Manejador de cada conexión entrante al servidor WebSocket
async def handler(websocket):
    global hp_control_start_time
    client_type = None
    try:
        # Espera el primer mensaje del cliente con su identificación
        mensaje_inicial = await websocket.recv()
        identificacion = json.loads(mensaje_inicial)
        client_type = identificacion.get("type")

        if client_type in clients:
            clients[client_type] = websocket
            print(f"✅ Cliente conectado: {client_type}")
            # Si se conecta HPISControl, inicia el contador
            if client_type == "HPISControl":
                hp_control_start_time = time.time()
                print("⏱ Inicio del conteo de tiempo para HPISControl")
        else:
            print(f"⚠️ Cliente desconocido conectado: {client_type}")
            await websocket.close()
            return

        while True:
            mensaje = await websocket.recv()
            data = json.loads(mensaje)
            print(f"<<< Mensaje recibido de {client_type}: {data}")

            if client_type == "esp32":
                if list(data.keys())[0] == "EMGA_counter":
                    datos_globales["EMGA_counter"] = data.get("EMGA_counter", 0)
                    print("EMGA_counter: " + str(datos_globales["EMGA_counter"]))
                elif list(data.keys())[0] == "EMGB_counter":
                    datos_globales["EMGB_counter"] = data.get("EMGB_counter", 0)
                    print("EMGB_counter: " + str(datos_globales["EMGB_counter"]))
                else:
                    print("LLAVE DESCONOCIDA!")

            elif client_type == "HRControl":
                datos_globales["Heart_Rate"] = data.get("Heart_Rate", 0)

            elif client_type == "HPISControl":
                message_type = data.get("type")
                # Si HPISControl sigue conectado, actualiza el tiempo
                if hp_control_start_time is not None:
                    datos_globales["tiempo"] = time.time() - hp_control_start_time

                if message_type == "activity-data":
                    datos_globales.update({
                        "actividad": data.get("actividad", 0),
                        "paso_actividad": data.get("paso_actividad", 0),
                        "HRI_strategy": data.get("HRI_strategy", 0),
                        "GT": data.get("GT", 0)
                    })
                    respuesta = {
                        "status": "OK",
                        "mensaje": "Datos de actividad actualizados",
                        "tiempo": datos_globales["tiempo"]
                    }
                elif message_type == "keep-alive":
                    respuesta = {
                        "status": "OK",
                        "mensaje": "Keep-alive recibido",
                        "tiempo": datos_globales["tiempo"]
                    }
                else:
                    respuesta = {
                        "status": "ERROR",
                        "mensaje": "Tipo de mensaje no reconocido",
                        "tiempo": datos_globales["tiempo"]
                    }
                await websocket.send(json.dumps(respuesta))

    except Exception as e:
        print(f"❌ Error con {client_type}: {e}")
    finally:
        print(f"🔌 Cliente desconectado: {client_type}")
        if client_type in clients:
            clients[client_type] = None
        # Si se desconecta HPISControl, detiene el contador y conserva el tiempo final
        if client_type == "HPISControl" and hp_control_start_time is not None:
            tiempo_final = time.time() - hp_control_start_time
            datos_globales["tiempo"] = tiempo_final
            print(f"⏱ Tiempo final para HPISControl: {tiempo_final} segundos")
            hp_control_start_time = None

async def main():
    os.system("ipconfig | findstr /C:\"Wireless LAN adapter Wi-Fi\" /C:\"IPv4 Address\"")
    async with serve(handler, "0.0.0.0", 7890):
        print("🚀 Servidor WebSocket escuchando en el puerto 7890...")
        await asyncio.gather(
            asyncio.Future(),
            enviar_datos_a_unity(),
            enviar_gt_a_esp32()
        )

if __name__ == "__main__":
    asyncio.run(main())
