"""Le tout debut de l'histoire, joue par un invite : premiere rencontre avec Ashland, acte lu, puis la hache et l'or.
Retour de testeurs (8 octobre 2026, 0.26.590) : le dialogue d'Ashland tournait en boucle et redonnait la hache et
l'or sans fin, la partie relancee rouvrait le meme dialogue.

    python _tools/mp_test.py            # monde neuf : rien de l'histoire n'est commence
    python _tools/story_start_suite.py

A1  l'invite parle a Ashland pour la premiere fois : un acte de propriete, la quete de la base commence dans les deux
    jeux, le dialogue arrive a son menu
A2  l'acte est lu (ce que le jeu fait apres la revendication, chez l'host) : la quete principale passe a 200 dans
    les deux jeux
A3  l'invite reparle a Ashland : une hache, dix lingots, la quete principale a 250 et celle de la base a 2 dans les
    deux jeux, les trois quetes d'Ashland proposees une fois, le dialogue arrive a son menu
A4  l'invite lui reparle : le menu tout de suite, rien n'est redonne

Ce que le banc ne joue pas comme un joueur : il avance le dialogue par ce que fait le clic (suite, ou saut de la ligne), sans la souris, il ne
lit pas l'acte (le monde de test est deja revendique : il appelle les deux ChangePhase que TraitDeed.OnRead fait),
et il ne ferme pas puis ne relance pas la partie."""
import sys
import time
from datetime import datetime, timezone

from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
CLICKS = 15

QUESTS = ('var m = EClass.game.quests.Get<QuestMain>(); var h = EClass.game.quests.Get<QuestHome>(); '
          'var f = EClass.player.dialogFlags.ContainsKey("ash1") ? EClass.player.dialogFlags["ash1"] : 0; '
          'var o = string.Join(",", EClass.game.quests.globalList.GroupBy(q => q.id).OrderBy(g => g.Key).Select(g => g.Key + "x" + g.Count())); '
          'return "main=" + (m == null ? "none" : m.phase.ToString()) + " home=" + (h == null ? "none" : h.phase.ToString()) + " ash1=" + f + " offres=[" + o + "]";')
# sur la carte et dans les sacs des joueurs, vus de ce jeu
COUNT = ('System.Func<string, int> n = id => EClass._map.things.Where(t => t.id == id).Sum(t => t.Num) + '
         'EClass._map.charas.Where(c => c.IsPC || c.GetBool("remote_chara")).SelectMany(c => c.things).Where(t => t.id == id).Sum(t => t.Num); '
         'return n("deed") + "," + n("axe") + "," + n("money2");')
WHERE = ('var d = LayerDrama.Instance; if (d == null) return "ferme"; '
         'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(false).Count(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Length > 3)); '
         'return d.drama.sequence.lastStep + "|" + b;')
NEXT = ('var d = LayerDrama.Instance; if (d == null) return "ferme"; var s = d.drama.sequence; '
        # ce que fait le clic sur une ligne (DramaEventTalk.Play) : la suite, ou le saut que la ligne porte
        'var t = HarmonyLib.Traverse.Create(s).Field("currentEvent").GetValue() as DramaEventTalk; if (t == null) return "attend"; '
        'if (t.temp) s.tempEvents.Clear(); if (t.idJump.IsEmpty()) s.PlayNext(); else s.Play(t.idJump); return "suite";')
HANG_UP = 'if (LayerDrama.Instance != null) EClass.ui.RemoveLayer<LayerDrama>(); "ok"'


def count(port):
    return [int(x) for x in ev(port, COUNT).split(",")]


def talk(ash):
    """L'invite parle a Ashland et avance le dialogue jusqu'a un choix : renvoie (etape atteinte, etapes vues, clics)."""
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {ash}); EClass.pc.Teleport(c.pos.GetNearestPoint(false, false), true, true); "ok"')
    time.sleep(2)
    ev(A, f'EClass._map.charas.Find(x => x.uid == {ash}).ShowDialog(); "ok"')
    eventually(lambda: ev(A, '(LayerDrama.Instance != null).ToString()') == "True", timeout=10)
    time.sleep(1)
    seen = []
    for clicks in range(CLICKS + 1):
        step, _, choices = ev(A, WHERE).partition("|")
        if step not in seen:
            seen.append(step)
        if step == "ferme" or int(choices or 0) > 0:
            return step, seen, clicks
        ev(A, NEXT)
        time.sleep(1.2)
    return step, seen, clicks


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for port in (H, A):
        ev(port, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
    ash = ev(A, 'var c = EClass._map.charas.Find(x => x.id == "ashland"); return c == null ? "" : c.uid.ToString();')
    start = ev(H, QUESTS)
    if not check(f"monde neuf, Ashland sur la carte ({ash or 'absent'}), histoire pas commencee chez l'host ({start})",
                 bool(ash) and "main=0 home=none ash1=0" in start):
        return finish(t0)

    before = count(H)
    step, seen, clicks = talk(ash)
    check(f"A1 premiere rencontre : le dialogue arrive a son menu ({step}) en {clicks} clics, etapes {seen}",
          step == "main" and seen[0] == "start_FirstMeet" and clicks < CLICKS)
    ev(A, HANG_UP)
    eventually(lambda: "home=0 ash1=1" in ev(H, QUESTS), timeout=15)
    h, a, got = ev(H, QUESTS), ev(A, QUESTS), count(H)
    check(f"A1 la quete de la base est commencee et la rencontre notee, host ({h}) et invite ({a})",
          "home=0 ash1=1" in h and "home=0 ash1=1" in a)
    check(f"A1 un acte de propriete et un seul (chez l'host : {before[0]} -> {got[0]})", got[0] - before[0] == 1)

    ev(H, 'EClass.game.quests.Home.ChangePhase(1); EClass.game.quests.Main.ChangePhase(200); "ok"')
    eventually(lambda: "main=200 home=1" in ev(A, QUESTS), timeout=15)
    h, a = ev(H, QUESTS), ev(A, QUESTS)
    check(f"A2 acte lu : quete principale a 200 et base a 1, host ({h}) et invite ({a})",
          "main=200 home=1" in h and "main=200 home=1" in a)

    before = count(H)
    step, seen, clicks = talk(ash)
    check(f"A3 apres l'acte : le dialogue arrive a son menu ({step}) en {clicks} clics, etapes {seen}",
          step == "main" and seen[0] == "start_AfterReadDeed" and clicks < CLICKS)
    ev(A, HANG_UP)
    want = "main=250 home=2"
    eventually(lambda: want in ev(H, QUESTS) and want in ev(A, QUESTS), timeout=15)
    h, a, got = ev(H, QUESTS), ev(A, QUESTS), count(H)
    check(f"A3 quete principale a 250 et base a 2, host ({h}) et invite ({a})", want in h and want in a)
    offers = "offres=[crafterx1,defensex1,sharedContainerx1]"
    check(f"A3 les trois quetes d'Ashland sont proposees une fois chacune, host et invite ({a})", offers in h and offers in a)
    check(f"A3 une hache et une seule (chez l'host : {before[1]} -> {got[1]}), dix lingots ({before[2]} -> {got[2]})",
          got[1] - before[1] == 1 and got[2] - before[2] == 10)

    before = got
    step, seen, clicks = talk(ash)
    ev(A, HANG_UP)
    time.sleep(3)
    got = count(H)
    check(f"A4 il lui reparle : le menu tout de suite ({seen}, {clicks} clic), rien n'est redonne ({before} -> {got})",
          seen == ["main"] and got == before)
    finish(t0)


def finish(t0):
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
