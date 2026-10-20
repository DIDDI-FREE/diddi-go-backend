# DiddiGo - Brief frontend integre

Date : 2026-10-20  
Version : 2026-10-20.v1  
Public : applications passager, chauffeur et DiddiFree Pro

## Regle de lecture

Ce brief rassemble les parcours frontend disponibles dans la branche `stage`.
Pour activer une route dans l'application staging, verifier d'abord qu'elle est
presente dans <https://go-staging.diddifree.com/openapi.json>. Cette URL decrit
le runtime effectivement deploye. Une capacite presente ici mais absente de cet
OpenAPI attend encore son deploiement : la cacher ou la proteger par feature
flag, sans simuler son resultat.

Sources complementaires :

- Swagger : <https://go-staging.diddifree.com/docs>
- WebSocket : `wss://go-staging.diddifree.com/v1/ws?token=<access_token>`
- Guides : `docs/guides/`
- Integrations : `docs/integrations/`
- Erreurs : `docs/api/error-catalog.md`

Les routes `admin` et `internal` ne doivent jamais etre appelees par une
application utilisateur.

## Principes communs

1. Le JWT DiddiFreeID est envoye dans `Authorization: Bearer <access_token>`.
2. Le serveur tire l'identite, le role et les droits du JWT. Le frontend ne
   transmet jamais un `user_id`, un `driver_id`, un expediteur ou un statut.
3. Une erreur metier utilise `error.code` pour la logique UX ; le texte reste
   une information d'affichage.
4. Le WebSocket accelere l'interface, mais `GET /v1/rides/{ride_id}` reste la
   source canonique apres reconnexion ou evenement ambigu.
5. Les fichiers passent par DiddiFiles : le frontend envoie ensuite seulement
   les `file_id` confirmes a DiddiGo.

## Parcours passager

### Rechercher, deviser et creer une course

1. Rechercher un lieu avec `GET /v1/places/search`, en envoyant le `bias_lat`
   et le `bias_lng` lorsque la position du telephone est disponible.
2. Appeler `POST /v1/rides/pricing/estimate` avec pickup, dropoff, categorie et
   niveau de confort. Conserver `quote_id`, montant, details de prix et
   `expires_at`.
3. Creer la course via `POST /v1/rides` avec le `quote_id` encore valide.
4. Toute modification de pickup, dropoff, categorie ou confort impose un
   nouveau devis. Le moyen de paiement peut changer sans invalider le devis.

Un devis expire doit etre refait ; ne pas reutiliser silencieusement son prix.
Les escales existent techniquement mais restent hors MVP de lancement : ne pas
les exposer sans activation produit explicite.

### Suivre la course

1. Ouvrir le WebSocket apres connexion et s'abonner a la course selon le
   contrat AsyncAPI.
2. Traiter `ride.new_request`, `ride.status_changed`, `ride.driver_location`,
   `ride.waiting_changed`, `ride.supplement_changed` et `ride.no_driver_found`.
3. A chaque reconnexion, ou apres un evenement manquant, relire
   `GET /v1/rides/{ride_id}`.
4. La position affichee au passager est celle du chauffeur. Seule la trace GPS
   chauffeur peut servir a la facturation et a l'audit.

### Arrivee et attente avant depart

Quand le chauffeur signale son arrivee, la course retourne le bloc `arrival`.
Afficher l'heure d'arrivee et le compteur d'attente :

- `free_seconds = 180` : trois minutes gratuites ;
- apres ces trois minutes, attente facturee a `100 XOF` par minute, au prorata
  de la seconde ;
- `no_show_after_seconds = 600` : dix minutes avant le parcours client absent.

Les 180 secondes gratuites ne se repetent pas : elles sont appliquees une fois
depuis le debut de l'attente avant depart. La valeur `waiting_seconds` est la
duree ecoulee ; la valeur `waiting_fee` est le montant deja facture.

Le passager peut partager le code de depart a six chiffres, ou un QR contenant
`ride_id + code`. Le chauffeur appelle toujours la route de demarrage existante
apres lecture du QR ou saisie du code.

