import asyncio  # Librería para manejar programación asíncrona
import json  # Librería para trabajar con datos en formato JSON
import signal  # Para capturar Ctrl+C
from websockets.asyncio.client import connect  # Cliente WebSocket asíncrono

# Variable global para controlar la interrupción
interrupted_event = None

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
            '1': {'pasos': 6, 
                'gt': {1:1, 2:1, 3:1, 4:1, 5:1, 6:1}, 
                'gM': {1:1, 2:1, 3:1, 4:1, 5:1, 6:1}},
            
            '2': {'pasos': 12, 
                'gt': {1:1, 2:1, 3:1, 4:1, 5:4, 6:1, 7:1, 8:1, 9:3, 10:3, 11:3, 12:3}, 
                'gM': {1:2, 2:2, 3:2, 4:2, 5:2, 6:2, 7:2, 8:2, 9:2, 10:2, 11:2, 12:2}},
            
            '3': {'pasos': 13, 
                'gt': {1:4, 2:4, 3:4, 4:4, 5:4, 6:4, 7:5, 8:3, 9:3, 10:3, 11:3, 12:3, 13:3}, 
                'gM': {1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:2, 8:2, 9:2, 10:2, 11:2, 12:2, 13:2}},
            
            '4': {'pasos': 6,
                'gt': {1:1, 2:1, 3:1, 4:1, 5:1, 6:1},
                'gM': {1:1, 2:1, 3:1, 4:1, 5:1, 6:1}},
            
            '5': {'pasos': 9, 
                'gt': {1:3, 2:3, 3:3, 4:3, 5:3, 6:3, 7:3, 8:3, 9:3}, 
                'gM': {1:2, 2:2, 3:2, 4:2, 5:2, 6:2, 7:2, 8:2, 9:2}}
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

    # Nuevo método para obtener datos de finalización
    def obtener_datos_fin(self):
        """Retorna un mensaje de finalización que señala a Unity que limpie todo el feedback"""
        return {
            "type": "activity-data",
            "actividad": 0,
            "paso_actividad": 0,
            "HRI_strategy": 0,
            "EMGA_counter": 0,
            "EMGB_counter": 0,
            "EMGTotal_counter": 0,
            "Heart_Rate": 0,
            "GT": 0,
            "UserID": int(self.participante),
            "GM": 0,
            "tiempo": 0
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
async def enviar_datos_al_servidor(app, websocket_holder):
    uri = "ws://LocalHost:7890"  # Dirección IP del servidor WebSocket
    websocket = None
    keep_alive_task = None

    try:
        websocket = await connect(uri)  # Establecer conexión WebSocket
        websocket_holder['ws'] = websocket  # Guardar referencia para el signal handler
        await websocket.send(json.dumps({"type": "HPISControl"}))  # Identificar el cliente
        print("Conectado al servidor WebSocket como HPISControl.")

        keep_alive_task = asyncio.create_task(enviar_keep_alive(websocket, app))  # Iniciar keep-alive

        while app.running:  # Mientras haya pasos and the app is running
            # Chequear si hubo interrupción
            if interrupted_event.is_set():
                print("\n⚠️ Interrupción detectada (Ctrl+C).")
                break

            datos = app.obtener_datos()  # Obtener datos actuales
            
            try:
                await websocket.send(json.dumps(datos))  # Enviar datos
                print(f">>> Datos enviados: {datos}")
            except Exception as e:
                print(f"❌ Error enviando datos: {e}")
                break

            try:
                respuesta = await asyncio.wait_for(websocket.recv(), timeout=5)  # Esperar respuesta
                print(f"<<< Respuesta del servidor: {respuesta}")
            except asyncio.TimeoutError:
                print("Tiempo de espera agotado. No se recibió respuesta del servidor.")

            if app.running and not interrupted_event.is_set():
                try:
                    # Esperar input o interrupción - máximo 30 segundos
                    print("Presiona Enter para continuar al siguiente paso (o Ctrl+C para salir)...\n")
                    
                    # Crear tarea para input
                    input_task = asyncio.create_task(asyncio.to_thread(input))
                    interrupt_task = asyncio.create_task(interrupted_event.wait())
                    
                    # Esperar a que termine uno u otro
                    done, pending = await asyncio.wait(
                        [input_task, interrupt_task],
                        timeout=30.0,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancelar tareas pendientes
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                        except EOFError:
                            pass
                    
                    # Si fue la interrupción, salir
                    if interrupt_task in done:
                        break
                    
                    # Si fue el input, avanzar
                    if input_task in done:
                        try:
                            input_task.result()
                            app.avanzar_paso()
                        except Exception:
                            app.avanzar_paso()
                    else:
                        # Timeout
                        print("(Avanzando automáticamente por timeout)")
                        app.avanzar_paso()
                        
                except Exception as e:
                    print(f"Error en input: {e}")
                    app.avanzar_paso()

        # Enviar señal de fin cuando se termina o se interrumpe
        print("\n✅ Enviando señal de fin a Unity...")
        if websocket:
            try:
                datos_fin = app.obtener_datos_fin()
                print(f">>> Datos fin: {datos_fin}")
                await websocket.send(json.dumps(datos_fin))
                print("✅ Señal de fin enviada a Unity")
                await asyncio.sleep(0.5)  # Dar tiempo para que se procese
            except Exception as e:
                print(f"❌ Error enviando señal: {e}")

    except Exception as e:
        print(f"❌ Error en la comunicación: {e}")

    finally:
        print("\nLimpiando recursos...")
        app.keep_alive_active = False  # Detener el keep-alive
        if keep_alive_task:
            try:
                keep_alive_task.cancel()
                await keep_alive_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        if websocket:
            try:
                await websocket.close()
            except Exception:
                pass
        print("🔌 Conexión cerrada.")


# Handler para Ctrl+C
def handle_sigint(signum, frame):
    """Maneja la señal SIGINT (Ctrl+C)"""
    global interrupted_event
    if interrupted_event:
        print("\n⚠️ Señal de Ctrl+C recibida")
        interrupted_event.set()  # Setear el evento

# Punto de entrada principal del programa
if __name__ == "__main__":
    import sys
    
    app = AplicacionHRI()  # Crear instancia de la aplicación
    app.seleccionar_participante()  # Seleccionar participante
    app.seleccionar_actividad()  # Seleccionar actividad
    app.seleccionar_estrategia()  # Seleccionar estrategia
    
    # Inicializar el evento de interrupción
    interrupted_event = asyncio.Event()
    
    # Registrar el signal handler para Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
    websocket_holder = {'ws': None}
    
    try:
        asyncio.run(enviar_datos_al_servidor(app, websocket_holder))  # Ejecutar la conexión WebSocket y el envío de datos
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrumpido por el usuario.")
    except Exception as e:
        print(f"\n\n❌ Error en el programa: {e}")
