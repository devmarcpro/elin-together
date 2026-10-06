"""Rejoindre avec un personnage d'une de ses sauvegardes solo. Test court (host + 1 client a la Prairie).

    python _tools/mp_test.py
    python _tools/import_suite.py     # ~4 minutes, finit avec le client en jeu sur son premier personnage

Demande de l'utilisateur le 2026-10-03. Tout passe par le vrai menu de connexion (les boutons sont cliques).
La sauvegarde "solo" est une copie du monde de test (world_import) : le meme personnage que celui de l'host,
ce qui donne de quoi comparer (niveau, or, equipement, sac) et le pire cas pour les numeros d'objets (tous
deja pris chez l'host).

I1  case cochee : l'ecran propose "un personnage d'une de mes sauvegardes", puis la liste des sauvegardes
I2  il choisit world_import : il joue ce personnage (nom, niveau, or, equipement, sac, renommee, karma),
    aucun numero en double chez l'host, la sauvegarde n'a pas change d'un octet
I3  il revient et redemande la meme sauvegarde : refuse (un seul exemplaire par joueur), rien de plus chez l'host
I4  il revient : son personnage importe est dans la liste, comme les autres
I5  case decochee : le choix n'est plus propose
I6  une sauvegarde du nuage Steam (un dossier avec index.txt et cloud.zip, comme le jeu les range entre deux
    sessions) est dans la liste, se lit sans etre deballee ni modifiee, et donne le meme personnage
"""
import hashlib
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chara_suite import CHOICES, click, connect, in_game, leave, roster  # noqa: E402
from combat_suite import set_option  # noqa: E402
from mp_test import PRISTINE, SAVES, log, shot, state, wait  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
SOLO = SAVES / "world_import"
CLOUD = SAVES.parent / "Cloud Save" / "world_importcloud"
IMPORT = "A character from one of my saves"
TITLE = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); '
         'return d == null ? "" : d.textDetail.text;')

# nom | niveau | or | objets equipes (identifiants tries) | tout ce qu'il porte, sacs compris (identifiant x nombre)
SHEET = ('{0}.Name + "|" + {0}.LV + "|" + {0}.GetCurrency("money") + "|" + '
         'string.Join(",", {0}.body.slots.Where(s => s.thing != null).Select(s => s.thing.id).OrderBy(x => x)) + "|" + '
         'string.Join(",", {0}.things.Flatten().Select(t => t.id + "x" + t.Num).OrderBy(x => x))')


def same(sheet, reference):
    """La meme fiche, a la hache pres : le mod en offre une a tout invite qui n'en a pas."""
    if sheet == reference:
        return True
    head, _, bag = sheet.rpartition("|")
    ref_head, _, ref_bag = reference.rpartition("|")
    items = bag.split(",")
    if "axex1" in items and "axex1" not in ref_bag.split(","):
        items.remove("axex1")
    return head == ref_head and items == ref_bag.split(",")
# les numeros du personnage et de tout ce qu'il porte
UIDS = '{0}.uid + "," + string.Join(",", {0}.things.Flatten().Select(t => t.uid))'


