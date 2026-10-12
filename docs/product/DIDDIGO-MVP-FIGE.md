# DiddiGo — MVP figé

**Statut :** source de vérité produit pour le MVP DiddiGo

**Décisions figées le :** 9 octobre 2026, complétées le 12 octobre 2026

**Portée :** DiddiGo, lancement Abidjan, staging puis production.

**Usage :** toute epic, user story, ticket backend/frontend/mobile/QA ou configuration doit référencer cette page. En cas de contradiction, cette page prévaut jusqu'à une décision produit explicitement enregistrée ici.

## 1. Le parcours MVP

1. Le passager recherche une destination et reçoit un devis persistant.
2. Il crée une course exclusivement depuis un devis encore valide.
3. Le matching cherche des chauffeurs selon une stratégie configurable.
4. Le chauffeur accepte, se rend au point de départ puis signale son arrivée.
5. Trois minutes d'attente avant course sont gratuites ; la suite est facturée à la seconde.
6. Le passager donne son code de démarrage à six chiffres, manuellement ou par QR code.
7. La course démarre, les positions GPS sont envoyées à DiddiMap sans données personnelles.
8. La course se termine ; le montant accepté au devis demeure la base du prix.
9. Le passager paie en cash ou par moyen numérique. En cas d'échec numérique, il choisit un autre moyen ; un impayé devient un incident support.
10. Le chauffeur consulte son wallet, puis peut demander un retrait réel.

## 2. Décisions produit figées

| Sujet | Règle MVP |
|---|---|
| Devis | Persisté. Valable 15 minutes. Une course exige un `quote_id` valide. Un devis expiré demande un rafraîchissement ; aucune course n'est créée. Le prix du devis reste la base acceptée, sans recalcul silencieux. |
| Matching | Modèle configurable par environnement. Les rayons, délais et vagues ne sont pas figés à 30 s / 1 km, 60 s / 3 km, 180 s / 5 km. |
| Arrivée | Le chauffeur peut déclarer son arrivée à moins de 50 m du point de prise en charge. Ce rayon est configurable par environnement. L'attente pré-course commence alors. |
| Attente avant course | 3 minutes gratuites, puis 100 XOF/minute proratisés à la seconde. Les deux valeurs sont configurables par environnement. |
| Client absent | Après 10 minutes d'attente, le chauffeur peut annuler pour client absent sans pénalité. La course est annulée : l'attente n'est pas facturée au passager, qui est néanmoins signalé/pénalisé. |
| Démarrage | Un code de 6 chiffres est requis. Seul le passager le voit. Après 5 erreurs, le démarrage est bloqué et passe au support ; la course ne s'annule pas automatiquement. |
| QR de démarrage | Il porte l'identifiant de course et le même code à 6 chiffres. Il ne remplace pas la vérification backend. |
| Commission | Configurable par variable d'environnement et appliquée à la création de chaque course. Aucun hot reload. |
| Paiement numérique échoué | Proposer un autre moyen de paiement. Si le paiement n'est pas régularisé, créer un incident paiement/litige ; ne pas bloquer automatiquement les prochaines courses. Aucun gain chauffeur n'est reversé automatiquement avant décision support. |
| Retrait chauffeur | Inclus au MVP réel. Minimum 2 000 XOF, configurable. Les frais sont à la charge du chauffeur. Le bénéficiaire est renseigné par le chauffeur dans les limites DiddiPay/PSP. Un payout inconnu est réessayé, réconcilié puis escaladé au support en cas d'échec persistant. |
| Urgence | Le contact d'urgence reçoit SMS et WhatsApp ; le support reçoit toujours l'alerte. L'alerte reste ouverte si la notification externe échoue. Plusieurs déclenchements sont possibles, mais le contact n'est notifié qu'une fois par course ; les répétitions sont visibles par le support et limitées. |
| Appels | Numéro direct entre les participants autorisés. Pas d'appel masqué dans le MVP. |
| Traces GPS | DiddiMap reçoit `trace_id`, `source_service`, `source_ride_id` et les points GPS. Il ne reçoit ni `user_id`, ni nom, téléphone, e-mail, document ou token utilisateur. DiddiGo conserve son lien d'audit interne. |
| KYV véhicule | Six photos obligatoires pour toute nouvelle soumission ou resoumission : avant, arrière, côté gauche, côté droit, intérieur habitacle, plaque lisible. Les dossiers historiques validés restent acceptés. |
| Suppléments | Le chauffeur propose une ligne tarifaire et le passager l'accepte ou la conteste. Seules les lignes acceptées entrent dans le prix : péage 500 XOF, parking 200 XOF, bagage standard 500 XOF, bagage volumineux 1 000 XOF, autre frais plafonné à 1 000 XOF. L'attente est calculée automatiquement à 100 XOF/minute et n'est pas un montant libre. |

