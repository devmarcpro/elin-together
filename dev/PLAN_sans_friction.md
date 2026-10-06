# Audit des frictions : ce que le mod demande, arrête ou n'explique pas (6 octobre 2026)

Demande de l'utilisateur : « le jeu devrait savoir quel personnage est à qui... il se connecte au serveur et voilà, tout est
bon ; il se déconnecte, aucun problème ; un autre se connecte, aucun problème ; le joueur 1 se reconnecte pendant que le
joueur 2 joue, ils jouent ensemble ». Hier, en jeu : les boîtes de saisie coupaient une clé GitHub à 22 caractères, et le
bouton « Depot » de l'onglet Client Settings débordait.

Méthode : lecture du code, du classeur `package/LangMod/EN/emp_localization.xlsx` (anglais + japonais) et de
`package/LangMod/CN/SourceLocalization.json`. Rien lancé, rien compilé, rien modifié sauf ce fichier. Les numéros de ligne sont
ceux du 6 octobre ; une compilation tournait pendant la lecture, ils peuvent bouger. Ce qui n'a pas pu être prouvé est marqué
« non vérifié ». Les chemins sont sous `ElinTogether/ElinTogether/` sauf mention.

## Déjà réglé (pour ne pas le refaire)

- Boîtes coupées à 22 caractères : `characterLimit = 0` est posé aux trois saisies de texte libre (`Components/Tabs/TabClientConfiguration.cs:37`,
  `:49`, `Components/Tabs/TabLobbyBrowser.cs:42`). Les deux autres boîtes (`Components/LayerPlayerTrade.cs:143`, `:154`) ne reçoivent que des
  nombres. Le jeu fixe 500, 100, 30 ou 8 pour ses types de saisie (`dev/_decomp/Elin/Dialog.cs:545-554`) ; le type par défaut garde la limite du
  modèle de la boîte. Pas rejoué au banc (HANDOFF) : à revérifier en jeu avec une clé de 40 caractères.
- Le bouton qui déborde, lui, n'est PAS réglé : voir A3.

## Les 10 points qui gênent le plus un invité qui veut juste jouer avec son ami

1. **Écran « Who do you want to play? » à chaque connexion** (A1) : un invité qui a déjà un personnage est quand même interrogé.
2. **Aucun retour automatique après une coupure** (B1) : toute coupure ramène au titre, il faut se faire réinviter.
3. **On ne rejoint que par invitation Steam** (B2) : la liste des parties est affichée mais on ne peut pas cliquer dessus.
4. **Prendre le monde pendant que l'ami joue** (A2, B3) : un bouton au texte de 170 caractères, puis « demande une invitation ».
5. **Un nouveau venu passe par toute la création de personnage** (B5).
6. **« X part en quête, tu viens ? » avec 15 secondes pour répondre** (B6), dans les deux sens.
7. **Quand l'host entre sur la carte de l'invité, l'écran de l'invité est rechargé de force** (B7).
8. **Messages d'échec faux ou en clé brute à la connexion** (A4, A5) : « vérifie l'adresse et le port » à un invité Steam, et
   `emp_not_allowed` affiché tel quel.
9. **Onglet Client Settings** (A3, B12) : bouton qui déborde, dépôt et clé à saisir à la main, mode d'emploi de 525 caractères.
10. **L'host doit cliquer « Start Server » après chaque chargement, et avoir fondé une base** (B8) : sans cela l'invité n'a rien à rejoindre.

---

## Groupe A : à supprimer, sûr (une seule bonne réponse)

