"""Combat au rythme de chaque joueur : host + 2 clients A, B, tous dans la Prairie.

    python _tools/combat_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/combat_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

F1  un monstre qui attaque A vit sur l'horloge de A ; un PNJ sans combat reste en temps normal
F2  A ne fait rien, B se promene (le monde tourne) : le monstre de A n'agit pas, le PNJ libre si
F3  A passe des tours : son monstre agit
F6  A surcharge : son monstre joue au rythme de la vraie vitesse de A (celle de son jeu)
F4  un monstre qui attaque l'host : il n'agit que quand l'host joue, pas quand A joue
F5  option decochee (et tour par tour decoche) : le monstre de A agit pendant que B se promene, comme avant
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from companion_suite import walk_away  # noqa: E402
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

FIND = "EClass.game.cards.globalCharas.Find"


def spawn(target_uid, hostile=True):
    """L'host fait apparaitre un putit a cote du perso ; hostile, il le prend pour cible."""
    who = "EClass.pc" if target_uid is None else f"{FIND}({target_uid})"
    fight = ('m.hostility = Hostility.Enemy; m.c_originalHostility = Hostility.Enemy; m.SetEnemy(p); ' if hostile
             else 'm.hostility = Hostility.Neutral; m.c_originalHostility = Hostility.Neutral; ')
    return int(ev(H, f'var p = {who}; var m = CharaGen.Create("putty"); '
                     f'EClass._zone.AddCard(m, p.pos.GetNearestPoint(allowChara: false)); {fight}m.uid.ToString()'))


def turns(uid):
    r = int(ev(H, f'var m = EClass._map.charas.Find(c => c.uid == {uid}); m == null ? "-1" : m.turn.ToString()'))
    if r < 0:
        raise RuntimeError(f"le perso {uid} n'est plus sur la carte")
    return r


def owner(uid):
    """Joueur dont les tours font agir ce perso (0 : temps normal), vu par l'host."""
    return int(ev(H, f'var m = EClass._map.charas.Find(c => c.uid == {uid}); if (m == null) return "-1"; '
                     'var o = HarmonyLib.AccessTools.Method("ElinTogether.Patches.PlayerCombatTime:TimeOwner")'
                     '.Invoke(null, new object[] { m }) as Chara; o == null ? "0" : o.uid.ToString()'))


def keep_fighting(monster, target_uid):
    """Le monstre garde sa cible, la cible reste en vie (le test dure plus qu'un vrai combat)."""
    who = "EClass.pc" if target_uid is None else f"{FIND}({target_uid})"
    ev(H, f'var p = {who}; p.hp = p.MaxHP; var m = EClass._map.charas.Find(c => c.uid == {monster}); '
          'if (m != null) { m.hp = m.MaxHP; m.SetEnemy(p); } "ok"')


def pass_turns(port, n):
    """Le joueur passe n tours (comme la touche attendre)."""
    for _ in range(n):
        ev(port, 'EClass.player.EndTurn(); "ok"')
        time.sleep(0.5)


def set_option(name, value):
    ev(H, 'var entry = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Server"), '
          f'"{name}").GetValue(null); '
          f'HarmonyLib.AccessTools.Property(entry.GetType(), "Value").SetValue(entry, {str(value).lower()}); '
          'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport).Method("UpdateRemoteSessionRules").GetValue(); "ok"')


def f1(ctx):
    ctx["a"], ctx["b"] = state(A)["pc"]["uid"], state(B)["pc"]["uid"]
    # les habitants de la base tuent tout monstre en quelques secondes : carte de test sans eux
    gone = ev(H, 'var list = EClass._map.charas.Where(c => !c.IsPC && !c.GetBool("remote_chara") && c.party == null).ToList(); '
                 'foreach (var c in list) c.Destroy(); list.Count.ToString()')
    log(f"{gone} habitants retires de la carte de test")
    time.sleep(2)
    # chacun dans son coin : cote a cote, un monstre change de cible pour le joueur d'a cote et passe sur son
    # horloge au milieu d'une mesure (F4 et F5 echouaient une fois sur deux pour ca)
    for port, uid, dx, dz in ((A, ctx["a"], 9, 0), (B, ctx["b"], 0, 9)):
        ev(port, f'var p = new Point(EClass.pc.pos.x + {dx}, EClass.pc.pos.z + {dz}).GetNearestPoint(allowBlock: false, allowChara: false); '
                 'EClass.pc.Teleport(p, true, true); "ok"')
        far = lambda u=uid: int(ev(H, f'var c = {FIND}({u}); return c.pos.Distance(EClass.pc.pos).ToString();')) >= 6  # noqa: E731
        check(f"le joueur {uid} se met a l'ecart de l'host", eventually(far, timeout=10))
    ctx["ma"] = spawn(ctx["a"])
    ctx["free"] = spawn(ctx["b"], hostile=False)
    log(f"monstre de A : {ctx['ma']}, PNJ libre : {ctx['free']}")
    time.sleep(2)
    keep_fighting(ctx["ma"], ctx["a"])
    check("le monstre qui attaque A vit sur l'horloge de A", eventually(lambda: owner(ctx["ma"]) == ctx["a"], timeout=10))
    check("un PNJ sans combat reste en temps normal", owner(ctx["free"]) == 0)


