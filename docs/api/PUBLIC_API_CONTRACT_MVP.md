# Contrat API public DiddiGo - MVP

**Version :** `mvp.2026-10-14`

**Clients :** applications passager et chauffeur

**Auth :** JWT utilisateur DiddiFreeID

Ce document décrit les règles métier stables. Les schémas HTTP exhaustifs restent dans `openapi.json`.

## Devis et création

1. `POST /v1/rides/pricing/estimate` retourne `quote_id` et `expires_at`.
2. Le devis expire après 15 minutes et ne peut servir qu'une fois.
3. `POST /v1/rides` exige ce `quote_id` et `payment_method=cash|mobile_money`.
4. Changer pickup, dropoff, catégorie ou confort exige un nouveau devis. Changer le réseau Mobile Money n'invalide pas le devis.

## Paiement

- `cash` : après la course, seul le chauffeur confirme avec `POST /v1/payments/{ride_id}/confirm-cash`.
- `mobile_money` : `POST /v1/payments/{ride_id}/prepare` exige `mobile_money_network=orange|wave|mtn`.
- DiddiPay est le fournisseur technique, pas une méthode affichée à l'utilisateur.
- Si l'e-mail DiddiFreeID est indisponible, DiddiGo utilise `<telephone>@diddifree.com` uniquement pour le paiement.
- Une intention échouée ou expirée peut être remplacée. Une intention active est réutilisée.

## Prix final

Course normale : `devis figé + attente pré-course + attente en course + suppléments acceptés`.

La trace GPS chauffeur alimente l'audit et l'algorithme sans changer le devis d'une course normale.

## Arrêt anticipé

1. Le passager appelle `POST /v1/rides/{ride_id}/early-stop/request`.
2. Le montant retourné est provisoire et la demande expire après deux minutes.
3. Le chauffeur appelle `POST /v1/rides/{ride_id}/early-stop/confirm`.
4. Le prix définitif utilise la trace chauffeur : base + distance réelle + durée réelle + attentes + suppléments. Le minimum est `base_fare` et le multiplicateur du devis reste figé.
5. La course termine avec `status=completed` et `completion_reason=early_stop`.

## Démarrage

Le passager montre le code à six chiffres ou un QR généré localement avec `ride_id + code`. Le chauffeur utilise toujours `POST /v1/rides/{ride_id}/start`. Aucun endpoint QR supplémentaire n'existe.

## Hors MVP déjà exposé

Les routes d'escales restent visibles mais ne doivent pas être intégrées au lancement MVP. Leur présence dans OpenAPI ne constitue pas une activation produit.
