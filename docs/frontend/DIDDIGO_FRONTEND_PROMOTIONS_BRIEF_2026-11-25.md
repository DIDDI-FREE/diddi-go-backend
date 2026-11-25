# DiddiGo - Promotions et remises : spécification frontend

Date : 2026-11-25
Version : V3 (V2 = ticket 040 : offres automatiques, prix garanti, bloc `offer`, « Mes offres », parrainage ; V3 = ticket 049 : bonus chauffeur)
Pour : équipes Frontend et UI/UX (appli client, appli chauffeur)
Source produit : « Promotions et bonus DIDDI — Note pour les équipes Frontend et UI/UX » (18 novembre 2026)

Ce document dit ce que l'appli peut faire avec l'API DiddiGo pour afficher une
remise sur une course, et ce qui **n'existe pas encore**. La V1 décrivait le
staging du 25 novembre (`stage`, commit `2cbc24a`). La V2 ajoute ce que livre le
ticket 040 (branche `feat/040-promotions-api`) : ces parties sont marquées
**(V2)** et ne marchent sur le staging qu'après son déploiement. Les schémas
exacts restent dans `/openapi.json`.

## 1. En bref

| Besoin de la note produit | État côté serveur |
|---|---|
| Voir la remise avant de commander (devis) | **Prêt** |
| La remise s'applique seule, rien à saisir | **(V2) Prêt**, une fois le réglage serveur activé (section 3.1) |
| Le prix affiché est le prix payé | **(V2) Prêt** : un devis valide garde sa remise ; une seule exception, refusée avant la création de la course (section 4) |
| Nom de l'offre, pourcentage, plafond, rang (« 2e sur 3 »), date de fin, services | **(V2) Prêt** : bloc `rewards.offer` (section 3.1) |
| Voir le prix initial, la remise et le montant à payer pendant et après la course | **Prêt** |
| Le chauffeur voit le montant à encaisser | **Prêt** |
| Liste de mes offres, avec historique | **(V2) Prêt** : `GET /v1/me/offers` (section 3.5) |
| Saisir un code de parrainage | **(V2) Prêt** : `POST /v1/me/referral/code` (section 3.5) |
| Mon code de parrainage à partager | **(V2) Prêt** : `GET /v1/me/referral` ; le lien de partage vaut `null` pour l'instant |
| Savoir pourquoi une offre ne s'applique pas | **(V2) Partiel** : codes stables dans « Mes offres » (`state`, `reason`) ; au devis automatique, pas de message |
| Code promo (autre que parrainage) | **N'existe pas** |
| Progression d'une offre client (« 4 courses sur 10 ») | **N'existe pas** (`progress` vaut `null`) |
| Bonus chauffeur : bloqué, débloqué, versé, progression, date limite | **(V3) Prêt** : `GET /v1/drivers/me/bonuses` (section 7.1) ; versé = ligne `rewards_bonus` du wallet |

À retenir :
- Avant la V2, l'appli ne pouvait afficher une remise que si elle connaissait un
  identifiant de campagne (`campaign_id`). Avec la V2 elle n'a plus rien à
  envoyer : DiddiGo demande la meilleure offre du client à chaque devis.
- Constat au 25 novembre : l'appli n'envoie jamais `campaign_id` et ne lit pas
  le bloc `rewards`. Avec la V2, il suffit de lire le bloc `rewards`.

## 2. Règles de la note produit, appliquées à DiddiGo

1. **L'appli affiche, le serveur décide.** Ne jamais calculer une remise.
   Afficher les champs de la section 3 tels quels.
2. **Aucun montant écrit en dur.** Pas de « −50 % », pas de « 1 000 F max » dans
   le code de l'appli. Le pourcentage et le plafond viennent du bloc
   `rewards.offer` (V2) : affichez-les seulement quand il est présent.
3. **Le prix affiché est le prix payé.** Vrai pour le devis tant qu'il n'est pas
   expiré, avec une exception à gérer : section 4.
4. **Un seul appui, une seule action.** Section 6.
5. **Des textes simples.** Le nom et la description de l'offre viennent du
   serveur (`offer.name`, `offer.description`, V2). Les libellés des écrans de
   prix (« Prix », « Remise », « À payer ») et les phrases construites à partir
   des champs (« 2e course sur 3 ») sont à vous.

Tous les montants sont des entiers en francs CFA (`XOF`). Le suffixe `_minor`
dans certains noms de champs ne veut **pas** dire centimes : `246` = 246 F.

## 3. Parcours client

### 3.1 Devis

`POST /v1/rides/pricing/estimate`

```json
{
  "pickup": {"lat": 5.3599, "lng": -4.0083},
  "dropoff": {"lat": 5.3760, "lng": -3.9876},
  "vehicle_category": "standard",
  "comfort_level": "standard",
  "campaign_id": "ce99efdd-3e7f-4efd-85d3-09f4260afc8d"
}
```

