# La nuit : chacun dort pour soi (conseil 10, point iii) — 2026-10-06

État : **écrit, compile en ReleaseNightly (0 erreur), jamais joué** (le jeu était pris). Tests écrits, à lancer :
`python _tools/sleep_suite.py --only n1,n2,n3,n4`, puis la suite entière, puis `trio_sleep_suite.py` (trois fenêtres).
Règle : `NetSession.Instance.Rules.UseOwnSleep` (case host « OwnSleep »). Décochée = l'ancien comportement.
`J:` = `dev/_decomp/Elin_23351/`, `M:` = `ElinTogether/`, `SSC` = `M:Patches/Synchronization/SleepSynchronizationContext.cs`.

## 1. Comment ça marche

Deux sortes de nuit, un seul drapeau dans chaque jeu (`_ownNight` : « l'écran de nuit de ce jeu est la nuit de son
joueur seul »).

**Nuit à soi** (quelqu'un d'autre est debout) : l'écran de nuit tourne sans toucher à la date, puis le joueur se
réveille de lui-même.
- *Host* : son sommeil du jeu, sans attente (`GateSleepTick`). Pendant le tour qui lance la nuit et pendant la fin de
  nuit du jeu, « le groupe » est réduit à l'host et ses propres compagnons (`NarrowParty` / `RestoreParty`) : le jeu
  n'endort (J:ConSleep.cs:131-137), ne soigne ni n'affame (J:LayerSleep.cs:76-79) personne d'autre. Les familiers
  des autres restent où ils sont (`ShieldOtherPlayers`, déjà là). Rien n'est envoyé aux invités (`OnHostSleep`).
