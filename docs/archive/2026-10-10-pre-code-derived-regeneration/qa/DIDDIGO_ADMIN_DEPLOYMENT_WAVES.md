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

- le confort influence le prix et devient un filtre hierarchique de matching.

Objectif V2 :

- si un passager paie `premium`, il ne doit pas recevoir un vehicule `standard`;
- definir une matrice claire entre categorie vehicule, comfort_level et offre
  eligible;
- exposer la raison si aucun chauffeur compatible n'est trouve.

Duree estimee : 3 a 5 jours.

### 2. Prix final reel

Probleme :

- DiddiGo recalcule un prix theorique depuis la trace reelle, mais le prix
  facture client reste le prix accepte au depart.

Objectif V2 :

- envoyer la trace finale a DiddiMap;
- recevoir distance/duree reelles;
- comparer estimation vs reel via `actual_pricing_fare` et `pricing_delta`;
- garder `final_fare` verrouille sur le prix accepte;
- figer commission et payout sur le prix facture;
- alimenter les futures regles de dynamic pricing.

Duree estimee : 1 a 2 semaines. Le contrat REST DiddiMap traces existe; le
travail restant est l'adapter DiddiGo, le stockage des references trace et la
regle produit de recalcul.

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

## Timeline acceleree recommandee

Objectif business : arriver a une production limitee prudente en 3 semaines,
puis viser une beta ouverte plus large au bout d'environ 1 mois.

Principe : on ne developpe pas tout puis on teste a la fin. Chaque semaine
contient du dev, une mise en staging, des tests terrain et une decision de
promotion vers production limitee si les criteres sont bons.

```text
Semaine 1
V1.0 stabilisation terrain
Dev     : corrections bugs bloquants, logs, Portainer, DiddiPay/FCM/DiddiMap
Staging : deploiement continu des correctifs
Tests   : Bruno + 10 chauffeurs + passagers + KYC + cash + partage + urgence
Prod    : pas encore ouverte, seulement preparation env prod
Sortie  : demo direction + go/no-go pour production limitee interne

Semaine 2
V2.0 fonctions critiques
Dev     : confort garanti, notifications production, partage public finalise,
          debut prix final reel avec traces DiddiMap REST
Staging : tests quotidiens des nouveaux flux
Tests   : matching Standard/Comfort/Premium, FCM reel, lien public, urgence,
          paiements/recharges, traces GPS
Prod    : production limitee tres controlee si semaine 1 est validee
Sortie  : parcours critique utilisable par vrais testeurs

Semaine 3
Production limitee prudente
Dev     : admin/support complet minimum, reconciliation paiement surveillee,
          prix final reel stabilise, corrections terrain
Staging : regression complete avant chaque promotion
Tests   : tests humains quotidiens, incidents support, paiement, wallet,
          matching charge legere, DiddiMap indisponible
Prod    : ouverture limitee zone pilote / chauffeurs selectionnes
Sortie  : version production limitee stable

Semaine 4
Beta publique controlee
Dev     : messagerie/appels si arbitrage valide, dispatch avance, polish admin,
          durcissement monitoring/securite
Staging : validation finale beta
Tests   : volume plus large, scenarios edge cases, support, rollback
Prod    : beta ouverte progressivement
Sortie  : version full production beta
```

## Projection administrative

Version `1.0` :

- objectif : montrer vite un produit utilisable;
- delai : 1 semaine;
- risque principal : bugs terrain, configuration DiddiMap/DiddiPay/FCM;
- resultat attendu : demo fiable + test controle.

Version `2.0` :

- objectif : produit commercial plus solide;
- delai : 2 semaines apres V1 dans le plan accelere;
- risque principal : DiddiMap traces, DiddiPay production, frontend temps reel,
  workflow support;
- resultat attendu : production limitee serieuse.

Version `2.1` :

- objectif : experience avancee;
- delai : semaine 4 dans le plan accelere si les arbitrages techniques sont
  rapides;
- resultat attendu : beta plus large avec meilleure qualite operationnelle.

## Conditions pour tenir le delai de 3 semaines

- DiddiGo implemente l'adapter REST DiddiMap traces rapidement.
- DiddiMap staging reste stable sur `/api/v1/map-traces/*`.
- DiddiPay staging/prod reste stable pour paiements et recharges.
- FCM fonctionne sur vrais telephones test.
- Les testeurs chauffeur/passager sont disponibles chaque jour.
- Les decisions produit restantes sont tranchees vite : solde minimum, confort
  garanti, regle prix final, procedure urgence.
- Les bugs bloquants sont corriges immediatement, sans attendre une fin de
  sprint.

Si une dependance externe bloque, on garde la production limitee sur les flux
valides et on marque explicitement le flux bloque comme non actif.

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