**A1. Écran de choix du personnage.** `Net/Host/ElinNetHostPlayerManager.cs:81-104` envoie le choix dès que le joueur a au moins un personnage
et que `ChooseCharacter` est vrai (défaut vrai : `Emp/EmpConfig.cs:234`) ; côté invité `Net/Client/ElinNetClientPlayer.cs:29-63` ouvre une
`Dialog.List` (`:46`). Le joueur voit ses personnages, « A new character », et « A character from one of my saves… » si permis ; fermer la
boîte le déconnecte (`:58-62`). Friction : le jeu sait déjà qui joue qui (`remote_chara`, `pc_owner`) ; c'est ce que demande l'utilisateur
(`dev/PLAN_personnages_sans_question.md`). Plus petite façon : prendre le dernier personnage joué (code déjà prévu `:88-91`) et ne montrer le
choix que sur demande explicite (bouton dans l'onglet Session). Piège : un fichier de réglages déjà écrit garde `true` ; changer le défaut
ne suffit pas, il faut décider dans le code.

**A2. Bouton « le monde est tenu par X » avec un texte de 170 caractères.** `Components/Tabs/TabLobbyBrowser.cs:25` met `emp_ui_depot_held` (EN :
« {0} is hosting the world. Join them through Steam: ask for an invite, or use "Join Game"... wait up to 3 minutes. ») comme libellé de bouton ;
le clic ouvre une `Dialog.Ok` avec le même texte (`Helper/SaveDepot.cs:170`). Plus petite façon : libellé court (« X héberge le monde »), texte long
en infobulle ou seulement dans la boîte.

**A3. Les boutons de Client Settings débordent.** `Components/Tabs/TabClientConfiguration.cs:31` (`emp_ui_depot_folder` + la valeur, par exemple
`github:propriétaire/dépôt`) et `:41` (`emp_ui_depot_password` + `***`) : trois boutons dans une rangée à largeur partagée (`:11-12`). Le nom du
dépôt dépasse (vu par l'utilisateur). Plus petite façon : libellé fixe court (« Dépôt », « Clé »), valeur sur une ligne de texte dessous, une rangée
par bouton. Japonais et chinois sont plus larges : vérifier les trois langues.

**A4. Clés de texte utilisées dans le code et absentes du classeur : le joueur voit la clé brute** (comparaison faite par programme) :
- `emp_error_connection` : `Net/Client/ElinNetClient.cs:149` (lien coupé à l'ouverture) ;
- `emp_not_allowed` : `Net/Steam/SteamNetManager/SteamNetManagerServer.cs:116`, raison de fermeture, affichée côté invité via
  `Common/EmpDisconnectInfo.cs:29` → « Disconnected from host / emp_not_allowed » ;
- `emp_connection_no_server` : `Net/Steam/SteamNetLobby/SteamNetLobbyManager.cs:341` (et la fenêtre apparaît quand même, voir A9) ;
- `emp_zone_session_empty` : `Net/Host/ElinNetHostZoneSession.cs:180` ; non vérifié qu'elle soit montrée.
(`emp_tab_trade`, `emp_creating`, `emp_import`... sont des noms internes, pas des textes.) Plus petite façon : ajouter les lignes EN, JP, CN.

**A5. Mauvais texte au délai de connexion.** `Net/Client/ElinNetClient.cs:57-62` (Release seulement) : après 15 s sans lien (`EmpConfig.cs:29`, réglage
`Timeout`), « The server does not answer. Check the address, the port and the mode of the server » (`emp_ui_timeout`). Un invité Steam n'a ni adresse
ni port. Plus petite façon : deux textes selon `IsDirectConnection` ; celui de Steam : « la partie de X ne répond pas, il est peut-être parti ».

**A6. Textes anglais dans le jeu japonais.** 34 lignes du classeur ont la colonne JP identique à l'anglais : tout le bloc échange (`emp_trade_*`,
`emp_act_trade`, `emp_ui_trade`, `emp_ui_sv_cfg_player_trade`), le choix de personnage (`emp_ui_chara_pick`, `emp_ui_chara_new`,
`emp_ui_sv_cfg_choose_chara`), les boutons de robots (`emp_ui_bot_*`, versions de test) et `emp_ui_title` (normal). Un joueur japonais lit « Who do
you want to play? » et toute la fenêtre d'échange en anglais. Chinois : 246 clés sur 247 ont du chinois ; seule `emp_connection_rejected` manque et
n'est utilisée nulle part (la retirer). Plus petite façon : remplir JP ; ne jamais ajouter une clé sans ses trois langues.

**A7. Échange : « Add an item » ne fait rien quand il n'y a rien à offrir.** `Components/LayerPlayerTrade.cs:132-134` : `return;` sans message.
Plus petite façon : un message (« rien que tu puisses offrir ») ou griser le bouton.

**A8. « Server can only be started after claiming a zone! » sur l'écran titre.** `Components/Tabs/TabLobbyBrowser.cs:45`, dans le cas « aucune partie
lancée » : l'invité qui vient rejoindre lit une phrase qui ne le concerne pas. Plus petite façon : ne l'afficher que dans une partie lancée sans
base, là où « Start Server » échoue (`Net/Host/ElinNetHost.cs:27-31`).

**A9. Fenêtres techniques montrées au joueur.** `Emp/Logger/EmpLoggerPopup.cs:15-17` : `EmpPop.Debug` appelle `Popup`, donc les messages « debug »
s'affichent aussi (aucun filtre de niveau). Exemples : « Received lobby join request {LobbyId} » avec un numéro Steam (`SteamNetLobbyManager.cs:273`,
`:286`), « Player lobby state changed » suivi d'un objet brut (`:364`), « Switching zone… » (`Net/Host/ElinNetHostZone.cs:20`), « Waiting on zone state
sync… » (`ElinNetClientPlayer.cs:248`). Plus petite façon : `Debug` n'écrit que dans le journal.

**A10. Fenêtre coupée à 150 caractères.** `EmpLoggerPopup.cs:108-123` coupe le texte, la suite n'est visible qu'au survol. `Helper/SaveDepot.cs:597`
envoie « refus GitHub + The server did not receive this save... » : 223 à 258 caractères (calculé sur le classeur) ; la phrase « quoi faire » est
dans la partie cachée. Plus petite façon : `Dialog.Ok` pour ces cas, ou textes plus courts.

**A11. « Only the host can do this for now. » (`emp_base_host_only`).** `Patches/Remote/RemoteBasePaidPatch.cs:48`, `RemoteBuildModePatch.cs:40`,
`RemoteRevivePatch.cs:58`. Deux défauts : (1) c'est une règle de l'host quand « Only the host manages the base » est cochée, mais « for now » en fait
une limite du mod ; (2) dans la carte d'un invité c'est l'host qui est refusé (commentaire `RemoteRevivePatch.cs:55`) et il lit « seul l'host peut ».
Plus petite façon : deux textes (« l'host a réservé la base » ; « pas encore possible dans la carte d'un autre joueur »).

**A12. « (Temp) This quest cannot be started by client players. »** (`emp_ui_quest_client`, `Patches/DeltaEvents/Quest/BlockClientQuestPatch.cs:31`,
`QuestStartEvent.cs:29`). N'apparaît que si l'host a coupé les quêtes personnelles ou le voyage seul. « (Temp) » et « client » : jargon. Plus petite
façon : « L'host a coupé X : cette quête n'est pas ouverte aux autres joueurs ».

**A13. Refus de version sans conduite à tenir.** `Net/Client/ElinNetClientValidator.cs:55` (« Could not join: Version mismatch / Mod: Local... »).
Plus petite façon : ajouter « mets le mod à jour, puis réessaie » (ou « demande à l'host de le mettre à jour » si c'est lui qui est en retard).

**A14. Mot « Host » non traduit.** `ElinNetClientValidator.cs:66` passe la chaîne anglaise `"Host"` à `emp_game_version_differs`. Plus petite façon :
le nom du joueur host.

**A15. Boîte obligatoire après « Put this save on the server ».** `Helper/SaveDepot.cs:309` : `Dialog.Ok` à valider avant le rechargement. Information
sans choix : une fenêtre qui s'efface suffit.

---

## Groupe B : à supprimer, demande une décision de conception

**B1. Coupure : retour au titre, puis plus rien.** `Net/Client/ElinNetClient.cs:129-139` (`Stop` → écran titre), `:172-193` (« Disconnected from host / raison »),
`Net/NetSession.cs:160-183`. Recherche de `Rejoin`, `LastLobby`, `AutoReconnect` : rien (vérifié). Il faut une nouvelle invitation ou « Join Game » de Steam.
Les boutons « Reconnect » (`Components/Tabs/TabSessionInfo.cs:89`) n'existent que pendant la partie. Décision : retenir la dernière partie et (a) un bouton
« Rejoindre X » sur le titre, ou (b) retour automatique après une coupure réseau (pas après renvoi par l'host ni refus de version). Recommandation : (b), avec un
compte à rebours annulable.

**B2. Rejoindre = invitation Steam.** `TabLobbyBrowser.cs:128` affiche chaque partie en `HeaderCard` : du texte, aucun clic ; la seule voie est
`OnLobbyJoinRequested` (`SteamNetLobbyManager.cs:269`), lancée par Steam. Liste vide sans explication : en Release elle ne montre que les parties de la même version
du mod ET du jeu (`:169-174`), donc « 0 joueur » veut aussi dire « parties d'une autre version cachées ». Les salons sont créés publics (`:81-91`, défaut `Public`).
Décision : ligne cliquable ; salon « amis seulement » (la liste ne montre que les amis : mieux pour la vie privée) ; ligne « n'affiche que ta version ».

**B3. Prendre le monde quand l'ami le tient.** `Helper/SaveDepot.cs:124-159` ne rend qu'un nom (`WHO`) ; `:164-172` refuse par « demande une invitation ». Il manque à
l'invité l'identifiant Steam de l'host. Décision : le dépôt rend l'identifiant, un clic rejoint la partie de l'host (suppose qu'elle soit ouverte, B8). Sinon au
moins un message sans « 3 minutes ».

**B4. L'host part : l'invité reste sur le titre.** Verrou du dépôt de 3 minutes (`SaveDepot.cs:37`, `dev/server/ElinTogetherServer.cs:34`), battement toutes les 60 s
(`:38`). Après un départ propre le monde est libre (`ReleaseAtTitle`, `:692-714`), mais l'invité doit cliquer « Take the world » (`TabLobbyBrowser.cs:25-28`) ; après un
plantage : « wait up to 3 minutes ». Décision : reprise automatique par le premier invité (compte à rebours visible), verrou plus court, ou garder le clic. À décider avec B1.

**B5. Nouveau joueur : création complète de personnage.** `ElinNetHostPlayerManager.cs:106-109` → `ElinNetClientPlayer.cs:106-136` ouvre `LayerEditBio` (création du jeu sans
le choix du mode) ; le fermer déconnecte (`:131-135`). Décision : personnage au hasard avec « personnaliser » en option, ou garder l'écran. Cas lié, non vérifié : le premier
nouveau venu qui prend un vieux monde joue le personnage local de l'ancien host (`Net/Host/ElinNetHostHandOver.cs:135-143`, étape 2 de `PLAN_personnages_sans_question.md` pas faite).

**B6. Question « Go along? » avec 15 secondes.** Invité qui prend une quête : l'host reçoit `Dialog.YesNo` (`Net/Host/ElinNetHostTravel.cs:343`, délai `:259`) ; l'host part en
quête : l'invité reçoit la même (`Net/Client/ElinNetClientTravel.cs:681`, délai `:659`). Pas de réponse = non (« X did not answer », `Models/Delta/Quest/QuestFollowDelta.cs:100`).
Décision : une règle sans question. Options : toujours suivre (la récompense reste à celui qui a pris la quête), ou case de l'host « suivre les quêtes des autres » (conforme à
« toute nouveauté = une case côté host ») avec « oui » par défaut.