def digest():
    h = hashlib.sha256()
    for path in sorted(SOLO.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(SOLO)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def tree(root):
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        h.update(str(path.relative_to(root)).encode())
        if path.is_file():
            h.update(path.read_bytes())
    return h.hexdigest()


def make_cloud():
    """La meme copie, rangee comme une sauvegarde du nuage : index.txt a cote de cloud.zip (tout le dossier)."""
    shutil.rmtree(CLOUD, ignore_errors=True)
    CLOUD.mkdir(parents=True)
    shutil.copy(PRISTINE / "index.txt", CLOUD / "index.txt")
    shutil.make_archive(str(CLOUD / "cloud"), "zip", PRISTINE)


def choices():
    return [c for c in ev(A, CHOICES).split("|") if c]


def pick(text):
    """Clique le choix dont le texte contient `text` ; renvoie les choix proposes."""
    found = choices()
    index = next((i for i, c in enumerate(found) if text in c), None)
    if index is None:
        raise RuntimeError(f"choix \"{text}\" absent de {found}")
    click(index)
    return found


def host_chara(uid):
    return f"EClass.game.cards.globalCharas.Find({uid})"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        if not state(A)["connected"]:
            from mp_test import join_client
            join_client(H, A, "client")
        first = state(A)["pc"]["uid"]
        # l'ecran de choix ne s'ouvre plus tout seul (conseil 9, A1) : la case de l'host, pour toute la suite
        set_option("ChooseCharacter", True)

        shutil.rmtree(SOLO, ignore_errors=True)
        shutil.copytree(PRISTINE, SOLO, copy_function=shutil.copy)
        before = digest()
        # le personnage de l'host vient de la meme sauvegarde : c'est la reference
        sheet = ev(H, SHEET.format("EClass.pc"))
        standing = ev(H, 'EClass.player.fame + "|" + EClass.player.karma')
        log(f"reference (host) : {sheet} ; renommee|karma {standing}")

        log("--- I1")
        set_option("ImportCharacter", True)
        time.sleep(2)
        leave()
        offered = connect()
        log(f"choix proposes : {offered}")
        check("l'ecran propose son personnage, \"un personnage d'une de mes sauvegardes\" et \"nouveau personnage\"",
              len(offered) == 3 and IMPORT in offered[1] and offered[-1] == "A new character")
        pick(IMPORT)
        wait(lambda: any("(world_import)" in c for c in choices()), "liste des sauvegardes", timeout=30, every=1.0)
        saves = choices()
        log(f"sauvegardes proposees : {saves}")
        check("la liste des sauvegardes s'ouvre, 8 au plus, avec \"retour\"", 2 <= len(saves) <= 9 and saves[-1] == "Back")

        log("--- I2")
        pick("(world_import)")
        second = in_game()
        check("il joue un autre personnage que le premier", second != first and second != 1)
        mine = ev(A, SHEET.format("EClass.pc"))
        copy = ev(H, SHEET.format(host_chara(second)))
        log(f"chez l'invite : {mine}")
        log(f"chez l'host   : {copy}")
        check(f"le personnage importe a le nom, le niveau, l'or, l'equipement et le sac de la sauvegarde ({mine})", same(mine, sheet))
        check("et l'host en a la meme copie", same(copy, sheet))
        check(f"avec la renommee et le karma de la sauvegarde ({standing})",
              eventually(lambda: ev(A, 'EClass.player.fame + "|" + EClass.player.karma') == standing, timeout=15))
        uids = (ev(H, UIDS.format("EClass.pc")) + "," + ev(H, UIDS.format(host_chara(second)))).split(",")
        check(f"aucun numero en double entre l'host et le personnage importe ({len(uids)} numeros)", len(uids) == len(set(uids)))
        check("il vient bien de world_import", ev(H, host_chara(second) + '.GetStr("emp_import")').startswith("world_import/"))
        check("la sauvegarde n'a pas change d'un octet", digest() == before)

        log("--- I3")
        kept = roster()
        leave()
        offered = connect()
        log(f"choix proposes : {offered}")
        check("il revient : le personnage importe est propose avec le premier", len(offered) == 4 and IMPORT in offered[2])
        pick(IMPORT)
        wait(lambda: any("(world_import)" in c for c in choices()), "liste des sauvegardes", timeout=30, every=1.0)
        pick("(world_import)")
        wait(lambda: "already" in ev(A, TITLE), "refus du second exemplaire", timeout=60, every=1.0)
        check("la meme sauvegarde une seconde fois : refuse, le choix revient", len(choices()) == 4)
        check("rien de plus chez l'host", roster() == kept)

        log("--- I4")
        # l'ordre est celui de la liste du joueur : le premier personnage, puis l'importe
        click(1)
        check("il reprend le personnage importe", in_game() == second)
        check("toujours avec son or, son equipement et son sac", same(ev(A, SHEET.format("EClass.pc")), sheet))

        log("--- I5")
        set_option("ImportCharacter", False)
        time.sleep(2)
        leave()
        offered = connect()
        log(f"choix proposes : {offered}")
        check("case decochee : le choix n'est plus propose", len(offered) == 3 and not any(IMPORT in c for c in offered))
        click(0)
        check("il reprend son premier personnage", in_game() == first)
        check("la sauvegarde n'a toujours pas change", digest() == before)

        log("--- I6")
        make_cloud()
        packed = tree(CLOUD)
        set_option("ImportCharacter", True)
        time.sleep(2)
        leave()
        connect()
        pick(IMPORT)
        wait(lambda: any("Steam Cloud world_importcloud" in c for c in choices()), "la sauvegarde du nuage dans la liste", timeout=30, every=1.0)
        log(f"sauvegardes proposees : {choices()}")
        pick("Steam Cloud world_importcloud")
        third = in_game()
        check("sauvegarde du nuage : il joue un troisieme personnage", third not in (first, second, 1))
        check("avec la fiche de la sauvegarde", same(ev(A, SHEET.format("EClass.pc")), sheet))
        check("le dossier du nuage n'a pas change (ni deballe, ni deplace)", tree(CLOUD) == packed)
        set_option("ImportCharacter", False)
        time.sleep(2)
        leave()
        connect()
        click(0)
        check("il reprend son premier personnage pour finir", in_game() == first)

        log("--- I7")
        # seule la case d'import cochee (pas le choix du personnage) : un joueur qui a deja quelqu'un ici n'a pas
        # de question a chaque connexion, il reprend le dernier personnage joue
        import emp
        from mp_test import ok
        set_option("ChooseCharacter", False)
        set_option("ImportCharacter", True)
        try:
            time.sleep(2)
            leave()
            ok(emp.call(A, "command", {"cmd": "emp.connect_udp"}))
            asked = False
            end = time.time() + 20
            while time.time() < end and not (state(A)["sceneMode"] == "Zone" and state(A)["connected"]):
                asked = asked or bool(choices())
                time.sleep(0.5)
            check("import seul coche : pas d'ecran de choix pour un joueur qui a deja un personnage ici", not asked)
            check("il reprend le dernier personnage joue", in_game() == first)
        finally:
            set_option("ImportCharacter", False)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-import-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        try:
            set_option("ImportCharacter", False)
            set_option("ChooseCharacter", False)
        except Exception:  # noqa: BLE001
            pass
        shutil.rmtree(SOLO, ignore_errors=True)
        shutil.rmtree(CLOUD, ignore_errors=True)

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
