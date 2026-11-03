# Brief frontend - Historique de gains chauffeur

**Version :** 3 novembre 2026
**Statut :** route backend ajoutée, validation staging à effectuer

## Route

```text
GET /v1/drivers/me/wallet/earnings?period=day|week|month&from=YYYY-MM-DD&to=YYYY-MM-DD
```

Le JWT du chauffeur suffit. L'application ne transmet jamais un `driver_id`.
`from` et `to` sont inclusifs, en calendrier Abidjan, avec une plage maximale
de 366 jours.

## Affichage

- Afficher `ride_earnings_xof` comme les gains de courses acquis.
- Afficher `platform_commissions_xof` séparément.
- Afficher `withdrawals_succeeded_xof` comme des retraits, jamais comme un
  gain.
- Afficher `pending_or_disputed_xof` comme « en attente de confirmation ».
- Afficher `available_balance_xof` comme le solde actuellement retirable selon
  les autres règles wallet.

`buckets` contient les valeurs à dessiner pour la granularité demandée. Ne pas
additionner le ledger localement et ne pas présenter une recharge comme un
gain.
