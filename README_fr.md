# Elin Together — version « indépendance »

[English](README.md) | Français

Une version modifiée d'[Elin Together](https://github.com/ElinTogether/ElinTogether), le mod multijoueur
d'[Elin](https://store.steampowered.com/app/2135150/Elin/), avec un seul but : **en jeu, aucune différence entre
l'host et les autres joueurs**. Chacun va où il veut, avec ses compagnons, ses quêtes, sa renommée et son argent ;
le monde (histoire, base, guildes) reste commun.

Le mod d'origine garde tout le groupe sur la carte de l'host et traite les autres joueurs comme ses coéquipiers.
Ses auteurs ne prévoient pas les cartes séparées ; cette version est l'endroit où on l'essaie. Tout le mérite du
mod lui-même leur revient (voir [Crédits](#crédits)).

> **État : expérimental.** Tout ce qui suit est testé sur un seul PC avec plusieurs fenêtres du jeu (suites de
> tests automatiques en jeu, dossier `dev/`). Ce n'est **pas encore joué entre deux PC par Steam**. Faites
> d'abord une copie de vos sauvegardes : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Ce que cette version ajoute

| Fonction | Ce que ça change |
|---|---|
| Voyage indépendant | Un joueur part sur une autre carte sans l'host. La carte et ce qu'il y fait sont conservés. La progression est sauvée régulièrement ; le chat marche entre toutes les cartes. |
| Cartes partagées | Un joueur peut en rejoindre un autre sur sa carte, sans l'host. Si celui qui tient la carte part, un autre la reprend. |
| L'host ne traîne personne | Quand l'host change de carte, ceux qui sont restés restent. |
| Compagnons par joueur | Les compagnons suivent le joueur qui les a recrutés, voyagent avec lui, et ne comptent que dans sa limite d'alliés. |
| Expédition par joueur | Une seule caisse d'expédition ; l'argent d'une vente va à celui qui a déposé l'objet. |
| Combat au rythme de chacun | Un monstre agit au rythme du joueur qu'il combat, pas à celui de l'host. |
| Quêtes aléatoires par joueur | Les quêtes des habitants et des tableaux sont à celui qui les prend, avec la récompense, la renommée et le karma. Elles le suivent partout. |
| Histoire commune | Les quêtes d'histoire sont dans un seul journal : n'importe qui les lance, les avance, les termine. Dialogues déjà vus, objets clés et dette sont communs. |
| Quêtes à donjon pour tous | Un joueur qui n'est pas l'host peut prendre une quête qui a sa propre zone et la régler seul. |
| Échange entre joueurs | Clic sur un autre joueur → « Échanger » : chacun met des objets et de l'or, les deux confirment. |
| Choix du personnage | En rejoignant, un joueur choisit un de ses personnages de cette partie ou en crée un nouveau. |
| Karma et crime par joueur | C'est le joueur fautif qui perd du karma ; les gardes ne poursuivent que lui. |
| Affinité et guildes communes | L'affinité d'un habitant est la même pour tous ; rejoindre une guilde vaut pour le groupe. |

Chacune est une **case à cocher côté host** (Échap → Mods → Elin Together → *Server Setting*). Décochée, le mod
se comporte comme l'original.

## Limites connues

- Jamais testé entre deux PC par Steam.
- Le temps du monde suit encore l'host.
- Les dialogues d'histoire joués par un autre joueur que l'host sont testés par appels directs au code du jeu, pas
  encore en cliquant dans les vrais dialogues.
- Quêtes à donjon : seul celui qui prend la quête entre dans sa zone.
- Échange : pas d'objets équipés, pas de vérification du sac plein.
- Quelques conflits rares sont connus et pas corrigés (deux achats au même instant chez le même marchand, deux
  joueurs qui construisent sur la même case, une monture en double au retour d'un voyage).
- Compatibilité avec les autres mods : celle de l'original. Liste de mods courte et identique pour tous.

La liste complète, et ce qui est prévu : [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md).

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly** (cette version est compilée pour EA 23.350). **Tous les joueurs doivent avoir la même version de ce
fork** ; elle ne se connecte pas à la version du Workshop.

Il n'y a pas encore de téléchargement : il faut la compiler (ci-dessous), ou recevoir le zip de quelqu'un qui l'a
fait (`dev/make_release.ps1` fabrique `ElinTogether-independance.zip`, avec `Installer.bat` qui remplace la version
Workshop par celle-ci et `Desinstaller.bat` qui fait l'inverse).

Pour héberger : lancer Elin par Steam, charger une partie qui a un terrain revendiqué, puis Échap → Mods →
Elin Together.

## Compiler

Variables d'environnement : `ElinGamePath` (dossier du jeu) et `SteamContentPath` (`steamapps/workshop/content`,
pour `YKFramework.dll`). SDK .NET 11.0 preview, voir `global.json`.

```ps
git clone https://github.com/devmarcpro/elin-together
cd elin-together
dotnet restore ./ElinTogether --locked-mode
dotnet build ./ElinTogether -c ReleaseNightly
```

Le poste de développement (plusieurs fenêtres du jeu sur un PC, suites de tests en jeu, pont de test) est décrit
dans [`dev/SETUP.md`](dev/SETUP.md).

## Comment ça marche, en bref

Le principe d'origine : l'host simule le monde, chaque changement part vers les clients, les clients envoient
leurs actions à l'host. Cette version ajoute des **baux de zone** : un joueur qui quitte la carte de l'host lui
demande un bail sur la carte où il va, charge sa propre copie du monde et simule cette carte lui-même. Il la
renvoie à son retour et à chaque point de sauvegarde ; l'host reste la référence. Celui qui tient un bail peut
accueillir d'autres joueurs sur cette carte, et le passe à l'un d'eux quand il part.

## Signaler un problème

Pour cette version : [les tickets de ce dépôt](https://github.com/devmarcpro/elin-together/issues), avec les
fichiers `Player.log` et `ElinMP/Logs/Session_<date>.log` des deux joueurs
(`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`). Merci de ne pas signaler au projet d'origine les problèmes
de ce fork.

## Crédits

Le mod est l'œuvre de l'équipe Elin Together : [DK](https://github.com/gottyduke) et
[Redgeioz](https://github.com/Redgeioz) (code, architecture), [105gun](https://github.com/105gun) (code),
[Han](https://github.com/chuahan), Omega, [InuiDame](https://github.com/InuiDame),
[Drakeny](https://github.com/Drakeny) (tests), noa (Elin). Licence MIT, voir [LICENSE](LICENSE).

Les changements de ce fork ont été écrits avec un assistant de programmation (Claude Code), dirigé par le
propriétaire du fork ; chaque changement a son test en jeu, cité dans le message du commit. Aucun fichier du jeu
ni code décompilé du jeu n'est dans ce dépôt.
