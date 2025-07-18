import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_presets_dir() -> str:
    """Return absolute path to the presets folder in ComfyUI root."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    presets_dir = os.path.join(base, "Ollama_presets")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir


def pull_model(ip_port: str, model_name: str) -> bool:
    """Try to download a model via the Ollama API.

    If the model isn't available locally Ollama begins downloading it.  This
    helper shows a simple progress bar similar to the ``ollama`` CLI while the
    files are pulled.  ``True`` is returned on success, ``False`` otherwise.
    """
    import json
    import urllib.request
    from tqdm import tqdm

    url = f"http://{ip_port}/api/pull"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"name": model_name}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    logger.debug(f"pull_model: POST {url} name={model_name}")

    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.getcode()
            if code != 200:
                logger.warning(f"pull_model: HTTP {code} starting pull")
                return False

            totals = {}
            completed = {}
            pbar = tqdm(total=100, unit="%", bar_format="{l_bar}{bar}| {n_fmt}%")

            for raw in resp:
                try:
                    info = json.loads(raw.decode("utf-8"))
                except Exception:
                    continue

                status = info.get("status", "")
                if status == "success":
                    pbar.n = 100
                    pbar.refresh()
                    pbar.close()
                    logger.info("pull_model: download completed")
                    return True

                digest = info.get("digest")
                if digest:
                    if "total" in info:
                        totals[digest] = info["total"]
                    if "completed" in info:
                        completed[digest] = info["completed"]

                    total_sum = sum(totals.values())
                    completed_sum = sum(min(completed.get(d, 0), totals[d]) for d in totals)
                    if total_sum > 0:
                        percent = int(completed_sum * 100 / total_sum)
                        if percent > pbar.n:
                            pbar.update(percent - pbar.n)

                pbar.set_description(status)

            pbar.close()
            logger.warning("pull_model: download did not complete")
            return False

    except Exception as e:
        logger.error(f"pull_model: failed to pull {model_name}: {e}")
        return False


def stop_model(ip_port: str, model_name: str | None = None) -> bool:
    """Send a stop command to the Ollama API to unload the model from memory."""
    import urllib.request
    import json

    url = f"http://{ip_port}/api/stop"
    headers = {"Content-Type": "application/json"}
    payload = {"name": model_name} if model_name else {}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    logger.debug(f"stop_model: POST {url} payload={payload}")
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.getcode()
            logger.info(f"stop_model: HTTP {code}")
            return code == 200
    except Exception as e:
        logger.warning(f"stop_model: failed to stop model: {e}")
        return False
