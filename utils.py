import os


def get_presets_dir() -> str:
    """Return absolute path to the presets folder in ComfyUI root."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    presets_dir = os.path.join(base, "prompts")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir
