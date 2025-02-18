import websocket
import socket
from websockets.asyncio.client import connect
import _thread
import asyncio  # Biblioteca para manejar operaciones asíncronas
import json  # Biblioteca para manejar datos en formato JSON
import random  # Biblioteca para generar valores aleatorios
import time
import rel

#CONTROL_SERVER_URI = "ws://192.168.50.120:7890"

async def send_hr(hr):
    """
    Envia a frequência cardíaca ao software de controle.
    """
    async with connect(CONTROL_SERVER_URI) as websocket:  # Establecer conexión con el servidor
        # Enviar mensaje inicial identificando al cliente como esp32
        await websocket.send(json.dumps({"type": "HRControl"}))

        data = json.dumps({"Heart_Rate": hr})
        await websocket.send(data)  # Enviar los datos al servidor
        print(f">>> Sent Heart Rate: {data}")  # Mostrar los datos enviados
    
def on_message(ws, message):
    asyncio.run(send_hr(message))
    
def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    global CONTROL_SERVER_URI
    
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    
    CONTROL_SERVER_URI = "ws://" + IPAddr + ":7890"
    
    ws = websocket.WebSocketApp("wss://dev.pulsoid.net/api/v1/data/real_time?access_token=dd1ade8e-28ea-4b9c-8020-b98344c72a1e&response_mode=text_plain_only_heart_rate",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
    