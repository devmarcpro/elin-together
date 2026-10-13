#!/bin/bash
# Barriere avant une version : TOUTES les series a deux fenetres, chacune sur un monde de test neuf, puis un verdict.
# La 0.26.691 est sortie avec un defaut (l'animal brosse par un invite allait a l'host) parce que recruit_suite n'avait
# pas ete rejouee : publish_release.py refuse maintenant de publier sans le fichier que ce script ecrit, pour le code
# exact qui est publie. PC libre seulement (une heure et demie, ferme tous les Elin entre deux series).
#   usage : bash _tools/release_gate.sh            # tout
#           bash _tools/release_gate.sh quest_suite ride_suite    # quelques series (pas de verdict « BARRIERE OK »)
cd "$(dirname "$0")/.."
ALL="oct10_suite quest_suite together_suite base_suite trade_suite reconnect_suite death_suite ride_suite recruit_suite
     away_recruit_suite companion_suite travel_suite sleep_suite guest_suite"
# (celles qui lancent mp_test elles-memes : sur les fenetres deja ouvertes)
REUSE=" companion_suite travel_suite "
suites=${*:-$ALL}
# le code publie : le mod et ses textes, pas les notes ni les outils
code="$(git rev-parse HEAD:ElinTogether)-$(git rev-parse HEAD:package)"
dirty=$(git status --porcelain -- ../ElinTogether ../package | wc -l)
out=_shots/gate.txt
# (seulement les fenetres du banc, reconnues a « -empmute » : jamais un jeu lance par l'utilisateur)
bench() { powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='Elin.exe'\" | Where-Object { \$_.CommandLine -match 'empmute' } | ForEach-Object { \$_.ProcessId }" | tr -d '\r'; }
kill_all() {
    for p in $(bench); do taskkill //PID $p //F >/dev/null; done
    for i in $(seq 1 30); do [ -z "$(bench)" ] && break; sleep 2; done
}
# une seule barriere a la fois : la derniere lancee prend le verrou, une plus ancienne (arretee a moitie : seul son
# « tail » meurt) s'arrete d'elle-meme a la serie suivante au lieu de fermer les fenetres de la nouvelle
lock=_shots/gate.lock
me="$$-$RANDOM"
echo "$me" > $lock
echo "code $code" > $out
echo "debut $(date '+%Y-%m-%d %H:%M')" >> $out
[ "$dirty" != "0" ] && echo "ATTENTION : $dirty fichier(s) du mod pas dans git : ce n'est pas le code d'un commit" | tee -a $out
bad=0
for suite in $suites; do
    [ "$(cat $lock 2>/dev/null)" != "$me" ] && { echo "une autre barriere a pris la main, arret"; exit 3; }
    kill_all
    sleep 10
    log=_shots/${suite}-gate.log
    args=""
    case "$REUSE" in *" $suite "*) args="--reuse";; esac
    [ "$suite" = "away_recruit_suite" ] && args="all"
    PYTHONPATH=_tools/pylib PYTHONIOENCODING=utf-8 python -u _tools/mp_test.py > $log 2>&1 \
        && PYTHONPATH=_tools/pylib PYTHONIOENCODING=utf-8 python -u _tools/${suite}.py $args >> $log 2>&1
    code_exit=$?
    line="$suite exit=$code_exit $(grep -a 'verifications OK' $log | tr '\n' ' ') echecs=$(grep -ac 'ECHEC\]' $log)"
    echo "$line" | tee -a $out
    [ "$code_exit" != "0" ] && bad=$((bad + 1))
done
kill_all
echo "fin $(date '+%Y-%m-%d %H:%M')" >> $out
if [ "$suites" = "$ALL" ] && [ "$bad" = "0" ] && [ "$dirty" = "0" ]; then
    echo "BARRIERE OK" | tee -a $out
else
    echo "BARRIERE ROUGE : $bad serie(s) en echec$([ "$suites" != "$ALL" ] && echo ', passe partielle')" | tee -a $out
fi
