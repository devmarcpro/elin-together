# Chasse aux différences host / invité — 2026-10-04 (nuit)

Rendu par un agent, par **lecture seule** du jeu décompilé et du mod. **Rien n'a été joué** : chaque ligne est à
prouver par un test rouge avant d'être corrigée. Déjà connu ou corrigé : `PLAN_egalite_invites.md`.

Deux mécanismes nouveaux :
- **M-A** : le jeu agit chez l'host comme si l'invité était un habitant (`!IsPC`).
- **M-B** : tout `Trait.OnUse(Chara)` hors de la liste fermée de `Patches/Trait/TraitOnUsePatch.cs` s'exécute chez
  l'host puis chez tous les clients, et ouvre sa fenêtre sur leur écran (même défaut que la banque, M12).

| # | Ce que voit le joueur | Jeu (fichier:ligne) | Correction la plus petite | Confiance |
|---|---|---|---|---|
| **Haut** | | | | |
| 1 | un invité sous 20 % de points de vie reçoit « peur » et ne peut plus frapper | `Card.cs:4972`, `ActMelee.cs:110`, `ActRanged.cs:181` | ignorer `ConFear` venant de `DamageHP` pour un joueur distant | probable |
| 2 | guérisseur payant : l'invité paie, les soins sont effacés | `DramaCustomSequence.cs:1646-1669`, `ActEffect.cs:2579` | demander à l'host `HealHP` et `Cure`, comme la prière | probable |
| 3 | rangement automatique (`TaskDump`) d'un invité : l'host voit ses fenêtres se fermer, ses objets peuvent partir dans un coffre | `TaskDump.cs:67, 94, 172` | retirer `TaskDump` de la table des tâches (l'invité range chez lui) | probable |
| 4 | base réglée par l'invité (politiques, recherche, métiers, servante, foyer) : il paie, rien n'arrive chez l'host | `LayerPolicy.cs:39`, `TraitResearchBoard.cs:9`, `TraitResidentBoard.cs:11`, `DramaCustomSequence.cs:437-505, 1139-1163` | un message par famille (M14 étendu), ou dire « la base se règle chez l'host » | probable |
| **Moyen** | | | | |
| 5 | radio, juke-box, liste de lecture : fenêtre chez tout le monde | `TraitRadio.cs:17`, `TraitJukeBox.cs:15`, `TraitEditPlaylist.cs:3` | les ajouter à la liste de `TraitOnUsePatch.cs` | probable |
| 6 | caisse de ferme (quête de récolte) | `TraitFarmChest.cs:9` | idem | probable |
| 7 | runes et prises : fenêtre chez l'host, effet seulement chez l'invité | `TraitMod.cs:24`, `InvOwnerMod.cs:57-69` | liste + cas côté host « à la place du joueur » | probable |
| 8 | machine à gènes, roue | `TraitGeneMachine.cs:72-115`, `TraitGeneratorWheel.cs:30` | idem | probable |
| 9 | livre des résidents, livre de l'équipe | `TraitBookResident.cs:7`, `TraitBookRoster.cs:7` | idem | probable |
| 10 | carte au trésor lue : fenêtre chez tous, tirages différents par jeu | `TraitScrollMapTreasure.cs:13-32` | liste + tirage chez l'invité seul | à vérifier |
| 11 | investir (zone, boutique) : il paie, rien chez l'host | `DramaCustomSequence.cs:1188-1268` | un message « investir » vers l'host | probable |
| 12 | bénédiction des prêtresses : aucun effet | `DramaCustomSequence.cs:1327-1350` | demander la condition à l'host | probable |
| 13 | noyade et forte pluie : l'invité n'en souffre pas | `Chara.cs:4489`, `~4107` | les appliquer chez l'host pour un joueur distant | probable |
| 14 | vol à la tire d'un invité : l'host perd de l'endurance et peut avancer vers la victime | `AI_Steal.cs:125, 140, 206` | étendre `AISlaughterPatch` à `AI_Steal` | sûr |
| 15 | pied-de-biche (`AI_PryOpen`) hors de la table : tout reste chez l'invité | `Trait.cs:1061-1109` | l'ajouter à la table | à vérifier |
| 16 | retour, évacuation, passage : chez l'host l'invité est téléporté au hasard, ses alliés ne suivent pas | `ActEffect.cs:1718-1721, 1775-1783` | sauter ces cas chez l'host pour un joueur distant | à vérifier |
| 17 | les habitants ne remarquent que l'host (rumeurs, cadeaux, « bon retour ») | `AI_Idle.cs:621-695` | à décider (conseil) | — |
| 18 | tickets d'hôtesse : c'est l'host qui est massé | `Chara.cs:8869-8879` | `AsCrafter(from)` chez l'host | probable |
| **Bas** | | | | |
| 19 | note, nom de téléporteur, nom de zone écrits par un invité | `TraitNote.cs:29`, `TraitTeleporter.cs:38`, `TraitWaystone.cs:25` | les ajouter à la liste de `CardActReplayEvent.cs` | probable |
| 20 | pinceau, vue de carte : le mode d'action de l'host change | `TraitPainter.cs:19`, `TraitViewMap.cs:9` | liste de `TraitOnUsePatch.cs` | à vérifier |
| 21 | détecteur, tombe d'épée : saisie ou scène chez l'host | `TraitDetector.cs:19`, `TraitDaggerGrave.cs:13-52` | idem | probable |
| 22 | changement d'alias, retour du vide : fenêtre chez l'host | `ActEffect.cs:1659, 1694` | sauter chez l'host pour un joueur distant | probable |
| 23 | recette lue par un invité : l'host l'apprend aussi | `TraitRecipe.cs:18`, `TraitRecipeCat.cs:10` | comme `TraitBookSkillPatch` | probable |
| 24 | faucille : l'ecopo va à l'host | `TaskCullLife.cs:60-63` | donner à `owner` | sûr |
| 25 | dons de l'host dans les formules (plats, qualité du butin, « Strife ») | `FoodEffect.cs:25`, `Card.cs:5489`, `Card.cs:4822` | « à la place du joueur » chez l'host | probable |
| 26 | mort évitée par le don « fate » : seuil d'un habitant pour l'invité | `Card.cs:4651` | idem autour de `DamageHP` | à vérifier |
| 27 | survie et ciel (portail, casque du ciel, moongate) : l'host est déplacé | `TraitLandingPortal.cs:41`, `TraitSkyHelm.cs:13`, `TraitMoongate.cs:42` | liste de `TraitOnUsePatch.cs` | rare |
| 28 | actes de divorce et d'anneau perdu écrits avec `EClass.pc` | `TraitDeedDivorce.cs:18`, `TraitDeedLostRing.cs:24` | à voir | à vérifier |

Ordre proposé : 1, 2, 3, puis d'un coup 5-6-8-9-10-20-21-22 (une seule liste à compléter), 7, 14, 13, 11, 4, 12, 15.

Pas parcouru : les zones spéciales `Zone_*`, les dialogues hors `DramaCustomSequence`, les fenêtres `Layer*`, les
tâches hors table (torture, chariot, entraînement, peinture), les mutations et l'éther, les marchands un par un, les
religions au-delà de la prière, le détail de `GoalCombat` (`ShouldAllyAttack` lit les réglages de l'host).