### Supplement et arret anticipe

Le chauffeur peut proposer un supplement ; le passager doit pouvoir le voir et
l'accepter ou le refuser. Les forfaits MVP sont : peage `500 XOF`, bagage `500`
ou `1000 XOF`, parking `200 XOF`, autre frais jusqu'a `1000 XOF`. L'attente est
calculee par le serveur, pas declaree comme supplement libre.

Pour un arret anticipe, le passager demande puis le chauffeur confirme :

```text
POST /v1/rides/{ride_id}/early-stop/request
POST /v1/rides/{ride_id}/early-stop/confirm
```

La demande affiche un montant `provisional=true` et expire apres deux minutes.
Apres confirmation, la course reste `completed` avec
`completion_reason=early_stop`; le prix definitif est calcule depuis la trace
GPS chauffeur, avec le `base_fare` comme minimum.

### Paiement, dette et notation

Au depart, le passager choisit `cash` ou `mobile_money`. Pour Mobile Money,
choisir `orange`, `wave` ou `mtn` au moment de la preparation du paiement ;
le reseau est obligatoire. En cas d'echec ou expiration, creer une nouvelle
tentative, avec une nouvelle cle d'idempotence, sans effacer l'historique.

Pour le cash, seul le chauffeur confirme la reception. Ne pas afficher au
passager un bouton de confirmation finale.

Si `POST /v1/rides` retourne `409 PASSENGER_DEBT_OUTSTANDING`, ouvrir le flux
de regularisation : `GET /v1/passenger/debts`, puis paiement Mobile Money ou
demande de paiement cash. Une dette bloque une nouvelle course, mais pas le
login, l'historique ou la consultation de la dette.

La note est possible seulement apres `completed`, une fois par participant et
par course. Les notes vont de 1 a 5. Une course annulee se signale au support,
elle ne devient pas notee.

## Parcours chauffeur

### Profil, KYC et KYV

Le statut operationnel chauffeur et le statut du dossier sont distincts. Un
profil peut etre bloque pour verification alors que le compte DiddiFreeID reste
actif. Lire `GET /v1/drivers/me` et afficher les raisons de blocage, le statut
KYC et le statut KYV separement.

Documents KYC obligatoires : permis recto/verso, CNI recto/verso et selfie.
Documents KYV : carte grise, assurance, controle technique et six photos du
vehicule (avant, arriere, gauche, droite, interieur, plaque). L'autorisation
de transport peut etre stockee sans etre bloquante au MVP.

Les `purpose` DiddiFiles sont documentes dans `docs/integrations/diddifiles.md`.
Chaque fichier doit etre uploade puis confirme dans DiddiFiles avant l'appel
DiddiGo qui recoit son `file_id`.

- correction personnelle : `POST /v1/drivers/kyc/resubmit` ;
- correction KYV du vehicule :
  `POST /v1/drivers/vehicles/{vehicle_id}/kyv/resubmit` ;
- correction des informations du vehicule : `PUT /v1/drivers/me/vehicle`.

Ne renvoyer que les documents corriges lorsque le schema de route le permet.
Afficher les motifs et corrections attendues retournes par la revue de dossier,
sans transformer un refus de dossier en suspension definitive du compte.

`make` et `model` sont obligatoires pour le vehicule ; `color` est optionnel.

### Se mettre en ligne et executer une course

1. Verifier `GET /v1/me/capabilities` et `GET /v1/drivers/me` avant d'afficher
   le bouton disponible.
2. Le serveur reste decisif : `POST /v1/drivers/online` peut refuser si le
   profil, le KYV, le vehicule ou le solde ne sont pas eligibles.
3. Ecouter `ride.new_request`; le chauffeur ne voit pas le montant avant
   acceptation et demarrage selon la politique metier.
4. Envoyer les positions chauffeur a la frequence prevue par l'application,
   via `POST /v1/rides/{ride_id}/location-samples`.
