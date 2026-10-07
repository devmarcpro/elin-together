"""La liste des mods de la partie (tranche M1 de PLAN_mods_de_l_host.md) : l'host la publie, l'invite la compare aux
siens avant de recevoir le monde, et un refus nomme les mods. Test court, sur des instances deja lancees (host + 1
client, build Debug). 

    python _tools/mp_test.py
    python _tools/modlist_suite.py

L1  l'host a ecrit sa liste dans les donnees de son salon Steam (cle EmpMods : « mods sans numero;numeros du Workshop »)
L2  l'invite rejoint : une ligne du journal compare la liste de l'host aux siens (les deux fenetres ont les memes mods :
    rien ne manque, rien en trop, ou exactement ce que les deux listes lues separement donnent)
L3  l'host publie une liste differente (un mod du Workshop que personne n'a, un mod « installe a la main », un mod de
    l'invite en moins) : la comparaison de l'invite donne les trois listes attendues, et il entre quand meme (seuls les
    actes bloquent, comme avant) ; lue comme le fait la liste des parties, cette liste donne « n mods, 1 manquant »
L4  le meme invite, refuse pour ses actes : la fenetre du refus nomme ces mods
L5  case « Show the mods of the game » decochee : l'host n'envoie rien, l'invite ne compare rien et entre

Ce que le banc ne joue pas comme un joueur :
- deux fenetres d'un meme PC ont le meme compte Steam et les memes mods : la liste differente de L3 est donnee a l'host
  par le banc (`ModList.Bench`, build Debug), pas par de vrais mods ;
- l'invite rejoint par le port local, pas par le salon Steam : la liste des parties (onglet Lobby) ne se joue pas ; on
  verifie seulement ce que l'host a ecrit dans son salon et ce que l'invite en lirait (`ModList.Summary`) ;
- le refus de L4 est provoque en ajoutant un faux acte chez l'host (ce que ferait un mod a DLL que l'invite n'a pas ;
  chez l'invite il serait efface : sa liste d'actes est refaite a chaque connexion) ;
- la prise du monde dans un depot dont la liste differe (le message « n mods de ce monde ne sont pas charges ») n'est
  pas jouee ici : il faut un depot (a ajouter a depot_suite.py, avec un modlist.txt ecrit a la main dans le dossier) ;
- rien de la tranche M2 (telechargement, relance) : ce banc s'arrete si « FetchMods » est coche chez l'invite.
"""
import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import chara_suite  # noqa: E402
from combat_suite import set_option  # noqa: E402
from mp_test import log, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs, session_log_lines  # noqa: E402
from version_suite import joined  # noqa: E402

H, A = 27551, 27552
LIST = 'HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.ModList"))'
PAGE = "https://steamcommunity.com/sharedfiles/filedetails/?id="
FAKE_ID, FAKE_TITLE, HAND_ID, HAND_TITLE = "111", "Faux mod du banc", "banc.mod.local", "Faux mod local du banc"
# un acte que l'host n'a pas : ce que ferait un mod a DLL charge d'un seul cote
FAKE_ACT = 'ElinTogether.API.SourceValidation.ActMappingValidator.Default.ActToIdMapping'


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def here(port):
    """Les mods actifs de cette fenetre, comme le mod les lit : [(id, numero Workshop, titre)]."""
    raw = ev(port, f'var l = (System.Collections.IEnumerable){LIST}.Property("Here").GetValue(); '
                   'var o = new System.Collections.Generic.List<string>(); '
                   'foreach (var m in l) { var t = HarmonyLib.Traverse.Create(m); '
                   'o.Add(t.Property("Id").GetValue<string>() + "\\t" + t.Property("Workshop").GetValue<string>() + "\\t" + t.Property("Title").GetValue<string>()); } '
                   'return string.Join("\\n", o);')
    return [tuple(line.split("\t")) for line in raw.split("\n") if line]


def text(port, what):
    return ev(port, f'return {LIST}.Property("{what}").GetValue<string>() ?? "";')


def bench(value):
    """La liste que l'host publie (None : la sienne)."""
    arg = "null" if value is None else ('System.Text.Encoding.UTF8.GetString(System.Convert.FromBase64String("'
                                        + base64.b64encode(value.encode()).decode() + '"))')
    ev(H, f'{LIST}.Property("Bench").SetValue({arg}); "ok"')


def compared(t0):
    """La derniere comparaison de l'invite avec la liste de l'host depuis t0 (ligne du journal), ou None."""
    found = None
    for line in session_log_lines(t0):
        d = json.loads(line)
        if d.get("@mt", "").startswith("Mods compared with") and d.get("Source") == "the host":
            found = d
    return found


def rejoin():
    chara_suite.leave()
    t0 = now()
    return t0, joined()


