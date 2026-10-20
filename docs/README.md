# Documentation DiddiGo

Cette documentation est la reference humaine du module DiddiGo. L'OpenAPI
decrit les routes et schemas ; les guides expliquent les parcours et les
regles metier.

## Navigation

- Contrat HTTP et WebSocket : [`api/API_CONTRACT.md`](api/API_CONTRACT.md)
- Spécifications : [`api/openapi.yaml`](api/openapi.yaml) et [`api/asyncapi.yaml`](api/asyncapi.yaml)
- Décisions et lacunes : [`api/open-questions.md`](api/open-questions.md)
- Parcours : [`guides/passenger-ride-flow.md`](guides/passenger-ride-flow.md),
  [`guides/driver-ride-flow.md`](guides/driver-ride-flow.md),
  [`guides/driver-kyc-kyv.md`](guides/driver-kyc-kyv.md),
  [`guides/payments-wallet.md`](guides/payments-wallet.md),
  [`guides/sos-safety.md`](guides/sos-safety.md)
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

- Une modification HTTP ou WebSocket exige d'exécuter `tools/generate_api_contract.py` depuis la racine : les deux YAML et les blocs générés sont actualisés, les décisions humaines conservées.
- Une modification fonctionnelle exige de mettre a jour le guide concerne et
  `changelog/<date>.md` dans la meme pull request.
- Un nouveau document n'est cree que s'il ne rentre dans aucune rubrique
  existante de cette arborescence.
