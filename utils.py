import os


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

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.getcode() != 200:
                print(f"[pull_model] HTTP {resp.getcode()} starting pull")
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
            return False

    except Exception as e:
        print(f"[pull_model] failed to pull {model_name}: {e}")
        return False
