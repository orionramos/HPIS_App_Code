import json
import os
from gtts import gTTS
import pygame
import time

def cargar_datos(ruta_archivo):
    """
    Carga el archivo JSON y devuelve la estructura de datos en Python.
    """
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def obtener_contenido(data, actividad, estrategia, paso):
    """
    Devuelve el valor de 'content_value' (texto de la instrucción) para la actividad,
    estrategia y paso especificados. 
    
    - actividad, estrategia y paso deben ser cadenas o enteros que correspondan a las claves del JSON.
    """
    try:
        # Asegúrate de convertir los valores a string si en el JSON las claves son strings.
        actividad_str = str(actividad)
        estrategia_str = str(estrategia)
        paso_str = str(paso)
        
        # Navegamos por el diccionario según la jerarquía del JSON
        return data[actividad_str]["strategies"][estrategia_str]["steps"][paso_str]["content_value"]
    except KeyError:
        return "No se encontró la instrucción solicitada."

def crear_audio(texto, nombre_archivo):
    """
    Crea un archivo de audio MP3 a partir de un texto dado utilizando gTTS.
    """
    tts = gTTS(text=texto, lang='es')
    tts.save(nombre_archivo)
    print(f"Audio creado: {nombre_archivo}")

def generar_audios_desde_json(data, output_folder="audios_generados"):
    """
    Genera archivos de audio MP3 para cada texto en el JSON.
    """
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the output folder path relative to the script
    full_output_path = os.path.join(script_dir, output_folder)
    
    os.makedirs(full_output_path, exist_ok=True)  # Crea la carpeta si no existe

    for actividad, info_actividad in data.items():
        for estrategia, info_estrategia in info_actividad["strategies"].items():
            for paso, info_paso in info_estrategia["steps"].items():
                if info_paso["content_type"] == "audio":
                  texto = obtener_contenido(data, actividad, estrategia, paso)
                  nombre_archivo = os.path.join(full_output_path, f"example_audio_{actividad}_{estrategia}_{paso}.mp3")
                  crear_audio(texto, nombre_archivo)

def main():
    # Carga los datos desde el archivo JSON
    # Obtener la ruta absoluta del archivo JSON
    ruta_absoluta = os.path.join(os.path.dirname(__file__), "audio_estrategies.json")
    
    data = cargar_datos(ruta_absoluta)
    
    # Genera los audios para cada paso en el JSON
    generar_audios_desde_json(data)

    print ("audios generados")
if __name__ == "__main__":
    main()
