# Permissions de reference

- Passager : ses courses, paiements, supplements et notes.
- Chauffeur : courses assignees, position, attente et propositions de
  supplement.
- Admin humain : validation KYC/KYV et operations de support.
- Services : JWT S2S avec audience, subject, client ID et scope propres.

Pour DiddiSupport, la lecture du contexte redige d'une course exige le scope
`diddigo:support-context:read`, l'audience `diddigo`, le sujet
`service:diddisupport` et le client configure `diddisupport-staging-diddigo`.

Pour DiddiFree Pro, les projections `diddi.score.v1` exigent le scope
`diddigo:scores:read`, l'audience `diddigo`, le sujet
`service:diddifreepro` et le client configure
`diddifreepro-staging-diddigo`.

Un role ou une permission ne vient jamais d'un parametre fourni par le client.
Il vient du JWT verifie ou des profils metier DiddiGo.
