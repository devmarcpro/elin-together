"""Reglages d'objets qu'un invite changeait seulement chez lui (audit du 2026-10-18), sur des fenetres deja ouvertes
(host + invite sur la meme carte, une base avec des portes : le monde du depot ou world_lab).

    python _tools/settings2_suite.py

P1  une porte ouverte puis fermee a la main par l'invite (menu de la case, « ouvrir », Maj « fermer ») : pareil chez l'host
P2  un objet cache puis remontre par l'invite (outil de visibilite du mode construction) : pareil chez l'host
P3  le nom donne par l'invite a une graine de son sac (« changer le nom » est propose par le jeu) : l'host le connait
P4  le tableau de maison (toit, musique) change par l'invite : l'host a les memes reglages. Le banc va a la base si
    besoin, ecrit les champs puis appelle TraitHouseBoard.ApplyData (ce que fait chaque bouton du menu, pas le menu).
    OLD=1 : retire a chaud chez l'invite ce qui le dit aux autres (rouge attendu).
P5  l'invite renomme un habitant de la base (« changer le nom » de la liste des habitants : le banc ecrit c_altName,
    ce que fait la fenetre de saisie), puis l'host en renomme un autre : chaque nom est connu des deux jeux.
    OLD=1 : retire a chaud l'envoi dans les deux jeux (rouge attendu).
P6  l'invite peint une toile de son sac (une seule toile : le banc ecrit c_textureData, ce que font le pinceau et la
    fenetre de peinture ; pas la fenetre) : l'host a la meme image, octet pour octet. Pas couvert : une pile de
    plusieurs toiles (le jeu en detache une copie, numero provisoire). OLD=1 : envoi retire chez l'invite.
P7  l'invite bascule « atrium » d'une piece par l'entree du menu de la piece (la vraie action du jeu, sans le clic) :
    la plaque de la piece a la meme valeur chez l'host. Pas joue : nom (fenetre de saisie), acces, groupe, hauteur.
P8  un habitant attache (pose par eval dans les deux jeux) : l'invite le libere (TryUnrestrain, ce que fait « liberer »
    du menu), l'host le voit libre ; puis l'inverse.
P9  l'invite change le portrait d'un habitant (c_idPortrait, ce que fait la fenetre des portraits) : l'host l'a.
P10 l'invite change l'apparence de la monture d'un habitant (c_idRidePCC, ce que fait le curseur du poteau) : l'host l'a.
P11 l'invite bascule « allumage automatique » d'une lumiere (ce que fait l'entree Maj du menu de la case) : l'host l'a.
P12 l'invite crochete un coffre ferme (Trait.OnLockOpen, la fin du crochetage) : ouvert chez l'host aussi.
    (P11 et P12 trouves par le comparateur diff_suite.py, 2026-10-18)
P13 l'invite change la couleur d'une lumiere (c_lightColor, ce que fait la palette de l'entree Maj) : l'host l'a.
P14 l'invite change le modele d'une figurine par le curseur (la fonction du curseur du jeu, appelee par reflexion) :
    l'host a le meme.
P15 l'invite change l'apparence complete d'un habitant (la fenetre du jeu LayerEditPCC, ouverte par eval comme le fait
    « modifier l'apparence » de la liste des habitants ; une couleur changee, puis Apply) : l'host a la meme.
P16 l'outil « drapeaux de case » du mode construction (AM_FlagCell : pas de neige, flotter), utilise par l'invite sur
    une case pres de lui (OnProcessTiles, ce que fait le clic de l'outil) : la case a le drapeau chez l'host aussi ; puis
    l'host l'enleve, l'invite le voit.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually  # noqa: E402

H, A = 27551, 27552


def act(port, at, pick, all_actions=False):
    """Le menu d'une case, comme guest_suite.use_menu ; `all_actions` : Maj enfoncee (les actions de plus, dont fermer une porte)."""
    inp = "ActInput.AllAction" if all_actions else "ActInput.LeftMouse"
    return ev(port,
              f'var p = new ActPlan {{ input = {inp} }}; var pt = new PointTarget(); '
              f'pt.pos.Set(new Point({at[0]}, {at[1]})); p._Update(pt); '
              'var offered = string.Join(",", p.list.Select(i => i.act is DynamicAct d ? d.id : i.act.GetType().Name)); '
              f'var item = p.list.FirstOrDefault(i => {pick}); if (item == null) return "action absente, proposees : " + offered; '
              'item.Perform(); return "ok";')


