# KYC chauffeur et KYV vehicule

DiddiFiles stocke les pieces ; DiddiGo stocke les `file_id` et decide du
statut metier. Le frontend ne valide jamais un dossier.

Le chauffeur cree son profil, envoie ses documents, cree son vehicule puis
soumet KYC/KYV. Un admin DiddiGo approuve ou rejette. Un dossier rejete est
corrige puis soumis a nouveau.

Le `vehicle_id` utilise par `/drivers/vehicles/{vehicle_id}/kyv/resubmit` est
le champ `vehicle.id` retourne par `GET /v1/drivers/me`.

Les six vues obligatoires sont : avant, arriere, gauche, droite, interieur et
plaque. La matrice des purposes est dans `integrations/diddifiles.md`.
