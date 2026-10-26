# DiddiGo - Checklist de release V1

**Edition :** `2026-10-26`
**Statut :** registre stateful de la candidate `v1.0.0-rc.1`
**Branche source :** `stage`
**Promotion cible :** le meme commit immuable vers `main`.

Cette edition ne remplace pas la checklist du 19 octobre. Elle centralise la
preuve de release V1 ; les cas detailes precedents restent des procedures de
test applicables.

## Regles de preuve

- `[ ]` non execute ; `[x]` reussi ; `[!]` bloque ; `[~]` partiel.
- Une preuve comporte le commit/image, la date, l'environnement et des IDs non
  sensibles (`request_id`, `ride_id`, `payment_intent_id`, `withdrawal_id`).
- Aucun JWT, secret, telephone complet, URL signee ou document KYC ne figure
  dans cette checklist.
- Tout echec P0/P1 empeche la promotion tant qu'il est ouvert.

## Gate R0 - Artefact reproductible

- [ ] `R0-01` Commits atomiques presents sur `stage` et arbre Git propre.
- [ ] `R0-02` Tag `v1.0.0-rc.1` cree sur le commit deploye en staging.
- [ ] `R0-03` `alembic upgrade head` atteint `0a1b2c3d4e5f` sur staging.
- [ ] `R0-04` `uv run pytest -m unit -q` passe.
- [ ] `R0-05` `uv run pytest -q` passe sur `diddi_go_test`, PostgreSQL/PostGIS
  et Redis dedies.
- [ ] `R0-06` Ruff, compilation, build Docker backend et `mkdocs build --strict` passent.
- [ ] `R0-07` `/health`, `/ready`, `/metrics`, `/docs`, `/openapi.json` et le
  portail MkDocs staging repondent.

## Gate R1 - Services et configuration staging

- [ ] `R1-01` DiddiFreeID, DiddiMap, DiddiPay, DiddiFiles et DiddiComms sont
  joignables avec les credentials S2S de staging.
- [ ] `R1-02` FCM est configure et une offre est recue application ouverte puis
  en arriere-plan.
- [ ] `R1-03` WhatsApp et SMS sont configures ; le SOS et l'OTP retrait sont
  recus par des numeros de recette.
- [ ] `R1-04` Wave/Mobile Money est actif dans DiddiPay staging et son callback
  signe atteint DiddiGo.
- [ ] `R1-05` Les URLs de retour paiement, wallet et les webhooks pointent vers
  staging, jamais local.

## Gate R2 - Parcours MVP backend et mobile

- [ ] `R2-01` KYC, KYV, six photos, refus par piece et nouvelle soumission
  permettent la mise en ligne apres approbation.
- [ ] `R2-02` Devis, expiration, creation de course, matching par vagues,
  acceptation unique et suivi chauffeur passent.
- [ ] `R2-03` Arrivee, attente pre-course, no-show, code/QR, GPS, attente en
  course, supplement et arret anticipe passent.
- [ ] `R2-04` Course cash : confirmation chauffeur unique, commission, gain et
  ledger coherents.
- [ ] `R2-05` Course Mobile Money : Wave, callback, retry/echec puis passage
  aux especes, sans doublon financier.
- [ ] `R2-06` Recharge, retrait OTP, payout, echec et reconciliation passent.
- [ ] `R2-07` Partage, DiddiComms avant/apres cloture, SOS, partenaires et
  affectations vehicule/chauffeur passent.
- [ ] `R2-08` Backoffice, Pilotage, logs structures, metriques et recherche par
  `request_id` passent.
- [ ] `R2-09` Reconnexion WebSocket : l'etat REST reconcilie la course sans
  action ni ecriture dupliquee.

## Gate R3 - Pilote limite

- [ ] `R3-01` Cohorte creee : 10 chauffeurs valides, 50 passagers invites,
  comptes support et administration de recette.
- [ ] `R3-02` Sept jours de pilote termines.
- [ ] `R3-03` Au moins 50 courses sont terminees et reconciliees.
- [ ] `R3-04` Les courses couvrent cash et Wave/Mobile Money, avec une preuve
  de paiement reussi et une preuve d'echec/reprise.
- [ ] `R3-05` Aucun incident P0/P1 ne reste ouvert.
- [ ] `R3-06` Les totaux course, commission, wallet, payout et Pilotage sont
  rapproches pour la campagne.

## Gate R4 - Promotion et beta

- [ ] `R4-01` Direction technique et Operations prennent la decision manuelle
  d'ouverture ou de pause a partir des preuves R0 a R3.
- [ ] `R4-02` Le commit exact de `v1.0.0-rc.1` est promu vers `main` sans
  modification fonctionnelle.
- [ ] `R4-03` Smoke tests production reussis avec secrets, bases, Redis,
  audiences S2S et domaines production distincts.
- [ ] `R4-04` Le tag `v1.0.0` est cree seulement apres validation du pilote.
- [ ] `R4-05` La release note finale, le changelog et la decision d'ouverture
  beta sont publies.

## Journal de campagne

| Date/heure | Environnement | Commit/image | Gate | Resultat | Preuve | Responsable | Incident |
| --- | --- | --- | --- | --- | --- | --- | --- |
| - | staging | - | R0 | NON EXECUTE | - | - | - |
| - | staging | - | R1 | NON EXECUTE | - | - | - |
| - | staging | - | R2 | NON EXECUTE | - | - | - |
| - | pilote | - | R3 | NON EXECUTE | - | - | - |

## Incidents de release

| ID | Date | Gravite | Parcours | Impact | Preuve | Proprietaire | Decision | Statut |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | - | - | - | - | - | - |
