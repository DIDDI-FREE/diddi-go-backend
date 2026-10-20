# 20 octobre 2026 - Connecteur DiddiSupport

## Ajoute

- endpoint S2S `GET /internal/v1/support/ride/{ride_id}/context` ;
- scope DiddiGo `diddigo:support-context:read` ;
- contrat versionne `diddi.context.v1` ;
- validation du JWT DiddiFreeID, de `X-Client-ID`, de `X-Request-ID` et de `X-Support-Context-Scope` ;
- projection Support redigee : statut, montant, moyen de paiement, participants identifies et chronologie, sans telephone, geolocalisation ni KYC ;
- tests de contrat couvrant succes, `401`, `403`, `404` et indisponibilite JWKS `503`.
