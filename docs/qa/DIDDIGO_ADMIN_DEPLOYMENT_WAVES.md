# DiddiGo - Vagues de deploiement

Public : administration, direction produit, support, equipe technique.

Objectif : deployer DiddiGo progressivement, sans ouvrir trop largement avant
que le terrain valide les parcours essentiels.

## Vague 1.0 - Test terrain controle

But : verifier que le coeur VTC fonctionne avec de vrais chauffeurs.

Use cases :

- Un passager cherche une destination.
- Un passager obtient un prix.
- Un passager cree une course.
- Un chauffeur proche recoit une offre.
- Le chauffeur accepte ou refuse.
- La course passe par les statuts normaux.
- Le paiement cash est confirme.
- Le solde chauffeur et la commission sont visibles.

Sortie attendue :

- 10 chauffeurs testeurs actifs.
- Matching fiable.
- Pas de faux `no_driver_found` inexpliques.
- KYC chauffeur bloque bien les profils non valides.

## Vague 1.1 - Stabilisation

But : corriger les problemes observes pendant le test terrain.

Use cases :

- Un chauffeur perd la connexion puis revient en ligne.
- Un token expire sans casser le parcours.
- Une erreur DiddiMap est affichee clairement.
- Le support comprend les logs d'une course.
- Un testeur peut refaire un scenario sans intervention technique lourde.

Sortie attendue :

- Bugs critiques corriges.
- Logs lisibles.
- Parcours passager/chauffeur reproductibles.

## Vague 1.2 - Paiements numeriques

But : activer progressivement Wave/DiddiPay.

Use cases :

- Un passager paie une course via Wave ou DiddiPay.
- Le frontend execute le `next_action`.
- DiddiGo confirme le paiement seulement apres retour fiable de DiddiPay.
- Le chauffeur voit son payout.
- L'admin voit paiement, commission et statut.

Sortie attendue :

- Cash toujours disponible.
- Paiement digital teste en staging.
- Aucun montant accepte depuis le frontend.

## Vague 1.3 - Modele commercial chauffeur

But : rendre le solde chauffeur et la commission exploitables.

Use cases :

- Le chauffeur voit son solde.
- Une course cash debite la commission plateforme.
- Une recharge chauffeur credite son solde.
- Le support peut expliquer qui doit quoi.
- Un chauffeur peut etre bloque si son solde est trop bas.

Sortie attendue :

- Wallet comprehensible.
- Ledger exploitable par le support.
- Regles commerciales validees.

## Vague 1.4 - Confort garanti

But : garantir que le niveau paye correspond au service recu.

Use cases :

- Standard peut accepter plusieurs gammes compatibles.
- Confort ne doit pas etre servi par un vehicule trop basique.
- Premium doit etre servi par un vehicule premium.
- Le prix varie selon le confort choisi.

Sortie attendue :

- Le passager choisit seulement Standard, Confort ou Premium.
- Le backend applique les regles de compatibilite.

## Vague 1.5 - Securite course

But : rassurer passager, proches et support.

Use cases :

- Le passager partage un lien de course sans login.
- Le proche voit la position du chauffeur.
- Le passager declenche une urgence.
- Le support retrouve rapidement la course concernee.

Sortie attendue :

- Partage utilisable.
- Urgence journalisee.
- Donnees sensibles protegees.

## Vague 1.6 - GPS et amelioration DiddiMap

But : exploiter les traces reelles de course.

Use cases :

- Le chauffeur envoie ses positions pendant la course.
- DiddiGo stocke les traces liees au ride.
- En fin de course, DiddiGo transmet la trace a DiddiMap.
- DiddiMap analyse et produit des insights.
- Un admin valide ou rejette les insights.

Sortie attendue :

- Base pour prix final reel.
- Base pour ameliorer routes et scoring.

## Vague 2.0 - Pre-production

But : figer une version stable avant ouverture commerciale.

Use cases :

- Test avec plus de chauffeurs.
- Verification des variables prod.
- Verification sauvegardes.
- Verification monitoring.
- Validation support et operations.

Sortie attendue :

- Decision go/no-go.
- Branche `stage` validee.
- Release prete pour `main`.

## Vague 2.1 - Production limitee

But : ouvrir petit, mesurer, corriger vite.

Use cases :

- Une zone pilote est active.
- Chauffeurs selectionnes.
- Support disponible.
- Paiement cash prioritaire au debut.
- Paiement digital active progressivement.

Sortie attendue :

- Exploitation reelle sous controle.
- Donnees terrain pour prioriser la suite.
