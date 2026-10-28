import os
import subprocess
import time

import httpx

from app.config import LITELLM_CONFIG_PATH, LITELLM_PORT
from app.logging_config import logger

_proxy_process = None


def start_litellm_proxy(
    config_path: str = LITELLM_CONFIG_PATH,
    port: int = LITELLM_PORT,
    timeout: float = 30.0,
):
    """Launch LiteLLM and wait until its health endpoint confirms readiness."""
    global _proxy_process

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"'{config_path}' not found next to this project. Create it with the agent-pool / "
            f"summary-pool model_list before starting the proxy."
        )

    # Inherit API keys while removing debug settings that can change proxy behavior.
    proxy_env = os.environ.copy()
    proxy_env.pop("DEBUG", None)
    proxy_env["PYTHONUTF8"] = "1"
    proxy_env["PYTHONIOENCODING"] = "utf-8"

    log_file = open("litellm_proxy.log", "w", encoding="utf-8")

    proc = subprocess.Popen(
        ["litellm", "--config", config_path, "--port", str(port)],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=proxy_env,
    )

    # Polling avoids sending model traffic before the proxy has loaded its config.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"LiteLLM proxy process exited early (code {proc.returncode}). "
                f"Check litellm_proxy.log for details."
            )
        try:
            resp = httpx.get(f"http://localhost:{port}/health/liveliness", timeout=2)
            if resp.status_code == 200:
                logger.info("LiteLLM proxy is up at http://localhost:%d", port)
                _proxy_process = proc
                return proc
        except httpx.RequestError:
            pass
        time.sleep(1)

    proc.terminate()
    raise RuntimeError("LiteLLM proxy did not become healthy within the timeout. Check litellm_proxy.log.")


def stop_litellm_proxy() -> None:
    """Terminate only the proxy process created by this application instance."""
    global _proxy_process
    if _proxy_process is not None and _proxy_process.poll() is None:
        _proxy_process.terminate()
        _proxy_process.wait(timeout=10)
        logger.info("LiteLLM proxy stopped.")
        _proxy_process = None
"""Manage the local LiteLLM proxy process used by the LangChain clients."""
