"""Sonde de gels : interroge `state` toutes les 50 ms dans chaque jeu (pont de test, ports 27551 host, 27552-27553
clients) et mesure ce que le joueur sent comme un gel, sans recompiler le mod.

Le pont repond sur le fil principal du jeu : pendant un gel de l'image la reponse attend. Le plus long trou entre
deux reponses est donc la duree du gel (precision ~50 ms + le temps d'un aller-retour).

Rend, pour chaque jeu : le plus long trou (gel), le nombre de trous de plus de 200 ms / 500 ms / 1 s, le plus long
`ms` de reponse, et le nombre de sauvegardes pendant la mesure (`EClass.game.saveCount` lu par `eval`, avant et apres).

    python _tools/perf_probe.py                       # jeux ouverts (27551-27560), jusqu'a Ctrl+C
    python _tools/perf_probe.py --seconds 130         # duree donnee
    python _tools/perf_probe.py --ports 27551 27552

Module :

    sys.path.insert(0, str(Path(__file__).parent)); import perf_probe
    with perf_probe.Probe([27551, 27552, 27553]) as p:
        ...                                           # ce qu'on chronometre (depart, retour de l'host...)
    p.report()

A ajouter dans `trio_place_suite.py` (apres le test : pas encore fait) :

    1. en tete, a cote des autres imports :   import perf_probe  # noqa: E402
    2. dans host_leaves(ctx) et q2(ctx), autour de l'action (depart / retour de l'host) :
           with perf_probe.Probe([27551, 27552, 27553]) as probe:
               ...   # le corps actuel de la fonction
    3. juste apres ce bloc (meme niveau que le `with`) :   probe.report()

Avant la mesure, `emp.autosave_every 120` chez l'host si on veut des sauvegardes spontanees (sans cela le banc
ne sauvegarde jamais seul). `saveCount` ne compte que les sauvegardes du jeu (Game.Save), pas la copie du monde.
"""
import argparse
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402

DEFAULT_PORTS = (27551, 27552, 27553)
THRESHOLDS = (0.2, 0.5, 1.0)


def _save_count(port):
    try:
        r = emp.call(port, "eval", {"code": "EClass.game.saveCount"}, timeout=60.0)
        return int(r["result"]) if r.get("ok") else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


class _Watch(threading.Thread):
    """Un fil par jeu : un `state` toutes les `interval` secondes, en gardant les trous entre les reponses."""

    def __init__(self, port, interval, stop):
        super().__init__(daemon=True)
        self.port, self.interval, self.stop_event = port, interval, stop
        self.start_t = time.perf_counter()
        self.last = self.start_t       # derniere reponse (ou le debut)
        self.gaps = []                 # (duree, instant du trou depuis le debut)
        self.max_ms = 0
        self.answers = 0
        self.errors = 0

    def run(self):
        while not self.stop_event.is_set():
            try:
                r = emp.call(self.port, "state", timeout=60.0)
                now = time.perf_counter()
                if r.get("ok"):
                    self.gaps.append((now - self.last, self.last - self.start_t))
                    self.last = now
                    self.answers += 1
                    self.max_ms = max(self.max_ms, r.get("ms") or 0)
                else:
                    self.errors += 1
            except (OSError, ValueError):
                self.errors += 1
            self.stop_event.wait(self.interval)


class Probe:
    def __init__(self, ports=DEFAULT_PORTS, interval=0.05):
        self.ports, self.interval = list(ports), interval
        self._stop = threading.Event()
        self._watches = []
        self._saves_before = {}
        self._saves_after = {}
        self._open_gap = {}
        self.seconds = 0.0

    def __enter__(self):
        self._saves_before = {p: _save_count(p) for p in self.ports}
        self._t0 = time.perf_counter()
        self._watches = [_Watch(p, self.interval, self._stop) for p in self.ports]
        for w in self._watches:
            w.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        end = time.perf_counter()
        for w in self._watches:
            w.join(timeout=3.0)
            # a game still frozen when we stop: the gap is still open
            self._open_gap[w.port] = end - w.last
        self.seconds = end - self._t0
        self._saves_after = {p: _save_count(p) for p in self.ports}
        return False

    def results(self):
        out = {}
        for w in self._watches:
            gaps = w.gaps + [(self._open_gap.get(w.port, 0.0), w.last - w.start_t)]
            worst, at = max(gaps)
            before, after = self._saves_before.get(w.port), self._saves_after.get(w.port)
            out[w.port] = {
                "max_gap_s": round(worst, 3),
                "max_gap_at_s": round(at, 1),
                **{f"gaps_over_{int(t * 1000)}ms": sum(1 for g, _ in gaps if g > t) for t in THRESHOLDS},
                "max_response_ms": w.max_ms,
                "answers": w.answers,
                "errors": w.errors,
                "saves": None if before is None or after is None else after - before,
            }
        return out

    def report(self):
        res = self.results()
        print(f"perf_probe : {self.seconds:.1f} s, un `state` toutes les {self.interval * 1000:.0f} ms", flush=True)
        print(f"  {'port':<6} {'gel max':>8} {'a (s)':>7} {'>200ms':>7} {'>500ms':>7} {'>1s':>5} "
              f"{'ms max':>7} {'reponses':>9} {'erreurs':>8} {'saves':>6}", flush=True)
        for port, r in res.items():
            saves = "?" if r["saves"] is None else r["saves"]
            print(f"  {port:<6} {r['max_gap_s']:>7.2f}s {r['max_gap_at_s']:>7.1f} {r['gaps_over_200ms']:>7} "
                  f"{r['gaps_over_500ms']:>7} {r['gaps_over_1000ms']:>5} {r['max_response_ms']:>7} "
                  f"{r['answers']:>9} {r['errors']:>8} {saves:>6}", flush=True)
        return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ports", type=int, nargs="+", help="ports du pont (defaut : les jeux qui repondent)")
    ap.add_argument("--seconds", type=float, help="duree (defaut : jusqu'a Ctrl+C)")
    ap.add_argument("--interval", type=float, default=0.05)
    a = ap.parse_args()

    ports = a.ports or [r["port"] for r in emp.live_ports()]
    if not ports:
        sys.exit("aucun jeu avec le pont de test (build Debug lance ?)")
    print(f"mesure sur {ports}" + (f" pendant {a.seconds:.0f} s" if a.seconds else " (Ctrl+C pour finir)"), flush=True)

    with Probe(ports, a.interval) as probe:
        try:
            if a.seconds:
                time.sleep(a.seconds)
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
    probe.report()


if __name__ == "__main__":
    main()
