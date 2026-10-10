"""Double-click launcher. Bootstrap uses only the Python standard library."""
import os
import sys

# Conda's Windows extension modules may depend on DLLs outside python.exe's folder.
# Keep the handles alive and do this before importing ssl, sqlite3, pip or the app.
_dll_handles = []
if os.name == "nt":
    _dll_dirs = [os.path.join(sys.base_prefix, name) for name in
                 ("Library/bin", "Library/usr/bin", "Library/mingw-w64/bin", "Scripts", "bin")]
    _dll_dirs = [path for path in _dll_dirs if os.path.isdir(path)]
    for _directory in _dll_dirs:
        if hasattr(os, "add_dll_directory"):
            _dll_handles.append(os.add_dll_directory(_directory))
    os.environ["PATH"] = os.pathsep.join(_dll_dirs + [os.environ.get("PATH", "")])

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import socket
import subprocess
import threading
import time
from contextlib import contextmanager
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener
import webbrowser

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PROJECT_ID = hashlib.sha256(os.path.normcase(str(ROOT)).encode("utf-8")).hexdigest()
SUPPORTED = (3, 9) <= sys.version_info[:2] < (3, 14)


def child_environment():
    environment = os.environ.copy()
    # An activated Conda/Python environment must not override the private venv.
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def run_python(python, *args, capture=False):
    return subprocess.run(
        [str(python), str(Path(__file__).resolve()), *args], cwd=ROOT,
        env=child_environment(), check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        encoding="utf-8", errors="replace",
    )


def verify_dependencies():
    # Check every applicable pin, then import the runtime dependencies. This also
    # catches a venv copied from another machine or broken Conda native DLLs.
    import importlib.metadata
    from packaging.requirements import Requirement
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        if importlib.metadata.version(requirement.name) not in requirement.specifier:
            raise RuntimeError("Dependency needs updating: " + requirement.name)
    import flask
    import flask_sqlalchemy
    import flask_wtf
    import flask_limiter
    import openpyxl
    import sqlite3
    import ssl
    from zoneinfo import ZoneInfo
    ZoneInfo("Asia/Shanghai")


def prepare_environment():
    if VENV_PYTHON.exists():
        try:
            runtime = run_python(VENV_PYTHON, "--runtime-check", capture=True)
        except OSError:
            runtime = None
        if runtime is None or runtime.returncode:
            raise RuntimeError("The existing .venv belongs to an unavailable/incompatible Python. Rename only the .venv folder to .venv.old and double-click again. Keep trade_agent.db, uploads, backups and .secret_key in place.")
    if not VENV_PYTHON.exists():
        print("[1/3] Creating the project's private Python environment...", flush=True)
        # Run venv through this file so Conda DLL setup also applies to bootstrap.
        result = run_python(sys.executable, "--module", "venv", str(VENV))
        if result.returncode:
            raise RuntimeError("Could not create .venv. Check folder write access and the Python installation.")
    result = run_python(VENV_PYTHON, "--verify", capture=True)
    if result.returncode:
        print("[2/3] Installing/updating required packages (first start needs Internet)...", flush=True)
        result = run_python(VENV_PYTHON, "--module", "pip", "install", "--disable-pip-version-check", "-r", str(ROOT / "requirements.txt"))
        if result.returncode:
            raise RuntimeError("Dependency installation failed. Check the pip error above and Internet access, then double-click again.")
        result = run_python(VENV_PYTHON, "--verify", capture=True)
        if result.returncode:
            print(result.stdout, flush=True)
            raise RuntimeError("Python or its native libraries are unavailable. The project data has not been removed.")
    else:
        print("[2/3] All required packages are already available; no download needed.", flush=True)
    result = run_python(VENV_PYTHON, "--module", "pip", "check")
    if result.returncode:
        raise RuntimeError("The private environment contains conflicting packages; see pip check above.")


