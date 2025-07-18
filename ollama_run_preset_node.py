import os
import json
import urllib.request
import urllib.error
import io
import base64
import logging
from PIL import Image
import numpy as np

from .utils import get_presets_dir, pull_model, stop_model

logger = logging.getLogger("OllamaRunPresetNode")
logger.setLevel(logging.DEBUG)


def _to_pil(img):
    if isinstance(img, Image.Image):
        return img
    if hasattr(img, "cpu"):
        arr = img.cpu().detach().numpy()
    else:
        arr = np.array(img)
    arr = np.squeeze(arr)
    if np.issubdtype(arr.dtype, np.floating):
        arr = (arr * 255).clip(0, 255).astype(np.uint8)
    if arr.ndim == 3 and arr.shape[0] in (1, 3, 4):
        arr = np.transpose(arr, (1, 2, 0))
    if arr.ndim == 3:
        ch = arr.shape[2]
        mode = {1: "L", 3: "RGB", 4: "RGBA"}.get(ch)
        if not mode:
            raise TypeError(f"Unsupported channels: {ch}")
    elif arr.ndim == 2:
        mode = "L"
    else:
        raise TypeError(f"Cannot handle shape: {arr.shape}")
    return Image.fromarray(arr, mode)


class OllamaRunPresetNode:
    CATEGORY = "OllamaComfy"
    NODE_TITLE = "Ollama Run Preset"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "run"

    WRITEABLE = ["ip_port", "preset_name", "model_name", "user_prompt"]
    INPUT_LABELS = {
        "ip_port": "ip_port",
        "preset_name": "preset_name",
        "model_name": "model_name",
        "user_prompt": "user_prompt",
        "img": "img",
    }

    @classmethod
    def INPUT_TYPES(cls):
        preset_dir = get_presets_dir()
        presets = sorted(
            f for f in os.listdir(preset_dir) if f.lower().endswith(".txt")
        ) or ["< no .txt files >"]

        model_path = os.path.join(os.path.dirname(__file__), "list_models.json")
        models = ["< no models >"]
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                models = data
        except Exception as e:
            print(f"[OllamaRunPresetNode] Can't read {model_path}: {e}")

        return {
            "required": {
                "ip_port": ("STRING", {"default": "localhost:11434"}),
                "preset_name": (presets,),
                "model_name": (models,),
                "user_prompt": ("STRING", {"multiline": True, "lines": 5, "default": ""}),
                "keep_in_memory": ("BOOLEAN", {"default": True, "forceInput": False}),
            },
            "optional": {
                "img": ("IMAGE", {}),
            },
        }

    def run(self, ip_port: str, preset_name: str, model_name: str, user_prompt: str, img=None, keep_in_memory=True):
        preset_dir = get_presets_dir()
        path = os.path.join(preset_dir, preset_name)
        system_prompt = ""
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    system_prompt = f.read()
            except Exception as e:
                print(f"[OllamaRunPresetNode] Can't read {path}: {e}")

        url = f"http://{ip_port}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

        if img is not None:
            try:
                pil = _to_pil(img)
            except Exception as e:
                logger.error("Conversion to PIL failed", exc_info=True)
                return (f"Error converting image: {e}",)
            pil.thumbnail((512, 512))
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=75)
            data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ]
            payload = {"model": model_name, "messages": messages, "max_tokens": 1024, "keep_alive": -1 if keep_in_memory else 0}
        else:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "keep_alive": -1 if keep_in_memory else 0,
            }

        body = json.dumps(payload).encode("utf-8")

        pulled = False
        for attempt in range(1, 4):
            logger.info(f"OllamaRunPresetNode: Attempt {attempt}/3")
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["choices"][0]["message"]["content"]
                    logger.info(f"OllamaRunPresetNode: Got content length={len(text)}")
                    if not keep_in_memory:
                        stop_model(ip_port)
                    return (text,)
            except urllib.error.HTTPError as e:
                err = f"HTTPError {e.code}: {e.reason}"
                logger.warning(f"OllamaRunPresetNode: {err} on attempt {attempt}")
                if e.code == 404 and not pulled:
                    logger.info("OllamaRunPresetNode: model not found, pulling...")
                    pulled = pull_model(ip_port, model_name)
                    continue
                if attempt == 3:
                    return (f"Error: {err}",)
            except Exception as e:
                logger.warning(f"OllamaRunPresetNode: Exception on attempt {attempt}: {e}", exc_info=True)
                if attempt == 3:
                    return (f"Error: {e}",)
        return ("Error: exhausted retries",)
