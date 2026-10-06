# Plan : le jeu sait quel personnage est à qui, sans rien demander (6 octobre 2026)

Demande de l'utilisateur (elle remplace le verdict du conseil 8 sur la question posée au joueur) : « le jeu devrait
savoir quel personnage est à qui, l'objectif est une expérience seamless où le joueur n'a pas à réfléchir, il se connecte
au serveur et voilà tout est bon, il se déconnecte aucun problème, un autre joueur se connecte aucun problème, le
joueur 1 se reconnecte pendant que le joueur 2 joue aucun problème ils jouent ensemble ». Puis : « travaille en autonomie
maintenant, tu sais ce qu'on veut ». Donc : AUCUN écran de question, aucune démarche. Gardé du conseil 8 : copie de
secours avant tout échange, plus aucun cas muet. Faits de départ : `PLAN_depot_personnage.md`. Code : `Net/Host/ElinNetHostHandOver.cs`.

## Les règles (dans l'ordre où le jeu les applique)

Ce que la sauvegarde sait : `remote_chara` (compte Steam -> personnage joué, pour qui a joué en invité), `pc_owner`
(compte Steam -> personnage local de la sauvegarde), et, nouveau, `pc_orphan` (un ancien personnage local dont on ne
connaît pas le propriétaire).

1. `pc_owner` est tenu pour INCONNU s'il est vide, ou s'il nomme un compte qui a aussi un autre personnage dans
   `remote_chara` (c'est ce que la 0.26.494 a pu écrire à tort en hébergeant un monde repris).
2. À l'écriture : celui qui met sa sauvegarde au dépôt (« Put ») joue le personnage local : noté. Celui qui charge une
   sauvegarde de son propre PC qui n'est pas la copie du dépôt, propriétaire inconnu, sans personnage à son nom : noté.
   À l'ouverture d'une session : noté seulement si inconnu (ne plus écraser).
3. Au chargement, pour le joueur « moi » :
   - le propriétaire est moi : rien ;
   - j'ai un personnage à mon nom (`remote_chara`) : je le joue (échange). L'ancien local va à son propriétaire s'il est
     connu, sinon dans `pc_orphan` ;
   - je n'ai pas de personnage et il y a un `pc_orphan` : il est à moi (échange) ;
   - je n'ai pas de personnage, propriétaire inconnu, pas d'orphelin : le local est à moi (l'host d'origine qui revient
     sur son vieux monde ; c'est aussi, sans qu'on puisse le distinguer, un nouveau venu qui prendrait un vieux monde
     en premier : LE cas qu'on ne peut pas connaître, à dire à l'utilisateur) ;
   - je n'ai pas de personnage et le local est à un AUTRE connu : je suis un nouveau joueur : je crée mon personnage
     (l'écran de création du jeu, comme tout nouveau joueur), puis échange. ÉTAPE 2, voir plus bas.
4. À la connexion d'un invité sans personnage : s'il y a un `pc_orphan`, il le reçoit (exact à deux joueurs) ; sinon il
   crée le sien, comme aujourd'hui.
5. Avant tout échange : copie de secours du dossier de la sauvegarde. Personnage du repreneur mort, ou table
   incohérente : un message à l'écran, jamais le silence.

## Étapes

- Étape 1 : règles 1, 2, 3 (sauf la création), 4, 5. Tests rouges d'abord dans `depot_suite.py` : vieux monde repris par
  l'invité puis retour de l'host ; vieux monde repris par son host ; `pc_owner` faux de la 0.26.494 ; retour pendant que
  l'autre joue ; rien ne change pour un monde de la nouvelle version (P1 reste vert).
- Étape 2 : un nouveau joueur qui prend en premier le monde d'un autre : création locale. Piste : au chargement, noter
  « création en attente », retour à l'écran titre, `LayerEditBio` comme `ElinNetClientPlayer.OnSessionNewPlayerRequest`,
  garder le personnage fait, recharger, l'adopter par le code de `OnSessionNewPlayerResponse` (à sortir en fonction),
  inscrire, échanger.
- Puis : relecture, passe sur `depot_suite` (dossier et GitHub), proposer la 0.26.495.

## État

- Étape 1 ÉCRITE et relue (pas encore commitée au moment de cette ligne) : `PcOwner()`, `OwnCharaOf`, `PcOrphans`,
  `GiveOrphanTo` (début de `PreparePlayerJoin`), `RememberPcOwner` qui n'écrase plus, copie de secours
  (`GameIO.MakeBackup`, pas d'échange si elle échoue), message `emp_handover_failed`. Test : `DEPOT_OLD=1` (monde
  d'avant) et `DEPOT_OLD=2` (propriétaire faux de la 0.26.494) dans `depot_suite.py` P1 ; journaux
  `_shots/depot-old*-vert.log`, rouge d'abord `_shots/depot-old-rouge.log`.
- Piège trouvé : une table de sauvegarde VIDÉE n'est peut-être pas réécrite (le premier essai vidait `pc_owner`, le jeu
  de A a quand même lu l'ancienne valeur : 22/22 au lieu du rouge attendu). Non vérifié dans le kit ; le code ne croit
  donc un orphelin que si personne ne joue ce personnage, et le test écrit une entrée bidon au lieu de vider.
- Relecture, laissé tel quel et à dire à l'utilisateur : un orphelin va au premier joueur sans personnage qui rejoint ;
  à trois joueurs ou plus sur un vieux monde, un nouveau venu arrivé avant l'ancien host recevrait son personnage.
- Étape 2 FAITE : un nouveau joueur sans personnage qui prend le monde d'un autre passe par l'écran de création du jeu
  (depuis l'écran titre), puis joue ce personnage ; celui de l'autre attend. `depot_suite` P2 : rouge vu d'abord (28/33),
  puis 33/33 pour toute la passe dossier. Relu ; corrigé à la relecture : un monde du nuage est rechargé comme tel, un
  personnage fait pour un chargement qui n'a pas eu lieu est oublié après 3 minutes.
- Reste : passe large, `depot_suite` avec `DEPOT_GITHUB=1`, proposer la 0.26.495. Pas joué : deux PC et deux comptes
  Steam ; le joueur qui ferme l'écran de création ; un monde du nuage ; le monde du dépôt pris par un autre pendant l'écran.
