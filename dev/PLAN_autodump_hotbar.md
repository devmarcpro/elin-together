# Rangement automatique de l'host : objets sortis de sa barre d'outils (retour 0.26.506, 6 octobre 2026)

Lecture seule faite le 6 octobre. Rien n'a été joué : tout ce qui est marqué « non vérifié » est une déduction du code.
Code du jeu : `dev/_decomp/Elin` (identique à `Elin_23351` pour `TaskDump.cs` et `UIInventory.cs`).

## 1. Ce que fait le jeu (vanille)

- Le bouton ou la touche « ranger » appelle `TaskDump.TryPerform` (`TaskDump.cs:6-23`, `AM_Adv.cs:878`,
  `LayerInventory.cs:292`, `UIInventory.cs:854`). Seulement dans une base ou une tente. `pc` doit être sans but.
- `Run` (`TaskDump.cs:30-128`) liste les coffres de la carte dont le réglage `autodump` n'est pas « none » et qui ont
  quelque chose à prendre (`:136-155`), les visite un par un, puis `c.AddCard(objet)` (`:115`) : l'objet change de parent,
  il est empilé avec ce que le coffre contient déjà si ça s'empile (donc il peut « disparaître » dans une pile).
- Défaut des coffres : `AutodumpFlag` vaut `existing` (= 0, `Plugins.BaseCore/AutodumpFlag.cs:3`, `Window.cs:206`) ; tout
  coffre déjà ouvert une fois a donc « ranger ici ce qui s'y trouve déjà ». Les autres modes : `sameCategory`, `distribution`
  (dans ce mode, un drapeau vide accepte TOUT : `TaskDump.cs:199-206`).
- D'où il prend : `EClass.pc.things.Foreach(...)` (`:172, :214, :246`). `ThingContainer.Foreach` (`ThingContainer.cs:867-879`)
  descend dans tout sous-conteneur ouvrable (`Thing.CanSearchContents`, `Thing.cs:97-106`). La ceinture à outils est un
  conteneur équipé (`TraitToolBelt.cs`, `Player.cs:1744` : chaque personnage en a une) : le rangement entre donc dedans.
- Ce qu'il laisse (`ExcludeDump`, `TaskDump.cs:271-294`) : objet équipé, `c_isImportant`, `CanOnlyCarry`, non jetable, **objet
  de la barre de raccourcis (`IsHotItem` = `invY == 1`, `Card.cs:122`)**, la ceinture elle-même (`TraitToolBelt`), les
  capacités (`TraitAbility`), un conteneur non vide, le pourri si le coffre dit « pas de pourri », et tout ce dont le parent a
  la case « exclure du rangement » (`excludeDump`, `:289-293`).
- Il ne regarde PAS : l'objet tenu en main (`held`) qui n'est pas dans la barre (`invY == 0`), ni le verrou `c_lockLv` de
  l'objet (seulement celui du conteneur), ni `isNPCProperty` de l'objet.
- Piège central (non vérifié en jeu) : la case « exclure du rangement » (`UIInventory.cs:651-657`) est dans le menu de la
  fenêtre, mais la fenêtre de la ceinture n'a pas de menu (`UIInventory.cs:293-296` : `cgFloatMenu` désactivé). Le contenu de
  la ceinture ne peut donc pas être protégé par le joueur, et il est pris par le rangement.
- La barre d'outils du bas : un objet posé là reste dans `pc.things` avec `invY = 1`. Il perd ce rang si le jeu le retire puis le
  remet sans préciser (`Card.cs:3325` et `:3535` remettent `invY = 0`). Alors plus rien ne le protège.