def f2(ctx):
    keep_fighting(ctx["ma"], ctx["a"])
    time.sleep(1)
    before = {"ma": turns(ctx["ma"]), "free": turns(ctx["free"])}
    walk_away(B, steps=14, dx=8)
    walk_away(B, steps=14, dx=-8)
    after = {"ma": turns(ctx["ma"]), "free": turns(ctx["free"])}
    log(f"tours pendant que B marche, A immobile : monstre de A +{after['ma'] - before['ma']}, PNJ libre +{after['free'] - before['free']}")
    check("le monde tourne pendant que B marche (le PNJ libre agit)", after["free"] - before["free"] >= 3)
    check("le monstre de A attend A (au plus 1 tour deja en cours)", after["ma"] - before["ma"] <= 1)


def f3(ctx):
    keep_fighting(ctx["ma"], ctx["a"])
    before = turns(ctx["ma"])
    played = int(ev(A, 'EClass.player.stats.turns.ToString()'))
    pass_turns(A, 6)
    check("A a bien joue ses tours", int(ev(A, 'EClass.player.stats.turns.ToString()')) - played >= 5)
    ok = eventually(lambda: turns(ctx["ma"]) - before >= 3, timeout=15)
    log(f"tours du monstre de A pendant 6 tours de A : +{turns(ctx['ma']) - before}")
    check("A joue : son monstre agit", ok)


def f6(ctx):
    """A surcharge : son monstre recoit le temps de la vraie vitesse de A, pas de celle de sa copie chez l'host
    (la copie n'est pas "le joueur" pour le jeu : surchargee elle perd toute sa vitesse, le joueur la moitie)"""
    a, n = ctx.setdefault("a", state(A)["pc"]["uid"]), 12
    mine = spawn(a)
    heavy = ev(H, f'var c = {FIND}({a}); var t = ThingGen.Create("log"); t.SetNum(5000); c.AddThing(t); return t.uid.ToString();')

    def clock():
        """Temps de jeu recu par le monstre, en tours : ceux qu'il a joues, plus ce qui lui reste a jouer."""
        turn, timer, act = ev(H, f'var m = EClass._map.charas.Find(c => c.uid == {mine}); var inv = System.Globalization.CultureInfo.InvariantCulture; '
                                 'return m.turn + "|" + m.roundTimer.ToString(inv) + "|" + m.actTime.ToString(inv);').split("|")
        return int(turn) + float(timer) / float(act)

    try:
        check("A est surcharge au maximum", eventually(lambda: ev(A, 'EClass.pc.burden.GetPhase().ToString()') == "4", timeout=10))
        keep_fighting(mine, a)
        check("le nouveau monstre vit sur l'horloge de A", eventually(lambda: owner(mine) == a, timeout=10))
        time.sleep(3)
        real = int(ev(A, 'EClass.pc.Speed.ToString()'))
        copy = int(ev(H, f'{FIND}({a}).Speed.ToString()'))
        monster = int(ev(H, f'EClass._map.charas.Find(c => c.uid == {mine}).Speed.ToString()'))
        log(f"vitesses : A chez lui {real}, sa copie chez l'host {copy}, le monstre {monster}")
        check("le test distingue les deux calculs (les deux vitesses different nettement)", abs(real - copy) >= 10)
        # un tour de A, tel que l'host le traite a l'arrivee de son message, et le temps que le monstre en recoit,
        # lus dans la meme image : compter des tours joues depend trop du rythme des deux jeux
        used = ev(H, f'var m = EClass._map.charas.Find(c => c.uid == {mine}); var p = {FIND}({a}); '
                     'var inv = System.Globalization.CultureInfo.InvariantCulture; var before = m.roundTimer; '
                     'HarmonyLib.AccessTools.Method("ElinTogether.Patches.PlayerCombatTime:OnPlayerTurn").Invoke(null, new object[] { p }); '
                     'var grant = m.roundTimer - before; if (grant <= 0f) return "rien"; '
                     'var t = HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Patches.SynchronizationContext")); '
                     'var rs = System.Convert.ToSingle(t.Property("RefSpeed").PropertyExists() ? t.Property("RefSpeed").GetValue() : t.Field("RefSpeed").GetValue()); '
                     'return (EClass.player.baseActTime * rs / grant).ToString("0.0", inv);')
        check(f"un tour de A donne a son monstre le temps de la vitesse {used} (celle de A : {real} ; celle de sa copie : {copy})",
              used != "rien" and abs(float(used) - real) <= 2)
    finally:
        ev(H, f'var t = {FIND}({a}).things.Find({heavy}); if (t != null) t.Destroy(); '
              f'EClass._map.charas.Find(c => c.uid == {mine})?.Destroy(); "ok"')
        time.sleep(2)