def thing(uid):
    return f'EClass._map.things.Find(x => x.uid == {uid})'


def walk_next_to(port, x, z):
    near = lambda: int(ev(port, f'EClass.pc.pos.Distance(new Point({x}, {z})).ToString()')) <= 1  # noqa: E731
    for _ in range(4):
        # (comme dialog_walk_suite.open_dialog : le pas s'arrete parfois, le joueur recliquerait)
        ev(port, f'EClass.pc.SetAIImmediate(new AI_Goto(new Point({x}, {z}), 1)); "ok"')
        if eventually(near, timeout=15):
            return True
    return near()


def p1(ctx):
    to_base()
    me = state(A)["pc"]["uid"]
    door = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var d = EClass._map.things.Where(t => t.IsInstalled && t.trait.GetType() == typeof(TraitDoor) '
                 '&& t.c_lockLv == 0 && !(t.trait as TraitDoor).IsOpen() && !t.pos.HasChara).OrderBy(t => t.pos.Distance(c.pos)).Take(3); '
                 'return string.Join(";", d.Select(x => x.uid + "," + x.pos.x + "," + x.pos.z));')
    if not check("une porte fermee, sans serrure, sur la carte", bool(door)):
        return
    # (la plus proche n'est pas toujours atteignable a pied : le pas s'arretait en route, trois fois le 18 ; on essaie
    # les trois plus proches)
    for candidate in door.split(";"):
        uid, x, z = candidate.split(",")
        if walk_next_to(A, x, z):
            break
    else:
        check("l'invite marche a cote d'une des trois portes les plus proches", False)
        return
    dirs = lambda: (ev(H, f'{thing(uid)}.dir.ToString()'), ev(A, f'{thing(uid)}.dir.ToString()'))  # noqa: E731
    before = dirs()
    log(f"porte {uid} en {x},{z} : dir host/invite {before}")
    r = act(A, (x, z), 'i.act is DynamicAct d && d.id == "actOpen"')
    check(f"l'invite ouvre la porte ({r})", r == "ok")
    check("ouverte chez l'host comme chez l'invite", eventually(lambda: dirs()[0] == dirs()[1] != before[1], timeout=8))
    opened = dirs()
    r = act(A, (x, z), 'i.act is DynamicAct d && d.id == "actClose"', all_actions=True)
    check(f"l'invite la referme, Maj enfoncee ({r})", r == "ok")
    check("fermee chez l'host comme chez l'invite", eventually(lambda: dirs()[0] == dirs()[1] != opened[1], timeout=8))


def p2(ctx):
    to_base()
    me = state(A)["pc"]["uid"]
    spot = ev(A, f'var c = EClass.pc; var t = EClass._map.things.Where(x => x.IsInstalled && !x.isMasked && x.trait.CanBeMasked && x.pos.Distance(c.pos) < 12)'
                 '.OrderBy(x => x.pos.Distance(c.pos)).FirstOrDefault(); return t == null ? "" : t.uid + "," + t.pos.x + "," + t.pos.z;')
    if not check(f"un objet a cacher pres de l'invite ({me})", bool(spot)):
        return
    uid, x, z = spot.split(",")
    uid = ev(A, f'var t = ActionMode.Visibility.GetTarget(new Point({x}, {z})); return t == null ? "0" : t.uid.ToString();')
    masked = lambda: (ev(H, f'{thing(uid)}.isMasked.ToString()'), ev(A, f'{thing(uid)}.isMasked.ToString()'))  # noqa: E731
    log(f"objet vise par l'outil en {x},{z} : {uid}, cache host/invite {masked()}")
    ev(A, f'ActionMode.Visibility.OnProcessTiles(new Point({x}, {z}), 0); "ok"')
    check("cache chez l'host comme chez l'invite", eventually(lambda: masked() == ("True", "True"), timeout=8))
    ev(A, f'ActionMode.Visibility.OnProcessTiles(new Point({x}, {z}), 0); "ok"')
    check("remontre partout", eventually(lambda: masked() == ("False", "False"), timeout=8))


def p3(ctx):
    me = state(A)["pc"]["uid"]
    seed = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var s = ThingGen.Create("seed"); c.AddThing(s); return s.uid.ToString();')
    if not check("l'host donne une graine a l'invite", eventually(lambda: ev(A, f'(EClass.pc.things.Find(x => x.uid == {seed}) != null).ToString()') == "True", timeout=15)):
        return
    offered = ev(A, f'var t = EClass.pc.things.Find(x => x.uid == {seed}); return t.trait.CanName.ToString();')
    check("le jeu propose de nommer la graine", offered == "True")
    # ce que fait la fenetre de saisie du jeu (ActPlan, « changeName ») quand le joueur valide
    ev(A, f'EClass.pc.things.Find(x => x.uid == {seed}).c_refText = "Zorblax"; "ok"')
    name = lambda: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var t = c.things.Find(x => x.uid == {seed}); return t == null ? "absente" : (t.c_refText ?? "");')  # noqa: E731
    check("l'host connait le nom", eventually(lambda: name() == "Zorblax", timeout=8))


def p4(ctx):
    from travel_suite import host_goto  # noqa: PLC0415
    find = ('var b = EClass._map.things.FirstOrDefault(t => t.trait is TraitHouseBoard && t.IsInstalled && t.pos.cell.room != null); '
            'return b == null ? "" : b.uid.ToString();')
    if not ev(H, find):
        home = int(ev(H, 'return EClass.pc.homeZone.uid.ToString();'))
        log(f"pas de tableau ici : l'host va a la base ({home})")
        host_goto(H, A, home)
    uid = ev(H, find)
    if not check("un tableau de maison installe dans une piece", bool(uid)):
        return
    if os.environ.get("OLD") == "1":
        ev(A, 'new HarmonyLib.Harmony("bench.unpatch").Unpatch(HarmonyLib.AccessTools.Method(typeof(TraitHouseBoard), "ApplyData"), HarmonyLib.HarmonyPatchType.Postfix, "*"); return "ok";')
    read = lambda port: ev(port, f'var d = ({thing(uid)}.trait as TraitHouseBoard).data; return d == null ? "rien" : d.idRoofStyle + "/" + d.idBGM + "/" + d.snow;')  # noqa: E731
    before = read(H)
    log(f"tableau {uid} : host {before}, invite {read(A)}")
    ev(A, f'var b = {thing(uid)}.trait as TraitHouseBoard; if (b.data == null) b.data = new TraitHouseBoard.Data(); '
          'b.data.idRoofStyle = (b.data.idRoofStyle + 1) % 5; b.data.idBGM = 42; b.data.snow = !b.data.snow; b.ApplyData(); return "ok";')
    want = read(A)
    check(f"l'host a le toit, la musique et la neige choisis par l'invite ({want})", eventually(lambda: read(H) == want, timeout=8))
    log(f"host {read(H)} (avant {before})")


def p5(ctx):
    pick = ('return string.Join(",", EClass._map.charas.Where(c => c.IsPCFaction && !c.IsPCParty && !c.IsPC && !c.GetBool("remote_chara"))'
            '.Select(c => c.uid).Take(2));')
    uids = ev(H, pick).split(",")
    if not check(f"deux habitants de la base sur la carte ({uids})", len(uids) == 2 and all(uids)):
        return
    if os.environ.get("OLD") == "1":
        for port in (H, A):
            ev(port, 'new HarmonyLib.Harmony("bench.unpatch").Unpatch(HarmonyLib.AccessTools.PropertySetter(typeof(Card), "c_altName"), HarmonyLib.HarmonyPatchType.Postfix, "*"); return "ok";')
    chara = lambda uid: f'EClass._map.charas.Find(x => x.uid == {uid})'  # noqa: E731
    name = lambda port, uid: ev(port, f'var c = {chara(uid)}; return c == null ? "absent" : (c.c_altName ?? "");')  # noqa: E731
    for who, port, other, uid, new in (("l'invite", A, H, uids[0], "Zorblax"), ("l'host", H, A, uids[1], "Quimby")):
        ev(port, f'{chara(uid)}.c_altName = "{new}"; return "ok";')
        check(f"{who} renomme l'habitant {uid} en {new} : l'autre jeu a ce nom", eventually(lambda: name(other, uid) == new, timeout=8))
        log(f"{uid} : host {name(H, uid)}, invite {name(A, uid)}")


def p6(ctx):
    me = state(A)["pc"]["uid"]
    canvas = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var s = ThingGen.Create("canvas"); c.AddThing(s); return s.uid.ToString();')
    if not check("l'host donne une toile a l'invite", eventually(lambda: ev(A, f'(EClass.pc.things.Find(x => x.uid == {canvas}) != null).ToString()') == "True", timeout=15)):
        return
    if os.environ.get("OLD") == "1":
        ev(A, 'new HarmonyLib.Harmony("bench.unpatch").Unpatch(HarmonyLib.AccessTools.PropertySetter(typeof(Card), "c_textureData"), HarmonyLib.HarmonyPatchType.Postfix, "*"); return "ok";')
    ev(A, f'var t = EClass.pc.things.Find(x => x.uid == {canvas}); var tex = new UnityEngine.Texture2D(28, 28); '
          'for (var i = 0; i < 28; i++) tex.SetPixel(i, i, UnityEngine.Color.red); tex.Apply(); t.c_textureData = UnityEngine.ImageConversion.EncodeToPNG(tex); return "ok";')
    sig = lambda port, root: ev(port, f'var t = {root}.things.Find(x => x.uid == {canvas}); var d = t == null ? null : t.c_textureData; '  # noqa: E731
                                     'return d == null ? "vide" : d.Length + ":" + System.Convert.ToBase64String(System.Security.Cryptography.MD5.Create().ComputeHash(d));')
    mine = sig(A, "EClass.pc")
    there = lambda: sig(H, f'EClass._map.charas.Find(x => x.uid == {me})')  # noqa: E731
    check(f"l'host a la meme image que l'invite ({mine})", eventually(lambda: there() == mine, timeout=8))
    log(f"host : {there()}")


def p7(ctx):
    from travel_suite import host_goto  # noqa: PLC0415
    find = 'var r = EClass._map.rooms.listRoom.FirstOrDefault(x => x.plate != null); return r == null ? "" : r.plate.owner.uid.ToString();'
    if not ev(H, find):
        home = int(ev(H, 'return EClass.pc.homeZone.uid.ToString();'))
        log(f"pas de plaque ici : l'host va a la base ({home})")
        host_goto(H, A, home)
    uid = ev(H, find)
    if not check("une piece avec sa plaque", bool(uid)):
        return
    atrium = lambda port: ev(port, f'return ({thing(uid)}.trait as TraitRoomPlate).areaData.atrium.ToString();')  # noqa: E731
    before = atrium(A)
    r = ev(A, f'var room = EClass._map.rooms.listRoom.First(x => x.plate != null && x.plate.owner.uid == {uid}); '
              'var i = room.ListInteractions().First(x => x.text.StartsWith("toggleAtrium".lang())); i.action(); return room.data.atrium.ToString();')
    check(f"l'invite bascule l'atrium ({before} -> {r})", r != before)
    check(f"l'host a la meme valeur sur la plaque ({r})", eventually(lambda: atrium(H) == r, timeout=8))
    log(f"plaque {uid} : host {atrium(H)}, invite {atrium(A)}")
    ev(A, f'var room = EClass._map.rooms.listRoom.First(x => x.plate != null && x.plate.owner.uid == {uid}); '
          'room.ListInteractions().First(x => x.text.StartsWith("toggleAtrium".lang())).action(); return "ok";')


