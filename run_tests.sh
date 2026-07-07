#!/bin/bash
# Compila e roda a suíte de testes do pipeline de CV.
# Usa um runner em Swift puro (--test) — funciona só com Command Line Tools,
# sem precisar do Xcode completo (que o `swift test`/XCTest exigiriam).
set -e
cd "$(dirname "$0")"
swift build -c debug
exec ./.build/debug/IrisAnalyzer --test
