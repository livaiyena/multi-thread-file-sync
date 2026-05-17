"""Basic sync tests: simple copy, recursive dirs, empty dir, error cases."""

import os
import random
import subprocess

from helpers import (
    BaseTest,
    PROJECT_ROOT,
    create_file,
    create_random_file,
    dir_hash_map,
    run_sync,
)


class TestBasic(BaseTest):
    """Basic functionality tests."""

    def test_basic_sync(self) -> None:
        """Test: basic file copy from source to destination."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "a.txt"), b"hello\n")
        create_file(os.path.join(src, "b.txt"), b"world\n")

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "basic sync exit code")
        self.assert_eq(
            dir_hash_map(src), dir_hash_map(dst),
            "basic sync content match"
        )
        self.teardown()

    def test_recursive_directories(self) -> None:
        """Test: deeply nested subdirectories are synced."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        deep = os.path.join(src, "a", "b", "c", "d")
        os.makedirs(deep)
        create_file(os.path.join(deep, "deep.txt"), b"deep content\n")
        create_file(os.path.join(src, "a", "mid.txt"), b"mid\n")
        create_file(os.path.join(src, "root.txt"), b"root\n")

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "recursive sync exit code")
        self.assert_eq(
            dir_hash_map(src), dir_hash_map(dst),
            "recursive sync content match"
        )
        self.teardown()

    def test_empty_directory(self) -> None:
        """Test: syncing an empty source directory works."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "empty dir exit code")
        self.assert_true(os.path.isdir(dst), "empty dir dst created")
        self.teardown()

    def test_invalid_source(self) -> None:
        """Test: non-existent source directory returns error."""
        tmp = self.setup()
        result = run_sync(
            "/tmp/nonexistent_xyz_abc", os.path.join(tmp, "d")
        )
        self.assert_true(result.returncode != 0, "invalid source fails")
        self.teardown()

    def test_missing_args(self) -> None:
        """Test: no arguments prints usage and returns error."""
        result = subprocess.run(
            [str(PROJECT_ROOT / "filesync")],
            capture_output=True, text=True, timeout=5,
            cwd=str(PROJECT_ROOT),
        )
        self.assert_true(result.returncode != 0, "missing args fails")
        self.assert_true("Usage" in result.stderr, "usage message shown")
        self.teardown()

    def test_mixed_directory_tree(self) -> None:
        """Test: complex tree with varied file sizes and nesting."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        random.seed(42)
        dirs = ["", "docs", "docs/internal", "images", "data/raw"]
        for d in dirs:
            p = os.path.join(src, d)
            os.makedirs(p, exist_ok=True)
            for i in range(3):
                size = random.randint(100, 200000)
                create_random_file(os.path.join(p, f"f{i}.bin"), size)

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "mixed tree exit code")
        self.assert_eq(
            dir_hash_map(src), dir_hash_map(dst),
            "mixed tree full content match"
        )
        self.teardown()
