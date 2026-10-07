"""Les fenetres flottantes d'un joueur (sac, aptitudes) restent ouvertes, au meme endroit, quand il change de carte
ou recoit une copie du monde (dev/PLAN_fenetres_invite.md). Deux fenetres.

    python _tools/mp_test.py             # une fois : host + 1 client dans la Prairie
    python _tools/windows_suite.py       # 4 a 6 minutes, relancable (finit avec tout le monde a la Prairie)

W0  l'host et A ouvrent le sac et les aptitudes (l'appel que fait la touche : `ui.ToggleInventory()`,
    `ui.ToggleAbility()`, ActionMode.cs:745-768) et les deplacent comme a la souris ; A choisit un type de combat
    automatique qui n'est pas celui de l'host, et coche ses deux consignes de compagnons a l'inverse de l'host
W1  l'host sort sur la carte du monde, A le suit : fenetres ouvertes des deux cotes, une fois, meme place
W2  A entre seul a Vernis : idem chez A
W3  A revient aupres de l'host (copie du monde : `core.game` remplace) : idem chez A ; son memo est le sien
W4  retour a la Prairie : idem des deux cotes
W5  A quitte la partie et la rejoint, ce qu'il gardait en memoire efface : il retrouve tout d'apres son fichier
    (`ElinMP/OwnSettings`, voir Helper/OwnSettings.cs)

Apres chaque etape (`own_combat`) : le type de combat automatique de A est le sien, et c'est celui que son
personnage applique (`pc.tactics.source`) ; celui de l'host n'a pas bouge. Chez l'host, la copie de A ne porte pas
de type de combat (le combat automatique d'un joueur tourne dans son propre jeu) : ce que l'host garde de A, ce
sont ses deux consignes (`emp_tactics`, PlayerTacticsDelta), verifiees ici ; elles prouvent que A ne lui a pas
redit celles de l'host apres une copie du monde.

Ce que le banc ne joue pas comme un joueur :
- le type de combat et les consignes sont poses comme le fait le menu de l'onglet strategie
  (ContentTactics.cs:67-71 et 140-147), sans ouvrir la fenetre du personnage ; aucun combat n'est joue ;
- W5 : une vraie reprise apres avoir ferme le jeu n'est pas jouee, la memoire est effacee a la main ;
- les fenetres sont ouvertes par l'appel de la touche, pas par la touche ; deplacees en posant la position que
  pose le glisser de la souris (`Window.ProcessMovement` : `transform.position` puis `ClampToScreen`) ;
- A entre a Vernis par `player.EnterLocalZone(case de Vernis)` sans marcher jusqu'a la case ; les sorties passent
  par `player.ExitBorder()`, le vrai chemin du bord de carte ;
- pas de sac ouvert dans le sac si le personnage n'en porte pas (la liste des conteneurs ouverts est comparee,
  elle peut etre vide) ; pas de mort, pas de coffre de la carte ouvert au depart.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot  # noqa: E402
from place_suite import ENTER, back_home, game_id, region_uid  # noqa: E402
from travel_suite import (RESULTS, VERNIS, both_joined, check, client_settled, ev, scan_logs, wait,  # noqa: E402
                          zone_uid)

H, A = 27551, 27552
MEMO = "fenetres-" + str(int(time.time()))

OPEN = ('if (!EClass.ui.IsInventoryOpen) EClass.ui.ToggleInventory(); '
        'if (!EClass.ui.IsAbilityOpen) EClass.ui.ToggleAbility(); "ok"')

# le glisser de la souris : la position, puis le bord de l'ecran ; rien n'est ecrit dans la sauvegarde ici
DRAG = ('var f = EClass.ui.layerFloat.layers; '
        'var i = f.OfType<LayerInventory>().First(l => l.mainInv).windows[0]; '
        'var a = f.OfType<LayerAbility>().First().windows[0]; '
        'i.transform.position += new UnityEngine.Vector3(-150f, 70f, 0f); i.ClampToScreen(); '
        'a.transform.position += new UnityEngine.Vector3(120f, -90f, 0f); a.ClampToScreen(); "ok"')

# nombre@x,y,largeur,hauteur du sac | idem des aptitudes | conteneurs portes ouverts
SEEN = ('var f = EClass.ui.layerFloat.layers; '
        'var i = f.OfType<LayerInventory>().Where(l => l.mainInv).ToList(); '
        'var a = f.OfType<LayerAbility>().ToList(); '
        'System.Func<Layer, string> at = l => { var w = l.windows[0]; var r = (UnityEngine.RectTransform)w.transform; '
        'return (int)w.transform.position.x + "," + (int)w.transform.position.y + "," + (int)r.sizeDelta.x + "," + (int)r.sizeDelta.y; }; '
        'var b = LayerInventory.listInv.Select(l => l.GetPlayerContainer()).Where(c => c != null).Select(c => c.uid).OrderBy(u => u); '
        'i.Count + "@" + (i.Count > 0 ? at(i[0]) : "") + "|" + a.Count + "@" + (a.Count > 0 ? at(a[0]) : "") + "|" + string.Join(",", b)')


# le choix du menu deroulant de l'onglet strategie : un type offert au joueur, ni celui de l'host ni le sien
PICK = ('var r = EClass.sources.tactics.rows.First(t => t.tag.Contains("pc") && t.id != "{host}" '
        '&& t.id != EClass.game.config.autoCombat.idType); '
        'EClass.game.config.autoCombat.idType = r.id; EClass.pc._tactics = null; r.id')
# le reglage / celui que le personnage applique en combat
COMBAT = 'EClass.game.config.autoCombat.idType + "/" + EClass.pc.tactics.source.id'
# les deux consignes des compagnons : 1 = garder ses distances, 2 = ne pas vagabonder
BOXES = 'var t = EClass.game.config.tactics; ((t.allyKeepDistance ? 1 : 0) + (t.dontWander ? 2 : 0)).ToString()'
SET_BOXES = 'var t = EClass.game.config.tactics; t.allyKeepDistance = {keep}; t.dontWander = {wander}; "ok"'
# ce que l'host a retenu des consignes d'un joueur, sur sa copie (0 : jamais dit)
HELD = '(EClass.game.cards.globalCharas.Find({uid})?.GetInt("emp_tactics") ?? -1).ToString()'
FORGET = ('HarmonyLib.AccessTools.Field(HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.OwnSettings"), '
          '"_kept").SetValue(null, null); "ok"')


def own_combat(ctx, step, host=True):
    # A redit ses consignes a l'host toutes les 10 s (RemoteTacticsPatch) : le temps qu'une mauvaise arrive
    time.sleep(12)
    kind, boxes = ctx["kind"], ctx["boxes"]
    now = ev(A, COMBAT)
    check(f"{step}, A : son type de combat automatique, applique par son personnage ({kind} -> {now})",
          now == f"{kind}/{kind}")
    check(f"{step}, A : ses consignes de compagnons ({boxes} -> {ev(A, BOXES)})", ev(A, BOXES) == str(boxes))
    if not host:
        return
    held = ev(H, HELD.format(uid=ctx["uid"]))
    check(f"{step}, host : les consignes de A sur sa copie ({1 + boxes} -> {held})", held == str(1 + boxes))
    now = ev(H, COMBAT)
    check(f"{step}, host : son propre type de combat n'a pas bouge ({ctx['host_kind']} -> {now})",
          now == f"{ctx['host_kind']}/{ctx['host_kind']}")
    check(f"{step}, host : ses propres consignes n'ont pas bouge", ev(H, BOXES) == str(ctx["host_boxes"]))


def seen(port):
    """((nombre, [x, y, l, h]) du sac, idem des aptitudes, conteneurs ouverts)."""
    inv, ab, bags = ev(port, SEEN).split("|")

    def part(text):
        count, _, rect = text.partition("@")
        return int(count), [int(v) for v in rect.split(",")] if rect else []

    return part(inv), part(ab), bags


def same_place(a, b):
    return len(a) == len(b) == 4 and all(abs(x - y) <= 3 for x, y in zip(a, b))


def still_open(who, port, before, step):
    now = seen(port)
    for name, (count, rect), (_, ref) in (("sac", now[0], before[0]), ("aptitudes", now[1], before[1])):
        check(f"{step}, {who} : {name} ouvert une fois (vu {count})", count == 1)
        check(f"{step}, {who} : {name} a la meme place et a la meme taille ({ref} -> {rect})", same_place(rect, ref))
    check(f"{step}, {who} : memes conteneurs portes ouverts ('{before[2]}' -> '{now[2]}')", now[2] == before[2])


def w0(ctx):
    back_home()
    for who, port in (("host", H), ("A", A)):
        floating = ev(port, '(EClass.game.altInv && EClass.game.altAbility).ToString()') == "True"
        if not check(f"{who} : le sac et les aptitudes sont des fenetres flottantes (reglage du jeu)", floating):
            raise RuntimeError("sans fenetres flottantes il n'y a rien a verifier")
        ev(port, OPEN)
        time.sleep(1)
        ev(port, DRAG)
        time.sleep(1)
        ctx[port] = seen(port)
        check(f"{who} : sac et aptitudes ouverts ({ctx[port]})", ctx[port][0][0] == 1 and ctx[port][1][0] == 1)
    ev(A, f'EClass.player.memo = "{MEMO}"; "ok"')

    ctx["uid"] = ev(A, 'EClass.pc.uid.ToString()')
    ctx["host_kind"] = ev(H, 'EClass.game.config.autoCombat.idType')
    ctx["host_boxes"] = int(ev(H, BOXES))
    ctx["kind"] = ev(A, PICK.format(host=ctx["host_kind"]))
    ctx["boxes"] = 3 - ctx["host_boxes"]
    ev(A, SET_BOXES.format(keep=str(ctx["boxes"] & 1 != 0).lower(), wander=str(ctx["boxes"] & 2 != 0).lower()))
    check(f"A : un type de combat automatique autre que celui de l'host ({ctx['host_kind']} / {ctx['kind']})",
          ctx["kind"] != ctx["host_kind"])
    own_combat(ctx, "W0 depart")


def w1(ctx):
    region = region_uid(H)
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
    time.sleep(4)
    game = game_id(A)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, A, region)
    time.sleep(3)
    log(f"A suit l'host : monde {'recharge' if game_id(A) != game else 'garde'}")
    still_open("host", H, ctx[H], "W1 l'host change de carte")
    still_open("A", A, ctx[A], "W1 A suit l'host")
    own_combat(ctx, "W1 A suit l'host")
    shot("w1-A", A)


def w2(ctx):
    ev(A, ENTER.format(uid=VERNIS))
    wait(client_settled(A, VERNIS, True), "A seul a Vernis", timeout=180)
    time.sleep(3)
    still_open("A", A, ctx[A], "W2 A part seul a Vernis")
    own_combat(ctx, "W2 A part seul a Vernis")
    shot("w2-A", A)


def w3(ctx):
    region = region_uid(H)
    game = game_id(A)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, A, region)
    time.sleep(3)
    check("W3 : A a bien recu une copie du monde (sinon l'etape ne prouve rien)", game_id(A) != game)
    still_open("A", A, ctx[A], "W3 A revient aupres de l'host")
    check("W3 : le memo de A est le sien, pas celui de l'host", ev(A, 'EClass.player.memo') == MEMO)
    still_open("host", H, ctx[H], "W3 l'host, temoin")
    own_combat(ctx, "W3 A revient aupres de l'host")
    shot("w3-A", A)


def w4(ctx):
    back_home()
    time.sleep(3)
    still_open("host", H, ctx[H], "W4 retour a la Prairie")
    still_open("A", A, ctx[A], "W4 retour a la Prairie")
    own_combat(ctx, "W4 retour a la Prairie")
    shot("w4-A", A)


def w5(ctx):
    from chara_suite import connect_unasked, in_game, leave
    leave()
    # quitter la partie a ecrit le fichier ; sans ceci A reprendrait ce qu'il garde en memoire
    ev(A, FORGET)
    # le jeu sait a qui est le personnage : plus d'ecran de choix a la reconnexion
    check("W5 : A revient sans qu'on lui demande quel personnage", connect_unasked())
    check("W5 : A rejoint la partie avec le meme personnage", str(in_game()) == ctx["uid"])
    still_open("A", A, ctx[A], "W5 A rejoint la partie")
    check("W5 : le memo de A est le sien", ev(A, 'EClass.player.memo') == MEMO)
    own_combat(ctx, "W5 A rejoint la partie")
    shot("w5-A", A)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [w0, w1, w2, w3, w4, w5]
    if a.only:
        # w0 ouvre les fenetres et note leur place : toujours joue
        steps = [s for s in steps if s is w0 or s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass
            break

    try:
        back_home()
    except Exception as ex:  # noqa: BLE001
        print(f"    retour a la Prairie rate : {type(ex).__name__}: {ex}")

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
