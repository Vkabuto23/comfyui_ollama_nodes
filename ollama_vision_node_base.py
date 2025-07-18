# ollama_vision_node_base.py

import urllib.request
import urllib.error
import json
import io
import base64
import logging

from PIL import Image
import numpy as np

from .utils import pull_model, stop_model

logger = logging.getLogger("OllamaVisionNodeBase")
logger.setLevel(logging.DEBUG)

class OllamaVisionNodeBase:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ip_port":       ("STRING", {"multiline": False}),  # e.g. "localhost:11434"
                "model_name":    ("STRING", {"multiline": False}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt":   ("STRING", {"multiline": True}),
                "keep_in_memory": ("BOOLEAN", {"default": True, "forceInput": False}),
            },
            "optional": {
                "img":        ("IMAGE", {}),
                "max_tokens": ("INT", {"default": 1024}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION     = "call_ollama"
    CATEGORY     = "OllamaComfy"

    @staticmethod
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
            mode = {1:"L",3:"RGB",4:"RGBA"}.get(ch)
            if not mode:
                raise TypeError(f"Unsupported channels: {ch}")
        elif arr.ndim == 2:
            mode = "L"
        else:
            raise TypeError(f"Cannot handle shape: {arr.shape}")
        return Image.fromarray(arr, mode)

    def call_ollama(self, ip_port, model_name, system_prompt, user_prompt, keep_in_memory=True, img=None, max_tokens=1024):
        if img is not None:
            try:
                pil = self._to_pil(img)
            except Exception as e:
                logger.error("Conversion to PIL failed", exc_info=True)
                return (f"Error converting image: {e}",)

            pil.thumbnail((512, 512))
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=75)
            data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
            logger.debug(f"OllamaVisionNodeBase: data_url length={len(data_url)}")

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
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "keep_alive": -1 if keep_in_memory else 0,
        }
        body = json.dumps(payload).encode("utf-8")

        url = f"http://{ip_port}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

        pulled = False
        for attempt in range(1, 4):
            logger.info(f"OllamaVisionNodeBase: Attempt {attempt}/3 (max_tokens={max_tokens})")
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    j = json.loads(resp.read().decode("utf-8"))
                    text = j["choices"][0]["message"]["content"]
                    logger.info(f"OllamaVisionNodeBase: Got content length={len(text)}")
                    if not keep_in_memory:
                        result = stop_model(ip_port, model_name)
                        logger.info(f"OllamaVisionNodeBase: stop_model result={result}")
                    return (text,)
            except urllib.error.HTTPError as e:
                err = f"HTTPError {e.code}: {e.reason}"
                logger.warning(f"OllamaVisionNodeBase: {err} on attempt {attempt}")
                if e.code == 404 and not pulled:
                    logger.info("OllamaVisionNodeBase: model not found, pulling...")
                    pulled = pull_model(ip_port, model_name)
                    continue
                if attempt == 3:
                    return (f"Error: {err}",)
            except Exception as e:
                logger.warning(f"OllamaVisionNodeBase: Exception on attempt {attempt}: {e}", exc_info=True)
                if attempt == 3:
                    return (f"Error: {e}",)
        return ("Error: exhausted retries",)

# Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "OllamaVisionNodeBase": OllamaVisionNodeBase
}
