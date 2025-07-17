# ollama_node_base.py

import urllib.request
import json
import logging

from .utils import pull_model

# Настраиваем логгер для этой ноды
logger = logging.getLogger("OllamaNodeBase")
logger.setLevel(logging.DEBUG)

class OllamaNodeBase:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ip_port":       ("STRING", {"multiline": False}),  # e.g. "localhost:11434"
                "model_name":    ("STRING", {"multiline": False}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt":   ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION     = "call_ollama"
    CATEGORY     = "OllamaComfy"

    def call_ollama(self, ip_port, model_name, system_prompt, user_prompt):
        url = f"http://{ip_port}/v1/chat/completions"
        headers = {
            "Content-Type":  "application/json",
        }
        payload = {
            "model":    model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ]
        }
        data = json.dumps(payload).encode("utf-8")

        pulled = False
        for attempt in range(1, 4):
            logger.info(f"OllamaNodeBase: Attempt {attempt}/3")
            logger.debug(f"OllamaNodeBase: POST {url} (payload {len(data)} bytes)")

            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    status = getattr(resp, "status", resp.getcode())
                    logger.info(f"OllamaNodeBase: HTTP {status}")

                    raw = resp.read().decode("utf-8")
                    logger.debug(f"OllamaNodeBase: Raw response: {raw}")

                    resp_json = json.loads(raw)
                    content = resp_json["choices"][0]["message"]["content"]
                    logger.info(f"OllamaNodeBase: Got content length={len(content)}")
                    return (content,)

            except urllib.error.HTTPError as e:
                err = f"HTTPError {e.code}: {e.reason}"
                logger.warning(f"OllamaNodeBase: {err} on attempt {attempt}")
                if e.code == 404 and not pulled:
                    logger.info("OllamaNodeBase: model not found, pulling...")
                    pulled = pull_model(ip_port, model_name)
                    continue
                if attempt == 3:
                    return (f"Error: {err}",)

            except Exception as e:
                logger.warning(f"OllamaNodeBase: Exception on attempt {attempt}: {e}", exc_info=True)
                if attempt == 3:
                    return (f"Error: {e}",)

        return ("Error: exhausted retries",)

# Регистрация ноды
NODE_CLASS_MAPPINGS = {
    "OllamaNodeBase": OllamaNodeBase
}
