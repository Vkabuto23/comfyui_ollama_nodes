import json
import urllib.request
import urllib.error
import logging
import re

from .utils import pull_model, stop_model

logger = logging.getLogger("OllamaReasoningNode")
logger.setLevel(logging.DEBUG)


class OllamaReasoningNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ip_port": ("STRING", {"multiline": False}),
                "model_name": ("STRING", {"multiline": False}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
                "keep_in_memory": ("BOOLEAN", {"default": True, "forceInput": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("thoughts", "response")
    FUNCTION = "run"
    CATEGORY = "OllamaComfy"

    def _parse_answer(self, text: str):
        thoughts = ""
        response = text
        pattern = re.compile(
            r"(?is)(?:thoughts?|analysis)\s*[:\-]\s*(.*?)\n(?:response|answer|final)\s*[:\-]\s*(.*)"
        )
        m = pattern.search(text)
        if m:
            thoughts = m.group(1).strip()
            response = m.group(2).strip()
        return thoughts, response

    def run(self, ip_port, model_name, system_prompt, user_prompt, keep_in_memory=True):
        url = f"http://{ip_port}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "keep_alive": -1 if keep_in_memory else 0,
        }
        data = json.dumps(payload).encode("utf-8")

        pulled = False
        for attempt in range(1, 4):
            logger.info(f"OllamaReasoningNode: Attempt {attempt}/3")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    raw = resp.read().decode("utf-8")
                    logger.debug(f"OllamaReasoningNode: Raw response: {raw}")
                    j = json.loads(raw)
                    text = j["choices"][0]["message"]["content"]
                    logger.info(f"OllamaReasoningNode: Got content length={len(text)}")
                    if not keep_in_memory:
                        result = stop_model(ip_port, model_name)
                        logger.info(f"OllamaReasoningNode: stop_model result={result}")
                    return self._parse_answer(text)
            except urllib.error.HTTPError as e:
                err = f"HTTPError {e.code}: {e.reason}"
                logger.warning(f"OllamaReasoningNode: {err} on attempt {attempt}")
                if e.code == 404 and not pulled:
                    logger.info("OllamaReasoningNode: model not found, pulling...")
                    pulled = pull_model(ip_port, model_name)
                    continue
                if attempt == 3:
                    return ("", f"Error: {err}")
            except Exception as e:
                logger.warning(f"OllamaReasoningNode: Exception on attempt {attempt}: {e}", exc_info=True)
                if attempt == 3:
                    return ("", f"Error: {e}")
        return ("", "Error: exhausted retries")


NODE_CLASS_MAPPINGS = {
    "OllamaReasoningNode": OllamaReasoningNode,
}
