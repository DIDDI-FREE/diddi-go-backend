# Contrat S2S DiddiGo - MVP

**Version :** `mvp.2026-10-14`

**Surface :** routes `/internal/*`

Un appel S2S exige un JWT DiddiFreeID avec `iss`, `sub`, `aud`, `client_id`, `scope`, `status=active` et un en-tête `X-Client-ID` cohérent. Les scopes sont vérifiés par route.

Intégrations principales : Pilotage, DiddiComms, DiddiPay, DiddiMap et webhooks internes. Ces routes ne doivent jamais être appelées directement par une application publique. Les secrets client ne sont jamais envoyés au frontend.
