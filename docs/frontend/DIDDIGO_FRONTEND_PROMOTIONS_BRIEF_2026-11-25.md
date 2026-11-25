# DiddiGo - Promotions et remises : spécification frontend

Date : 2026-11-25
Version : V1
Pour : équipes Frontend et UI/UX (appli client, appli chauffeur)
Source produit : « Promotions et bonus DIDDI — Note pour les équipes Frontend et UI/UX » (18 novembre 2026)

Ce document dit ce que l'appli peut faire **aujourd'hui** avec l'API DiddiGo pour
afficher une remise sur une course, et ce qui **n'existe pas encore**. Il a été
écrit à partir du code déployé sur le staging le 25 novembre 2026 (`stage`,
commit `2cbc24a`). Les schémas exacts restent dans `/openapi.json`.

## 1. En bref

| Besoin de la note produit | État côté serveur |
|---|---|
| Voir la remise avant de commander (devis) | **Prêt** |
| Voir le prix initial, la remise et le montant à payer pendant et après la course | **Prêt** |
| Le chauffeur voit le montant à encaisser | **Prêt** |
| Savoir pourquoi une remise ne s'applique pas | **Partiel** : un texte libre, pas de code stable |
| Être prévenu si la remise a changé entre le devis et la commande | **Partiel** : pas de signal, l'appli doit comparer (section 4) |
| Liste des offres disponibles | **N'existe pas** |
| Saisir un code promo ou un code de parrainage | **N'existe pas** |
| Mon code de parrainage à partager | **N'existe pas** |
| Progression (« 4 courses sur 10 »), date de fin, services où l'offre est valable | **N'existe pas** |
| Bonus professionnel : bloqué, retirable, historique | **N'existe pas** |

À retenir : aujourd'hui l'appli ne peut afficher une remise que si elle connaît
déjà un identifiant de campagne (`campaign_id`). Aucune route ne lui donne cet
identifiant. Tant que ce point n'est pas réglé (section 8), le parcours remise
ne peut pas être branché de bout en bout. Les écrans, eux, peuvent être
construits dès maintenant.

Constat au 25 novembre : l'appli n'envoie jamais `campaign_id` et ne lit pas le
bloc `rewards`.

## 2. Règles de la note produit, appliquées à DiddiGo

1. **L'appli affiche, le serveur décide.** Ne jamais calculer une remise.
   Afficher les champs de la section 3 tels quels.
2. **Aucun montant écrit en dur.** Pas de « −50 % », pas de « 1 000 F max » dans
   le code de l'appli. DiddiGo renvoie des montants en francs, pas des
   pourcentages ni des plafonds : n'affichez pas de pourcentage tant que le
   serveur n'en fournit pas.
3. **Le prix affiché est le prix payé.** Vrai pour le devis tant qu'il n'est pas
   expiré, avec une exception à gérer : section 4.
4. **Un seul appui, une seule action.** Section 6.
5. **Des textes simples.** Les textes d'offre ne viennent pas encore du serveur.
   Les libellés des écrans de prix (« Prix », « Remise », « À payer ») sont à
   vous.

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
est le plein tarif, sans message à afficher. Ce réglage est **inactif** tant que
le service de remises n'est pas à jour : d'ici là, aucune remise n'arrive sans
`campaign_id`.

Réponse avec remise (extrait) :

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
    "reason": null
  }
}
```

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
    "status": "reserved"
  }
}
```

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

## 4. Quand la remise change entre le devis et la commande

La note produit demande : « si la remise change entre-temps, l'appli le dit
avant la validation ». Aujourd'hui le serveur ne peut le dire qu'**après** la
commande. Trois cas existent :

| Cas | Ce que fait DiddiGo | Ce que voit l'appli |
|---|---|---|
| Le droit du client ne couvre plus toute la remise (presque épuisé, deux commandes en même temps) | La course est créée avec une remise plus petite | `rewards.discount_amount_minor` de la course < celui du devis |
| Il ne reste plus rien | La course est créée au plein tarif | `rewards.discount_amount_minor` = 0, `client_payable_amount` = plein tarif |
| Le service de remises refuse ou ne répond pas à la commande | La commande échoue | Erreur `REWARDS_OPERATION_FAILED` ou `503 REWARDS_UNAVAILABLE` |

Ce que l'appli doit faire en attendant mieux :

1. Garder le `discount_amount_minor` du devis.
2. Après `POST /v1/rides`, lire `GET /v1/rides/{ride_id}`.
3. Si la remise de la course est plus petite que celle du devis, **prévenir le
   client tout de suite** avec le nouveau montant à payer, et lui laisser
   annuler (`POST /v1/rides/{ride_id}/cancel`).

