# DiddiGo - Catalogue des erreurs API

Ce document est la reference des erreurs exposees par DiddiGo.

Format standard :

```json
{
  "error": {
    "code": "DRIVER_NOT_VERIFIED",
    "message": "Votre profil chauffeur n'est pas encore valide.",
    "details": {
      "request_id": "req_..."
    }
  }
}
```

Regle produit :

- Le statut HTTP donne la famille technique de l'erreur.
- Le champ `error.code` donne la raison metier DiddiGo.
- Les clients doivent piloter l'UI avec `error.code`, pas avec le texte.
- Les codes DiddiGo sont textuels et explicites; ils ne reutilisent pas des
  numeros globaux DiddiFree.

## Auth et identite

| HTTP | Code | Sens |
|---|---|---|
| `401` | `TOKEN_MISSING` | Aucun bearer token fourni |
| `401` | `TOKEN_EXPIRED` | Access token expire |
| `401` | `TOKEN_INVALID` | Token invalide, mal signe, mauvais type ou claim manquant |
| `401` | `REFRESH_TOKEN_INVALID` | Refresh token invalide |
| `403` | `FORBIDDEN_ROLE` | Role global insuffisant, par exemple route admin appelee par `user` |
| `403` | `USER_NOT_VERIFIED` | Compte DiddiFreeID non actif |
| `403` | `USER_SUSPENDED` | Compte local ou shadow suspendu |
| `500` | `IDENTITY_NOT_CONFIGURED` | Integration DiddiFreeID non configuree cote backend |
| `4xx/5xx` | `IDENTITY_PROFILE_ERROR` | Profil DiddiFreeID indisponible ou erreur upstream |

## Auth locale de developpement

Ces routes restent utiles en local/dev si l'auth locale est active.

| HTTP | Code | Sens |
|---|---|---|
| `400` | `OTP_INVALID` | OTP incorrect ou inexistant |
| `410` | `OTP_EXPIRED` | OTP expire |
| `429` | `OTP_RATE_LIMITED` | Demande OTP trop rapprochee |
| `409` | `PHONE_ALREADY_REGISTERED` | Telephone deja enregistre |
| `422` | `INVALID_PHONE_FORMAT` | Format telephone invalide |
| `422` | `INVALID_ROLE` | Role demande invalide |

## Chauffeur, KYC et vehicule

| HTTP | Code | Sens |
|---|---|---|
| `403` | `DRIVER_NOT_VERIFIED` | Profil chauffeur non valide par l'admin KYC |
| `403` | `DRIVER_PROFILE_REQUIRED` | Une action exige un profil chauffeur |
| `404` | `DRIVER_PROFILE_NOT_FOUND` | Aucun profil chauffeur pour ce compte ou cet identifiant |
| `409` | `DRIVER_PROFILE_ALREADY_EXISTS` | Le compte a deja un profil chauffeur |
| `409` | `NO_ACTIVE_VEHICLE` | Aucun vehicule actif associe au chauffeur |
| `409` | `PLATE_ALREADY_REGISTERED` | Plaque vehicule deja enregistree |
| `422` | `DRIVER_KYC_STATUS_INVALID` | Filtre de statut KYC invalide |
| `422` | `INVALID_KYC_DOCUMENTS` | Documents KYC incoherents ou incomplets |
| `422` | `INVALID_LICENSE_NUMBER` | Numero de permis vide ou invalide |
| `422` | `INVALID_VEHICLE_CATEGORY` | Categorie vehicule inconnue |
| `422` | `INVALID_COMFORT_LEVEL` | Niveau de confort inconnu |

## Rides et matching

