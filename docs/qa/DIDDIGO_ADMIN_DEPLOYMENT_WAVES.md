# DiddiGo - Document administratif de deploiement

Public : administration, direction produit, operations, support, QA, equipe
technique.

Date de mise a jour : 2026-08-29.

Objectif : donner une vision courte et exploitable des vagues de livraison
DiddiGo, en parlant en use cases et en decisions operationnelles.

## Vision generale

DiddiGo doit etre lance progressivement. Le but n'est pas seulement de prouver
qu'une course peut etre creee, mais de verifier toute la chaine terrain :
passager, chauffeur, KYC, matching, paiement, commission, solde chauffeur,
support et securite.

Responsabilites des modules :

- DiddiGo gere le metier VTC : chauffeurs, vehicules, courses, matching,
  pricing, commission, wallet chauffeur, statut paiement, partage et urgence.
- DiddiFreeID gere l'identite : inscription, connexion, profil utilisateur
  global, roles globaux user/admin.
- DiddiMap gere la geographie : recherche de lieux, routes, distances, durees,
  traces et futurs insights.
- DiddiPay gere l'execution des paiements digitaux : DiddiPay, Wave, callbacks
  et statuts fournisseur.
- DiddiFiles gere les documents : permis, piece, selfie, carte grise, images et
  URLs signees.

## Etat actuel DiddiGo

Deja implemente cote backend :

- authentification via token DiddiFreeID et shadow user DiddiGo;
- creation profil chauffeur;
- documents KYC references par `file_id`;
- validation/rejet KYC par admin;
- blocage passage en ligne si chauffeur non valide;
- creation vehicule avec categorie et niveau de confort;
- recherche de lieux via DiddiMap;
- estimation de prix avec distance/duree DiddiMap;
- politique de prix DiddiGo avec commission et payout estime;
- creation, acceptation, refus, annulation, progression et notation de course;
- WebSocket chauffeur/passager quand l'application est active;
- enregistrement device FCM pour notifications push;
- paiement cash;
- paiement digital `diddipay` et `wave` via DiddiPay;
- recharge wallet chauffeur via DiddiPay/Wave;
- wallet chauffeur, ledger, commission et payout;
- reconciliation admin des paiements/recharges DiddiPay;
- lien public de partage de course sans login;
- bouton urgence journalise cote backend;
- stockage des samples GPS chauffeur pendant la course;
- catalogue d'erreurs DiddiGo documente;
- suite Bruno et documents QA disponibles.

Points a surveiller en test :

- le niveau de confort n'est pas encore un filtre dur de matching;
- le prix final reel base sur la distance/duree reellement parcourue depend
  encore du futur traitement de traces DiddiMap;
- les appels/messagerie instantanee ne sont pas dans DiddiGo actuellement;
- DiddiSend doit rester un service separe, pas une extension interne de DiddiGo.

## Vague 1.0 - MVP terrain controle

But : valider que DiddiGo fonctionne avec de vrais chauffeurs et passagers sur
une zone pilote.

Use cases :

- un passager se connecte;
- un passager cherche son depart et sa destination;
- un passager obtient un prix;
- un passager cree une course;
- un chauffeur KYC valide passe en ligne;
- un chauffeur proche recoit une offre;
- le chauffeur accepte ou refuse;
- le passager suit l'etat de la course;
- le chauffeur termine la course;
- le paiement cash est confirme;
- le support retrouve la course avec son identifiant.

Critere de sortie :

- 10 chauffeurs testeurs actifs;
- matching fiable sur les scenarios simples;
- pas de faux `no_driver_found` inexpliques;
- pas de 500 non documente sur le happy path;
- KYC bloque bien les chauffeurs non valides;
- logs lisibles par `request_id`, `ride_id`, `driver_id` et `user_id`.

Statut : pret pour test terrain controle, sous reserve de validation Portainer
et donnees de test.

## Vague 1.1 - Stabilisation terrain

But : corriger les problemes observes pendant les premiers tests reels.

Use cases :

- un chauffeur perd la connexion puis revient en ligne;
- un token expire et l'application sait relancer l'authentification;
- DiddiMap indisponible provoque une erreur claire, pas un fallback silencieux;
- un testeur peut refaire le meme scenario plusieurs fois;
- le support comprend pourquoi une course a echoue.

Critere de sortie :

- bugs critiques terrain corriges;
- erreurs principales connues par le frontend;
- tests Bruno verts sur les parcours MVP;
- protocole QA humain rempli.

Statut : a executer apres les premiers retours chauffeurs/passagers.

## Vague 1.2 - Paiements et wallet chauffeur

But : tester le modele commercial minimum.

Use cases :

- le passager paie en cash;
- le passager paie via DiddiPay;
- le passager paie via Wave quand disponible;
- DiddiGo cree le paiement mais ne decide pas le statut fournisseur;
- DiddiPay confirme le paiement par callback;
- si le callback est perdu, l'admin lance une reconciliation;
- le chauffeur voit son solde;
- le chauffeur recharge son solde;
- le support voit paiement, commission et payout.

Critere de sortie :

- cash reste toujours disponible;
- DiddiPay/Wave testables en staging;
- aucun montant n'est accepte depuis le frontend;
- `next_action` est renvoye pour ouvrir le checkout;
- le solde chauffeur change seulement apres confirmation paiement;
- callback rejoue deux fois ne double pas le solde.

Statut : implemente cote DiddiGo; a valider bout en bout avec DiddiPay staging.

