# Permissions de reference

- Passager : ses courses, paiements, supplements et notes.
- Chauffeur : courses assignees, position, attente et propositions de
  supplement.
- Admin humain : validation KYC/KYV et operations de support.
- Services : JWT S2S avec audience, subject, client ID et scope propres.

Un role ou une permission ne vient jamais d'un parametre fourni par le client.
Il vient du JWT verifie ou des profils metier DiddiGo.