def f4(ctx):
    ctx["mh"] = spawn(None)
    time.sleep(2)
    keep_fighting(ctx["mh"], None)
    check("le monstre qui attaque l'host vit sur l'horloge de l'host", eventually(lambda: owner(ctx["mh"]) == 1, timeout=10))
    keep_fighting(ctx["ma"], ctx["a"])
    time.sleep(1)
    before = {"mh": turns(ctx["mh"]), "ma": turns(ctx["ma"])}
    pass_turns(A, 6)
    time.sleep(2)
    mid = {"mh": turns(ctx["mh"]), "ma": turns(ctx["ma"])}
    log(f"A joue 6 tours : monstre de l'host +{mid['mh'] - before['mh']}, monstre de A +{mid['ma'] - before['ma']}")
    check("A joue : le monstre de l'host n'agit pas", mid["mh"] - before["mh"] <= 1)
    keep_fighting(ctx["mh"], None)
    pass_turns(H, 6)
    time.sleep(2)
    end = {"mh": turns(ctx["mh"]), "ma": turns(ctx["ma"])}
    log(f"l'host joue 6 tours : monstre de l'host +{end['mh'] - mid['mh']}, monstre de A +{end['ma'] - mid['ma']}")
    check("l'host joue : son monstre agit", end["mh"] - mid["mh"] >= 3)
    check("l'host joue : le monstre de A n'agit pas", end["ma"] - mid["ma"] <= 1)
    ev(H, f'EClass._map.charas.Find(c => c.uid == {ctx["mh"]})?.Destroy(); "ok"')


def f5(ctx):
    set_option("PlayerCombatTime", False)
    set_option("TurnBasedCombat", False)
    time.sleep(3)
    try:
        keep_fighting(ctx["ma"], ctx["a"])
        check("option decochee : plus d'horloge par joueur", owner(ctx["ma"]) == ctx["a"] and
              ev(H, f'var m = EClass._map.charas.Find(c => c.uid == {ctx["ma"]}); if (m == null) return "gone"; '
                    'HarmonyLib.AccessTools.Method("ElinTogether.Patches.PlayerCombatTime:IsBound")'
                    '.Invoke(null, new object[] { m }).ToString()') == "False")
        before = turns(ctx["ma"])
        walk_away(B, steps=14, dx=8)
        walk_away(B, steps=14, dx=-8)
        log(f"option decochee, B marche, A immobile : monstre de A +{turns(ctx['ma']) - before}")
        check("option decochee : le monstre de A agit pendant que B marche, comme avant", turns(ctx["ma"]) - before >= 3)
    finally:
        set_option("PlayerCombatTime", True)
        set_option("TurnBasedCombat", True)
        ev(H, f'EClass._map.charas.Find(c => c.uid == {ctx["ma"]})?.Destroy(); EClass._map.charas.Find(c => c.uid == {ctx["free"]})?.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "2"], check=True)

    ctx = {}
    # F5 en dernier : option decochee, le monstre frappe A en temps reel et finit par le tuer
    steps = [f1, f2, f3, f6, f4, f5]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A), ("B", B)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass
            break

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
