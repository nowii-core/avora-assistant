"""Run short Python programs in a separate, resource-limited process.

This is a best-effort sandbox for trusted local use: a fresh temporary directory, an isolated
interpreter, a minimal environment, CPU/memory/file-size limits (POSIX), a hard timeout and a
prelude that disables network and process-spawning helpers. It is not a security boundary against
hostile code; every execution is started by the user or by the agent mode the user switched on.
"""
from __future__ import annotations

import base64
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_CODE_CHARS = 20000
MAX_OUTPUT_CHARS = 8000
MAX_FILES = 6
MAX_FILE_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT = 20
IMAGE_SUFFIXES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}
TEXT_SUFFIXES = {".csv", ".txt", ".json", ".md"}

_PRELUDE = '''import builtins as _b, os as _os, socket as _s, subprocess as _sp
def _deny(*a, **k):
    raise PermissionError("Operazione non consentita nella sandbox di Avora (rete e processi esterni disabilitati).")
for _n in ("socket", "create_connection", "getaddrinfo", "gethostbyname"):
    setattr(_s, _n, _deny)
for _n in ("Popen", "run", "call", "check_call", "check_output"):
    setattr(_sp, _n, _deny)
for _n in ("system", "popen", "execv", "execve", "execvp", "fork", "spawnl", "spawnv", "kill", "remove", "unlink", "rmdir", "rename"):
    if hasattr(_os, _n):
        setattr(_os, _n, _deny)
del _b, _os, _s, _sp
'''


def _limits(timeout: int):
    def apply() -> None:  # pragma: no cover - runs in the child process
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (timeout + 2, timeout + 2))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES * 4, MAX_FILE_BYTES * 4))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        if sys.platform.startswith("linux"):
            resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
        os.setsid()
    return apply


def _clip(text: str) -> str:
    text = text.replace("\x00", "")
    return text if len(text) <= MAX_OUTPUT_CHARS else text[:MAX_OUTPUT_CHARS] + "\n[... output troncato ...]"


def run_python(code: object, timeout: int = DEFAULT_TIMEOUT) -> dict:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Scrivi del codice Python da eseguire.")
    if len(code) > MAX_CODE_CHARS:
        raise ValueError(f"Il codice può contenere al massimo {MAX_CODE_CHARS:,} caratteri.".replace(",", "."))
    timeout = max(1, min(int(timeout), 60))
    workdir = Path(tempfile.mkdtemp(prefix="avora-sandbox-"))
    try:
        (workdir / "main.py").write_text(_PRELUDE + "\n" + code, encoding="utf-8")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(workdir), "MPLBACKEND": "Agg", "MPLCONFIGDIR": str(workdir),
               "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(workdir)}
        kwargs: dict = {}
        if os.name == "posix":
            kwargs["preexec_fn"] = _limits(timeout)
        started = time.monotonic()
        timed_out = False
        process = subprocess.Popen([sys.executable, "-I", "main.py"], cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **kwargs)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except OSError:
                process.kill()
            stdout, stderr = process.communicate()
        files = []
        for path in sorted(workdir.iterdir()):
            if path.name == "main.py" or not path.is_file() or len(files) >= MAX_FILES:
                continue
            suffix = path.suffix.lower()
            if suffix not in IMAGE_SUFFIXES and suffix not in TEXT_SUFFIXES:
                continue
            raw = path.read_bytes()
            if len(raw) > MAX_FILE_BYTES:
                continue
            if suffix in IMAGE_SUFFIXES:
                files.append({"name": path.name, "kind": "image", "mime": IMAGE_SUFFIXES[suffix], "data": base64.b64encode(raw).decode("ascii")})
            else:
                files.append({"name": path.name, "kind": "text", "mime": "text/plain", "text": raw.decode("utf-8", errors="replace")[:6000]})
        stderr = _clip(stderr)
        if "ModuleNotFoundError" in stderr:
            stderr += "\n(Modulo non installato in questo ambiente Python: installalo con pip nell'ambiente di Avora.)"
        return {"ok": process.returncode == 0 and not timed_out, "exit_code": process.returncode, "timed_out": timed_out,
                "stdout": _clip(stdout), "stderr": stderr, "files": files, "seconds": round(time.monotonic() - started, 2)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
