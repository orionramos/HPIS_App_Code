# import asyncio  # Biblioteca para manejar operaciones asíncronas
# import json  # Biblioteca para manejar datos en formato JSON
# import random  # Biblioteca para generar valores aleatorios
# from websockets.asyncio.server import serve  # Servidor WebSocket asíncrono

# # Variables globales para almacenar los datos de EMG y Heart Rate
# esp32_data = {"EMG_counter": 0, "Heart_Rate": 0}  # Inicialmente en 0

# # Función para manejar la recepción de datos de EMG y Heart Rate
# async def receive_esp32(websocket):
#     """
#     Recibe datos de EMG y Heart Rate de un cliente y los almacena globalmente.
#     También envía el dato 'GT' al cliente.
#     """
#     global esp32_data  # Acceso a las variables globales
#     try:
#         async for message in websocket:  # Recibe mensajes continuamente del cliente
#             esp32_data = json.loads(message)  # Convierte el mensaje JSON en un diccionario
#             print(f"<<< Received EMG and Heart Rate: {esp32_data}")  # Muestra los datos recibidos

#             # Generar un valor aleatorio para 'GT' y enviarlo al cliente ESP32
#             gt_data = {"GT": random.randint(1, 10)}  # GT aleatorio (1-10)
#             await websocket.send(json.dumps(gt_data))  # Enviar el dato 'GT'
#             print(f">>> Sent GT: {gt_data}")  # Mostrar el dato enviado
#     except Exception as e:
#         print(f"Error receiving EMG and Heart Rate: {e}")  # Maneja errores en la recepción


# # Función para enviar datos combinados al cliente receptor
# async def send_data(websocket):
#     """
#     Envía datos JSON combinados (aleatorios + EMG y Heart Rate) al cliente receptor.
#     """
#     global esp32_data  # Acceso a las variables globales
#     try:
#         while True:  # Enviar datos continuamente
#             # Generar datos aleatorios para las otras variables
#             data = {
#                 "actividad": random.randint(1, 5),  # Actividad aleatoria (1-5)
#                 "paso_actividad": random.randint(1, 25),  # Paso de la actividad (1-25)
#                 "HRI_strategy": random.randint(1, 6),  # Estrategia HRI (1-6)
#                 "GT": random.randint(1, 10)  # GT aleatorio (1-10)
#             }
#             # Combinar los datos generados con los datos de EMG y Heart Rate
#             data.update(esp32_data)
#             # Convertir el diccionario a JSON y enviarlo al cliente receptor
#             await websocket.send(json.dumps(data))
#             print(f">>> Sent: {data}")  # Muestra los datos enviados
#             await asyncio.sleep(0.2)  # Esperar 1 segundo antes de enviar los siguientes datos
#     except asyncio.CancelledError:
#         print("Client disconnected")  # Maneja desconexiones del cliente

# # Función principal para manejar las conexiones de los clientes
# async def handler(websocket):
#     """
#     Maneja las conexiones de los clientes y distribuye tareas según el tipo de cliente.
#     """
#     print("A client just connected")  # Notifica que un cliente se conectó
#     try:
#         # Recibir el primer mensaje del cliente para identificar su tipo
#         message = await websocket.recv()
#         client_type = json.loads(message).get("type")  # Obtener el tipo de cliente del mensaje

#         if client_type == "esp32":  # Si el cliente es de tipo EMG y Heart Rate
#             await receive_esp32(websocket)  # Llamar a la función para manejar estos datos
#         elif client_type == "Unity_receiver":  # Si el cliente es receptor de datos combinados
#             await send_data(websocket)  # Llamar a la función para enviar los datos
#         else:
#             print("Unknown client type")  # Manejar clientes desconocidos
#     except Exception as e:
#         print(f"Error in handler: {e}")  # Manejar errores en la conexión
#     finally:
#         print("A client just disconnected")  # Notificar desconexión del cliente 

# # Función principal del servidor
# async def main():
#     """
#     Inicia el servidor WebSocket y lo mantiene ejecutándose.
#     """
#     # Crear el servidor WebSocket en localhost y puerto 7890
#     async with serve(handler, "192.168.4.2", 7890):
#     # async with serve(handler, "192.168.4.2", 7890):
#         await asyncio.Future()  # Mantener el servidor en ejecución indefinidamente

# # Punto de entrada del script
# if __name__ == "__main__":
#     asyncio.run(main())  # Ejecutar la función principal del servidor





import asyncio
import json
from websockets.asyncio.server import serve

# Variables globales para almacenar los datos de EMG, frecuencia cardíaca y control de HPIS
esp32_data = {"EMG_counter": 0, "Heart_Rate": 0}
hpis_control_data = {
    "actividad": 0,
    "paso_actividad": 0,
    "HRI_strategy": 0,
    "GT": 0
}

# Función para manejar la recepción de datos de EMG y frecuencia cardíaca desde ESP32
async def receive_esp32(websocket):
    global esp32_data
    try:
        async for message in websocket:
            esp32_data = json.loads(message)
            print(f"<<< Received EMG and Heart Rate: {esp32_data}")

            # Enviar de vuelta el valor de GT actual al ESP32
            gt_data = {"GT": hpis_control_data["GT"]}
            await websocket.send(json.dumps(gt_data))
            print(f">>> Sent GT to ESP32: {gt_data}")
    except Exception as e:
        print(f"Error receiving EMG and Heart Rate: {e}")

# Función para manejar la recepción de datos del cliente HPISControl.py
async def receive_hpis_control(websocket):
    global hpis_control_data
    try:
        async for message in websocket:
            hpis_control_data = json.loads(message)
            print(f"<<< Received HPIS Control Data: {hpis_control_data}")
    except Exception as e:
        print(f"Error receiving HPIS Control Data: {e}")

# Función para enviar datos combinados al cliente receptor (Unity)
async def send_data(websocket):
    global esp32_data, hpis_control_data
    try:
        while True:
            # Combinar los datos de HPISControl y ESP32
            data = {**hpis_control_data, **esp32_data}
            
            await websocket.send(json.dumps(data))
            print(f">>> Sent to Unity: {data}")
            await asyncio.sleep(0.2)
    except asyncio.CancelledError:
        print("Client disconnected")

# Función principal para manejar las conexiones de los clientes
async def handler(websocket):
    print("A client just connected")
    try:
        message = await websocket.recv()
        client_type = json.loads(message).get("type")

        if client_type == "esp32":
            await receive_esp32(websocket)
        elif client_type == "Unity_receiver":
            await send_data(websocket)
        elif client_type == "HPISControl":
            await receive_hpis_control(websocket)
        else:
            print("Unknown client type")
    except Exception as e:
        print(f"Error in handler: {e}")
    finally:
        print("A client just disconnected")

# Función principal del servidor
async def main():
    async with serve(handler, "192.168.50.51", 7890):
        await asyncio.Future()

# Punto de entrada del script
if __name__ == "__main__":
    asyncio.run(main())
