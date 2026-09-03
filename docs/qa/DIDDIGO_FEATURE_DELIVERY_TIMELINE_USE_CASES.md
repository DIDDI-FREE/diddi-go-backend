# Timeline de livraison DiddiGo par use cases

Ce document organise les prochaines livraisons DiddiGo en use cases. L'objectif
est de stabiliser le MVP actuel, puis d'ajouter les fonctionnalites restantes
sans melanger les responsabilites des modules.

## Principes

- DiddiGo gere le metier VTC : courses, chauffeurs, matching, prix, statuts,
  disponibilite, securite course, paiement rattache a une course.
- DiddiFreeID gere l'identite commune : login, compte, profil global,
  role global user/admin.
- DiddiFiles gere les fichiers : photos, permis, documents, URLs signees.
- DiddiMap gere la geographie : recherche, route, distance, traces, insights.
- DiddiPay gere les paiements digitaux : intents, callbacks, statut paiement.
- Le frontend ne doit pas deviner les regles metier : il affiche les statuts
  et actions autorisees renvoyes par DiddiGo.

## Version 1.0 - MVP commercial testable

Objectif :
Prouver qu'une course reelle peut etre creee, attribuee, suivie, terminee et
payee, avec commission DiddiGo et solde chauffeur visibles. La version 1 ne
doit pas seulement prouver le transport, elle doit aussi prouver le modele
economique minimum.

Use cases inclus :

- UC-001 Passager cherche un lieu de depart et une destination.
- UC-002 Passager obtient une estimation de prix.
- UC-003 Passager cree une course.
- UC-004 Chauffeur valide passe en ligne.
- UC-005 Chauffeur proche recoit une offre.
- UC-006 Chauffeur accepte une course.
- UC-007 Chauffeur refuse une course et l'offre est reproposee ou cloturee.
- UC-008 Passager suit le chauffeur.
- UC-009 Chauffeur met a jour les statuts de course.
- UC-010 Chauffeur termine la course.
- UC-011 Chauffeur confirme paiement cash.
- UC-012 Passager note la course.
- UC-013 Passager partage un lien de suivi.
- UC-014 Passager ou chauffeur declare une urgence.
- UC-015 DiddiGo calcule la commission plateforme sur chaque course terminee.
- UC-016 DiddiGo calcule le montant net chauffeur.
- UC-017 Chauffeur voit son solde DiddiGo.
- UC-018 Chauffeur recharge son compte via DiddiPay ou Wave quand disponible.
- UC-019 Chauffeur est bloque ou alerte si son solde devient insuffisant selon
  la regle produit.
- UC-020 Passager peut payer cash, DiddiPay ou Wave selon disponibilite.
- UC-021 Admin/support peut voir le statut paiement, commission et payout d'une
  course.

Livrable attendu :

- API stable sur staging;
- suite Bruno MVP utilisable;
- protocole QA humain execute avec 10 chauffeurs;
- erreurs critiques documentees;
- logs lisibles par ride ID, driver ID, user ID et request ID.
- politique commission et solde chauffeur testable;
- cash, DiddiPay et Wave representes dans le contrat meme si tout n'est pas
  encore actif en production.

Critere de sortie :

- aucune erreur 500 non documentee sur le happy path;
- une course cash completee de bout en bout;
- une course DiddiPay ou Wave testable en staging si les dependances sont
  disponibles;
- commission et montant net chauffeur presents dans les donnees de course ou de
  paiement;
- solde chauffeur visible ou au minimum consultable par API;
- matching fonctionnel avec chauffeur proche;
- KYC bloque bien les chauffeurs non valides;
- DiddiMap est le seul fournisseur geo et les erreurs geo sont explicites.

Regle produit a figer avant production :

- taux commission DiddiGo;
- solde minimum chauffeur;
- comportement si solde insuffisant : blocage passage en ligne, alerte simple,
  ou delai de grace;
- ordre de priorite des moyens de paiement : cash, DiddiPay, Wave;
- responsabilite du recouvrement si cash non confirme.

## Version 1.1 - KYC chauffeur robuste

Objectif :
Rendre l'activation chauffeur fiable et controlable par admin.

Use cases inclus :

- UC-101 Chauffeur soumet permis, piece, selfie et documents vehicule.
- UC-102 Chauffeur voit le statut du dossier : draft, pending, approved, rejected.
- UC-103 Admin consulte la file KYC.
- UC-104 Admin approuve un dossier.
- UC-105 Admin rejette un dossier avec raison claire.
- UC-106 Chauffeur corrige et resoumet son dossier.
- UC-107 Chauffeur non approuve ne peut pas passer en ligne.
- UC-108 Chauffeur approuve peut passer en ligne.

Dependances :

- DiddiFiles pour upload et consultation des documents;
- DiddiFreeID pour role global si le pont service-to-service est active;
- DiddiGo garde le statut metier chauffeur local.

Critere de sortie :

- le frontend n'a pas besoin de calculer le statut KYC;
- les URLs de fichiers sont signees et temporaires;
- un admin peut valider un chauffeur de test sans requete SQL manuelle.