## Vague 1.3 - KYC et operations chauffeur

But : rendre l'activation chauffeur controlable sans intervention SQL.

Use cases :

- le chauffeur soumet ses informations metier;
- le chauffeur associe ses documents via DiddiFiles;
- l'admin consulte un dossier KYC;
- l'admin approuve ou rejette;
- le chauffeur approuve peut passer en ligne;
- le chauffeur rejete ou en attente reste bloque.

Critere de sortie :

- validation admin possible via API;
- front chauffeur affiche clairement le statut KYC;
- documents consultables via URLs signees DiddiFiles;
- raison de rejet visible et exploitable.

Statut : implemente cote DiddiGo pour les references `file_id` et revue KYC;
depend de DiddiFiles pour l'upload/lecture des documents.

## Vague 1.4 - Notifications et temps reel

But : assurer que chauffeur et passager recoivent les informations importantes.

Use cases :

- chauffeur recoit une offre via WebSocket si l'app est ouverte;
- chauffeur recoit une notification FCM si l'app est en arriere-plan;
- passager recoit les changements d'etat;
- device FCM peut etre enregistre et desactive;
- logs indiquent si une notification est envoyee ou ignoree.

Critere de sortie :

- FCM configure en staging;
- frontend Android active le foreground service pour les tests chauffeurs;
- aucun scenario critique ne depend uniquement d'un WebSocket en arriere-plan;
- payload notification stable.

Statut : base backend implemente; a valider sur vrais telephones.

## Vague 1.5 - Securite et partage de course

But : rassurer passager, proches et support.

Use cases :

- le passager cree un lien de partage;
- un proche ouvre le lien sans compte;
- le proche voit une vue limitee de la course;
- la position partagee suit le chauffeur;
- le passager ou chauffeur signale une urgence;
- le support retrouve rapidement la course concernee.

Critere de sortie :

- lien public limite et expirant;
- aucune donnee sensible inutile exposee;
- urgence journalisee avec contexte;
- mecanisme temps reel ou polling raisonnable choisi pour la page publique.

Statut : base backend implemente; experience frontend publique a finaliser.

## Vague 1.6 - Confort garanti

But : garantir que le client recoit le niveau de service qu'il paie.

Use cases :

- le passager choisit Standard, Comfort ou Premium;
- le prix varie selon le confort;
- un choix Premium ne doit pas etre servi par un vehicule Standard;
- le chauffeur voit une offre compatible avec son vehicule.

Critere de sortie :

- regles de compatibilite vehicule/confort validees;
- matching refuse les vehicules trop bas pour le niveau paye;
- tests Bruno couvrent Standard, Comfort et Premium.

Statut : prix par confort implemente; filtre dur de matching a renforcer.

## Vague 1.7 - GPS reel et DiddiMap avance

But : preparer le prix final reel, les traces et l'amelioration DiddiMap.

Use cases :

- le chauffeur envoie des positions pendant la course;
- DiddiGo stocke les samples GPS lies au ride;
- en fin de course, DiddiGo transmet la trace a DiddiMap quand le contrat est
  pret;
- DiddiMap analyse la trace et produit des insights;
- un admin valide ou rejette les insights.

Critere de sortie :

- donnees GPS coherentes et auditees;
- pas de recalcul silencieux si DiddiMap echoue;
- future base pour prix final reel et amelioration de route.

Statut : collecte samples GPS implemente; integration finale DiddiMap traces a
terminer quand le contrat DiddiMap est fige.

## Vague 2.0 - Pre-production

But : figer une version stable avant ouverture commerciale.

Use cases :

- test avec plus de chauffeurs;
- test passager/chauffeur sur plusieurs telephones;
- verification Portainer staging/prod;
- verification secrets et variables d'environnement;
- verification sauvegardes;
- verification monitoring;
- validation support et operations.

Critere de sortie :

- decision go/no-go documentee;
- branche `stage` validee;
- branche `main` prete pour prod;
- rollback connu;
- support capable de diagnostiquer auth, KYC, matching et paiement.

Statut : a planifier apres vagues 1.0 a 1.7.

## Vague 2.1 - Production limitee

But : ouvrir petit, mesurer et corriger vite.

Use cases :

- zone pilote active;
- chauffeurs selectionnes;
- support disponible;
- cash prioritaire au debut;
- DiddiPay/Wave actives progressivement;
- suivi quotidien des incidents.

Critere de sortie :

- exploitation reelle sous controle;
- incidents critiques sous seuil acceptable;
- donnees terrain suffisantes pour prioriser la suite.

Statut : non demarre.

## Decisions administratives restantes

- taux de commission officiel;
- solde minimum chauffeur;
- blocage strict ou simple alerte si solde bas;
- regle finale de compatibilite Comfort/Premium;
- timing exact du paiement digital passager;
- activation Wave en meme temps que DiddiPay ou plus tard;
- procedure support en cas de paiement `requires_action` trop long;
- procedure support en cas de chauffeur KYC rejete;
- seuils de lancement de la zone pilote.

## Resume executif

La base DiddiGo est suffisamment avancee pour lancer une vague de test terrain
controlee. La priorite immediate n'est plus d'ajouter beaucoup de nouvelles
fonctionnalites, mais de verifier les parcours reels avec chauffeurs,
passagers, DiddiMap, DiddiPay, FCM et Portainer.

La production limitee ne doit commencer qu'apres validation terrain, paiement,
KYC, notifications et support.
