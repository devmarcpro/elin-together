"""Chasse aux defauts dans les dialogues : chaque joueur parle a chaque personnage de la carte et essaie chaque choix
du menu, comme un joueur curieux. Rien n'est attendu d'un dialogue en particulier : la suite cherche ce qui serait
un defaut dans n'importe lequel (le retour de testeurs du 8 octobre 2026 : un dialogue qui tournait en boucle et
redonnait ses cadeaux).

    python _tools/mp_test.py                         # ou first_time_suite.py --keep, ou n'importe quelle partie a deux
    python _tools/dialog_walk_suite.py               # l'invite puis l'host, tous les personnages de la carte
    python _tools/dialog_walk_suite.py --who guest --max 6

Pour chaque choix du premier menu d'un personnage : le dialogue est avance ligne par ligne ; aux menus suivants le
dernier choix est pris (retour, au revoir). Est compte comme un defaut :
  - une boucle : la meme etape rejouee plus de 3 fois, ou plus de 40 clics sans revenir a un menu
  - une erreur du jeu pendant le dialogue (exception dans la reponse du pont, ou dans les journaux a la fin)
  - apres le dialogue, les deux jeux ne sont plus d'accord : quetes d'histoire et leur etape, objets au sol de la
    carte (par sorte), or de chaque joueur
  - un objet en double (meme numero, deux objets)
Ce que la suite ne sait pas : si ce que le dialogue a fait est « juste ». Elle note ce que chaque choix a change
(quetes, objets, or) pour qu'un humain le relise.

Pas comme un joueur : lignes avancees par ce que fait le clic (suite, ou saut de la ligne), choix cliques par leur onClick."""
import argparse
import sys
import time
from datetime import datetime, timezone

from bot import doubles, settle
from mp_test import log, state
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
LIMIT = 40

# quetes d'histoire et leur etape | objets au sol par sorte | or des joueurs
WORLD = ('var personal = ElinTogether.Net.NetSession.Instance.Rules.UsePersonalQuests; '
         'var q = string.Join(",", EClass.game.quests.list.Where(x => !personal || !x.IsRandomQuest).Select(x => x.id + ":" + x.phase).OrderBy(x => x)); '
         'var o = string.Join(",", EClass.game.quests.globalList.Select(x => x.id).OrderBy(x => x)); '
         'var t = string.Join(",", EClass._map.things.Where(x => x.placeState == PlaceState.roaming).GroupBy(x => x.id).OrderBy(g => g.Key).Select(g => g.Key + "x" + g.Sum(x => x.Num))); '
         'var g = string.Join(",", new[] { %s }.Select(u => EClass._map.charas.Find(c => c.uid == u)).Where(c => c != null).OrderBy(c => c.uid).Select(c => c.uid + "=" + c.GetCurrency("money"))); '
         # qui est sur la carte, et a qui : la faction du joueur (residents, compagnons) et les autres
         'var p = EClass._map.charas.Count(c => !c.isDead) + " dont " + EClass._map.charas.Count(c => !c.isDead && c.IsPCFaction) + " de la base"; '
         'return "quetes[" + q + "] offres[" + o + "] sol[" + t + "] or[" + g + "] gens[" + p + "]";')
SUB = 8
WHERE = ('var d = LayerDrama.Instance; if (d == null) return "ferme"; var top = EClass.ui.layers.LastOrDefault(); '
         'if (!(top is LayerDrama)) return "autre:" + top.GetType().Name; '
         'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(false).Where(x => x.interactable).Select(x => string.Join(" ", x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Select(t => t.text).Where(t => t.Length > 3))).Where(t => t.Length > 0); '
         # (l'etape, puis le numero de la ligne en cours : la meme ligne revue plusieurs fois est une boucle)
         'return d.drama.sequence.lastStep + "#" + HarmonyLib.Traverse.Create(d.drama.sequence).Field("currentEventID").GetValue() + "|" + string.Join("|", b);')
