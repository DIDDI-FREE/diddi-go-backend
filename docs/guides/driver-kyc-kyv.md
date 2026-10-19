# KYC chauffeur et KYV vehicule

DiddiFiles stocke les pieces ; DiddiGo stocke les `file_id` et decide du
statut metier. Le frontend ne valide jamais un dossier.

Le chauffeur cree son profil, envoie ses documents, cree son vehicule puis
soumet KYC/KYV. Un admin DiddiGo approuve ou rejette. Un dossier rejete est
corrige puis soumis a nouveau.

## Statuts et decisions

Le statut operationnel du chauffeur et le statut de son dossier sont distincts.
Un rejet documentaire ne devient pas une suspension : `kyc.status` vaut
`pending_verification`, `approved` ou `rejected`.

Chaque piece decidee expose son statut, un code motif, une explication, la
correction attendue et la date de decision. Pour un rejet, le Backoffice doit
identifier au moins une piece et fournir `reason_code`, `reason` et
`expected_correction`. L'identite du reviewer reste dans l'audit interne.

`POST /v1/drivers/kyc/resubmit` remet uniquement les pieces personnelles
renvoyees en attente. `POST /v1/drivers/vehicles/{vehicle_id}/kyv/resubmit`
fait de meme pour les pieces du vehicule ; les autres decisions sont conservees.

La regle d'age minimum de 21 ans est hors MVP et n'est pas appliquee.

Le `vehicle_id` utilise par `/drivers/vehicles/{vehicle_id}/kyv/resubmit` est
le champ `vehicle.id` retourne par `GET /v1/drivers/me`.

Les six vues obligatoires sont : avant, arriere, gauche, droite, interieur et
plaque. La matrice des purposes est dans `integrations/diddifiles.md`.
