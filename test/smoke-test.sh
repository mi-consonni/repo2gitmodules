#!/bin/sh -e

SELF_PATH="$(realpath "$0")"
SELF_DIR="$(dirname "$SELF_PATH")"
SCRIPT_PATH="$SELF_DIR/../repo2gitmodules.py"

run_smoke_test() {
    "$SCRIPT_PATH" -u https://github.com/varigit/variscite-bsp-platform -b kirkstone -m default.xml \
	    && git commit -m "kirkstone" \
	    && "$SCRIPT_PATH" -u https://github.com/varigit/variscite-bsp-platform -b scarthgap -m imx-6.6.52-2.2.0.xml \
	    && git commit -m "scarthgap"
}

tmpdir="$(mktemp -d)"
( cd "$tmpdir" && run_smoke_test ) && echo "SUCCESS" || echo "FAILED"
rm -rf "$tmpdir"
