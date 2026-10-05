# Lignes 8, 7, 9, 10, 11 de la deuxième chasse : lecture, correction proposée, test à écrire

Rendu par lecture seule le 2026-10-05. Rien n'a été compilé, rien n'a été joué. Le jeu lu est `dev/_decomp/Elin` (EA 23.352).
Écarts avec 23.351 (comparés avec `_decomp/Elin_23351`) : `TraitWhipEgg.cs` a trois lignes de plus au début de
`TrySetHeldAct` (« pas de bénéfice en carte d'utilisateur ») ; `Chara.cs` a deux lignes de plus avant `GetRevived`
(5478 au lieu de 5476) ; rien d'autre ne touche ces lignes. Tous les numéros ci-dessous sont ceux de 23.352.

Numéros d'union à prendre : **830** `CharaReviveRequestDelta` (ligne 8), **831** `CopyShopDelta` (ligne 9). Les lignes 7, 10 et 11 n'en
demandent pas (clé ajoutée à un delta existant, ou nouveau « genre » dans `CardSettingDelta`, numéro 826). Les trous 108,
815, 818, 820 de `ElinDelta.cs` ne sont pas à reprendre (peut-être retirés). Aucun argument de tâche (226) n'est nécessaire.

## Résumé

| Ligne | Défaut | Taille | Conseil ? |
|---|---|---|---|
| 8 résurrection | confirmé (et pire : le parchemin/sort ressuscite à côté de l'host, l'autre sens est à vérifier) | moyenne (2 fichiers neufs, 3 retouchés) | non, une seule bonne réponse (le compagnon garde son maître) |
| 7 réglages de coffre | confirmé ; en plus le delta n'est pas relayé à un 3e joueur | petite (2 fichiers retouchés, pas de format neuf) | oui pour un point mineur : sacs des invités (option B) |
| 9 copie Kettle/Demitas | confirmé, et plus grave que dit : l'objet déposé est perdu | petite si on refuse (1 ligne), moyenne si on le fait vraiment (2 fichiers) | oui : refuser d'abord ou faire pour de vrai |
| 10 autel | confirmé : dés tirés dans chaque jeu ; l'artefact reforgé n'existe que chez l'host, à ses pieds, et n'est même pas annoncé aux invités | moyenne (1 fichier neuf, 2 retouchés) | non, une seule bonne réponse (graine commune) |
| 11 clé à molette, marque écolo, brosse, marteau, fouets | confirmé ; l'autre sens (l'host les utilise) est aussi incomplet pour les champs d'objets | petite pour « l'effet existe » (4 lignes), moyenne pour « l'autre joueur le voit » | oui : jusqu'où synchroniser (tentes, passe-temps des fouets) |

---

## Ligne 8. Ressusciter un compagnon (barman, parchemin, sort)

### 1. Ce que fait le jeu en solo

Trois chemins, qui finissent tous dans `Chara.GetRevived` (`Chara.cs:5478-5497`) :

- **Barman** (`TraitBartender.CanRevive`, `DramaCustomSequence.cs:243` offre le choix, l'étape `_revive` `DramaCustomSequence.cs:1451-1459`
  ouvre `LayerPeople.Create<ListPeopleRevive>`). Le clic sur un nom appelle `ListPeopleRevive.OnClick`
  (`ListPeopleRevive.cs:18-24`) : `EClass.pc.TryPay(CalcMoney.Revive(c))` (prix `(niveau+5)^2*3`, réduit par le Charisme de
  « pc », `CalcMoney.cs:5-8, 40-43`), puis `c.GetRevived()`, puis `list.List()`. La liste (`OnList`, ligne 27-31) prend tout
  `game.cards.globalCharas` mort, `CanRevive()` (verrou de mort, seul `AI_Slaughter.cs:102` le pose), de la faction du joueur, pas invoqué.
- **Parchemin ou sort** : `AI_Read` → `TraitScrollStatic.OnRead` → `ActEffect.ProcAt` → `ActEffect.Proc` cas `EffectId.Revive`
  (`ActEffect.cs:2494-2510`). Le jeu choisit **au hasard** (`RandomItem`) parmi les morts de la faction qui étaient du groupe
  (`c_wasInPcParty`), puis `GetRevived()`. Pas de paiement (le parchemin est consommé par `owner.ModNum(-1)`, le sort coûte du mana).
- **Histoire** : `DramaOutcome.revive_pet` (déjà envoyé à l'host par `StoryOutcomePatch`, hors sujet).

`GetRevived` : `Revive(EClass.pc.pos.GetNearestPoint(false,false), true)` (le compagnon se relève **à côté de « pc »**), puis,
s'il est de la faction : retour chez lui s'il ne peut pas rejoindre le groupe, sinon `EClass.pc.party.AddMemeber(this, true)`.
`Revive` (`Chara.cs:5499`) remet `hp = MaxHP/3`, pose la créature sur la carte (`EClass._zone.AddCard`).

### 2. Ce que fait le mod aujourd'hui

- **Invité, barman : défaut confirmé.** L'argent part (`TryPay` → `ModCurrency` du joueur, envoyé à l'host par
  `CardModCurrencyEvent.cs:16-30`), mais `CharaReviveEvent.cs:39-42` jette le `Revive` de tout non-joueur chez un client
  (« drop all other character revives and wait for delta » : il n'y a pas de delta qui l'attend pour un compagnon). Ensuite
  `GetRevived` appelle `Party.AddMemeber` ; `PartyJoinEvent.cs:56-109` (branche client 99-107) le transforme en `CharaMakeAllyRequestDelta{JoinOnly}`, que
  l'host ignore parce que le compagnon est toujours mort (`CharaMakeAllyRequestDelta.cs:49`, `isDead: false` exigé). Résultat :
  or perdu, compagnon mort.
- **Invité, parchemin ou sort : défaut confirmé, autre forme.** Chez l'invité le `Revive` est jeté de la même manière. Chez l'host, la lecture
  est rejouée pour la copie de l'invité (`AIReadArgs`, ou `CharaActPerformDelta` pour le sort) : `Proc` choisit un mort
  avec **les dés de l'host** et appelle `GetRevived()` où « pc » est l'host : le compagnon se relève **à côté de l'host** et
  `EClass.pc.party` est le groupe de l'host (comme dit le plan). Aucun `AsCrafter` ni équivalent sur ce chemin.
- **Host.** Le geste est natif. `CharaReviveEvent.cs:75-91` n'envoie `CharaReviveDelta` que si `IsPlayer` : pour un compagnon
  l'invité reçoit seulement l'ajout à la carte (`ZoneAddCardDelta`, sans changer `isDead`) ; le relèvement arrive ensuite par le rapprochement périodique
  (`CharaStateSnapshot.cs:121-131` fait `Revive` pendant un `DynamicDelta`). À vérifier en jeu (voir test) : l'invité voit-il
  tout de suite son compagnon debout ?
- Le plan dit « `CharaReviveDelta.cs` sait revivre sur demande » : vrai pour un **joueur** (`CharaReviveDelta.cs:34-86`,
  l'host revit `chara` au point demandé, sans payer, sans contrôle de qui demande). Pour un compagnon il choisirait `pc.pos`
  de l'host si la case demandée est refusée (ligne 53-55) et ne gère pas le « retour chez soi » de `GetRevived`.

### 3. La correction la plus petite

Modèle : `b559952` (l'invité demande, l'host vérifie et **paie une fois**) + `TraitSeedPatch` (un joueur « tient lieu de pc » pour un acte).

**a) Nouveau delta 830** `ElinTogether/Models/Delta/Chara/CharaReviveRequestDelta.cs` :

```csharp
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A guest asks the host to bring back a dead companion at the barman's: the guest's game would pay and lose the
///     revive (Chara.Revive of a non-player is dropped there). The host checks, takes the price from that player's
///     purse once, and revives it next to that player (RemoteRevivePatch)
/// </summary>
[MessagePackObject]
public class CharaReviveRequestDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || host.IsAwayPeer(OriginPeer) ||
            !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
            Target.Find() is not Chara { isDead: true, isSummon: false } dead || !dead.CanRevive() || dead.faction != pc.faction) {
            return;
        }

        // the price is the one the guest saw: its own Charisma
        int cost;
        using (RemoteCraft.AsCrafter(sender)) {
            cost = CalcMoney.Revive(dead);
        }

        if (sender.GetCurrency() < cost) {
            return;
        }

        using var simulate = Simulate();
        using var told = MsgRelayContext.RedirectTo(sender);
        sender.ModCurrency(-cost);
        dead.GetRevived();
    }
}
```

