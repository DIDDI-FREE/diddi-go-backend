# Message à l’équipe DiddiRewards — raccordement DiddiGo

Bonjour,

DiddiGo a terminé son lot d’améliorations Rewards sur la branche :

```text
codex/diddigo-rewards-improvements-2026-11-24
```

La branche a été poussée sur le dépôt DiddiGo. La référence DiddiGo reste
`stage`; aucun déploiement Portainer n’a été effectué par ce lot.

## Contrat à implémenter côté DiddiRewards

DiddiGo appelle le endpoint suivant pour libérer une réservation qui n’a pas
été consommée :

```http
POST /internal/v1/rewards/integrations/diddigo/benefits/release
Authorization: Bearer <service-token>
X-Client-ID: diddigo
X-Request-ID: <request-id>
Idempotency-Key: diddigo:ride:<ride-id>:rewards-release:v1
Content-Type: application/json
```

Payload :

```json
{
  "reservation_id": "uuid",
  "ride_id": "uuid",
  "reason": "no_driver_found"
}
```

Réponse attendue proposée :

- `204` : réservation libérée ;
- répétition avec la même clé : succès idempotent ;
- `409` : réservation déjà consommée ;
- `404` : réservation inconnue.

Le scope S2S requis est :

```text
diddirewards:benefits:release
```

## Quand DiddiGo appelle release

- `no_driver_found` ;
- `cancelled_by_passenger` ;
- `cancelled_by_driver`.

Une réservation non consommée est libérée. Une consommation déjà confirmée
reste traitée par `correct` après remboursement ou annulation financière.

## Événements et réconciliation

DiddiGo conserve l’outbox SQL et le worker Redis existants. Les événements sont
publiés sur :

```text
diddigo.events.v1
```

Les identifiants d’événements incluent désormais le type, la course et la
transaction de paiement afin de distinguer plusieurs opérations légitimes sur
une même course.

## Vérifications demandées à DiddiRewards

1. Confirmer que le endpoint `release` est disponible avec le scope indiqué.
2. Confirmer le comportement `204`, `404`, `409` et l’idempotence.
3. Confirmer que le consumer Rewards lit `diddigo.events.v1`.
4. Exécuter une recette avec une remise, un paiement et une annulation sans paiement.
5. Retourner les identifiants de corrélation et le résultat de traitement.

Les tests locaux DiddiGo sont verts : lint, compilation et 453 tests unitaires.
Le contrat complet est documenté dans `docs/DIDDIREWARDS-INTEGRATION.md`.

Merci de confirmer la prise en charge du contrat release et la validation du
stream côté DiddiRewards.
