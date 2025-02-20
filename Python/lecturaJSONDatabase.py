import json

def get_feedback(activity_id, strategy_id, step_id, data):
    """Obtiene la retroalimentación basada en actividad, estrategia y paso."""
    try:
        activity = data[str(activity_id)]
        strategy = activity["strategies"][str(strategy_id)]
        step = strategy["steps"][str(step_id)]
        return {
            "activity_name": activity["name"],
            "strategy_name": strategy["name"],
            "content_type": step["content_type"],
            "content_value": step["content_value"]
        }
    except KeyError as e:
        return {"error": f"Clave no encontrada: {e}"}

# Cargar el JSON desde el archivo
with open("Python/feedback_data_named.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Prueba del código
activity_id = 4  # ID de actividad (ejemplo)
strategy_id = 9  # ID de estrategia (ejemplo)
step_id = 4      # ID de paso (ejemplo)

feedback = get_feedback(activity_id, strategy_id, step_id, data)
print(feedback)
