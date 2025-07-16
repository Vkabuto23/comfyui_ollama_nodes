import os
from .utils import get_presets_dir


class OllamaSavePresetNode:
    CATEGORY = "Ollama"
    NODE_TITLE = "Ollama Save Preset"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("preset_prompt",)
    FUNCTION = "process"

    WRITEABLE = ["prompt", "name", "save_preset"]
    INPUT_LABELS = {
        "prompt": "preset_prompt",
        "name": "preset_name",
        "save_preset": "save_preset",
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "lines": 5, "default": ""}),
                "name": ("STRING", {"default": ""}),
                "save_preset": ("BOOLEAN", {"default": False, "forceInput": False}),
            }
        }

    def process(self, prompt: str, name: str, save_preset: bool):
        if save_preset and name.strip():
            try:
                path = os.path.join(get_presets_dir(), f"{name}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(prompt)
            except Exception as e:
                print(f"[OllamaSavePresetNode] error saving preset: {e}")
        return (prompt,)


class OllamaLoadPresetNode:
    CATEGORY = "Ollama"
    NODE_TITLE = "Ollama Load Preset"
    RETURN_TYPES = ("STRING", "NODE_OVERLAY")
    RETURN_NAMES = ("preset_text", "overlay")
    FUNCTION = "load"
    OUTPUT_NODE = True

    WRITEABLE = ["file_name"]
    INPUT_LABELS = {"file_name": "file_name"}

    @classmethod
    def INPUT_TYPES(cls):
        preset_dir = get_presets_dir()
        files = sorted(
            f for f in os.listdir(preset_dir) if f.lower().endswith(".txt")
        ) or ["< no .txt files >"]
        return {"required": {"file_name": (files,)}}

    def load(self, file_name: str):
        preset_dir = get_presets_dir()
        path = os.path.join(preset_dir, file_name)
        text = ""
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"[OllamaLoadPresetNode] Can't read {path}: {e}")
        overlay = {"text": text, "image": None}
        return (text, overlay)
