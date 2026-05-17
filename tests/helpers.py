"""Shared helpers, constants, and base test class for filesync tests."""

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
LOG_FILE: str = "logs/sync.log"


def md5sum(path: str) -> str:
    """Return MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def create_file(path: str, content: bytes) -> None:
    """Create a file with given binary content, making parents."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def create_random_file(path: str, size: int) -> None:
    """Create a file filled with random bytes."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        remaining = size
        while remaining > 0:
            chunk = min(remaining, 65536)
            f.write(os.urandom(chunk))
            remaining -= chunk


def run_sync(
    src: str,
    dst: str,
    threads: int = 4,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Run the filesync binary and return the result."""
    cmd = [str(PROJECT_ROOT / "filesync"), src, dst, str(threads)]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )


def dir_hash_map(directory: str) -> dict[str, str]:
    """Return {relative_path: md5} for every file under directory."""
    result: dict[str, str] = {}
    for root, _dirs, files in os.walk(directory):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, directory)
            result[rel] = md5sum(full)
    return result


def read_log() -> str:
    """Read the sync log file contents."""
    log_path = PROJECT_ROOT / LOG_FILE
    if log_path.exists():
        return log_path.read_text()
    return ""


def parse_perf_report(stdout: str) -> dict[str, str]:
    """Parse performance report lines from stdout."""
    data: dict[str, str] = {}
    for line in stdout.splitlines():
        if ":" in line and line.strip().startswith(
            ("Threads", "Files", "Bytes", "Elapsed", "Throughput")
        ):
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip()
    return data


class BaseTest:
    """Base test class with setup/teardown and assertion helpers."""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.errors: list[str] = []
        self._tmpdir: Optional[str] = None

    def setup(self) -> str:
        """Create a fresh temp directory and return its path."""
        self._tmpdir = tempfile.mkdtemp(
            dir=str(PROJECT_ROOT), prefix="test_"
        )
        return self._tmpdir

    def teardown(self) -> None:
        """Remove the temp directory."""
        if self._tmpdir and os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir)
        log_dir = PROJECT_ROOT / "logs"
        if log_dir.exists():
            shutil.rmtree(log_dir)

    def assert_true(self, cond: bool, msg: str) -> None:
        """Check condition is true."""
        if cond:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"  FAIL: {msg}")

    def assert_eq(self, a: object, b: object, msg: str) -> None:
        """Check two values are equal."""
        if a == b:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"  FAIL: {msg} (got {a!r} != {b!r})")
