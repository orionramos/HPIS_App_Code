import asyncio
import json
from websockets.asyncio.client import connect
from aioconsole import ainput  # Input asíncrono para no bloquear el bucle de eventos

class AplicacionHRI:
    def __init__(self):
        self.participante = None
        self.estrategia = None
        self.actividad = None
        self.paso_actividad = 1  # Inicia desde el paso 1
        self.keep_alive_active = True  # Flag para mantener el keep-alive activo

        # Diccionario combinado con información de actividades y valores de GT
        self.actividades = {
            '1': {'pasos': 9, 'gt': {1: 1, 2: 3, 3: 1, 4: 2, 5: 3, 6: 2, 7: 1, 8: 3, 9: 1}},
            '2': {'pasos': 9, 'gt': {1: 2, 2: 1, 3: 4, 4: 3, 5: 2, 6: 3, 7: 1, 8: 2, 9: 4}},
            '3': {'pasos': 9, 'gt': {1: 3, 2: 2, 3: 1, 4: 3, 5: 2, 6: 1, 7: 3, 8: 2, 9: 1}},
            '4': {'pasos': 9, 'gt': {1: 1, 2: 2, 3: 3, 4: 1, 5: 2, 6: 3, 7: 1, 8: 2, 9: 1}},
            '5': {'pasos': 9, 'gt': {1: 2, 2: 3, 3: 1, 4: 2, 5: 3, 6: 1, 7: 2, 8: 3, 9: 1}}
        }

    def seleccionar_participante(self):
        self.participante = input("Ingresa el número de participante a evaluar: ")

    def seleccionar_actividad(self):
        print("Selecciona la actividad a evaluar:")
        print("[1] - Beber líquido")
        print("[2] - Lavarse la cara")
        print("[3] - Preparar una tostada")
        print("[4] - Comer una tostada")
        print("[5] - Vestirse")
        self.actividad = input("Ingresa el número de la actividad (1-5): ")

        while self.actividad not in ['1', '2', '3', '4', '5']:
            print("Selección inválida. Por favor, ingresa un número del 1 al 5.")
            self.actividad = input("Ingresa el número de la actividad (1-5): ")

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

        while self.estrategia not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            print("Selección inválida. Por favor, ingresa un número del 1 al 9.")
            self.estrategia = input("Ingresa el número de la estrategia (1-9): ")

    def obtener_datos(self):
        # Obtener el valor de GT desde el diccionario combinado
        gt_value = self.actividades[self.actividad]['gt'].get(self.paso_actividad, 1)
        return {
            "type": "activity-data",  # Tipo de mensaje para datos de actividad
            "actividad": int(self.actividad),
            "paso_actividad": self.paso_actividad,
            "HRI_strategy": int(self.estrategia),
            "GT": gt_value
        }

    def avanzar_paso(self):
        self.paso_actividad += 1

# Función para enviar keep-alive periódicamente
async def enviar_keep_alive(websocket, app):
    while app.keep_alive_active:
        try:
            # Enviar un mensaje de keep-alive independiente
            await websocket.send(json.dumps({"type": "keep-alive"}))
            print(">>> Keep-alive enviado")
        except Exception as e:
            print(f"Error al enviar keep-alive: {e}")
            break
        await asyncio.sleep(30)  # Cada 30 segundos

# Función asíncrona para enviar datos al servidor WebSocket
async def enviar_datos_al_servidor(app):
    uri = "ws://192.168.50.51:7890"  # Dirección del servidor WebSocket

    async with connect(uri) as websocket:
        await websocket.send(json.dumps({"type": "HPISControl"}))
        print("Conectado al servidor WebSocket como HPISControl.")

        keep_alive_task = asyncio.create_task(enviar_keep_alive(websocket, app))

        try:
            while app.paso_actividad <= app.actividades[app.actividad]['pasos']:
                # Enviar datos de la actividad
                datos = app.obtener_datos()
                await websocket.send(json.dumps(datos))
                print(f">>> Datos enviados: {datos}")

                try:
                    # Esperar respuesta del servidor
                    respuesta = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"<<< Respuesta del servidor: {respuesta}")
                except asyncio.TimeoutError:
                    print("Tiempo de espera agotado. No se recibió respuesta del servidor.")

                # Usar input asíncrono para no bloquear el bucle de eventos
                await ainput("Presiona Enter para continuar al siguiente paso...")
                app.avanzar_paso()

            app.keep_alive_active = False
            await keep_alive_task  # Esperar a que la tarea de keep-alive termine
            print("✅ Actividad completada, cerrando conexión.")
        except Exception as e:
            print(f"Error en la comunicación con el servidor: {e}")
            app.keep_alive_active = False
            await keep_alive_task  # Asegurarse de que la tarea de keep-alive termine

if __name__ == "__main__":
    app = AplicacionHRI()
    app.seleccionar_participante()
    app.seleccionar_actividad()
    app.seleccionar_estrategia()
    asyncio.run(enviar_datos_al_servidor(app))