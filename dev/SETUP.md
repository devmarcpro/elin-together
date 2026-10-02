# Installer le poste de développement sur une autre machine

Tout ce qui sert à développer et tester le fork est dans ce dépôt, dossier `dev/`. Ce guide remet une machine
Windows en état de compiler, lancer plusieurs fenêtres Elin et passer les tests. Compter 30 à 45 minutes.

## 0. Ce qu'il faut

- Windows 10 ou 11, Steam, **Elin acheté sur ce compte Steam** (les tests lancent le vrai jeu).
- Elin sur le **canal Nightly** (Steam → Elin → Propriétés → Bêtas), version EA 23.350 Patch 1 ou plus récente.
  Le fork se compile en `DebugNightly` / `ReleaseNightly`.
- Environ 3 Go libres sur **le même disque que le jeu** (les copies de test sont des liens vers le jeu).

## 1. Le dépôt

```
git clone https://github.com/devmarcpro/elin-together
cd elin-together
git checkout feat/independent-travel
git remote add upstream https://github.com/ElinTogether/ElinTogether.git
git remote set-url --push upstream NE-JAMAIS-POUSSER-SUR-UPSTREAM
git config user.name "<ton nom>"
git config user.email "<ton adresse>"
```

`upstream` est le projet d'origine : on y lit, **on n'y pousse jamais** (la troisième ligne rend un envoi par
erreur impossible). Sur une machine neuve git ne sait pas qui tu es : sans les deux dernières lignes, aucun
commit ne se fait. Le premier `git push` ouvre une fenêtre de connexion à GitHub (à faire soi-même, une fois).
Ouvrir la session Claude dans le dossier du dépôt (le fichier `CLAUDE.md` à la racine lui dit comment travailler).

### Autre façon : emporter tout le dossier de travail

Ne **pas** copier le dossier `ElinMods` tel quel : il contient une centaine de raccourcis vers le jeu (les copies
de test), que Windows recopierait comme autant de jeux entiers. À la place, sur l'ancienne machine :

```
python ElinTogether\dev\_tools\make_transfer.py        # fabrique Documents\ElinMods-transfert.zip
```

Copier ce zip, le décompresser sur la nouvelle machine (dans `Documents` de préférence), puis lancer une fois :

```
powershell -ExecutionPolicy Bypass -File ElinMods\ElinTogether\dev\apres-deplacement.ps1
```

Ce script remet les raccourcis entre dossiers, refait les copies du jeu et liste ce qui manque encore (jeu,
Python, SDK…). Avec cette façon, l'étape 2 ci-dessous est déjà faite, et l'étape 5 aussi si le script a tout trouvé.
Les copies du jeu recopient les réglages du mod et `loadorder.txt` : tant qu'Elin n'a pas tourné une fois avec le
mod (étape 4.6), le script le dit et ne les fait pas. Le relancer ensuite.

## 2. Ce qui n'est pas dans le dépôt (à copier à la main depuis l'ancienne machine)

| Quoi | D'où (ancienne machine) | Où (nouvelle machine) | Obligatoire |
|---|---|---|---|
| Le monde de test | `Documents\ElinMods\_lab\saves\world_lab.pristine` (dossier, 1 Mo) | `dev\_lab\saves\world_lab.pristine` | **oui**, tous les tests partent de lui |
| Tes vraies sauvegardes | `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\Save` | même endroit | seulement si tu veux jouer tes parties |
| Sauvegardes d'origine des réglages | `Documents\ElinMods\_backup` | `dev\_backup` | non |

Rien d'autre n'est à copier. Le code décompilé du jeu, les copies du jeu et les bibliothèques Python se
refabriquent (étapes 4 à 6). Ils ne sont **jamais** mis dans le dépôt : il est public.

## 3. Outils à installer

