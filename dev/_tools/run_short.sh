#!/bin/bash
# Suites courtes (host + 1 client) a la chaine, chacune sur un monde de test neuf : instances d'Elin fermees
# (PID exacts), mp_test, puis la suite. PC libre seulement, comme run_all.sh.
# usage : bash _tools/run_short.sh <suffixe> suite1 suite2 ...
cd "$(dirname "$0")/.."
tag=$1; shift
kill_all() {
    for p in $(tasklist //FI "IMAGENAME eq Elin.exe" //FO CSV //NH | cut -d, -f2 | tr -d '"' | grep -E '^[0-9]+$'); do taskkill //PID $p //F >/dev/null; done
}
for suite in "$@"; do
    kill_all
    sleep 15
    PYTHONPATH=_tools/pylib python -u _tools/mp_test.py > _shots/${suite}-${tag}.log 2>&1 \
        && PYTHONPATH=_tools/pylib python -u _tools/${suite}.py >> _shots/${suite}-${tag}.log 2>&1
    echo "$suite exit=$? $(grep 'verifications OK' _shots/${suite}-${tag}.log)"
done
kill_all
echo "fini"