def residents():
    return ev(H, 'return string.Join(",", EClass._map.charas.Where(c => c.IsPCFaction && !c.IsPCParty && !c.IsPC && !c.GetBool("remote_chara"))'
                 '.Select(c => c.uid).Take(2));').split(",")


def to_base():
    from travel_suite import host_goto  # noqa: PLC0415
    if residents() == [""]:
        home = int(ev(H, 'return EClass.pc.homeZone.uid.ToString();'))
        log(f"pas d'habitant ici : l'host va a la base ({home})")
        host_goto(H, A, home)
        # (un pas lance dans les premieres secondes apres l'arrivee s'arretait en route, trois fois le 18-19 : a creuser,
        # le journal de l'host dit « Halting abandoned act ... client reports idle »)
        time.sleep(8)
        for port in (H, A):
            ev(port, 'foreach (var c in EClass._map.charas.Where(m => m.IsPC || m.GetBool("remote_chara"))) '
                     'if (!c.HasEditorTag(EditorTag.Invulnerable)) c.AddEditorTag(EditorTag.Invulnerable); return "ok";')
    return residents()


def p8(ctx):
    uids = to_base()
    if not check(f"deux habitants ({uids})", len(uids) == 2):
        return
    chara = lambda uid: f'EClass._map.charas.Find(x => x.uid == {uid})'  # noqa: E731
    tied = lambda port, uid: ev(port, f'return {chara(uid)}.isRestrained.ToString();')  # noqa: E731
    for who, port, other, uid in (("l'invite", A, H, uids[0]), ("l'host", H, A, uids[1])):
        for p in (H, A):
            ev(p, f'{chara(uid)}.isRestrained = true; return "ok";')
        ev(port, f'{chara(uid)}.TryUnrestrain(true, EClass.pc); return "ok";')
        check(f"{who} libere l'habitant {uid} : libre dans l'autre jeu", eventually(lambda: tied(other, uid) == "False", timeout=8))
        for p in (H, A):
            ev(p, f'{chara(uid)}.isRestrained = false; return "ok";')


def p9(ctx):
    uids = to_base()
    chara = f'EClass._map.charas.Find(x => x.uid == {uids[0]})'
    want = ev(A, f'var c = {chara}; var other = EClass._map.charas.Select(x => x.c_idPortrait).FirstOrDefault(x => !string.IsNullOrEmpty(x) && x != c.c_idPortrait); '
                 'c.c_idPortrait = other ?? "bench_portrait"; return c.c_idPortrait;')
    check(f"l'invite change le portrait de {uids[0]} ({want}) : l'host l'a",
          eventually(lambda: ev(H, f'return {chara}.c_idPortrait ?? "";') == want, timeout=8))


def p10(ctx):
    uids = to_base()
    chara = f'EClass._map.charas.Find(x => x.uid == {uids[0]})'
    want = ev(A, f'var c = {chara}; var l = EClass.core.pccs.sets["ride"].map["body"].map.Keys.ToList(); '
                 'var v = l.FirstOrDefault(x => x != c.c_idRidePCC); c.c_idRidePCC = v; c._CreateRenderer(); return v ?? "";')
    check(f"l'invite change la monture de {uids[0]} ({want}) : l'host l'a",
          bool(want) and eventually(lambda: ev(H, f'return {chara}.c_idRidePCC ?? "";') == want, timeout=8))


def p11(ctx):
    to_base()
    uid = ev(A, 'var t = EClass._map.things.Where(x => x.IsInstalled && x.trait.IsLighting).OrderBy(x => x.pos.Distance(EClass.pc.pos)).FirstOrDefault(); return t == null ? "" : t.uid.ToString();')
    if not check("une lumiere installee", bool(uid)):
        return
    want = ev(A, f'var t = {thing(uid)}; t.disableAutoToggle = !t.disableAutoToggle; return t.disableAutoToggle.ToString();')
    check(f"l'invite bascule l'allumage automatique de {uid} ({want}) : l'host l'a",
          eventually(lambda: ev(H, f'return {thing(uid)}.disableAutoToggle.ToString();') == want, timeout=8))
    ev(A, f'var t = {thing(uid)}; t.disableAutoToggle = !t.disableAutoToggle; return "ok";')