`campaign_id` est optionnel, et **l'appli n'a pas à l'envoyer** : il est décidé
(25 novembre) que l'offre s'applique seule. Quand le réglage serveur
`DIDDI_REWARDS_AUTO_QUOTE_ENABLED` est actif, DiddiGo demande lui-même la
meilleure offre du client à chaque devis. S'il y en a une, la réponse contient
le bloc `rewards` ci-dessous ; sinon elle n'a pas de bloc `rewards` et le prix
est le plein tarif, sans message à afficher. Ce réglage est **inactif** sur le
staging au 25 novembre : il sera activé après le déploiement de la V2 (le
service de remises est prêt depuis le 25 novembre). D'ici là, aucune remise
n'arrive sans `campaign_id`.

Réponse avec remise (extrait, V2) :

```json
{
  "estimated_fare": 1234,
  "currency": "XOF",
  "quote_id": "1d51eadd-b5c6-4775-b7a2-eaeb9addcb70",
  "expires_at": "2026-11-25T10:20:11.199733Z",
  "rewards": {
    "campaign_id": "ce99efdd-3e7f-4efd-85d3-09f4260afc8d",
    "eligible": true,
    "discount_amount_minor": 246,
    "final_amount_minor": 988,
    "currency": "XOF",
    "reason": null,
    "offer": {
      "offer_id": "ce99efdd-3e7f-4efd-85d3-09f4260afc8d",
      "name": "Bienvenue",
      "description": "20 % sur tes 3 premières courses",
      "value_type": "percent",
      "rate_percent": 20,
      "cap_per_order_minor": null,
      "uses_total": 3,
      "uses_used": 1,
      "uses_left": 2,
      "use_number": 2,
      "progress": null,
      "ends_at": "2026-12-31T23:59:59Z",
      "services": ["go"],
      "state": "usable",
      "reason": null,
      "history": []
    }
  }
}
```

Exemple construit d'après le contrat du service de remises, pas copié du
staging (non vérifié de bout en bout).

Le bloc `offer` (V2) est relayé tel quel depuis le service de remises.
`null` quand aucune offre ne s'applique. À afficher :

