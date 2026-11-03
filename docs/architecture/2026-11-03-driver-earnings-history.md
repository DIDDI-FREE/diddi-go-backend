# Journal d'implémentation - Historique de gains chauffeur

**Date :** 3 novembre 2026
**Fonctionnalité :** agrégats wallet chauffeur par jour, semaine et mois
**Statut :** implémenté et validé localement sur PostgreSQL

## Décision appliquée

Le ledger reste le détail paginé des écritures. Le tableau de bord ne le
recalcule pas côté application : DiddiGo retourne des agrégats financiers en
heure `Africa/Abidjan`.

## Source des montants

- `ride_earnings_xof` et `platform_commissions_xof` viennent des courses dont
  le paiement est confirmé. Cette règle couvre aussi les courses cash : le
  gain cash ne figure pas comme crédit wallet.
- `withdrawals_succeeded_xof` vient des retraits effectivement réussis.
- `available_balance_xof` vient du wallet courant et ne représente pas les
  gains de la période.
- `pending_or_disputed_xof` reste distinct et n'est jamais présenté comme un
  gain acquis.

## Contrat livré

```text
GET /v1/drivers/me/wallet/earnings?period=day|week|month&from=YYYY-MM-DD&to=YYYY-MM-DD
```

Les bornes sont des dates locales Abidjan inclusives. La plage maximale est de
366 jours pour éviter les scans non bornés. Le JWT identifie toujours le
chauffeur concerné ; aucun `driver_id` client n'est accepté.

## Validation exécutée

- Tests unitaires de périodes, bornes Abidjan et autorisation chauffeur.
- Tests PostgreSQL réels couvrant une course cash, une course numérique,
  une transaction en attente et un retrait réussi.
- Test HTTP de la réponse typée.
- Lint, génération OpenAPI et build MkDocs strict.

## Hors périmètre

- Tarification par zone et carte de demande.
- Gestion autonome par les partenaires.
- Comptabilité PSP et settlements DiddiPay.
