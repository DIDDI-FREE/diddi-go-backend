# DiddiGo - Acces frontend aux contrats

Date : 2026-10-19

## But

Ce document indique ou trouver chaque contrat DiddiGo et lequel doit faire
foi pendant l'integration frontend.

Le frontend ne doit pas deduire les comportements depuis les ecrans, les logs
ou le code backend. Il doit utiliser les contrats publies et les guides de
parcours.

## HTTP : routes, schemas et erreurs

Utiliser en staging :

- Swagger : <https://go-staging.diddifree.com/docs>
- ReDoc : <https://go-staging.diddifree.com/redoc>
- OpenAPI JSON : <https://go-staging.diddifree.com/openapi.json>

`openapi.json` est la source de verite pour les routes effectivement deployees
en staging. Il permet de connaitre les chemins, methodes HTTP, parametres,
payloads et schemas de reponse.

Une route presente dans le depot mais absente de `openapi.json` ne doit pas
etre utilisee par l'application : elle n'est pas encore livree sur cet
environnement.

## Temps reel : WebSocket

Le WebSocket applicatif est :

```text
wss://go-staging.diddifree.com/v1/ws?token=<access_token>
```

Le jeton est le JWT utilisateur DiddiFreeID. Une authentification invalide est
rejetee en HTTP `403` pendant le handshake. Si un jeton devient invalide apres
connexion, le serveur peut fermer la connexion avec le code `4401`.

Le contrat des evenements et de leurs payloads est dans :

- `docs/api/asyncapi.yaml` : specification AsyncAPI lisible par les outils ;
- `docs/realtime/websocket-contract.md` : explication des evenements ;
- `docs/realtime/reconnection-strategy.md` : strategie de reconnexion.

Ne jamais inventer un evenement, une propriete ou une frequence d'envoi. Une
mise a jour de course doit toujours pouvoir etre reconciliee avec
`GET /v1/rides/{ride_id}` apres reconnexion.

## Guides de parcours

Les guides expliquent l'ordre des appels et les regles UX qui ne tiennent pas
dans OpenAPI :

| Besoin | Guide |
| --- | --- |
| Course passager | `docs/guides/passenger-ride-flow.md` |
| Course chauffeur | `docs/guides/driver-ride-flow.md` |
| Dossier chauffeur KYC/KYV | `docs/guides/driver-kyc-kyv.md` |
| Paiement et wallet | `docs/guides/payments-wallet.md` |
| SOS et securite | `docs/guides/sos-safety.md` |
| DiddiFiles | `docs/integrations/diddifiles.md` |
| DiddiPay | `docs/integrations/diddipay.md` |
| DiddiMap | `docs/integrations/diddimap.md` |
| DiddiComms | `docs/integrations/diddicomms.md` |

Le brief KYC/KYV courant est
`docs/frontend/DIDDIGO_FRONTEND_KYC_KYV_BRIEF_2026-10-19.md`.

## Portail documentaire

La cible de lecture unique est :

```text
https://docs-go-staging.diddifree.com/
```

Ce portail MkDocs doit publier les guides, les contrats OpenAPI/AsyncAPI, les
integrations et les changelogs. Au 19 octobre 2026, son certificat SSL ne
permet pas encore son utilisation. En attendant sa correction, lire ces
documents directement dans le depot Git et utiliser les URLs staging pour
Swagger/OpenAPI.

## Regle de priorite

En cas de divergence :

1. `openapi.json` staging decide si une route HTTP est livree ;
2. AsyncAPI decide le nom et la forme d'un evenement WebSocket ;
3. le guide correspondant decide le workflow et l'UX ;
4. le changelog date explique les changements recents ;
5. une ambiguite ou un manque est remonte au backend avant implementation.

## Ce qui reste a completer

OpenAPI doit encore declarer de maniere exhaustive :

- `X-Client-ID` requis sur les routes S2S ;
- les reponses metier `401`, `403` et `409` ;
- les scopes S2S exiges par route.

Ces elements concernent surtout DiddiAdmin et les autres services internes. Ils
ne doivent pas etre devines par l'application passager ou chauffeur.
