"""Comparateur (idee de l'utilisateur, 2026-10-18 : « tester chaque fonction du jeu en multijoueur » ; conseil : commencer
petit). Sur des fenetres deja ouvertes (host + invite a la base, ex. `mp_test.py --world _lab/saves/world_depot.copy`).

    python _tools/diff_suite.py                 # toutes les actions des cases autour de l'invite
    python _tools/diff_suite.py --radius 1      # moins de cases
    python _tools/diff_suite.py --kinds 40      # a cote d'un objet de chaque sorte de la carte (40 sortes)
    WITNESS=1 python _tools/diff_suite.py       # temoin : retire a chaud un partage deja corrige (porte ouverte a la
                                                # main) chez l'invite ; le comparateur doit le retrouver

Pour chaque action que le jeu propose a l'invite dans le menu d'une case (clic, puis Maj+clic) : empreinte de l'invite
avant, l'invite fait l'action par le chemin du menu (ActPlan, sans le clic), attente, empreinte de l'invite apres et
de l'host. Ce que l'action a change chez l'invite doit etre pareil chez l'host ; sinon c'est consigne (action, objet,
valeur chez l'un et chez l'autre) dans _shots/diff-report.txt.
Empreinte : chaque objet de la carte et du sac de l'invite (numero, id, champs entiers, cartes de valeurs), chaque
habitant et joueur (cartes de valeurs, drapeaux ; ni PV ni position). Ignore : PNJ vivants (pas, PV), interface, hasard.
Pas joue : ce qui ouvre une fenetre de saisie (fermee aussitot), les actions qui font voyager, attaquer ou dormir
(liste noire), les actions hors menu (glisser, construction).
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log  # noqa: E402
from travel_suite import ev  # noqa: E402

H, A = 27551, 27552
SHOTS = Path(__file__).parent.parent / "_shots"

# actions qui font quitter la carte, se battre, dormir, ou qui ne finissent pas seules
SKIP = ("actEnter", "ActNewZone", "actSleep", "ActSleep", "ActMelee", "ActRanged", "ActThrow", "AI_Goto", "actExitBorder",
        "ActKick", "ActSteal", "ActSuicide", "TaskDig", "TaskMine", "TaskCut", "TaskHarvest", "AI_Fish", "actDrink_well",
        "ActPray", "actRest", "actWait", "ActEscape", "actReadBook", "AI_Read")

FP = r'''
var lines = new System.Collections.Generic.List<string>();
System.Func<BaseCard, string> maps = c => string.Join(";", c.mapInt.OrderBy(x => x.Key).Select(x => x.Key + "=" + x.Value))
    + "#" + string.Join(";", c.mapStr.OrderBy(x => x.Key).Select(x => x.Key + "=" + x.Value))
    + "#" + string.Join(";", c.mapObj.Where(x => x.Key != 2).OrderBy(x => x.Key).Select(x => x.Key + "=" + Newtonsoft.Json.JsonConvert.SerializeObject(x.Value).GetHashCode()));
System.Action<Thing, string> thing = null;
thing = (t, where) => {
    // (ce qu'un objet porte dans un sac : sa derniere case et sa place, propres a chaque jeu ; fenetres : mapObj 2)
    var ints = (int[])t._ints.Clone(); if (where != "map") { ints[7] = ints[8] = ints[9] = ints[18] = 0; }
    // (l'orientation d'un objet pose sans etre installe est tiree par chaque jeu ; « ne pas ramasser seul » : bit 7,
    // propre a celui qui a pose l'objet)
    if (!t.IsInstalled) ints[5] = 0; var b1 = t._bits1.Bits & ~(1u << 7);
    lines.Add("T" + t.uid + "\t" + where + "|" + t.id + "|" + string.Join(",", ints) + "|" + b1 + "," + t._bits2.Bits + "|" + maps(t));
    foreach (var c in t.things) thing(c, "in" + t.uid);
};
foreach (var t in EClass._map.things) thing(t, "map");
var me = EClass._map.charas.Find(x => x.uid == __ME__);
if (me != null) foreach (var t in me.things) thing(t, "bag");
foreach (var c in EClass._map.charas.Where(c => c.IsPCFaction || c.IsPC || c.GetBool("remote_chara")))
    // (32 : minuteur du « bon retour » de l'IA d'un habitant, propre au jeu qui le fait vivre)
    lines.Add("C" + c.uid + "\t" + c.id + "|" + c._bits1.Bits + "," + c._bits2.Bits + "|" + maps(c).Replace(";32=" + c.GetInt(32), "").Replace("32=" + c.GetInt(32) + ";", ""));
return string.Join("\n", lines);
'''

PLAN = r'''
var me = EClass.pc; var res = new System.Collections.Generic.List<string>();
for (var dx = -__R__; dx <= __R__; dx++) for (var dz = -__R__; dz <= __R__; dz++) {
    var pt = new Point(me.pos.x + dx, me.pos.z + dz); if (!pt.IsValid) continue;
    foreach (var inp in new[] { ActInput.LeftMouse, ActInput.RightMouse, ActInput.AllAction }) {
        var p = new ActPlan { input = inp }; var tg = new PointTarget(); tg.pos.Set(pt); p._Update(tg);
        for (var i = 0; i < p.list.Count; i++) {
            var a = p.list[i].act; var id = a is DynamicAct d ? d.id : a.GetType().Name;
            res.Add(pt.x + "," + pt.z + "," + (inp == ActInput.AllAction ? 1 : inp == ActInput.RightMouse ? 2 : 0) + "," + i + "," + id + "," + (p.list[i].tc == null ? 0 : p.list[i].tc.uid));
        }
    }
}
return string.Join("\n", res.Distinct());
'''

DO = r'''
var p = new ActPlan { input = __INP__ }; var tg = new PointTarget(); tg.pos.Set(new Point(__X__, __Z__)); p._Update(tg);
var item = p.list.FirstOrDefault(x => (x.act is DynamicAct d ? d.id : x.act.GetType().Name) == "__ID__");
if (item == null) return "gone";
try { item.Perform(); } catch (System.Exception ex) { return "throw " + ex.GetType().Name; }
return "ok";
'''

# un objet installe de chaque sorte (trait), le plus proche de l'invite d'abord
KINDS = r'''
var me = EClass.pc;
return string.Join("\n", EClass._map.things.Where(t => t.IsInstalled && t.pos.IsValid)
    .GroupBy(t => t.trait.GetType().Name).Select(g => g.OrderBy(t => t.pos.Distance(me.pos)).First())
    .OrderBy(t => t.pos.Distance(me.pos)).Take(__N__).Select(t => t.trait.GetType().Name + "," + t.pos.x + "," + t.pos.z));
'''

GO = 'var p = new Point(__X__, __Z__).GetNearestPoint(allowChara: false); EClass.pc.MoveImmediate(p); return p.x + "," + p.z;'

# un objet du sac de l'invite par sorte (trait) ; pas ce qui fait quitter la carte ni les papiers du monde
HELD = r'''
var all = new System.Collections.Generic.List<Thing>(); System.Action<Thing> walk = null;
walk = t => { all.Add(t); if (t.IsContainer) foreach (var c in t.things) walk(c); };
foreach (var t in EClass.pc.things) walk(t);
var skip = new[] { "Return", "Escape", "Evac", "Gate", "Deed", "Bill", "Letter", "Teleport", "Container", "Purse", "ToolBelt", "Map", "Spellbook", "Ancient" };
return string.Join("\n", all.Where(t => !t.isEquipped && !skip.Any(k => t.trait.GetType().Name.Contains(k)))
    .GroupBy(t => t.trait.GetType().Name).Select(g => g.First()).Take(__N__).Select(t => t.trait.GetType().Name + "," + t.uid));
'''

HOLD = ('var all = new System.Collections.Generic.List<Thing>(); System.Action<Thing> walk = null; '
        'walk = t => { all.Add(t); if (t.IsContainer) foreach (var c in t.things) walk(c); }; foreach (var t in EClass.pc.things) walk(t); '
        'var h = all.Find(t => t.uid == __U__); if (h == null) return "gone"; EClass.pc.HoldCard(h); EClass.player.RefreshCurrentHotItem(); return "ok";')

DROP = 'if (EClass.pc.held != null) EClass.pc.PickHeld(); EClass.player.RefreshCurrentHotItem(); return "ok";'

CLOSE = 'EClass.ui.CloseLayers(); if (EClass.pc.ai is AIAct ai && !(ai is GoalManualMove) && !ai.IsIdle) EClass.pc.SetNoGoal(); return "ok";'


def fingerprint(port, me):
    out = ev(port, FP.replace("__ME__", str(me)), timeout=60)
    return dict(line.split("\t", 1) for line in out.split("\n") if "\t" in line)


def witness():
    """Retire a chaud chez l'invite un partage deja corrige qui passe par le menu d'une case (porte ouverte ou fermee a
    la main, 2026-10-18) : le comparateur doit le retrouver"""
    n = ev(A, 'var h = new HarmonyLib.Harmony("bench.unpatch"); var n = 0; '
              'foreach (var m in HarmonyLib.AccessTools.GetDeclaredMethods(typeof(TraitDoor)).Concat(typeof(TraitDoor).GetNestedTypes(HarmonyLib.AccessTools.all).SelectMany(HarmonyLib.AccessTools.GetDeclaredMethods)).Where(m => m.Name.Contains("<TrySetAct>"))) '
              '{ h.Unpatch(m, HarmonyLib.HarmonyPatchType.Postfix, "*"); n++; } return n.ToString();')
    log(f"temoin : partage des portes retire chez l'invite ({n} fonctions)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, default=2)
    ap.add_argument("--wait", type=float, default=4)
    ap.add_argument("--kinds", type=int, default=0, help="aller a cote d'un objet de chaque sorte (N sortes)")
    ap.add_argument("--host-acts", action="store_true", help="l'host fait les actions, l'invite est compare")
    ap.add_argument("--held", type=int, default=0, help="prendre en main N sortes d'objets du sac, une a une")
    ap.add_argument("--zone", help="id d'une zone ou aller d'abord (ex. mysilia), host et invite ensemble")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    global H, A
    if a.host_acts:
        H, A = A, H  # (A : celui qui agit ; H : celui qu'on compare)
    if a.zone:
        from travel_suite import host_goto  # noqa: PLC0415
        uid = int(ev(H, f'return EClass.game.spatials.map.Values.First(z => z.id == "{a.zone}" && z is Zone).uid.ToString();'))
        if int(ev(H, 'return EClass._zone.uid.ToString();')) != uid:
            host_goto(27551, 27552, uid)
    me = ev(A, 'return EClass.pc.uid.ToString();')
    if os.environ.get("WITNESS") == "1":
        witness()
    spots = [None]
    if a.held:
        spots = [("held:" + k, u) for k, u in (line.split(",") for line in ev(A, HELD.replace("__N__", str(a.held)), timeout=60).split("\n") if line)]
    elif a.kinds:
        spots = [line.split(",") for line in ev(A, KINDS.replace("__N__", str(a.kinds)), timeout=60).split("\n") if line]
    plan = []
    for spot in spots:
        if spot and spot[0].startswith("held:"):
            if ev(A, HOLD.replace("__U__", spot[1])) != "ok":
                continue
            time.sleep(0.5)
        elif spot:
            ev(A, GO.replace("__X__", spot[1]).replace("__Z__", spot[2]))
            time.sleep(1)
        for line in ev(A, PLAN.replace("__R__", str(a.radius)), timeout=60).split("\n"):
            # (une fois par action et par sorte d'objet)
            if line and (line.split(",")[4], spot and spot[0]) not in {(p[4], p[6]) for p in plan}:
                plan.append(line.split(",") + ([spot[0], spot[1], spot[2] if len(spot) > 2 else ""] if spot else ["", "", ""]))
        if spot and spot[0].startswith("held:"):
            ev(A, DROP)
    plan = [p for p in plan if not any(s.lower() == p[4].lower() for s in SKIP)]
    log(f"{len(plan)} actions proposees a l'invite autour de lui")
    report, done = [], 0
    for x, z, shift, i, act, tc, kind, sx, sz in plan:
        if kind.startswith("held:"):
            if ev(A, HOLD.replace("__U__", sx)) != "ok":
                log(f"  {kind} : plus dans le sac")
                continue
            time.sleep(0.5)
        elif sx:
            ev(A, GO.replace("__X__", sx).replace("__Z__", sz))
            time.sleep(1)
        before = fingerprint(A, me)
        r = ev(A, DO.replace("__INP__", {"1": "ActInput.AllAction", "2": "ActInput.RightMouse"}.get(shift, "ActInput.LeftMouse"))
               .replace("__X__", x).replace("__Z__", z).replace("__ID__", act).replace("__I__", i))
        if r != "ok":
            log(f"  {act} en {x},{z} : {r}")
            continue
        done += 1
        time.sleep(a.wait)
        ev(A, CLOSE)
        if kind.startswith("held:"):
            ev(A, DROP)
        after = fingerprint(A, me)
        changed = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
        if not changed:
            continue
        bad = []
        for attempt in range(4):
            host = fingerprint(H, me)
            after = fingerprint(A, me)
            bad = [k for k in changed if host.get(k) != after.get(k)]
            if not bad:
                break
            time.sleep(3)
        line = f"{act} en {x},{z}{' (Maj)' if shift == '1' else ' (droit)' if shift == '2' else ''}{' [' + kind + ']' if kind else ''} : {len(changed)} change(s) chez l'invite"
        if bad:
            line += f", {len(bad)} DIFFERENT(S) chez l'host"
            report.append(line)
            for k in bad[:5]:
                report.append(f"    {k}\n      invite : {(after.get(k) or 'absent')[:300]}\n      host   : {(host.get(k) or 'absent')[:300]}")
        log("  " + line)
    SHOTS.mkdir(exist_ok=True)
    (SHOTS / "diff-report.txt").write_text("\n".join(report) or "aucune difference", encoding="utf-8")
    log(f"=== {done} actions jouees, {sum(1 for r in report if not r.startswith(' '))} avec une difference (detail : _shots/diff-report.txt)")


if __name__ == "__main__":
    main()
