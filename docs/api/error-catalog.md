# Catalogue d'erreurs DiddiGo

Version : `2026-10-23`. Ce catalogue est la reference frontend pour les
erreurs metier DiddiGo. OpenAPI decrit les schemas ; ce document explique quoi
faire. Le format normal est :

```json
{"error":{"code":"CODE","message":"Message lisible","details":{}}}
```

Les erreurs de proxy, les 404 de route et les erreurs HTML externes ne sont pas
garanties dans cette enveloppe.

## Session et droits

| HTTP | Code | Action frontend |
|---:|---|---|
| 401 | `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED` | Renouveler la session puis refaire une lecture, jamais une mutation inconnue. |
| 403 | `RIDE_NOT_OWNED_BY_USER`, `FORBIDDEN_ROLE` | Ne pas rejouer ; retirer l'action de l'interface. |
| 403 | `DRIVER_PROFILE_REQUIRED`, `DRIVER_NOT_VERIFIED`, `VEHICLE_NOT_VERIFIED` | Afficher le parcours chauffeur/KYC ou KYV. |
| 403 | `DRIVER_BALANCE_TOO_LOW` | Ouvrir la recharge du wallet chauffeur. |

## Course, devis et matching

| HTTP | Code | Action frontend |
|---:|---|---|
| 404 | `RIDE_NOT_FOUND`, `ACTIVE_RIDE_NOT_FOUND` | Revenir a la liste ou a l'accueil. |
| 409 | `ACTIVE_RIDE_ALREADY_EXISTS` | Restaurer la course active. |
| 409 | `QUOTE_EXPIRED` | Demander un nouveau devis. |
| 409 | `RIDE_ALREADY_CANCELLED`, `RIDE_ALREADY_COMPLETED`, `RIDE_NOT_CANCELLABLE` | Relire la course. |
| 409/423 | `RIDE_START_CODE_REQUIRED`, `INVALID_RIDE_START_CODE`, `RIDE_START_CODE_ALREADY_USED`, `RIDE_START_CODE_BLOCKED` | Afficher ou redemander le code de depart ; pour le verrouillage, contacter le support. |
| 422 | `DRIVER_LOCATION_REQUIRED`, `DRIVER_TOO_FAR_FROM_PICKUP` | Publier une position chauffeur puis retenter l'arrivee. |
| 409 | `ARRIVAL_INVALID_RIDE_STATUS`, `NO_SHOW_INVALID_RIDE_STATUS`, `NO_SHOW_TOO_EARLY` | Relire la course ; utiliser `details.remaining_seconds` si fourni. |

## Attente, supplements et escales

| HTTP | Code | Action frontend |
|---:|---|---|
| 409 | `WAITING_TELEMETRY_REQUIRED`, `VEHICLE_NOT_STOPPED` | Publier une position GPS recente ou attendre l'arret reel du vehicule. |
| 409 | `WAITING_INVALID_RIDE_STATUS`, `WAITING_STOP_ENDPOINT_REQUIRED` | Relire la course et utiliser la bonne action. |
| 422 | `INVALID_SUPPLEMENT_TYPE`, `INVALID_SUPPLEMENT_AMOUNT`, `SUPPLEMENT_LABEL_REQUIRED` | Recharger le catalogue tarifaire ; demander un libelle pour `other`. |
| 404 | `SUPPLEMENT_NOT_FOUND` | Recharger les supplements. |
| 409 | `SUPPLEMENT_ALREADY_DECIDED` | Recharger les supplements. |

## Paiements

| HTTP | Code | Action frontend |
|---:|---|---|
| 409 | `PAYMENT_OPERATION_CONFLICT` | Relire la course et son paiement avant une nouvelle tentative. |
| 409 | `RIDE_NOT_COMPLETED` | Attendre la fin effective de la course puis relire son montant final avant de preparer le paiement. |
| 422 | `INVALID_PAYMENT_METHOD` | Afficher cash ou Mobile Money avec reseau obligatoire. |
| 503 | `PAYMENT_CONFIGURATION_MISSING`, `PAYMENT_PROVIDER_UNAVAILABLE` | Afficher une indisponibilite temporaire ; ne pas creer de doublon. |
| 409 | `IDEMPOTENCY_CONFLICT`, `IDEMPOTENCY_IN_PROGRESS` | Conserver la meme cle pour le meme retry ; relire le paiement si le traitement est en cours. |
| 409 | `WITHDRAWAL_PROFILE_PHONE_REQUIRED`, `WITHDRAWAL_QUOTE_ALREADY_USED`, `WITHDRAWAL_VERIFICATION_USED` | Completer le profil ou relire le retrait existant ; ne pas creer un second payout. |
| 400/404/410/429 | `WITHDRAWAL_VERIFICATION_INVALID`, `WITHDRAWAL_VERIFICATION_NOT_FOUND`, `WITHDRAWAL_VERIFICATION_EXPIRED`, `WITHDRAWAL_VERIFICATION_LOCKED`, `WITHDRAWAL_VERIFICATION_RATE_LIMITED` | Afficher l'echec OTP ; permettre une nouvelle demande quand le delai le permet. |
| 503 | `SMS_NOT_CONFIGURED`, `WITHDRAWAL_VERIFICATION_DELIVERY_FAILED` | Afficher une indisponibilite temporaire ; ne jamais contourner l'OTP. |

Les codes `PASSENGER_DEBT_*` sont conserves pour les routes historiques
`/v1/passenger/debts/*`, hors parcours MVP courant. Un echec Mobile Money ne
cree plus automatiquement de dette et ne bloque plus une nouvelle course.

## Integrations et infrastructure

| HTTP | Code | Action frontend |
|---:|---|---|
| 503 | `DIDDIMAP_UNAVAILABLE`, `DIDDIMAP_AUTHENTICATION_FAILED`, `DIDDIMAP_INVALID_RESPONSE` | Afficher l'indisponibilite cartographique ; ne pas inventer un itineraire. |
| 503 | `DATABASE_UNAVAILABLE`, `CACHE_UNAVAILABLE` | Retry avec backoff ; conserver les saisies locales. |
| 429 | `EMERGENCY_RATE_LIMITED` | Afficher `details.retry_after_seconds` ; l'alerte precedente reste tracee. |

## Regle de maintenance

Tout nouveau code stable doit etre ajoute ici, dans la route OpenAPI concernee,
dans le guide utilisateur correspondant et dans le changelog date du jour.
