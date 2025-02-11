import asyncio
import json
import random
from websockets.asyncio.client import connect

async def send_emg_hr(websocket):
    """
    Envía datos de EMG y Heart Rate periódicamente.
    """
    try:
        while True:
            data = {
                "EMG_counter": random.randint(0, 500),
                "Heart_Rate": random.randint(0, 205)
            }
            await websocket.send(json.dumps(data))
            print(f">>> Sent EMG and Heart Rate: {data}")
            await asyncio.sleep(1)  # Espera antes del próximo envío
    except Exception as e:
        print(f"Error in send_emg_hr: {e}")

async def receive_gt(websocket):
    """
    Recibe y muestra el valor de GT en tiempo real.
    """
    try:
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if "GT" in data:
                print(f"<<< Received GT: {data['GT']}")  # Mostrar solo GT
    except Exception as e:
        print(f"Error in receive_gt: {e}")

async def main():
    uri = "ws://192.168.50.51:7890"
    async with connect(uri) as websocket:
        await websocket.send(json.dumps({"type": "esp32"}))  # Identificación inicial
        
        # Ejecutar envío y recepción en paralelo
        await asyncio.gather(send_emg_hr(websocket), receive_gt(websocket))

if __name__ == "__main__":
    asyncio.run(main())
