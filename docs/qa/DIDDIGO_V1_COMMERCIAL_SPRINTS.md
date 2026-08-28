# Sprints V1 commerciale - Commission, solde et paiements

Ce document decompose la V1 commerciale DiddiGo en sprints executables. Le
but n'est pas seulement de faire rouler une course, mais de valider le modele
economique minimum : prix variable, commission, montant net chauffeur, solde
chauffeur, recharge et paiements.

## Principe metier

DiddiGo reste responsable de la politique VTC :

- prix de course;
- categorie vehicule;
- niveau de confort;
- commission plateforme;
- montant net chauffeur;
- regles de solde chauffeur;
- rattachement paiement/course;
- visibilite admin/support.

DiddiPay ou Wave executent le paiement. Ils ne decident pas la politique VTC.

DiddiMap fournit distance et duree. Il ne decide pas le prix final DiddiGo.

## Variation des prix

Le prix doit varier selon :

- distance DiddiMap;
- duree DiddiMap;
- categorie vehicule;
- comfort_level;
- profil de course;
- surge_multiplier;
- moyen de paiement si une regle produit le justifie.

Variables a formaliser :

```text
base_fare
distance_fare
duration_fare
surge_multiplier
surge_cap
commission_rate
platform_commission
driver_payout_estimate
driver_payout_final
payment_method
vehicle_category
comfort_level
ride_profile
```

Exemples de profils de course :

- immediate;
- scheduled;
- airport;
- night;
- high_demand;
- test;

Decision produit pour V1 :
Si un profil n'est pas encore implemente, DiddiGo doit retourner `standard` ou
`immediate`, mais ne doit pas inventer une variation cachee.

## Sprint 1 - Pricing contractuel complet

Objectif :
Le passager voit une estimation fiable avant commande, et DiddiGo expose tous
les champs utiles pour commission et payout.

Use cases :

- UC-V1-001 Passager demande un prix pour une course standard.
- UC-V1-002 Passager demande un prix avec comfort_level different.
- UC-V1-003 Passager demande un prix avec categorie vehicule differente.
- UC-V1-004 DiddiGo refuse un comfort_level invalide.
- UC-V1-005 DiddiGo refuse une categorie vehicule invalide.
- UC-V1-006 Admin/support peut comprendre comment le prix a ete calcule.

Backend :

- verifier les valeurs supportees de `vehicle_category`;
- verifier les valeurs supportees de `comfort_level`;
- ajouter ou confirmer `ride_profile`;
- retourner le breakdown complet dans `/rides/pricing/estimate`;
- stocker le breakdown au moment de `POST /rides`;
- garantir que DiddiMap est obligatoire pour distance/duree.

Frontend :

- afficher estimation totale;
- afficher moyen de paiement choisi;
- afficher categorie/confort choisi;
- ne pas recalculer le prix;
- afficher une erreur claire si DiddiMap ou pricing echoue.

Tests :

- Bruno pricing standard;
- Bruno pricing comfort different;
- Bruno pricing categorie differente;
- Bruno invalid comfort;
- Bruno invalid category;
- QA humaine : comparer plusieurs options et verifier que le prix varie.

Critere de sortie :

- les prix changent si categorie/confort changent;
- tous les champs contractuels sont presents;
- aucune regle de prix n'est cachee cote frontend;
- aucun fallback silencieux si DiddiMap echoue.

## Sprint 2 - Commission et payout par course

Objectif :
Chaque course terminee produit une commission plateforme et un montant net
chauffeur.

Use cases :

- UC-V1-101 Course terminee cash cree une commission.
- UC-V1-102 Course terminee DiddiPay cree une commission.
- UC-V1-103 Course terminee Wave cree une commission.
- UC-V1-104 Chauffeur voit son montant net estime avant acceptation.
- UC-V1-105 Chauffeur voit son montant net final apres completion.
- UC-V1-106 Admin/support voit fare, commission et payout.