## Version 1.2 - Notifications chauffeur/passager

Objectif :
Fiabiliser la communication temps reel et push.

Use cases inclus :

- UC-201 Chauffeur recoit une offre au premier plan via WebSocket.
- UC-202 Chauffeur recoit une offre en arriere-plan Android via FCM.
- UC-203 Passager recoit les changements de statut.
- UC-204 Passager recoit position chauffeur pendant la course.
- UC-205 Chauffeur recoit annulation passager.
- UC-206 Passager recoit no_driver_found.
- UC-207 Device token FCM est enregistre, remplace et supprime proprement.

Dependances :

- FCM cote backend et frontend;
- foreground service Android pour la phase test chauffeur;
- WebSocket pour l'experience active.

Critere de sortie :

- les limites OS sont documentees;
- aucun use case critique ne depend uniquement d'un WebSocket en arriere-plan;
- les notifications importantes ont un payload stable.

## Version 1.3 - Integration DiddiMap avancee

Objectif :
Exploiter DiddiMap sans fallback silencieux.

Use cases inclus :

- UC-301 Passager obtient une recherche de lieux rapide avec bias GPS.
- UC-302 Passager voit des suggestions utiles pendant la saisie.
- UC-303 DiddiGo cree une course uniquement si DiddiMap fournit route/distance.
- UC-304 DiddiGo enregistre les positions GPS chauffeur pendant la course.
- UC-305 DiddiGo envoie la trace finale a DiddiMap quand le contrat REST/WebSocket est pret.
- UC-306 DiddiGo affiche une erreur explicite si DiddiMap est indisponible.
- UC-307 Admin peut retrouver les courses avec probleme geo.

Dependances :

- DiddiMap v1.3 pour search/autocomplete/route;
- futur contrat DiddiMap Core pour traces et insights.

Critere de sortie :

- pas de fallback geographique silencieux;
- logs clairs quand DiddiMap echoue;
- distance/duree utilisees pour pricing clairement identifiables.

## Version 1.4 - Pricing, commission et solde chauffeur

Objectif :
Stabiliser la politique de prix propre a DiddiGo, la commission plateforme, le
montant net chauffeur et le solde chauffeur.

Use cases inclus :

- UC-401 Passager recoit prix estime avant commande.
- UC-402 DiddiGo calcule base_fare.
- UC-403 DiddiGo calcule distance_fare.
- UC-404 DiddiGo calcule duration_fare.
- UC-405 DiddiGo applique surge_multiplier avec surge_cap.
- UC-406 DiddiGo calcule platform_commission.
- UC-407 DiddiGo calcule driver_payout_estimate.
- UC-408 DiddiGo recalcule le payout final selon distance/duree reelles quand disponible.
- UC-409 DiddiGo enregistre la commission definitive apres completion.
- UC-410 DiddiGo alimente un ledger chauffeur lisible et auditable.
- UC-411 Chauffeur consulte son solde.
- UC-412 Chauffeur recharge son solde via DiddiPay.
- UC-413 Chauffeur recharge son solde via Wave si active.
- UC-414 DiddiGo applique la regle solde minimum avant passage en ligne.

Parametres actuels :

```text
surge_cap = 1.6
commission_rate = 0.08
```

Critere de sortie :

- estimation et prix final sont audites;
- le frontend recoit tous les champs contractuels;
- aucun prix ne depend d'une regle cachee cote frontend.
- chaque course terminee cree une ecriture commission/payout;
- le solde chauffeur est coherent apres recharge et apres course;
- le blocage ou l'alerte solde insuffisant est explicite.

## Version 1.5 - Paiements cash, DiddiPay, Wave et recharge

Objectif :
Rendre les paiements et recharges testables dans la version 1 sans casser le
cash. DiddiGo orchestre le paiement rattache a la course et le solde chauffeur;
DiddiPay execute les paiements digitaux.

Use cases inclus :

- UC-501 Passager choisit cash.
- UC-502 Chauffeur confirme cash collecte.
- UC-503 Passager choisit DiddiPay si disponible.
- UC-504 DiddiGo cree un payment intent DiddiPay.
- UC-505 DiddiGo recoit callback DiddiPay.
- UC-506 DiddiGo marque paiement paye/echec/en attente.
- UC-507 Passager choisit Wave quand l'integration est disponible.
- UC-508 Admin voit les paiements ambigus.
- UC-509 Chauffeur initie une recharge de compte.
- UC-510 DiddiGo cree une recharge via DiddiPay.
- UC-511 DiddiGo recoit le callback de recharge.
- UC-512 DiddiGo credite le solde chauffeur apres paiement confirme.
- UC-513 Chauffeur voit l'historique des recharges.
- UC-514 Admin voit les recharges echouees ou ambigues.

Dependances :

- DiddiPay pour paiement digital;
- integration Wave future via DiddiPay ou connecteur dedie.

Critere de sortie :

