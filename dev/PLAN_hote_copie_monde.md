# Copie du monde chez les invités (conseil 9, étape 3 : A') — notes

Écrit le 6 octobre 2026. Compilé (ReleaseNightly et DebugNightly, 0 erreur), **jamais lancé en jeu**. Verdict :
`PLAN_conseil9_verdict.md` ; faits : `PLAN_hote_qui_part.md`. Code : `ElinTogether/Net/Handover/`.

## Ce que fait A'

Après chaque sauvegarde automatique réussie de l'host (`EmpAutoHost.Save`), chaque invité reçoit ce qui a changé
dans le dossier de sauvegarde de l'host et garde une copie entière du monde sur son disque. Le joueur ne voit rien ;
une ligne au journal du mod chez l'invité (« World copy kept: … »), une chez l'host (« World copy: save of … »).

- **Quoi** : tout le dossier de sauvegarde (`game.txt`, `index.txt`, les cartes, les fichiers du mod), sauf `Temp/`
  (la visite en cours) et `cloud.zip` (l'archive du nuage Steam) : ce que le jeu met lui-même dans ses copies de secours.
- **Quand** : après chaque sauvegarde automatique (2 minutes, 5 si elle est lente). Pas après une sauvegarde à la
  main ni en mode `-empserver` (voir « Reste »).
- **Où, chez l'invité** : `…\AppData\LocalLow\Lafrontier\Elin\ElinMP\WorldCopy\<identifiant Steam de l'host>_<monde>\`
  (à côté des journaux du mod, **hors** de `Save\` et de `Cloud Save\`). Dedans : `incoming\` (copie en cours) et
  `copy-<numéro de reprise>-<date>\` (copies entières, les **2** plus récentes), chacune avec son `copy.json`
  (monde, host, numéro de reprise, date de la sauvegarde, liste des fichiers avec taille et somme SHA-256).
- **Numéro de reprise** : nouveau champ gardé dans la sauvegarde (`world_handover`, `ElinNetHost.HandoverNumber`).
  Il vaut 0 partout : rien ne l'augmente encore (étape 4).

## Comment (protocole, 3 messages)

1. Host → invité `WorldCopyManifest` : la liste des fichiers de la sauvegarde (chemin, taille, somme).
2. Invité → host `WorldCopyWant` : les fichiers qu'il n'a pas (ni dans sa dernière copie entière, ni déjà reçus).
3. Host → invité `WorldCopyPiece` : ces fichiers, par morceaux de **32 Ko, 4 par seconde au plus** (128 Ko/s). Un
   morceau ne part que si Steam n'a presque plus rien en attente pour ce joueur (16 Ko) : une liaison lente ralentit
   la copie, pas le jeu.

Quand tout est là, l'invité (hors du fil du jeu) reprend les fichiers inchangés dans sa copie précédente, vérifie
**chaque** fichier (taille + somme), écrit `copy.json`, puis renomme `incoming` en `copy-…` (un seul renommage).
Tant que ce renommage n'a pas eu lieu, et si quoi que ce soit échoue, la copie précédente reste la copie.

- Poids : 1re fois, tout le monde (1 Mo ≈ 8 s, 5 Mo ≈ 40 s, 20 Mo ≈ 2 min 40). Ensuite `game.txt` + les cartes
  changées (≈ 1 Mo sur le monde d'essai). Rien n'est compressé.
- Une sauvegarde plus récente n'interrompt jamais un envoi en cours (sinon un gros monde ne finirait jamais) : elle
  est proposée dès que l'envoi se termine.
- Coupure : ce que l'invité a reçu en entier reste (mémoire du jeu + `incoming`) ; à son retour l'host lui repropose
  la sauvegarde et il ne redemande que le reste. Jeu relancé : il redemande ce qui a changé depuis sa dernière copie entière.
- Chez l'host : le dossier est lu **hors du fil du jeu**, en mémoire (le monde entier tient en mémoire, une fois) ; un
  fichier que la sauvegarde n'a pas touché n'est ni relu ni gardé deux fois. Si une autre sauvegarde tombe pendant la
  lecture, cette lecture est jetée.
- Sécurité : un chemin envoyé par l'host qui sortirait du dossier est refusé (tout le manifeste) ; au plus 20 000
  fichiers et 1 Go.

## Fichiers

| Fichier | Rôle |
|---|---|
| `Net/Handover/WorldCopyPackets.cs` | les 3 messages |
| `Net/Handover/ElinNetHostWorldCopy.cs` | host : lecture de la sauvegarde, offre, envoi étalé, numéro de reprise, `WorldCopyBench` (Debug) |
| `Net/Handover/ElinNetClientWorldCopy.cs` | invité : réception des messages |
| `Net/Handover/WorldCopyReceiver.cs` | invité : ce qui manque, écriture dans `incoming`, reprise |
| `Net/Handover/WorldCopyStore.cs` | le dossier des copies : chemins sûrs, vérification, renommage, ménage |
| `Net/Handover/WorldHandover.cs` | **préparation de l'étape 4, appelée par rien** |
| `Emp/EmpAutoHost.cs` | un appel après une sauvegarde réussie |
| `Net/Client/ElinNetClient.cs` | une ligne : `RegisterWorldCopy()` |
| `Emp/EmpConfig.cs`, `Net/NetSessionRules.cs` (clé 21), `Components/Tabs/TabServerConfiguration.cs` | la case |

Aucun delta : les deltas sont filtrés quand un joueur est seul sur une carte et pendant un chargement. `ElinDelta.cs`
n'est pas touché, 843 reste libre.

## Préparation de l'étape 4 (`WorldHandover`, rien n'est déclenché)

- `Mine()` / `Find(host, monde)` : « j'ai une copie entière de ce monde, numéro de reprise N, sauvegardée à telle heure ».
- `Verify(copie)` : relit tous les fichiers (à faire avant d'ouvrir un monde depuis la copie).
- `Successor(invités, secondes sans host)` : le plus petit identifiant Steam ; le suivant toutes les 2 minutes.
- `IsMyTurn(secondes)` : c'est à ce jeu de reprendre, et il a une copie.
- `Copy.IsNewerThan` : le plus grand numéro de reprise gagne, puis la sauvegarde la plus récente.
- La liste des invités est celle connue au dernier manifeste reçu (au plus vieille d'une sauvegarde).

## Reste, et ce qui n'est pas sûr

- **Une ligne à ajouter par celui qui tient `Net/Client/ElinNetClientTravel.cs`**, dans `ShouldReceiveWhileAway` :
  `WorldCopyManifest or WorldCopyPiece or`. Sans elle, un invité parti seul sur une autre carte ne reçoit rien tant
  qu'il y est (il reçoit la sauvegarde suivante à son retour ; rien ne casse).
- Mode `-empserver` : `EmpServer` sauvegarde lui-même, sans passer par `EmpAutoHost` : pas de copie. Une ligne à
  ajouter après sa sauvegarde : `(NetSession.Instance.Transport as ElinNetHost)?.WorldSaved();`.
- Un invité qui se reconnecte reçoit la dernière sauvegarde **lue**, qui peut dater d'avant une sauvegarde faite
  quand l'host était seul ; la suivante (2 minutes) la remplace.
- Les invités ne savent pas si les autres ont une copie : un invité sans copie dont c'est le tour fait perdre 2 minutes.
- Le texte de la case ne promet pas la reprise : elle n'existe pas encore.
- Non mesuré : le débit réel par Steam, l'effet sur les autres messages sur une liaison lente, la mémoire et les
  pauses du ramasse-miettes sur un monde de 20 Mo, la durée de lecture du dossier.
- Un antivirus ou l'explorateur qui tient `incoming` ouvert fait échouer le renommage : la copie est refaite à la
  sauvegarde suivante (les fichiers inchangés viennent de la copie précédente).

## Test

`dev/_tools/worldcopy_suite.py` (deux fenêtres, pas encore lancé) : C1 copie entière identique au dossier de l'host et
aucun gel de plus de 200 ms chez l'invité ; C2 seuls les fichiers changés partent ; C3 copie coupée au milieu
(`emp.cut_link`), l'ancienne reste entière, la suivante se termine ; C4 aucune sauvegarde de l'invité touchée.
À deux PC seulement : le débit par le relais Steam, une liaison lente, un vrai plantage de l'host en plein envoi.
