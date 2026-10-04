# Message de départ pour une nouvelle session

À coller tel quel dans une nouvelle session ouverte dans **`G:\ElinMods`** (le dossier a été déplacé le 2026-10-04 ;
`C:\Users\steamdeckwin\Documents\ElinMods` n'est plus qu'un raccourci vers lui).

---

Je reprends le travail sur ElinTogether (le fork « indépendance »), dans `G:\ElinMods\ElinTogether`. Charge d'abord
le skill `ponytail:ponytail` et garde-le pour toute la session. **Active Remote Control tout de suite.** Lis dans cet
ordre : `CLAUDE.md`, `dev/HANDOFF.md`, la fin de `dev/MODLOG.md` (section « Points restants traités en autonomie »),
`dev/PLAN_egalite_invites.md`, `dev/PLAN_quetes_donjon_a_deux.md`, `dev/PLAN_chasse_differences.md` et la section 7
de `dev/DOCUMENTATION.md`. Réponds-moi en français simple et court, sans jargon.

Le but ne change pas : **aucune différence entre un joueur host et un joueur invité, tout doit être fluide, tous les
joueurs doivent pouvoir tout faire** ; on doit pouvoir jouer à Elin à plusieurs comme si le jeu avait été fait pour
ça. Je joue comme invité, avec un ami comme host.

Comment travailler :
- **Travaille en continu, sans t'arrêter et sans me demander d'autorisation : j'autorise tout.** Quand une liste est
  finie, cherche la suivante (lecture du code du jeu, parties au bot, commentaires du Workshop) au lieu de rendre
  la main. Si le mode de l'application demande encore des confirmations, dis-le-moi une fois, je changerai le mode.
- Chaque décision de conception (plusieurs options défendables, effet sur l'équité entre joueurs ou sur la
  sauvegarde) est tranchée par le skill `llm-council`, puis appliquée ; note la question, le verdict en deux lignes
  et ce qui a été écarté dans `dev/MODLOG.md`. Critères, dans l'ordre : 1) un invité obtient ce qu'un joueur solo
  obtiendrait ; 2) pas de duplication ni de perte d'objets, d'or ou d'expérience ; 3) le changement le plus petit
  qui marche ; 4) aucun risque pour les sauvegardes existantes. Ne me pose la question que si le verdict demande
  une action irréversible sur mes sauvegardes. Un bug à une seule bonne réponse se corrige sans conseil.
- Utilise autant d'agents que tu veux : plusieurs en parallèle pour lire le code, écrire des corrections dans des
  fichiers différents, relire (agent `relecteur-elintogether` avant la première compilation de tout changement de
  plus de quelques lignes). Les tests en jeu restent en série : deux fenêtres Elin au plus.
- Un point = un test rouge puis vert = un commit, sur la branche `fix/points-restants` (pas sur la branche
  principale). Compile (`dev/build.ps1`, jeu fermé) et lance les tests après chaque point.
- Ce qui ne peut pas être vérifié sans deux vrais joueurs : fais le changement, dis-le clairement, ajoute-le à ma
  liste d'essais dans `dev/HANDOFF.md`.
- Tiens `dev/MODLOG.md`, `dev/HANDOFF.md` et `dev/DOCUMENTATION.md` à jour à chaque étape.
- Ne publie pas de version et ne pousse rien sur GitHub sans me le dire dans le résumé ; ne retire aucune ancienne
  version.

Par où commencer : la liste « À faire ensuite » de `dev/HANDOFF.md`, dans l'ordre. En tête : compiler et tester la
branche `wip/lots-non-compiles` (du code écrit par des agents, jamais compilé), puis les quêtes à donjon à deux.

À la fin de chaque grande étape, un résumé en français simple : les décisions du conseil (une ligne chacune), ce qui
est fait et testé, ce qui est fait mais reste à essayer en vrai, ce qui n'a pas été fait et pourquoi, les questions
qui restent pour moi.

Modèles : pas tout au modèle le plus cher. `haiku` pour chercher et résumer ; `sonnet` pour relire, écrire un test ou
une correction sur un modèle existant, tenir la documentation, les avis et relectures du conseil ; `opus` pour
concevoir, pour le président du conseil et pour un bug qui résiste.
