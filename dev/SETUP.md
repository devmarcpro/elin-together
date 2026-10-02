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
```

`upstream` est le projet d'origine : on y lit, **on n'y pousse jamais**. Ouvrir la session Claude dans le dossier
du dépôt (le fichier `CLAUDE.md` à la racine lui dit comment travailler).

## 2. Ce qui n'est pas dans le dépôt (à copier à la main depuis l'ancienne machine)

| Quoi | D'où (ancienne machine) | Où (nouvelle machine) | Obligatoire |
|---|---|---|---|
| Le monde de test | `Documents\ElinMods\_lab\saves\world_lab.pristine` (dossier, 1 Mo) | `dev\_lab\saves\world_lab.pristine` | **oui**, tous les tests partent de lui |
| Tes vraies sauvegardes | `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\Save` | même endroit | seulement si tu veux jouer tes parties |
| Sauvegardes d'origine des réglages | `Documents\ElinMods\_backup` | `dev\_backup` | non |

Rien d'autre n'est à copier. Le code décompilé du jeu, les copies du jeu et les bibliothèques Python se
refabriquent (étapes 4 à 6). Ils ne sont **jamais** mis dans le dépôt : il est public.

## 3. Outils à installer

1. **SDK .NET `11.0.100-preview.5.26302.115`** exactement (le projet l'exige, voir `global.json`).
2. **Python 3.12**.
3. Bibliothèques Python des outils, dans le dossier que les outils attendent :
   ```
   python -m pip install --target dev/_tools/pylib -r dev/requirements.txt
   ```
4. (Pour relire le code du jeu) ILSpy en ligne de commande, version 9.1 (la 11 demande .NET 10) :
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

## 7. Vérifier que tout marche

Depuis `dev/`, PC libre (deux fenêtres Elin muettes vont s'ouvrir) :

```
set PYTHONPATH=_tools/pylib
python _tools/mp_test.py            # host + 1 client, environ 3 minutes
python _tools/parity_suite.py       # 17 vérifications, 1 minute
python _tools/trade_suite.py        # 32 vérifications, 2 minutes
```

Si `mp_test.py` dit « pont du host » sans fin : le pont de test n'est pas activé (étape 4.6) ou le jeu n'a pas
chargé le build de développement (étape 4.5). Si une deuxième fenêtre se ferme aussitôt : refaire l'étape 5.

## 8. À savoir

- **Désactiver la mise en veille du PC** pendant une longue série de tests : tout s'arrête sinon.
- Les fenêtres se lancent une à la fois (`mp_test.py` le fait). Ne pas compiler pendant un lancement.
- `dev/_shots` reçoit les captures et les journaux des tests ; rien n'y est précieux.
- Sur l'ancienne machine, les dossiers vivaient dans `Documents\ElinMods\` (`_tools`, `_lab`, `_shots`…) : le
  journal `dev/MODLOG.md` en parle encore avec ces chemins. Lire `dev/` à la place.
