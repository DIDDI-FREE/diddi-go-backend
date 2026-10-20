# DiddiGo - Checklist DiddiSupport

Edition : `2026-10-20`

Version du registre : `2026-10-20.v1`

Branche de reference : `stage`

## Objet

Cette checklist valide le connecteur DiddiSupport vers DiddiGo. Elle couvre
uniquement le contexte de course en lecture seule :

```text
GET /internal/v1/support/ride/{ride_id}/context
```

Le contrat retourne `diddi.context.v1`. DiddiGo reste proprietaire de la
course ; DiddiSupport ne lit ni n'ecrit les tables DiddiGo.

## Legende et preuves

- `[ ]` : non execute.
- `[x]` : valide avec une preuve reproductible.
- `[!]` : bloque ; decrire le blocage dans le journal.
- `[~]` : partiellement valide.

Ne jamais inscrire un JWT, un client secret, un telephone complet, une adresse
ou une URL signee dans ce fichier. Conserver seulement `request_id`, `ride_id`
de recette, heure UTC et resultat.

## Prerequis staging

- Client DiddiFreeID : `diddisupport-staging-diddigo`.
- JWT S2S : `aud=diddigo`, `sub=service:diddisupport`,
  `scope=diddigo:support-context:read`, `status=active`.
- En-tetes : `Authorization`, `X-Client-ID`, `X-Request-ID` et
  `X-Support-Context-Scope: diddigo:support-context:read`.
- Une course de recette connue, terminee et une course inexistante UUID.
- URL du connecteur DiddiSupport configuree vers l'adresse interne DiddiGo ;
  utiliser l'URL staging seulement si aucun reseau interne n'est disponible.

## A. Tests unitaires DiddiGo

Commande :

```powershell
uv run pytest tests/test_support_context_resolver.py tests/test_support_context_router.py -q
```

| ID | Verification | Etat | Preuve |
| --- | --- | --- | --- |
| UT-SUP-01 | Une course terminee retourne `protocol=diddi.context.v1`, `origin_service=diddigo`, `resource_type=ride` et le bon `resource_id`. | `[x]` | `test_support_context_router.py` |
| UT-SUP-02 | Le contexte retourne statut, montant, devise, moyen de paiement, participants et timeline. | `[x]` | `test_support_context_resolver.py` |
| UT-SUP-03 | `final_fare` est prefere a `estimated_fare`; le devis reste le fallback lorsque le prix final est absent. | `[x]` | `test_support_context_resolver.py` |
| UT-SUP-04 | Les telephones, positions, adresses, KYC/KYV et details fournisseur ne sont pas dans `data`; ils sont declares dans `redacted_fields`. | `[x]` | `test_support_context_router.py` |
| UT-SUP-05 | Sans Bearer token, la route retourne `401 TOKEN_MISSING`. | `[x]` | `test_support_context_router.py` |
| UT-SUP-06 | Sans `X-Support-Context-Scope`, ou avec une valeur differente, la route retourne `403 SERVICE_SCOPE_HEADER_INVALID`. | `[x]` | `test_support_context_router.py` |
| UT-SUP-07 | Un JWT sans scope retourne `403 SERVICE_SCOPE_INVALID`. | `[x]` | `test_support_context_router.py` |
| UT-SUP-08 | Un client different de `diddisupport-staging-diddigo` retourne `403 SERVICE_CLIENT_FORBIDDEN`. | `[ ]` | Ajouter test explicite ou preuve de `test_service_token_verifier.py`. |
| UT-SUP-09 | Un sujet different de `service:diddisupport` retourne `403`. | `[ ]` | Ajouter test explicite. |
| UT-SUP-10 | JWKS indisponible retourne `503 SERVICE_JWKS_UNAVAILABLE`, sans reponse partielle. | `[x]` | `test_support_context_router.py` |
| UT-SUP-11 | Course inconnue retourne `404 RIDE_NOT_FOUND`. | `[x]` | Tests resolver et routeur. |
| UT-SUP-12 | `X-Request-ID` est retourne et le log `support.context.ride.fetched` est emis sans PII. | `[x]` | `test_support_context_router.py` |
| UT-SUP-13 | OpenAPI declare le header de protocole et le schema `SupportRideContextResponse`. | `[x]` | `test_support_context_router.py` |

## B. Tests d'integration locale / CI

Prerequis : PostgreSQL, migrations a jour, Redis si l'environnement de test le
demande et un JWKS DiddiFreeID de test. Ne pas utiliser de secrets staging.

