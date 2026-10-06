# Conseil 9 : verdict

## Où le conseil est d'accord
- D'abord le retour automatique (E) et la fin de l'écran « Who do you want to play? » (A1).
- Ensuite la reprise automatique par un invité (A). Tout le monde recule ensemble : jamais d'objet en double.
- B (doublons), C (trop gros) et D (port à ouvrir) sont écartés.
- Qui reprend : le plus petit identifiant Steam présent.
- L'ancien host revient en invité. Sa partie isolée est gardée de côté.

## Où le conseil s'oppose
- Copie du monde chez les invités (A') avant ou après le dépôt. Je tranche : avant. GitHub demande une clé, donc une démarche.
- Reprise allumée ou éteinte par défaut. Je tranche : allumée. Éteinte, c'est « l'host doit d'abord cocher ».
- Verrou supprimé ou raccourci. Je tranche : 45 secondes, jamais zéro.

## Les angles morts trouvés à la relecture
- Un host qui a seulement perdu Internet joue encore : deux hosts.
- L'host planté qui clique « Continue » sur sa vieille sauvegarde.
- La sauvegarde régulière n'a jamais été chronométrée.
- Au banc, les deux fenêtres ont le même compte Steam : il faut de fausses identités.
- Copie coupée en plein envoi ; versions du mod différentes.

## La recommandation
**(i)** E, puis A', puis A. Tout est allumé par défaut ; la case de l'host ne sert qu'à éteindre.

1. **Retour automatique, A1, message B15.** Tu vois « reconnexion… » au lieu du titre. Coupure de 20 s : retour en 25 à 40 s, 0 minute perdue (60 s si tu voyageais seul). Host mort : 3 minutes d'attente, puis le titre avec une phrase claire. Perte comme aujourd'hui.
2. **Sauvegarde de l'host toutes les 2 minutes si un invité est là, plus « Start Server » automatique.** Plantage : 2 minutes perdues au pire, pour tous. Cette sauvegarde tourne dans le jeu : elle peut le figer. On la chronomètre d'abord. Plus d'une demi-seconde : 5 minutes.
3. **A' : l'host envoie son monde à chaque invité après chaque sauvegarde.** Tu ne vois rien. Envoi en arrière-plan, copie vérifiée, la précédente gardée, hors de tes sauvegardes.
4. **Reprise automatique.** Départ propre : « X est parti, tu reprends », 30 à 90 s, 0 minute perdue. Plantage : 25 s figé, 60 s d'attente, 30 à 90 s de chargement ; 2 minutes perdues pour tous.
5. **Dépôt, en bonus** : verrou de 45 s, rendu à la fermeture.

**(ii)** Étapes 1 et 4. L'host d'avant rejoint en invité en 30 à 90 s et perd ce qu'il a joué seul.

**Deux hosts.** Chaque reprise augmente un numéro écrit dans le monde. Le plus grand gagne. L'host coupé lit aussitôt : « hors ligne, ce que tu joues ne sera pas gardé ». Il perd la durée de sa coupure, lui seul. Rien n'est effacé.

**« Continue ».** Au chargement, le mod cherche le même monde, numéro plus grand, chez un ami. Trouvé : il rejoint en invité, sans question. Sinon il joue ; à la rencontre, le plus grand numéro gagne.

**GitHub.** Seul, il porte la perte à 7 minutes. A' ne passe pas par lui : 2 minutes.

**(iii)** Le plus petit identifiant. S'il n'a pas ouvert en 2 minutes, le suivant. Les autres réessaient toutes les 5 s.

**(iv)** Sans dépôt : A' suffit. Le mot « dépôt » ne s'affiche jamais.

**(v)** A1, B15 : étape 1. B8, B14 : étape 2. B2, B3 : étape 4.

## Ce qui ne peut être prouvé qu'à deux PC
**(vi)** Le délai de mort d'un lien Steam, la survie du salon, retrouver l'ami sans invitation, le relais vers un nouvel host, les temps de chargement, GitHub avec une vraie clé. L'étape 4 peut donc échouer chez toi : tu retombes au titre, comme aujourd'hui, sans perdre plus. Les notes diront « non testé à deux PC ». Une soirée avec ton ami tranche.

## La première chose à faire
Donner au banc le moyen de couper un invité 20 secondes, puis écrire le test rouge : il revient seul, à sa place, sans écran.

## Pour l'ingénieur
1. Crochets : délai 15 s en Debug (`ElinNetClient.cs:57`), commande « couper le lien », identité Steam injectable, faux salon (fichier : port, monde, numéro de reprise).
2. A1 : `ElinNetHostPlayerManager.cs:81-104`. Rouge : l'écran s'ouvre.
3. E : `NetSession.cs:160-183`, `SteamNetLobbyManager.cs:115`. Rouge : titre après coupure ; un seul personnage chez l'host.
4. B15 : `GameSaveLoad.cs:12-20`.
5. Chronométrer `Game.Save` sur le vrai monde.
6. Périodique + B8 : modèle `EmpServer.cs:111`, `TabLobbyBrowser.cs:48`. Rouge : host tué par PID, sauvegarde trop vieille.
7. A' : morceaux, taille et somme, hors `Save/`. Rouge : envoi coupé, ancienne copie lisible.
8. Numéro de reprise dans `context_vars`. Rouge : A relancé redevient host.
9. A : `SaveDepot.cs:164`, `ElinNetHost.cs:22`. Rouge (`depot_suite.py`) : A tué, B au titre.
10. Verrou : `SaveDepot.cs:37,107`, `GitHubDepot.cs:28,276`. Champs ajoutés seulement, fausse horloge.
11. Trois fenêtres : demander l'accord.