- Jouer d'un instrument : `TraitToolMusic.TrySetHeldAct` lance `AI_PlayMusic { tool = l'objet }`. `Run` (`AI_PlayMusic.cs:46-48`)
  lit `owner.Tool`, qui est l'objet tenu (`Card.cs:2479-2489`). Aucun déplacement d'objet du joueur dans `Run` ; `ThrowReward`
  (`AI_PlayMusic.cs:472+`) ne fait que donner au joueur.

## 2. Ce que fait le mod sur ces chemins

- Le rangement n'est PAS rejoué chez les autres : `CharaTaskRemoteEvent.cs:72-77` (la ligne `TaskDump` a été retirée par
  `f4c5b44`) ; il reste `TaskDumpArgs.cs` mais plus rien ne l'envoie. Aucun patch sur `TaskDump`, ni sur le bouton.
- Chaque objet rangé passe par `Card.AddThing` : `CardAddThingEvent.cs:63-137` envoie `CardAddThingDelta`. Si le coffre n'est
  pas dans le cache et que c'est l'host, rien n'est envoyé (`:113-120`) : l'invité garde alors l'objet dans la ceinture de
  l'host de son côté (écart d'affichage, pas une perte chez l'host).
- Réglages de coffre : `InvSaveDataDelta.cs:34-36` ignore tout conteneur dont la racine est un personnage (sac, ceinture) ;
  l'envoi les ignore aussi (`InvRefreshMenuEvent.cs:30, 68`). La ceinture ou le sac de l'host ne reçoivent donc JAMAIS un
  réglage d'un autre. `CopyRules` ne copie pas `excludeDump` (`:80-93`).
- Mais `CopyRules` copie `autodump` (`InvSaveDataDelta.cs:89`, comparé en `:101`) : depuis le 5 octobre, le mode « ranger »
  d'un coffre posé par l'INVITÉ devient celui de l'host (`:64-65`), et inversement (si `HostManagesBase`, l'host le renvoie à
  l'invité, `:46-57`).
- Objet tenu : `RemoteGetToolPatch.cs:10-17` remplace `Card.Tool` pour TOUT personnage, joueur compris, par `chara.held`
  (au lieu de la barre active). `CharaSwitchHeldDelta.cs:56-66` ne fait que dire aux autres ce qui est en main (pour le joueur local
  il ne fait rien d'autre, `:30-33`). Fantômes de capacités : `InvPlaceAbilityDelta` et `InvalidateFakeAbilityCard` ne touchent
  que le personnage d'un invité (`ElinNetClientPlayer.cs:220`, `ElinNetHostTravel.cs:1280`).
- Garde-fous host : `CardAddThingDelta.cs:46-53`, `ThingRequest.cs:54-63`, `CardTryStackToDelta.cs:22-37` refusent de toucher un objet
  qui est dans le sac d'un joueur autre que l'envoyeur. `CardModNumDelta.cs:14-30` n'a PAS cette garde (seulement « pas un
  personnage ») : un invité peut mettre à 0 le nombre d'un objet de l'host s'il en connaît le numéro (non vérifié : aucun chemin
  du jeu normal ne le fait).

## 3. Hypothèses, de la plus à la moins probable

1. **(a) Le rangement du jeu vide le contenu de la ceinture à outils** (`TaskDump.cs:172` + `ThingContainer.cs:867-879` +
   `UIInventory.cs:293-296`). Un joueur seul le vivrait aussi : pas un défaut du mod (non vérifié en jeu). Les objets sont dans
   un coffre (ou empilés dans une pile de coffre) : message « rangé » dans le journal des messages (`dump_item`, `dump_dumped`),
   coffres dont le mode est « ranger ce qui s'y trouve déjà » et qui contiennent le même objet. Rien de détruit. Si les objets
   manquants étaient dans la RANGÉE DU BAS (touches 1 à 0), (a) ne les explique pas : ils sont protégés (`:273`).
2. **(b) Un coffre réglé par l'invité** (`InvSaveDataDelta.cs:89`) : l'invité (ou l'host par erreur) a mis un coffre en
   « distribution » à drapeaux vides : il prend tout (`TaskDump.cs:199-206`). Pas le sac ni la ceinture de l'host (voir §2) :
   c'est le COFFRE qui change. Objets dans ce coffre, rien de détruit. Cet écart est symétrique (l'invité subit aussi le réglage de
   l'host), donc pas une inégalité, mais une surprise née du lot du 5 octobre. Plausible seulement si quelqu'un a touché ce menu.
3. **(c) Fusion dans une pile de coffre** : l'objet « disparaît » car il s'est empilé (`Card.AddThing`, `things.TryStack`, vu
   `TaskDump.cs:115`). Il est dans le coffre, compté dans la pile. Pas détruit. Se confond avec (a).
4. **(d) Perte de rang dans la barre (`invY` remis à 0)**, puis rangement normal : `Card.cs:3325, 3535`. Je n'ai trouvé AUCUN
   chemin du mod qui le fasse chez l'host : `CardAddThingDelta.cs:74-87` ne s'applique pas à ses propres objets (garde
   `:46-53`), `Rebind` garde `invX/invY` (`:93-106`). Probabilité faible, non vérifié.
5. **(e) Destruction par un invité** : `CardModNumDelta.cs:14-30` (Num = 0 accepté sans regarder le propriétaire). Théorique.
   Objets détruits, introuvables. Rien dans le code ne le déclenche sans que l'invité manipule exactement ces numéros.
- **L'instrument n'est pas la cause** : `AIPlayMusicPatch.cs` ne touche que « qui compte comme public »
  (`Evaluate`, `ThrowReward`, `ListWitnesses`) ; `AIPlayMusicArgs.cs` n'envoie que l'instrument ; `AI_PlayMusic.Run` ne déplace
  rien. Le luth sert surtout de repère dans le temps (non vérifié). Si l'objet tenu change après le rangement, c'est parce
  que le rangement a bougé l'objet (`RefreshCurrentHotItem`, `Player.cs:2297-2331`).

## 4. Plus petite correction et test rouge pour les deux premières

### (a) le rangement ne prend pas ce qui est dans la ceinture
- Correction : un `HarmonyPostfix` sur `TaskDump.ListThingsToPut(Thing c)` (méthode publique d'instance) qui fait
  `__result.RemoveAll(t => (t.parent as Thing)?.trait is TraitToolBelt);`. `IsValidContainer` appelle la même méthode : un coffre
  qui n'aurait que ça à prendre devient « sans objet » (`:150`). Fichier neuf `ElinTogether/Patches/...` (une dizaine de lignes).
- Décision pour l'utilisateur : c'est un changement de comportement du jeu, pour tous les joueurs d'une partie à plusieurs.
  Règle de `CLAUDE.md` : une case à cocher « Server Setting » côté host (cochée par défaut), ou seulement quand une
  partie à plusieurs est en cours (`NetSession.Instance.Connection != null`).
- Test (modèle `hunt_suite.py` D3, lignes 127-166, deux fenêtres, les deux sens avec `both(ctx)`) : `d3b`. Pour chaque joueur,
  `give(... "bucket", 3)` puis déplacer ces seaux dans sa ceinture (`pc.things.Find(t => t.trait is TraitToolBelt).AddThing(s, false)`,
  la ceinture de départ est équipée ; sinon `EQ_ID("toolbelt")`, non vérifié sur les personnages du banc), un coffre `chest3` avec
  1 seau dupliqué et `c_windowSaveData = new Window.SaveData { autodump = AutodumpFlag.existing }` dans les deux jeux, puis
  `TaskDump.TryPerform()`. Vérifier : 3 seaux encore dans la ceinture (host ET invité), 1 seul dans le coffre. **Rouge avant la
  correction** : le coffre en contient 4 (c'est exactement le cas D3 avec la ceinture comme source).
- Variante pour la barre du bas : même chose avec `invY = 1` : doit être VERT dès maintenant (preuve que `IsHotItem` protège).

### (b) le mode « ranger » d'un coffre reste à chaque joueur
- Correction : retirer `to.autodump = from.autodump;` (`InvSaveDataDelta.cs:89`) et `(int)d.autodump` de `Rules` (`:101`),
  corriger le commentaire `:10`. Ainsi le mode choisi par l'un ne devient pas celui de l'autre.
  Contre-argument : le lot du 5 octobre l'avait mis en commun exprès ; à demander avant.
- Test (modèle `setting_suite.py` S7, lignes 168-215) : même mise en place ; après `buttonSort.onClick.Invoke()`, poser
  `d.autodump = AutodumpFlag.distribution; d.priority = 3` (le changement de priorité fait partir le delta même sans autodump),
  fermer le menu (`currentMenu.Hide()`), attendre, puis lire `(int)autodump` du coffre CHEZ L'AUTRE JOUEUR. **Rouge avant** :
  l'autre voit `distribution`. **Vert après** : il garde `existing` et voit quand même `priority = 3`.

## 5. Trois questions au joueur (et où chercher en attendant)

1. Les objets partis étaient dans la rangée de raccourcis en bas de l'écran (touches 1 à 0) ou dans la petite fenêtre de la
   ceinture à outils, à côté de l'équipement ?
2. Quand il appuie sur « ranger automatiquement » tout seul (sans partie à plusieurs), ça fait pareil ? Et un message du
   genre « N objets rangés » est-il passé dans le journal des messages ?
3. Toi qui es l'invité : vois-tu ces objets dans un coffre de la base ? Et as-tu changé, sur un coffre, le réglage « ranger »
   (menu du bouton de tri) ?

En attendant : ne pas relancer le rangement ; lire le journal des messages de l'host (lignes « rangé … dans … ») ; ouvrir les
coffres proches de l'endroit où il a marché et chercher le même objet (il a pu s'empiler dans une pile existante) ; utiliser la
recherche d'objets du jeu (elle fouille les coffres, `WidgetSearch.cs:165`, non vérifié) ; regarder le coffre que l'invité a
réglé en dernier. Si rien n'est trouvé nulle part, c'est (e) ou un défaut non vu : garder la sauvegarde telle quelle et le journal
du jeu (`Player.log`), et me les envoyer.

## État

- Aucun fichier du mod modifié, rien compilé, rien lancé. Seul ce plan est écrit.
- Rien n'est confirmé en jeu. Le point (a) se prouve en un test court (deux fenêtres) avant toute correction.
