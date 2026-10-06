# Fenêtres de l'invité fermées à chaque changement de carte (retour 0.26.532, 7 octobre 2026)

Lecture du code + correction écrite, **rien n'a été joué**. Compilation ReleaseNightly : 0 erreur.
Test à lancer : `python _tools/windows_suite.py` (deux fenêtres déjà ouvertes par `mp_test.py`).

## 1. Le jeu seul (`dev/_decomp/Elin_23351`, `Plugins.UI`)

- Sac, sacs portés ouverts, aptitudes, liste de fabrication : des calques de `ui.layerFloat` (`UI.cs:49`), pas de
  `ui.layers`. `Scene.Init` ne vide que `ui.layers` (`Scene.cs:181`, `Layer.cs:501`) : un changement de carte ne les touche pas.
- Seul `Game.Kill` les ferme (`Game.cs:1137` -> `UI.OnKillGame`, `UI.cs:198` : `layerFloat.RemoveLayers(true)`, et
  `widgets.OnKillGame` détruit tous les widgets, `WidgetManager.cs:123`).
- Au chargement, `Game.Load` les rouvre (`Game.cs:340-354`) d'après `player.pref.layerInventory / layerAbility`, écrits par
  `Game.Save` (`Game.cs:1075-1080`). `OpenFloatInv` rouvre le sac puis les conteneurs dont `c_windowSaveData.open` est vrai (`UI.cs:649-669`).
- Fermer une fenêtre remet `open` à faux (`Window.cs:1116-1122`).

Où vit l'état :

| Quoi | Où | Sorte |
|---|---|---|
| sac / aptitudes ouverts | `Player.pref.layerInventory`, `layerAbility`, `layerCraft` (`Player.cs:33-37`) | (a) sauvegarde |
| place et taille du sac, des aptitudes | `Window.dictData` (statique, `Window.cs:594`) = `Player.dataWindow` (`Player.cs:1179`, `:1511-1514`, `:1540`), clés `LayerInventoryFloatMain0`… | (a) sauvegarde |
| réglages de la fenêtre d'aptitudes | `Player.layerAbilityConfig` (`Player.cs:1107`), tri `pref.sortAbility`, onglet `pref.lastIdTabAbility` | (a) |
| place, taille, « ouvert », tri, filtres d'un sac porté | `Thing.c_windowSaveData` (`Card.cs:1860`, `LayerInventory.cs:450-479`) | (b) sur l'objet |
| barre d'objets du bas | objets du sac avec `invY == 1` + la ceinture | (b) |
| widgets (mini-carte, journal, barres) : place, actif ou non | `Player.mainWidgets / subWidgets / useSubWidgetTheme` (`Player.cs:1050, 1098-1101`) | (a) |
| contenu des barres de raccourcis | `Player.hotbars` (`Player.cs:1155`) | (a) |
| zoom (valeurs), toit, inclinaison, tactiques, préférences | `Game.config` (`Game.cs:10-98`) | (a) |
| zoom éloigné en cours | `ActionMode.Adv.zoomOut2` (`AM_Adv.cs:106`), refait par `ActionMode.OnGameInstantiated` | (c) mémoire |
| journal déplié | `WidgetMainText.box.isShowingLog` | (c) mémoire |
| carte au trésor ouverte | `LayerTreasureMap` dans `layerFloat` (`TraitScrollMapTreasure.cs:32`) | (c) mémoire |

## 2. Le mod, chez un invité

| Chemin | Fenêtres | Pourquoi |
|---|---|---|
| (i) suivre l'host sans copie du monde (`ElinNetClientZone.cs` `OnZoneActivateResponse`, branche `else`) | restent | même `core.game`, `player.MoveZone` -> `Scene.Init` comme en solo |
| (ii) copie du monde (`ElinNetClientPlayer.cs` `OnSaveDataProbe`) | **fermées** | `scene.Init(Scene.Mode.None)` fait `game.Kill()` ; puis `core.game = probeGame` : le `Player` reçu est celui de l'host (ses `pref`, `dataWindow`, widgets, barres, `Game.config`) ; le mod ne rejoue pas la fin de `Game.Load` |
| (iii) partir seul (`ElinNetClientTravel.cs` `TravelTo`) | restent | `pc.MoveZone`, même jeu |
| (iv) rechargement sur place (`AdoptHostCopy`, `RequestZoneState`) | restent | `ui.RemoveLayers()` ne touche que `ui.layers` (un coffre de la carte), pas `layerFloat` |

(ii) arrive à chaque retour auprès de l'host, à chaque rappel, à chaque entrée dans la carte d'un autre joueur : c'est le défaut signalé.
Les sacs portés : leur `c_windowSaveData` vient de la copie de l'host, qui n'a que ce que le personnage rapportait à son dernier retour.

## 3. Correction (`ElinTogether/Helper/OpenWindows.cs`)

- `Keep()` (`ElinNetClientPlayer.cs:189`, avant la destruction du jeu) : écrit les places comme `Game.Save` (`player.OnBeforeSave`,
  `widgets.UpdateConfigs`), note sac ouvert / aptitudes ouvertes / conteneurs portés ouverts (uid) / `c_windowSaveData` de tout ce
  que porte le joueur (uid) / l'ancien `Player` et `Game.config`.
- `Carry(chara)` (`:224`, avant `OnGameInstantiated` et `OnLoad`) : recopie dans le nouveau `Player` ce qui est l'écran du joueur
  (liste en 4), remet les `c_windowSaveData` sur les objets retrouvés par uid.
- `Reopen()` (`ElinNetClientZone.cs:223`, après `scene.Init(Scene.Mode.Zone)`) : comme la fin de `Game.Load`. Rien si le joueur est
  mort ; pas de double (teste ce qui est déjà ouvert) ; seulement ce que porte le joueur (un coffre de la carte n'est jamais noté).

## 4. Host, et réglages d'affichage

Host : ses fenêtres restent (son jeu n'est jamais remplacé quand il change de carte avec des invités). Créer son personnage
dans le monde d'un autre (`ElinNetHostHandOver.cs:179-202`) passe par `Game.Load`, qui les rouvre.

Remplacé par celui de l'host à chaque copie du monde, **corrigé** par `Carry` : `pref` (tris, sac/aptitudes ouverts, onglet),
`dataWindow`, `layerAbilityConfig`, widgets (place, mini-carte ouverte ou non, thème), `hotbars` (raccourcis), `Game.config`
(zoom, toit, tactiques, préférences), `windowAllyInv`, `openContainerCenter`, `dataPick`, `favAbility`, `priorityActions`,
`questTracker`, `tracked*`, `memo`, `memo2`, filtres et tri des sacs portés, zoom éloigné.

Reste (noté, pas fait) :
- première connexion de la séance (et après une déconnexion) : rien à reprendre, l'invité part de l'écran de l'host. Il faudrait
  garder l'écran dans un fichier par monde et par personnage.
- journal déplié, carte au trésor ouverte, sac d'un compagnon ouvert : perdus à chaque copie du monde.
- `Player.currentHotItem`, `lastRecipes`, `cinemaConfig`, `knownBGMs`, `popups` : ceux de l'host, non regardés.
- un joueur mort au moment où la carte arrive ne retrouve pas ses fenêtres en revenant à la vie.
