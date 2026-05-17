#!/usr/bin/env python3
"""Main test runner — discovers and runs all test suites."""

import subprocess
import sys
from pathlib import Path

from helpers import BaseTest, PROJECT_ROOT
from test_basic import TestBasic
from test_files import TestFiles
from test_threads import TestThreads


def collect_tests(suite: BaseTest) -> list[str]:
    """Return sorted list of test method names."""
    return sorted(
        m for m in dir(suite)
        if m.startswith("test_") and callable(getattr(suite, m))
    )


def run_suite(suite: BaseTest, name: str, totals: dict[str, int]) -> None:
    """Run all tests in a suite and accumulate results."""
    methods = collect_tests(suite)
    print(f"\n  ── {name} ({len(methods)} tests) ──\n")

    for method_name in methods:
        label = method_name.replace("test_", "").replace("_", " ").title()
        try:
            before = suite.passed + suite.failed
            getattr(suite, method_name)()
            after = suite.passed + suite.failed
            checks = after - before
            print(f"  +  {label} ({checks} checks)")
        except Exception as e:
            suite.failed += 1
            suite.errors.append(f"  EXCEPTION in {method_name}: {e}")
            print(f"  !  {label} (exception: {e})")

    totals["passed"] += suite.passed
    totals["failed"] += suite.failed
    totals["errors"].extend(suite.errors)


def main() -> None:
    """Build if needed, then run all test suites."""
    binary = PROJECT_ROOT / "filesync"
    if not binary.exists():
        print("Building filesync...")
        result = subprocess.run(
            ["make", "-C", str(PROJECT_ROOT)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Build failed:\n{result.stderr}")
            sys.exit(1)

    suites: list[tuple[BaseTest, str]] = [
        (TestBasic(), "Basic Sync Tests"),
        (TestFiles(), "File Operation Tests"),
        (TestThreads(), "Thread & Performance Tests"),
    ]

    totals: dict[str, object] = {
        "passed": 0,
        "failed": 0,
        "errors": [],
    }

    total_tests = sum(len(collect_tests(s)) for s, _ in suites)
    print(f"\n{'=' * 56}")
    print(f"  filesync test suite — {total_tests} tests")
    print(f"{'=' * 56}")

    for suite, name in suites:
        run_suite(suite, name, totals)

    print(f"\n{'─' * 56}")
    print(f"  Results: {totals['passed']} passed, {totals['failed']} failed")
    errors = totals["errors"]
    if errors:
        print()
        for err in errors:
            print(err)
    print(f"{'=' * 56}\n")
    sys.exit(0 if totals["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