| HTTP | Code | Sens |
|---|---|---|
| `403` | `RIDE_NOT_OWNED_BY_USER` | L'utilisateur n'est ni passager, ni chauffeur assigne, ni admin |
| `403` | `OFFER_NOT_YOURS` | Offre de course reservee a un autre chauffeur |
| `404` | `RIDE_NOT_FOUND` | Course introuvable |
| `409` | `ACTIVE_RIDE_ALREADY_EXISTS` | Le passager a deja une course active |
| `409` | `INVALID_STATUS_TRANSITION` | Transition de statut interdite |
| `409` | `OFFER_EXPIRED` | Offre chauffeur expiree |
| `409` | `RIDE_ALREADY_CANCELLED` | Course deja annulee |
| `409` | `RIDE_ALREADY_COMPLETED` | Course deja terminee |
| `409` | `RIDE_ALREADY_MATCHED` | Course deja acceptee par un chauffeur |
| `409` | `RIDE_NOT_CANCELLABLE` | Course non annulable dans son etat actuel |
| `409` | `RIDE_NOT_COMPLETED` | Action impossible avant fin de course |
| `409` | `RIDE_NOT_OFFERABLE` | Course pas dans un etat pouvant etre propose au matching |
| `422` | `INVALID_CANCEL_REASON` | Motif d'annulation invalide |
| `422` | `INVALID_STATUS` | Statut inconnu |
| `422` | `RATING_OUT_OF_RANGE` | Note hors intervalle 1 a 5 |
| `409` | `RATING_ALREADY_SUBMITTED` | Note deja envoyee pour ce role |

## Places, routing et DiddiMap

DiddiMap est le fournisseur geographique unique. DiddiGo ne fait pas de fallback
silencieux.

| HTTP | Code | Sens |
|---|---|---|
| `502` | `DIDDIMAP_INVALID_RESPONSE` | Reponse geographique invalide ou inexploitable |
| `503` | `DIDDIMAP_UNAVAILABLE` | DiddiMap indisponible, timeout ou erreur reseau |
| `422` | `INVALID_VEHICLE_CATEGORY` | Categorie demandee invalide |
| `422` | `INVALID_COMFORT_LEVEL` | Comfort level invalide |
| `422` | `INVALID_PAYMENT_METHOD` | Methode de paiement invalide |

## Paiement

| HTTP | Code | Sens |
|---|---|---|
| `403` | `DRIVER_PROFILE_REQUIRED` | Seul un chauffeur metier peut encaisser |
| `404` | `RIDE_NOT_FOUND` | Course introuvable |
| `409` | `RIDE_NOT_COMPLETED` | Encaissement impossible avant fin de course |
| `422` | `INVALID_PAYMENT_METHOD` | Methode inconnue ou non supportee |
| `422` | `PAYMENT_EMAIL_REQUIRED` | Email client requis pour initialiser DiddiPay/Paystack |
| `503` | `PAYMENT_CONFIGURATION_MISSING` | Configuration DiddiPay manquante cote DiddiGo |
| `503` | `PAYMENT_PROVIDER_UNAVAILABLE` | DiddiPay indisponible |
| `401` | `PAYMENT_CALLBACK_INVALID` | Signature ou enveloppe callback DiddiPay invalide |
| `404` | `PAYMENT_INTENT_NOT_FOUND` | PaymentIntent inconnu cote DiddiGo |
| `409` | `PAYMENT_OPERATION_CONFLICT` | Operation paiement incompatible avec l'etat courant |
| `422` | `PAYMENT_STATUS_INVALID` | Statut DiddiPay inconnu |

## Partage et securite

| HTTP | Code | Sens |
|---|---|---|
| `404` | `SHARE_LINK_NOT_FOUND` | Lien de partage introuvable ou expire |
| `403` | `RIDE_NOT_OWNED_BY_USER` | Seul un participant ou admin peut creer le lien ou signaler une urgence |

## WebSocket

Les erreurs WebSocket sont envoyees soit via close code, soit via message JSON.

| Canal | Code | Sens |
|---|---|---|
| close `4401` | `TOKEN_MISSING` | Token absent |
| close `4401` | `TOKEN_EXPIRED` | Token expire |
| close `4401` | `TOKEN_INVALID` | Token invalide |
| message | `FORBIDDEN_ROLE` | Evenement reserve a un chauffeur/admin |
| message | `INVALID_LOCATION` | Position invalide |
| message | `INVALID_RIDE_ID` | Identifiant course invalide |

## Codes reserves

Ces codes sont reserves pour la suite et ne doivent pas etre reutilises pour
un autre sens :

| Code | Usage prevu |
|---|---|
| `INVALID_KYC_DOCUMENTS` | Validation stricte future des documents KYC |
| `DIDDIPAY_UNAVAILABLE` | Provider DiddiPay indisponible |
| `WAVE_UNAVAILABLE` | Provider Wave indisponible |
| `PUSH_PROVIDER_UNAVAILABLE` | FCM indisponible |
| `NOTIFICATION_DEVICE_NOT_FOUND` | Token device inconnu |
