# Instructions pour Claude — fork ElinTogether « indépendance »

Fork du mod multijoueur ElinTogether pour le jeu Elin. But fixé par l'utilisateur : **en jeu, aucune différence
entre l'host et les autres joueurs**. Dépôt : https://github.com/devmarcpro/elin-together (public), branche de
travail `feat/independent-travel`. `upstream` (ElinTogether/ElinTogether) est le projet d'origine : ne jamais y pousser.

## Par où commencer

1. `dev/DOCUMENTATION.md` : ce qui existe, comment ça marche, comment tester, limites, reste à faire (section 7).
2. La fin de `dev/MODLOG.md` : le journal, dernière entrée = où le travail s'est arrêté et quoi faire ensuite.
3. Les `dev/PLAN_*.md` : plans prêts à réaliser (quêtes à donjon phase 2, profil de mods…).
4. Machine pas encore installée (pas de `dev/_lab`, `mp_test.py` ne trouve pas le jeu) : suivre `dev/SETUP.md`.

## L'utilisateur

- Écrit en français. Réponses **courtes, en français simple, sans jargon** ; il ne lit pas le code.
- Chaque nouveau comportement doit être **une case à cocher côté host** (onglet « Server Setting »).
- Il veut voir : captures d'écran des nouveautés (`dev/_tools/showcase.py`), résumés honnêtes (ce qui marche,
  ce qui a été corrigé, ce qui reste, ce qui n'est pas testé).
- Demander avant de commencer une grosse nouveauté de conception. Ne **pas** commencer le « temps du monde
  commun » sans lui.

## Où sont les choses

| Chemin | Contenu |
|---|---|
| `ElinTogether/` | code du mod (C#, Harmony). Les deltas ont un numéro unique dans `Models/Delta/ElinDelta.cs` |
| `package/LangMod/` | textes : `EN/emp_localization.xlsx` (anglais + japonais), `CN/SourceLocalization.json` |
| `dev/_tools/` | banc de test : `mp_test.py` (lance host + clients), suites `*_suite.py`, `bot.py`, `showcase.py` |
| `dev/build.ps1`, `dev/make_release.ps1` | compiler + installer (Debug) ; fabriquer le zip à distribuer |
| `dev/_lab`, `dev/_shots`, `dev/_decomp`, `dev/_backup`, `dev/_tools/pylib` | **hors dépôt** : copies du jeu, journaux et captures, code du jeu décompilé, sauvegardes, bibliothèques Python |

Les commandes de test se lancent depuis `dev/` avec `PYTHONPATH=_tools/pylib`.

## Règles de travail

- **Tester comme un joueur joue** (retour de l'utilisateur, 2026-10-03 : sa vraie partie a trouvé en un quart
  d'heure ce que les suites rataient). Un test passe par le vrai chemin du jeu : marcher plutôt que se téléporter,
  le choix du dialogue ou du menu plutôt que la fonction interne qui « fait pareil ». Un raccourci du pont de test
  ne prouve que le raccourci. Les suites rapides restent pour prouver une correction (rouge puis vert) et ne rien
  casser ; les vraies parties et le bot disent ce qu'on n'a pas pensé à tester.
- **Un changement = un test = un commit.** Ne jamais laisser une correction sans test, même venue d'une relecture.
  Ce qui n'a pas pu être testé est écrit comme tel dans le commit, le journal et le résumé.
- Tenir `dev/MODLOG.md` (journal daté, pièges, résultats de tests) et `dev/DOCUMENTATION.md` à jour à chaque étape :
  c'est ce qui permet de reprendre après une coupure.
- Tests **courts**, sur des fenêtres déjà ouvertes, pour ce qui a changé. Les passes longues (`run_all.sh`) et les
  bots : seulement quand le PC est libre (vérifier avec `dev/_tools/idle.ps1`, ou demander).
- Fenêtres Elin toujours **muettes** (`-empmute`, `mp_test.py` le fait), lancées **une à la fois** ; ne pas
  compiler pendant un lancement. Le jeu doit être fermé pour `build.ps1`.
- Fermer Elin **par numéro de processus exact**. Ce travail passe avant les fenêtres Elin ouvertes par d'autres
  sessions Claude (les prévenir, puis fermer) ; **ne jamais fermer un jeu lancé par l'utilisateur**.
  `run_all.sh` ferme tous les Elin entre deux suites : PC libre seulement.
- Déléguer la lecture de code et les relectures à des agents (lecture seule) ; garder pour soi les tests en jeu.
  Faire relire chaque gros changement.
- Coupe-circuit : le même échec trois fois → l'écrire dans le journal et changer d'approche.
- Après un changement de texte existant, supprimer `LangMod/EN/SourceLocalization.json` dans le mod installé
  (fichier fabriqué par le jeu, qui garde les anciens textes).

## Ce qui ne va jamais dans le dépôt (il est public)

Fichiers du jeu, code décompilé (`dev/_decomp`), copies du jeu (`dev/_lab`), sauvegardes de l'utilisateur,
journaux et captures bruts (`dev/_shots`), bibliothèques tierces. `dev/.gitignore` les écarte : ne pas le contourner.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1          # compile en Debug et installe dans le jeu
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                                       # host + 1 client (--clients 2 ou 3)
python _tools/quest_suite.py                                   # une suite courte, sur les fenêtres ouvertes
bash _tools/run_all.sh <nom> shared_suite travel_suite          # suites longues à la chaîne
python _tools/showcase.py                                      # captures des nouveautés -> _shots/nouveautes
powershell -ExecutionPolicy Bypass -File dev\make_release.ps1   # zip à distribuer, puis refaire build.ps1
```

Pont de test (build Debug) : chaque fenêtre écoute sur 127.0.0.1, ports 27551 (host), 27552… (clients) ;
`dev/_tools/emp.py` envoie `state`, `eval` (du C# exécuté dans le jeu), `screenshot`.
