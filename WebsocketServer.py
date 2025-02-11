import asyncio
import json
from websockets.asyncio.server import serve

# Diccionario para gestionar múltiples clientes conectados
clients = {
    "esp32": None,
    "HPISControl": None,
    "Unity_receiver": None
}

# Variables globales que se actualizan con los datos recibidos
datos_globales = {
    "EMG_counter": 0,
    "Heart_Rate": 0,
    "actividad": 0,
    "paso_actividad": 0,
    "HRI_strategy": 0,
    "GT": 0
}

# Función para enviar datos actualizados a Unity constantemente
async def enviar_datos_a_unity():
    while True:
        if clients["Unity_receiver"]:
            try:
                await clients["Unity_receiver"].send(json.dumps(datos_globales))
                print(f">>> Datos enviados a Unity: {datos_globales}")
            except Exception as e:
                print(f"Error enviando a Unity: {e}")
                clients["Unity_receiver"] = None
        await asyncio.sleep(1)

# Función para enviar GT a ESP32 periódicamente
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
        await asyncio.sleep(1)

# Manejador de cada conexión entrante
async def handler(websocket):
    try:
        mensaje_inicial = await websocket.recv()
        identificacion = json.loads(mensaje_inicial)
        client_type = identificacion.get("type")

        if client_type in clients:
            clients[client_type] = websocket
            print(f"✅ Cliente conectado: {client_type}")
        else:
            print(f"⚠️ Cliente desconocido conectado: {client_type}")
            await websocket.close()
            return

        while True:
            mensaje = await websocket.recv()
            data = json.loads(mensaje)
            print(f"<<< Mensaje recibido de {client_type}: {data}")

            # Procesar el mensaje según su tipo
            if client_type == "esp32":
                datos_globales["EMG_counter"] = data.get("EMG_counter", 0)
                datos_globales["Heart_Rate"] = data.get("Heart_Rate", 0)

            elif client_type == "HPISControl":
                message_type = data.get("type")

                if message_type == "activity-data":
                    # Actualizar variables globales solo si es un mensaje de actividad
                    datos_globales["actividad"] = data.get("actividad", 0)
                    datos_globales["paso_actividad"] = data.get("paso_actividad", 0)
                    datos_globales["HRI_strategy"] = data.get("HRI_strategy", 0)
                    datos_globales["GT"] = data.get("GT", 0)
                    respuesta = {"status": "OK", "mensaje": "Datos de actividad actualizados"}
                elif message_type == "keep-alive":
                    # No actualizar variables globales, solo responder al keep-alive
                    respuesta = {"status": "OK", "mensaje": "Keep-alive recibido"}
                else:
                    respuesta = {"status": "ERROR", "mensaje": "Tipo de mensaje no reconocido"}

                await websocket.send(json.dumps(respuesta))

    except Exception as e:
        print(f"❌ Error con {client_type}: {e}")
    finally:
        print(f"🔌 Cliente desconectado: {client_type}")
        if client_type in clients:
            clients[client_type] = None

# Función principal del servidor
async def main():
    async with serve(handler, "0.0.0.0", 7890):
        print("🚀 Servidor WebSocket escuchando en el puerto 7890...")
        await asyncio.gather(asyncio.Future(), enviar_datos_a_unity(), enviar_gt_a_esp32())

# Ejecutar el servidor
if __name__ == "__main__":
    asyncio.run(main())