"""File-level tests: large files, modifications, permissions, many files."""

import os
import stat
import time

from helpers import (
    BaseTest,
    create_file,
    create_random_file,
    dir_hash_map,
    md5sum,
    parse_perf_report,
    run_sync,
)


class TestFiles(BaseTest):
    """File copy and detection tests."""

    def test_large_file(self) -> None:
        """Test: large file (5MB) is copied block-by-block correctly."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        size = 5 * 1024 * 1024
        create_random_file(os.path.join(src, "big.bin"), size)

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "large file exit code")
        self.assert_eq(
            md5sum(os.path.join(src, "big.bin")),
            md5sum(os.path.join(dst, "big.bin")),
            "large file integrity"
        )
        self.teardown()

    def test_modified_file_updated(self) -> None:
        """Test: changed file is re-copied on second run."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "data.txt"), b"version1\n")
        run_sync(src, dst)

        # Sleep >1s so mtime (second resolution) advances,
        # and use different size so size comparison also triggers
        time.sleep(1.1)
        create_file(
            os.path.join(src, "data.txt"),
            b"version2 with extra content\n"
        )

        run_sync(src, dst)
        with open(os.path.join(dst, "data.txt"), "rb") as f:
            content = f.read()
        self.assert_eq(
            content, b"version2 with extra content\n",
            "modified file updated"
        )
        self.teardown()

    def test_unchanged_file_skipped(self) -> None:
        """Test: unchanged files yield 0 copies on second run."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "same.txt"), b"same\n")
        run_sync(src, dst)

        result = run_sync(src, dst)
        perf = parse_perf_report(result.stdout)
        files_str = perf.get("Files copied", "0")
        self.assert_eq(files_str, "0", "unchanged files skipped")
        self.teardown()

    def test_file_permissions_preserved(self) -> None:
        """Test: file permissions are copied to destination."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        fpath = os.path.join(src, "script.sh")
        create_file(fpath, b"#!/bin/bash\necho hi\n")
        os.chmod(fpath, 0o755)

        run_sync(src, dst)
        dst_mode = os.stat(os.path.join(dst, "script.sh")).st_mode
        self.assert_true(
            bool(dst_mode & stat.S_IXUSR),
            "execute permission preserved"
        )
        self.teardown()

    def test_many_small_files(self) -> None:
        """Test: 100 small files are all synced correctly."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        for i in range(100):
            create_file(
                os.path.join(src, f"file_{i:03d}.txt"),
                f"content {i}\n".encode()
            )

        result = run_sync(src, dst)
        self.assert_eq(result.returncode, 0, "many files exit code")
        self.assert_eq(
            dir_hash_map(src), dir_hash_map(dst),
            "many files content match"
        )
        self.teardown()
