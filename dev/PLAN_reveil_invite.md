# Réveil de l'invité (point 10 de la soirée du 6 octobre) — 2026-10-06

Demande : « vérifie si les invités apprennent des sorts et des recettes comme l'hôte quand ils dorment ».
État : **écrit, compile en Release (0 erreur), jamais joué** (le jeu était pris). Test : `sleep_suite.py` K1, à lancer.
`J:` = `dev/_decomp/Elin_23351/`, `M:` = `ElinTogether/`.

## 1. Ce qu'un joueur solo obtient, et l'invité (avant / après ce changement)

Début de nuit (`J:ConSleep.cs:62-143`, `J:LayerSleep.cs:40-50`)

| Ce que fait le jeu | Invité avant | Invité après |
|---|---|---|
| Monstre de rêve (`SuccubusVisit`, l.64-68) | non (traité à part, plan sommeil) | pareil |
| Descend de monture (l.71-82), remonte au réveil (l.240-255) | non, il reste en selle | pareil (rien à rendre) |
| Familiers « dormir à côté » (l.106-130) | oui (`BringCompanionsBeside`) | pareil |
| Saignement, poison, miasme retirés (l.138-140) | **non** | **non** (voir 4) |
| Révélation du dieu, compteur `stats.slept` (LayerSleep l.48-49) | oui, dans son jeu (`SleepStartDelta`) | pareil |

Fin de nuit (`J:LayerSleep.cs:52-101`)

| Ce que fait le jeu | Invité avant | Invité après |
|---|---|---|
| Bases rattrapées (`SimulateFaction`, l.57-60) | non, voulu | pareil |
| Boîtes-repas des habitants (l.61-75) | faites par l'host, selon l'amitié envers l'host | pareil |
| Repos selon SON lit et SON oreiller (`Chara.OnSleep(bed)`, l.76-79 ; cercueil = pas de soleil) | **non** : la puissance du lit de l'host | **oui** |
| Oreiller d'Opatos : sites de la carte du monde renouvelés (l.81-84) | non | **non** (voir 4) |

Réveil (`J:ConSleep.cs:228-352`)