## 3. Contrats à implémenter

### Configuration par environnement

| Variable proposée | Valeur MVP |
|---|---:|
| `DIDDIGO_COMMISSION_RATE` | `0.18` |
| `PRE_RIDE_WAIT_FREE_SECONDS` | `180` |
| `PRE_RIDE_WAIT_PRICE_PER_MINUTE_XOF` | `100` |
| `PRE_RIDE_NO_SHOW_SECONDS` | `600` |
| `DRIVER_ARRIVAL_MAX_DISTANCE_METERS` | `50` |
| `RIDE_START_CODE_MAX_ATTEMPTS` | `5` |
| `RIDE_QUOTE_TTL_SECONDS` | `900` |
| `DRIVER_WITHDRAWAL_MIN_AMOUNT_XOF` | `2000` |
| `RIDE_EMERGENCY_RATE_LIMIT_SECONDS` | `60` |
| `RIDE_EMERGENCY_CONTACT_NOTIFY_ONCE` | `true` |
| `VEHICLE_KYV_REQUIRED_PHOTOS` | `front,back,left,right,interior,plate` |
| `DIDDIMAP_TRACE_ANONYMIZATION_ENABLED` | `true` |

Les noms suivent la convention proposée par QA. Le backend peut les adapter à une convention existante, sans modifier les règles produit ci-dessus.

### QR code de démarrage

```json
{
  "type": "diddigo_ride_start",
  "version": 1,
  "ride_id": "<uuid-course>",
  "code": "123456"
}
```

Le backend vérifie la course, le chauffeur affecté, le statut, le code, le compteur d'essais et l'usage unique. Le code ne doit pas apparaître en clair dans les logs.

### Trace envoyée à DiddiMap

```json
{
  "trace_id": "<uuid-trace>",
  "source_service": "diddigo",
  "source_ride_id": "<uuid-course>",
  "points": [
    {"lat": 5.0, "lng": -4.0, "recorded_at": "2026-10-09T12:00:00Z", "accuracy_m": 8}
  ]
}
```

### KYV : champs de photo

| Champ API | Libellé affiché |
|---|---|
| `vehicle_front_photo_file_id` | Vue avant du véhicule |
| `vehicle_back_photo_file_id` | Vue arrière du véhicule |
| `vehicle_left_photo_file_id` | Vue côté gauche |
| `vehicle_right_photo_file_id` | Vue côté droit |
| `vehicle_interior_photo_file_id` | Vue intérieure habitacle |
| `vehicle_plate_photo_file_id` | Plaque d'immatriculation lisible |

## 4. Support et incidents

**Paiement :** `payment_incident_open` → `payment_dispute_under_review` → `payment_recovery_requested` → `payment_resolved_paid` / `payment_resolved_waived` / `payment_unrecoverable`.

**Urgence :** `emergency_open` → `emergency_notified` ou `emergency_notification_failed` → `emergency_acknowledged` → `emergency_closed`.

**Code de démarrage bloqué :** événement `ride_start_code_blocked`, avec course, chauffeur affecté, nombre d'essais et horodatage. Seul le support/admin peut débloquer, régénérer le code ou appliquer une procédure manuelle.

## 5. Parcours MVP de référence

Ces parcours sont la référence produit utilisée pour organiser les epics, tickets, recettes et contrats. Un ticket ne peut préciser que son implémentation : il ne modifie pas le parcours.

### W1 — Devis et création de course

1. Le passager recherche sa destination, choisit son niveau de confort et obtient un devis persistant valable 15 minutes.
2. La création de course exige le `quote_id` encore valide. Un devis expiré demande un nouveau chargement ; le tarif du devis est ensuite figé.
3. Le matching applique le modèle configurable, propose la course par vagues et informe le passager en cas d'absence de chauffeur.
4. L'acceptation unique par un chauffeur affecte la course et ouvre le suivi de son approche.