PICK = ('var d = LayerDrama.Instance; if (d == null) return "ferme"; '
        'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(false).Where(x => x.interactable && x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Length > 3)).ToList(); '
        'var i = %d; if (i < 0) i = b.Count + i; if (i < 0 || i >= b.Count) return "pas de choix"; b[i].onClick.Invoke(); return "clic";')
NEXT = ('var d = LayerDrama.Instance; if (d == null) return "ferme"; var s = d.drama.sequence; '
        # ce que fait le clic sur une ligne (DramaEventTalk.Play) : la suite, ou le saut que la ligne porte
        'var t = HarmonyLib.Traverse.Create(s).Field("currentEvent").GetValue() as DramaEventTalk; if (t == null) return "attend"; '
        'if (t.temp) s.tempEvents.Clear(); if (t.idJump.IsEmpty()) s.PlayNext(); else s.Play(t.idJump); return "suite";')
CLOSE = 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"'
PEOPLE = ('string.Join(";", EClass._map.charas.Where(c => !c.IsPC && !c.GetBool("remote_chara") && !c.isDead && !c.IsHostile() && c.host == null)'
          '.OrderBy(c => c.pos.Distance(EClass.pc.pos)).Select(c => c.uid + "," + c.id + "," + c.Name.Replace(";", " ").Replace(",", " ")))')


LINES = []


def where(port):
    step, _, rest = ev(port, WHERE).partition("|")
    step, _, line = step.partition("#")
    LINES.append(line)
    return step, [c for c in rest.split("|") if c]


def open_dialog(port, uid):
    who = f'EClass._map.charas.Find(x => x.uid == {uid})'
    if ev(port, f'({who} != null).ToString()') != "True":
        return False
    far = lambda: int(ev(port, f'var c = {who}; return c == null ? "99" : EClass.pc.pos.Distance(c.pos).ToString();'))  # noqa: E731
    for _ in range(3):
        # (le personnage bouge, ou la case visee vient d'etre prise : le joueur recliquerait)
        ev(port, f'var c = {who}; EClass.pc.SetAIImmediate(new AI_Goto(c.pos.Copy(), 1)); "ok"')
        if eventually(lambda: far() <= 1, timeout=15):
            break
    if far() > 1:
        return False
    ev(port, f'if (EClass.pc.ai != null) EClass.pc.ai.Cancel(); {who}.ShowDialog(); "ok"')
    return eventually(lambda: ev(port, '(LayerDrama.Instance != null).ToString()') == "True", timeout=8)


def to_menu(port, picks=()):
    """Avance jusqu'a un menu (ou la fin), en prenant `picks` aux menus rencontres, dans l'ordre.
    Renvoie (probleme ou None, etape, choix, etapes vues, clics)."""
    seen, picks, clicked, waited = [], list(picks), [], 0
    for clicks in range(LIMIT + 1):
        step, choices = where(port)
        seen.append(step)
        line = LINES[-1]
        if step == "ferme":
            return None, step, [], seen, clicks
        if step.startswith("autre:"):
            # le choix ouvre une autre fenetre du jeu (boutique, liste...) : hors de cette chasse
            return None, step, [], seen, clicks
        if choices:
            if not picks:
                return None, step, choices, seen, clicks
            ev(port, PICK % picks.pop(0))
        elif ev(port, NEXT) == "suite":
            clicked.append(line)
            if clicked.count(line) >= 3:
                return f"boucle : la ligne {line} de l'etape {step} est rejouee pour la {clicked.count(line)}e fois ({clicks} clics)", step, choices, seen, clicks
        else:
            # le dialogue attend autre chose qu'un clic (une saisie, une animation) : pas un defaut, on n'insiste pas
            waited += 1
            if waited > 6:
                return None, step + " (attend autre chose qu'un clic)", [], seen, clicks
        time.sleep(0.9)
    return f"pas de menu ni de fin apres {LIMIT} clics (etapes {sorted(set(seen))})", step, [], seen, LIMIT