def running_project(port):
    try:
        # Local readiness probes must not be sent through a company/system proxy.
        opener = build_opener(ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
            data = json.loads(response.read(4096))
            return isinstance(data, dict) and data.get("status") == "ok" and data.get("local_project") == PROJECT_ID
    except (OSError, ValueError, URLError):
        return False


def port_available(port):
    with socket.socket() as probe:
        if os.name == "nt":
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def open_browser_when_ready(port):
    for _ in range(60):
        if running_project(port):
            webbrowser.open(f"http://127.0.0.1:{port}/")
            return
        time.sleep(0.5)
    print("[ERROR] Browser was not opened because the service is not ready. Check the server log above.", flush=True)


@contextmanager
def launcher_lock():
    # Lock stays held while the child server runs. Do not unlink this file: a
    # second launcher must always lock the same file, including during setup.
    with (ROOT / ".launcher.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError("Another launcher for this folder is starting or running. Wait for its window to finish setup, then double-click again.") from None
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def serve(port, no_browser):
    # Explicit local mode; do not require hosting credentials to run a BAT file.
    os.environ["TRADE_ENV"] = "development"
    os.environ["TRADE_TRUST_PROXY"] = "0"
    from app import app, init_db
    from werkzeug.serving import ThreadedWSGIServer

    class LocalServer(ThreadedWSGIServer):
        def server_bind(self):
            if os.name == "nt":
                self.allow_reuse_address = False
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    original_health = app.view_functions["healthz"]

    def local_health():
        result = original_health()
        if isinstance(result, tuple):
            return result
        data = result.get_json()
        data["local_project"] = PROJECT_ID
        return data

    app.view_functions["healthz"] = local_health
    # Reserve the port before migrating/writing any database. Never kill a process
    # that already owns the port, including another copy of this project.
    server = LocalServer("127.0.0.1", port, app)
    try:
        init_db(app)
        app.extensions["start_backups"]()
        print(f"[3/3] Ready: http://127.0.0.1:{port}/", flush=True)
        print(f"Data folder: {app.config['DATA_ROOT']}", flush=True)
        print("Keep this window open. Press Ctrl+C to stop.", flush=True)
        if not no_browser:
            threading.Thread(target=open_browser_when_ready, args=(port,), daemon=True).start()
        server.serve_forever()
    finally:
        server.server_close()


def main():
    if not SUPPORTED:
        print("[ERROR] This project supports Python 3.9 - 3.13. Python 3.12 is not specifically required.")
        return 1
    # Internal subprocess commands all perform the same early Conda DLL setup.
    if sys.argv[1:2] == ["--module"]:
        module, *arguments = sys.argv[2:]
        sys.argv = [module, *arguments]
        runpy.run_module(module, run_name="__main__")
        return 0
    if sys.argv[1:2] == ["--verify"]:
        verify_dependencies()
        return 0
    if sys.argv[1:2] == ["--runtime-check"]:
        import sqlite3
        import ssl
        import venv
        return 0
    parser = argparse.ArgumentParser(description="Trade Agent local launcher")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check", action="store_true", help="prepare dependencies without starting the app")
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    options = parser.parse_args()
    if not 1 <= options.port <= 65535:
        parser.error("port must be between 1 and 65535")
    os.chdir(ROOT)
    if options.serve:
        serve(options.port, options.no_browser)
        return 0
    if not options.check:
        if running_project(options.port):
            print(f"This project is already running: http://127.0.0.1:{options.port}/", flush=True)
            if not options.no_browser:
                webbrowser.open(f"http://127.0.0.1:{options.port}/")
            return 0
        if not port_available(options.port):
            raise RuntimeError(f"Port {options.port} is used by another program. Close that program, or run start.bat --port 5001. No process was stopped.")
    with launcher_lock():
        print(f"Python: {sys.version.split()[0]} ({sys.executable})", flush=True)
        prepare_environment()
        if options.check:
            print("[OK] Local environment is ready.", flush=True)
            return 0
        args = ["--serve", "--port", str(options.port)]
        if options.no_browser:
            args.append("--no-browser")
        return run_python(VENV_PYTHON, *args).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nService stopped.", flush=True)
        raise SystemExit(0)
    except Exception as error:
        print(f"\n[ERROR] {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