| Élément de la maquette | Champ |
|---|---|
| Nom de l'offre (« Bienvenue ») | `offer.name` |
| Texte de l'offre | `offer.description` (peut être `null`) |
| Valeur (« −20 % ») | `offer.rate_percent` quand `offer.value_type` vaut `percent` (seule valeur aujourd'hui) |
| Plafond (« 1 000 F max ») | `offer.cap_per_order_minor`, seulement s'il n'est pas `null` |
| Rang (« 2e course sur 3 ») | `offer.use_number` sur `offer.uses_total` (`uses_total` `null` = sans limite) |
| Date de fin | `offer.ends_at` (`null` = sans date) |
| Services où l'offre vaut | `offer.services` (codes : `go`, `food`, `send`…) |

`offer_id` est le même sur tous les services DIDDI : c'est l'identifiant à
utiliser pour ouvrir le détail (`GET /v1/me/offers/{offer_id}`, section 3.5).

Réponse sans remise (extrait) :

```json
{
  "estimated_fare": 1234,
  "rewards": {
    "eligible": false,
    "discount_amount_minor": 0,
    "final_amount_minor": 1234,
    "reason": "No eligible entitlement"
  }
}
```

À afficher :

| Élément | Champ |
|---|---|
| Prix initial | `estimated_fare` |
| Remise | `rewards.discount_amount_minor`, seulement si `rewards.eligible` est `true` |
| Montant à payer | `rewards.final_amount_minor` si `eligible`, sinon `estimated_fare` |
| Fin de validité du prix | `expires_at` (15 minutes par défaut) |

Cas à maquetter :

- **Pas de bloc `rewards`** : pas de campagne demandée, ou remises désactivées
  sur l'environnement. Afficher le plein tarif, sans message.
- **`eligible: false`** : afficher le plein tarif et dire que l'offre ne
  s'applique pas. Voir section 5 pour le motif.
- **`reason: "rewards_unavailable"`** : le service de remises ne répond pas. Le
  devis reste valable au plein tarif. Proposer de réessayer ; ne pas bloquer la
  commande.

Les champs `entitlement_id` et `campaign_version_id` du bloc `rewards` sont
techniques : ne pas les afficher, ne pas les renvoyer.

### 3.2 Commande

`POST /v1/rides`

```json
{"quote_id": "1d51eadd-b5c6-4775-b7a2-eaeb9addcb70", "payment_method": "cash"}
```

La remise vient du devis : il n'y a rien d'autre à envoyer. La réponse (`201`)
ne contient **pas** la remise :

```json
{"ride_id": "fd8257d4-3c74-44cd-af2c-1eb643920cba", "status": "requested", "estimated_fare": 1234, "currency": "XOF", "payment_method": "cash"}
```

Il faut donc lire la course juste après (3.3) pour connaître la remise
réellement appliquée.

(V2) Erreur propre aux remises : `409 REWARDS_OFFER_ALREADY_USED`. L'offre a
déjà servi pour une autre commande du client (par exemple deux commandes en
même temps). La course **n'est pas créée**, rien n'est débité. Afficher un
message simple, puis redemander un devis et réafficher le prix (section 4).

### 3.3 Pendant et après la course

`GET /v1/rides/{ride_id}` (et `GET /v1/rides/active/current`) renvoie toujours un
bloc `rewards` :

```json
{
  "estimated_fare": 1234,
  "final_fare": 1234,
  "rewards": {
    "campaign_id": "ce99efdd-3e7f-4efd-85d3-09f4260afc8d",
    "discount_amount_minor": 246,
    "client_payable_amount": 988,
    "status": "reserved",
    "offer": {"offer_id": "ce99efdd-…", "name": "Bienvenue", "rate_percent": 20, "use_number": 2, "uses_total": 3}
  }
}
```

(V2) `rewards.offer` est l'offre **telle qu'elle était au moment de la
commande** (figée sur la course), mêmes champs que dans le devis sauf
`history`. Elle sert au reçu (« Bienvenue · −20 % · 2e course sur 3 »).
Elle vaut `null` pour une course sans offre, pour une course commandée avant la
V2, et toujours pour le chauffeur.

À afficher (détail du prix demandé par la note produit) :

| Élément | Champ |
|---|---|
| Prix initial | `final_fare` s'il est rempli, sinon `estimated_fare` |
| Remise | `rewards.discount_amount_minor` (0 = pas de remise, ne rien afficher) |
| Montant à payer | `rewards.client_payable_amount` |

Le prix initial peut changer pendant la course (attente, arrêts, suppléments).
La remise, elle, ne change plus après la commande : c'est un montant fixe en
francs. Relire la course à chaque événement `ride.status_changed`.

`rewards.status` est un état technique. Valeurs possibles : `null`, `quoted`,
`reserved`, `confirmed`, `corrected`, `correction_deferred`, `released`,
`release_deferred`, `confirmation_refused`, `release_refused`. D'autres valeurs
peuvent s'ajouter. **Ne construisez pas l'écran dessus.** Une seule lecture
utile : `confirmed` = la remise est définitivement enregistrée. Pour l'affichage,
`discount_amount_minor` suffit.

### 3.4 Paiement

`GET /v1/payments/{ride_id}` et `POST /v1/payments/{ride_id}/prepare` (cas
espèces) renvoient les trois montants :

```json
{
  "ride_id": "fd8257d4-3c74-44cd-af2c-1eb643920cba",
  "status": "pending",
  "method": "cash",
  "amount": 988,
  "currency": "XOF",
  "gross_amount": 1234,
  "discount_amount_minor": 246,
  "client_payable_amount": 988
}
```

- `gross_amount` = prix initial, `discount_amount_minor` = remise,
  `client_payable_amount` = ce que le client paie.
- En Mobile Money, le montant envoyé à DiddiPay est déjà le montant remisé.
  La présence des trois champs dans la réponse de `prepare` en Mobile Money
  n'est **pas vérifiée** : pour le détail du prix, lire `GET /v1/payments/{ride_id}`.
- Reçu et historique : mêmes champs.
- Le bloc `offer` n'est **pas** dans les réponses de paiement (le chauffeur
  les lit aussi). Pour le nom de l'offre sur le reçu, lire la course (3.3).

### 3.5 Mes offres et parrainage (V2)

Quatre routes, toutes avec le jeton de l'utilisateur connecté. DiddiGo ne garde
aucune donnée d'offre : il relaie la réponse du service de remises.

| Route | Rôle |
|---|---|
| `GET /v1/me/offers` | Toutes mes offres valables sur DiddiGo, tous états, historique compris, les plus récentes d'abord. Réponse `{"offers": [ … ]}`, chaque élément a les champs du bloc `offer` (3.1). Un nouveau client y voit son offre de bienvenue avant sa première course. |
| `GET /v1/me/offers/{offer_id}` | Une offre de la liste. `404 REWARDS_OFFER_NOT_FOUND` si le client ne l'a pas. |
| `POST /v1/me/referral/code` | Saisir un code de parrainage. En-tête `Idempotency-Key` obligatoire (8 à 100 caractères, une nouvelle valeur par code saisi). Corps `{"code": "AB12CD34"}`. |
| `GET /v1/me/referral` | Mon code à partager, le lien, ce que gagne le parrain, les limites, le nombre d'amis. Le code est créé à la première demande, puis toujours le même. |