Limite connue : le client est prévenu après avoir validé, pas avant. C'est un
écart avec la note produit. Une évolution est proposée en section 8.

Non vérifié : après un échec de commande dû aux remises, on ne sait pas si le
devis peut être réutilisé. Dans le doute, redemander un devis.

## 5. Motif de refus

Le seul motif disponible est `rewards.reason` dans le devis :

- `"rewards_unavailable"` : valeur stable, produite par DiddiGo.
- toute autre valeur : texte libre en anglais venu du service de remises
  (exemple vu : `"No eligible entitlement"`). **Ce n'est pas un code**, il peut
  changer, et il n'est pas fait pour être montré au client.

Les quatre motifs de la note produit (code expiré, non éligible, déjà utilisé,
budget épuisé) ne sont donc pas distinguables aujourd'hui. En attendant :
afficher un message unique du type « Cette offre ne s'applique pas à cette
course », et prévoir dans la maquette l'emplacement des quatre messages précis.

## 6. Un seul appui, une seule action

| Action | Protection côté serveur | À faire côté appli |
|---|---|---|
| Demander un devis | Aucune nécessaire (pas d'effet) | Rien |
| Commander (`POST /v1/rides`) | Un devis ne sert qu'une fois : le second envoi répond `409 QUOTE_ALREADY_USED`. Un client ne peut pas avoir deux courses actives : `409 ACTIVE_RIDE_ALREADY_EXISTS` | Désactiver le bouton dès l'appui. Sur l'une de ces deux erreurs, ou après une coupure réseau, appeler `GET /v1/rides/active/current` et reprendre la course existante au lieu de recommander |
| Préparer le paiement (`prepare`) | Pas d'en-tête `Idempotency-Key` sur cette route | Désactiver le bouton ; après une coupure, relire `GET /v1/payments/{ride_id}` avant de renvoyer |
| Confirmer les espèces (chauffeur) | Voir section 7 | Désactiver le bouton ; relire le paiement après une coupure |

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

Bonus professionnels (bonus d'accueil, bonus de performance) : rien n'est
exposé à l'appli. Dans le wallet chauffeur (`GET /v1/drivers/me/wallet`),
`reserved_balance` est l'argent d'un **retrait en cours**, pas un bonus bloqué.
Ne pas l'utiliser pour l'écran « bloqué / retirable » de la note produit.

## 8. Ce qui manque, et à qui le demander

Ces points ne sont ni dans DiddiGo ni ouverts à l'appli ailleurs : le service
de remises (DiddiRewards) n'a que des routes de service à service, aucune route
pour un utilisateur connecté.

| Manque | Conséquence pour l'appli | Proposition |
|---|---|---|
| Liste des offres du client (titre, texte, condition, date de fin, services, progression) | Pas d'écran « Mes offres », et pas de `campaign_id` à envoyer au devis | Route à créer ; propriétaire à décider (PM) |
| Saisie d'un code promo ou de parrainage | Pas d'écran de saisie branchable | Route à créer côté remises |
| Mon code de parrainage | Pas d'écran de partage branchable | Route à créer côté remises |
| Motifs de refus sous forme de codes | Un seul message générique (section 5) | Codes stables dans `rewards.reason` |
| Remise réelle connue avant la validation | Écart avec la règle « le prix affiché est le prix payé » (section 4) | Faire refuser la commande par `POST /v1/rides` quand la remise a baissé, avec le nouveau prix et le motif, pour que le client confirme (DiddiGo, voir section 10) |
| Bonus professionnels : bloqué, retirable, en cours de versement, historique, repris | Aucun écran bonus branchable | Routes à créer ; lien avec le wallet chauffeur à décider |
| Pourcentage, plafond, textes d'offre | Ne pas les afficher | Fournis par la future liste des offres |

États de la note produit, côté client DiddiGo, avec ce qui existe :

| État | Disponible aujourd'hui ? |
|---|---|
| Disponible | Seulement « une remise s'applique à ce devis » (`eligible: true`) |
| En cours (progression) | Non |
| Utilisable | Oui, au devis : `discount_amount_minor` |
| Utilisé | Oui, par course : `discount_amount_minor` > 0 sur une course payée |
| Expiré | Non (seulement l'expiration du devis, `expires_at`) |
| Refusé | Partiel : `eligible: false` + texte libre |
| Annulé ou repris | Non visible par le client |
| Bloqué, Retirable, En cours de versement (professionnels) | Non |

## 9. Ce que vous pouvez construire dès maintenant

1. Le bloc « détail du prix » (prix initial, remise, à payer) sur le devis, la
   course en cours, l'écran de paiement, le reçu et l'historique.
2. L'écran de fin de course chauffeur avec le montant à encaisser.
3. Le message « votre remise a changé » après la commande (section 4).
4. Les messages de refus, avec un texte générique pour l'instant.
5. Les maquettes de la liste des offres, de la saisie de code, du parrainage et
   des bonus professionnels, en attendant les routes de la section 8.

Pour tester sur le staging : une campagne de test existe
(`ce99efdd-3e7f-4efd-85d3-09f4260afc8d`, comptes review). Demander à l'équipe de
test si elle est encore active avant de vous en servir.

## 10. Écran par écran : maquettes Figma du 25 novembre

Maquettes lues : fichier « DiddiFree — Compte unique · Utilisateur / Pro », page
« 🎁 Promotions et bonus », sections 01 à 04 (la section 05 est DiddiAdmin, hors
de ce document). Pour chaque écran : ce qu'il affiche, et si le serveur le
fournit aujourd'hui.

Légende : **Oui** = fourni par DiddiGo aujourd'hui. **Montants seuls** = les
francs sont fournis, pas les libellés. **Non** = aucune route.

### Section 01 — Mes offres, le prix réel, ce qui change (client)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| 01 Mes offres — disponibles | Liste d'offres : nom, valeur (« −50 % »), nombre d'usages, condition, plafond, progression (« 1 utilisée sur 3 »), date de fin, service, badge d'état ; compteur « Disponibles · 4 » ; onglet Historique | **Non** |
| 02 Détail — les six réponses | Les six réponses en phrases, catégories de véhicule concernées (« Standard, Confort et Moto »), date et heure de fin | **Non** |
| 03 Estimation — remise appliquée | Prix barré 1 500 F, prix remisé 750 F, ligne « −750 F », bouton « Commander · 750 FCFA » | **Montants seuls** : `estimated_fare`, `rewards.discount_amount_minor`, `rewards.final_amount_minor` (section 3.1) |
| 03, même écran | Nom de l'offre (« Bienvenue »), pourcentage (« −50 % »), rang (« 2e course sur 3 »), plafond (« 1 000 F max ») | **Non** |
| 04 Remise modifiée avant validation | « Le prix a changé — avant que tu commandes », motif (« n'a plus de budget »), avant / maintenant, « Rien n'a été débité », boutons « Commander à 1 500 FCFA » et « Ne pas commander » | **Non, et le serveur fait aujourd'hui autre chose** : voir ci-dessous |
| 05 Reçu — prix, remise, payé | Prix de la course, remise, « Payé en espèces » | **Oui** : `gross_amount`, `discount_amount_minor`, `client_payable_amount` (section 3.4) |
| 05, même écran | Nom et pourcentage de l'offre, « Il te reste 1 course à −50 % jusqu'au 31 déc. » | **Non** |
| 06 Panier (DiddiFood) | Hors DiddiGo. À noter pour DiddiGo : « Retirer » un code pour le garder suppose que le client peut choisir de ne pas appliquer une offre. DiddiGo ne le permet pas aujourd'hui | **Non** |
| 07 Planche des sept états client | Disponible, en cours, utilisable, utilisée, expirée, refusée (avec motif), reprise après remboursement | **Non** (seul « une remise s'applique à ce devis » existe) |

Trois écarts entre ces maquettes et le serveur, à trancher avant de brancher :

1. **« Rien à saisir : la remise s'applique seule »** (écran 02). Aujourd'hui
   DiddiGo n'applique une remise que si l'appli envoie un `campaign_id`. Pour
   tenir cette promesse, le serveur doit choisir lui-même l'offre du client au
   devis. Ce n'est pas fait.
2. **« Le prix a changé, avant que tu commandes »** (écran 04). Aujourd'hui, si
   la remise a baissé, DiddiGo **crée quand même la course** avec la remise
   réduite (section 4). L'écran 04 demande l'inverse : ne rien créer, montrer
   l'ancien et le nouveau prix avec le motif, et attendre l'accord du client.
   Il faut une évolution de `POST /v1/rides` : refuser la commande avec une
   erreur dédiée qui porte le nouveau prix et le motif. Tant qu'elle n'existe
   pas, l'appli ne peut afficher cet écran qu'après coup, avec « Annuler la
   course » à la place de « Ne pas commander », et la phrase « Rien n'a été
   débité » reste vraie (le paiement n'a lieu qu'en fin de course).
3. **Pourcentage, nom, rang et plafond de l'offre** (écrans 03 et 05). Le
   serveur ne renvoie que des francs. Ces libellés ne doivent pas être déduits
   par l'appli (un « −50 % » plafonné à 1 000 F ne se recalcule pas à partir
   de −750 F).

### Section 02 — Saisir un code, parrainer, comprendre un refus (client)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Code · vérification | Envoi d'un code, un seul envoi même après double appui (« demande idempotente côté serveur ») | **Non** |
| Code · accepté | Ce que le code donne, où, jusqu'à quand, ce que gagne le parrain | **Non** |
| Code · refusé | Motif en clair : expiré, non éligible, déjà utilisé, budget épuisé (« le texte exact vient du serveur ») | **Non** |
| Parrainage · mon code | Mon code, gain des deux côtés, limites (« 10 amis par mois », « plafonnée à 1 000 F ») seulement si elles existent | **Non** |
| Parrainage · suivi | Liste des filleuls avec état (gagnée, en attente, non éligible) et compteur | **Non** |
| Offre · reprise | Commande remboursée, remise reprise, code de nouveau utilisable | **Non** |

Le service de remises a déjà des routes de parrainage, mais de service à
service seulement : l'appli ne peut pas les appeler.

### Section 03 — Bonus professionnels (chauffeur, livreur, restaurant)

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Bonus · vue d'ensemble | Totaux « Retirable » et « Bloqué », liste des bonus avec progression et date de fin | **Non** |
| Bonus d'accueil · paliers | Dix paliers de 1 000 F, débloqués ou non, règle d'expiration | **Non** |
| Bonus de performance · en cours | « 32 / 50 courses », temps restant, ce qui compte et ne compte pas | **Non** |
| Bonus · en cours de versement | Étapes : objectif atteint, bonus validé, versement en cours | **Non** |
| Bonus · historique et planche des neuf états | Versé, débloqué, repris, expiré, gelé | **Non** |
| Bonus · suivi sur l'accueil | Pastille « Objectif semaine · 32/50 », « Bonus débloqué aujourd'hui » | **Non**. « Gagné aujourd'hui » existe déjà (`GET /v1/drivers/me/wallet/earnings`), sans les bonus |

### Section 04 — Portefeuille professionnel

| Écran | Ce que l'écran affiche | Fourni ? |
|---|---|---|
| Portefeuille · deux soldes | « Solde retirable » | **Oui** : `available_balance` de `GET /v1/drivers/me/wallet` |
| même écran | « Bonus bloqué 6 000 F », progression, « Il te reste 6 courses » | **Non**. Ne pas utiliser `reserved_balance` (retrait en cours) |
| Portefeuille · mouvements | Liste des mouvements, filtre « Retraits » | **Oui** : `GET /v1/drivers/me/wallet/ledger` |
| même écran | Filtre « Bonus », lignes débloqué / versé / repris avec l'offre d'origine | **Non** : le wallet DiddiGo n'a aucun mouvement de type bonus |
| Retrait · plafonné au retirable | Montant, frais, « Tu reçois » | **Oui** : parcours de retrait existant (brief du 10 octobre) |
| même écran | « Les 6 000 F de bonus bloqué ne peuvent pas être retirés » | **Non** |
| Mouvement · bonus repris | Montant repris, raison, offre, « Contester ce mouvement » | **Non** |

Ces maquettes placent les bonus dans le portefeuille DiddiGo. Aujourd'hui les
bonus n'y entrent pas : ni solde bloqué, ni mouvement bonus. C'est une
décision d'architecture à prendre (question ouverte ci-dessous), pas un simple
branchement.

## 11. Questions ouvertes

- D'où l'appli obtient-elle `campaign_id` ? (bloquant pour le branchement)
- Une seule campagne par devis aujourd'hui. Que faire si le client a plusieurs
  offres : le serveur choisit-il la meilleure, ou le client choisit-il ?
- Qui expose les routes « offres », « codes » et « bonus » à l'appli : chaque
  service (DiddiGo, DiddiFood, DiddiSend) ou une porte commune ?
- Le client doit-il pouvoir refuser une remise réduite avant la création de la
  course ? La maquette 04 dit oui ; le serveur fait aujourd'hui l'inverse
  (sections 4 et 10).
- Le serveur doit-il choisir seul l'offre au devis (« rien à saisir »,
  maquette 02), sans `campaign_id` envoyé par l'appli ?
- Bonus professionnels : il est décidé (25 novembre) que chaque service paie
  le bonus dans son propre portefeuille, donc dans le wallet DiddiGo pour un
  chauffeur. Ce qui reste ouvert : le solde bloqué, les paliers, les états et
  la progression des maquettes de la section 04 (ticket PM 037).