**B7. L'host qui entre sur la carte d'un invité la lui retire.** `ElinNetHostTravel.cs:700-719` (« Waiting for X to hand the zone back… ») et `ElinNetClientTravel.cs:614-631`
(« X is coming to this place: the screen will reload to rejoin them… »). L'invité subit un rechargement qu'il n'a pas demandé ; l'inverse n'existe pas. La session de zone existe
déjà (un invité rejoint la carte d'un autre invité, `ElinNetHostTravel.cs:742`). Décision : l'host rejoint la carte comme invité au lieu de la reprendre. Pas d'attente maximale
vue côté host pour le rappel (non vérifié).

**B8. « Start Server » à la main, et il faut une base.** `Components/Tabs/TabLobbyBrowser.cs:50` ; `Net/Host/ElinNetHost.cs:27-31` refuse (popup) sans `homeBranch.owner` (base fondée).
Chaque chargement de partie coupe la session (`Patches/GameSaveLoad.cs:36-46`). Décision : case host « ouvrir la partie automatiquement au chargement » ; et pourquoi la base est
exigée (non vérifié : la raison n'est pas écrite dans le code lu ; si c'est une précaution, la lever).

**B9. Coupure de plus de 15 s = fin de session.** `ElinNetClient.cs:57-62` (Release), réglage `Timeout` de 1 à 60 s (`EmpConfig.cs:29-37`). Un trou de réseau court n'est pas rattrapé.
`Net/Client/ElinNetClientZone.cs:14-34` : trois échecs de synchronisation de carte, puis déconnexion (`emp_dc_invalid_zone`). Décision : relever la valeur, ou B1 qui règle les deux.

**B10. Rejoindre par Steam depuis une partie en cours ramène au titre sans demander.** `SteamNetLobbyManager.cs:129-133` : `scene.Init(Title)`. Une partie non sauvée est quittée (non vérifié
que le jeu sauve avant). Décision : sauver d'abord, ou demander.

**B11. Le jeu se fige pendant un échange avec le dépôt, sans message.** `SaveDepot.cs:472-482` (le commentaire du code le dit : « the game waits »), connexion 5 s (`:486`), lecture jusqu'à
60 s (`:491`), `Settle` jusqu'à 60 s (`:561`) ; à la fermeture jusqu'à 30 s (`:114`). Le joueur ne sait pas si le jeu est planté. Décision : un message « Connexion au dépôt… » avant l'appel
(petit), ou un fil séparé (gros).

**B12. Dépôt et clé à saisir à la main.** `TabClientConfiguration.cs:30-53` : mode d'emploi en 4 étapes (525 caractères, `emp_ui_depot_gh_help`) : créer un dépôt privé, une clé, la coller, puis
« envoyer les deux lignes à tes amis pour qu'ils les tapent ». C'est exactement « le joueur réfléchit ». Décision : l'host envoie dépôt et clé aux invités par la connexion (la clé est déjà partagée
à la main) ; ou un seul « code d'invitation » à coller ; ou cet onglet sous « Avancé » pour qui veut juste jouer.

