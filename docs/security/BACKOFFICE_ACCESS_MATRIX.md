# Contrat d'acces Backoffice DiddiGo

## Regle

Le navigateur ne recoit jamais le secret du client S2S. Le Backend Backoffice
obtient un jeton de service DiddiFreeID, puis appelle les routes internes
DiddiGo au nom d'un administrateur humain explicite. DiddiGo valide a la fois le
scope du service et le statut admin actif de cet acteur local.

Les routes historiques `/v1` avec JWT humain admin restent disponibles pendant
la migration. Le parametre d'URL, le frontend et `X-Client-ID` ne peuvent jamais
attribuer le role admin.

## Matrice V1

| Action | Route | Authentification | Permission cible |
| --- | --- | --- | --- |
| Lire le manifeste | `GET /internal/backoffice/v1/manifest` | JWT service Backoffice + `X-Client-ID` | `diddigo:operations:read` |
| Lire la file KYC | `GET /internal/v1/drivers/kyc` | JWT service + `X-Client-ID` | `diddigo:kyc:read` |
| Lire un dossier KYC | `GET /internal/v1/drivers/{id}/kyc` | JWT service + `X-Client-ID` | `diddigo:kyc:read` |
| Decider un KYC | `POST /internal/v1/drivers/{id}/kyc/{approve,reject}` | JWT service + acteur/audit/idempotence | `diddigo:kyc:decide` |
| Provisionner un chauffeur | `POST /internal/v1/drivers/provision` | JWT service + acteur/audit/idempotence | `diddigo:drivers:write` |
| Lire la file KYV | `GET /v1/admin/vehicles/kyv` | JWT humain admin | `diddigo:kyc:read` |
| Decider un KYV | routes `kyv/approve` et `kyv/reject` | JWT humain admin | `diddigo:kyc:decide` |
| Lire les courses | `GET /v1/rides` | JWT humain admin | `diddigo:rides:read` |
| Annuler une course | `POST /v1/rides/{id}/cancel` | JWT humain admin + regle metier | `diddigo:rides:cancel` |
| Lire wallet/ledger | `GET /v1/admin/drivers/{id}/wallet*` | JWT humain admin | `diddigo:wallets:read` |
| Reconciliation | `POST /v1/admin/payments/*/reconcile` | JWT humain admin | `diddigo:payments:reconcile` |

Les lignes KYV, courses, wallet et paiements documentent encore la cible. Le
KYC chauffeur et le provisioning du profil chauffeur disposent de routes S2S
synchrones dans cette version.

## Client S2S Backoffice

Le client S2S doit utiliser `aud=diddigo`, `role=service`, `token_type=service`,
`status=active`, un `X-Client-ID` identique au claim `client_id`, et uniquement
des scopes `diddigo:*` autorises par DiddiFreeID.

Toutes les routes Backoffice S2S exigent aussi `sub=service:backoffice`.

Pour une decision KYC, le Backend Backoffice doit aussi transmettre :

- `X-Backoffice-Actor`: identifiant DiddiFreeID de l'admin humain ayant decide;
- `X-User-ID`: alias legacy temporaire de `X-Backoffice-Actor`;
- `X-Request-ID`: identifiant de correlation;
- `Idempotency-Key`: cle stable lors des reprises de la meme commande.

Au moins un des deux en-tetes acteur est requis. Si les deux sont presents, ils
doivent contenir le meme identifiant, sinon la commande est rejetee. Aucun de
ces en-tetes n'accorde un droit seul : DiddiGo charge son shadow user et exige
`role=admin` et `status=active`. Une cle d'idempotence reutilisee avec un contenu
different est rejetee. La reponse d'une commande terminee est rejouee sans
executer une seconde decision.

Chaque mutation S2S terminee est aussi inscrite dans
`audit.backoffice_events`, dans la meme transaction PostgreSQL que la mutation
metier. L'audit conserve le client et le sujet du service, l'admin humain,
l'action, la cible, `X-Request-ID`, `Idempotency-Key`, le motif et le resultat.
La contrainte `(client_id, action, idempotency_key)` garantit qu'une reprise ne
cree pas une seconde trace. Les logs applicatifs contiennent l'`audit_id` pour
relier diagnostic technique et historique persistant.

Pour le provisioning, le Backoffice doit d'abord rechercher et valider
l'identite dans DiddiFreeID. DiddiGo fait confiance au contexte transmis par ce
client S2S autorise et cree uniquement son shadow technique et son profil metier
`pending_verification`; il ne cree aucun compte global et ne rend pas le
chauffeur eligible aux courses.

## Erreurs attendues

- `401`: token absent, invalide ou expire;
- `400`: en-tetes acteur canonique et legacy contradictoires;
- `403`: role ou scope insuffisant;
- `404`: ressource metier absente;
- `409`: commande deja en cours ou cle d'idempotence reutilisee autrement;
- `422`: UUID, statut ou payload invalide;
- `5xx`: dependance indisponible, avec `X-Request-ID` pour diagnostic.