| ID | Scenario | Etat | Preuve |
| --- | --- | --- | --- |
| IT-SUP-01 | Appliquer `alembic upgrade head`, creer une course complete avec chauffeur affecte, puis appeler le resolver avec une vraie session PostgreSQL. | `[ ]` | |
| IT-SUP-02 | Verifier que le `user_id` du chauffeur vient du profil chauffeur et non du `driver_id` interne. | `[ ]` | |
| IT-SUP-03 | Verifier une course sans chauffeur : seul le passager est retourne, sans erreur. | `[ ]` | |
| IT-SUP-04 | Verifier une course annulee et une course terminee : `cancellation_reason`, `completion_reason` et `as_of` sont coherents. | `[ ]` | |
| IT-SUP-05 | Signer un JWT de test conforme et valider issuer, audience, subject, status, client id et scope. | `[ ]` | |
| IT-SUP-06 | Rejouer la meme lecture avec le meme `X-Request-ID` : lecture stable, sans mutation ni nouvel evenement metier. | `[ ]` | |
| IT-SUP-07 | Capturer les logs et verifier qu'aucun telephone, coordonnee, token ou detail de paiement n'est journalise. | `[ ]` | |

## C. Recette staging S2S

| ID | Scenario | Etat | Preuve a renseigner |
| --- | --- | --- | --- |
| STG-SUP-00 | Noter le commit/image DiddiGo, version DiddiSupport et heure UTC de la recette. | `[ ]` | |
| STG-SUP-01 | Verifier `/health` puis `/openapi.json`; la route interne Support doit etre exposee. | `[x]` | 2026-10-20 : `/health=200`, route exposee. |
| STG-SUP-02 | Obtenir un token DiddiFreeID S2S conforme pour DiddiSupport, sans le coller dans le rapport. | `[ ]` | |
| STG-SUP-03 | Appeler le contexte d'une course de recette terminee et verifier tous les champs obligatoires. | `[ ]` | `request_id`, `ride_id`, HTTP. |
| STG-SUP-04 | Verifier `redacted_fields` et confirmer l'absence de telephone, GPS, adresse, KYC et details processeur. | `[ ]` | |
| STG-SUP-05 | Envoyer un token absent : `401 TOKEN_MISSING`. | `[ ]` | |
| STG-SUP-06 | Envoyer le bon JWT avec mauvais `X-Client-ID` : `403 SERVICE_CLIENT_FORBIDDEN`. | `[ ]` | |
| STG-SUP-07 | Envoyer le bon JWT sans le header scope : `403 SERVICE_SCOPE_HEADER_INVALID`. | `[ ]` | |
| STG-SUP-08 | Envoyer un token sans `diddigo:support-context:read` : `403 SERVICE_SCOPE_INVALID`. | `[ ]` | |
| STG-SUP-09 | Appeler un UUID inexistant : `404 RIDE_NOT_FOUND`. | `[ ]` | |
| STG-SUP-10 | Correlation : retrouver le `request_id` dans les logs DiddiGo, sans PII. | `[ ]` | |

## D. E2E DiddiSupport / Backoffice

| ID | Scenario | Etat | Preuve a renseigner |
| --- | --- | --- | --- |
| E2E-SUP-01 | Un utilisateur cree un dossier Support lie a une course de recette. | `[ ]` | `case_id`, `ride_id`. |
| E2E-SUP-02 | DiddiSupport recupere automatiquement le contexte DiddiGo avec son token S2S. | `[ ]` | `request_id` DiddiGo. |
| E2E-SUP-03 | Le Backoffice voit le statut, montant, devise, timeline et participants pseudonymises. | `[ ]` | Capture anonymisee. |
| E2E-SUP-04 | Le Backoffice ne voit ni telephone, adresse, position GPS, KYC ni detail processeur. | `[ ]` | Capture anonymisee. |
| E2E-SUP-05 | Une course inexistante produit une erreur lisible, sans creer un contexte vide ou un faux dossier. | `[ ]` | |
| E2E-SUP-06 | Une indisponibilite JWKS/DiddiGo produit un etat retryable et conserve le dossier Support. | `[ ]` | |
| E2E-SUP-07 | Chaque consultation est tracable par `case_id`, `ride_id` et `request_id`, sans secret. | `[ ]` | |

## Gate de validation

Le connecteur est pret pour activation quand :

1. `UT-SUP-01` a `UT-SUP-13` sont verts ou les exceptions sont corrigees ;
2. `IT-SUP-01` a `IT-SUP-07` sont executes en CI/integration ;
3. `STG-SUP-03` a `STG-SUP-10` sont verts avec un vrai token S2S ;
4. `E2E-SUP-01` a `E2E-SUP-07` confirment l'affichage redige dans Backoffice.

## Journal des executions

| Date UTC | Environnement | Lots executes | Resultat | Preuve / blocage | Responsable |
| --- | --- | --- | --- | --- | --- |
| 2026-10-20 | local | UT-SUP-01 a UT-SUP-07, UT-SUP-10 a UT-SUP-13 | `[x]` | Tests existants `test_support_context_resolver.py` et `test_support_context_router.py` | Codex |
| 2026-10-20 | staging | STG-SUP-01 | `[x]` | `/health=200`, route dans OpenAPI | Codex |
