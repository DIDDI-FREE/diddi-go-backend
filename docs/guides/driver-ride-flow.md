# Parcours course chauffeur

```text
Profil valide + vehicule valide + solde suffisant -> en ligne
-> offre -> acceptation -> navigation pickup -> arrivee
-> code passager -> course -> fin -> paiement/gain
```

## Notifications d'offres (D9)

Le téléphone doit enregistrer son jeton FCM actuel via `/v1/devices/register`
après connexion et lors du renouvellement du jeton. Le serveur cible les appareils
activés appartenant au compte chauffeur ; il ne découvre pas un téléphone non
enregistré. Une acceptation FCM ne prouve pas l'affichage sur le téléphone.

Le backend désactive les jetons explicitement déclarés `UNREGISTERED`, ainsi que
le cas `INVALID_ARGUMENT` accompagné du diagnostic FCM explicite « registration
token is not a valid FCM registration token ». Une erreur générique 400/404,
un problème de configuration, de quota, d'authentification ou une panne temporaire
ne désactive pas le jeton. Les autres appareils continuent à être traités.
Référence : [codes d'erreur FCM](https://firebase.google.com/docs/cloud-messaging/error-codes).

Traces à corréler par `ride_id` et `driver_user_id` :

- `push.ride_offer.targets` : nombre d'appareils actifs trouvés ;
- `push.ride_offer.attempted` : appareil, plateforme, fournisseur, dernière date
  d'enregistrement et empreinte du jeton ;
- `push.ride_offer.sent` : fournisseur ayant accepté l'envoi ;
- `push.ride_offer.failed` : code fournisseur / statut HTTP ou type d'erreur ;
- `push.device.disabled` : jeton désactivé et motif ;
- `push.ride_offer.skipped` : aucun appareil, fournisseur non pris en charge ou
  push désactivé. Un push désactivé n'est plus annoncé comme envoyé.

Les corps d'erreur FCM et les jetons complets ne sont pas journalisés. La
désactivation est sauvegardée dans la transaction d'envoi ; les appareils désactivés
ne sont plus ciblés aux envois suivants. L'enregistrement explicite d'un jeton via
l'application peut le réactiver. Aucune boucle de retry supplémentaire n'est créée.

Pour la recette : connecter le téléphone actuel, autoriser les notifications,
placer l'application en arrière-plan et déclencher une offre. Fournir l'heure,
le compte et la course ; vérifier dans les traces que le nouvel appareil est bien
ciblé et que les anciens jetons invalides ne le sont plus après leur désactivation.

## Escales et historique

Le chauffeur affecté et le passager peuvent ajouter une escale pendant la course.
S'abonner à `ride.stop_added`, puis relire la course et ses `stops`. Le prix ne
change pas automatiquement lors de l'ajout. Après reconnexion, récupérer la liste
par HTTP. Voir le [contrat escales et historique du guide passager](passenger-ride-flow.md#escales).

L'historique distingue `planned_distance_km` du devis et `actual_distance_km` de
la trace GPS. Lire les adresses dans `pickup.address` / `dropoff.address` ou leurs
alias historiques. Une mesure ou une adresse absente reste `null`.

## Arrivee

Le chauffeur publie d'abord une position recente, puis appelle `/arrive`.
L'arrivee est refusee hors du rayon configure avec
`422 DRIVER_TOO_FAR_FROM_PICKUP`.

## Attente pendant la course

`POST /waiting/start` exige une course `in_progress`, une vitesse datant de
moins de 30 secondes et une vitesse inferieure ou egale a 3 km/h.

## Supplements

Le chauffeur charge le catalogue serveur via
`GET /v1/rides/config/supplements`. Il ne fixe pas librement le tarif, sauf
`other`, plafonne a 1 000 XOF et accompagne d'un libelle obligatoire. La
proposition reste hors prix tant que le passager ne l'a pas acceptee.

```http
POST /v1/rides/{ride_id}/supplements
```

```json
{"type":"toll"}
```

Pour `other`, le payload contient `amount` et `custom_label`. Le champ
historique `reason` reste accepte temporairement comme alias de `type`.
