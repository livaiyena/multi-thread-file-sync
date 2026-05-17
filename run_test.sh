#!/bin/bash
# Quick functional test for filesync

BINARY="./filesync"
SRC="test_src"
DST="test_dst"

echo "=== Creating test directories ==="
mkdir -p "$SRC/subdir1/nested" "$SRC/subdir2"
echo "Hello World" > "$SRC/file1.txt"
echo "Test file 2" > "$SRC/file2.txt"
dd if=/dev/urandom of="$SRC/large_file.bin" bs=1M count=10 2>/dev/null
echo "Nested content" > "$SRC/subdir1/nested/deep.txt"
echo "Subdir file" > "$SRC/subdir1/sub1.txt"
echo "Another one" > "$SRC/subdir2/sub2.txt"

echo ""
echo "=== Running sync with 4 threads ==="
$BINARY "$SRC" "$DST" 4

echo ""
echo "=== Verifying sync ==="
if diff -rq "$SRC" "$DST" > /dev/null 2>&1; then
    echo "SUCCESS: All files synced!"
else
    echo "FAIL: Differences found"
    diff -rq "$SRC" "$DST"
    exit 1
fi

echo ""
echo "=== Log output ==="
cat logs/sync.log

echo ""
echo "=== Cleaning up ==="
rm -rf "$SRC" "$DST" logs
echo "Done."