`state` d'une offre (liste fixe) : `available`, `in_progress`, `usable`,
`used`, `expired`, `refused`, `given_back` (rendue après un remboursement).
Aujourd'hui `available` et `in_progress` ne sont jamais renvoyés pour un client.

`reason` d'une offre `refused` (liste fixe) : `expired`, `not_eligible`,
`already_used`, `budget_exhausted`, `code_unknown`, `own_code`.

`history` : une ligne par course remisée (`service_operation_id` = la course,
`discount_amount_minor`, `state` = `used` ou `given_back`, `at`).

**Saisie d'un code.** Réponse `200` dans les deux cas :

```json
{"status": "accepted", "reason": null, "offer_id": "…", "duplicate": false}
{"status": "refused", "reason": "own_code", "offer_id": null, "duplicate": false}
```

`reason` d'un refus : `code_unknown` (code inconnu), `own_code` (c'est mon
propre code), `already_used` (j'ai déjà un parrain), `not_eligible` (compte non
éligible ou plafond de filleuls du parrain atteint), `expired` (pas de
parrainage ouvert). `duplicate: true` = même demande reçue deux fois, même
réponse. Un code tapé et un lien partagé donnent le même parrainage.

**Mon code.** Réponse (exemple construit d'après le contrat) :

```json
{"code": "AB12CD34", "link": null, "offer_id": "…", "reward_amount_minor": 1000,
 "reward_services": ["go"], "max_referrals": null, "ends_at": null,
 "referred_count": 0, "pending_count": 1}
```

- `link` vaut `null` pour l'instant : le format décidé est
  `diddifree.com/r/<code>`, construit hors du service de remises ; qui le
  fabrique n'est pas encore décidé. En attendant, partager le code seul.
- `referred_count` = amis qualifiés, `pending_count` = amis rattachés pas encore
  qualifiés. Des nombres seulement, jamais de noms : l'écran « liste des
  filleuls » de la maquette ne peut pas être nourri.
- `max_referrals`, `ends_at` : afficher seulement s'ils ne sont pas `null`.

**Erreurs de ces quatre routes.** `503 REWARDS_UNAVAILABLE` : le service de
remises ne répond pas, ou les remises sont désactivées. Réessayer plus tard ;
pour la saisie de code, renvoyer **la même** demande avec **le même**
`Idempotency-Key`. Au moment de l'écriture, les deux routes de parrainage
répondent ce `503` sur le staging tant que DiddiGo n'a pas reçu les droits
d'accès nécessaires (non vérifié après déploiement).

## 4. Quand la remise change entre le devis et la commande

Décision du 25 novembre : **le prix affiché est le prix payé** tant que le devis
est valide (15 minutes). (V2) DiddiGo donne au service de remises la fin de
validité du devis ; jusqu'à cette heure, la remise du devis est gardée à la
commande, même si la campagne s'arrête ou atteint son budget entre-temps.

| Cas | Ce que fait DiddiGo | Ce que voit l'appli |
|---|---|---|
| Cas normal (V2) | La course est créée avec la remise du devis | `rewards.discount_amount_minor` de la course = celui du devis |
| L'offre a déjà servi pour une autre commande (V2, seule exception) | La commande est refusée, rien n'est créé ni débité | `409 REWARDS_OFFER_ALREADY_USED` : redemander un devis, réafficher le prix |
| Devis expiré | La commande est refusée | `409 QUOTE_EXPIRED` : redemander un devis |
| Le droit ne couvre plus qu'une partie de la remise (cas rare, droit utilisé en partie entre-temps) | La course est créée avec la remise restante | `rewards.discount_amount_minor` de la course < celui du devis |
| Le service de remises refuse autrement ou ne répond pas à la commande | La commande échoue | Erreur `REWARDS_OPERATION_FAILED` ou `503 REWARDS_UNAVAILABLE` |

Ce que l'appli doit faire :

1. Garder le `discount_amount_minor` du devis.
2. Sur `409 REWARDS_OFFER_ALREADY_USED` : écran 04 de la maquette (« Le prix a
   changé, avant que tu commandes »), après un nouveau devis.
3. Après `POST /v1/rides`, lire `GET /v1/rides/{ride_id}`. Si la remise de la
   course est plus petite que celle du devis (cas rare ci-dessus), prévenir le
   client tout de suite avec le nouveau montant, et lui laisser annuler
   (`POST /v1/rides/{ride_id}/cancel`).

Après un échec de commande dû aux remises, la course n'existe pas et le devis
n'est pas consommé ; mais pour `REWARDS_OFFER_ALREADY_USED` il échouera de
nouveau : redemander un devis.

## 5. Motif de refus

Le seul motif disponible est `rewards.reason` dans le devis :

- `"rewards_unavailable"` : valeur stable, produite par DiddiGo.
- toute autre valeur : texte libre en anglais venu du service de remises
  (exemple vu : `"No eligible entitlement"`). **Ce n'est pas un code**, il peut
  changer, et il n'est pas fait pour être montré au client.

Les quatre motifs de la note produit (code expiré, non éligible, déjà utilisé,
budget épuisé) ne sont pas distinguables **au devis**. En attendant :
afficher un message unique du type « Cette offre ne s'applique pas à cette
course », et prévoir dans la maquette l'emplacement des quatre messages précis.

(V2) Avec l'offre automatique, le devis n'a pas de motif : pas d'offre = pas de
bloc `rewards`, rien à dire. Les motifs stables sont dans « Mes offres »
(`state: "refused"` + `reason`, section 3.5) et dans la réponse de saisie d'un
code.

## 6. Un seul appui, une seule action

| Action | Protection côté serveur | À faire côté appli |
|---|---|---|
| Demander un devis | Aucune nécessaire (pas d'effet) | Rien |
| Commander (`POST /v1/rides`) | Un devis ne sert qu'une fois : le second envoi répond `409 QUOTE_ALREADY_USED`. Un client ne peut pas avoir deux courses actives : `409 ACTIVE_RIDE_ALREADY_EXISTS` | Désactiver le bouton dès l'appui. Sur l'une de ces deux erreurs, ou après une coupure réseau, appeler `GET /v1/rides/active/current` et reprendre la course existante au lieu de recommander |
| Préparer le paiement (`prepare`) | Pas d'en-tête `Idempotency-Key` sur cette route | Désactiver le bouton ; après une coupure, relire `GET /v1/payments/{ride_id}` avant de renvoyer |
| Confirmer les espèces (chauffeur) | Voir section 7 | Désactiver le bouton ; relire le paiement après une coupure |
| Saisir un code de parrainage (V2) | `Idempotency-Key` obligatoire : même clé = même réponse, une seule application | Créer la clé à l'appui ; la garder pour réessayer après une coupure ou un `503` ; une nouvelle clé pour un autre code |

Devis expiré : `409 QUOTE_EXPIRED`. Redemander un devis et réafficher le prix,
la remise peut avoir changé.

Format des erreurs : `{"error": {"code": "...", "message": "...", "details": ...}}`.
Se baser sur `code`, jamais sur `message`.

## 7. Appli chauffeur

- Le chauffeur lit la même fiche course (`GET /v1/rides/{ride_id}`).
- Les montants ne lui sont visibles que lorsque la course est `in_progress` ou
  `completed`. Avant, `discount_amount_minor` vaut 0 et `client_payable_amount`
  vaut `null` : ne rien afficher.
- **Montant à encaisser en espèces = `rewards.client_payable_amount`**, pas
  `final_fare`. C'est le point le plus important de l'écran de fin de course.
- `POST /v1/payments/{ride_id}/confirm-cash` avec `{"amount_collected": 988}`.
  Le serveur refuse (`422 AMOUNT_MISMATCH`) un montant qui s'écarte de plus de
  200 F ou de plus de 10 % du montant attendu (la plus grande des deux limites).
- **Rémunération du chauffeur sur une course remisée.** DIDDI paie la remise,
  le chauffeur reçoit toujours le prix complet (décision du 25 novembre).
  En Mobile Money, son wallet est crédité de sa rémunération complète. En
  espèces, il encaisse le montant remisé, la commission est prélevée sur son
  wallet et **la remise lui est recréditée** dans le même wallet (ticket 039).
  Exemple : prix 1 234 F, commission 222 F, remise 246 F. Il encaisse 988 F,
  son wallet bouge de −222 F + 246 F = +24 F, il a bien 1 012 F au total.
- Dans `GET /v1/drivers/me/wallet/ledger`, cette ligne a le type
  `rewards_discount`, `direction: "credit"`, `reference_type: "ride"`. Prévoir
  un libellé du type « Remise DIDDI ». D'autres types pourront s'ajouter :
  garder un libellé par défaut pour un type inconnu.

### 7.1 Bonus chauffeur (V3, ticket 049)

`GET /v1/drivers/me/bonuses` (jeton du chauffeur ; il faut un profil chauffeur,
validé ou non). Réponse `{"bonuses": [ … ]}`, relayée telle quelle depuis le
service de remises. Exemple construit d'après le contrat :

```json
{"bonuses": [{
  "offer_id": "…", "name": "Bonus d'accueil", "description": "…",
  "kind": "stepped", "state": "withdrawable",
  "total_amount_minor": 10000, "unlocked_amount_minor": 3000,
  "locked_amount_minor": 7000, "paying_amount_minor": 2000,
  "paid_amount_minor": 1000, "expired_amount_minor": 0,
  "progress": {"current": 3, "target": 10, "counts": "…"},
  "window_start": "account_created", "window_start_at": "…", "deadline_at": "…"
}]}
```

| Élément de la maquette | Champ |
|---|---|
| Nom, texte | `name`, `description` |
| Total du bonus | `total_amount_minor` |
| Bloqué (pas encore gagné) | `locked_amount_minor` |
| Débloqué | `unlocked_amount_minor` |
| En cours de versement | `paying_amount_minor` |
| Versé dans le wallet | `paid_amount_minor` |
| Expiré | `expired_amount_minor` |
| Progression (« 3 / 10 courses ») | `progress.current` / `progress.target` ; `progress.counts` dit ce qui compte |
| Date limite | `deadline_at` (`null` = sans date) |
| Paliers ou seuil | `kind` : `stepped` (un montant par course) ou `threshold` (tout à l'objectif) |

`state` (liste fixe) : `available`, `in_progress`, `locked`, `paying`,
`withdrawable`, `paid`, `expired`. `frozen` existe mais n'est jamais renvoyé
aujourd'hui. Un bonus auquel le chauffeur n'a pas droit n'est pas listé.

Erreurs : `404 DRIVER_PROFILE_NOT_FOUND` (pas de profil chauffeur),
`503 REWARDS_UNAVAILABLE` (réessayer plus tard).

**Un seul solde.** Un bonus versé est une ligne du wallet, type
`rewards_bonus`, `direction: "credit"`, `reference_type: "rewards_action"`,
`description` = « Bonus DIDDI : <nom de l'offre> ». Il entre dans le solde
retirable comme les autres gains. Il n'y a **pas** de solde bloqué dans le
wallet : le « bloqué » de la maquette se lit dans `GET /v1/drivers/me/bonuses`
(`locked_amount_minor`), il n'est pas dans le wallet. `reserved_balance` reste
l'argent d'un **retrait en cours** : ne pas l'utiliser pour les bonus.

**Rien n'est repris.** Une course remboursée ne retire pas un bonus déjà versé.

## 8. Ce qui manque, et à qui le demander

Avec la V2, la liste des offres, la saisie d'un code de parrainage, mon code,
les textes et le prix garanti existent (sections 3 et 4). Il reste :

| Manque | Conséquence pour l'appli | Proposition |
|---|---|---|
| Code promo (autre que parrainage) | Pas d'écran de saisie de code promo | À décider (PM) |
| Lien de partage du parrainage | `link` vaut `null` : partager le code seul | Format décidé (`diddifree.com/r/<code>`), fabrication à décider |
| Liste nominative des filleuls | Seulement des nombres (`referred_count`, `pending_count`) | Choix assumé : pas de noms |
| Progression d'une offre client (« 4 courses sur 10 ») | `progress` vaut `null` | Pas d'objectif sur les offres client aujourd'hui |
| Motif au devis automatique | Pas de message au devis quand aucune offre ne s'applique | Motifs stables dans « Mes offres » |

États de la note produit, côté client DiddiGo, avec ce qui existe :

| État | Disponible ? |
|---|---|
| Disponible, En cours (progression) | Non : jamais renvoyés pour un client aujourd'hui |
| Utilisable | (V2) Oui : `state: "usable"` dans « Mes offres », et le bloc `offer` du devis |
| Utilisé | (V2) Oui : `state: "used"`, et `history` |
| Expiré | (V2) Oui : `state: "expired"` |
| Refusé | (V2) Oui : `state: "refused"` + `reason` |
| Repris après remboursement | (V2) Oui : `state: "given_back"` |
| Bloqué, Retirable, En cours de versement (chauffeur) | (V3) Oui : `state` et montants de `GET /v1/drivers/me/bonuses` |

## 9. Ce que vous pouvez construire dès maintenant

1. Le bloc « détail du prix » (prix initial, remise, à payer) sur le devis, la
   course en cours, l'écran de paiement, le reçu et l'historique.
2. L'écran de fin de course chauffeur avec le montant à encaisser.
3. (V2) Le nom, le pourcentage, le plafond et le rang de l'offre sur le devis
   et le reçu (`rewards.offer`).
4. (V2) L'écran 04 « le prix a changé » sur `409 REWARDS_OFFER_ALREADY_USED`.
5. (V2) « Mes offres » avec l'historique, la saisie d'un code de parrainage et
   « mon code ».
6. Les maquettes des bonus professionnels, en attendant leurs routes.

Pour tester sur le staging : une campagne de test existe
(`ce99efdd-3e7f-4efd-85d3-09f4260afc8d`, comptes review). Demander à l'équipe de
test si elle est encore active avant de vous en servir.

## 10. Écran par écran : maquettes Figma du 25 novembre

Maquettes lues : fichier « DiddiFree — Compte unique · Utilisateur / Pro », page
« 🎁 Promotions et bonus », sections 01 à 04 (la section 05 est DiddiAdmin, hors
de ce document). Pour chaque écran : ce qu'il affiche, et si le serveur le
fournit aujourd'hui.

Légende : **Oui** = fourni par DiddiGo aujourd'hui. **V2** = fourni après le
déploiement du ticket 040. **Montants seuls** = les francs sont fournis, pas les
libellés. **Non** = aucune route.

### Section 01 — Mes offres, le prix réel, ce qui change (client)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| 01 Mes offres — disponibles | Liste d'offres : nom, valeur (« −50 % »), nombre d'usages, condition, plafond, progression (« 1 utilisée sur 3 »), date de fin, service, badge d'état ; compteur « Disponibles · 4 » ; onglet Historique | **V2** : `GET /v1/me/offers` (section 3.5). Compteur « Disponibles » = offres `usable`. Progression : non (`progress` vaut `null`) |
| 02 Détail — les six réponses | Les six réponses en phrases, catégories de véhicule concernées (« Standard, Confort et Moto »), date et heure de fin | **V2 en partie** : `GET /v1/me/offers/{offer_id}` (nom, texte, valeur, plafond, usages, date de fin, services). Pas les catégories de véhicule |
| 03 Estimation — remise appliquée | Prix barré 1 500 F, prix remisé 750 F, ligne « −750 F », bouton « Commander · 750 FCFA » | **Montants seuls** : `estimated_fare`, `rewards.discount_amount_minor`, `rewards.final_amount_minor` (section 3.1) |
| 03, même écran | Nom de l'offre (« Bienvenue »), pourcentage (« −50 % »), rang (« 2e course sur 3 »), plafond (« 1 000 F max ») | **V2** : `rewards.offer` (section 3.1) |
| 04 Remise modifiée avant validation | « Le prix a changé — avant que tu commandes », motif (« n'a plus de budget »), avant / maintenant, « Rien n'a été débité », boutons « Commander à 1 500 FCFA » et « Ne pas commander » | **V2 en partie** : sur `409 REWARDS_OFFER_ALREADY_USED` rien n'est créé ; l'appli redemande un devis pour « maintenant ». Le motif « n'a plus de budget » n'arrive plus à cet endroit : un devis valide garde sa remise (section 4) |
| 05 Reçu — prix, remise, payé | Prix de la course, remise, « Payé en espèces » | **Oui** : `gross_amount`, `discount_amount_minor`, `client_payable_amount` (section 3.4) |
| 05, même écran | Nom et pourcentage de l'offre, « Il te reste 1 course à −50 % jusqu'au 31 déc. » | **V2** : `rewards.offer` de la course (figé à la commande). « Il te reste » : `uses_left` au moment de la commande ; pour la valeur à jour, lire `GET /v1/me/offers/{offer_id}` |
| 06 Panier (DiddiFood) | Hors DiddiGo. À noter pour DiddiGo : « Retirer » un code pour le garder suppose que le client peut choisir de ne pas appliquer une offre. DiddiGo ne le permet pas aujourd'hui | **Non** |
| 07 Planche des sept états client | Disponible, en cours, utilisable, utilisée, expirée, refusée (avec motif), reprise après remboursement | **V2 en partie** : `usable`, `used`, `expired`, `refused` (avec motif), `given_back`. Pas « disponible » ni « en cours » |

Les trois écarts relevés en V1 sont traités par la V2 :

1. **« Rien à saisir : la remise s'applique seule »** (écran 02). DiddiGo
   demande lui-même la meilleure offre du client à chaque devis (section 3.1),
   une fois le réglage serveur activé.
2. **« Le prix a changé, avant que tu commandes »** (écran 04). Un devis valide
   garde sa remise. La seule exception (offre déjà servie pour une autre
   commande) est refusée **avant** la création de la course :
   `409 REWARDS_OFFER_ALREADY_USED`, rien n'est créé ni débité. L'appli
   redemande un devis pour afficher « maintenant » (section 4). L'erreur ne
   porte pas le nouveau prix : il vient du nouveau devis.
3. **Pourcentage, nom, rang et plafond de l'offre** (écrans 03 et 05). Fournis
   par `rewards.offer`. Ne toujours rien déduire des francs (un « −50 % »
   plafonné à 1 000 F ne se recalcule pas à partir de −750 F).

### Section 02 — Saisir un code, parrainer, comprendre un refus (client)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Code · vérification | Envoi d'un code, un seul envoi même après double appui (« demande idempotente côté serveur ») | **V2** : `POST /v1/me/referral/code` avec `Idempotency-Key`, codes de parrainage seulement |
| Code · accepté | Ce que le code donne, où, jusqu'à quand, ce que gagne le parrain | **V2** : `offer_id` de la réponse, puis `GET /v1/me/offers/{offer_id}` |
| Code · refusé | Motif en clair : expiré, non éligible, déjà utilisé, budget épuisé (« le texte exact vient du serveur ») | **V2** : un code stable dans `reason` ; le texte affiché est à vous |
| Parrainage · mon code | Mon code, gain des deux côtés, limites (« 10 amis par mois », « plafonnée à 1 000 F ») seulement si elles existent | **V2** : `GET /v1/me/referral` (code, gain du parrain, `max_referrals`, `ends_at`). Lien : `null` pour l'instant |
| Parrainage · suivi | Liste des filleuls avec état (gagnée, en attente, non éligible) et compteur | **V2 en partie** : compteurs seulement (`referred_count`, `pending_count`), pas de liste |
| Offre · reprise | Commande remboursée, remise reprise, code de nouveau utilisable | **V2** : `state: "given_back"` dans « Mes offres » et dans `history` |

(V2) DiddiGo relaie les routes de parrainage du service de remises : l'appli
appelle DiddiGo, jamais le service de remises directement.

### Section 03 — Bonus professionnels (chauffeur, livreur, restaurant)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Bonus · vue d'ensemble | Totaux « Retirable » et « Bloqué », liste des bonus avec progression et date de fin | **V3** : `GET /v1/drivers/me/bonuses` (section 7.1). « Retirable » = solde du wallet ; « Bloqué » = somme des `locked_amount_minor` |
| Bonus d'accueil · paliers | Dix paliers de 1 000 F, débloqués ou non, règle d'expiration | **V3 en partie** : `kind: "stepped"`, montants et `progress` ; pas la liste palier par palier ni le texte de la règle |
| Bonus de performance · en cours | « 32 / 50 courses », temps restant, ce qui compte et ne compte pas | **V3** : `progress`, `deadline_at`, `progress.counts` |
| Bonus · en cours de versement | Étapes : objectif atteint, bonus validé, versement en cours | **V3** : `state: "paying"`, `paying_amount_minor` |
| Bonus · historique et planche des neuf états | Versé, débloqué, repris, expiré, gelé | **V3 en partie** : `state` (sept valeurs) et les lignes `rewards_bonus` du wallet. « Repris » n'existe pas (rien n'est repris), « gelé » jamais renvoyé |
| Bonus · suivi sur l'accueil | Pastille « Objectif semaine · 32/50 », « Bonus débloqué aujourd'hui » | **V3 en partie** : `progress` de `GET /v1/drivers/me/bonuses`. « Gagné aujourd'hui » (`GET /v1/drivers/me/wallet/earnings`) ne compte pas les bonus (non vérifié) |

### Section 04 — Portefeuille professionnel

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Portefeuille · deux soldes | « Solde retirable » | **Oui** : `available_balance` de `GET /v1/drivers/me/wallet` |
| même écran | « Bonus bloqué 6 000 F », progression, « Il te reste 6 courses » | **V3** : somme des `locked_amount_minor` et `progress` de `GET /v1/drivers/me/bonuses` (pas dans le wallet). Ne pas utiliser `reserved_balance` (retrait en cours) |
| Portefeuille · mouvements | Liste des mouvements, filtre « Retraits » | **Oui** : `GET /v1/drivers/me/wallet/ledger` |
| même écran | Filtre « Bonus », lignes débloqué / versé / repris avec l'offre d'origine | **V3 en partie** : lignes `rewards_bonus` (versé), nom de l'offre dans `description`. Pas de ligne « débloqué » ni « repris » |
| Retrait · plafonné au retirable | Montant, frais, « Tu reçois » | **Oui** : parcours de retrait existant (brief du 10 octobre) |
| même écran | « Les 6 000 F de bonus bloqué ne peuvent pas être retirés » | **V3** : vrai par construction (le bloqué n'est pas dans le wallet) ; montant = somme des `locked_amount_minor` |
| Mouvement · bonus repris | Montant repris, raison, offre, « Contester ce mouvement » | **Sans objet** : rien n'est repris (décision du 25 novembre) |

(V3) Décidé le 25 novembre : un seul solde. Un bonus versé entre dans le
wallet DiddiGo comme une ligne `rewards_bonus` ; la part encore bloquée reste
côté service de remises et se lit dans `GET /v1/drivers/me/bonuses`.

## 11. Questions ouvertes

Réglées le 25 novembre (décisions et ticket 040) : l'appli n'envoie plus de
`campaign_id` ; le serveur choisit la meilleure offre ; chaque service relaie
les offres et codes à l'appli (DiddiGo pour les courses) ; le client ne commande
pas une remise plus petite sans le savoir (section 4).

Encore ouvertes :

- Code promo autre que parrainage : existe-t-il, et où le saisir ?
- Lien de partage du parrainage : qui fabrique la page `diddifree.com/r/<code>` ?