def p12(ctx):
    to_base()
    uid = ev(H, 'var c = ThingGen.Create("chest_practice"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(allowChara: false)).Install(); '
                'c.c_lockLv = 5; return c.uid.ToString();')
    lock = lambda port: ev(port, f'var t = {thing(uid)}; return t == null ? "absent" : t.c_lockLv.ToString();')  # noqa: E731
    if not check(f"un coffre ferme pose par l'host, connu de l'invite ({lock(A)})", eventually(lambda: lock(A) not in ("absent", "0"), timeout=10)):
        return
    ev(A, f'var t = {thing(uid)}; t.trait.OnLockOpen(EClass.pc); return "ok";')
    check(f"l'invite le crochete : ouvert chez l'host aussi ({lock(A)} / {lock(H)})", eventually(lambda: lock(H) == "0", timeout=8))
    ev(H, f'{thing(uid)}.Destroy(); return "ok";')


def p13(ctx):
    to_base()
    uid = ev(A, 'var t = EClass._map.things.Where(x => x.IsInstalled && x.LightData != null).OrderBy(x => x.pos.Distance(EClass.pc.pos)).FirstOrDefault(); return t == null ? "" : t.uid.ToString();')
    if not check("une lumiere installee", bool(uid)):
        return
    want = ev(A, f'var t = {thing(uid)}; t.c_lightColor = t.c_lightColor == 31 * 1024 + 1 * 32 + 1 ? 1 * 1024 + 31 * 32 + 1 : 31 * 1024 + 1 * 32 + 1; return t.c_lightColor.ToString();')
    check(f"l'invite colore la lumiere {uid} ({want}) : l'host a la meme couleur",
          eventually(lambda: ev(H, f'return {thing(uid)}.c_lightColor.ToString();') == want, timeout=8))


def p14(ctx):
    to_base()
    uid = ev(A, 'var t = EClass._map.things.FirstOrDefault(x => x.trait is TraitFigure f && f.source != null && f.source.tiles.Length > 1); return t == null ? "" : t.uid.ToString();')
    if not uid:
        # (une figurine d'un monstre a plusieurs modeles : celles de la base n'en ont qu'un)
        uid = ev(H, 'foreach (var x in EClass._map.things.Where(x => x.trait is TraitFigure f && f.source == null).ToList()) x.Destroy(); '
                    'var row = EClass.sources.charas.rows.First(r => r.tiles != null && r.tiles.Length > 1); '
                    'var t = ThingGen.Create("figure"); t.c_idRefCard = row.id; EClass._zone.AddCard(t, EClass.pc.pos.GetNearestPoint(allowChara: false)).Install(); return t.uid.ToString();')
        eventually(lambda: ev(A, f'({thing(uid)} != null).ToString()') == "True", timeout=10)
    want = ev(A, f'var f = {thing(uid)}.trait as TraitFigure; var n = f.source.tiles.Length; var b = (f.owner.refVal + 1) % System.Math.Max(n, 2); '
                 'var m = typeof(TraitFigure).GetMethods(System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).First(x => x.Name.Contains("<TrySetAct>") && x.GetParameters().Length == 1 && x.GetParameters()[0].ParameterType == typeof(float)); '
                 'm.Invoke(f, new object[] { (float)b }); return f.owner.refVal.ToString();')
    check(f"l'invite choisit le modele {want} de la figurine {uid} : l'host a le meme",
          eventually(lambda: ev(H, f'return {thing(uid)}.refVal.ToString();') == want, timeout=8))


