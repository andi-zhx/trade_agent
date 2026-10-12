"""Run a check with its real exit status and readable GitHub job diagnostics."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, *sys.argv[1:]], env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    print(result.stdout, flush=True)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as output:
            output.write("### " + " ".join(sys.argv[1:]) + "\n\n")
            output.write("Exit status: " + str(result.returncode) + "\n\n")
            output.write("```text\n" + result.stdout[-50000:].replace("```", "'''") + "\n```\n")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
