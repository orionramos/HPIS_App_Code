# client_data_recorder.py
import asyncio
import json
import csv
import time
from websockets.asyncio.client import connect
import os

class DataRecorder:
    def __init__(self, output_folder="C:/Users/orion.ramos/OneDrive - Universidad del rosario/[02] PhD/[01] HPIS/[01] HPIS Pilot Test/[01] Interfaz/[01] Control Interface/[01] 2025 1S Control Interface Python/[01] Comunications V1/UserData/"):
        self.output_folder = output_folder
        self.is_recording = False
        self.start_time = None
        self.end_time = None
        self.data_buffer = []
        self.last_message_time = None
        self.current_file_path = None # Added: Track the path of the current file
        
        # Create the output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)

    def start_recording(self, user_id, activity_id, strategy_id):
        print("⏱️ Iniciando la grabación de datos...")
        self.is_recording = True
        self.start_time = time.time()
        self.data_buffer = []  # Limpiar el buffer al iniciar
        self.last_message_time = time.time()
        # Generate new file name based on IDs and timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_name = f"user{user_id}_activity{activity_id}_strategy{strategy_id}_{timestamp}.csv"
        self.current_file_path = os.path.join(self.output_folder, file_name)
        print(f"Archivo creado: {self.current_file_path}")
        # Create the new CSV and write the header
        with open(self.current_file_path, "w", newline="") as csvfile:
            fieldnames = [
                "timestamp",
                "EMGA_counter",
                "EMGB_counter",
                "Heart_Rate",
                "actividad",
                "paso_actividad",
                "HRI_strategy",
                "GT",
                "tiempo",
                "UserID",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    def stop_recording(self):
        print("🛑 Deteniendo la grabación de datos...")
        self.is_recording = False
        self.end_time = time.time()
        self.save_data()
        self.current_file_path = None  # Reset the current file path

    def record_data(self, data):
        if self.is_recording:
            timestamp = time.time()
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
                "UserID": data.get("UserID", 0),  # Now it is get from the JSON
            }
            self.data_buffer.append(data_to_save)
            print(f"💾 Datos registrados: {data_to_save}")
            self.last_message_time = time.time() # update last message

    def save_data(self):
        if self.data_buffer and self.current_file_path:
            print(f"📤 Guardando datos en {self.current_file_path}...")
            with open(self.current_file_path, "a", newline="") as csvfile:
                fieldnames = [
                    "timestamp",
                    "EMGA_counter",
                    "EMGB_counter",
                    "Heart_Rate",
                    "actividad",
                    "paso_actividad",
                    "HRI_strategy",
                    "GT",
                    "tiempo",
                    "UserID"
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for row in self.data_buffer:
                    writer.writerow(row)
            print(f"✅ Datos guardados en {self.current_file_path}")
            self.data_buffer = [] #limpiar el buffer luego de guardar

async def client(recorder):
    uri = "ws://localhost:7890"
    # Added: Time in seconds after which the client will assume HPISControl is disconnected
    HPIS_TIMEOUT = 45 

    async with connect(uri) as websocket:
        print("Conectado al servidor WebSocket como Client_Data_Recorder")
        await websocket.send(json.dumps({"type": "Client_Data_Recorder"}))  # Identify
        try:
            while True:
                # Added: Check for timeout
                if recorder.is_recording and time.time() - recorder.last_message_time > HPIS_TIMEOUT:
                    recorder.stop_recording()
                    print(f"🛑 Timeout: No se han recibido datos en {HPIS_TIMEOUT} segundos. Deteniendo la grabación.")
                    
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                except asyncio.TimeoutError:
                    continue  # Go to next iteration of the loop without processing any message
                
                if data["hpi_connected"]:
                    if not recorder.is_recording:
                        user_id = data.get("UserID", "unknown")
                        activity_id = data.get("actividad", "unknown")
                        strategy_id = data.get("HRI_strategy", "unknown")
                        recorder.start_recording(user_id, activity_id, strategy_id)
                        print(f"HPISControl se conecto, inicia la grabacion, User_id: {user_id}, Activity_id: {activity_id}, Strategy_id: {strategy_id}")
                else:
                    if recorder.is_recording:
                        recorder.stop_recording()
                        print("HPISControl se desconecto, detiene la grabacion")
                
                recorder.record_data(data)

        except Exception as e:
            print(f"Error en la comunicación: {e}")
            if recorder.is_recording:
                recorder.stop_recording()

async def main():
    recorder = DataRecorder()
    await client(recorder)

if __name__ == "__main__":
    asyncio.run(main())
