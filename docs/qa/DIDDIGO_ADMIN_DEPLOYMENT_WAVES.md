# DiddiGo - Rapport administratif de livraison

Public : administration, direction produit, operations, support, QA, equipe
technique.

Date de mise a jour : 2026-08-29.

Objectif : clarifier ce qui existe deja dans DiddiGo, ce qu'il faut tester pour
livrer rapidement une V1 propre, puis ce qui doit etre ajoute dans la V2.

## Position produit

DiddiGo est deja tres avance. La prochaine etape ne doit pas etre presentee
comme "plusieurs semaines pour tester les notifications, l'urgence, le KYC ou
le wallet", car ces briques existent deja cote backend.

La bonne lecture est :

- version actuelle : `0.9`, backend MVP fonctionnel mais encore a stabiliser en
  conditions terrain;
- version `1.0` : version terrain propre, livrable rapidement a la direction et
  aux testeurs;
- version `2.0` : version produit plus complete, avec les fonctions restantes
  qui demandent du vrai developpement;
- production limitee : apres validation terrain, pas avant.

## Ce qui existe deja cote DiddiGo

Use cases deja couverts par le backend :

- passager authentifie via DiddiFreeID;
- shadow user local DiddiGo;
- creation profil chauffeur;
- references documents KYC via `file_id`;
- validation ou rejet KYC par admin;
- blocage chauffeur non valide sur passage en ligne;
- creation vehicule;
- categorie vehicule;
- niveau de confort;
- recherche de lieux via DiddiMap;
- estimation de prix via distance/duree DiddiMap;
- politique de prix DiddiGo;
- commission plateforme;
- payout chauffeur estime;
- creation course;
- matching chauffeur proche;
- acceptation/refus course;
- statuts de course;
- annulation;
- notation;
- WebSocket chauffeur/passager;
- FCM device register/unregister;
- notification d'offre chauffeur via FCM quand configure;
- bouton urgence journalise;
- lien de partage public sans login;
- samples GPS chauffeur pendant la course;
- paiement cash;
- paiement `diddipay` et `wave` via DiddiPay;
- wallet chauffeur;
- recharge chauffeur;
- ledger chauffeur;
- reconciliation admin paiement/recharge;
- catalogue d'erreurs;
- tests automatises backend;
- suite Bruno pour tests API.

Conclusion : la V1 ne doit pas etre un gros chantier fonctionnel. La V1 est un
chantier de stabilisation, validation terrain et correction des vrais bugs.

## Version 1.0 - Stabilisation terrain rapide

Objectif : livrer une version propre et testable en conditions reelles.

Duree cible : 5 a 7 jours ouvrables.

Use cases a tester bout en bout :

- un passager se connecte;
- un chauffeur se connecte;
- le chauffeur cree son profil et son vehicule;
- un admin valide le KYC chauffeur;
- le chauffeur passe en ligne;
- le passager cherche une destination;
- le passager obtient un prix;
- le passager cree une course;
- le chauffeur recoit l'offre;
- le chauffeur accepte;
- le passager suit le chauffeur;
- le chauffeur met a jour les statuts;
- le passager partage la course;
- une personne externe ouvre le lien de partage;
- le bouton urgence cree un signal visible/loggue;
- la course est terminee;
- le paiement cash est confirme;
- une recharge chauffeur est testee;
- le support retrouve la course, le paiement, la commission et le wallet.

Tests a faire dans la semaine :

- tests Bruno sur routes critiques;
- test WebSocket reel avec chauffeur/passager;
- test FCM sur au moins un telephone Android reel;
- test KYC admin avant/apres validation;
- test DiddiMap indisponible ou erreur explicite;
- test DiddiPay/Wave si environnement DiddiPay disponible;
- test partage public;
- test urgence;
- test solde minimum si la valeur est activee;
- test 10 chauffeurs et plusieurs passagers.

Critere de sortie V1 :

- le happy path fonctionne sans intervention technique;
- pas de 500 non documente sur les parcours critiques;
- les erreurs sont compréhensibles cote frontend;
- les logs permettent de retrouver `request_id`, `ride_id`, `driver_id`,
  `user_id`;
- KYC bloque bien les chauffeurs non valides;
- matching fonctionne dans un cas simple et reproductible;
- cash fonctionne;
- DiddiPay/Wave sont soit testables, soit explicitement marques non actifs;
- la direction peut voir une demo fiable.

Livrable V1 :

- backend DiddiGo staging stable;
- protocole de test terrain rempli;
- rapport des bugs trouves/corriges;
- liste claire des limites restantes;
- decision go/no-go pour production limitee.

## Ce qui doit etre ajoute apres V1

Ces elements ne sont pas de simples tests. Ce sont les vrais chantiers V2.

### 1. Matching confort garanti

Probleme :

- aujourd'hui le confort influence le prix, mais n'est pas encore un filtre dur
  suffisant de matching.

Objectif V2 :

- si un passager paie `premium`, il ne doit pas recevoir un vehicule `standard`;
- definir une matrice claire entre categorie vehicule, comfort_level et offre
  eligible;
- exposer la raison si aucun chauffeur compatible n'est trouve.

Duree estimee : 3 a 5 jours.

### 2. Prix final reel

Probleme :