5. A l'arrivee, appeler `/arrive`; au depart, `/start` avec le code a six
   chiffres ou le code issu du QR.
6. Pendant la course, l'attente necessite une vitesse GPS recente faible ; le
   serveur applique les regles et calcule le montant.
7. Terminer par la route de statut existante, puis confirmer le cash seulement
   si l'argent a ete recu.

### Score affiche

Un nouveau chauffeur affiche publiquement `rating_avg=5.0`, `rating_count=0`
et `rating_status=new`. Ce n'est pas une moyenne de notes recues. Apres la
premiere note valide, `rating_status=rated` et la moyenne reelle est affichee.

Les scores internes peuvent utiliser une base neutre `4.0` avec
`score_status=insufficient_data`; ne pas afficher cela comme une mauvaise
reputation. Un SOS, une course en cours, ou `no_driver_found` ne degrade pas
le score par eux-memes.

Activer `rating_status` uniquement quand il apparait dans l'OpenAPI staging et
la reponse runtime. Le schema local le prevoit dans `stage`, mais le deploiement
staging reste la reference d'activation.

### Wallet et retraits

Le chauffeur consulte son wallet et son ledger avec les routes wallet. Pour un
retrait : demander d'abord un devis de retrait, choisir la destination Mobile
Money, puis creer le retrait avec le montant et la destination retournee. Ne
pas reutiliser un devis expire ni inventer un statut de paiement local.

## Securite, partage et communication

Le partage de course est en lecture seule, sans login, avec le lien partage
genere par le serveur. Ne pas exposer les donnees personnelles du passager ou
du chauffeur au-dela du contrat de partage.

Pour SOS, l'application peut creer l'alerte et afficher son resultat. WhatsApp
est le canal disponible a confirmer par la reponse serveur ; le SMS reste
conditionne a la configuration et ne doit pas etre annonce comme garanti tant
qu'il n'est pas confirme en staging.

La messagerie et les appels passent par DiddiComms. Le frontend appelle les
routes publiques DiddiComms, jamais le resolver interne DiddiGo. DiddiGo decide
des participants, de la fenetre de communication et des permissions.

## Erreurs et etats a traiter

| Cas | Action frontend |
| --- | --- |
| `401` / token expire | rafraichir la session, puis rejouer seulement une requete idempotente |
| Handshake WebSocket `403` | ne pas ouvrir de socket ; renouveler la session |
| WebSocket `4401` | renouveler le token et reconnecter |
| `409 QUOTE_EXPIRED` | demander un nouveau devis |
| `409 PASSENGER_DEBT_OUTSTANDING` | ouvrir la regularisation de dette |
| `403 DRIVER_NOT_VERIFIED` | afficher le dossier KYC/KYV et ses corrections |
| echec Mobile Money | permettre une nouvelle tentative, sans creer une nouvelle course |
| evenement WebSocket inconnu ou manque | relire le detail REST de la course |

Les autres codes doivent etre lus dans `docs/api/error-catalog.md`; ne pas
coder une liste de messages uniquement a partir de statuts HTTP.

## Recette frontend minimale

1. Passager : recherche, devis, creation, suivi temps reel, annulation et
   reprise apres reconnexion.
2. Chauffeur : profil, uploads DiddiFiles, KYC/KYV refuse puis corrige,
   eligibilite en ligne et reception d'offre.
3. Course : arrivee, compteur gratuit, code/QR de depart, GPS, attente,
   supplement accepte/refuse, fin et paiement cash/Mobile Money.
4. Cas de protection : dette ouverte, token expire, WebSocket coupe, erreur
   DiddiMap explicite, SOS avec statut de livraison retourne.
5. Communication : ouverture d'une conversation DiddiComms seulement lorsque
   la course autorise encore l'echange.

## Escalade backend

Remonter au backend avec `X-Request-ID`, `ride_id`, chemin, statut HTTP,
`error.code` et heure UTC. Ne jamais joindre de JWT, secret, numero de
telephone complet, document KYC ou URL signee DiddiFiles dans un ticket public.
