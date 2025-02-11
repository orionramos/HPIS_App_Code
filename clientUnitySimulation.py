import asyncio  # Biblioteca para manejar operaciones asíncronas
import json  # Biblioteca para manejar datos en formato JSON
from websockets.asyncio.client import connect  # Cliente WebSocket asíncrono

# Función para recibir datos del servidor
async def receive_data():
    """
    Se conecta al servidor WebSocket y recibe datos combinados continuamente.
    """
    uri = "ws://192.168.50.51:7890"  # Dirección del servidor WebSocket
    # uri = "ws://192.168.4.2:7890"  # Dirección del servidor WebSocket
    async with connect(uri) as websocket:  # Establecer conexión con el servidor
        # Enviar mensaje inicial identificando al cliente como receptor
        await websocket.send(json.dumps({"type": "Unity_receiver"}))

        try:
            while True:  # Recibir datos continuamente
                message = await websocket.recv()  # Recibir mensaje del servidor
                data = json.loads(message)  # Convertir el mensaje JSON en un diccionario
                print(f"<<< Received data: {data}")  # Mostrar los datos recibidos
        except Exception as e:
            print(f"Error receiving data: {e}")  # Manejar errores durante la recepción

# Punto de entrada del script
if __name__ == "__main__":
    asyncio.run(receive_data())  # Ejecutar la función de recepción de datos
