# client_data_recorder.py
import asyncio  # Para programación asíncrona (manejar múltiples tareas al mismo tiempo)
import json  # Para manejar datos en formato JSON
import csv  # Para guardar los datos en archivos CSV
import time  # Para obtener timestamps y medir tiempos
from websockets.asyncio.client import connect  # Para conectarse al servidor WebSocket de forma asíncrona
import os  # Para operaciones del sistema de archivos
from pathlib import Path  # Para manejo de rutas de forma portable

class DataRecorder:
    def __init__(self, output_folder=None):
        # Si no se da una carpeta, usar "UserData" en D:/GitHub/HPIS_App_Code/UserData
        if output_folder is None:
            base_path = Path(__file__).resolve().parents[2]
            output_folder = base_path / "UserData"

        self.output_folder = Path(output_folder)  # Convertir a objeto Path
        self.is_recording = False  # Bandera que indica si se está grabando
        self.start_time = None  # Timestamp de inicio de grabación
        self.end_time = None  # Timestamp de finalización de grabación
        self.data_buffer = []  # Lista que almacena los datos temporalmente antes de guardarlos
        self.last_message_time = None  # Tiempo del último mensaje recibido
        self.current_file_path = None  # Ruta del archivo CSV actual

        # Crear la carpeta de salida si no existe
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def start_recording(self, user_id, activity_id, strategy_id):
        print("[INFO] Iniciando la grabación de datos...")
        self.is_recording = True
        self.start_time = time.time()  # Guardar el tiempo actual como inicio
        self.data_buffer = []  # Limpiar el buffer
        self.last_message_time = time.time()  # Inicializar el tiempo del último mensaje

        # Crear nombre del archivo con formato: user<ID>_activity<ID>_strategy<ID>_YYYYMMDD-HHMMSS.csv
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_name = f"user{user_id}_activity{activity_id}_strategy{strategy_id}_{timestamp}.csv"
        self.current_file_path = self.output_folder / file_name  # Ruta completa al archivo

        print(f"Archivo creado: {self.current_file_path}")

        # Crear el archivo CSV y escribir la cabecera
        with open(self.current_file_path, "w", newline="") as csvfile:
            fieldnames = [
                "timestamp", "EMGA_counter", "EMGB_counter", "Heart_Rate",
                "actividad", "paso_actividad", "HRI_strategy", "GT",
                "tiempo", "UserID"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    def stop_recording(self):
        print("[INFO] Deteniendo la grabación de datos...")
        self.is_recording = False
        self.end_time = time.time()  # Guardar el tiempo de finalización
        self.save_data()  # Guardar los datos acumulados
        self.current_file_path = None

    def record_data(self, data):
        if self.is_recording:
            timestamp = time.time()  # Obtener el timestamp actual
            # Crear un diccionario con los datos
            data_to_save = {
                "timestamp": timestamp,
                "EMGA_counter": data.get("EMGA_counter", 0),
                "EMGB_counter": data.get("EMGB_counter", 0),
                "Heart_Rate": data.get("Heart_Rate", 0),
                "actividad": data.get("actividad", 0),
                "paso_actividad": data.get("paso_actividad", 0),
                "HRI_strategy": data.get("HRI_strategy", 0),
                "GT": data.get("GT", 0),
                "tiempo": data.get("tiempo", 0),
                "UserID": data.get("UserID", 0),
            }
            self.data_buffer.append(data_to_save)  # Guardar en el buffer
            print(f"[DATA] Datos registrados: {data_to_save}")
            self.last_message_time = time.time()  # Actualizar tiempo del último mensaje

    def save_data(self):
        # Guardar los datos en el archivo CSV si hay algo en el buffer
        if self.data_buffer and self.current_file_path:
            print(f"[INFO] Guardando datos en {self.current_file_path}...")
            with open(self.current_file_path, "a", newline="") as csvfile:
                fieldnames = [
                    "timestamp", "EMGA_counter", "EMGB_counter", "Heart_Rate",
                    "actividad", "paso_actividad", "HRI_strategy", "GT",
                    "tiempo", "UserID"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for row in self.data_buffer:
                    writer.writerow(row)
            print(f"[INFO] Datos guardados en {self.current_file_path}")
            self.data_buffer = []  # Limpiar el buffer luego de guardar

async def client(recorder):
    uri = "ws://localhost:7890"  # URL del servidor WebSocket
    HPIS_TIMEOUT = 45  # Tiempo límite sin mensajes antes de detener la grabación

    async with connect(uri) as websocket:
        print("Conectado al servidor WebSocket como Client_Data_Recorder")
        await websocket.send(json.dumps({"type": "Client_Data_Recorder"}))  # Identificarse ante el servidor
        try:
            while True:
                # Verificar si se ha excedido el tiempo límite sin mensajes
                if recorder.is_recording and time.time() - recorder.last_message_time > HPIS_TIMEOUT:
                    recorder.stop_recording()
                    print(f"[WARNING] Timeout: No se han recibido datos en {HPIS_TIMEOUT} segundos.")

                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)  # Esperar mensaje
                    data = json.loads(message)  # Decodificar JSON
                except asyncio.TimeoutError:
                    continue  # Si no hay mensaje, continuar

                # Si HPISControl está conectado
                if data.get("hpi_connected"):
                    if not recorder.is_recording:
                        user_id = data.get("UserID", "unknown")
                        activity_id = data.get("actividad", "unknown")
                        strategy_id = data.get("HRI_strategy", "unknown")
                        recorder.start_recording(user_id, activity_id, strategy_id)
                        print(f"[INFO] HPISControl conectado. Grabando datos de User_id: {user_id}, Activity_id: {activity_id}, Strategy_id: {strategy_id}")
                else:
                    if recorder.is_recording:
                        recorder.stop_recording()
                        print("[INFO] HPISControl desconectado. Grabación detenida.")

                recorder.record_data(data)

        except Exception as e:
            print(f"[ERROR] Error en la comunicación: {e}")
            if recorder.is_recording:
                recorder.stop_recording()

async def main():
    recorder = DataRecorder()  # Crear instancia del grabador
    await client(recorder)  # Ejecutar cliente WebSocket

if __name__ == "__main__":
    asyncio.run(main())  # Ejecutar el programa principal
