import io
import base64
import json
import urllib.request
import urllib.error
import logging
from PIL import Image
import numpy as np

from .utils import pull_model, stop_model

logger = logging.getLogger("OllamaCompareImageNode")
logger.setLevel(logging.DEBUG)

class OllamaCompareImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ip_port":      ("STRING", {"default": "localhost:11434"}),
                "model_name":   ("STRING", {"multiline": False}),
                "system_prompt":("STRING", {"multiline": True, "default": "You are a vision assistant that compares two images."}),
                "user_prompt":  ("STRING", {"multiline": True, "default": "Compare these two images and describe differences."}),
                "image1":       ("IMAGE", {}),
                "image2":       ("IMAGE", {}),
                "keep_in_memory":("BOOLEAN", {"default": True, "forceInput": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("comparison",)
    FUNCTION = "compare"
    CATEGORY = "OllamaComfy"

    @staticmethod
    def _to_pil(img):
        """Copied from OllamaVisionNodeBase: convert Tensor/ndarray to PIL.Image."""
        if isinstance(img, Image.Image):
            pil = img
        else:
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
            pil = Image.fromarray(arr, mode)
        return pil

    def _to_data_url(self, pil: Image.Image, fmt="JPEG", quality=75):
        """Resize, encode PIL.Image to data URL."""
        pil = pil.copy()
        pil.thumbnail((512, 512))
        buf = io.BytesIO()
        pil.save(buf, format=fmt, quality=quality)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    def compare(self, ip_port, model_name, system_prompt, user_prompt, image1, image2, keep_in_memory=True):
        # Convert both inputs to PIL
        try:
            pil1 = self._to_pil(image1)
            pil2 = self._to_pil(image2)
        except Exception as e:
            logger.error("Image conversion failed", exc_info=True)
            return (f"Error converting images: {e}",)

        # Encode to data URLs
        data_url1 = self._to_data_url(pil1)
        data_url2 = self._to_data_url(pil2)
        logger.debug(f"Data URLs lengths: {len(data_url1)}, {len(data_url2)}")

        # Build messages
        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": data_url1}},
                {"type": "image_url", "image_url": {"url": data_url2}},
            ]},
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "keep_alive": -1 if keep_in_memory else 0,
        }
        body = json.dumps(payload).encode("utf-8")
        url = f"http://{ip_port}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

        pulled = False
        for attempt in range(1, 4):
            logger.info(f"OllamaCompareImageNode: Attempt {attempt}/3")
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    j = json.loads(resp.read().decode("utf-8"))
                    text = j["choices"][0]["message"]["content"].strip()
                    logger.info(f"OllamaCompareImageNode: Got response length={len(text)}")
                    if not keep_in_memory:
                        stopped = stop_model(ip_port, model_name)
                        logger.info(f"OllamaCompareImageNode: stop_model result={stopped}")
                    return (text,)
            except urllib.error.HTTPError as e:
                logger.warning(f"OllamaCompareImageNode: HTTPError {e.code} on attempt {attempt}")
                if e.code == 404 and not pulled:
                    pulled = pull_model(ip_port, model_name)
                    continue
                if attempt == 3:
                    return (f"Error: HTTP {e.code}",)
            except Exception as e:
                logger.warning(f"OllamaCompareImageNode: Exception on attempt {attempt}: {e}", exc_info=True)
                if attempt == 3:
                    return (f"Error: {e}",)
        return ("Error: exhausted retries",)

NODE_CLASS_MAPPINGS = {
    "OllamaCompareImageNode": OllamaCompareImageNode,
}
