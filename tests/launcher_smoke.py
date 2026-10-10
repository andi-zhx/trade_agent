"""Exercise a fresh local launcher and real HTTP workflow without touching user data.

Run explicitly with ``python tests/launcher_smoke.py``. The first launch installs
dependencies into a temporary project; Windows executes the actual Chinese BAT.
"""
from contextlib import closing
from http.cookiejar import CookieJar
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener
import uuid


SOURCE = Path(__file__).resolve().parents[1]
COMPANY = "双击启动测试企业"
PRODUCT = "重启后仍存在的产品"
ATTACHMENT = "原始企业资料：重启后仍可下载。".encode("utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def copy_project(destination):
    destination.mkdir()
    # An allowlist deliberately excludes existing databases, credentials, uploads,
    # backups, virtual environments and Git configuration from the user's checkout.
    for pattern in ("*.py", "*.bat", "requirements.txt"):
        for source in SOURCE.glob(pattern):
            shutil.copy2(source, destination / source.name)
    for directory in ("config", "utils", "templates", "static"):
        shutil.copytree(SOURCE / directory, destination / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    require(not (destination / "trade_agent.db").exists(), "Copied a user database")
    require(not (destination / ".secret_key").exists(), "Copied a user secret")
    for name in ("start.bat", "启动企业库系统.bat"):
        content = (destination / name).read_bytes()
        content.decode("ascii")
        require(b"\r\n" in content and b"\n" not in content.replace(b"\r\n", b""),
                name + " must use CRLF line endings")


def clean_environment(offline=False):
    environment = os.environ.copy()
    for name in list(environment):
        if name.startswith("TRADE_") or name in {"PYTHONHOME", "PYTHONPATH"}:
            environment.pop(name)
    environment.update(TRADE_LAUNCHER_NO_PAUSE="1", PYTHONUTF8="1",
                       PYTHONIOENCODING="utf-8", PIP_DISABLE_PIP_VERSION_CHECK="1")
    environment["TRADE_PYTHON"] = environment.get("SMOKE_BOOTSTRAP_PYTHON", sys.executable)
    if offline:
        environment["PIP_NO_INDEX"] = "1"
    return environment


def launch(project, port, log, offline=False):
    if os.name == "nt":
        # Pass a command-line string so cmd receives its required outer quotes
        # literally, including when the BAT's path contains spaces and '&'.
        cmd = subprocess.list2cmdline([os.environ.get("COMSPEC", "cmd.exe")])
        command = cmd + ' /d /s /c ""{}" --no-browser --port {}"'.format(
            project / "启动企业库系统.bat", port)
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        command = [os.getenv("SMOKE_BOOTSTRAP_PYTHON", sys.executable), str(project / "launch_local.py"),
                   "--no-browser", "--port", str(port)]
        options = {"start_new_session": True}
    # Deliberately start outside the project to verify launcher path resolution.
    with log.open("wb") as output:
        return subprocess.Popen(command, cwd=project.parent, env=clean_environment(offline),
                                stdout=output, stderr=subprocess.STDOUT, **options)


def stop(process):
    if os.name == "nt":
        if process.poll() is None:
            # This PID belongs only to a launcher created by this test. Never
            # search by executable name or terminate the process owning a port.
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=10)


def request(client, base, path, fields=None, attachment=False):
    headers = {}
    data = None
    if fields is not None:
        if attachment:
            boundary = "smoke-" + uuid.uuid4().hex
            parts = []
            for name, value in fields.items():
                parts.append(('--' + boundary + '\r\nContent-Disposition: form-data; '
                              'name="' + name + '"\r\n\r\n' + str(value) + '\r\n').encode("utf-8"))
            parts.extend([('--' + boundary + '\r\nContent-Disposition: form-data; '
                           'name="attachments"; filename="proof.txt"\r\n'
                           'Content-Type: text/plain\r\n\r\n').encode("ascii"), ATTACHMENT,
                          ('\r\n--' + boundary + '--\r\n').encode("ascii")])
            data = b"".join(parts)
            headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        else:
            data = urlencode(fields).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    with client.open(Request(base + quote(path, safe="/?=&%#"), data=data, headers=headers),
                     timeout=10) as response:
        require(response.status == 200, "Unexpected HTTP status: " + str(response.status))
        return response.read(), response.url


def field(page, name):
    match = re.search(r'name="' + re.escape(name) + r'" value="([^"]+)"', page.decode("utf-8"))
    require(match, "Missing form field: " + name)
    return match.group(1)


def wait_ready(process, base, timeout=300):
    client = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        require(process.poll() is None, "Launcher exited before the service became ready")
        try:
            body, _ = request(client, base, "/healthz")
            health = json.loads(body)
            if health.get("status") == "ok" and health.get("local_project"):
                return
        except (OSError, URLError, ValueError):
            pass
        time.sleep(0.3)
    raise AssertionError("Local service did not become ready within {} seconds".format(timeout))


def saved_workflow(client, base):
    page, _ = request(client, base, "/登录")
    request(client, base, "/登录", {"csrf_token": field(page, "csrf_token"),
                                      "用户名": "admin", "密码": "admin123"})
    page, _ = request(client, base, "/library/enterprises/new")
    page, url = request(client, base, "/library/enterprises/new", {
        "csrf_token": field(page, "csrf_token"), "submission_key": field(page, "submission_key"),
        "company_name": COMPANY, "primary_contact_name": "张女士",
    }, attachment=True)
    match = re.fullmatch(r"/library/enterprises/(\d+)", urlsplit(url).path)
    require(match, "Enterprise was not saved: " + url)
    enterprise_id = match.group(1)
    attachment_match = re.search(rb'href="(/documents/\d+/download)"', page)
    require(attachment_match, "Saved attachment has no download link")
    attachment_path = attachment_match.group(1).decode("ascii")
    page, _ = request(client, base, "/library/products/new?enterprise_id=" + enterprise_id)
    page, _ = request(client, base, "/library/products/new", {
        "csrf_token": field(page, "csrf_token"), "submission_key": field(page, "submission_key"),
        "enterprise_id": enterprise_id, "product_name_cn": PRODUCT, "model": "规格 A",
    })
    require(PRODUCT.encode("utf-8") in page, "Saved product is missing from enterprise detail")
    check_saved(client, base, attachment_path)
    return attachment_path


def check_saved(client, base, attachment_path):
    enterprises, _ = request(client, base, "/library")
    require(COMPANY.encode("utf-8") in enterprises, "Enterprise disappeared or login session failed")
    require("更新于".encode("utf-8") in enterprises, "Local timezone/date rendering failed")
    products, _ = request(client, base, "/library/products")
    require(PRODUCT.encode("utf-8") in products, "Product disappeared")
    attachment, _ = request(client, base, attachment_path)
    require(attachment == ATTACHMENT, "Attachment changed or disappeared")


class OtherService(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","service":"unrelated"}')

    def log_message(self, *_args):
        pass


def run_smoke(root):
    project = root / "中文 路径 & (BAT test)"
    copy_project(project)
    with socket.socket() as socket_probe:
        socket_probe.bind(("127.0.0.1", 0))
        port = socket_probe.getsockname()[1]
    base = "http://127.0.0.1:" + str(port)
    processes = []
    try:
        print("[smoke] Fresh launch and dependency installation", flush=True)
        first = launch(project, port, root / "first-launch.log")
        processes.append(first)
        wait_ready(first, base)
        if os.environ.get("SMOKE_BOOTSTRAP_PYTHON"):
            output = (root / "first-launch.log").read_text(encoding="utf-8", errors="replace")
            require(os.environ["SMOKE_BOOTSTRAP_PYTHON"].lower() in output.lower(),
                    "Launcher did not select the requested bootstrap interpreter")
        client = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        attachment_path = saved_workflow(client, base)
        secret = (project / ".secret_key").read_bytes()

        print("[smoke] A second launch reuses the same running project", flush=True)
        duplicate_log = root / "duplicate-launch.log"
        duplicate = launch(project, port, duplicate_log, offline=True)
        processes.append(duplicate)
        require(duplicate.wait(timeout=60) == 0, "Second launch failed")
        require("already running" in duplicate_log.read_text(encoding="utf-8", errors="replace"),
                "Second launch did not recognize its own service")
        check_saved(client, base, attachment_path)
        stop(first)
        with closing(sqlite3.connect(project / "trade_agent.db")) as connection:
            require(connection.execute("SELECT company_name FROM enterprises").fetchall() == [(COMPANY,)],
                    "Enterprise was not committed to disk")
            require(connection.execute("SELECT product_name_cn FROM products").fetchall() == [(PRODUCT,)],
                    "Product was not committed to disk")

        print("[smoke] Offline restart preserves records, attachment, secret and login", flush=True)
        restart_log = root / "restart.log"
        restarted = launch(project, port, restart_log, offline=True)
        processes.append(restarted)
        wait_ready(restarted, base, timeout=90)
        require("no download needed" in restart_log.read_text(encoding="utf-8", errors="replace"),
                "Restart unnecessarily reinstalled dependencies")
        require((project / ".secret_key").read_bytes() == secret, "Restart replaced the local secret")
        check_saved(client, base, attachment_path)
        stop(restarted)

        print("[smoke] An unrelated occupied port fails without stopping its service", flush=True)
        with OtherHTTPServer(("127.0.0.1", 0), OtherService) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                occupied = server.server_address[1]
                collision_log = root / "occupied-port.log"
                collision = launch(project, occupied, collision_log, offline=True)
                processes.append(collision)
                require(collision.wait(timeout=60) != 0, "Launcher accepted another service's port")
                output = collision_log.read_text(encoding="utf-8", errors="replace")
                require("used by another program" in output, "Port error was not clearly reported")
                body, _ = request(build_opener(ProxyHandler({})), "http://127.0.0.1:" + str(occupied), "/")
                require(json.loads(body).get("service") == "unrelated", "Unrelated service was stopped")
            finally:
                server.shutdown()
    finally:
        for process in reversed(processes):
            stop(process)


# Keep request threads bounded by closing their sockets before Windows cleanup.
class OtherHTTPServer(ThreadingHTTPServer):
    daemon_threads = False


def main():
    with tempfile.TemporaryDirectory(prefix="trade-launcher-") as directory:
        root = Path(directory)
        try:
            run_smoke(root)
        except Exception:
            for log in sorted(root.glob("*.log")):
                print("\n--- {} ---\n{}".format(log.name, log.read_text(encoding="utf-8", errors="replace")),
                      file=sys.stderr, flush=True)
            raise
    print("[smoke] PASS: launch, login, save, attachment, reuse, offline restart and port conflict", flush=True)


if __name__ == "__main__":
    main()
