import asyncio  # Módulo para programación asíncrona en Python
import json  # Biblioteca para codificar y decodificar JSON
from bleak import BleakClient, BleakScanner  # Cliente y escáner BLE
from websockets.asyncio.client import connect  # Cliente WebSocket asíncrono

# UUID BLE del servicio y característica de HR (estándar)
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Filtro de nombre para Polar Verity Sense
DEVICE_NAME_FILTER = "Polar Sense"

# URI del servidor WebSocket de control
CONTROL_SERVER_URI = "ws://localhost:7890"

# Intervalo de suspensión breve para mantener vivo el loop
# Reducirlo acelera la capacidad de manejo de eventos, sin impactar la frecuencia BLE
SLEEP_INTERVAL = 0.1  # en segundos

def parse_heart_rate(data: bytearray):
    flags = data[0]
    hr_format = flags & 0x01
    if hr_format == 0:
        return data[1]
    return int.from_bytes(data[1:3], byteorder='little')

async def main():
    # 1) Buscar el dispositivo BLE por nombre
    print("🔍 Buscando Polar Verity Sense…")
    device = await BleakScanner.find_device_by_filter(
        lambda d, _: d.name and DEVICE_NAME_FILTER in d.name
    )
    if not device:
        print(f"❌ No se encontró ningún dispositivo con '{DEVICE_NAME_FILTER}' en su nombre.")
        return

    # 2) Conexión única WebSocket y mensaje de identificación
    print(f"🌐 Conectando al servidor WebSocket en {CONTROL_SERVER_URI}…")
    ws = await connect(CONTROL_SERVER_URI)
    await ws.send(json.dumps({"type": "HRControl"}))
    print("✅ Enviado mensaje de identificación HRControl")

    # 3) Conexión BLE y suscripción a notificaciones
    async with BleakClient(device) as client:
        print(f"✅ Conectado a {device.name} (BLE)")

        async def ble_handler(sender, data):
            hr = parse_heart_rate(data)
            print(f"HR: {hr} BPM")
            await ws.send(json.dumps({"Heart_Rate": hr}))

        # Iniciar notificaciones HR
        await client.start_notify(HR_CHARACTERISTIC_UUID, ble_handler)
        print("📡 Recibiendo datos y enviando al servidor... Ctrl+C para detener")

        # 4) Mantener el loop vivo con intervalo reducido
        try:
            while True:
                await asyncio.sleep(SLEEP_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Detención solicitada por el usuario.")
        finally:
            # Detener notificaciones y cerrar WS
            await client.stop_notify(HR_CHARACTERISTIC_UUID)
            print("🔌 Desconectado del sensor BLE.")
            await ws.close()
            print("🔌 Conexión WebSocket cerrada.")

if __name__ == "__main__":
    asyncio.run(main())  # Ejecutar la función principal
