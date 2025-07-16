import json
import os


class OllamaModelNode:
    CATEGORY = "Ollama"
    NODE_TITLE = "Ollama Model"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_name",)
    FUNCTION = "select"

    WRITEABLE = ["model_name"]
    INPUT_LABELS = {"model_name": "model_name"}

    @classmethod
    def INPUT_TYPES(cls):
        path = os.path.join(os.path.dirname(__file__), "list_models.json")
        models = ["< no models >"]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                models = data
        except Exception as e:
            print(f"[OllamaModelNode] Can't read {path}: {e}")
        return {"required": {"model_name": (models,)}}

    def select(self, model_name: str):
        return (model_name,)
