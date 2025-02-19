import asyncio  # Importa la librería asyncio para manejar tareas asíncronas.
import json  # Permite trabajar con datos en formato JSON.
import random  # Se usa para generar valores aleatorios de EMG y Heart Rate.
from websockets.asyncio.client import connect  # Importa la función para conectar con un servidor WebSocket.

async def send_emg_hr(websocket):
    """
    Envía datos de EMG y frecuencia cardíaca periódicamente al servidor WebSocket.
    """
    try:
        while True:  # Bucle infinito para enviar datos continuamente.
            data = {
                "EMG_counter": random.randint(0, 500),  # Genera un valor aleatorio para EMG (0-500).
                "Heart_Rate": random.randint(0, 205)  # Genera un valor aleatorio para la frecuencia cardíaca (0-205).
            }
            await websocket.send(json.dumps(data))  # Envía los datos convertidos a formato JSON.
            print(f">>> Sent EMG and Heart Rate: {data}")  # Muestra en consola los datos enviados.
    except Exception as e:
        print(f"Error in send_emg_hr: {e}")  # Captura y muestra cualquier error en la comunicación.

async def receive_gt(websocket):
    """
    Recibe datos del servidor y extrae el valor de GT en tiempo real.
    """
    try:
        while True:  # Bucle infinito para recibir datos continuamente.
            response = await websocket.recv()  # Espera la recepción de un mensaje del servidor.
            data = json.loads(response)  # Convierte el mensaje JSON recibido a un diccionario de Python.
            if "GT" in data:  # Verifica si el mensaje contiene la clave "GT".
                print(f"<<< Received GT: {data['GT']}")  # Muestra en consola el valor recibido de GT.
    except Exception as e:
        print(f"Error in receive_gt: {e}")  # Captura y muestra cualquier error en la recepción de datos.

async def main():
    """
    Función principal que establece la conexión WebSocket y ejecuta las tareas de envío y recepción en paralelo.
    """
    uri = "ws://192.168.50.52:7890"  # Dirección del servidor WebSocket.
    async with connect(uri) as websocket:  # Se conecta al servidor WebSocket.
        await websocket.send(json.dumps({"type": "esp32"}))  # Envía un mensaje de identificación como "esp32".
        
        # Ejecuta las funciones de envío y recepción simultáneamente.
        await asyncio.gather(send_emg_hr(websocket), receive_gt(websocket))

if __name__ == "__main__":  # Punto de entrada del script.
    asyncio.run(main())  # Ejecuta la función principal de forma asíncrona.
