# Prompt à donner à la session Claude de la nouvelle machine

À coller tel quel dans une session Claude Code ouverte dans `Documents\ElinMods\ElinTogether`.

```
Je viens de déplacer mon projet ElinTogether sur cette machine. Le contenu du dossier ElinMods est dans
Documents\ElinMods (le dépôt du mod est dans Documents\ElinMods\ElinTogether). Installe tout ce qu'il faut pour
que le développement et les tests en jeu marchent ici comme sur l'ancienne machine, sans que j'aie à m'en occuper,
puis reprends le travail là où il s'est arrêté.

Lis d'abord, dans cet ordre : CLAUDE.md (à la racine du dépôt), dev/SETUP.md, puis la fin de dev/MODLOG.md.
Réponds-moi en français simple et court, sans jargon : je ne lis pas le code.

Ce que tu dois faire toi-même, dans l'ordre :

1. État des lieux. Vérifie ce qui est déjà là : le dépôt et sa branche feat/independent-travel, le dossier dev/,
   le monde de test (dev\_lab\saves\world_lab.pristine ou Documents\ElinMods\_lab\saves\world_lab.pristine),
   Steam et le dossier du jeu Elin (emplacement habituel, sinon cherche dans les bibliothèques Steam et règle la
   variable d'environnement utilisateur ELIN_GAME_PATH), Python, le SDK .NET, git.
2. Outils manquants. Installe ce qui manque avec winget : Python 3.12, le SDK .NET exact demandé par global.json
   (11.0.100-preview.5.26302.115), git. Si dev\_tools\pylib est absent ou si Python n'est pas en 3.12, refais les
   bibliothèques : python -m pip install --target dev/_tools/pylib -r dev/requirements.txt
3. Remise en place. Lance dev\apres-deplacement.ps1 et traite tout ce qu'il liste dans « Reste à faire ».
   Si le dossier a été copié tel quel au lieu de passer par le zip, il peut contenir de fausses copies du jeu
   (Documents\ElinMods\_lab\Elin2, Elin3, Elin4, et des doubles de _tools ou _release à côté du dépôt) : les
   copies du jeu se refont avec dev\_tools\make_lab.py, et la seule version des outils qui compte est celle de
   dev\_tools. Ne supprime jamais un dossier à travers un raccourci (jonction) : retire le raccourci lui-même.
4. Le jeu. Crée steam_appid.txt (contenu : 2135150) dans le dossier du jeu s'il manque. Compile avec
   dev\build.ps1, puis active le build de développement avec dev\use-workshop.ps1 -Dev. Lance Elin une fois pour
   que le mod crée son fichier de réglages, ferme-le, puis mets Listener = true dans la section [Dev] de
   BepInEx\config\dk.elinplugins.elintogether.cfg.
5. Copies du jeu pour les tests : dev\_tools\make_lab.py pour Elin2, Elin3 et Elin4 (identités 2, 3 et 4), et la
   variable d'environnement utilisateur ELINTOGETHER_LAB sur dev\_lab.
6. Code du jeu pour le lire : si dev\_decomp\Elin est vide, refais-le (SETUP.md, étape 6). Il ne doit jamais
   être mis dans le dépôt.
7. Vérification en jeu, depuis dev/ : mp_test.py, puis parity_suite.py et trade_suite.py. Les fenêtres se lancent
   une à la fois et restent muettes. Tout doit passer.
8. Git : vérifie que git status est propre, que le remote origin est https://github.com/devmarcpro/elin-together
   et qu'un git pull ne ramène rien de nouveau. Ne pousse jamais sur upstream.

Ce que toi tu ne peux pas faire, et que tu dois me demander en une seule fois, clairement, avec les clics à
faire : me connecter à Steam, installer Elin, le mettre sur le canal Nightly (Propriétés → Bêtas), m'abonner dans
le Workshop à YK Framework (3400020753) et à Elin Together (3773298709), lancer le jeu une première fois, et me
connecter à GitHub pour pouvoir pousser. Vérifie d'abord ce qui est déjà fait pour ne me demander que le reste,
et continue pendant ce temps tout ce qui ne dépend pas de moi.

Règles : ne ferme jamais un jeu que j'ai lancé moi-même ; ferme tes propres fenêtres Elin par numéro de processus
exact ; ne lance les tests en jeu que si je ne suis pas en train d'utiliser le PC (demande-moi en cas de doute) ;
ne mets dans le dépôt ni fichiers du jeu, ni code décompilé, ni sauvegardes ; un changement = un test = un commit.
Si une étape échoue trois fois de la même façon, note-le dans dev/MODLOG.md et essaie autrement.

Quand tout marche, écris une entrée datée dans dev/MODLOG.md (ce qui a été installé, ce qui diffère de
l'ancienne machine, les pièges rencontrés), corrige dev/SETUP.md si une étape était fausse ou manquante, commite
et pousse. Donne-moi alors un résumé court : ce qui marche, ce qui reste à ma charge, ce qui n'a pas pu être
vérifié.

Ensuite reprends le travail en attente, dans cet ordre : les deux tests en échec notés à la fin du journal
(shared_suite G5 et travel_suite S15 : scénario de test périmé ou vrai défaut ?), une série de bots de 30 minutes,
un nouveau zip avec dev\make_release.ps1, puis la suite de la liste « Reste à faire » de dev/DOCUMENTATION.md.
Ne commence pas le « temps du monde commun » sans moi.
```

## Avant de coller ce prompt

- Avoir décompressé `ElinMods-transfert.zip` dans `Documents` (ou copié le contenu de `ElinMods` dans
  `Documents\ElinMods`).
- Avoir installé Steam et Claude Code sur la machine, et ouvert la session dans `Documents\ElinMods\ElinTogether`.
- Le reste (Python, SDK, compilation, copies du jeu, tests), la session le fait.