- cash reste toujours testable;
- DiddiPay n'est jamais un fallback silencieux;
- les erreurs paiement ont des codes DiddiGo explicites.
- une recharge chauffeur peut etre simulee ou executee sur staging;
- le solde chauffeur change seulement apres confirmation paiement;
- le frontend affiche clairement pending, paid, failed, expired.

## Version 1.6 - Securite course et partage

Objectif :
Rendre la course suivable et rassurante.

Use cases inclus :

- UC-601 Passager cree un lien de partage.
- UC-602 Un proche ouvre le lien sans login.
- UC-603 Le proche voit une vue limitee et securisee.
- UC-604 La position affichee suit le chauffeur, pas le passager.
- UC-605 Le lien expire ou devient inutile apres la course selon regle produit.
- UC-606 Passager declenche une urgence.
- UC-607 Chauffeur declenche une urgence.
- UC-608 Admin/support voit l'urgence avec ride ID et contexte.

Critere de sortie :

- aucune donnee sensible inutile sur la page publique;
- suivi assez temps reel sans surcharger l'API;
- WebSocket/SSE ou polling raisonne documente pour la page publique.

## Version 1.7 - Qualite matching et disponibilite

Objectif :
Eviter les faux no_driver_found et mieux controler le dispatch.

Use cases inclus :

- UC-701 Chauffeur online reste eligible tant que sa presence est fraiche.
- UC-702 Chauffeur offline ne recoit plus d'offre.
- UC-703 Matching respecte distance pickup.
- UC-704 Matching respecte la categorie vehicule et la hierarchie `comfort_level`.
- UC-705 Offre expire proprement.
- UC-706 Offre refusee passe au chauffeur suivant.
- UC-707 Course sans chauffeur passe en no_driver_found avec raison observable.
- UC-708 Logs matching expliquent pourquoi chaque chauffeur a ete exclu.

Critere de sortie :

- test 10 chauffeurs reproductible;
- raison de non matching observable;
- pas de course bloquee sans statut final.

## Version 2.0 - Production minimale

Objectif :
Passer d'un MVP testable a un service exploitable.

Use cases inclus :

- UC-801 Admin voit activite courses/chauffeurs.
- UC-802 Admin peut rechercher une course par ride ID.
- UC-803 Admin peut rechercher un chauffeur par phone/user ID/driver ID.
- UC-804 Support peut diagnostiquer auth, KYC, matching, paiement.
- UC-805 Logs et metriques permettent d'estimer requetes/heure et erreurs.
- UC-806 Procedures de rollback/deploiement sont connues.
- UC-807 Secrets/env de staging et production sont separes.

Critere de sortie :

- staging stable;
- main/prod protegee;
- stage/dev workflow clair;
- Portainer env documente;
- erreurs cataloguees;
- tests Bruno et QA humains utilises a chaque livraison.

## Version 2.1 - Fonctionnalites conducteur avancees

Objectif :
Ameliorer l'experience chauffeur apres stabilisation MVP.

Use cases possibles :

- UC-901 Chauffeur voit historique gains detaille.
- UC-902 Chauffeur voit projections et statistiques de commission.
- UC-903 Chauffeur voit zones de forte demande.
- UC-904 Chauffeur definit zone preferee.
- UC-905 Chauffeur definit destination de retour.
- UC-906 Chauffeur recoit alertes qualite ou penalites.

Critere de sortie :

- ne pas demarrer avant solde/recharge/paiement version 1 stable;
- ne pas melanger avec DiddiSend.

## Version 3.0 - Preparation DiddiSend

Objectif :
Preparer l'interaction future sans fusionner les metiers.

Position recommandeee :

- DiddiSend doit etre un service separe;
- DiddiGo peut partager certains concepts : chauffeur, vehicule, tracking,
  paiement, notification;
- DiddiGo ne doit pas devenir le backend colis;
- les modules communiquent via contrats API/evenements.

Use cases de preparation :

- UC-1001 Un chauffeur DiddiGo peut devenir livreur DiddiSend si valide.
- UC-1002 Les documents communs restent dans DiddiFiles.
- UC-1003 L'identite reste dans DiddiFreeID.
- UC-1004 Les paiements restent dans DiddiPay.
- UC-1005 Les routes restent dans DiddiMap.

Critere de sortie :

- aucun code DiddiSend dur dans le coeur ride;
- seulement des hooks d'integration si necessaire;
- contrat API DiddiSend separe.

## Ordre recommande

```text
1.0 MVP commercial testable
1.1 KYC chauffeur robuste
1.2 Notifications
1.3 DiddiMap avance
1.4 Pricing, commission et solde chauffeur
1.5 Paiements cash, DiddiPay, Wave et recharge
1.6 Securite/partage
1.7 Matching qualite
2.0 Production minimale
2.1 Experience chauffeur avancee
3.0 Preparation DiddiSend
```

## Regle de decision

Une fonctionnalite ne sort pas si son use case principal n'a pas :

- un endpoint ou un comportement backend clair;
- un statut frontend clair;
- une erreur documentee;
- un test Bruno si c'est automatisable;
- un scenario QA humain si l'experience utilisateur compte.
