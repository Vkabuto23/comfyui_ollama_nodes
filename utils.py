import os


def get_presets_dir() -> str:
    """Return absolute path to the presets folder in ComfyUI root."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    presets_dir = os.path.join(base, "Ollama_presets")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir


def pull_model(ip_port: str, model_name: str) -> bool:
    """Try to download model via Ollama API if it's missing.

    Returns True on success, False otherwise.
    """
    import json
    import urllib.request
    url = f"http://{ip_port}/api/pull"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"name": model_name}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            # HTTP 200 means the pull started successfully
            resp.read()  # drain response
            return resp.getcode() == 200
    except Exception as e:
        print(f"[pull_model] failed to pull {model_name}: {e}")
        return False
