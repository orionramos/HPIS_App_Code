# Importa las bibliotecas necesarias
import asyncio  # Biblioteca para manejar tareas asíncronas
import json  # Biblioteca para manejar datos en formato JSON
from websockets.asyncio.server import serve  # Importa la función `serve` para crear un servidor WebSocket

# Diccionario para gestionar múltiples clientes conectados
clients = {
    "esp32": None,  # Cliente ESP32, encargado de enviar datos de sensores
    "HPISControl": None,  # Cliente HPISControl, envía datos de actividad
    "Unity_receiver": None,  # Cliente Unity, encargado de recibir y mostrar datos en la interfaz
    "HRControl": None
}

# Variables globales que se actualizan con los datos recibidos de los clientes
datos_globales = {
    "EMG_counter": 0,  # Contador de señales EMG (actividad muscular)
    "Heart_Rate": 0,  # Frecuencia cardíaca
    "actividad": 0,  # Actividad actual seleccionada
    "paso_actividad": 0,  # Paso específico dentro de la actividad
    "HRI_strategy": 0,  # Estrategia de interacción humano-robot utilizada
    "GT": 0  # Mensaje GT que se envía al ESP32
}

# Función asíncrona para enviar datos actualizados a Unity de manera constante
async def enviar_datos_a_unity():
    while True:  # Bucle infinito para mantener el envío de datos activo
        if clients["Unity_receiver"]:  # Verifica si el cliente Unity está conectado
            try:
                # Envía los datos globales en formato JSON a Unity
                await clients["Unity_receiver"].send(json.dumps(datos_globales))
                print(f">>> Datos enviados a Unity: {datos_globales}")
            except Exception as e:
                print(f"Error enviando a Unity: {e}")
                clients["Unity_receiver"] = None  # Si hay error, se desconecta el cliente
        await asyncio.sleep(0.3)  # Pausa de 300 ms antes de enviar nuevamente


# Función asíncrona para enviar el mensaje GT al ESP32 periódicamente
async def enviar_gt_a_esp32():
    while True:  # Bucle infinito para mantener el envío de datos activo
        if clients["esp32"]:  # Verifica si el ESP32 está conectado
            try:
                # Crea un diccionario con el tipo de mensaje y el valor de GT
                datos_esp32 = {"type": "GT", "GT": datos_globales["GT"]}
                await clients["esp32"].send(json.dumps(datos_esp32))  # Envía el mensaje a ESP32
                print(f">>> GT enviado a ESP32: {datos_esp32}")
            except Exception as e:
                print(f"Error enviando GT a ESP32: {e}")
                clients["esp32"] = None  # Si hay error, se desconecta el cliente
        await asyncio.sleep(0.5)  # Pausa de 500 ms antes de enviar nuevamente

# Manejador de cada conexión entrante al servidor WebSocket
async def handler(websocket):
    try:
        # Espera el primer mensaje del cliente con su identificación
        mensaje_inicial = await websocket.recv()
        identificacion = json.loads(mensaje_inicial)  # Convierte el JSON recibido en un diccionario
        client_type = identificacion.get("type")  # Extrae el tipo de cliente

        if client_type in clients:  # Verifica si el tipo de cliente es válido
            clients[client_type] = websocket  # Almacena el WebSocket en el diccionario de clientes
            print(f"✅ Cliente conectado: {client_type}")
        else:
            print(f"⚠️ Cliente desconocido conectado: {client_type}")
            await websocket.close()  # Cierra la conexión si el cliente es desconocido
            return  # Sale de la función

        while True:  # Bucle infinito para recibir y procesar mensajes
            mensaje = await websocket.recv()  # Recibe un mensaje del cliente
            data = json.loads(mensaje)  # Convierte el mensaje JSON en un diccionario
            print(f"<<< Mensaje recibido de {client_type}: {data}")

            # Procesa el mensaje dependiendo del tipo de cliente
            if client_type == "esp32":  
                # Actualiza las variables globales con los datos del ESP32
                datos_globales["EMG_counter"] = data.get("EMG_counter", 0)
    
            elif client_type == "HRControl":
                # Actualiza las variables globales con los datos del HRControl
                datos_globales["Heart_Rate"] = data.get("Heart_Rate", 0)
                
            elif client_type == "HPISControl":  
                message_type = data.get("type")  # Obtiene el tipo de mensaje

                if message_type == "activity-data":  
                    # Si el mensaje es de tipo actividad, actualiza las variables globales
                    datos_globales["actividad"] = data.get("actividad", 0)
                    datos_globales["paso_actividad"] = data.get("paso_actividad", 0)
                    datos_globales["HRI_strategy"] = data.get("HRI_strategy", 0)
                    datos_globales["GT"] = data.get("GT", 0)
                    respuesta = {"status": "OK", "mensaje": "Datos de actividad actualizados"}
                
                elif message_type == "keep-alive":  
                    # Si es un mensaje de keep-alive, solo responde sin actualizar datos
                    respuesta = {"status": "OK", "mensaje": "Keep-alive recibido"}
                
                else:
                    respuesta = {"status": "ERROR", "mensaje": "Tipo de mensaje no reconocido"}

                await websocket.send(json.dumps(respuesta))  # Envía la respuesta al cliente HPISControl
            

    except Exception as e:
        print(f"❌ Error con {client_type}: {e}")  # Captura y muestra cualquier error
    finally:
        print(f"🔌 Cliente desconectado: {client_type}")  # Mensaje cuando un cliente se desconecta
        if client_type in clients:
            clients[client_type] = None  # Elimina la referencia del cliente desconectado

# Función principal del servidor WebSocket
async def main():
    # Inicia el servidor WebSocket en la dirección 0.0.0.0 (todas las interfaces de red) en el puerto 7890
    async with serve(handler, "0.0.0.0", 7890):
        print("🚀 Servidor WebSocket escuchando en el puerto 7890...")
        # Ejecuta en paralelo la función de recepción de conexiones y las de envío de datos
        await asyncio.gather(asyncio.Future(), enviar_datos_a_unity(), enviar_gt_a_esp32())

# Punto de entrada del script
if __name__ == "__main__":
    asyncio.run(main())  # Inicia el servidor WebSocket