def p15(ctx):
    to_base()
    uid = ev(A, 'var c = EClass._map.charas.FirstOrDefault(x => x.IsPCFaction && !x.IsPCParty && !x.IsPC && x.pccData != null); return c == null ? "" : c.uid.ToString();')
    if not uid:
        # (aucun dans la base : l'invite en donne une a un habitant, ce que fait le bouton « apparence complete » ; ce
        # bouton lui-meme n'est pas joue)
        uid = ev(A, 'var c = EClass._map.charas.First(x => x.IsPCFaction && !x.IsPCParty && !x.IsPC && !x.GetBool("remote_chara")); '
                    'c.pccData = PCCData.Create(c.IDPCCBodySet); c.pccData.Randomize(c.IDPCCBodySet); c._CreateRenderer(); return c.uid.ToString();')
    if not check("un habitant a apparence complete (PCC)", bool(uid)):
        return
    chara = f'EClass._map.charas.Find(x => x.uid == {uid})'
    look = lambda port: ev(port, f'var c = {chara}; if (c.pccData == null) return "aucune"; return string.Join(";", c.pccData.map.OrderBy(x => x.Key).Select(x => x.Key + "=" + string.Join(",", x.Value)));')  # noqa: E731
    r = ev(A, f'var c = {chara}; var l = EClass.ui.AddLayer<LayerEditPCC>("LayerPCC/LayerEditPCC"); l.Activate(c, UIPCC.Mode.Full); '
              'var d = l.uiPCC.pcc.data; var k = d.map.Keys.First(x => d.map[x].Length > 2 && d.map[x][2].Length >= 6); var v = d.map[k]; '
              'v[2] = v[2].StartsWith("123456") ? "654321FF" : "123456FF"; l.Apply(); l.Close(); return k + "=" + v[2];')
    want = look(A)
    check(f"l'invite change une couleur ({r}) : l'host a la meme apparence", eventually(lambda: look(H) == want, timeout=8))


def p16(ctx):
    to_base()
    at = ev(A, 'var p = EClass.pc.pos.Copy(); p.x += 1; return p.x + "," + p.z;')
    x, z = at.split(",")
    flags = lambda port: ev(port, f'var c = EClass._map.cells[{x}, {z}]; return c.isClearSnow + "/" + c.isForceFloat;')  # noqa: E731
    before = flags(H)
    for mode in ("flagSnow", "flagFloat"):
        ev(A, f'ActionMode.FlagCell.mode = AM_FlagCell.Mode.{mode}; ActionMode.FlagCell.OnProcessTiles(new Point({x}, {z}), 0); return "ok";')
    want = "/".join(str(v != "True") for v in before.split("/"))
    check(f"l'invite bascule neige et flotter sur la case {x},{z} ({before} -> {want}) : pareil chez l'host et chez lui",
          eventually(lambda: flags(H) == want and flags(A) == want, timeout=8))
    for mode in ("flagSnow", "flagFloat"):
        ev(H, f'ActionMode.FlagCell.mode = AM_FlagCell.Mode.{mode}; ActionMode.FlagCell.OnProcessTiles(new Point({x}, {z}), 0); return "ok";')
    check(f"l'host les remet : pareil chez l'invite ({before})", eventually(lambda: flags(A) == before and flags(H) == before, timeout=8))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    steps = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16]
    if len(sys.argv) > 1:
        steps = [x for x in steps if x.__name__ in sys.argv[1].split(",")]
    # (les deux joueurs de test ne meurent pas pendant la serie : un yeek de la base du depot a tue l'invite de test, niveau 1,
    # le 19 octobre ; comme oct10_suite, l'etiquette du jeu « invulnerable » dans les deux jeux)
    for port in (H, A):
        ev(port, 'foreach (var c in EClass._map.charas.Where(m => m.IsPC || m.GetBool("remote_chara"))) '
                 'if (!c.HasEditorTag(EditorTag.Invulnerable)) c.AddEditorTag(EditorTag.Invulnerable); return "ok";')
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__ or ''}")
        try:
            step({})
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
    ok = sum(1 for r in RESULTS if r[1])
    log(f"=== {ok}/{len(RESULTS)}")


if __name__ == "__main__":
    main()