Backend :

- distinguer `driver_payout_estimate` et `driver_payout_final`;
- figer `platform_commission` definitive a la fin de course;
- garder `commission_rate` dans la course pour audit;
- ajouter les champs admin/support si absents;
- documenter quand le prix final reste egal a l'estimation;
- ne pas copier silencieusement l'estimation dans les champs reels si DiddiMap
  trace n'est pas disponible.

Frontend :

- afficher estimation chauffeur dans l'offre si disponible;
- afficher montant final apres course;
- afficher commission ou frais plateforme uniquement sur les ecrans pertinents;
- ne pas inventer le payout si le backend ne le renvoie pas.

Tests :

- Bruno ride complete cash;
- Bruno payment get apres completion;
- Bruno admin/support detail payment;
- QA chauffeur : verifier montant vu dans l'offre et montant final.

Critere de sortie :

- une course completee garde une trace commission/payout;
- admin/support peut auditer une course;
- le chauffeur voit un montant comprehensible.

## Sprint 3 - Ledger et solde chauffeur

Objectif :
Creer la source de verite du solde chauffeur dans DiddiGo.

Use cases :

- UC-V1-201 Chauffeur consulte son solde.
- UC-V1-202 Une course terminee ajoute une ecriture de payout/commission.
- UC-V1-203 Une recharge confirmee ajoute une ecriture positive.
- UC-V1-204 Une erreur paiement ne modifie pas le solde.
- UC-V1-205 Admin/support voit l'historique ledger d'un chauffeur.
- UC-V1-206 Le solde est recalculable depuis les ecritures.

Backend :

- ajouter table `driver_wallets` ou equivalent;
- ajouter table `driver_ledger_entries` ou equivalent;
- types d'ecriture minimum : `ride_payout`, `platform_commission`,
  `topup_pending`, `topup_confirmed`, `topup_failed`, `adjustment`;
- chaque ecriture doit avoir `driver_id`, `amount`, `currency`, `direction`,
  `reference_type`, `reference_id`, `status`, `created_at`;
- exposer `GET /v1/drivers/me/wallet`;
- exposer `GET /v1/drivers/me/wallet/ledger`;
- exposer endpoint admin/support de consultation.

Frontend :

- afficher solde chauffeur;
- afficher historique simple;
- afficher pending/confirmed/failed;
- ne pas permettre une recharge double sans confirmation utilisateur.

Tests :

- Bruno get wallet chauffeur;
- Bruno get ledger chauffeur;
- test idempotence sur meme reference;
- test admin/support ledger;
- QA chauffeur : solde visible et comprehensible.

Critere de sortie :

- le solde n'est pas un champ magique modifie directement;
- chaque mouvement a une ecriture;
- le solde est coherent apres course et recharge.

## Sprint 4 - Recharge chauffeur via DiddiPay/Wave

Objectif :
Permettre au chauffeur de recharger son compte depuis DiddiGo.

Use cases :

- UC-V1-301 Chauffeur choisit montant de recharge.
- UC-V1-302 Chauffeur choisit DiddiPay.
- UC-V1-303 Chauffeur choisit Wave si disponible.
- UC-V1-304 DiddiGo cree une intention de recharge.
- UC-V1-305 DiddiPay confirme la recharge par callback.
- UC-V1-306 DiddiGo credite le solde apres confirmation.
- UC-V1-307 DiddiGo ne credite pas si paiement failed/expired.
- UC-V1-308 Chauffeur voit recharge pending puis confirmee.

Backend :

- ajouter endpoint `POST /v1/drivers/me/wallet/topups`;
- ajouter endpoint `GET /v1/drivers/me/wallet/topups/{id}`;
- rattacher chaque recharge a un payment intent DiddiPay;
- supporter `method=diddipay` et `method=wave`;
- rendre les callbacks idempotents;
- separer recharge chauffeur et paiement course passager.

