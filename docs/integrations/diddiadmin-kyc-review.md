# Integration DiddiAdmin - revue KYC/KYV DiddiGo

Date : 2026-10-19

## Objectif

DiddiAdmin affiche les pieces privees via des URLs signees DiddiFiles, puis
envoie la decision metier a DiddiGo. DiddiAdmin ne modifie jamais directement
les tables DiddiGo et ne calcule pas le statut global du dossier.

## Sprints d'integration

### Sprint A - Lecture

1. Lister les dossiers avec `GET /internal/v1/drivers/kyc`.
2. Charger un dossier avec `GET /internal/v1/drivers/{driver_id}/kyc`.
3. Lire `kyc.status`, `kyc.document_reviews`, `vehicle.verification_status` et
   `vehicle.document_reviews`.
4. Demander les URLs signees a DiddiFiles pour visualiser les fichiers prives.

### Sprint B - Decision

1. Permettre une decision par piece.
2. Exiger un motif, une explication et une correction attendue pour chaque rejet.
3. Envoyer la decision avec un `X-Request-ID` et une `Idempotency-Key` uniques.
4. Ne jamais utiliser `suspended` pour representer un rejet documentaire.

### Sprint C - Suivi

1. Afficher `pending_verification`, `approved` ou `rejected` pour le KYC.
2. Apres une resoumission chauffeur, recharger le dossier au lieu de conserver
   localement l'ancien statut.
3. Garder la suspension operationnelle dans un parcours support distinct.

## Authentification S2S

```text
aud=diddigo
scope=diddigo:kyc:read pour la lecture
scope=diddigo:kyc:decide pour les decisions
sub=service:backoffice
X-Client-ID=backoffice-staging-diddigo
X-Backoffice-Actor=<user_id admin DiddiFreeID>
```

`X-User-ID` reste accepte temporairement pour compatibilite legacy, mais les
nouveaux appels doivent utiliser `X-Backoffice-Actor`.

## Rejet KYC

```http
POST /internal/v1/drivers/{driver_id}/kyc/reject
```

```json
{
  "notes": "Controle du dossier chauffeur",
  "documents": [
    {
      "document_type": "national_id_back",
      "decision": "rejected",
      "reason_code": "unreadable",
      "reason": "Le numero est masque par un reflet.",
      "expected_correction": "Reprendre la photo sans flash, a plat et avec les quatre bords visibles."
    },
    {
      "document_type": "selfie",
      "decision": "approved"
    }
  ]
}
```

Un rejet sans piece rejetee, ou sans les trois informations actionnables,
retourne `422`.

## Approbation KYC

```http
POST /internal/v1/drivers/{driver_id}/kyc/approve
```

Le tableau `documents` est optionnel. S'il est fourni, cette route accepte
uniquement `decision=approved`. DiddiGo refuse l'approbation globale tant que
toutes les pieces KYC obligatoires ne sont pas approuvees.

## KYV vehicule

Le Backend Backoffice utilise les routes S2S suivantes :

```text
GET /internal/v1/drivers/vehicles/kyv
GET /internal/v1/drivers/vehicles/{vehicle_id}/kyv
POST /internal/v1/drivers/vehicles/{vehicle_id}/kyv/approve
POST /internal/v1/drivers/vehicles/{vehicle_id}/kyv/reject
```

Elles utilisent les memes structures de decisions. Les types vehicule sont :

```text
registration
insurance
technical_inspection
transport_authorization
vehicle_front
vehicle_back
vehicle_left
vehicle_right
vehicle_interior
vehicle_plate
```

## Erreurs a traiter

| Code | Signification |
|---|---|
| `DOCUMENT_REJECTION_DETAILS_REQUIRED` | Rejet incomplet ou inutilisable par le chauffeur |
| `DOCUMENT_DECISIONS_INCOMPLETE` | Approbation demandee alors que des pieces obligatoires ne sont pas approuvees |
| `INVALID_DOCUMENT_TYPE` | Type de piece incompatible avec KYC ou KYV |
| `DUPLICATE_DOCUMENT_DECISION` | Meme piece presente plusieurs fois |
| `IDEMPOTENCY_CONFLICT` | Reutilisation d'une cle avec un payload different |

## Ordre de deploiement

1. Deployer DiddiGo et sa migration Alembic.
2. Verifier le nouveau schema dans `/openapi.json`.
3. Deployer DiddiAdmin avec le payload structure.
4. Tester rejet, affichage chauffeur, resoumission et approbation finale.