### W2 — Prise en charge et exécution de course

1. Le chauffeur accepte, rejoint le point de prise en charge et signale son arrivée.
2. L'attente pré-course démarre : trois minutes gratuites, puis 100 XOF/minute proratisés à la seconde. Les valeurs sont configurées par environnement.
3. Après dix minutes, il peut annuler pour client absent sans pénalité. La course est annulée sans facturer l'attente ; le passager est signalé.
4. Pour démarrer, le chauffeur saisit le code à six chiffres que seul le passager voit ou lit le QR contenant `ride_id` et ce code. Le backend contrôle l'affectation, l'état, l'usage unique et cinq essais maximum.
5. Pendant la course, le chauffeur envoie les positions GPS. À la fin, DiddiGo finalise la course et transmet la trace minimisée à DiddiMap.

### W3 — Paiement et incident de paiement

1. À la fin de la course, le passager règle selon le moyen choisi.
2. Si un paiement numérique échoue, l'application propose un autre moyen.
3. Sans régularisation, la course crée un incident paiement/litige. Le client n'est pas automatiquement bloqué pour ses prochaines courses.
4. Le gain chauffeur concerné reste en attente de la décision support ; il n'est pas reversé automatiquement.

### W4 — Gain et retrait chauffeur

1. Le chauffeur consulte son solde disponible après la décision applicable à la course.
2. Il demande un retrait d'au moins 2 000 XOF. Il renseigne le bénéficiaire dans les limites DiddiPay/PSP et voit le montant débité, les frais et le montant reçu avant confirmation.
3. Un payout inconnu est réessayé puis réconcilié. Un échec persistant ouvre un traitement support et affiche l'erreur au chauffeur.

### W5 — Urgence

1. Un participant déclenche une alerte pendant la course.
2. DiddiGo enregistre l'événement et alerte le support. Le contact d'urgence reçoit une notification SMS et WhatsApp une seule fois pour cette course.
3. Une erreur d'envoi externe ne ferme pas l'alerte. Les déclenchements suivants restent visibles par le support, avec une limite de fréquence raisonnable.

### W6 — Onboarding, KYV et mise en ligne

1. Le chauffeur crée son profil, soumet son KYC et ajoute son véhicule.
2. Toute soumission ou resoumission véhicule contient six photos obligatoires : avant, arrière, gauche, droite, intérieur et plaque lisible.
3. Après validation administrative, le chauffeur peut se mettre en ligne si les autres règles d'éligibilité sont satisfaites. Les anciens dossiers validés ne sont pas invalidés rétroactivement.

## 6. Découpage de delivery

| Epic | Contenu |
|---|---|
| EPIC-GO-01 — Devis et prix | Devis persistants, expiration, création par `quote_id`, figer le prix. |
| EPIC-GO-02 — Course au départ | Arrivée chauffeur, attente pré-course, client absent, code/QR de démarrage. |
| EPIC-GO-03 — Paiement et wallet | Échec/fallback paiement, incident/litige, commission configurable, retrait et réconciliation payout. |
| EPIC-GO-04 — Sécurité et urgence | Contacts d'urgence SMS/WhatsApp, support, rate limits, visibilité des numéros. |
| EPIC-GO-05 — KYV et confidentialité | Six photos véhicule, compatibilité dossiers existants, payload GPS DiddiMap minimisé. |
| EPIC-GO-06 — Recette de lancement | Parcours mobile complet, dix chauffeurs, concurrence, WebSocket/reconnexion, GPS réel, paiements staging, observabilité et restauration. |

## 7. Règles de documentation

- Cette page remplace les notes de brainstorming et les décisions dispersées.
- Jira ne contient que des tickets actionnables : un objectif, des critères d'acceptation, des dépendances et un lien vers cette page.
- Confluence ne contient qu'une copie de cette page et, au besoin, des comptes rendus datés. Les anciennes pages sont archivées, jamais utilisées comme référence active.
- Toute nouvelle décision modifie d'abord cette page, avec date et auteur, puis les tickets concernés.

## 8. Hors de ce gel

Le détail d'implémentation (routes exactes, schéma SQL, migrations, librairies, stratégie de retry, écrans et composants) est décidé dans les tickets techniques, tant qu'il respecte les règles de cette page. Les changements de règles produit nécessitent une mise à jour explicite de cette page avant développement.