def leave(port):
    """Sort du dialogue comme le joueur : le dernier choix de chaque menu, puis ferme ce qui reste."""
    for _ in range(4):
        step, choices = where(port)
        if step == "ferme" or step.startswith("autre:") or not choices:
            break
        ev(port, PICK % -1)
        time.sleep(0.9)
        to_menu(port)
    ev(port, CLOSE)
    time.sleep(1.5)


def diff(before, after):
    return "rien" if before == after else f"{before}  ->  {after}"


def walk(port, name, uid, chara_id, label, problems, world):
    if not open_dialog(port, uid):
        log(f"{name} : {label} ({chara_id}) ne se laisse pas approcher ou n'ouvre pas de dialogue")
        ev(port, CLOSE)
        return 0
    problem, step, root, seen, _ = to_menu(port)
    if problem:
        problems.append(f"{name} parle a {label} ({chara_id}) : {problem}")
    leave(port)
    tried = 0
    # chaque choix du premier menu, puis chaque choix du menu qu'il ouvre (pas plus profond)
    paths = [((i,), choice[:40]) for i, choice in enumerate(root)]
    while paths:
        picks, told = paths.pop(0)
        before = ev(H, world)
        if not open_dialog(port, uid):
            break
        problem, step2, sub, seen2, clicks = to_menu(port, picks)
        if len(picks) == 1 and sub and step2 != step:
            paths[0:0] = [(picks + (j,), f"{told} > {c[:40]}") for j, c in enumerate(sub[:SUB])]
        leave(port)
        tried += 1
        same, wh, wa = settle(lambda: ev(H, world), lambda: ev(A, world), timeout=12)
        log(f"{name} > {label} > « {told} » : {clicks} clics, fin a {step2} ; chez l'host : {diff(before, wh)[:500]}")
        if problem:
            problems.append(f"{name} > {label} ({chara_id}) > « {told} » : {problem}")
        if not same:
            problems.append(f"{name} > {label} ({chara_id}) > « {told} » : les deux jeux ne sont plus d'accord, host {wh[:400]} / invite {wa[:400]}")
        for p, n in ((H, "host"), (A, "invite")):
            twice = doubles(p)
            if twice:
                problems.append(f"{name} > {label} > « {told} » : objets en double chez l'{n} ({twice})")
    return tried


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", choices=["guest", "host", "both"], default="both")
    ap.add_argument("--max", type=int, default=12, help="nombre de personnages, les plus proches d'abord")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for port in (H, A):
        ev(port, CLOSE)
    same = state(H)["zone"]["uid"] == state(A)["zone"]["uid"]
    if not check("les deux joueurs sont sur la meme carte", same):
        return finish(t0)
    # l'or des deux joueurs, lu dans chaque jeu par leur numero
    world = WORLD % f'{int(state(H)["pc"]["uid"])}, {int(state(A)["pc"]["uid"])}'
    players = [(A, "l'invite"), (H, "l'host")] if a.who == "both" else [(A, "l'invite")] if a.who == "guest" else [(H, "l'host")]
    for port, name in players:
        people = [p.split(",") for p in ev(port, PEOPLE).split(";") if p][:a.max]
        problems, tried = [], 0
        for uid, chara_id, label in people:
            try:
                tried += walk(port, name, int(uid), chara_id, label, problems, world)
            except Exception as ex:  # noqa: BLE001
                problems.append(f"{name} > {label} ({chara_id}) : erreur du jeu pendant le dialogue ({type(ex).__name__}: {str(ex)[:200]})")
                try:
                    ev(port, CLOSE)
                except Exception:  # noqa: BLE001
                    pass
        check(f"{name} a parle a {len(people)} personnages et essaye {tried} choix : {len(problems)} defaut(s)", not problems)
        for p in problems:
            check(p, False)
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
