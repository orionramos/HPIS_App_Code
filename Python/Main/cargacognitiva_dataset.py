import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path
from bleak import BleakClient, BleakScanner

HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Estado y parámetros de grabación
records = []
state = "IDLE"
phase_start = None
test_load_id = None
user_id = None

# Carpeta de destino
DATASET_FOLDER = Path("CognitiveLoadDataset")
DATASET_FOLDER.mkdir(exist_ok=True)

def parse_heart_rate(data: bytearray):
    flags = data[0]
    hr_format = flags & 0x01
    if hr_format == 0:
        heart_rate = data[1]
    else:
        heart_rate = int.from_bytes(data[1:3], byteorder='little')
    return heart_rate

def notification_handler(sender, data):
    global state, phase_start, records, test_load_id, user_id
    hr = parse_heart_rate(data)
    now = time.monotonic()
    elapsed = now - phase_start if phase_start else 0
    ts = datetime.now().isoformat(timespec='seconds')

    if state == "RESTING":
        carga = 0
    elif state == "TEST":
        carga = test_load_id
    else:
        return

    records.append({
        'timestamp': ts,
        'elapsed_time': round(elapsed, 2),
        'HR': hr,
        'carga_cognitiva': carga,
        'ID_usuario': user_id
    })
    print(f"[{ts} | {elapsed:6.1f}s] HR: {hr} BPM  | carga_cognitiva: {carga} | ID_usuario: {user_id}")

async def main():
    global state, phase_start, test_load_id, user_id

    # Obtener ID de usuario automáticamente
    all_files = list(DATASET_FOLDER.glob("HR_CG_*_*.csv"))
    user_id = len(all_files) + 1
    print(f"👤 ID de usuario asignado automáticamente: {user_id}")

    # Pedir carga cognitiva
    while True:
        choice = input("Introduce ID de carga cognitiva para la prueba [1–6]: ").strip()
        if choice in ('1', '2', '3', '4', '5', '6'):
            test_load_id = int(choice)
            break
    print(f"\n✔️ La prueba será carga cognitiva {test_load_id}\n")

    print("🔍 Buscando dispositivo Polar Verity Sense...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, _: d.name and "Polar" in d.name
    )
    if not device:
        print("❌ No se encontró un dispositivo Polar.")
        return

    async with BleakClient(device) as client:
        print("✅ Conectado al Polar Verity Sense.")
        await client.start_notify(HR_CHARACTERISTIC_UUID, notification_handler)

        # Fase de reposo
        state = "RESTING"
        phase_start = time.monotonic()
        print("⏺️ Grabando FC en reposo durante 5 minutos (carga = 0)...")
        await asyncio.sleep(60*5)
        print("⏹️ Reposo finalizado.\n")

        # Fase de prueba
        input(f"➡️ Pulsa ENTER para empezar la prueba de carga cognitiva {test_load_id}...")
        state = "TEST"
        phase_start = time.monotonic()
        print(f"⏺️ Grabando prueba (carga = {test_load_id}). Pulsa ENTER para parar.")
        await asyncio.to_thread(input)
        state = "IDLE"
        print("⏹️ Prueba finalizada.\n")

        await client.stop_notify(HR_CHARACTERISTIC_UUID)

    # Guardar CSV con nombre secuencial dentro de la carpeta
    carga_files = list(DATASET_FOLDER.glob(f"HR_CG_{test_load_id}_*.csv"))
    seq = len(carga_files) + 1
    csv_file = DATASET_FOLDER / f"HR_CG_{test_load_id}_{seq}.csv"

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['timestamp', 'elapsed_time', 'HR', 'carga_cognitiva', 'ID_usuario']
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Datos guardados en '{csv_file}' ({len(records)} muestras).")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Finalizado por el usuario.")
