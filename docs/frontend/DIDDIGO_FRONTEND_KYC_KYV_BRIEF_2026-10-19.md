# DiddiGo - Brief frontend KYC/KYV

Date : 2026-10-19

## Changement principal

Le statut operationnel du chauffeur est maintenant distinct du statut KYC.
Utiliser `kyc.status` pour l'ecran dossier :

- `pending_verification` : dossier en cours de verification ;
- `approved` : dossier approuve ;
- `rejected` : au moins une piece doit etre corrigee.

Ne plus interpreter `driver.status=suspended` comme un refus KYC. Une
suspension est un blocage operationnel distinct qui doit orienter vers le support.

## Lecture du dossier

`GET /v1/drivers/me` est la source DiddiGo du profil chauffeur. La reponse est
maintenant typee dans OpenAPI. Le bloc `kyc.document_reviews` et le bloc
`vehicle.document_reviews` contiennent les decisions par piece.

Exemple :

```json
{
  "document_type": "national_id_back",
  "status": "rejected",
  "reason_code": "unreadable",
  "reason": "Le numero est masque par un reflet.",
  "expected_correction": "Reprendre la photo sans flash.",
  "reviewed_at": "2026-10-19T14:30:00Z"
}
```

Pour chaque piece rejetee, afficher le motif et `expected_correction`. Ne pas
demander au chauffeur de reprendre les pieces deja approuvees.

## Correction et resoumission

- Piece personnelle : `POST /v1/drivers/kyc/resubmit`.
- Piece vehicule : `POST /v1/drivers/vehicles/{vehicle_id}/kyv/resubmit`.
- Informations descriptives du vehicule : `PUT /v1/drivers/me/vehicle`.

Une resoumission remet uniquement les pieces envoyees a `pending`. Le dossier
global repasse a `pending_verification`. Recharger `GET /v1/drivers/me` pour
rafraichir l'ecran. `/v1/pro/metiers` n'est pas une route DiddiGo livree et ne
doit pas etre appelee.

La carte grise se renvoie avec `registration_document_file_id`. Le `vehicle_id`
et les identifiants des six photos sont disponibles dans `GET /v1/drivers/me`.

## Pieces MVP

KYC obligatoire : permis recto/verso, CNI recto/verso et selfie.

KYV obligatoire : carte grise, assurance, controle technique et six photos
(avant, arriere, gauche, droite, interieur, plaque). L'autorisation de transport
est stockee mais n'est pas bloquante actuellement.

Les purposes DiddiFiles du dossier chauffeur sont publies. Utiliser la matrice
de `docs/integrations/diddifiles.md`, notamment :

- `diddigo_driver_kyc_license_back` ;
- `diddigo_driver_kyc_national_id_back` ;
- `diddigo_vehicle_insurance` ;
- `diddigo_vehicle_technical_inspection` ;
- `diddigo_vehicle_transport_authorization`.

## Statut KYV vehicule

`vehicle.verification_status` est toujours l'une de ces valeurs :

- `pending_verification` : documents en attente de revue ;
- `active` : vehicule KYV valide et utilisable, sous reserve des autres regles
  d'eligibilite chauffeur ;
- `rejected` : au moins une piece doit etre corrigee ;
- `suspended` : blocage operationnel distinct du rejet documentaire.

Ne pas attendre la valeur `approved` pour un vehicule : la valeur contractuelle
de validation est `active`.

## Hors MVP

- controle serveur d'un age minimum de 21 ans ;
- promesse de traitement en 6 h ou 48 h ;
- affichage au chauffeur de l'identite de l'administrateur ayant decide.