Ajouter `[Union(830, typeof(CharaReviveRequestDelta))]` dans `ElinDelta.cs`, section « Chara ».

**b) Nouveau fichier** `ElinTogether/Patches/Remote/RemoteRevivePatch.cs` (l'host, quand il joue un acte **de** un joueur, fait de lui « pc » ; même
forme que `TraitSeedPatch.cs`). Il sert à la demande ci-dessus, à la lecture du parchemin et au sort rejoués chez l'host, et corrige au passage
`revive_pet` (le compagnon revient près de l'invité qui parle à Fiama) :

```csharp
[HarmonyPatch(typeof(Chara), nameof(Chara.GetRevived))]
internal static class RemoteRevivePatch
{
    [HarmonyPrefix]
    internal static void Before(Chara __instance, out ScopeExit? __state)
    {
        __state = null;
        // Recruiter: the remote player whose delta is applied or whose turn runs (same rule as an ally made on the way)
        if (CharaMakeAllyEvent.Recruiter(__instance) is not { } who) {
            return;
        }

        var told = MsgRelayContext.RedirectTo(who);
        var standIn = RemoteCraft.AsCrafter(who);
        __state = new() {
            OnExit = () => {
                standIn.Dispose();
                told.Dispose();
            },
        };
    }

    [HarmonyFinalizer]
    internal static void After(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}
```

**c) Clic du barman chez l'invité** : ajouter dans `CharaReviveEvent.cs` (ou fichier voisin) :

```csharp
[HarmonyPrefix]
[HarmonyPatch(typeof(ListPeopleRevive), nameof(ListPeopleRevive.OnClick))]
internal static bool OnReviveClick(Chara c)
{
    if (NetSession.Instance.Connection is not ElinNetClient client || ElinDelta.IsApplying) {
        return true;
    }

    // the host visiting a guest's zone cannot ask the world's host: refused as the base's plans are
    if (client.IsZoneSession) {
        SE.Beep();
        EmpPop.Information("emp_base_host_only".lang());
        return false;
    }

    client.Delta.AddRemote(new CharaReviveRequestDelta { Target = c });
    SE.Click();
    return false;
}
```

**d) Dire aux invités quand l'host ressuscite un compagnon** : dans `CharaReviveEvent.OnCharaReviveEnd` (ligne 81) remplacer
`!__instance.IsPlayer` par `!(__instance.IsPlayer || (__instance.IsPCFaction && __instance.IsInActiveMap))`. `CharaReviveDelta` côté invité sait déjà
relever un chara qui n'est pas joueur (lignes 90-103) et le remettre dans le groupe (ligne 124). Risque : `Zone.Revive` (`Zone.cs:1218-1245`) relève
aussi les habitants d'une base à chaque entrée dans la zone ; l'invité les relève déjà de son côté, le delta est un doublon sans effet
(`if (chara.isDead)` ligne 92). Si on craint le bruit : ajouter `&& __instance.c_wasInPcParty`.

Risques : doublon de relèvement pour un sort lancé par un invité à 2 morts ou plus (son jeu choisit A et jette ; l'host choisit B et relève B : un seul relèvement,
mais le message de l'invité peut nommer A, cosmétique) ; sauvegarde : rien de neuf (le compagnon garde `emp_owner`, `CompanionOwnerUid`).

### 4. Options

**Une seule bonne réponse.** Le commentaire de `PartyJoinEvent.cs:68-70` a déjà tranché : « a companion of the host a guest brings back to life stays
the host's » (le compagnon garde son maître, qui paie ne l'adopte pas). Ne pas réattribuer. Remarque d'équité symétrique, pas une différence host/invité : le parchemin choisit
parmi les morts **de tous les joueurs** (le groupe est commun). Le filtrer sur ceux du lecteur demanderait de changer `ActEffect.Proc` (transpileur) : déconseillé.

### 5. Brouillon de test (`hunt2_suite.py`, à ajouter sous le nom `h8`)

```python
from hunt_suite import hang_up, pick, talk  # noqa: E402
from base_suite import step_played  # noqa: E402
from guest_suite import count, stand  # noqa: E402


def h8(ctx):
    """barman (ligne 8) : le compagnon mort se releve a cote de celui qui paie, il paie une fois, l'invite comme l'host"""
    bar = ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Bartender").id')
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        clear_conditions(uid)
        pet = tame(ctx, "cat", key)
        if not check(f"{who} a un compagnon ({pet})", bool(pet)):
            continue
        barman = 0
        try:
            clear_conditions(pet)
            ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {pet}); m.hp = 0; m.Die(); "ok"')
            dead = lambda p: ev(p, f'var m = EClass.game.cards.globalCharas.Find({pet}); return m == null ? "absent" : m.isDead.ToString();')  # noqa: E731
            check(f"{who} : le compagnon est mort dans les deux jeux", eventually(lambda: dead(H) == "True" and dead(A) == "True", timeout=15))
            give(ctx, key, "money", 100000)
            barman = spawn(uid, bar, "Friend")
            eventually(lambda: seen(port, barman), timeout=15)
            # l'invite s'eloigne de l'host : le compagnon doit revenir pres de CELUI QUI PAIE
            if key == "a":
                stand(port, uid, *(int(v) for v in free_next_to(H, ctx["h"][1], 8).split(",")))
            price = int(ev(port, f'CalcMoney.Revive(EClass.game.cards.globalCharas.Find({pet})).ToString()'))
            g0 = count(H, uid, "money")
            talk(port, barman)
            log(f"{who} : etape {step_played(port, '_revive')}")
            r = ev(port, 'var l = EClass.ui.layers.OfType<LayerPeople>().LastOrDefault(); if (l == null) return "pas de liste"; '
                         'var it = l.GetComponentsInChildren<ItemGeneral>().FirstOrDefault(x => x.gameObject.activeInHierarchy); '
                         'if (it == null) return "pas de ligne"; it.button1.onClick.Invoke(); return "clic";')
            log(f"{who} clique le compagnon : {r}")
            check(f"{who} : relevé chez l'host", eventually(lambda: dead(H) == "False", timeout=15))
            check(f"{who} : relevé dans son propre jeu", eventually(lambda: dead(port) == "False", timeout=15))
            check(f"{who} paie une fois, {price} (or {g0} -> {count(H, uid, 'money')})", eventually(lambda: count(H, uid, "money") == g0 - price, timeout=10))
            near = ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {pet}); var p = {chara(H, uid)}; return m == null ? "99" : m.Dist(p).ToString();')
            check(f"{who} : le compagnon est a cote de celui qui a paye (distance {near})", int(near) <= 3)
            owner = ev(H, f'EClass._map.charas.Find(x => x.uid == {pet}).GetInt("emp_owner").ToString()')
            check(f"{who} : il garde son maitre ({owner})", owner == (str(uid) if key == "a" else "0"))
        finally:
            hang_up(port)
            drop([barman, pet])
```

Variante parchemin (à écrire ensuite) : chercher une ligne de `sources.things.rows` dont `trait[0]` est `ScrollStatic` et `vals[1] == "Revive"` ; tuer **deux** compagnons ; `give_made` du
parchemin ; `AI_Read` comme `g10` ; vérifier qu'**un seul** se relève, à côté du lecteur (pas de l'host).