def dialog(port):
    return ev(port, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); return d == null ? "" : d.textDetail.text;')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = now()
    fetch = ev(A, 'var e = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client"), "FetchMods").GetValue(null); '
                  'return HarmonyLib.AccessTools.Property(e.GetType(), "Value").GetValue(e).ToString();')
    if fetch != "False":
        sys.exit("« FetchMods » est coche chez l'invite : ce banc ne joue pas le telechargement ni la relance. Decocher, puis relancer.")
    if not (state(H).get("connected") and state(A).get("connected")):
        sys.exit("il faut un host et un client deja en jeu (python _tools/mp_test.py)")

    mine, theirs = here(H), here(A)
    try:
        log("--- L1 : la liste de l'host dans les donnees de son salon Steam")
        lobby = ev(H, 'var l = ElinTogether.Net.NetSession.Instance.Lobby.Current; return l.IsValid ? (l["EmpMods"] ?? "") : "pas de salon";')
        compact = text(H, "Compact")
        if lobby == "pas de salon":
            log("l'host n'a pas de salon Steam (Steam absent ?) : L1 ne se verifie pas ici")
        else:
            workshop = [m[1] for m in mine if m[1]]
            check(f"le salon de l'host porte la liste ({lobby[:80]}...)", lobby == compact and ";" in lobby)
            check(f"elle compte ses {len(mine) - len(workshop)} mods sans numero et nomme ses {len(workshop)} mods du Workshop",
                  lobby.split(";")[0] == str(len(mine) - len(workshop))
                  and sorted(x for x in lobby.split(";")[1].split(",") if x) == sorted(workshop))

        log("--- L2 : l'invite rejoint, sa comparaison est dans le journal")
        t0, inside = rejoin()
        check("l'invite entre", inside)
        d = compared(t0) or {}
        host_ws, host_ids = {m[1] for m in mine if m[1]}, {m[0].lower() for m in mine}
        missing = sorted(m[1] for m in mine if m[1] and m[1] not in {x[1] for x in theirs})
        extra = sorted(m[0] for m in theirs if m[1] not in host_ws and m[0].lower() not in host_ids)
        check(f"une ligne du journal de l'invite compare la liste de l'host aux siens ({d.get('Count')} mods la-bas, {d.get('Here')} ici)",
              d.get("Count") == len(mine) and d.get("Here") == len(theirs))
        check(f"il manque ici ce que les deux listes lues separement donnent ({len(missing)} : {d.get('Missing')})",
              sorted(x.rsplit("id=", 1)[-1] for x in d.get("Missing", ["?"])) == missing)
        check(f"et en trop aussi ({len(extra)} : {d.get('Extra')})", len(d.get("Extra", ["?"])) == len(extra))

        log("--- L3 : l'host publie une autre liste : trois listes chez l'invite, et il entre quand meme")
        # un mod du Workshop que les deux ont, retire de la liste publiee : il devient « en trop » chez l'invite
        dropped = next((m for m in theirs if m[1] and m[1] in host_ws), None)
        lines = text(H, "Text").split("\n")
        if dropped:
            at = next(i for i, l in enumerate(lines) if l.strip() == PAGE + dropped[1])
            del lines[at - 1:at + 1]
        published = "\n".join(lines) + (f"\n{FAKE_TITLE}\n    {PAGE}{FAKE_ID}\n{HAND_TITLE}\n"
                                        f"    (installed by hand, not on the Workshop: ask the player who hosts) id {HAND_ID}\n")
        bench(published)
        check("l'host publie la liste du banc", text(H, "Reference") == published)
        t0, inside = rejoin()
        check("l'invite entre quand meme : seuls les actes bloquent", inside)
        d = compared(t0) or {}
        check(f"manquant ici : le mod du Workshop que personne n'a, avec sa page ({d.get('Missing')})",
              [x for x in d.get("Missing", []) if x == f"{FAKE_TITLE} {PAGE}{FAKE_ID}"] and len(d.get("Missing", [])) == len(missing) + 1)
        check(f"impossible a recuperer : le mod installe a la main ({d.get('Unfetchable')})",
              f"{HAND_TITLE} (id {HAND_ID})" in d.get("Unfetchable", []))
        if dropped:
            check(f"en trop ici : le mod retire de la liste, {dropped[2]} ({len(d.get('Extra', []))} en trop)",
                  any(x.endswith(PAGE + dropped[1]) for x in d.get("Extra", [])))
        summary = ev(A, f'var s = {LIST}.Method("Summary", new object[] {{ "{text(H, "Compact")}" }}).GetValue(); return s == null ? "rien" : s.ToString();')
        check(f"lue comme la liste des parties la lit : nombre de mods et 1 de plus manquant ({summary})",
              summary.replace(" ", "") == f"({len(lines_mods(published))},{len(missing) + 1})")

        log("--- L4 : refuse pour ses actes : la fenetre nomme les mods")
        chara_suite.leave()
        ev(H, f'{FAKE_ACT}[typeof(System.Text.StringBuilder)] = 987654; "ok"')
        refused = not joined(timeout=40)
        said = dialog(A)
        check("l'invite n'entre pas", refused and len(state(H).get("players", [])) == 1)
        check(f"la fenetre du refus nomme le mod manquant et le mod a installer a la main ({said[-200:]!r})",
              FAKE_TITLE in said and HAND_TITLE in said)
        ev(H, f'{FAKE_ACT}.Remove(typeof(System.Text.StringBuilder)); "ok"')
        ev(A, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); '
              'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
        time.sleep(4)

        log("--- L5 : case decochee : rien n'est envoye, rien n'est compare")
        set_option("PublishMods", False)
        t0 = now()
        check("l'invite entre", joined())
        check("aucune comparaison dans son journal", compared(t0) is None)
    finally:
        ev(H, f'{FAKE_ACT}.Remove(typeof(System.Text.StringBuilder)); "ok"')
        bench(None)
        set_option("PublishMods", True)
        if not state(A).get("connected"):
            ev(A, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
            time.sleep(4)
            joined()
    check("a la fin : l'invite est de retour chez l'host, avec sa vraie liste",
          eventually(lambda: len(state(H).get("players", [])) == 2, timeout=30) and text(H, "Reference") == text(H, "Text"))
    scan_logs(t_start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


def lines_mods(published):
    """Combien de mods une liste publiee compte : ses lignes de page du Workshop et ses lignes « installed by hand »
    (la ligne du fork n'en est pas une)."""
    return [l for l in published.split("\n") if "filedetails/?id=" in l or l.strip().startswith("(installed by hand")]


if __name__ == "__main__":
    main()
