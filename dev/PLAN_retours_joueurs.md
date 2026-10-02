# Plan — retours des joueurs (Workshop + dépôt d'origine), 2026-10-02

Demande de l'utilisateur le 2026-10-02 : « il faut régler tout ça ». Source des retours : `MODLOG.md`, sections
« Page Workshop » et « Page GitHub du projet d'origine ». Trois agents ont lu le code (lecture seule) pour dire ce
qui existe encore dans le fork. **Rien de ce qui suit n'est vérifié en jeu tant que la ligne ne le dit pas.**

Règle : un défaut = un test qui le montre (rouge) = une correction = le test vert = un commit. Ce qui change la
façon de jouer est proposé à l'utilisateur avant d'être codé, et devient une case de l'host.

## A. Combat tour par tour

| Retour | Verdict de la lecture | À faire |
|---|---|---|
| « La dinde joue 20 fois de suite » | Réglé par la case « Combat on each player's time » : un monstre ne reçoit du temps qu'aux vrais tours du joueur qu'il combat (`Patches/PlayerCombatTime.cs:73-119`). | rien |
| Reste possible | Le temps donné au monstre se calcule avec la vitesse de la **copie** du joueur chez l'host (`PlayerCombatTime.cs:80`). Cette copie n'est pas « le joueur » pour le jeu : en surcharge maximale elle perd 100 % de vitesse au lieu de 50 % → les monstres auraient ~10 tours pour un. | Test : surcharger le client, compter les tours du monstre par tour du joueur (`combat_suite`). Correction : prendre la vitesse annoncée par le client (`NetPeerState.Speed`). |
| Fée rapide jouant « à la vitesse moyenne » | Réglé par la même case, si « Shared Average Speed » est décochée. | rien |
| Fée qui n'esquive pas | Impossible à dire en lisant. Le tirage se fait chez l'host sur sa copie du personnage ; seules les valeurs de base sont synchronisées. Si l'esquive vient de la race, d'un don ou de l'équipement, la copie peut ne pas l'avoir. | Test : comparer chez l'host et chez le client `Evalue(57)`, `Evalue(151)`, `Evalue(150)`, `DV`, `PER` du même personnage. Se recoupe avec B « dons sans effet ». |
| Ceux qui construisent sont bloqués pendant un combat | Réglé par la même case (pas de pause, pas de file d'attente). Si la case est décochée, le tour par tour d'origine revient pour tous. | rien |
| La case « Turn-Based Combat » | Sans effet quand « Combat on each player's time » est cochée, mais toujours affichée. | Le dire dans la ligne d'explication, ou la griser. |
| Limites de la case du fork | Un monstre sans cible joueur vit en temps réel ; un monstre ne suit que l'horloge de sa cible (un 2ᵉ joueur le frappe « gratuitement ») ; seulement avec ≥ 2 joueurs sur la carte. | À noter dans les limites. |

## B. Le personnage d'un joueur qui n'est pas l'host

Cause commune : le jeu demande souvent « le joueur » (`EClass.pc`), et chez l'host, quand il rejoue l'action d'un
autre, « le joueur » c'est l'host.

| Retour | Verdict de la lecture | À faire |
|---|---|---|
| Apparence changée au miroir pas gardée | **Encore là.** L'apparence (`pccData`, portrait, couleur des cheveux) n'est jamais envoyée à l'host ; la copie de l'host écrase celle du joueur à chaque retour. (En voyage seul, le point de sauvegarde envoie tout le personnage : là ça tiendrait.) | Nouveau message `CharaAppearanceDelta` envoyé à la fermeture de l'écran d'apparence ; l'host l'applique à sa copie et le relaie. Test : changer la couleur des cheveux côté client par le pont, la lire chez l'host, se reconnecter, la relire. |
| Tenue changée à la coiffeuse | Même cause (la coiffeuse n'a pas de code à elle). | Couvert par le même message, à vérifier. |
| Don « rêve lucide » | **Déjà corrigé** dans la base du fork (le client fait lui-même son rêve). | Test seulement. |
| Don « vie de sorcière » (potions en double), et qualité / talents de fabrication et de cuisine | **Encore là.** La fabrication d'un client est rejouée chez l'host, qui lit ses propres dons et talents (`RecipeCard.cs:302`, `Recipe.cs:404`, `TraitCrafter.cs`). | Pendant le rejeu, faire passer le personnage du client pour « le joueur » (comme `PlayerStandIn` pour les quêtes), autour de `Craft` dans `AIUseCrafterPatch.RunRemote`. Attention à une boucle sans fin dans `OnAddProduct` / `OnHoldProduct`. Test : le client a le don, pas l'host ; fabriquer une potion ; compter. |
| Autres effets du réveil (lecture de grimoire, recettes rêvées) | Supposé absent pour un client. | À vérifier après le reste. |
| Race slime : gènes et dons perdus à la mort | La mort elle-même ne touche pas aux gènes. Mais l'host ne traite jamais le personnage d'un autre comme un slime : un gène mangé sur la carte de l'host n'existe que chez le joueur, et disparaît au prochain retour de la copie de l'host. | Chez l'host, accepter les joueurs distants dans `Card.IsSlimeEvolvable` et `AI_Eat.IsValidTarget`. Test : faire manger un gène au client, le compter des deux côtés, mourir, revenir, se reconnecter, recompter. |
| Objets fabriqués « tous en granit » | **Déjà corrigé** dans la base du fork (les ingrédients choisis sont transmis). | Test seulement. |

## E. Objets posés, messages, carte

| Retour | Verdict de la lecture | À faire |
|---|---|---|
| #9 un invité pose un objet tenu, il tombe au sol (y compris depuis une pile) | **Déjà corrigé** dans la base du fork (les effets d'une pose voyagent avec la pose). Cas restant supposé : si le rejeu chez le client s'arrête tôt (joueur à plus d'une case), l'objet reste au sol → couvert par la ligne suivante. | Test : deux poses à la suite depuis une pile de 2, des deux côtés « installé », pas de « Refusing stale CharaBuildDelta ». |
| L'host pose un objet (panneau) : l'invité le voit au sol et peut le ramasser | **Encore là.** L'état « installé » n'est pas envoyé pendant une pose (`CardSetPlacedStateEvent.cs:19-21`) ; en mode construction de l'host, rien d'autre ne le porte. | Joindre l'état « installé » aux effets de la pose. Test : l'host pose un coffre par le pont, lire `placeState` chez le client. |
| #10 message « vous avez fabriqué » ou « vous ajoutez du combustible » affiché chez l'host | **Déjà corrigé** dans la base du fork (`MsgRelayContext`). Reste supposé : le message et le ticket de « première fabrication » vont à l'host (`AIUseCrafterPatch.cs:316`). | Test du combustible ; déplacer le bonus de première fabrication dans la redirection. |
| Un boss casse un mur : l'invité le voit traverser le mur | **Encore là.** Aucun message ne porte les changements de terrain faits par un monstre (`Chara.DestroyPath`) ; idem pour un pont détruit en combat. | Nouveau message `CharaDestroyPathDelta` envoyé par l'host. Test : l'host fait casser un mur par un personnage, lire la case chez le client. |
| Squelette nommé : objets en plus pas vus par l'invité | Probablement corrigé depuis (commit du 2026-08-13). Risque : si le rejeu chez le client plante, la liste des effets est sautée. | Test ; mettre l'application des effets dans un `finally`. |

## Ordre de travail (corrections sans choix de jeu)

1. Objet posé par l'host vu au sol par l'invité (E).
2. Mur cassé par un monstre (E).
3. Dons et talents de fabrication d'un invité (B).
4. Apparence au miroir (B).
5. Gènes du slime (B).
6. Vitesse d'un joueur surchargé dans le combat au rythme de chacun (A).
7. Après une mort sur la carte de l'host : pouvoir repartir, pas d'objets fantômes (C, les deux défauts).
8. Bonus de première fabrication ; effets dans un `finally` ; ligne d'explication de la case « Turn-Based Combat ».
9. Tests seuls de ce qui est « déjà corrigé » : rêve lucide, matières, pose depuis une pile, message de combustible,
   squelette nommé ; comparaison de l'esquive d'une fée chez l'host et chez l'invité.

## C. La mort — **à décider par l'utilisateur**

Aujourd'hui (lu dans le code) :
- Un joueur meurt sur la carte de l'host : il voit l'écran de mort du jeu, mais le choix « ville / maison » ne fait
  rien ; l'host le relève **là où il est tombé**, à un tiers de sa vie, au milieu des monstres.
- À vérifier en jeu : après ça, il ne pourrait plus quitter la carte seul (`deathZoneMove` resterait vrai) ; l'or
  et les objets lourds perdus à la mort n'existeraient que chez lui (objets fantômes) ; l'host subit la perte
  d'affinité d'« un allié mort ».
- Un joueur meurt en voyage seul : comme dans le jeu normal, puis il part vers l'endroit choisi.
- L'host meurt : comme dans le jeu normal ; les autres restent où ils sont (voyage indépendant coché).

Options :
1. Garder « relevé sur place » mais le rendre sûr (case sûre la plus proche ou entrée de la carte, courte
   protection) et cacher les choix qui ne font rien.
2. Respecter le choix du joueur : relevé, puis voyage seul vers la ville ou la maison.
3. Un état « à terre » jusqu'à ce qu'un allié le relève ou qu'un délai passe, avec une case de l'host pour la
   pénalité (aucune / or / comme le jeu).

Les deux défauts « ne peut plus quitter la carte » et « objets fantômes » se corrigent quelle que soit l'option.

## D. Reconnexion — **à décider par l'utilisateur**

Aujourd'hui : un bouton « Reconnect » dans l'onglet de session, des deux côtés. Si la connexion tombe toute seule,
le joueur est renvoyé à l'écran titre avec un simple message ; l'host garde son personnage et son dernier point de
sauvegarde.

Options : (1) une question « Connexion perdue. Se reconnecter ? » ; (2) quelques essais automatiques, puis la
question ; (3) un bouton permanent « Rejoindre la dernière partie » à l'écran titre.
Il faut dans tous les cas : garder l'adresse de la partie avant de tout effacer, ne pas proposer après une
exclusion ou une version différente, un message « l'host n'est plus là », et une variante pour le banc de test.
Test prévu : l'host coupe le joueur, le joueur accepte, il revient avec le même personnage.
