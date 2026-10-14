# Catalogue d'erreurs DiddiGo

Format standard :

```json
{"error":{"code":"CODE","message":"Message lisible","details":{}}}
```

| HTTP | Code | Signification | Action client |
|---:|---|---|---|
| 401 | `TOKEN_MISSING` | Jeton absent | Reconnecter l'utilisateur |
| 401 | `TOKEN_INVALID` | Jeton non valide | Reconnecter l'utilisateur |
| 401 | `TOKEN_EXPIRED` | Jeton expire | Rafraichir ou reconnecter |
| 403 | `RIDE_NOT_OWNED_BY_USER` | Utilisateur non participant | Ne pas rejouer |
| 409 | `ARRIVAL_INVALID_RIDE_STATUS` | Arrivee impossible dans cet etat | Relire la course |
| 422 | `DRIVER_LOCATION_REQUIRED` | Position recente absente | Renvoyer une position GPS |
| 422 | `DRIVER_TOO_FAR_FROM_PICKUP` | Chauffeur hors rayon | Afficher `distance_meters` et `maximum_meters` |
| 409 | `NO_SHOW_INVALID_RIDE_STATUS` | Attente pre-course inactive | Relire la course |
| 409 | `NO_SHOW_TOO_EARLY` | Delai de 10 minutes non atteint | Utiliser `remaining_seconds` |
| 409 | `WAITING_TELEMETRY_REQUIRED` | Vitesse GPS recente absente | Publier une position puis rejouer |
| 409 | `VEHICLE_NOT_STOPPED` | Vitesse superieure au seuil | Afficher `speed_kmh` et `maximum_kmh` |
| 422 | `INVALID_SUPPLEMENT_TYPE` | Type de supplement inconnu | Recharger le catalogue |
| 422 | `INVALID_SUPPLEMENT_AMOUNT` | Montant hors regle | Afficher le tarif contractuel |
| 409 | `SUPPLEMENT_ALREADY_DECIDED` | Proposition deja traitee | Relire les supplements |
| 422 | `VALIDATION_ERROR` | Corps, chemin ou paramètres invalides | Corriger `details.violations` |
| 422 | `INVALID_PAYMENT_METHOD` | Moyen ou réseau de paiement invalide | Utiliser le contrat typé |
| 409 | `PAYMENT_OPERATION_CONFLICT` | Choix ou état de paiement incompatible | Relire la course et le paiement |
| 409 | `EARLY_STOP_INVALID_RIDE_STATUS` | Arrêt anticipé indisponible dans cet état | Relire la course |
| 409 | `EARLY_STOP_NOT_REQUESTED` | Aucune demande active | Le passager doit demander l'arrêt |
| 409 | `EARLY_STOP_REQUEST_EXPIRED` | Fenêtre de deux minutes expirée | Refaire la demande |
| 503 | `EARLY_STOP_PRICING_UNAVAILABLE` | Trace chauffeur insuffisante | Conserver la course active et réessayer |

Ce catalogue complete l'OpenAPI. Chaque nouveau code stable doit etre ajoute
ici et dans le changelog du jour.
