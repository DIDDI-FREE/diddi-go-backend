# DiddiGo - Brief frontend retraits chauffeur

Version : `2026-10-10`

## Parcours

1. Afficher le wallet avec `GET /v1/drivers/me/wallet`.
2. Demander un devis avec `POST /v1/drivers/me/wallet/withdrawals/quote`.
3. Afficher le montant, les frais, le net et l'expiration du devis.
4. Confirmer avec `POST /v1/drivers/me/wallet/withdrawals` en envoyant le `quote_id` et la reference beneficiaire.
5. Suivre le retrait avec `GET /v1/drivers/me/wallet/withdrawals/{id}` ou la liste chauffeur.

## Soldes

- `available_balance` : argent utilisable immediatement.
- `reserved_balance` : argent immobilise pendant un retrait en cours.
- `total_balance` : somme disponible et reservee.
- `balance` reste present pour compatibilite et correspond au solde disponible.

## Statuts

- `reserved` : montant reserve localement.
- `processing` : traitement DiddiPay en cours.
- `succeeded` : retrait confirme, aucune seconde deduction ne doit etre faite.
- `released` : retrait echoue ou rejete, montant restitue au wallet.

Le frontend ne doit jamais recalculer les frais ni le net. Le devis serveur est la seule reference. Un bouton de confirmation doit etre desactive apres le premier envoi, mais une repetition reseau reste sure grace a l'idempotence backend.

## Erreurs utiles

- `WITHDRAWAL_BALANCE_INSUFFICIENT`
- `WITHDRAWAL_QUOTE_NOT_FOUND`
- `WITHDRAWAL_QUOTE_EXPIRED`
- `WITHDRAWAL_QUOTE_ALREADY_USED`
- `WITHDRAWAL_NOT_FOUND`

Les retraits Wave ne doivent pas etre annonces tant que DiddiPay ne confirme pas ce canal de payout. La `beneficiary_reference` doit respecter le format fourni par DiddiPay.
