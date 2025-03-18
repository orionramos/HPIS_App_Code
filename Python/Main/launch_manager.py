import subprocess
import time
import os
import signal

def launch_scripts_in_terminals():
    """
    Lanza cada script en una terminal separada:
    1. WebsocketServer.py
    2. client_data_recorder.py
    3. Espera la señal del usuario para lanzar HPIS_Control.py
    """

    # Define las rutas de los scripts (asegúrate de que sean correctas)
    server_script_path = r"C:\Users\orion.ramos\OneDrive - Universidad del rosario\[02] PhD\[01] HPIS\[01] HPIS Pilot Test\[01] Interfaz\[01] Control Interface\[01] 2025 1S Control Interface Python\[01] Comunications V1\Python\Main\WebsocketServer.py"
    recorder_script_path = r"C:\Users\orion.ramos\OneDrive - Universidad del rosario\[02] PhD\[01] HPIS\[01] HPIS Pilot Test\[01] Interfaz\[01] Control Interface\[01] 2025 1S Control Interface Python\[01] Comunications V1\Python\Main\client_data_recorde.py"
    control_script_path = r"C:\Users\orion.ramos\OneDrive - Universidad del rosario\[02] PhD\[01] HPIS\[01] HPIS Pilot Test\[01] Interfaz\[01] Control Interface\[01] 2025 1S Control Interface Python\[01] Comunications V1\Python\Main\HPIS_Control.py"

    # Verifica que los archivos existan
    if not all(os.path.exists(path) for path in [server_script_path, recorder_script_path, control_script_path]):
        print("Error: Uno o más archivos de script no se encontraron.")
        return

    # --- Lanzar WebsocketServer.py en una terminal ---
    print("Lanzando WebsocketServer.py en una nueva terminal...")
    # Use triple quotes around the script path and the command to handle spaces.
    server_command = f'start cmd /k """python "{server_script_path}" & pause"""'
    server_process = subprocess.Popen(server_command, shell=True)
    print(f"WebsocketServer.py lanzado.")

    # Espera un momento para que el servidor se inicie (ajusta si es necesario)
    time.sleep(3)

    # --- Lanzar client_data_recorder.py en una terminal ---
    print("Lanzando client_data_recorder.py en una nueva terminal...")
    # Use triple quotes around the script path and the command to handle spaces.
    recorder_command = f'start cmd /k """python "{recorder_script_path}" & pause"""'
    recorder_process = subprocess.Popen(recorder_command, shell=True)
    print(f"client_data_recorder.py lanzado.")

    # Espera un momento para que el cliente se conecte al servidor (ajusta si es necesario)
    time.sleep(3)

    # --- Esperar la señal del usuario para lanzar HPIS_Control.py en una terminal ---
    input("Presiona Enter cuando estés listo para lanzar HPIS_Control.py en una nueva terminal...")
    print("Lanzando HPIS_Control.py en una nueva terminal...")
    # Use triple quotes around the script path and the command to handle spaces.
    control_command = f'start cmd /k """python "{control_script_path}" & pause"""'
    control_process = subprocess.Popen(control_command, shell=True)
    print(f"HPIS_Control.py lanzado.")

    # --- Mantener el script principal en ejecución hasta que el usuario decida terminar---
    print("Los scripts están en ejecución. Presiona Ctrl+C para detener el launch manager.")
    print("Para detener cada script, cierra la ventana de su terminal.")

    try:
        while True:
            time.sleep(1)  # Check every second if Ctrl+C is pressed
    except KeyboardInterrupt:
        print("\nDeteniendo el launch manager...")
        print("Para detener cada script, cierra la ventana de su terminal.")
        print("Recuerda cerrar todas las terminales manualmente.")

    print("Launch manager detenido")

if __name__ == "__main__":
    launch_scripts_in_terminals()
