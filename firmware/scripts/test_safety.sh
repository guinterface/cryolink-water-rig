#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
g++ -std=c++17 -Wall -Wextra -Werror tests/safety_native.cpp -o tests/safety_native
./tests/safety_native
python -m unittest discover -s tests -p test_protocol.py -v
python tests/pty_interlocks.py
