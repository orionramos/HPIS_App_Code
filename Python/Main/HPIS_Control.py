import asyncio  # Librería para manejar programación asíncrona
import json  # Librería para trabajar con datos en formato JSON
from websockets.asyncio.client import connect  # Cliente WebSocket asíncrono
from aioconsole import ainput  # Entrada de usuario asíncrona para no bloquear el bucle de eventos

# Clase que gestiona la aplicación de interacción humano-robot
class AplicacionHRI:
    def __init__(self):
        # Variables de configuración inicial
        self.participante = None  # Número de participante evaluado
        self.estrategia = None  # Estrategia de HRI seleccionada
        self.actividad = None  # Actividad seleccionada
        self.paso_actividad = 1  # El primer paso de la actividad
        self.keep_alive_active = True  # Control para mantener activo el keep-alive
        self.running = True # Flag to control the main loop

      # Diccionario con información de actividades y valores GT y gM por paso
        self.actividades = {
            '1': {'pasos': 5, 'gt': {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}, 'gM': {1:1, 2: 2, 3: 3, 4: 1, 5: 1}},
            '2': {'pasos': 10, 'gt': {1: 1, 2: 1, 3: 1, 4: 4, 5: 4, 6: 4, 7: 1, 8: 3, 9: 3, 10: 3}, 'gM': {1: 1, 2: 1, 3: 1, 4: 4, 5: 4, 6: 4, 7: 1, 8: 3, 9: 3, 10: 3}},
            '3': {'pasos': 11, 'gt': {1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 3, 9: 3 , 10:3, 11:3}, 'gM': {1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 3, 9: 3 , 10:3, 11:3}},
            '4': {'pasos': 7, 'gt': {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}, 'gM': {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}},
            '5': {'pasos': 13, 'gt': {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10:3, 11:3, 12: 3, 13:3}, 'gM': {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10:3, 11:3, 12: 3, 13:3}}
        }
       

    # Método para seleccionar el participante
    def seleccionar_participante(self):
        self.participante = input("Ingresa el número de participante a evaluar: ")

    # Método para seleccionar la actividad de la lista predefinida
    def seleccionar_actividad(self):
        print("Selecciona la actividad a evaluar:")
        print("[1] - Beber líquido")
        print("[2] - Lavarse la cara")
        print("[3] - Preparar una tostada")
        print("[4] - Comer una tostada")
        print("[5] - Vestirse")
        self.actividad = input("Ingresa el número de la actividad (1-5): ")

        # Validación para asegurar que se ingrese una opción válida
        while self.actividad not in ['1', '2', '3', '4', '5']:
            print("Selección inválida. Por favor, ingresa un número del 1 al 5.")
            self.actividad = input("Ingresa el número de la actividad (1-5): ")

    # Método para seleccionar la estrategia de HRI
    def seleccionar_estrategia(self):
        print("Selecciona la estrategia:")
        print("[1] - Estrategia Auditiva 1")
        print("[2] - Estrategia Auditiva 2")
        print("[3] - Estrategia Auditiva 3")
        print("[4] - Estrategia Visual 1")
        print("[5] - Estrategia Visual 2")
        print("[6] - Estrategia Visual 3")
        print("[7] - Estrategia Multimodal 1")
        print("[8] - Estrategia Multimodal 2")
        print("[9] - Estrategia Multimodal 3")
        self.estrategia = input("Ingresa el número de la estrategia (1-9): ")

        # Validación para asegurar que se ingrese una opción válida
        while self.estrategia not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            print("Selección inválida. Por favor, ingresa un número del 1 al 9.")
            self.estrategia = input("Ingresa el número de la estrategia (1-9): ")

    # Método para obtener los datos actuales y enviarlos al servidor
    def obtener_datos(self):
        gt_value = self.actividades[self.actividad]['gt'].get(self.paso_actividad, 1)
        gM_value = self.actividades[self.actividad]['gM'].get(self.paso_actividad, 1)
        return {
            "type": "activity-data",  # Tipo de mensaje
            "actividad": int(self.actividad),
            "paso_actividad": self.paso_actividad,
            "HRI_strategy": int(self.estrategia),
            "GT": int(gt_value),
            "UserID":int(self.participante),
            "GM": int(gM_value)
        }

    # Método para avanzar al siguiente paso de la actividad
    def avanzar_paso(self):
        self.paso_actividad += 1
        if self.paso_actividad > self.actividades[self.actividad]['pasos']:
             self.running = False # set to false when the activity is finished

# Función asíncrona para enviar keep-alive periódicamente
async def enviar_keep_alive(websocket, app):
    while app.keep_alive_active:
        try:
            await websocket.send(json.dumps({"type": "keep-alive"}))  # Enviar mensaje de keep-alive
            print(">>> Keep-alive enviado")
        except Exception as e:
            print(f"Error al enviar keep-alive: {e}")
            break  # Salir del bucle en caso de error
        await asyncio.sleep(30)  # Esperar 30 segundos antes del siguiente envío

# Función asíncrona para conectar con el servidor WebSocket y enviar datos
async def enviar_datos_al_servidor(app):
    uri = "ws://LocalHost:7890"  # Dirección IP del servidor WebSocket

    async with connect(uri) as websocket:  # Establecer conexión WebSocket
        await websocket.send(json.dumps({"type": "HPISControl"}))  # Identificar el cliente
        print("Conectado al servidor WebSocket como HPISControl.")

        keep_alive_task = asyncio.create_task(enviar_keep_alive(websocket, app))  # Iniciar keep-alive

        try:
            while app.running:  # Mientras haya pasos and the app is running
                datos = app.obtener_datos()  # Obtener datos actuales
                await websocket.send(json.dumps(datos))  # Enviar datos
                print(f">>> Datos enviados: {datos}")

                try:
                    respuesta = await asyncio.wait_for(websocket.recv(), timeout=5)  # Esperar respuesta
                    print(f"<<< Respuesta del servidor: {respuesta}")
                except asyncio.TimeoutError:
                    print("Tiempo de espera agotado. No se recibió respuesta del servidor.")

                if app.running:
                    await ainput("Presiona Enter para continuar al siguiente paso...")  # Esperar input del usuario
                    app.avanzar_paso()  # Avanzar al siguiente paso

            print("✅ Actividad completada, cerrando conexión.")

        except Exception as e:
            print(f"Error en la comunicación con el servidor: {e}")

        finally:
            app.keep_alive_active = False  # Detener el keep-alive
            await keep_alive_task  # Asegurar que la tarea de keep-alive finaliza
            await websocket.close() # close websocket
            print("🔌 Conexión cerrada.")

# Punto de entrada principal del programa
if __name__ == "__main__":
    app = AplicacionHRI()  # Crear instancia de la aplicación
    app.seleccionar_participante()  # Seleccionar participante
    app.seleccionar_actividad()  # Seleccionar actividad
    app.seleccionar_estrategia()  # Seleccionar estrategia
    asyncio.run(enviar_datos_al_servidor(app))  # Ejecutar la conexión WebSocket y el envío de datos
