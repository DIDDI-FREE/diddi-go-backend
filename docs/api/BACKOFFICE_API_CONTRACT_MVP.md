# Contrat API Backoffice DiddiGo - MVP

**Version :** `mvp.2026-10-14`

**Surface :** routes `/v1/admin/*`

Le Backoffice utilise un administrateur humain DiddiFreeID ou les routes S2S explicitement prévues. Un paramètre de requête ne devient jamais un rôle d'autorisation.

Fonctions disponibles : validation KYC/KYV, partenaires, véhicules, wallet/retraits, paiements et recherche de logs. Toute décision administrative est auditée. Les fichiers privés sont consultés avec des URLs signées DiddiFiles, jamais avec une URL MinIO interne.

Les schémas, statuts et erreurs sont dans `openapi.json`. Les routes `/v1/admin/*` ne sont pas destinées aux applications passager ou chauffeur.
