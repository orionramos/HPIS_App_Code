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
    """Decodifica los datos de ritmo cardíaco del sensor."""
    flags = data[0]
    hr_format = flags & 0x01  # 0: UINT8, 1: UINT16
    if hr_format == 0:
        return data[1]
    return int.from_bytes(data[1:3], byteorder='little')

async def main():
    """Función principal para conectar y leer datos del sensor."""
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
    try:
        ws = await connect(CONTROL_SERVER_URI)
        await ws.send(json.dumps({"type": "HRControl"}))
        print("✅ Enviado mensaje de identificación HRControl")
    except ConnectionRefusedError:
        print(f"❌ Error: La conexión a {CONTROL_SERVER_URI} fue rechazada. ¿Está el servidor WebSocket en ejecución?")
        return
    except Exception as e:
        print(f"❌ Error al conectar con WebSocket: {e}")
        return

    # 3) Conexión BLE, emparejamiento y suscripción a notificaciones
    client = BleakClient(device)
    try:
        print(f"✅ Conectando a {device.name} ({device.address})...")
        await client.connect()
        print(f"✅ Conectado a {device.name}")

        # Intentar emparejar para manejar la notificación de conexión segura de Windows
        print("🔐 Intentando emparejar con el dispositivo...")
        paired = await client.pair()
        if paired:
            print("🤝 Dispositivo emparejado correctamente.")
        else:
            print("⚠️ No se pudo emparejar o ya estaba emparejado.")

        async def ble_handler(sender, data):
            """Callback para manejar las notificaciones BLE."""
            hr = parse_heart_rate(data)
            print(f"❤️ HR: {hr} BPM")
            try:
                await ws.send(json.dumps({"Heart_Rate": hr}))
            except Exception as e:
                print(f"❌ Error al enviar datos por WebSocket: {e}")

        # Iniciar notificaciones HR
        await client.start_notify(HR_CHARACTERISTIC_UUID, ble_handler)
        print("📡 Recibiendo datos y enviando al servidor... (Ctrl+C para detener)")

        # 4) Mantener el loop vivo mientras esté conectado
        while client.is_connected:
            await asyncio.sleep(SLEEP_INTERVAL)
        print("⚠️ El cliente BLE se ha desconectado.")

    except KeyboardInterrupt:
        print("\n🛑 Detención solicitada por el usuario.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")
    finally:
        # Detener notificaciones y cerrar conexiones
        if client.is_connected:
            try:
                await client.stop_notify(HR_CHARACTERISTIC_UUID)
            except Exception as e:
                print(f"⚠️ Error al detener notificaciones: {e}")
            await client.disconnect()
            print("🔌 Desconectado del sensor BLE.")
        if 'ws' in locals() and ws.open:
            await ws.close()
            print("🔌 Conexión WebSocket cerrada.")

if __name__ == "__main__":
    asyncio.run(main())