| Ligne | Ce que fait le jeu | Invité avant | Invité après |
|---|---|---|---|
| 262-266 | reprend lit et oreiller posés par la barre | oui | oui |
| 267-310 | lit les livres de son grimoire (sorts appris, livres usés, livre ancien déchiffré) | **non** | **oui** |
| 315 | une recette en rêve (oreiller d'Ehekatl compté) | **non** : seulement celle de l'host | **oui**, la sienne, et l'host la reçoit |
| 316 | un sort en rêve | oui | oui (une seule fois) |
| 317-320 | oreiller d'un dieu : le dieu parle | **non** | **oui** |
| 321-331 | oreiller de Jure : −15 de raison ; renaissance (don 1275) | **non** pour Jure ; renaissance donnée par l'host | **oui** pour Jure (voir 3) |
| 332-351 | dons de karma 1270 / 1271 perdus ou gagnés, selon SON karma | **non** | **oui** |

## 2. Ce qui a été changé

- `M:Models/Delta/Chara/CharaSleepDelta.cs` (réécrit, repris de `_shots/reveil_invite.patch`) :
  - chez l'invité qui dort : `pc.OnSleep(son lit)`, puis `slept = true` et `Kill()` : c'est le réveil du jeu lui-même
    (`ConSleep.OnRemoved`) qui joue tout le reste. S'il ne dormait pas : l'ancien comportement, inchangé.
  - **recette** : tirée *après* le réveil, hors du « geste du joueur ». Raison : tirée pendant, elle partait chez
    l'host par `AddRecipeDelta`, que l'host renvoie à tout le monde, donc aussi à celui qui l'a apprise : il
    l'avait deux fois. C'est le défaut de l'essai retiré (journal `_shots/sleep_suite-lot2.log` : host +2, invité +3).
  - l'invité envoie ensuite à l'host un `CharaSleepDelta` (champs 2 et 3, nouveaux) : ses livres lus (numéro, charges
    restantes, lu ou non) et l'identifiant de sa recette. L'host : retire les charges (seulement des livres de ce
    joueur, seulement à la baisse), détruit le livre vide, apprend la recette et l'envoie aux **autres** invités
    (`AddRecipeDelta`, sauf à l'expéditeur).
  - l'écran de nuit se ferme même si le réveil plante (`finally`).
- `M:Patches/Synchronization/SleepSynchronizationContext.cs:206-211` : préfixe sur `RecipeManager.OnSleep` qui
  retarde le tirage pendant ce réveil. `_bed` / `TakeBed` : **gardés et utilisés** (le lit de l'invité).
- Pas de nouveau delta, `ElinDelta.cs` pas touché.
- `dev/_tools/sleep_suite.py` : K1 compare les recettes **une par une** entre host et invité (au lieu d'un total), et
  revérifie 3 secondes après (un doublon qui revient plus tard se voit) ; `said` cherche toutes les variantes d'un
  message.

## 3. Ce dont je ne suis pas sûr

1. **Rien n'a été joué.** K1 doit être lancé : `python _tools/sleep_suite.py --only k1`.
2. Pourquoi K1 disait « 0 message de recette » avec l'essai : pas expliqué. Les totaux (host +2, invité +3) disent
   que le tirage avait bien eu lieu et que la recette revenait en double. J'ai rendu `said` plus tolérant (variantes),
   sans preuve que c'était la cause. Si ce contrôle reste rouge seul, regarder le texte de `learnRecipeSleep`.
3. Oreiller de Jure chez l'invité : le jeu retire 15 de raison à « tout le groupe ». Chez l'invité le groupe contient
   aussi l'host et les autres joueurs : baisse affichée chez lui seulement pour eux (non vérifié qu'elle ne part pas
   chez l'host ; K1 contrôle que la raison de l'host ne bouge pas).
4. Dons de karma et sorts : je suppose qu'ils arrivent chez l'host comme tout changement d'élément du joueur
   (vu dans le journal pour le sort du livre). Pas contrôlé pour les dons 1270 / 1271.
5. Lecture ratée pendant le sommeil : comme pour toute lecture d'un invité, la confusion et les monstres n'arrivent
   pas (limite déjà acceptée, MODLOG conseil du 4 octobre) ; mana et téléportation, oui.
6. Livre ancien déchiffré : noté chez l'host, pas envoyé aux autres invités (ils voient l'ancien nom jusqu'au
   rechargement de la carte).
7. La liste des recettes passe par le pont de test en un seul texte : si un monde en connaît des milliers, à surveiller.

## 4. Vu en passant, PAS corrigé (hors des fichiers permis)

- **Recette apprise par un invité = comptée deux fois chez lui**, pour toute recette (parchemin lu, récolte) :
  `M:Models/Delta/Misc/AddRecipeDelta.cs:20`, l'host fait `net.Delta.AddRemote(this)`, qui repart aussi vers
  l'expéditeur. Correction d'une ligne : `host.SendDeltaToAllExcept(OriginPeer, this)`. `hunt_suite` D9 ne le voit
  pas (il lit le compteur du lecteur avant le retour). Déduit du code et du journal lot2, pas rejoué.
- **Recette de bloc ou de sol (avec pilier / pont) = comptée deux fois chez celui qui la reçoit** :
  `AddRecipeEvent` envoie un message par variante, et chaque message refait les variantes à l'arrivée. K1 peut
  donc rester rouge sur le contrôle des recettes si l'host tire une telle recette : ce serait ce défaut-là.
- Un invité **parti seul** qui apprend une recette (nuit comprise) : elle n'arrive pas chez l'host
  (`M:Net/Host/ElinNetHostUpdate.cs:116` ne laisse pas passer `AddRecipeDelta` d'un joueur éloigné).
- Saignement, poison, miasme retirés au coucher : pour l'host seulement. Plus petit ajout : dans `OnSleepStart`
  (SleepSynchronizationContext), trois `RemoveCondition` par invité endormi. Pas fait : pas de test sûr (un invité
  empoisonné à 1 PV meurt pendant l'attente).
- Oreiller d'Opatos d'un invité : sans effet (c'est l'oreiller de l'host qui compte).
