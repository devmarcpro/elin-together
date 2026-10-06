# Joueurs invisibles les uns pour les autres (partie à 4 du 6 octobre, 0.26.524)

Lu : les trois journaux de la partie (hors dépôt) et le code. Rien n'a été lancé. Horloges : le journal d'Arma Minima
avance d'environ 35 s sur celui de l'host Layinne, celui de LemiWinks aussi.

## 1. La cause principale (prouvée par les journaux) : plus aucun patch après la fermeture d'une session de zone

`ElinTogether/Net/Base/ElinNetBase.cs`, `OnDestroy` : en version Release (`#if !DEBUG`) chaque composant réseau détruit
retirait TOUS les patchs du mod (`SharedHarmony.UnpatchSelf()`), et ils ne revenaient qu'à la création du composant
suivant (`Awake`). Une session de zone qui se ferme (rappel par l'host, dernier invité parti, refus de validation) laisse
le lien avec l'host vivant, mais sans un seul patch : plus rien n'est envoyé ni appliqué image par image
(`CoreSynchronizationContext`), les positions (qui passent par la même file) non plus. L'invité ne voit alors que ce que
sa copie du monde et le fichier de carte ont posé à l'activation : les personnages globaux dont `currentZone` est cette
carte DANS SA COPIE. Les autres joueurs (hors carte ou sur la carte du monde au moment de la copie) n'y sont pas, et un
rechargement de carte ne les rend pas. Le banc tourne en Debug : il ne pouvait pas le voir.

Corrigé pendant ce travail par un autre agent (commit f910922 : les patchs ne partent qu'avec le dernier composant).

Preuves :
- Tous les signalements « personnages en moins » sont dans un séjour qui suit la fermeture d'une session de zone sans
  nouveau composant : Arma 20:25:46 (session fermée 20:25:35), LemiWinks 20:25:53 (20:25:44) et 20:28:14 (20:28:14),
  Arma 20:45:59 (20:45:52) et 20:50:52 (20:50:25). Aucun dans les séjours ouverts par une connexion neuve ou par un
  retour de voyage sans session de zone (Arma 20:19:42, LemiWinks 20:18:18), sauf le cas passager du point 3.
- Arma, 20:25:46 à 20:27:00 : aucune ligne venant d'un delta ou d'une position pendant 71 s. L'host a émis
  `Element 301 changed on chara 1` à 20:25:24, puis 72 et 261 à 20:25:52 et 20:25:55 : Arma les applique TOUS à
  20:27:00.29, d'un bloc, avec 48 `Reconcile force move` (les positions retenues), au moment où un appel direct vide la
  file (`StayAsGuest` → `WorldStateDeltaProcess()`).
- LemiWinks, 20:25:54 à 20:26:39 : aucune ligne de delta en 46 s ; `charas 8/10` deux fois, rechargement sans effet :
  sa copie du monde (prise par l'host à 20:25:10.33, host sur la carte du monde) a 541 et 658 hors carte.
- Host, 20:25:12 à 20:26:25 : 58 `Reconcile force move` des personnages 541, 582, 658 (les trois invités marchent chez
  eux, leurs pas n'arrivent plus que par leurs positions).
- Les nombres : `8/10` = les 2 autres joueurs ; `Zone_field 5/8` et `6/7` chez Arma = l'host et son groupe, qui étaient
  sur la carte du monde dans sa copie ; `11/13` puis égal après rechargement puis `12/14, things 17/18` = des
  personnages NON globaux apparus chez l'host, jamais annoncés (deltas non appliqués), rendus par le fichier de carte.
- `9/9 (not the same ones)` chez Arma à 20:26:43 : le départ de 582 (`CharaRemoveFromGameDelta`) attendait dans la file.

## 2. Le cycle de la copie d'un joueur B dans le jeu d'un invité A (lu dans le code)

| Moment | Ce que l'host fait et envoie | Ce que A fait | B chez A |
|---|---|---|---|
| A reçoit le monde | `SendSaveProbe` (copie du monde + carte) | charge ; `Zone.AddGlobalCharasOnActivate` pose les globaux dont `currentZone` = cette carte | dans `globalCharas` si B existait ; posé seulement si B était sur cette carte dans la copie |
| A est placé | `OnZoneDataReceivedResponse` puis `RemoveLeftOverCharas(null)` : `CharaRemoveFromGameDelta` pour CHAQUE personnage de joueur que personne ne joue | sort B du groupe, de `globalCharas`, de la carte, du `CardCache` | inconnu si B n'est pas joué |
| B rejoint ou revient (monde envoyé à B) | `SendSaveProbe(B)` : `CharaMakeAllyDelta(B)`, `ZoneAddCardDelta(B)` ; B est DÉJÀ sur la carte de l'host | `MakeAlly` : B introuvable, remis à plus tard (7200 images) ; `ZoneAddCard` : jeté | inconnu, l'host l'a sur sa carte : A ne le voit pas (voir 3) |
| B est placé | `CardGenDelta(B)` (données entières), position, `BringCompanions` : `CardGenDelta` + `ZoneAddCardDelta` + `CharaMakeAllyDelta` par compagnon | crée B (cache, et maintenant `globalCharas`) ; le `MakeAlly` en attente passe (groupe, `globalCharas`) ; les positions le posent | connu, sur la carte |
| B part voyager, ou se déconnecte | `RemoveRemoteChara` + `TakeCompanionsAlong` : `CharaRemoveFromGameDelta` pour B et chaque compagnon | les retire de tout | inconnu |
| l'host change de carte, B ailleurs | carte à tous ; à chaque joueur placé, de nouveau `CharaRemoveFromGameDelta(B)` | recharge ; B reste inconnu | inconnu |
| A part voyager | rien pour A (les deltas reçus loin de l'host sont jetés, sauf la discussion) | joue seul | la copie qu'il avait |
| A revient | monde neuf | tout est refait | comme à la première ligne |

Un compagnon de B suit exactement B (mêmes messages, `OwnerUid` dans `CharaMakeAllyDelta`).

## 3. Autres trous trouvés

1. **Passager, 5 à 8 s (prouvé)** : l'host pose B sur sa carte dès `SendSaveProbe` (`chara.MoveZone`), les autres ne
   reçoivent `CardGenDelta(B)` qu'au placement de B. Preuve : 20:41:22.69, les deux invités signalent `charas 10/11`
   50 ms avant `Assigned zone sync position` du 3e joueur ; plus rien après. Si B ne finit jamais de charger, B reste
   invisible. Correction (fichier interdit, non faite) : `ElinTogether/Net/Host/ElinNetHostPlayerManager.cs`,
   `SendSaveProbe`, avant `chara.MakeAlly();` ajouter
   `Delta.AddRemote(CardGenDelta.Create(chara));` (les autres le créent tout de suite, `ZoneAddCardDelta` le pose ; le
   `CardGenDelta` du placement est alors sans effet). Pas vérifié en jeu.
2. **Un personnage reçu par `CardGenDelta` n'était pas dans `globalCharas`** (lu, pas vu dans ces journaux : le
   `CharaMakeAllyDelta` l'y remet quand il passe). S'il ne passe pas (attente dépassée) ou pour un renvoi du détecteur,
   le personnage ne tenait que par la carte : au rechargement suivant il n'était plus posé et pouvait disparaître de la
   mémoire. Corrigé : `CardGenDelta.cs` (ajout à `globalCharas`), et `CharaStateSnapshot.cs` (même chose quand une
   position pose un personnage global connu du cache seul).
3. **Les affaires d'un NOUVEAU joueur en double dans le cache (prouvé)** : Arma 20:16:44 et 20:18:39, 18 lignes
   `Card uid conflict: uid 583… refusing incoming`. L'host crée les affaires du nouveau personnage une à une
   (`CardGenDelta` par objet), puis envoie le personnage entier : chez les invités déjà là, le cache gardait les copies
   isolées, pas celles du sac. Tout delta suivant sur ces objets touchait la mauvaise copie (sac qui dérive). Corrigé
   dans `CardGenDelta.cs` : les objets portés par la carte reçue remplacent une copie sans parent.
4. Pas corrigé : `CardGenDelta.cs`, branche « déjà dans `globalCharas` » : A garde SA copie de B même si l'host vient
   de remplacer la sienne par celle que B a rapportée (`ReplaceRemoteChara`) entre la copie du monde de A et le
   placement de B. Sac de B faux chez A jusqu'au prochain monde. Fenêtre étroite (vue : LemiWinks 20:25:10 à 20:25:11).

## 4. Le renvoi du détecteur (`NetDesync.Explain`, `CardGenDelta` à tous)

- Invité qui ne connaît pas le personnage : créé, mis au cache et (maintenant) dans `globalCharas` ; la position
  suivante le pose (`CharaStateSnapshot` : même zone, pas sur la carte → `AddCard`). Un rechargement le garde.
- Invité qui l'a (cache, même sorte, pas détruit) : retour immédiat, rien de doublé. Invité qui l'a dans
  `globalCharas` mais plus au cache : sa copie est remise au cache, pas de deuxième objet.
- Rien à changer dans `NetDesync.cs`.

## 5. Sacs des autres joueurs, condition sans élément

- `CardAddThingDelta.cs` : carte détruite chez l'invité + données jointes → sortie du cache et refaite.
- `CharaPickThingDelta.cs` / `CharaPickThingEvent.cs` : `TryStack` (clé 4) transporté et rejoué.
- `CharaSwitchHeldDelta.cs` : une copie lâche ce qu'elle tient sans l'empiler (`held = null` si l'objet est dans son
  sac) ; l'empilement du vrai joueur arrive par `CardTryStackToDelta`.
- `CharaAddConditionDelta.cs` / `CharaAddConditionEvent.cs` : `RefVal`, `RefVal2` (clés 5 et 6) : `ConWeapon` lisait
  l'élément 0 (`KeyNotFoundException ''`).

## 6. Test

`dev/_tools/trio_place_suite.py --only q5` (jamais lancé, trois fenêtres). Le banc est en Debug : il ne rejoue pas la
cause du point 1. Pour elle : une partie en version Release où l'host entre sur la carte tenue par un invité qui a
lui-même un invité, puis `world_diff`.