1. **SDK .NET `11.0.100-preview.5.26302.115`** exactement (le projet l'exige, voir `global.json`), **Python 3.12**
   et **git** (avec lui vient `bash`, dont `_tools/run_all.sh` a besoin) :
   ```
   winget install --id Microsoft.DotNet.SDK.Preview --version 11.0.100-preview.5.26302.115
   winget install --id Python.Python.3.12
   winget install --id Git.Git
   ```
   Le SDK et git affichent chacun une fenêtre Windows « Autoriser cette application ? » : il faut être devant
   l'écran pour cliquer Oui, sinon l'installation s'annule toute seule au bout de deux minutes. Ouvrir ensuite
   un nouveau terminal (l'ancien ne voit pas les nouveaux programmes).
2. Bibliothèques Python des outils, dans le dossier que les outils attendent (déjà là si le dossier de travail
   est venu par le zip : elles sont faites pour Python 3.12 et rien d'autre) :
   ```
   python -m pip install --target dev/_tools/pylib -r dev/requirements.txt
   ```
3. (Pour relire le code du jeu) ILSpy en ligne de commande, version 9.1 (la 11 demande .NET 10). Déjà là aussi
   si le dossier est venu par le zip (`dev/_tools/ilspycmd.exe` et `dev/_tools/.store`) :
   ```
   dotnet tool install ilspycmd --version 9.1.0.7988 --tool-path dev/_tools
   ```

## 4. Le jeu

1. Lancer Elin une fois normalement, puis le fermer.
2. Workshop : s'abonner à **YK Framework** (3400020753) et à **Elin Together** (3773298709). Relancer le jeu une
   fois pour qu'ils apparaissent dans `loadorder.txt`, puis le fermer.
3. Dans le dossier du jeu, créer `steam_appid.txt` contenant seulement `2135150` (sans lui, une deuxième fenêtre
   ne peut pas parler à Steam).
4. Si Steam n'est pas dans `C:\Program Files (x86)\Steam`, définir la variable d'environnement utilisateur
   `ELIN_GAME_PATH` sur le dossier du jeu (celui qui contient `Elin.exe`). Tous les scripts la lisent.
5. Compiler et installer le build de développement, puis le rendre actif à la place de la version Workshop :
   ```
   powershell -ExecutionPolicy Bypass -File dev\build.ps1
   powershell -ExecutionPolicy Bypass -File dev\use-workshop.ps1 -Dev
   ```
   (`dev\use-workshop.ps1` sans `-Dev` remet la version Workshop pour jouer normalement.)
6. Lancer Elin une fois : le mod crée `BepInEx\config\dk.elinplugins.elintogether.cfg`. Fermer le jeu, ouvrir ce
   fichier et, dans la section `[Dev]`, mettre `Listener = true` (le pont de test, ports 27551 et suivants).
   Dans cet ordre : à son tout premier lancement sur une machine, le mod remet ses réglages à neuf, un
   `Listener = true` écrit avant est effacé.

**Si Elin n'a jamais tourné sur cette machine** (pas fait les étapes 1 et 2 à la main) :

- `loadorder.txt` n'existe pas encore, `use-workshop.ps1` échoue. Le jeu le crée à son premier lancement ; quand
  les deux versions du mod sont là, il prend de lui-même celle de `Package` (le build de développement).
- Le jeu s'arrête sur le choix de la langue et ne garde ses réglages qu'une fois ce choix fait. Pour l'éviter,
  poser avant le lancement, dans `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\Save\`, le `config.txt` de
  l'ancienne machine (`dev\_backup\config.test-fenetre.txt` : fenêtre 1280×720) **et** un `version.txt` (le bloc
  `version` de ce `config.txt`, entre accolades). Sans `version.txt`, le jeu ignore `config.txt`.
- Les sauvegardes Steam Cloud arrivent dans `Cloud Save`, pas dans `Save` : le dossier `Save` est vide, c'est
  normal. Les tests n'utilisent que `world_lab`, recopié à chaque fois depuis `dev\_lab\saves`.

## 5. Les copies du jeu pour les tests

Elin refuse de s'ouvrir deux fois. `make_lab.py` fabrique des lanceurs (des liens vers le jeu, pas des copies),
chacun avec sa propre identité de joueur :

```
cd dev
set PYTHONPATH=_tools/pylib
python _tools/make_lab.py Elin2 2
python _tools/make_lab.py Elin3 3
python _tools/make_lab.py Elin4 4
```

À refaire après chaque mise à jour d'Elin. Pour que le bouton « Add a bot player » du menu trouve ces copies,
définir la variable d'environnement utilisateur `ELINTOGETHER_LAB` sur `<dépôt>\dev\_lab`.

## 6. Le code du jeu, pour le lire (jamais publié)

```
dev\_tools\ilspycmd.exe -p -o dev\_decomp\Elin -r "<Elin>\Elin_Data\Managed" "<Elin>\Elin_Data\Managed\Elin.dll"
dev\_tools\ilspycmd.exe -p -o dev\_decomp\YKF "<Steam>\steamapps\workshop\content\2135150\3400020753\YKFramework.dll"
```

Les quatre bibliothèques `Plugins.*.dll` du même dossier `Managed` se décompilent de la même façon si besoin
(`Plugins.BaseCore`, `Plugins.UI`, `Plugins.Modding`, `Plugins.ActorSystem`).

Si `ilspycmd.exe` ne dit rien et ne fait rien : il est fait pour .NET 8, et seul le SDK 11 est installé. Avant
de le lancer (PowerShell) : `$env:DOTNET_ROLL_FORWARD = "LatestMajor"; $env:DOTNET_ROLL_FORWARD_TO_PRERELEASE = "1"`.
Inutile de refaire `dev\_decomp` s'il est venu par le zip et que la version d'Elin est la même.

## 7. Vérifier que tout marche

Depuis `dev/`, PC libre (deux fenêtres Elin muettes vont s'ouvrir) :

```
set PYTHONPATH=_tools/pylib
python _tools/mp_test.py            # host + 1 client, environ 3 minutes
python _tools/parity_suite.py       # 16 vérifications, 1 minute
python _tools/trade_suite.py        # 31 vérifications, 2 minutes
```

(Une vérification de plus par journal de 2e ou 3e client datant de moins de deux heures dans `_shots`.)

Si `mp_test.py` dit « pont du host » sans fin : le pont de test n'est pas activé (étape 4.6) ou le jeu n'a pas
chargé le build de développement (étape 4.5). Si une deuxième fenêtre se ferme aussitôt : refaire l'étape 5.

## 8. À savoir

- **Pas de mise en veille du PC** pendant une longue série de tests : tout s'arrête sinon. Laisser tourner
  `powershell -ExecutionPolicy Bypass -File dev\_tools\keep-awake.ps1` dans un autre terminal (il ne change aucun
  réglage de Windows et s'arrête seul au bout de deux heures, `-Minutes 480` pour une nuit).
- Les fenêtres se lancent une à la fois (`mp_test.py` le fait). Ne pas compiler pendant un lancement.
- `dev/_shots` reçoit les captures et les journaux des tests ; rien n'y est précieux.
- Sur l'ancienne machine, les dossiers vivaient dans `Documents\ElinMods\` (`_tools`, `_lab`, `_shots`…) : le
  journal `dev/MODLOG.md` en parle encore avec ces chemins. Lire `dev/` à la place.