Chemin réel emprunté : `DramaSequence.Play("_revive")` puis le bouton de la ligne de `ListPeopleRevive` (`OnClick`), donc `TryPay` + `GetRevived` du jeu. Ce que le banc ne
joue pas comme un joueur : le choix « Ressusciter » du dialogue (l'étape est jouée directement, comme `base_suite`), la souris sur la ligne (`onClick.Invoke`) ;
la mort est fabriquée par `Die()` ; le sort n'est pas écrit (nom de la compétence à chercher dans `sources.elements`).

---

## Ligne 7. Réglages de coffre (`InvSaveDataDelta`)

### 1. Ce que fait le jeu en solo

Le bouton de tri du coffre (`UIInventory.RefreshMenu`, `UIInventory.cs:461`) ouvre un menu dont **chaque entrée modifie en place** `window.saveData`
(`= container.c_windowSaveData`, `LayerInventory.cs:478-481`, `Card.cs:2649-2659`) : priorité (curseur, 541-545), « seulement ce qui pourrit » (550-554), « pas de
nourriture pourrie » (556-560), répartition avancée (561-566), filtre texte (567-580), catégories de `ShowDistribution` (`flag`, ligne 956-1013) et de `UIDistribution`
(`cats`, modifié sur place), mode de dépôt automatique (621-638), « exclure de la fabrication » (646-650), compresser, coller un réglage copié (712-725).
Rien n'est envoyé nulle part : ce sont les champs `ints[10]` priorité, `ints[11]` flag, `b1` bits 3-4-7-8-9-10, `cats`, `filter`, `ints[6]` de
`Window.SaveData` (`Plugins.UI/Window.cs:98-480`). Qui les lit : les habitants qui rangent
(`AI_Haul.cs:19-61` → `Zone.TryAddThingInSharedContainer` → `Zone.FindSharedContainer`, `Zone.cs:2333-2400`, qui compare priorité, noRotten,
onlyRottable, filtre, cats, flag), le dépôt d'un joueur (`TaskDump.cs:126-293`, tâche que l'host rejoue : `TaskDumpArgs`), la fabrication
(`Card.IsExcludeFromCraft`, `DropdownGrid.cs:121`, `UIDragGridIngredients.cs:54`) et l'empilement `compress` (`Thing.cs:1787`).
Le plan cite `Chara.cs:3313` : c'est le ramassage automatique **du joueur** (`player.dataPick`), pas un réglage de coffre ; hors sujet.

### 2. Ce que fait le mod aujourd'hui

**Confirmé.** `InvRefreshMenuEvent.cs:11-37` n'accroche que `buttonShared` (clic « partagé/personnel »). Le delta envoyé porte tout le `SaveData`
(`LZ4Bytes.Create(window.saveData)`, ligne 30-35), mais `InvSaveDataDelta.cs:34-47` ne recopie que `sharedType`. Rien n'est envoyé pour le menu. Deux
défauts de plus, vus en lisant : (1) `InvSaveDataDelta.OnApply` **ne relaie pas** (`host.Delta.AddRemote(this)` absent, comparer
`CardSettingDelta.cs:73-78`) : un 3e joueur n'apprend jamais le drapeau partagé d'un invité ; (2) à la **première ouverture** d'un frigo
`LayerInventory.cs:450-472` crée le `SaveData` avec `onlyRottable = true` : chez le seul joueur qui l'ouvre ; l'autre jeu (donc l'host, qui range) reste sans ce réglage.

### 3. La correction la plus petite

Pas de format neuf : le delta existant transporte déjà tout. Trois retouches.

**a) `InvSaveDataDelta.cs`** : recopier les champs « de règle » (pas la mise en page : x, y, taille, ancre, couleur, ouvert, tri restent à chaque joueur), et relayer :

```csharp
protected override void OnApply(ElinNetBase net)
{
    if (Container?.Find() is not { IsContainer: true } container || container.GetRootCard() is Chara ||
        Data.Decompress<Window.SaveData>() is not { } data) {
        return;
    }

    // the host tells the others (the sender too: the same state twice changes nothing)
    if (net is ElinNetHost host) {
        host.Delta.AddRemote(this);
    }

    var saveData = container.c_windowSaveData ??= new Window.SaveData { useBG = true };
    saveData.sharedType = data.sharedType;
    CopyRules(data, saveData);
    // ... la suite (le bouton de la fenêtre ouverte) inchangée
}

internal static void CopyRules(Window.SaveData from, Window.SaveData to)
{
    to.priority = from.priority;
    to.flag = from.flag;
    to.advDistribution = from.advDistribution;
    to.noRotten = from.noRotten;
    to.onlyRottable = from.onlyRottable;
    to.excludeCraft = from.excludeCraft;
    to.compress = from.compress;
    to.autodump = from.autodump;
    to.cats = [..from.cats ?? []];
    to.filter = from.filter;
    to._filterStrs = null;
}

// the part of the settings that is a rule of the world; the menu's changes are compared with it
internal static string Rules(Window.SaveData d)
{
    return string.Join("|", d.priority, (int)d.flag, d.advDistribution, d.noRotten, d.onlyRottable, d.excludeCraft, d.compress,
        (int)d.autodump, d.filter, string.Join(",", d.cats.OrderBy(i => i)));
}
```

**b) `InvRefreshMenuEvent.cs`** : le menu fabrique ses entrées à l'ouverture et les modifie sur place. On l'envoie **à sa fermeture** si les règles ont changé
(l'envoi à chaque cran du curseur serait 60 paquets par seconde ; les lambdas sont trop nombreuses pour être accrochées une par une ; `cats` est un `HashSet` modifié sur place).
Après `__instance.window.buttonShared.onClick.AddListener(PropagateSharedType);` :

```csharp
// the game's own listener (it builds the menu) runs first: this one finds the menu and watches it close
__instance.window.buttonSort?.onClick.AddListener(WatchMenu);

void WatchMenu()
{
    if (NetSession.Instance.Connection is not { } connection || __instance.owner.Container is not { } container ||
        container.GetRootCard() is Chara || UIContextMenuManager.Instance.currentMenu is not { } menu) {
        return;
    }

    var data = __instance.window.saveData;
    var before = InvSaveDataDelta.Rules(data);
    menu.onDestroy += () => {
        if (InvSaveDataDelta.Rules(data) != before) {
            connection.Delta.AddRemote(new InvSaveDataDelta {
                WindowId = __instance.window.idWindow,
                Data = LZ4Bytes.Create(data),
                IsShop = false,
                Container = container,
            });
        }
    };
}
```

**c) (petit) premier réglage d'un frigo** : un postfix sur `LayerInventory.CreateContainer(Card, Card)` qui, si `c_windowSaveData` était `null` avant et si le
conteneur est un meuble de la carte, envoie le même delta. Sans lui, un frigo que l'invité ouvre en premier a `onlyRottable` chez lui, pas chez l'host. Si on veut rester petit : le noter et ne pas le faire.