Frontend :

- ecran recharge;
- choix montant;
- choix moyen paiement;
- affichage next_action DiddiPay/Wave;
- statut pending/paid/failed/expired.

Tests :

- Bruno prepare topup DiddiPay;
- Bruno prepare topup Wave;
- Bruno callback topup success;
- Bruno callback topup failed;
- Bruno idempotence callback;
- QA chauffeur : recharge visible dans solde.

Critere de sortie :

- aucune recharge n'est creditee avant confirmation;
- callback rejoue deux fois ne double pas le solde;
- erreur DiddiPay/Wave est explicite.

## Sprint 5 - Paiement passager cash, DiddiPay, Wave

Objectif :
Permettre au passager de payer une course avec cash, DiddiPay ou Wave selon
disponibilite.

Use cases :

- UC-V1-401 Passager choisit cash avant commande.
- UC-V1-402 Chauffeur confirme cash collecte.
- UC-V1-403 Passager choisit DiddiPay.
- UC-V1-404 Passager choisit Wave.
- UC-V1-405 DiddiGo prepare le paiement apres creation ou completion selon
  regle produit.
- UC-V1-406 DiddiGo recoit callback paiement course.
- UC-V1-407 DiddiGo marque paiement paid.
- UC-V1-408 DiddiGo marque paiement failed/expired.
- UC-V1-409 Admin/support voit les paiements ambigus.

Backend :

- confirmer le timing : paiement avant dispatch, apres acceptation, ou apres
  completion;
- maintenir cash fonctionnel;
- utiliser DiddiPay pour `diddipay` et `wave` si c'est le connecteur retenu;
- refuser les changements de moyen de paiement non autorises;
- exposer statut paiement clair dans `GET /v1/payments/{ride_id}`;
- rattacher payment transaction a la ride;
- creer commission/payout seulement quand le paiement est regle selon le mode.

Frontend :

- selection moyen paiement avant commande;
- afficher cash/DiddiPay/Wave selon capabilities backend;
- ouvrir next_action paiement;
- afficher pending/paid/failed;
- ne pas terminer l'experience sans statut paiement clair.

Tests :

- Bruno cash happy path;
- Bruno DiddiPay prepare payment;
- Bruno Wave prepare payment;
- Bruno webhook success;
- Bruno webhook failed;
- QA passager/chauffeur : verifier messages et statuts.

Critere de sortie :

- cash reste stable;
- paiement digital testable en staging;
- pas de statut paiement ambigu pour le frontend.

## Sprint 6 - Regle de solde minimum chauffeur

Objectif :
Decider et appliquer la regle commerciale du compte chauffeur.

Use cases :

- UC-V1-501 Chauffeur avec solde suffisant passe en ligne.
- UC-V1-502 Chauffeur avec solde insuffisant est bloque ou alerte.
- UC-V1-503 Chauffeur recharge puis peut passer en ligne.
- UC-V1-504 Admin/support comprend pourquoi un chauffeur est bloque.
- UC-V1-505 Le blocage n'affecte pas un chauffeur deja en course sauf regle
  explicite.

Backend :

- ajouter configuration `driver_min_balance`;
- appliquer la regle dans `POST /v1/drivers/online` si blocage retenu;
- retourner erreur explicite `DRIVER_BALANCE_TOO_LOW`;
- inclure solde actuel et solde minimum dans les details;
- logguer driver_id, balance, min_balance et decision.

Frontend :

- afficher message clair avant passage en ligne;
- proposer bouton recharge;
- ne pas afficher une erreur technique brute.

Tests :

- Bruno online avec solde insuffisant;
- Bruno topup puis online;
- Bruno admin/support diagnostic;
- QA chauffeur : comprendre quoi faire sans appeler support.

Critere de sortie :

- la regle est visible;
- le chauffeur comprend pourquoi il est bloque;
- recharge resout le blocage.

