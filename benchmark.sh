#!/bin/bash
# **************************************************************************** #
#  benchmark.sh - Single-thread vs Multi-thread Performance Comparison         #
# **************************************************************************** #

set -e

BINARY="./filesync"
TEST_DIR="bench_src"
SIZES=(1 5 10)
THREADS=(1 2 4 8)

echo "=========================================="
echo "  Multi-Thread File Sync Benchmark"
echo "=========================================="
echo ""

# Create test data
create_test_data() {
    local size_mb=$1
    echo "[*] Creating test data (${size_mb}MB total across multiple files)..."
    rm -rf "$TEST_DIR"
    mkdir -p "$TEST_DIR/subdir1" "$TEST_DIR/subdir2" "$TEST_DIR/subdir3"

    local file_count=$((size_mb * 4))
    local file_size=$((256 * 1024))

    for i in $(seq 1 $file_count); do
        dir_num=$((i % 3 + 1))
        dd if=/dev/urandom of="${TEST_DIR}/subdir${dir_num}/file_${i}.bin" \
            bs=$file_size count=1 2>/dev/null
    done
    echo "[*] Created $file_count files"
}

# Run benchmark
run_benchmark() {
    local threads=$1
    local dst="bench_dst_t${threads}"
    rm -rf "$dst" logs/sync.log

    echo -n "  Threads: $threads -> "
    $BINARY "$TEST_DIR" "$dst" "$threads" 2>/dev/null | grep "Elapsed\|Throughput\|Files"
    rm -rf "$dst"
}

# Main benchmark loop
for size in "${SIZES[@]}"; do
    echo ""
    echo "--- Dataset: ${size}MB ---"
    create_test_data $size
    echo ""

    for t in "${THREADS[@]}"; do
        run_benchmark $t
    done
done

# Cleanup
rm -rf "$TEST_DIR" bench_dst_* logs

echo ""
echo "=========================================="
echo "  Benchmark Complete"
echo "=========================================="