- DiddiGo stocke deja des samples GPS, mais ne recalcule pas encore le prix
  final avec la distance/duree reellement parcourue.

Objectif V2 :

- envoyer la trace finale a DiddiMap;
- recevoir distance/duree reelles;
- comparer estimation vs reel;
- calculer `driver_payout_final`;
- figer commission finale;
- documenter les regles d'ajustement.

Duree estimee : 1 a 2 semaines, depend du contrat DiddiMap traces.

### 3. Admin/support complet

Probleme :

- des routes admin existent, mais l'exploitation support doit devenir plus
  confortable.

Objectif V2 :

- recherche course par telephone, user_id, driver_id, ride_id;
- dashboard courses en cours;
- vue incidents;
- vue paiements ambigus;
- actions admin tracees;
- export support/finance.

Duree estimee : 1 a 2 semaines cote backend, hors UI complete.

### 4. Paiement production et regles commerciales

Probleme :

- les paiements et recharges existent, mais la politique produit doit etre
  verrouillee avant production large.

Objectif V2 :

- regle officielle solde minimum;
- comportement si solde insuffisant;
- delai de grace ou blocage strict;
- reconciliation planifiee surveillee;
- procedure support paiement `requires_action`;
- rapports commission/payout.

Duree estimee : 1 semaine si DiddiPay est stable.

### 5. Notifications production

Probleme :

- FCM est prevu, mais la fiabilite doit etre prouvee sur vrais appareils.

Objectif V2 :

- templates notifications;
- payload stable versionne;
- retry/logs par notification;
- notification passager plus complete;
- strategie Android/iOS documentee;
- tableau des notifications critiques.

Duree estimee : 3 a 7 jours.

### 6. Partage course temps reel

Probleme :

- le lien public existe, mais l'experience publique doit etre finalisee.

Objectif V2 :

- page publique officielle;
- flux temps reel WebSocket ou SSE;
- limite des donnees visibles;
- expiration/revocation claire;
- affichage position chauffeur;
- aucun besoin de login.

Duree estimee : 3 a 7 jours, depend surtout du frontend.

### 7. Urgence et securite operationnelle

Probleme :

- le signal urgence existe, mais ce n'est pas encore un vrai workflow support.

Objectif V2 :

- statut urgence;
- assignation support;
- historique actions;
- contacts d'urgence;
- event/log prioritaire;
- procedure interne d'intervention.

Duree estimee : 1 semaine.

### 8. Messagerie et appels

Probleme :

- non implemente dans DiddiGo actuellement.

Objectif V2 :

- chat passager/chauffeur pendant la course;
- masquage numerique ou appel relaye;
- historique limite;
- moderation/support si incident.

Decision architecture :

- peut etre dans DiddiGo pour le contexte course uniquement;
- ou dans un futur service commun DiddiCom si tous les modules en ont besoin.

Duree estimee : 2 a 3 semaines selon choix technique.

### 9. Qualite dispatch 10+ chauffeurs

Probleme :

- le matching simple doit etre observe en charge terrain.

Objectif V2 :

- raison detaillee d'exclusion chauffeur;
- anti-double-assign;
- timeout offre;
- reproposition apres refus;
- presence chauffeur plus robuste;
- metriques matching.

Duree estimee : 1 a 2 semaines selon bugs observes en V1.

## Timeline recommandee

```text
Semaine 1
V1.0 stabilisation terrain DiddiGo
Tests reels 10 chauffeurs + passagers
Correction bugs bloquants
Demo direction

Semaines 2-3
V2.0 lot A : matching confort garanti + notifications production + partage
public finalise

Semaines 4-5
V2.0 lot B : prix final reel + traces DiddiMap + commission finale

Semaines 6-7
V2.0 lot C : admin/support complet + urgence operationnelle + paiement
production

Semaines 8-10
V2.1 : messagerie/appels + qualite dispatch avancee + durcissement production
```

## Projection administrative

Version `1.0` :

- objectif : montrer vite un produit utilisable;
- delai : 1 semaine;
- risque principal : bugs terrain, configuration DiddiMap/DiddiPay/FCM;
- resultat attendu : demo fiable + test controle.

Version `2.0` :

- objectif : produit commercial plus solide;
- delai : 4 a 7 semaines apres V1 selon dependances;
- risque principal : DiddiMap traces, DiddiPay production, frontend temps reel,
  workflow support;
- resultat attendu : production limitee serieuse.

Version `2.1` :

- objectif : experience avancee;
- delai : 8 a 10 semaines apres V1 si messagerie/appels inclus;
- resultat attendu : meilleure qualite operationnelle et confort utilisateur.

## Message simple pour la direction

DiddiGo n'est plus au stade conceptuel. Le backend couvre deja les parcours
essentiels : chauffeur, passager, KYC, course, matching, paiement, wallet,
notifications, partage et urgence.

La prochaine etape est une V1 terrain rapide sur une semaine : tester en vrai,
corriger les bugs bloquants, documenter les limites et faire une demonstration
fiable.

La V2 ajoutera les fonctions produit plus lourdes : confort garanti dans le
matching, prix final reel via traces DiddiMap, support/admin plus complet,
notifications production, partage temps reel finalise, urgence operationnelle,
messagerie et appels.
