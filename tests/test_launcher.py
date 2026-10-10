"""Local startup regressions; no business database or package downloads needed."""
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import launch_local as launcher


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(self.server.response_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.server.response_body)

    def log_message(self, *_args):
        pass


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthHandler)
        self.server.response_status = 200
        self.server.response_body = b"{}"
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.01}, daemon=True,
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def response(self, payload, status=200):
        self.server.response_status = status
        self.server.response_body = json.dumps(payload).encode("utf-8")

    def test_only_healthy_instance_of_this_project_is_ready(self):
        for payload in (
            [], None, "ok", 1,
            {"status": "ok"},
            {"status": "ok", "local_project": "another-project"},
            {"status": "unavailable", "local_project": launcher.PROJECT_ID},
        ):
            with self.subTest(payload=payload):
                self.response(payload)
                self.assertFalse(launcher.running_project(self.port))
        self.response({"status": "ok", "local_project": launcher.PROJECT_ID})
        self.assertTrue(launcher.running_project(self.port))

    def test_malformed_or_unavailable_health_response_is_not_ready(self):
        self.server.response_body = b"not json"
        self.assertFalse(launcher.running_project(self.port))
        self.response({"status": "ok", "local_project": launcher.PROJECT_ID}, status=503)
        self.assertFalse(launcher.running_project(self.port))

    def test_system_proxy_does_not_intercept_local_readiness(self):
        self.response({"status": "ok", "local_project": launcher.PROJECT_ID})
        with patch.dict(os.environ, {
            "HTTP_PROXY": "http://127.0.0.1:1",
            "http_proxy": "http://127.0.0.1:1",
            "ALL_PROXY": "http://127.0.0.1:1",
            "NO_PROXY": "", "no_proxy": "",
        }):
            self.assertTrue(launcher.running_project(self.port))

    def test_occupied_port_is_reported_without_stopping_its_server(self):
        self.assertFalse(launcher.port_available(self.port))
        self.response({"status": "ok", "local_project": launcher.PROJECT_ID})
        self.assertTrue(launcher.running_project(self.port))


