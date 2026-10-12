# Documentation DiddiGo

Cette documentation est la reference humaine du module DiddiGo. L'OpenAPI
decrit les routes et schemas ; les guides expliquent les parcours et les
regles metier.

## Navigation

- API : [`api/openapi.json`](api/openapi.json) et [`api/error-catalog.md`](api/error-catalog.md)
- Parcours : [`guides/passenger-ride-flow.md`](guides/passenger-ride-flow.md),
  [`guides/driver-ride-flow.md`](guides/driver-ride-flow.md),
  [`guides/driver-kyc-kyv.md`](guides/driver-kyc-kyv.md),
  [`guides/payments-wallet.md`](guides/payments-wallet.md),
  [`guides/sos-safety.md`](guides/sos-safety.md)
- Temps reel : [`realtime/websocket-contract.md`](realtime/websocket-contract.md) et
  [`realtime/reconnection-strategy.md`](realtime/reconnection-strategy.md)
- Integrations : [`integrations/diddifiles.md`](integrations/diddifiles.md),
  [`integrations/diddipay.md`](integrations/diddipay.md),
  [`integrations/diddimap.md`](integrations/diddimap.md),
  [`integrations/diddicomms.md`](integrations/diddicomms.md)
- References : [`reference/statuses.md`](reference/statuses.md),
  [`reference/configuration.md`](reference/configuration.md),
  [`reference/permissions.md`](reference/permissions.md)
- Changements : [`changelog/2026-10-12.md`](changelog/2026-10-12.md)

Les documents dans `archive/` sont historiques et ne definissent plus le
comportement courant.

## Regles de maintenance

- Une modification HTTP exige de regenerer `api/openapi.json`.
- Une modification fonctionnelle exige de mettre a jour le guide concerne et
  `changelog/<date>.md` dans la meme pull request.
- Un nouveau document n'est cree que s'il ne rentre dans aucune rubrique
  existante de cette arborescence.
