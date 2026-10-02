#!/bin/bash
# Enchaine les suites de test, ferme les instances d'Elin (PID exacts) entre chaque.
# usage : bash _tools/run_all.sh <suffixe> suite1 suite2 ...
cd "$(dirname "$0")/.."
tag=$1; shift
for suite in "$@"; do
    for p in $(tasklist //FI "IMAGENAME eq Elin.exe" //FO CSV //NH | cut -d, -f2 | tr -d '"' | grep -E '^[0-9]+$'); do taskkill //PID $p //F >/dev/null; done
    sleep 15
    PYTHONPATH=_tools/pylib python -u _tools/${suite}.py > _shots/${suite}-${tag}.log 2>&1
    echo "$suite exit=$? $(grep 'verifications OK' _shots/${suite}-${tag}.log)"
done
for p in $(tasklist //FI "IMAGENAME eq Elin.exe" //FO CSV //NH | cut -d, -f2 | tr -d '"' | grep -E '^[0-9]+$'); do taskkill //PID $p //F >/dev/null; done
echo "fini"
