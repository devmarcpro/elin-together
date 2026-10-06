"""Compare ce que plusieurs jeux voient de la meme carte : sert a toutes les suites (dev/PLAN_desync.md).

    from world_diff import diff
    gaps = diff([27551, 27552, 27553])        # [] : les jeux sont d'accord ; sinon une ligne lisible par ecart

    python _tools/world_diff.py                # sur toutes les fenetres ouvertes
    python _tools/world_diff.py 27551 27552

Compare, par numero (uid), dans chaque jeu :
- les personnages de la carte : identifiant, case, vie, mort ou non ;
- les objets au sol de la carte (meubles compris) : identifiant, case, quantite ;
- le sac et l'equipement de chaque personnage « du monde » present sur la carte (les joueurs et leurs compagnons :
  ceux qui viennent de la copie du monde, pas de la copie de la carte) : identifiant, quantite, emplacement d'equipement,
  contenant.

Ce qui n'est PAS compare : le contenu des coffres poses au sol, le terrain, les competences, l'argent en banque, les
quetes, la case d'un objet dans la grille du sac (propre a chaque jeu), les cartes d'aptitude du sac (refaites par
chaque jeu), les objets dont le numero est encore « en attente » chez un invite (pas confirmes par l'host : sautes
et comptes).

Les jeux ne sont pas lus au meme instant (un appel par fenetre, l'un apres l'autre) : un personnage qui marche ou
une vie qui remonte donnent un ecart d'un instant. Un ecart n'est donc rendu que s'il tient sur `tries` lectures
espacees de `every` secondes, et la case d'un personnage est acceptee a `chara_slack` cases pres (le mod lui-meme ne
corrige une case qu'au-dela de 2 cases).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402

PENDING = 0x40000000  # ElinTogether.Models.PendingUid.Flag

SNAPSHOT = (
    'if (!EClass.core.IsGameStarted || EClass._map == null) return ""; '
    'var sb = new System.Text.StringBuilder(); '
    'sb.Append("Z|").Append(EClass._zone.uid).Append(";"); '
    'foreach (var c in EClass._map.charas) { sb.Append("C|").Append(c.uid).Append("|").Append(c.id).Append("|")'
    '.Append(c.pos.x).Append(",").Append(c.pos.z).Append("|").Append(c.hp).Append("|").Append(c.isDead ? 1 : 0).Append(";"); } '
    'foreach (var t in EClass._map.things) { sb.Append("T|").Append(t.uid).Append("|").Append(t.id).Append("|")'
    '.Append(t.pos.x).Append(",").Append(t.pos.z).Append("|").Append(t.Num).Append(";"); } '
    'foreach (var c in EClass._map.charas.Where(x => x.IsGlobal)) { '
    'var todo = new System.Collections.Generic.Stack<Thing>(c.things); '
    'while (todo.Count > 0) { var t = todo.Pop(); if (t.id == "ability") continue; '
    'sb.Append("B|").Append(c.uid).Append("|").Append(t.uid).Append("|").Append(t.id).Append("|").Append(t.Num).Append("|")'
    '.Append(t.c_equippedSlot).Append("|").Append(t.parent is Card p ? p.uid : 0).Append(";"); '
    'foreach (var k in t.things) todo.Push(k); } } '
    'return sb.ToString();'
)


def snapshot(port):
    """Ce que ce jeu voit : {"zone": uid, "charas": {uid: (id, (x, z), vie, mort)}, "things": {uid: (id, (x, z), n)},
    "bags": {(perso, uid): (id, n, emplacement, contenant)}, "pending": nombre d'objets en attente sautes}."""
    r = emp.call(port, "eval", {"code": SNAPSHOT}, timeout=120.0)
    if not r.get("ok"):
        raise RuntimeError(r.get("error"))
    snap = {"zone": None, "charas": {}, "things": {}, "bags": {}, "pending": 0}
    for rec in (r.get("result") or "").split(";"):
        f = rec.split("|")
        if f[0] == "Z":
            snap["zone"] = int(f[1])
        elif f[0] in ("C", "T"):
            uid = int(f[1])
            x, z = (int(v) for v in f[3].split(","))
            if f[0] == "C":
                snap["charas"][uid] = (f[2], (x, z), int(f[4]), f[5] == "1")
            elif uid & PENDING:
                snap["pending"] += 1
            else:
                snap["things"][uid] = (f[2], (x, z), int(f[4]))
        elif f[0] == "B":
            if int(f[2]) & PENDING:
                snap["pending"] += 1
            else:
                snap["bags"][(int(f[1]), int(f[2]))] = (f[3], int(f[4]), int(f[5]), int(f[6]))
    return snap


def _same_chara(values, slack):
    if any(v is None for v in values):
        return False
    first = values[0]
    return all(v[0] == first[0] and v[2:] == first[2:]
               and max(abs(v[1][0] - first[1][0]), abs(v[1][1] - first[1][1])) <= slack for v in values)


def _tell(kind, value):
    if value is None:
        return "absent"
    if kind == "chara":
        return f"{value[0]} case {value[1][0]},{value[1][1]} vie {value[2]}{' mort' if value[3] else ''}"
    if kind == "thing":
        return f"{value[0]} case {value[1][0]},{value[1][1]} x{value[2]}"
    worn = f" equipe ({value[2]})" if value[2] else ""
    return f"{value[0]} x{value[1]}{worn} dans {value[3]}"


def diff_once(ports, names=None, chara_slack=2):
    """Une lecture de chaque jeu : {cle de l'ecart: ligne lisible}. Voir `diff` pour ce qui tient dans le temps."""
    names = names or {p: str(p) for p in ports}
    snaps = {p: snapshot(p) for p in ports}
    gaps = {}
    zones = {p: s["zone"] for p, s in snaps.items()}
    if len(set(zones.values())) > 1:
        gaps[("zone",)] = "pas la meme carte : " + ", ".join(f"{names[p]} {z}" for p, z in zones.items())
        return gaps
    labels = {"charas": ("chara", "personnage"), "things": ("thing", "objet au sol"), "bags": ("bag", "objet porte")}
    for table, (kind, label) in labels.items():
        for key in sorted(set().union(*(s[table] for s in snaps.values()))):
            values = [snaps[p][table].get(key) for p in ports]
            same = _same_chara(values, chara_slack) if kind == "chara" else all(v == values[0] for v in values)
            if same:
                continue
            what = f"{label} {key[1]} (porte par {key[0]})" if kind == "bag" else f"{label} {key}"
            gaps[(table, key)] = what + " : " + " | ".join(f"{names[p]} {_tell(kind, v)}" for p, v in zip(ports, values))
    return gaps


def diff(ports, names=None, tries=4, every=1.5, chara_slack=2):
    """Liste des ecarts lisibles entre ces jeux (ports du pont de test), vide s'ils sont d'accord.
    Seuls les ecarts qui tiennent sur toutes les lectures sont rendus (messages en route, personnages qui marchent)."""
    gaps = diff_once(ports, names, chara_slack)
    for _ in range(tries - 1):
        if not gaps:
            break
        time.sleep(every)
        again = diff_once(ports, names, chara_slack)
        gaps = {k: again[k] for k in gaps if k in again}
    return list(gaps.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ports = [int(a) for a in sys.argv[1:]] or [r["port"] for r in emp.live_ports()]
    if len(ports) < 2:
        sys.exit("il faut au moins deux fenetres")
    gaps = diff(ports)
    for line in gaps:
        print(line)
    print(f"{len(gaps)} ecart(s) entre {ports}")
    sys.exit(1 if gaps else 0)


if __name__ == "__main__":
    main()
