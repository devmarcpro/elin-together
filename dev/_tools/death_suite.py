"""La mort d'un joueur qui n'est pas l'host, sur la carte de l'host. Test court (host + 1 client deja lances).

    python _tools/mp_test.py
    python _tools/death_suite.py        # ~2 minutes, finit avec tout le monde a la Prairie

D1  le client meurt pour de bon chez l'host et passe l'ecran de mort comme un joueur : il est releve, en vie des
    deux cotes, toujours chez l'host
D2  apres ca il peut repartir seul sur une autre carte (il restait bloque : le jeu gardait "retour apres la mort")
D3  rien n'existe que chez lui autour de l'endroit ou il est tombe (ce que la mort fait perdre : objets fantomes)
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bot import choices, click  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move,  # noqa: E402
                          scan_logs, wait)

H, A = 27551, 27552
FIND = "EClass.game.cards.globalCharas.Find"


def around(port, uid):
    """Objets a trois cases du personnage, vus par ce jeu : "numero:type" tries."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); if (c == null) return "absent"; '
                    'return string.Join(" ", EClass._map.things.Where(t => t.pos.Distance(c.pos) <= 3)'
                    '.Select(t => t.uid + ":" + t.id).OrderBy(x => x));')


def death_screen(port, pick):
    """L'ecran de mort, comme un joueur : valider les derniers mots, puis le choix numero `pick` de la liste.
    Renvoie (choix proposes, choix fait)."""
    wait(lambda: "Ok" in choices(port), "fenetre des derniers mots", timeout=20, every=1.0)
    click(port, "Ok")
    options = []

    def listed():
        options[:] = [c for c in choices(port) if c and c not in ("Ok", "Cancel")]
        return len(options) >= 2

    wait(listed, "choix du retour", timeout=20, every=1.0)
    click(port, options[pick])
    wait(lambda: state(port).get("sceneMode") == "Zone" and ev(port, "EClass.pc.isDead.ToString()") == "False",
         "retour a la vie", timeout=120, every=1.0)
    time.sleep(3)
    return list(options), options[pick]


def d1(ctx):
    """le client meurt chez l'host et choisit, a l'ecran de mort, de revenir dans la derniere ville visitee"""
    me = ctx["a"]
    # de quoi perdre : la mort fait tomber de l'or (la bourse d'un joueur se remplit depuis son propre jeu)
    gold = lambda: int(ev(A, 'EClass.pc.GetCurrency("money").ToString()'))  # noqa: E731
    had = gold()
    ev(A, 'EClass.pc.ModCurrency(2000); "ok"')
    eventually(lambda: gold() == had + 2000, timeout=10)
    ctx["gold"] = gold()
    check(f"avant : le meme or des deux cotes ({ctx['gold']})",
          eventually(lambda: int(ev(H, f'{FIND}({me}).GetCurrency("money").ToString()')) == ctx["gold"], timeout=10))
    # un joueur qui a deja vu une ville se voit proposer d'y revenir : c'est ce choix qui posait la marque
    # "retour apres la mort" que rien n'effacait
    ev(A, f'EClass.player.uidLastTown = {VERNIS}; "ok"')
    ev(H, f'var c = {FIND}({me}); c.hp = 0; c.Die(); "ok"')
    check("le client se voit mort", eventually(lambda: ev(A, "EClass.pc.isDead.ToString()") == "True", timeout=15))
    try:
        options, choice = death_screen(A, 0)
        log(f"choix proposes : {options} ; choisi : {choice}")
        back = True
    except TimeoutError as ex:
        log(str(ex))
        back = False
    check("il passe l'ecran de mort et revient en vie", back)
    s = state(A)
    check("il est toujours chez l'host, pas en voyage", (s.get("zone") or {}).get("uid") == HOME and not s.get("awayZone"))
    check("l'host le voit en vie sur sa carte",
          eventually(lambda: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); '
                                   'return (c != null && !c.isDead).ToString();') == "True", timeout=15))


def d2(ctx):
    """apres sa mort, le client peut repartir seul"""
    check("le jeu du client n'attend plus un \"retour apres la mort\"", ev(A, "EClass.player.deathZoneMove.ToString()") == "False")
    move(A, VERNIS)
    ok = eventually(client_settled(A, VERNIS, True), timeout=60)
    check("il part seul a Vernis", ok)
    if ok:
        move(A, HOME)
        both_joined(H, A, HOME)


def d3(ctx):
    """ce que la mort a fait tomber existe des deux cotes"""
    me = ctx["a"]
    time.sleep(3)
    mine, hosts = around(A, me), around(H, me)
    log(f"autour du client, chez lui   : {mine}")
    log(f"autour du client, chez l'host : {hosts}")
    check("les memes objets autour du client, chez lui et chez l'host", mine == hosts)
    gold_a = int(ev(A, 'EClass.pc.GetCurrency("money").ToString()'))
    gold_h = int(ev(H, f'{FIND}({me}).GetCurrency("money").ToString()'))
    check(f"le meme or des deux cotes (avant la mort {ctx['gold']}, client {gold_a}, host {gold_h})", gold_a == gold_h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": state(A)["pc"]["uid"]}
    # l'ordre compte : D3 regarde l'endroit de la mort avant que D2 n'emmene le client ailleurs
    steps = [d1, d3, d2]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
            for name, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
