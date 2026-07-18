#!/usr/bin/env bash
set -e

echo "=================================================="
echo "==> Running test suite..."
echo "=================================================="
pytest --cov=app --cov-report=term-missing

echo ""
echo "=================================================="
echo "==> Tests passed. Starting the weather service..."
echo "=================================================="
exec python3 script.py