## Sprint 7 - Admin/support commercial

Objectif :
Permettre a l'equipe support de diagnostiquer les paiements, commissions,
payouts et soldes sans acceder a la base.

Use cases :

- UC-V1-601 Admin recherche une course par ride ID.
- UC-V1-602 Admin voit prix, commission, payout et paiement.
- UC-V1-603 Admin recherche un chauffeur.
- UC-V1-604 Admin voit solde et ledger chauffeur.
- UC-V1-605 Admin voit recharges pending/failed.
- UC-V1-606 Admin voit erreurs DiddiPay/Wave.

Backend :

- endpoints admin/support en lecture;
- filtres par ride_id, driver_id, user_id, status, dates;
- reponse orientee diagnostic;
- logs avec request_id et references paiement.

Frontend/admin :

- meme sans UI complete, fournir un mode test Bruno ou backoffice minimal;
- ne pas forcer support a utiliser SQL.

Tests :

- Bruno admin ride financial detail;
- Bruno admin driver wallet detail;
- Bruno admin failed payments list;
- QA support : diagnostiquer une course test en moins de 2 minutes.

Critere de sortie :

- support peut repondre "qui doit quoi a qui";
- aucune verification critique ne depend d'un acces direct Postgres.

## Sprint 8 - Stabilisation et contrat API V3/V4

Objectif :
Figer les comportements commerciaux pour frontend, backend et QA.

Use cases :

- UC-V1-701 Frontend connait les moyens de paiement disponibles.
- UC-V1-702 Frontend connait les champs pricing obligatoires.
- UC-V1-703 Frontend connait les erreurs possibles.
- UC-V1-704 QA peut tester chaque use case avec Bruno.
- UC-V1-705 Support peut retrouver chaque transaction.

Backend :

- mettre a jour contrat API;
- mettre a jour catalogue erreurs;
- ajouter tests Bruno;
- documenter variables Portainer;
- verifier migration DB propre;
- verifier compatibilite staging.

Frontend :

- mettre a jour briefing frontend;
- utiliser uniquement les champs contractuels;
- ne pas coder de regle prix locale.

Tests :

- run Bruno complet;
- test humain 10 chauffeurs;
- test paiement/recharge;
- test regression cash;
- test admin/support.

Critere de sortie :

- documentation et code racontent la meme histoire;
- chaque paiement a un statut final ou une raison pending;
- chaque course terminee est auditable financierement.

## Ordre recommande des sprints

```text
Sprint 1  Pricing contractuel complet
Sprint 2  Commission et payout par course
Sprint 3  Ledger et solde chauffeur
Sprint 4  Recharge chauffeur via DiddiPay/Wave
Sprint 5  Paiement passager cash, DiddiPay, Wave
Sprint 6  Regle de solde minimum chauffeur
Sprint 7  Admin/support commercial
Sprint 8  Stabilisation et contrat API
```

## Decisions produit restantes

Ces decisions ne bloquent pas l'ecriture technique, mais doivent etre figees
avant production :

- taux commission officiel;
- solde minimum chauffeur;
- blocage strict ou simple alerte si solde bas;
- timing du paiement digital passager;
- Wave via DiddiPay ou integration separee;
- liste finale des comfort_level;
- liste finale des profils de course;
- regle d'ajustement si prix final different de l'estimation;
- visibilite exacte de la commission cote chauffeur.

## Definition of Done V1 commerciale

La V1 commerciale est terminee seulement si :

- le prix varie selon categorie/confort/profil;
- chaque course terminee a fare, commission et payout;
- le chauffeur voit son solde;
- le chauffeur peut recharger;
- cash fonctionne;
- DiddiPay/Wave sont testables ou explicitement desactives par configuration;
- admin/support peut auditer une course et un chauffeur;
- Bruno couvre les use cases critiques;
- QA humaine valide au moins un cycle complet chauffeur/passager.