- *Invité sur la carte de l'host* : il demande (`SleepRequestDelta`, avec ses heures de nuit), l'host pose le
  sommeil sur son personnage et fait pour lui ce que le jeu fait pour le joueur local (`OnGuestAsleep` : ses
  familiers contre lui, ses compagnons s'endorment, plus de saignement / poison / miasme). Dès que le sommeil revient
  chez lui, son jeu ouvre l'écran de nuit (`Update`). À la fin, il joue SON réveil (`CharaSleepDelta.WakeOwn`, le
  réveil écrit pour le point 10) et le dit à l'host (`CharaSleepDelta` avec `Own`) : l'host retire le sommeil du
  personnage et repose le personnage et ses compagnons avec la puissance de SON lit (les PV sont tenus par l'host).
- *Invité seul sur sa carte* : le sommeil du jeu, sans avancer la date (`OnAdvance`). Il dit lui-même à l'host
  « je dors » / « je ne dors plus » (`SleepStateDelta`, numéro 840).

**Nuit du monde** (tous les joueurs vivants et connectés dorment, où qu'ils soient) : c'est la nuit d'avant, celle du
jeu de l'host (date +10 minutes par pas, fin de nuit pour tout le groupe, `CharaSleepDelta` qui réveille chacun).
- L'host se couche le dernier : au tour qui lance sa nuit tout le monde dort déjà, c'est la nuit du monde.
- Un invité se couche le dernier pendant que l'host dort sa nuit à lui : `Update` transforme l'écran de nuit de
  l'host (remis à zéro, heures du dernier couché) et envoie `SleepStartDelta`. Les écrans de nuit des invités, déjà
  ouverts, attendent alors le réveil de l'host.
- La date n'avance que dans le jeu de l'host du monde, par `GameDate.AdvanceMin` (chemin existant), une fois.

**Se coucher** : fatigué seulement (la règle du jeu), sauf si quelqu'un dort déjà (`AllowPartySleep`, compteur
`Sleepers` : l'host le calcule, les invités le reçoivent par `SleepReadyDelta`).

**Qui compte** : les joueurs de la carte de l'host (comme avant), plus, avec la règle, les joueurs partis ailleurs
(l'host les lit dans ses liens réseau ; ils sont « endormis » quand ils l'ont dit). Avant, un joueur parti ne
comptait pas du tout : l'host seul sur sa carte faisait passer la nuit pour tous.

## 2. Ce qui a été changé

| Fichier | Quoi |
|---|---|
| `SSC` | presque tout (voir 1). `OnClientAdvance` devient `OnAdvance` + `OnAdvanceEnd` ; `BringCompanionsBeside` devient `BringBeside` (un joueur) ; `_bed` effacé à chaque fin de sommeil |
| `M:Models/Delta/Chara/CharaSleepDelta.cs` | `WakeOwn`, champ `Own` (clé 4), l'host repose le dormeur et ses compagnons ; rapport envoyé dans un `finally` ; un joueur debout n'est plus « reposé » par la nuit des autres (règle cochée) |
| `M:Models/Delta/Misc/SleepRequestDelta.cs` | champ `Hours` (clé 0), appel de `OnGuestAsleep` |
| `M:Models/Delta/Misc/SleepReadyDelta.cs` | champ `Name` (clé 4), compteur `Sleepers`, texte `emp_ui_sleep_count`, rien d'affiché au réveil (règle cochée) |
| `M:Models/Delta/Misc/SleepStartDelta.cs` | `JoinNight` : un joueur debout est laissé tranquille, un écran de nuit déjà ouvert devient celui de la nuit du monde |
| `M:Models/Delta/Misc/SleepCancelDelta.cs` | la nuit à soi de l'host ne bloque plus l'annulation d'un invité |
| `M:Models/Delta/Misc/SleepStateDelta.cs` | NEUF, 840 |
| `M:Models/Delta/ElinDelta.cs:124` | `[Union(840, typeof(SleepStateDelta))]` (841 pas pris) |
| `M:Net/Host/ElinNetHostUpdate.cs:116` | liste blanche : `or CharaSleepDelta or SleepStateDelta` |

## 3. Lignes qui manquent ailleurs (fichiers interdits pour ce lot)

1. **`M:Net/Client/ElinNetClientTravel.cs:941`** (`ApplyChatWhileAway`, ce qu'un joueur parti accepte de l'host).
   Sans elle, un joueur parti ne lit pas « Alice dort (1 sur 3) », ne peut donc rejoindre un dormeur que s'il est
   fatigué, ne lit pas « Tout le monde dort », et n'est pas réveillé par l'host : sa nuit finit seule, quelques
   secondes avant ou après, et sa date rattrape celle du monde (comme pour tout saut de date).
   - avant : `... or WorldDateAdvanceDelta or WeatherDelta or DayDataDelta or QuestFollowDelta) {`
   - après : `... or WorldDateAdvanceDelta or WeatherDelta or DayDataDelta or QuestFollowDelta or SleepReadyDelta or SleepStartDelta or CharaSleepDelta) {`
   Le code de ces trois messages est écrit pour ce cas (`JoinNight(…, away)`, `EndAwayNight`), **jamais exécuté**.
2. `M:Net/Base/ElinNetBase.cs` : `internal IReadOnlyList<ISteamNetPeer> Peers => Socket.Peers;` remplacerait le
   `FieldRefAccess` sur `Socket` (marqué `// ponytail:` dans `SSC`). Confort, pas nécessaire.

## 4. Textes à ajouter (pas faits : `package/LangMod` est hors de ce lot)

Appelés par `.Loc(...)` (qui passe par `.lang()`), comme les textes voisins. Rien à réutiliser : les trois textes
de sommeil existants (`emp_ui_sleep_request`, `_wish`, `_cancel`) restent ceux de la règle décochée.

| Identifiant | Anglais | Japonais | Chinois |
|---|---|---|---|
| `emp_ui_sleep_alone` | You slept. The world did not move on: {0} still awake. | 眠った。世界の時間は進まなかった：{0} がまだ起きている。 | 你睡了一觉。世界的时间没有前进：{0} 还醒着。 |
| `emp_ui_sleep_count` | {0} is asleep ({1} of {2}) | {0} は眠っている（{1}/{2}） | {0} 睡着了（{1}/{2}） |
| `emp_ui_sleep_all` | Everyone is asleep: the night passes. | 全員が眠った：夜が過ぎていく。 | 所有人都睡着了：夜晚过去了。 |

`{0}` de `emp_ui_sleep_alone` : les noms séparés par des virgules (« … » si ce jeu n'en connaît aucun).

## 5. Tests

`dev/_tools/sleep_suite.py` : N1 (l'invité dort, l'host marche), N2 (l'inverse), N3 (les deux : une nuit), N4 (reposé :
refusé seul, accepté si l'autre dort ; deux sens). Étapes d'avant adaptées : B2 et B3 (« l'invité renonce » : avec la
règle il dort sa nuit seul, `give_up`), Y1 (« l'heure a avancé » devient « la date n'a pas sauté »), textes de Z1 et P2.
`dev/_tools/trio_sleep_suite.py` (NEUF, trois fenêtres) : Q1 deux couchés un debout, Q2 trois couchés, Q3 un joueur
ailleurs.

## 6. Ce qu'on peut perdre, ce qui n'est pas sûr

- **Rien n'a été joué.**
- La fenêtre pour « dormir ensemble » est la durée de l'écran de nuit du premier couché (quelques secondes, pas
  mesurée). Si elle est trop courte en vrai : l'allonger (ne pas fermer l'écran de nuit à soi tant qu'un autre
  joueur est en train de s'endormir), sans faire attendre personne.
- Un invité se réveille de sa nuit à lui au moment exact où le dernier se couche (le temps d'un aller-retour
  réseau) : l'host le compte encore endormi, la nuit passe, et lui la voit sauter debout. Il n'est pas reposé deux
  fois chez lui ; chez l'host son personnage reçoit deux fois les PV du repos.
- Un joueur parti ailleurs et mort compte comme vivant : il empêche la nuit commune jusqu'à son retour.
- L'invité s'endort sans les 15 tours de décompte de l'host (son écran de nuit s'ouvre dès que l'host a répondu) :
  petite différence host / invité, assumée.
- L'host qui dort sa nuit seul sur sa carte avec des amis ailleurs fait toujours le tour de ses bases en retard
  (`OnSimulateFaction` n'a pas changé) ; sans heures passées il n'y a rien à rattraper, pas vérifié.
- Chez l'invité, « qui est éveillé » (`emp_ui_sleep_alone`) ne connaît que les joueurs de sa carte.
- Pendant la nuit à soi de l'host, son sommeil ne finit plus un tour après le début de la nuit (c'était le cas en
  session, où le jeu n'est pas en pause) : il dort jusqu'à la fin de l'écran, comme en solo. Règle cochée seulement.
- Le visiteur d'un autre invité (session de carte) : écrit sur le même modèle (celui qui tient la carte y joue le
  rôle de l'host, sans jamais toucher à la date), jamais exécuté.
- Oreiller d'Opatos, boîtes-repas, sauvegarde automatique : la fin de nuit du jeu les fait aussi pour la nuit à soi
  de l'host (comme une nuit solo).
- `SSC` lit la liste des liens réseau de l'host à chaque image (une petite liste copiée).