**B13. Question « envoyer ta dernière sauvegarde ? ».** `SaveDepot.cs:179` (`Dialog.YesNo emp_ui_depot_unsent`). Le texte dit que « Oui » garde l'ancien monde de côté : « Oui » ne détruit rien
(`CopyTo` garde l'ancien dossier, `:397`). Décision : envoyer sans demander ; pour GitHub le code (`:175`) dit « jamais sans demander, un autre a pu héberger » : garder la question dans ce seul cas.

**B14. GitHub : un envoi toutes les 5 minutes.** `SaveDepot.cs:42` ; un plantage perd jusqu'à 5 minutes du monde partagé (le dernier envoi part à la sortie propre, `:114`). Décision : acceptable, ou
plus fréquent (GitHub demande de ne pas écrire trop souvent).

**B15. Sauvegarde bloquée pour un invité, en silence.** `Patches/GameSaveLoad.cs:12-20` : `Game.Save` rend « réussi » sans rien faire (journal seulement). Le joueur peut croire avoir sauvé.
Décision : une phrase « l'host sauvegarde le monde, ton personnage y est » (non vérifié : ce que montre alors le menu de sauvegarde).

---

## Groupe C : légitime, à garder

- **C1. Refus de version du mod** (`ElinNetClientValidator.cs:47-58`, `Common/BuildVersionIntegrity.cs:48-52`) : deux mods différents ne jouent pas ensemble ; seul le texte change (A13). Une
  version du JEU différente est déjà permise avec un avertissement (`Net/Host/ElinNetHostIntegrity.cs:122-130`, case host `SameGameVersion`, défaut faux).
- **C2. Écart de sources** (`ElinNetClientValidator.cs:154`, `Dialog.YesNo`) : seulement si l'host active la vérification (défaut : aucune, `EmpConfig.cs:79`).
- **C3. Invitations d'échange et de duel** (`Helper/PlayerTrade.cs:202`, `Helper/PlayerDuel.cs:132`, 15 s pour le duel `:32`) : consentement d'un autre joueur.
- **C4. Choix d'objet, quantité, or dans l'échange** (`LayerPlayerTrade.cs:136`, `:143`, `:154`) : saisies nécessaires.
- **C5. « dialogDeleteRecruit »** (`Patches/Remote/RemoteResidentPatch.cs:97`) : confirmation du jeu pour une action destructive ; la case « ne plus demander » est retirée à dessein.
- **C6. Choix de la touche de ping** (`TabClientConfiguration.cs:19`) : réglage facultatif.
- **C7. Refus par règle de l'host** (`emp_travel_disabled`, `emp_party_gather` `ElinNetClientTravel.cs:99`, `emp_base_refused` `Models/Delta/Zone/BaseRequestDelta.cs:284`) : l'host a décidé ; le texte dit pourquoi (sauf A11).
- **C8. Annuler la création de personnage déconnecte** (`ElinNetClientPlayer.cs:131-135`) : sans personnage, rien à jouer.
- **C9. Refus du dépôt GitHub public, trop gros, ou clé refusée** (`SaveDepot.cs:315-327`) : protège le monde, et les textes disent quoi faire.
- **C10. Boutons « Kick » et « Reconnect »** (`TabSessionInfo.cs:89-92`) : outils de l'host.
- **C11. Échange de personnage impossible** (`ElinNetHostHandOver.cs:146`, `:156`) : personnage mort ou copie de secours impossible ; dit la vérité (« tu joues le personnage de la sauvegarde »).
- **C12. « Un autre a repris le monde »** (`SaveDepot.cs:661`) : dit une fois que ce qui est joué ne part plus au dépôt ; il faut le savoir.
- **C13. Attente du sommeil commun** (`Patches/Synchronization/SleepSynchronizationContext.cs:145`) : conséquence du temps commun ; le texte dit qui on attend.
- **C14. Informations utiles** : joueur connecté / parti (`ElinNetHost.cs:152`, `:166`), serveur démarré (`:67`), partie rejointe (`SteamNetLobbyManager.cs:346`).
- **C15. Annulations d'échange et de duel avec leur raison** (`emp_trade_*`, `emp_duel_*`).
- **C16. Erreurs de salon Steam** (`SteamNetLobbyManager.cs:246`, `:300`) : utiles ; seule la raison est un code brut (`{Result}`, `{Response}`), à traduire.

---

## Ordre proposé

1. A1, A4, A5, A6, A9 : sûrs, petits, tous vus par l'invité.
2. A2, A3, A8, A11 : textes et mise en page, à revérifier en jeu dans les trois langues.
3. B1 (retour automatique) puis B3/B4 (reprise du monde) : le cœur de « se déconnecter, se reconnecter, aucun problème ».
4. B2, B8, B12 : « se connecter au serveur et voilà » (liste cliquable, ouverture automatique, dépôt envoyé aux invités).
5. B6, B7, B5 : décisions de jeu à poser à l'utilisateur.

## Non vérifié (à ne pas croire sans test)

- Que le bouton « Depot » déborde de la même façon à toutes les tailles d'écran (seul le constat de l'utilisateur est sûr ; aucun calcul de largeur fait).
- Ce que voit exactement un invité avec `emp_not_allowed` : la chaîne passe par `EmpDisconnectInfo.Describe` (lu), pas jouée.
- Un invité qui se reconnecte avant que l'host ait fermé l'ancienne connexion (`ElinNetHost.cs:129` : 25 images d'attente) : le code lu retire les personnages actifs du choix
  (`ElinNetHostPlayerManager.cs:132`), mais je n'ai pas suivi la suite. À jouer : « invité qui se reconnecte tout de suite après un plantage ».
- Les fenêtres Debug en jeu Release (le code les montre toutes, `EmpLoggerPopup.cs:15`) : un essai en Release le confirmerait.
- `Patches/GameSaveLoad.cs:25-34` : « Blocked loading game as host with active client connection » vise tout joueur non client dont une partie est déjà lancée ; geste du joueur concerné non cherché.
- Colonne CN : vérifiée par présence de signes chinois, pas relue par un locuteur.
- Boutons de robots (`TabLobbyBrowser.cs:75-79`, `#if DEBUG`) et `EmpBotLauncher` : non comptés, absents du zip distribué (non revérifié dans `dev/make_release.ps1`).
