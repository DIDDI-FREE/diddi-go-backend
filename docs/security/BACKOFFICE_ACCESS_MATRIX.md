# Contrat d'acces Backoffice DiddiGo

## Regle

Le Backoffice interactif utilise un JWT humain DiddiFreeID avec `role=admin`.
Le parametre d'URL, le frontend et `X-Client-ID` ne peuvent jamais attribuer ce
role. DiddiGo reste responsable des controles metier et de l'audit.

## Matrice V1

| Action | Route | Authentification | Permission cible |
| --- | --- | --- | --- |
| Lire la file KYC | `GET /v1/drivers/kyc` | JWT humain admin | `diddigo:kyc:read` |
| Lire un dossier KYC | `GET /v1/drivers/{id}/kyc` | JWT humain admin | `diddigo:kyc:read` |
| Decider un KYC | `POST /v1/drivers/{id}/kyc/{approve,reject}` | JWT humain admin | `diddigo:kyc:decide` |
| Lire la file KYV | `GET /v1/admin/vehicles/kyv` | JWT humain admin | `diddigo:kyc:read` |
| Decider un KYV | routes `kyv/approve` et `kyv/reject` | JWT humain admin | `diddigo:kyc:decide` |
| Lire les courses | `GET /v1/rides` | JWT humain admin | `diddigo:rides:read` |
| Annuler une course | `POST /v1/rides/{id}/cancel` | JWT humain admin + regle metier | `diddigo:rides:cancel` |
| Lire wallet/ledger | `GET /v1/admin/drivers/{id}/wallet*` | JWT humain admin | `diddigo:wallets:read` |
| Reconciliation | `POST /v1/admin/payments/*/reconcile` | JWT humain admin | `diddigo:payments:reconcile` |

Les permissions cibles documentent la future equivalence S2S. Elles ne rendent
pas les routes synchrones accessibles au client service Backoffice aujourd'hui.

## Client S2S Backoffice

Le client S2S doit utiliser `aud=diddigo`, `role=service`, `token_type=service`,
`status=active`, un `X-Client-ID` identique au claim `client_id`, et uniquement
des scopes `diddigo:*` autorises par DiddiFreeID.

Il sera limite aux commandes asynchrones lorsque ces routes et leur mecanisme
d'idempotence existeront. Un token S2S ne remplace jamais un JWT admin humain
sur les routes ci-dessus.

## Erreurs attendues

- `401`: token absent, invalide ou expire;
- `403`: role ou scope insuffisant;
- `404`: ressource metier absente;
- `422`: UUID, statut ou payload invalide;
- `5xx`: dependance indisponible, avec `X-Request-ID` pour diagnostic.