Risques : dernier arrivé gagne si deux joueurs règlent le même coffre dans la même seconde (on envoie l'état complet des règles) ; le renvoi
de l'host revient à l'envoyeur : même état, sans effet. Pas de risque de sauvegarde (c'est déjà `c_windowSaveData`, sauvegardé avec le coffre).

### 4. Options

- **A. Menu fermé = envoi (proposé).** Une seule bonne réponse pour les coffres de la carte.
- **B. Les sacs des invités (conseil).** Aujourd'hui `container.GetRootCard() is Chara` écarte aussi un conteneur **porté** par un invité. L'host
  rejoue les fabrications de l'invité sur **sa** copie du sac (`excludeCraft`, `compress`) : le réglage n'y est pas. Pour l'égalité, accepter côté host
  `GetRootCard() == l'envoyeur`, sans relais aux autres. Petit ajout, mais change la règle écrite (« un sac appartient à son joueur »).

### 5. Brouillon de test (`setting_suite.py`, `s7`)

```python
def s7(ctx):
    """reglages de coffre (ligne 7) : priorite, pas de pourri, categories, partage ; lus par l'autre jeu, dans les deux sens ; les habitants de l'host les suivent"""
    if ev(H, 'EClass._zone.IsPCFaction.ToString()') != "True":
        print("    [SAUTE] S7 : la carte n'est pas une base")
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        t = furniture(uid, extra="t.c_lockLv = 0;")
        win = f'LayerInventory.listInv.Find(l => l.invs[0].owner.Container == {thing(t)})'
        read = lambda p: ev(p, f'var d = {thing(t)}.c_windowSaveData; return d == null ? "aucun" : d.priority + "/" + d.noRotten + "/" + (int)d.flag + "/" + d.sharedType + "/" + string.Join(",", d.cats.OrderBy(i => i));')  # noqa: E731
        try:
            x, z = (int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(","))
            awake(port)
            log(f"{who} ouvre le coffre : {use_menu(port, (x, z), 'i.act is DynamicAct d && d.id == \"actContainer\"')}")
            if not check(f"{who} : la fenetre du coffre est ouverte", eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=10)):
                continue
            # le vrai menu : le bouton de tri le fabrique ; on fait ce que font ses entrees (elles changent window.saveData), puis on le ferme
            ev(port, f'{win}.invs[0].window.buttonSort.onClick.Invoke(); "ok"')
            ev(port, f'var d = {win}.invs[0].window.saveData; d.priority = 7; d.noRotten = true; d.sharedType = ContainerSharedType.Shared; '
                     'd.flag |= ContainerFlag.food; "ok"')
            ev(port, 'UIContextMenuManager.Instance.currentMenu.Hide(); "ok"')    # c'est la fermeture qui envoie
            check(cond=eventually(lambda: read(H) == read(port) == read(A) and read(H).startswith("7/True"), timeout=10),
                  label=f"{who} regle le coffre : les trois jeux disent pareil (host {read(H)}, invite {read(A)})")
            # ce que fait un habitant de l'host : un objet pourri refuse, un frais accepte (Zone.FindSharedContainer, AI_Haul)
            rotten = ev(H, 'var t = ThingGen.Create("meat"); t.decay = 99999; EClass._zone.AddCard(t, EClass.pc.pos); return t.uid.ToString();')
            check(f"{who} : l'host refuse un objet pourri pour ce coffre",
                  ev(H, f'var m = EClass._map.things.Find(q => q.uid == {rotten}); var c = EClass._zone.FindSharedContainer(m); return (c != null && c.uid == {t}).ToString();') == "False")
            ev(H, f'var m = EClass._map.things.Find(q => q.uid == {rotten}); if (m != null) m.Destroy(); "ok"')
        finally:
            close_layers()
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')
```

Chemin réel : fenêtre ouverte par le clic gauche (`use_menu`, `actContainer`) ; bouton de tri = le vrai ; fermeture = `UIContextMenu.Hide()` (la
vraie voie par laquelle `onDestroy` s'appelle). Ce que le banc ne joue pas comme un joueur : il ne clique pas les curseurs et cases du sous-menu ; il pose les valeurs
que leurs lambdas posent. Sans correctif, `read(other)` reste `7/...` chez l'envoyeur seulement (test rouge) ; `FindSharedContainer` côté host accepte le pourri.

---

## Ligne 9. Copie d'objets chez Kettle et de grimoires chez Demitas

### 1. Ce que fait le jeu en solo

Le dialogue choisit l'étape `_copyItem` (`DramaCustomSequence.cs:1721-1740`) : `c.trait.OnBarter()` (marchand rempli), puis, si `c.c_copyContainer == null`, `c.c_copyContainer =
ThingGen.Create("container_deposit")` (ligne 1732-1735), `things.SetSize(NumCopyItem, 1)` (1737), et ouvre `LayerInventory.CreateContainer<InvOwnerCopyShop>(c, c.c_copyContainer)` (1738).
Le joueur **glisse** ses objets dans ce coffre (`InvOwnerCopyShop.AllowMoved` = `CanCopy`, `InvOwnerCopyShop.cs:9-17`) : ils y restent, sans prix. Au réassortiment (`Trait.OnBarter`,
`Trait.cs:1738-1790`, tous les 28 jours : `TraitKettle.RestockDay`), chaque objet du coffre est **dupliqué** (`Duplicate(1)`, `isCopy`) dans le coffre du marchand
(`chest_merchant`) ; le joueur les achète ensuite par le marchand normal. `c_copyContainer` est un champ de la carte du personnage (`Card.cs:1848`), sauvegardé avec lui.

### 2. Ce que fait le mod aujourd'hui

**Confirmé, en plus grave.** `grep copyContainer` : rien. Chez l'invité l'étape tourne dans son jeu : `ThingGen.Create` reçoit un numéro « en attente »
(`CardGenEvent.cs:31-46`) et est **détruit à l'image suivante** (`CardCache.DelayDestroy`, `CardCache.Update` ligne 207-211). Le glisser d'un objet du sac passe par `ThingRequest`
(`InvStartDragEvent.cs:48-55`) : l'host le sort de son sac ; le dépôt dans un coffre « en attente » reste local (`CardAddThingEvent.cs:108-111`) et part avec le coffre.
Résultat probable : **l'objet de l'invité est perdu** (à jouer pour le confirmer) ; l'host n'a rien reçu, son `c_copyContainer` est vide, ses copies ne contiennent rien de l'invité.
`OnBarterEvent.cs:11-24` : le marchand temporaire ne couvre que `chest_merchant`, le réassortiment est fait par l'host (`OnBarterDelta.cs:18-35`) : bon, c'est seulement le **dépôt** qui manque. Chez l'host
le dépôt marche et son `c_copyContainer` est la référence ; les invités n'en reçoivent que la création (`CardGenDelta`), pas le lien avec Kettle.

### 3. La correction la plus petite

**Option A (une ligne, d'abord, arrête la perte d'objets).** Dans `RemoteBasePaidPatch.OnPlayStep` (`RemoteBasePaidPatch.cs:129-136`) :
`if (id is not ("_buyPlan" or "_upgradeHearth" or "_copyItem") || !IsClient)`. L'invité reçoit « seul l'host peut faire ça pour l'instant » (texte `emp_base_host_only` existant)
et retourne au pas précédent. Ce n'est pas l'égalité, mais plus rien n'est perdu.

**Option B (le vrai geste).** L'host crée le coffre et le dit à tous, puis l'invité l'ouvre ; ensuite le dépôt est un dépôt dans un coffre de l'host comme les autres.

Nouveau delta 831, `ElinTogether/Models/Delta/Zone/CopyShopDelta.cs` (demande si `Container` est nul, réponse sinon, diffusée à tous pour poser le lien) :

```csharp
[MessagePackObject]
public class CopyShopDelta : ElinDelta
{
    // the invited guest waits for the answer to open the step; one shop at a time
    private static int _waiting;
    internal static bool Replaying { get; private set; }

    [Key(0)]
    public required RemoteCard Shop { get; init; }

    [Key(1)]
    public RemoteCard? Container { get; init; }

    /// <summary>
    ///     The step "_copyItem" of a client: true when the request replaces it (it is played again when the answer comes)
    /// </summary>
    internal static bool Ask(Chara? shop)
    {
        if (shop is null || shop.trait.CopyShop == Trait.CopyShopType.None || Replaying ||
            NetSession.Instance.Connection is not ElinNetClient client || ElinDelta.IsApplying) {
            return false;
        }

        if (client.IsZoneSession) {
            SE.Beep();
            EmpPop.Information("emp_base_host_only".lang());
            return true;
        }

        if (shop.c_copyContainer is { } box && box.IsHostOwned) {
            return false;
        }

        _waiting = shop.uid;
        client.Delta.AddRemote(new CopyShopDelta { Shop = shop });
        return true;
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Shop.Find() is not Chara { isDestroyed: false } shop || shop.trait.CopyShop == Trait.CopyShopType.None) {
            return;
        }

        if (net is ElinNetHost host) {
            if (Container is not null || host.IsAwayPeer(OriginPeer)) {
                return;
            }

            using var simulate = Simulate();
            // the box is made by the host (CardGenDelta goes out first, in the same batch)
            var box = shop.c_copyContainer ??= ThingGen.Create("container_deposit");
            box.things.SetSize(shop.trait.NumCopyItem, 1);
            host.Delta.AddRemote(new CopyShopDelta { Shop = shop, Container = box });
            return;
        }

        if (Container?.Find() is not Thing found) {
            return;
        }

        shop.c_copyContainer = found;
        if (_waiting == shop.uid) {
            _waiting = 0;
            if (LayerDrama.Instance?.drama?.sequence is { } sequence) {
                Replaying = true;
                try {
                    sequence.Play("_copyItem");
                } finally {
                    Replaying = false;
                }
            }
        }
    }
}
```

et une retouche : dans `RemoteBasePaidPatch.OnPlayStep` (ou un patch jumeau sur `DramaSequence.Play(string)`), avant le test existant :
`if (id == "_copyItem" && CopyShopDelta.Ask(__instance.manager?.tg?.chara)) { id = __instance.lastStep ?? ""; return; }`.

Risques : l'ordre « création du coffre » puis « réponse » est celui du tampon de sortie (`CardGenDelta` est ajouté par la création, la réponse juste après, pas
d'`SendDeltaTo` qui pourrait passer devant) ; un coffre déjà plein chez l'host dont le contenu n'est jamais venu chez l'invité (déposé avant sa venue) : le contenu part avec la sauvegarde que
l'invité charge ; sinon il manque à l'écran de l'invité jusqu'à `CardAddThingDelta` (à vérifier avec le test). Sauvegarde : le coffre est dans la fiche de Kettle de l'host, déjà le cas.

### 4. Options (conseil)

- **A (refuser) puis B (faire).** A règle la perte tout de suite en une ligne ; B donne l'égalité. Ce n'est pas un choix d'équité mais d'ordre de travail : A maintenant, B ensuite, **si le conseil veut la copie pour les invités**.
- Question de fond pour B : **un seul coffre de dépôt par personnage**, partagé par tous les joueurs (c'est ce que fait le jeu : un coffre dans la fiche de Kettle, un seul stock de copies). Mettre un coffre par joueur
  changerait la sauvegarde (plusieurs champs) et l'économie (Kettle copierait N fois plus). Déconseillé.

### 5. Brouillon de test (`unplayed_suite.py` ou `hunt2_suite.py`, `h9`)

```python
def h9(ctx):
    """copie chez Kettle (ligne 9) : l'objet depose arrive dans le coffre de l'host, il n'est pas perdu ; l'invite comme l'host"""
    kid = ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Kettle").id')
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        for p in (H, A):
            ev(p, 'EClass.debug.enable = true; "ok"')       # TraitKettle.CanJoinParty : quete « vernis_gold » ou mode debug
        shop = spawn(uid, kid, "Friend")
        item = give_made(ctx, key, 'var t = ThingGen.Create("figure");')      # figure : CanCopy vrai pour Kettle (Trait.cs, TraitKettle.CanCopy)
        try:
            eventually(lambda: seen(port, shop), timeout=15)
            box = lambda p: ev(p, f'var c = EClass._map.charas.Find(x => x.uid == {shop}); var b = c.c_copyContainer; return b == null ? "aucun" : b.uid + ":" + b.things.Count;')  # noqa: E731
            talk(port, shop)
            log(f"{who} : etape {step_played(port, '_copyItem')}")
            if not check(f"{who} : la fenetre de depot s'ouvre", eventually(lambda: ev(port, '(LayerInventory.listInv.Any(l => l.invs[0].owner is InvOwnerCopyShop)).ToString()') == "True", timeout=15)):
                continue
            check(f"{who} : le coffre est celui de l'host (host {box(H)}, invite {box(port)})", eventually(lambda: box(H) != "aucun" and box(H).split(":")[0] == box(port).split(":")[0], timeout=10))
            # le depot : ce que fait le glisser (Transaction.Process vers la fenetre du coffre)
            r = ev(port, f'var l = LayerInventory.listInv.First(q => q.invs[0].owner is InvOwnerCopyShop); var t = EClass.pc.things.Find(x => x.uid == {item}); '
                         'var b = EClass.ui.layers.OfType<LayerInventory>().SelectMany(q => q.GetComponentsInChildren<ButtonGrid>()).FirstOrDefault(g => g.card == t); '
                         'if (b == null) return "bouton absent"; new InvOwner.Transaction(new DragItemCard.DragInfo(b), l.invs[0], 1).Process(true); return "ok";')
            log(f"{who} depose : {r}")
            check(f"{who} : l'objet est dans le coffre chez l'host ({box(H)})", eventually(lambda: box(H).endswith(":1"), timeout=15))
            check(f"{who} : et il a quitte son sac ({count(H, uid, 'figure')} figurine(s) chez l'host)", count(H, uid, "figure") == 0)
        finally:
            close_layers()
            hang_up(port)
            ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {shop}); if (c != null && c.c_copyContainer != null) c.c_copyContainer.things.DestroyAll(); "ok"')
            for p in (H, A):
                ev(p, 'EClass.debug.enable = false; "ok"')
            drop([shop])
```

Chemin réel : `DramaSequence.Play("_copyItem")` (le choix du dialogue saute à cette étape), la vraie fenêtre `InvOwnerCopyShop`, `InvOwner.Transaction.Process` pour le dépôt (ce que fait le
glisser-déposer). Ce que le banc ne joue pas comme un joueur : la souris, `UI.StartDrag` (le `ThingRequest` du début de glissement n'est pas passé : l'objet est pris
du sac directement) ; `EClass.debug.enable = true` simule la quête « vernis_gold » (à remplacer par l'achèvement de la quête si le banc sait le faire) ; `figure` est un
exemple d'objet copiable (`TraitKettle.CanCopy` accepte `figure`). Le réassortiment (28 jours) n'est pas rejoué.

---

## Ligne 10. Duel d'autel et artefact reforgé

### 1. Ce que fait le jeu en solo

Clic droit sur l'autel : `TraitAltar.TrySetAct` (`TraitAltar.cs:49-72`) → `actOffer` → `LayerDragGrid.CreateOffering(this)`. Le dépôt appelle `InvOwnerOffering._OnProcess`
→ `altar.OnOffer(EClass.pc, t)` (`InvOwnerOffering.cs:21-24`). `OnOffer` (`TraitAltar.cs:99-258`) :
- artefact du dieu de l'autel (`HasTag(godArtifact)`, ligne 171) : `t.Destroy()`, puis `EClass.game.religions.Reforge(t.id)` (ligne 173) : **`pos == null`
  donc `EClass.pc.pos`** (`ReligionManager.cs:116-127`), l'objet neuf est posé aux pieds de « pc » ;
- offrande à un autre dieu : **le duel de conversion**, `bool flag = EClass.rnd(c.faith.GetOfferingValue(t, t.Num)) > EClass.rnd(200) || IsEyth` (ligne 193) ;
  gagné : `TakeOver(c)` (l'autel prend le dieu du joueur : `SetDeity` change `c_idDeity` et le matériau, ligne 287-292) ; perdu : `Deity.PunishTakeOver(c)` (`Religion.cs:442-445`,
  `DoPunish` : pv/mana/endurance divisés par deux, `punish_ball` créé dans le sac, condition `ConWrath`) ;
- puis `_OnOffer` (piété du joueur : `c.elements.ModExp`, karma si volé).

### 2. Ce que fait le mod aujourd'hui

**Confirmé.** `InvOwnerOnProcessEvent.cs:75-84` envoie une `InvOwnerOnProcessDelta{Dest = autel}` pour **tout** dépôt, de l'host comme de l'invité. Chez celui qui dépose, le jeu joue
`OnOffer` pour lui-même (indispensable : la piété est à lui, `ElementChangedEvent.cs:57-61` ignore les éléments d'un joueur distant). À l'arrivée
(`InvOwnerOnProcessDelta.cs:140-157`) : l'host vérifie l'envoyeur, **relaie** à tous, puis joue `altar.OnOffer(offerer, thing)` pour la copie de l'invité ; chaque
autre invité le rejoue aussi. Donc **un tirage par jeu**, sans graine commune : l'autel peut changer de dieu chez l'un seul, la punition (pv, boule, colère) peut être celle d'un jeu et pas
de l'autre. Pour l'artefact : chez l'host, `Reforge` prend `EClass.pc.pos` = **pieds de l'host** ; et, comme la branche ne passe pas par `Simulate()`, `IsApplying` est vrai, donc
`ZoneAddCardEvent.cs:21-32` n'envoie **pas** l'ajout à la carte : l'objet reforgé n'existe que chez l'host (les invités reçoivent seulement sa création, `CardGenDelta`, non posée). Chez l'invité qui a offert : son `Reforge` local
crée un objet « en attente », détruit à l'image suivante. L'artefact est donc perdu pour lui. Sens host : l'artefact tombe bien aux pieds de l'host (jeu natif) et les invités le voient ;
mais le duel est tiré dans chaque jeu.

### 3. La correction la plus petite

Idée : **une graine commune, tirée par celui qui dépose**, envoyée avec l'offrande ; chaque jeu joue `OnOffer` avec elle (même modèle que `rndSeed` du jeu, `Rand.SetSeed`
est déjà utilisé par le mod, `AIUseCrafterPatch.cs:403`). L'artefact est reforgé à côté **du donneur** et annoncé par l'host.

**a) `InvOwnerOnProcessDelta.cs`** : ajouter `[Key(10)] public int Seed { get; init; }` (les clés 1 à 9 sont prises). Dans la branche `TraitAltar` (lignes 140-157) :

```csharp
// the host plays it as its own gesture, so that what is made (the reforged artifact) is announced to everyone
using var simulate = Simulate(net.IsHost);
AltarDice.Next = Seed;
altar.OnOffer(offerer, thing);
```

**b) `InvOwnerOnProcessEvent.cs`** : au moment de créer le delta (ligne 75) : `Seed = __instance is InvOwnerOffering ? AltarDice.Roll() : 0`, dans l'initialiseur ;
l'appel se fait juste avant que le jeu joue `_OnProcess` (même passage), donc `Next` est lu par `OnOffer` du même jeu.

**c) Nouveau fichier** `ElinTogether/Patches/Remote/RemoteAltarPatch.cs` :

```csharp
internal static class AltarDice
{
    internal static int Next, Current;
    internal static Chara? Offerer;

    internal static int Roll() => Next = 1 + EClass.rnd(int.MaxValue - 1);
}

[HarmonyPatch(typeof(TraitAltar), nameof(TraitAltar.OnOffer))]
internal static class AltarOfferPatch
{
    [HarmonyPrefix]
    internal static void Before(Chara c, out (int Dice, Chara? Who) __state)
    {
        __state = (AltarDice.Current, AltarDice.Offerer);
        (AltarDice.Current, AltarDice.Next, AltarDice.Offerer) = (AltarDice.Next, 0, c);
    }

    [HarmonyFinalizer]
    internal static void After((int Dice, Chara? Who) __state)
    {
        if (AltarDice.Current != 0) {
            Rand.SetSeed();
        }

        (AltarDice.Current, AltarDice.Offerer) = __state;
    }
}

// the duel rolls "rnd(value) > rnd(200)" right after asking the value: the dice are set again there, so that nothing
// drawn before (effects, sounds) can shift them from one game to the other
[HarmonyPatch(typeof(Religion), nameof(Religion.GetOfferingValue))]
internal static class AltarDiceReseed
{
    [HarmonyPostfix]
    internal static void After()
    {
        if (AltarDice.Current != 0) {
            Rand.SetSeed(AltarDice.Current);
        }
    }
}

[HarmonyPatch(typeof(ReligionManager), nameof(ReligionManager.Reforge))]
internal static class AltarReforgePatch
{
    [HarmonyPrefix]
    internal static void Before(ref Point pos)
    {
        if (pos == null && NetSession.Instance.Connection is ElinNetHost && AltarDice.Offerer is { IsRemotePlayer: true } who) {
            pos = who.pos.Copy();
        }
    }
}
```

Risques : (1) `Simulate` fait aussi partir le `Destroy` de l'objet offert et l'ajout à la carte de l'artefact, donc un `CardModNumDelta{Num = 0}` en double pour les invités qui l'ont déjà
détruit en rejouant (sans effet : `Find` rend nul) ; (2) `GetOfferingValue` est surchargé par `ReligionCustom` mais appelle la base : le postfixe de la base joue ;
(3) la graine n'est pas posée pour un pair plus ancien (`Seed == 0` : `Next` = 0, comportement d'aujourd'hui) ; (4) les données que lit le calcul (foi, piété de la copie de l'invité chez l'host) doivent
être les mêmes dans les deux jeux : la piété de l'invité arrive chez l'host par `ElementChangeDelta`, un instant avant ; à confirmer par le test (le même autel, 10 offrandes) ; (5) le punish_ball
et la condition de colère sont créés dans les deux jeux (l'objet de l'invité en attente est détruit, celui de l'host est envoyé) : à surveiller dans le test (une seule boule dans le sac de l'invité).
Pas de risque de sauvegarde (le dieu de l'autel est `c_idDeity` de l'autel, déjà sauvegardé).

### 4. Options

**Une seule bonne réponse** (la graine commune) : l'autre voie (« l'host seul décide ») perdrait la piété de l'invité, qui ne vit que dans le jeu de l'invité (`ElementChangedEvent`). Détail : l'host
doit aussi tirer la graine pour **ses** offrandes (le point (b) le fait pour tout `InvOwnerOffering`, host ou invité).

### 5. Brouillon de test (`hunt2_suite.py`, `h10`)

```python
def h10(ctx):
    """autel (ligne 10) : le duel donne le meme dieu a l'autel dans les trois jeux, et l'artefact reforge est a cote de celui qui l'offre, vu des deux jeux"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        clear_conditions(uid)
        god = ev(H, 'EClass.game.religions.list.First(r => r.CanJoin && r.id != "eyth" && r.id != EClass.pc.faith.id).id')
        mine = ev(H, f'{chara(H, uid)}.faith.id')
        t = furniture(uid, make='ThingGen.Create("altar")', extra=f'((TraitAltar)t.trait).SetDeity("{god}");')
        deity = lambda p: ev(p, f'var a = {thing(t)}; return a == null ? "absent" : ((TraitAltar)a.trait).idDeity;')  # noqa: E731
        win = 'LayerDragGrid.Instance'
        try:
            for essai in range(8):
                # l'autel reprend le dieu de depart, puis une offrande dont la valeur donne a peu pres une chance sur deux (valeur voisine de 200)
                for p in (H, A):
                    ev(p, f'((TraitAltar){thing(t)}.trait).SetDeity("{god}"); "ok"')
                item = give_made(ctx, key, 'var t = ThingGen.Create("figure"); t.SetNum(3);')
                awake(port)
                use_menu(port, tuple(int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(",")), 'i.act is DynamicAct d && d.id == "actOffer"')
                eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=8)
                # le depot : ce que fait le glisser (OnProcess du draglet, comme g10)
                ev(port, f'var g = {win}; var o = EClass.pc.things.Find(x => x.uid == {item}); var b = g.owner.buttons[g.currentIndex]; '
                         'b.SetCardGrid(o, b.invOwner); g.owner.OnProcess(o); "ok"')
                time.sleep(3)
                check(f"{who}, offrande {essai} : meme dieu sur l'autel chez l'host et chez l'invite (host {deity(H)}, invite {deity(A)})", deity(H) == deity(A))
                close_layers()
            # artefact du dieu de l'autel : reforge a cote de celui qui l'offre, pas aux pieds de l'autre joueur
            art = ev(H, f'var r = EClass.sources.things.rows.FirstOrDefault(x => EClass.game.religions.GetArtifactDeity(x.id) != null && EClass.game.religions.GetArtifactDeity(x.id).id == "{god}"); return r == null ? "" : r.id;')
            if art:
                item = give_made(ctx, key, f'var t = ThingGen.Create("{art}"); t.c_idDeity = "{god}";')
                near = lambda p, who_uid: ev(p, f'(EClass._map.things.Count(m => m.id == "{art}" && m.pos.Distance({chara(p, who_uid)}.pos) <= 3)).ToString()')  # noqa: E731
                # ... meme depot ; puis :
                # check(near(H, uid) == "1" et near(A, uid) == "1" ; l'artefact n'est pas a moins de 3 cases de l'autre joueur)
        finally:
            close_layers()
            ev(H, f'var a = {thing(t)}; if (a != null) a.Destroy(); "ok"')
```

Chemin réel : `actOffer` du clic gauche sur l'autel, la vraie fenêtre `LayerDragGrid`, `InvOwnerDraglet.OnProcess` (la fonction que le dépôt appelle, la même que `g10`), donc `InvOwnerOnProcessEvent` et
`OnOffer` du jeu. Ce que le banc ne joue pas comme un joueur : le glisser à la souris ; le dieu de départ posé par `SetDeity` (le joueur l'a
d'origine) ; la valeur d'offrande est réglée par un nombre de figurines choisi, pas par un vrai objet précieux. Avant le correctif le test doit être rouge au moins une fois sur 8 (probabilité d'accord
de deux tirages à une chance sur deux : 50 % par essai ; 8 essais, 99,6 % de voir un désaccord).

---

## Ligne 11. Clé à molette, marque écolo, brosse et marteau « à effacer », fouets

### 1. Ce que fait le jeu en solo

Tous sont des objets tenus en main qui ajoutent des entrées de menu par `TrySetHeldAct` (`p.TrySetAct(nom, lambda, cible)`) ; la lambda **est** le geste :
- **Clé à molette** (`TraitWrench.cs:61-150`) : `Upgrade(t)` change des champs de l'objet cible (lit : `c_containerSize++` ; coffre magique : `c_containerUpgrade.cap += 20` ;
  frigo : `cool = 1` et élément 405 à 50 ; coffre : `things.SetSize(l, h+1)` ; tentes : éléments de la zone-tente 3606, 2201, 2200), `owner.ModNum(-1)`, `Branch.resources.SetDirty()`, `RefreshElectricity()` ; renvoie `false`.
- **Marque écolo** (`TraitEcoMark.cs:5-24`) : `ModNum(-1)`, `t.elements.SetBase(652, 10)`, `t.ChangeWeight(poids*100/110)` ; renvoie `false`. Pas de cible passée (l'entrée n'a pas de `tc`).
- **Brosse à effacer** (`TraitToolBrushStrip.cs:5-34`) : `t.Dye(null)` sur un meuble teint, ou, sur une case teinte, `cell.isObjDyed = false` (carte, pas un objet) ; renvoie `false`. Ne s'use pas.
- **Marteau à effacer** (`TraitToolHammerStrip.cs:5-24`) : `t.SetEncLv(0)` ; renvoie `false`.
- **Fouets** (`TraitWhipLove.cs:13-57`, passe-temps et centre d'intérêt, `TraitWhipEgg.cs:8-48`, œuf) : `c.RerollHobby()` (au hasard, `Chara.cs:9716`) puis
  `RefreshWorkElements`, ou `c.MakeEgg()` (œuf, hasard pour « fécondé »), `owner.ModCharge(-1)` et destruction à zéro, `EClass.player.ModKarma(-1)` pour l'œuf ; renvoient `true`.

### 2. Ce que fait le mod aujourd'hui

**Confirmé.** `CardActReplayEvent.cs:23-33` ne remplace la lambda que pour le ticket, les seringues, le stéthoscope, la laisse et le puits ; `CardActReplayDelta.cs:73-81`
refuse les autres. Chez l'invité la lambda du reste tourne seule : `ModNum` d'une carte de l'host est **annulé** (`CardModNumEvent.cs:13-18` met `a = 0`), l'œuf créé est détruit (`CardGenEvent`), les champs
changent sur sa copie seulement. Chez l'host le geste est natif : la pile baisse et l'œuf est créé (envoyés), mais les **champs** (taille, poids, teinte, enchantement, passe-temps) ne sont
pas des événements du mod (`ElementChangedEvent.cs:57-61` ne suit que les personnages) : l'invité garde l'ancienne valeur, par exemple la taille d'un coffre qu'il ne peut plus remplir
(sa grille est plus petite). Les deux sens sont donc touchés ; le plan ne parlait que de l'invité. Autres écarts relevés : l'écran de la brosse sur une case teinte, et les tentes (éléments
de la zone), ne sont portés par aucun delta du mod (le terrain n'est pas synchronisé, `build_suite.py:135`).

### 3. La correction la plus petite

Modèle : `CardActReplayEvent` / `CardActReplayDelta` (« l'invité demande, l'host rejoue la lambda pour le joueur »), `CardSettingDelta` (« envoyer l'état, pas le clic »).

**Étape 1, l'effet existe (4 lignes).**
- `CardActReplayEvent.TargetMethods` (ligne 26) : ajouter `typeof(TraitWrench), typeof(TraitEcoMark), typeof(TraitToolBrushStrip), typeof(TraitToolHammerStrip), typeof(TraitWhipLove), typeof(TraitWhipEgg)`
  (`TraitWhipInterest` hérite de `TraitWhipLove`, ne redéclare rien).
- `CardActReplayEvent.Request`, dernière ligne (98) : `return trait is not (TraitTicketFurniture or TraitWrench or TraitEcoMark or TraitToolBrushStrip or TraitToolHammerStrip);`
  (les quatre outils rendent `false` dans le jeu, les fouets `true`).
- `CardActReplayDelta.cs:75` : `card.trait is not (TraitTicketFurniture or TraitSyringe or TraitStethoscope or TraitLeash or TraitWrench or TraitEcoMark or TraitToolBrushStrip or TraitToolHammerStrip or TraitWhipLove)`.
- `CardActReplayDelta.cs:113` : remplacer `using var standIn = RemoteCraft.AsCrafter(sender);` par `using var standIn = PlayerStandIn.For(host, OriginPeer, sender);`
  (même échange de « pc », en plus il recueille le karma pris et l'envoie au joueur : sans cela le `ModKarma(-1)` du fouet-œuf est pris **à l'host**, `PlayerKarma.Reroute` ne voit ni tueur ni progrès,
  `PlayerKarma.cs:62-83`). `PlayerStandIn` est dans `Helper/PersonalQuests.cs:396-437`.

Avec cela : la pile baisse chez tous (`CardModNumDelta` de l'host), l'œuf apparaît pour tous (`Simulate()` de l'host), le fouet ne coûte plus de karma à l'host, l'effet est joué chez l'host (qui fait vivre habitants et sauvegarde).

**Étape 2, l'autre joueur voit le résultat.** Un nouveau « genre » dans `CardSettingDelta` (numéro 826 inchangé, un champ `[Key(5)] public int[]? Numbers`) qui envoie l'état des champs
touchés par ces quatre outils. Code à ajouter :

```csharp
// CardSettingDelta.cs
public const byte Fields = 4;

[Key(5)]
public int[]? Numbers { get; init; }

internal static int[] FieldsOf(Card c)
{
    // read without creating: c_containerUpgrade makes its object when it is read
    var up = c.trait is TraitMagicChest ? c.c_containerUpgrade : null;
    return [
        c.isWeightChanged ? c.c_weight : -1,       // 0 marque ecolo
        c.elements.Base(652),                      // 1 marque ecolo
        c.isDyed ? c.c_dyeMat : 0,                 // 2 brosse
        c.encLV,                                   // 3 marteau
        c.c_containerSize,                         // 4 lit
        up?.cap ?? 0, up?.cool ?? 0,               // 5, 6 coffre magique
        c.things.width, c.things.height,           // 7, 8 agrandir
        c.elements.Base(405),                      // 9 frigo
    ];
}

internal static List<(Thing Thing, int[] Fields)> Snapshot(Point pos)
{
    return pos.Things.Where(t => t.IsInstalled).Select(t => (t, FieldsOf(t))).ToList();
}

internal static void TellChanged(List<(Thing Thing, int[] Fields)> before)
{
    foreach (var (thing, old) in before) {
        if (!thing.isDestroyed && !FieldsOf(thing).SequenceEqual(old)) {
            CardSettingEvent.Tell(thing, Fields);
        }
    }
}
```

Dans `Create` : `Numbers = kind == Fields ? FieldsOf(card) : null`. Dans `OnApply` : le test de tête devient `... || Kind > Fields`, ajouter `if (Kind == Fields && net is ElinNetHost) return;`
(seul l'host envoie ce genre), puis :

```csharp
case Fields when Numbers is { Length: 10 } n:
    if (n[0] >= 0 && thing.c_weight != n[0]) thing.ChangeWeight(n[0]);
    if (n[1] > 0) thing.elements.SetBase(652, n[1]);
    thing.Dye(n[2] == 0 ? null : sources.materials.map.TryGetValue(n[2]));
    if (thing.encLV != n[3]) thing.SetEncLv(n[3]);
    thing.c_containerSize = n[4];
    if (thing.trait is TraitMagicChest) { var up = thing.c_containerUpgrade; up.cap = n[5]; up.cool = n[6]; }
    if (n[7] > 0 && thing.things.GridSize != 0 && (thing.things.width != n[7] || thing.things.height != n[8])) thing.things.SetSize(n[7], n[8]);
    if (n[9] > 0) thing.elements.SetBase(405, n[9]);
    LayerInventory.SetDirty(thing);
    break;
```

Où l'appeler : (a) dans `CardActReplayDelta.OnApply`, `var before = CardSettingDelta.Snapshot(pos);` juste avant `item?.act.Perform()` et `CardSettingDelta.TellChanged(before);` juste après, pour ces quatre traits ;
(b) pour **l'host qui s'en sert lui-même** : dans `CardActReplayEvent.After`, quand `Connection is ElinNetHost` et que `__instance` est l'un des quatre, envelopper
`act.onPerform` : `var before = CardSettingDelta.Snapshot(item.pos); var r = own(); CardSettingDelta.TellChanged(before); return r;`.

Non traités (à dire dans le commit) : tentes de la clé (éléments de la zone-tente, pas un champ d'objet), passe-temps des fouets (`_hobbies`, `_works`, `bio.idInterest` : l'effet de jeu est chez l'host qui fait travailler les habitants ; l'invité voit
l'ancienne valeur dans la fiche jusqu'au prochain chargement), case teinte de la brosse (carte).

Risques : `ChangeWeight` pose `isWeightChanged` ; `Dye(null)` ne recalcule pas la couleur à l'écran avant le prochain rafraîchissement ; `SetEncLv` change des éléments de l'objet (déterministe) ; l'ordre : l'envoi
d'état se fait avant la baisse de pile (la lambda fait `Upgrade` puis `ModNum`), mais `CardSettingDelta` ne dépend pas de la pile (le delta est lu avec `Find()` et l'objet existe encore). Pas de risque de sauvegarde (champs déjà sauvegardés).

### 4. Options (conseil)

- Jusqu'où synchroniser le résultat : (a) étape 1 seule (les effets existent, l'autre joueur a une vue périmée) ; (b) étape 1 + 2 (champs d'objets) ; (c) en plus tentes et passe-temps. Je recommande (b) : ce sont les seuls cas où
  la vue périmée **change ce que l'autre joueur peut faire** (grille de coffre trop petite, lit trop petit). (c) demande deux deltas de plus et change l'état du monde (zones-tentes) : à décider.
- La brosse sur une case : le jeu ne synchronise pas le terrain ; ne pas le traiter ici.

### 5. Brouillon de test (`hunt2_suite.py`, `h11`)

```python
def h11(ctx):
    """clé a molette (lit), marque ecolo, brosse, marteau, fouet-oeuf (ligne 11) : l'effet est chez l'host ET chez l'invite, la pile baisse, l'oeuf existe
    Ce que le banc ne joue pas comme un joueur : voir sous la fonction"""
    wrench = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.trait != null && x.trait.Length > 1 && x.trait[0] == "Wrench" && x.trait[1] == "bed"); return r == null ? "" : r.id;')
    bed, eco, whip = first_id("Bed"), first_id("EcoMark"), first_id("WhipEgg")
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        # --- clé a molette sur un lit
        if wrench and bed:
            t = furniture(uid, make=f'ThingGen.Create("{bed}")')
            size = lambda p: ev(p, f'{thing(t)}.c_containerSize.ToString()')  # noqa: E731
            s0 = size(H)
            tool = give(ctx, key, wrench, 3)
            x, z = (int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(","))
            awake(port)
            log(f"{who} : {use_held(port, tool, at=(x, z), pick=f'i.tc != null && i.tc.uid == {t}')}")
            check(cond=eventually(lambda: size(H) == str(int(s0) + 1) and size(A) == str(int(s0) + 1), timeout=15), label=f"{who} : le lit a un couchage de plus chez l'host ({size(H)}) et chez l'invite ({size(A)})")
            check(f"{who} : une cle de moins ({count(H, uid, wrench)})", eventually(lambda: count(H, uid, wrench) == 2 and count(port, uid, wrench) == 2, timeout=10))
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')
        # --- marque ecolo sur un meuble
        if eco:
            t = furniture(uid)
            w = lambda p: ev(p, f'var t = {thing(t)}; return t.Evalue(652) + "/" + t.Weight;')  # noqa: E731
            w0 = w(H)
            tool = give(ctx, key, eco, 2)
            ...  # use_held(port, tool, at=(x, z)) sans pick (l'entree n'a pas de cible)
            check(cond=eventually(lambda: w(H) == w(A) and w(H).startswith("10/") and w(H) != w0, timeout=15), label=f"{who} : marque ecolo posee, poids pareil chez l'host et l'invite ({w(H)} / {w(A)})")
        # --- fouet-oeuf : karma de qui l'a donne, oeuf pour tous
        if whip:
            res = spawn(uid, "putty", "Friend")
            k0 = {p: int(ev(p, 'EClass.player.karma.ToString()')) for p in (H, A)}
            tool = give(ctx, key, whip)
            ...  # use_held(port, tool, at=(res.x, res.z), pick=f'i.tc != null && i.tc.uid == {res}')
            check(f"{who} : un oeuf est apparu chez l'host et chez l'invite", eventually(lambda: eggs(H) > 0 and eggs(A) == eggs(H), timeout=15))
            fouetteur, autre = (A, H) if key == "a" else (H, A)
            check(f"{who} : le karma est retire a celui qui fouette ({k0[fouetteur]} -> {int(ev(fouetteur, 'EClass.player.karma.ToString()'))}), pas a l'autre",
                  eventually(lambda: int(ev(fouetteur, 'EClass.player.karma.ToString()')) == k0[fouetteur] - 1, timeout=10)
                  and int(ev(autre, 'EClass.player.karma.ToString()')) == k0[autre])
            drop([res])
```

Chemin réel : `HotItemHeld` → `TrySetAct` du jeu (le clic droit avec l'objet en main : `use_held` de `guest_suite`, qui construit la liste des actions et exécute celle qui répond à `pick`). Le test passe donc
par le vrai `TrySetHeldAct` et par la lambda remplacée du mod. Ce que le banc ne joue pas comme un joueur : la souris sur la case ; le karma suppose l'option « karma personnel » (sans elle le karma est commun, la ligne de
`PlayerKarma.Reroute` ne distingue pas) ; la marque écolo, la brosse et le marteau sont à écrire sur le même modèle (`Dye` posé avant l'ajout à la carte par `extra`, `encLV` par `t.SetEncLv(3)`) ; l'`ID` de la clé « lit » dépend
des données du jeu (cherché dans `sources.things`) ; les tentes et les passe-temps (étape non faite) ne sont pas testés.

---

## Non vérifié

- **Tout** : rien n'a été compilé ni joué ; les diffs ci-dessus n'ont pas été passés au compilateur (noms de membres lus dans le décompilé et le code du mod, pas essayés).
- Ligne 8 : que l'host rejoue bien la lecture du parchemin et le sort d'un invité sur la copie de cet invité, au moment où `Chara.Tick` marque `ActingRemotePlayer` ; que `sender.party` est bien le groupe de l'host
  (`EClass.pc.party` pendant la substitution) ; que `RemoteCard.Create` marche pour un compagnon mort hors carte ; que `ListPeopleRevive` se clique par `ItemGeneral.button1` ; que `CharaReviveDelta` côté invité suffit à
  rebrancher un compagnon (message, groupe) ; combien de temps l'invité reste sans voir son compagnon relevé par l'host avant le correctif (rapprochement périodique).
- Ligne 7 : que `UIContextMenuManager.Instance.currentMenu` est bien le menu de tri au moment où l'écouteur ajouté s'exécute (après l'écouteur du jeu) et que `onDestroy` est appelé sur tous les chemins de fermeture ;
  le comportement quand la fenêtre se ferme en même temps que le menu.
- Ligne 9 : que l'objet déposé par l'invité est réellement perdu aujourd'hui (lecture seule : `DelayDestroy` + dépôt local) ; l'ordre d'arrivée « création du coffre, réponse » ; le contenu d'un coffre rempli avant
  l'arrivée de l'invité ; la quête `vernis_gold` pour le test (ici simulée par `debug.enable`) ; `DragItemCard.DragInfo(ButtonGrid)` utilisé tel quel.
- Ligne 10 : qu'aucun autre tirage ne s'intercale entre `GetOfferingValue` et les deux `rnd` du duel (le correctif le rend sans objet, mais le test doit le montrer) ; que `Simulate()` autour de `OnOffer` ne double aucun effet
  (message, karma de l'objet volé, boule de punition) ; `ElementChangeDelta` de la piété arrive avant le delta d'offrande.
- Ligne 11 : le résultat exact de `PlayerStandIn.For` quand le karma personnel est coupé ; `TrySetHeldAct` des fouets chez l'host quand `EClass.pc.CanSee` est évalué pour la copie de l'invité ; `Dye(null)` et `SetEncLv`
  appliqués à une copie ; l'ordre des entrées d'une case à plusieurs meubles (repli `Index` de `CardActReplayDelta`) pour la marque écolo et la brosse, dont l'entrée n'a pas de cible ; les tentes ; les passe-temps.
- Numéros d'union : 830 et 831 supposés libres (rien au-dessus de 829 dans `ElinDelta.cs` à ce jour) ; pas cherché dans l'historique git si 108, 815, 818, 820 ont servi.
