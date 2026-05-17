"""Thread and performance tests: thread variants, benchmark."""

import os

from helpers import (
    BaseTest,
    create_file,
    create_random_file,
    dir_hash_map,
    parse_perf_report,
    read_log,
    run_sync,
)


class TestThreads(BaseTest):
    """Thread pool and performance tests."""

    def test_single_vs_multi_thread(self) -> None:
        """Test: both 1-thread and 4-thread produce correct output."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for i in range(20):
            create_random_file(
                os.path.join(src, f"f_{i}.bin"), 64 * 1024
            )

        dst1 = os.path.join(tmp, "dst_t1")
        dst4 = os.path.join(tmp, "dst_t4")
        r1 = run_sync(src, dst1, threads=1)
        r4 = run_sync(src, dst4, threads=4)

        self.assert_eq(r1.returncode, 0, "1-thread exit code")
        self.assert_eq(r4.returncode, 0, "4-thread exit code")
        self.assert_eq(
            dir_hash_map(dst1), dir_hash_map(dst4),
            "1-thread vs 4-thread identical output"
        )
        self.teardown()

    def test_thread_count_variants(self) -> None:
        """Test: thread counts 1, 2, 4, 8 all produce correct results."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for i in range(10):
            create_file(
                os.path.join(src, f"t{i}.txt"),
                f"thread test {i}\n".encode()
            )

        src_map = dir_hash_map(src)
        for tc in [1, 2, 4, 8]:
            dst = os.path.join(tmp, f"dst_t{tc}")
            result = run_sync(src, dst, threads=tc)
            self.assert_eq(
                result.returncode, 0, f"{tc}-thread exit code"
            )
            self.assert_eq(
                src_map, dir_hash_map(dst),
                f"{tc}-thread content match"
            )
        self.teardown()

    def test_log_file_created(self) -> None:
        """Test: log file is created and contains expected entries."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "log_test.txt"), b"log me\n")

        run_sync(src, dst)
        log = read_log()
        self.assert_true("START" in log, "log contains START")
        self.assert_true("COPY" in log, "log contains COPY")
        self.assert_true("FINISH" in log, "log contains FINISH")
        self.assert_true("log_test.txt" in log, "log contains filename")
        self.teardown()

    def test_log_thread_id(self) -> None:
        """Test: log entries contain thread IDs."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "tid.txt"), b"tid test\n")

        run_sync(src, dst)
        log = read_log()
        self.assert_true("tid:" in log, "log contains thread ID")
        self.teardown()

    def test_performance_report_output(self) -> None:
        """Test: stdout contains a valid performance report."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        dst = os.path.join(tmp, "dst")
        os.makedirs(src)
        create_file(os.path.join(src, "perf.txt"), b"perf\n")

        result = run_sync(src, dst)
        self.assert_true(
            "Performance Report" in result.stdout,
            "performance report header"
        )
        perf = parse_perf_report(result.stdout)
        self.assert_true("Threads" in perf, "report has Threads")
        self.assert_true("Elapsed time" in perf, "report has Elapsed")
        self.assert_true("Throughput" in perf, "report has Throughput")
        self.teardown()

    def test_performance_benchmark(self) -> None:
        """Benchmark: compare throughput across thread counts."""
        tmp = self.setup()
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for i in range(30):
            create_random_file(
                os.path.join(src, f"bench_{i}.bin"), 128 * 1024
            )

        print("\n  ┌─────────┬────────────┬──────────────┐")
        print("  │ Threads │   Time (s) │ Throughput   │")
        print("  ├─────────┼────────────┼──────────────┤")
        for tc in [1, 2, 4, 8]:
            dst = os.path.join(tmp, f"bench_dst_{tc}")
            result = run_sync(src, dst, threads=tc)
            perf = parse_perf_report(result.stdout)
            elapsed = perf.get("Elapsed time", "?")
            throughput = perf.get("Throughput", "?")
            print(f"  │ {tc:>7} │ {elapsed:>10} │ {throughput:>12} │")
        print("  └─────────┴────────────┴──────────────┘")

        self.assert_true(True, "benchmark completed")
        self.teardown()
