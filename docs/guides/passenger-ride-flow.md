# Parcours course passager

```text
Recherche lieu -> estimation -> creation -> matching -> chauffeur assigne
-> approche -> arrivee -> verification code -> course -> paiement -> note
```

## Arrivee et attente pre-course

Quand le chauffeur appelle `POST /v1/rides/{ride_id}/arrive`, la course passe
a `arrived`. Le compteur appartient uniquement a cette arrivee :

- `0..180` secondes : gratuites ;
- au-dela : `100 XOF/minute`, calcule au prorata des secondes ;
- apres `600` secondes : le chauffeur peut declarer `passenger_no_show` ;
- les secondes gratuites inutilisees ne sont jamais reportees.

Le passager suit `ride.status_changed`, mais relit la course apres reconnexion.
La lecture `GET /v1/rides/{ride_id}` expose aussi dans `arrival` les valeurs
contractuelles `free_seconds`, `price_per_minute_xof` et
`no_show_after_seconds` : ne jamais les remplacer par des constantes Flutter.

## Reprise apres interruption

Au retour de l'application ou apres une coupure WebSocket :

1. appeler `GET /v1/rides/active/current` ;
2. si la route retourne 200, afficher cette course et se reabonner au socket ;
3. si elle retourne `404 ACTIVE_RIDE_NOT_FOUND`, revenir a l'ecran d'accueil ;
4. ne jamais deduire une course active depuis le cache seul.

## Supplements

Le chauffeur propose une ligne ; le passager la voit avant facturation et
l'accepte ou la conteste. Seules les lignes acceptees entrent dans le total.

```http
GET /v1/rides/{ride_id}/supplements
POST /v1/rides/{ride_id}/supplements/{supplement_id}/decision
```

```json
{"decision":"accepted"}
```

La valeur alternative est `disputed`. Rejouer la meme decision est
idempotent ; tenter de remplacer une decision terminale retourne
`409 SUPPLEMENT_ALREADY_DECIDED`.

| Type | Tarif |
|---|---:|
| `toll` | 500 XOF |
| `parking` | 200 XOF |
| `baggage_standard` | 500 XOF |
| `baggage_large` | 1 000 XOF |
| `other` | montant propose, maximum 1 000 XOF |

L'attente a `100 XOF/minute` est calculee par le backend et n'est pas une
ligne libre ajoutee par le chauffeur.

## Escales

Une escale est un waypoint qui modifie l'itineraire complet, et non une pause
facturee automatiquement. Le chauffeur peut actuellement ajouter le point via
`POST /v1/rides/{ride_id}/stops`. La tarification d'une escale doit donc venir
d'un nouveau devis ou d'un ajustement explicite valide par le passager ; elle
ne doit pas etre calculee comme une attente. Les horodatages operationnels par
escale ne sont pas encore exposes et ne doivent pas etre affiches comme acquis.