class LauncherBehaviorTests(unittest.TestCase):
    def test_browser_opens_only_after_this_project_becomes_ready(self):
        with patch.object(launcher, "running_project", side_effect=[False, False, True]), \
                patch.object(launcher.webbrowser, "open") as browser:
            def wait_without_opening(_seconds):
                browser.assert_not_called()
            with patch.object(launcher.time, "sleep", side_effect=wait_without_opening):
                launcher.open_browser_when_ready(5123)
            browser.assert_called_once_with("http://127.0.0.1:5123/")

    def test_failed_start_does_not_open_browser(self):
        output = StringIO()
        with patch.object(launcher, "running_project", return_value=False), \
                patch.object(launcher.time, "sleep"), \
                patch.object(launcher.webbrowser, "open") as browser, \
                redirect_stdout(output):
            launcher.open_browser_when_ready(5123)
        browser.assert_not_called()
        self.assertIn("not ready", output.getvalue())

    def test_existing_instance_is_reopened_without_installing_or_starting(self):
        with patch.object(sys, "argv", ["launch_local.py", "--port", "5123"]), \
                patch.object(launcher.os, "chdir"), \
                patch.object(launcher, "running_project", return_value=True), \
                patch.object(launcher, "prepare_environment") as prepare, \
                patch.object(launcher, "run_python") as run_python, \
                patch.object(launcher.webbrowser, "open") as browser, \
                redirect_stdout(StringIO()):
            self.assertEqual(launcher.main(), 0)
        prepare.assert_not_called()
        run_python.assert_not_called()
        browser.assert_called_once_with("http://127.0.0.1:5123/")

    def test_conflicting_port_fails_before_package_setup(self):
        with patch.object(sys, "argv", ["launch_local.py", "--no-browser"]), \
                patch.object(launcher.os, "chdir"), \
                patch.object(launcher, "running_project", return_value=False), \
                patch.object(launcher, "port_available", return_value=False), \
                patch.object(launcher, "prepare_environment") as prepare, \
                patch.object(launcher, "run_python") as run_python:
            with self.assertRaisesRegex(RuntimeError, "No process was stopped"):
                launcher.main()
        prepare.assert_not_called()
        run_python.assert_not_called()

    def test_child_environment_keeps_data_location_but_isolates_python(self):
        with patch.dict(os.environ, {
            "PYTHONHOME": "unrelated-python", "PYTHONPATH": "unrelated-packages",
            "TRADE_DATA_DIR": "existing-business-data",
        }):
            environment = launcher.child_environment()
            self.assertNotIn("PYTHONHOME", environment)
            self.assertNotIn("PYTHONPATH", environment)
            self.assertEqual(environment["TRADE_DATA_DIR"], "existing-business-data")
            self.assertEqual(os.environ["PYTHONHOME"], "unrelated-python")

    def test_broken_venv_gives_safe_recovery_instructions_and_keeps_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            python = root / ".venv" / "python.exe"
            python.parent.mkdir()
            python.touch()
            data_paths = [root / "trade_agent.db", root / ".secret_key",
                          root / "uploads" / "existing.txt", root / "backups" / "existing.zip"]
            for path in data_paths:
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b"existing data must remain untouched")
            for failure in (subprocess.CompletedProcess([], 1), OSError("missing base Python")):
                with self.subTest(failure=type(failure).__name__), \
                        patch.object(launcher, "VENV_PYTHON", python), \
                        patch.object(launcher, "run_python") as run_python:
                    if isinstance(failure, Exception):
                        run_python.side_effect = failure
                    else:
                        run_python.return_value = failure
                    with self.assertRaises(RuntimeError) as caught:
                        launcher.prepare_environment()
                    message = str(caught.exception)
                    for expected in (".venv", "trade_agent.db", "uploads", "backups", ".secret_key"):
                        self.assertIn(expected, message)
                    run_python.assert_called_once()
                    for path in data_paths:
                        self.assertEqual(path.read_bytes(), b"existing data must remain untouched")


class LauncherLockTests(unittest.TestCase):
    def attempt_lock_in_another_process(self, root):
        code = (
            "from pathlib import Path\n"
            "import sys\n"
            "import launch_local as launcher\n"
            "launcher.ROOT = Path(sys.argv[1])\n"
            "try:\n"
            "    with launcher.launcher_lock():\n"
            "        print('acquired')\n"
            "except RuntimeError as error:\n"
            "    print(error)\n"
            "    sys.exit(23)\n"
        )
        return subprocess.run(
            [sys.executable, "-c", code, str(root)],
            cwd=Path(launcher.__file__).resolve().parent,
            capture_output=True, encoding="utf-8", errors="replace", timeout=15,
        )

    def test_other_process_is_excluded_and_can_restart_after_lock_release(self):
        with tempfile.TemporaryDirectory(prefix="trade launcher ") as temporary:
            root = Path(temporary) / "中文 项目"
            root.mkdir()
            with patch.object(launcher, "ROOT", root):
                with launcher.launcher_lock():
                    blocked = self.attempt_lock_in_another_process(root)
                    self.assertEqual(blocked.returncode, 23, blocked.stdout + blocked.stderr)
                    self.assertIn("Another launcher", blocked.stdout)
                restarted = self.attempt_lock_in_another_process(root)
                self.assertEqual(restarted.returncode, 0, restarted.stdout + restarted.stderr)
                self.assertIn("acquired", restarted.stdout)

    def test_setup_failure_releases_lock_for_the_next_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(launcher, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "installation failed"):
                    with launcher.launcher_lock():
                        raise RuntimeError("installation failed")
                restarted = self.attempt_lock_in_another_process(root)
                self.assertEqual(restarted.returncode, 0, restarted.stdout + restarted.stderr)


if __name__ == "__main__":
    unittest.main()
