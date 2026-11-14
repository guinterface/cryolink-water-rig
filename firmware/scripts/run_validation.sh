#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
./scripts/test_safety.sh > logs/safety_tests.log 2>&1
python tests/integration.py > logs/integration.log 2>&1
python tests/integration.py --fault seat > logs/fault_seat_test.log 2>&1
python tests/integration.py --fault latch > logs/fault_latch_test.log 2>&1
python tests/check_evidence.py
