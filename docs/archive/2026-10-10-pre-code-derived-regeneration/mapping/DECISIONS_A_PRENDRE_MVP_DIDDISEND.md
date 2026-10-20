# DiddiSend — décisions à prendre avant le gel du code du 18 novembre 2026

Relevé du 9 octobre 2026. Même méthode et mêmes consignes de triage que
[`archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md`](archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md), qui couvre Common et DiddiGo.

**26 questions** restent à trancher, sur 41 points relevés. Les trois critères
du focus MVP :

1. une contradiction bloquante entre le code existant et le parcours utilisateur ;
2. un comportement métier qui bloque le déroulement d'une commande ou d'une course ;
3. un cas limite qui empêche d'aller au bout d'un parcours principal.

Le reste est fermé : **6** questions de valeur dont le défaut du code fait foi et part
en variable d'environnement, **0** sujets légaux traités par procédure manuelle au
support, **9** hors des trois critères. Tout est listé en fin de document, rien n'est
écarté en silence.

| Axe | Questions |
| --- | --- |
| Décisions produit | 17 |
| Décisions techniques | 9 |
| **Total** | **26** |

| Parcours | Attendu | Questions |
| --- | --- | --- |
| `PAR-020` | Créer une livraison | 8 |
| `PAR-021` | Collecter, suivre et remettre le colis | 7 |
| `PAR-022` | Encaisser, régulariser et retirer | 4 |
| `PAR-023` | Limites du lancement | 7 |

---

# Décisions produit

## `PAR-020` — Créer une livraison

**Ce que le planning attend.** Collecte, destinataire, remise, caractéristiques du colis, devis, paiement, confirmation. Contraintes colis/couverture/véhicule visibles avant création. Offre à un coursier éligible. Si aucun coursier : pas de fausse attribution. Un retry ne crée pas un 2e colis.

**Décisions produit applicables.** PROD-021 livraison colis · PROD-035 preuve et périmètre colis · PROD-041 payeur et échec imputable

**Livrable backend `BE017` — Devis, création et attribution du colis.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Valider expéditeur/destinataire, colis et couverture ; payer retenu, création idempotente et coursier éligible.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-238` Terminé(e) · `SCRUM-239` Terminé(e) · `SCRUM-241` Terminé(e) · `SCRUM-464` Terminé(e) · `SCRUM-526` A tester · `SCRUM-548` En cours

**Confluence.** Lot — DiddiSend / Expediteur et Destinataire (1310721) · DiddiSend — Brief transverse workflows, personas et parcours (4227073)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent.** `POST /v1/deliveries`, `GET /v1/deliveries`, `GET /v1/deliveries/{id}`, devis par `POST /v1/quotes` — 108 opérations exposées au total. Le payeur est modélisé (`payment_payer`, défaut `sender`) et la création porte une `idempotency_key`. Le tarif est calculé par `PricingPolicy.quote` : base 1 500, 120 par km, forfait de taille 300 / 600 / 900, relais 250, assurance 500, multiplicateur de pointe figé à 1,0 (`delivery/domain/pricing.py:30-40`).

### 1. La devise du devis de livraison est le franc CFA d'Afrique centrale, alors que la zone de lancement est Abidjan et que DiddiPay encaisse en franc CFA d'Afrique de l'Ouest

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · non désigné
- **Pourquoi retenue** · Contradiction code / parcours
- **Concerne aussi** · `PAR-021`
- **Source** · management/specs/etat/contradictions.md · section « Portée MVP » · 14/09/2026

**Réponse :**

> 

### 2. La règle produit fonde le prix sur distance + poids ou taille + urgence ; le calcul du code ne connaît aucune notion d'urgence, express ou standard

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · non désigné
- **Pourquoi retenue** · Contradiction code / parcours
- **Concerne aussi** · `PAR-021`
- **Source** · management/specs/etat/contradictions.md · section « Portée MVP » · 14/09/2026

**Réponse :**

> 

### 3. La règle produit prévoit 4 catégories de colis — léger, petit, moyen, gros ; le code utilise trois tailles pour le prix et quatre types de colis distincts, fragile ou non, qui ne recouvrent pas ces catégories

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · non désigné
- **Pourquoi retenue** · Contradiction code / parcours
- **Concerne aussi** · `PAR-021`
- **Source** · management/specs/etat/contradictions.md · section « Portée MVP » · 14/09/2026

**Réponse :**

> 

### 4. Le calcul applique une commission de 10 % alors que la commission DiddiSend décidée le 14/09 est de 20 %

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · non désigné
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-021`
- **Source** · management/specs/etat/contradictions.md · section « Portée MVP » · 14/09/2026

**Réponse :**

> 

### 5. Quelles sont les trois raisons d'échec prédéfinies ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-021` · `PAR-022`
- **Rattachement et Jira** · UC-040 L'expéditeur choisit une destination de secours en cas d'échec → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Quand une livraison échoue (destinataire absent, adresse introuvable), le colis a besoin d'une destination : un point relais par défaut, sauf choix contraire de l'expéditeur.
- **Source** · Fiche UC-040 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 6. Quels sont les frais de tentative facturés en cas d'échec de livraison ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-021`
- **Rattachement et Jira** · UC-040 L'expéditeur choisit une destination de secours en cas d'échec → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Quand une livraison échoue (destinataire absent, adresse introuvable), le colis a besoin d'une destination : un point relais par défaut, sauf choix contraire de l'expéditeur.
- **Source** · Fiche UC-040 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 7. Que se passe-t-il si aucun point relais n'est disponible dans la zone de l'échec ?

- **Nature** · Fait à établir
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-021`
- **Rattachement et Jira** · UC-040 L'expéditeur choisit une destination de secours en cas d'échec → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Quand une livraison échoue (destinataire absent, adresse introuvable), le colis a besoin d'une destination : un point relais par défaut, sauf choix contraire de l'expéditeur.
- **Source** · Fiche UC-040 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-021` — Collecter, suivre et remettre le colis

**Ce que le planning attend.** Coursier enregistre la prise en charge ; expéditeur suit. Destinataire reçoit SMS (suivi, PIN si besoin) et peut être appelé. Remise avec preuve ; personne non autorisée ne peut clore. Échec (absent, PIN KO) : parcours d'échec + support. Retour / nouvelle tentative encadrés.

**Limite que le planning déclare.** Pas de destination de secours automatique au MVP.

**Décisions produit applicables.** PROD-035 PIN destinataire et photo · PROD-047 tentative échouée et garde du colis · PROD-036 panne et remplacement

**Livrable backend `BE018` — Collecte, suivi, destinataire sans compte et preuve de remise.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Fiabiliser SMS/PIN, lien public limité et preuves protégées ; gérer remise impossible et nouvelle tentative.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-240` Terminé(e) · `SCRUM-242` Terminé(e) · `SCRUM-243` Terminé(e) · `SCRUM-244` Terminé(e) · `SCRUM-245` Terminé(e) · `SCRUM-449` Terminé(e) · `SCRUM-526` A tester · `SCRUM-539` Terminé(e)

**Confluence.** Lot — DiddiSend / Livreur (1343489) · DiddiSend — Brief transverse (4227073)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent.** Preuve de remise par code PIN réellement implémentée : `proof/domain/pin.py`, `proof/application/pin_service.py`, champ `delivery_pin` sur l'entité, le modèle, le dépôt et le routeur. Lien public de suivi par `share_token`. `GET /v1/deliveries/{id}/relay-scans` expose les scans.

### 1. Que fait le système d'un colis que le coursier détient encore à la fin de sa journée ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-048 Le livreur met à jour sa disponibilité → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Un coursier doit pouvoir se déclarer disponible pour recevoir des offres, ou indisponible pour s'arrêter — sans pouvoir partir avec un colis d'un client encore en sa possession.
- **Source** · Fiche UC-048 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Existe-t-il un chemin pour annuler ou signaler l'absence de colis au point de collecte, distinct d'un échec de livraison ?

- **Nature** · Fait à établir
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-043 Le livreur confirme la prise en charge du colis → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Quand le coursier récupère le colis chez l'expéditeur, il doit le confirmer dans l'application, avec une preuve qui protège les deux parties en cas de litige ultérieur.
- **Source** · Fiche UC-043 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Pas de destination de secours automatique au MVP.

- **Nature** · Point flou à fermer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Limite que le planning déclare lui-même ouverte
- **Source** · Planning de lancement, onglet « Parcours sources » · 09/10/2026

**Réponse :**

> 

## `PAR-022` — Encaisser, régulariser et retirer

**Ce que le planning attend.** Paiement numérique ou cash. Commission coursier 18 % (aussi sur les missions Food). Voit ses gains ET le cash à reverser (dette cash ≠ gain retirable). Plafonds, échéances, reversements partiels, déblocage après régularisation. Recharge wallet, retrait des gains avec bénéficiaire/frais/net.

**Limite que le planning déclare.** Assiette de la commission à préciser.

**Décisions produit applicables.** PROD-033 encours cash coursier · PROD-004 commission sur la livraison · PROD-032 retraits sans minimum

**Livrable backend `BE019` — Wallet livreur, cash à reverser, recharge et retrait.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Aligner seuil 1 000 F et dette cash maximale 15 000 F ; contrôler dette projetée ; reversement partiel distinct de recharge ; livrer retrait.

Blocage déclaré par le planning : Contrat/intégration à fermer sur staging ; voir tickets liés.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-100` À faire · `SCRUM-101` Revue en cours · `SCRUM-103` À faire · `SCRUM-450` Terminé(e) · `SCRUM-451` Terminé(e) · `SCRUM-452` Terminé(e) · `SCRUM-454` Revue en cours · `SCRUM-459` Terminé(e) · `SCRUM-475` Terminé(e) · `SCRUM-553` A tester · `SCRUM-572` À faire

**Confluence.** Lot — Argent des pros (1015809) · Lot — DiddiSend / Livreur (1343489)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent.** Garde d'encours cash à trois conditions dans `delivery/application/eligibility.py:150-164` : nombre de livraisons non soldées, montant à reverser, échéance la plus ancienne dépassée — sinon `CourierCashRemittanceRequired`. Wallet coursier exposé (`/v1/couriers/me/wallet`, `/entries`, `/topups/{id}`). Valeurs déjà en configuration : `max_unsettled_deliveries = 3`, `max_amount_to_remit = 25000`, `remittance_deadline_hours = 24` (`config/diddisend.toml:34-41`). La commission plateforme vaut **10 %**, codée en dur à `pricing.py:45`, et elle est **ajoutée** au sous-total : `courier_payout_estimate` égale le sous-total, donc la commission est portée par le payeur et non prélevée sur le coursier. `partner_share_percent = 0` neutralise la part partenaire.

### 1. La commission de DiddiSend vaut 10 % dans le code et 18 % dans le planning : quel taux fait foi, et sur quelle assiette ?

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · `pricing.py:45` applique `subtotal × 0,1` et l'**ajoute** au sous-total, si bien que `courier_payout_estimate` égale le sous-total : la commission est payée par le client, pas prélevée sur le coursier. Le planning annonce « commission coursier 18 % » et déclare lui-même l'assiette à préciser.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 2. Le plafond de dette cash du coursier vaut 25 000 F en configuration et 15 000 F dans le livrable `BE019` : lequel s'applique au lancement ?

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · `config/diddisend.toml` pose `max_amount_to_remit = 25000`. `BE019` demande d'« aligner seuil 1 000 F et dette cash maximale 15 000 F » ; le seuil de 1 000 F n'a aucun équivalent dans la configuration de DiddiSend.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. Le reversement du cash coursier se déclenche avant l'échéance dans la plupart des cas : qui enregistre le reversement, et où ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · La garde bloque dès 3 livraisons non soldées, 25 000 F à reverser ou une échéance de 24 h dépassée. `SCRUM-101` « Un responsable enregistre le reversement d'espèces d'un coursier » est en « Revue en cours » et le parcours physique du dépôt n'est pas décrit.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 4. Assiette de la commission à préciser.

- **Nature** · Point flou à fermer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Limite que le planning déclare lui-même ouverte
- **Source** · Planning de lancement, onglet « Parcours sources » · 09/10/2026

**Réponse :**

> 

## `PAR-023` — Limites du lancement

**Ce que le planning attend.** Pas de points relais, partenaires ni flottes. Missions Food exclusives : pas groupées, coursier occupé non sollicité. Incidents, réclamations, stats de base et anti-fraude inclus.

**Décisions produit applicables.** PROD-001 points relais, partenaires et flottes hors MVP · PROD-022 livraison Food exclusive

**Livrable backend `BE017` — Devis, création et attribution du colis.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Valider expéditeur/destinataire, colis et couverture ; payer retenu, création idempotente et coursier éligible.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-238` Terminé(e) · `SCRUM-239` Terminé(e) · `SCRUM-241` Terminé(e) · `SCRUM-464` Terminé(e) · `SCRUM-526` A tester · `SCRUM-548` En cours

**Livrable backend `BE022` — Livraison repas exclusive, préparation et heure d’arrivée estimée.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Lier commande et livraison unique ; coursier/véhicule compatible ; synchroniser préparation, collecte, remise et estimation.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-44` Terminé(e) · `SCRUM-45` Terminé(e) · `SCRUM-46` Terminé(e) · `SCRUM-47` À faire · `SCRUM-54` À faire · `SCRUM-55` À faire · `SCRUM-404` A tester · `SCRUM-414` A tester · `SCRUM-469` Terminé(e) · `SCRUM-552` A tester

**Confluence.** Lot — DiddiSend / Points relais (1081361)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent, au-delà de la limite déclarée.** Le module `relay` existe avec ses propres routes — `/v1/relay-points`, `/me`, `/scan-in`, `/scan-out`, `/stats`, `/problems`, `/v1/admin/relay-points/pending`, `/{id}/approve` — et le module `partner` aussi : `/v1/admin/partners`, `/{id}/status`, `/{id}/members`, `/v1/partners/{id}/wallet`, `/wallet-policy`. L'exclusivité des missions est imposée côté serveur à `eligibility.py:166-171`.

### 1. Les points relais et les partenaires sont codés et exposés alors que le planning les exclut du lancement : les ouvre-t-on, ou les ferme-t-on par configuration ?

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Contexte** · `PAR-023` déclare « pas de points relais, partenaires ni flottes ». Les modules `relay` et `partner` existent avec leurs routes publiques et d'administration, et `PricingPolicy` facture déjà un `relay_fee` de 250 F sur les modes relais.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 2. Qui supporte la perte d'un colis endommagé ou manquant chez un relais ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Juridique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-344 Le point relais signale un colis endommagé ou manquant → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Un colis peut arriver endommagé, ou être introuvable au moment où on le cherche. Le gérant du relais doit pouvoir le signaler, pour que le support prenne le relais.
- **Source** · Fiche UC-344 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Un colis retourné à l'expéditeur sans remise donne-t-il quand même lieu à une rémunération partielle du relais pour la garde ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-343 Le système calcule la rémunération du point relais par colis traité → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Un point relais rend un service commercial qui mérite rémunération. Ce calcul existe déjà en germe dans le prix de la livraison ; il doit être persisté pour devenir consultable (UC-056).
- **Source** · Fiche UC-343 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Décisions techniques

## `PAR-020` — Créer une livraison

**Ce que le planning attend.** Collecte, destinataire, remise, caractéristiques du colis, devis, paiement, confirmation. Contraintes colis/couverture/véhicule visibles avant création. Offre à un coursier éligible. Si aucun coursier : pas de fausse attribution. Un retry ne crée pas un 2e colis.

**Décisions produit applicables.** PROD-021 livraison colis · PROD-035 preuve et périmètre colis · PROD-041 payeur et échec imputable

**Livrable backend `BE017` — Devis, création et attribution du colis.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Valider expéditeur/destinataire, colis et couverture ; payer retenu, création idempotente et coursier éligible.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-238` Terminé(e) · `SCRUM-239` Terminé(e) · `SCRUM-241` Terminé(e) · `SCRUM-464` Terminé(e) · `SCRUM-526` A tester · `SCRUM-548` En cours

**Confluence.** Lot — DiddiSend / Expediteur et Destinataire (1310721) · DiddiSend — Brief transverse workflows, personas et parcours (4227073)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent.** `POST /v1/deliveries`, `GET /v1/deliveries`, `GET /v1/deliveries/{id}`, devis par `POST /v1/quotes` — 108 opérations exposées au total. Le payeur est modélisé (`payment_payer`, défaut `sender`) et la création porte une `idempotency_key`. Le tarif est calculé par `PricingPolicy.quote` : base 1 500, 120 par km, forfait de taille 300 / 600 / 900, relais 250, assurance 500, multiplicateur de pointe figé à 1,0 (`delivery/domain/pricing.py:30-40`).

### 1. La formule de répartition du prix de la livraison rend le versement du coursier égal au sous-total avant commission ; est-ce voulu ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-021`
- **Source** · management/specs/etat/a-verifier.md · section « Portée MVP » · 14/09/2026

**Réponse :**

> 

## `PAR-021` — Collecter, suivre et remettre le colis

**Ce que le planning attend.** Coursier enregistre la prise en charge ; expéditeur suit. Destinataire reçoit SMS (suivi, PIN si besoin) et peut être appelé. Remise avec preuve ; personne non autorisée ne peut clore. Échec (absent, PIN KO) : parcours d'échec + support. Retour / nouvelle tentative encadrés.

**Limite que le planning déclare.** Pas de destination de secours automatique au MVP.

**Décisions produit applicables.** PROD-035 PIN destinataire et photo · PROD-047 tentative échouée et garde du colis · PROD-036 panne et remplacement

**Livrable backend `BE018` — Collecte, suivi, destinataire sans compte et preuve de remise.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Fiabiliser SMS/PIN, lien public limité et preuves protégées ; gérer remise impossible et nouvelle tentative.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-240` Terminé(e) · `SCRUM-242` Terminé(e) · `SCRUM-243` Terminé(e) · `SCRUM-244` Terminé(e) · `SCRUM-245` Terminé(e) · `SCRUM-449` Terminé(e) · `SCRUM-526` A tester · `SCRUM-539` Terminé(e)

**Confluence.** Lot — DiddiSend / Livreur (1343489) · DiddiSend — Brief transverse (4227073)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent.** Preuve de remise par code PIN réellement implémentée : `proof/domain/pin.py`, `proof/application/pin_service.py`, champ `delivery_pin` sur l'entité, le modèle, le dépôt et le routeur. Lien public de suivi par `share_token`. `GET /v1/deliveries/{id}/relay-scans` expose les scans.

### 1. La règle produit exige une preuve de collecte — photo plus code, ou code QR ; le code enregistre une preuve de collecte sans photo ni vérification

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-043 Le livreur confirme la prise en charge du colis → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Quand le coursier récupère le colis chez l'expéditeur, il doit le confirmer dans l'application, avec une preuve qui protège les deux parties en cas de litige ultérieur.
- **Source** · Fiche UC-043 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le trou de suivi en cas de perte de connexion doit-il être corrigé par une persistance de la position, ou par un mécanisme de reprise côté application ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-044 Le livreur envoie sa position pendant la livraison → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Le point de départ et le point d'arrivée sont visibles à l'expéditeur et au destinataire pendant une livraison en cours.
- **Source** · Fiche UC-044 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. En production, la vérification que l'acteur d'une collecte ou d'une remise est bien le coursier assigné est-elle effective ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-045 Le livreur confirme la livraison avec preuve → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · La remise du colis au destinataire est le moment décisif de toute la prestation. Elle doit être prouvée par une photo, pour protéger le coursier et la plateforme en cas de contestation.
- **Source** · Fiche UC-045 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Un coursier peut-il aujourd'hui passer hors ligne alors qu'il détient un colis collecté ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Concerne aussi** · `PAR-022`
- **Rattachement et Jira** · UC-048 Le livreur met à jour sa disponibilité → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Un coursier doit pouvoir se déclarer disponible pour recevoir des offres, ou indisponible pour s'arrêter — sans pouvoir partir avec un colis d'un client encore en sa possession.
- **Source** · Fiche UC-048 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-023` — Limites du lancement

**Ce que le planning attend.** Pas de points relais, partenaires ni flottes. Missions Food exclusives : pas groupées, coursier occupé non sollicité. Incidents, réclamations, stats de base et anti-fraude inclus.

**Décisions produit applicables.** PROD-001 points relais, partenaires et flottes hors MVP · PROD-022 livraison Food exclusive

**Livrable backend `BE017` — Devis, création et attribution du colis.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Valider expéditeur/destinataire, colis et couverture ; payer retenu, création idempotente et coursier éligible.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-238` Terminé(e) · `SCRUM-239` Terminé(e) · `SCRUM-241` Terminé(e) · `SCRUM-464` Terminé(e) · `SCRUM-526` A tester · `SCRUM-548` En cours

**Livrable backend `BE022` — Livraison repas exclusive, préparation et heure d’arrivée estimée.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Lier commande et livraison unique ; coursier/véhicule compatible ; synchroniser préparation, collecte, remise et estimation.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-44` Terminé(e) · `SCRUM-45` Terminé(e) · `SCRUM-46` Terminé(e) · `SCRUM-47` À faire · `SCRUM-54` À faire · `SCRUM-55` À faire · `SCRUM-404` A tester · `SCRUM-414` A tester · `SCRUM-469` Terminé(e) · `SCRUM-552` A tester

**Confluence.** Lot — DiddiSend / Points relais (1081361)

**État du code au 09/10, relevé dans `diddi-send`.** **Présent, au-delà de la limite déclarée.** Le module `relay` existe avec ses propres routes — `/v1/relay-points`, `/me`, `/scan-in`, `/scan-out`, `/stats`, `/problems`, `/v1/admin/relay-points/pending`, `/{id}/approve` — et le module `partner` aussi : `/v1/admin/partners`, `/{id}/status`, `/{id}/members`, `/v1/partners/{id}/wallet`, `/wallet-policy`. L'exclusivité des missions est imposée côté serveur à `eligibility.py:166-171`.

### 1. UC-054 décrit un retrait par le client qui termine la livraison ; le scan de sortie fait passer la livraison en cours de remise dans tous les cas

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Rattachement** · DiddiSend / Points relais
- **Contexte** · Ce lot couvre le commerce de quartier qui garde un colis. Un administrateur crée, approuve ou suspend le relais.
- **Source** · Fiche de lot « DiddiSend / Points relais » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. DiddiSend impose l'exclusivité côté serveur, contrairement à ce que supposent DiddiFood et le ticket `SCRUM-47` : la garantie est-elle considérée comme acquise ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Contexte** · `eligibility.py:166-171` lève `CourierExclusiveMissionActive` si le coursier a déjà une mission exclusive active, et `ExclusiveDeliveryRequiresFreeCourier` si une mission exclusive est proposée à un coursier chargé ; le type de véhicule requis est contrôlé juste après. `SCRUM-47` « UC-360 — Mission repas exclusive, non groupable » est pourtant encore « À faire ».
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. Le code PIN ou QR de vérification d'identité au retrait est-il aujourd'hui vérifié par le code, ou seulement prévu ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-054 Le destinataire ou l'expéditeur retire un colis au point relais → aucun ticket cité par le planning · phase backlog MVP
- **Contexte** · Un client — destinataire ou expéditeur selon le cas — doit pouvoir venir chercher lui-même son colis au point relais, avec une vérification que la bonne personne repart avec le bon colis.
- **Source** · Fiche UC-054 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Le retour à l'expéditeur suit-il le même dispatch qu'une livraison ordinaire, avec les mêmes risques d'échec ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-342 Le système déclenche le retour à l'expéditeur à l'échéance de la durée de garde → aucun ticket cité par le planning · phase backlog V1
- **Contexte** · Un colis ne peut pas rester indéfiniment chez un relais. Passé une durée de garde, il doit être retourné à l'expéditeur automatiquement, sans qu'un humain ait à s'en souvenir.
- **Source** · Fiche UC-342 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Valeurs fermées — à reporter en variable d'environnement

Consigne de lancement : toute question de durée, de seuil, de limite ou de valeur numérique est
fermée. Le défaut actuel du code fait foi et part en variable d'environnement — aucune valeur
modifiable à chaud, pour qu'un changement de comportement passe par un redéploiement traçable.

| Question fermée | Parcours | Source |
| --- | --- | --- |
| Quel est le barème de prix de la livraison — part fixe, part au kilomètre, part par catégorie, majoration express ? | `PAR-020` | Fiche UC-032 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Au bout de combien de temps sans position un coursier cesse-t-il d'être considéré comme disponible ? | `PAR-021` | Fiche UC-049 · section « Questions ouvertes » · corpus du 14/09/2026 |
| À partir de quel âge une position du coursier est-elle présentée comme ancienne ? | `PAR-020` | Fiche UC-034 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Combien de temps un colis reste-t-il en garde avant retour à l'expéditeur ? | `PAR-023` | Fiche UC-342 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Combien de tentatives de remise avant de déclarer un échec ? | `PAR-021` | Fiche de lot « DiddiSend / Livreur » · section « Questions ouvertes » · corpus du 14/09/2026 |
| Quelle est la rémunération d'un point relais ? | `PAR-023` | Fiche de lot « DiddiSend / Points relais » · section « Questions ouvertes » · corpus du 14/09/2026 |

# Fermées — légal et conformité

Non bloquant pour le code MVP. Procédure manuelle au support pour le lancement.

| Question | Parcours | Nature | Décideur |
| --- | --- | --- | --- |
| _aucun sujet légal relevé sur ce périmètre_ | — | — | — |

# Hors des trois critères du focus MVP

9 questions conservées pour après le gel.

| Question | Parcours | Axe | Nature | Décideur |
| --- | --- | --- | --- | --- |
| Le barème de frais et la réduction de 50 % tranchés le 14/09 sont-ils déjà appliqués tels quels dans le calcul, ou restent-ils à implémenter précisément ? | `PAR-020` | Technique | Fait à établir | Technique |
| Comment l'expéditeur choisit-il un relais parmi ceux disponibles — proximité du destinataire, liste complète, recommandation ? | `PAR-023` | Produit | Décision à prendre | Produit |
| L'interface indique-t-elle clairement à l'expéditeur que les codes affichés ne sont aujourd'hui vérifiés par aucun endpoint ? | `PAR-020` | Produit | Fait à établir | Produit |
| Existe-t-il une route permettant de lister les livraisons présentes dans un relais donné, autre que le comptage ? | `PAR-023` | Technique | Fait à établir | Technique |
| Le choix d'un relais dès la création change-t-il le prix de la livraison, par rapport à une livraison directe ? | `PAR-023` | Produit | Décision à prendre | Produit |
| Quel algorithme d'optimisation de tournée est envisagé — DiddiMap fournit-il déjà une capacité de ce type ? | `PAR-021` | Technique | Fait à établir | Technique |
| L'expéditeur ou le destinataire est-il notifié quand un colis entre au relais ? | `PAR-023` | Produit | Fait à établir | Produit |
| Un relais peut-il refuser un colis à l'entrée, et pour quels motifs ? | `PAR-023` | Produit | Décision à prendre | Produit |
| Le retour à l'expéditeur est-il facturé, et à qui ? | `PAR-023` | Produit | Décision à prendre | Administration |

# Sources

| Source | Date | Rôle |
| --- | --- | --- |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx` | 09/10/2026 | source de spécification principale : parcours, livrables, tickets |
| `management/specs` — fiches de use case et de lot, registres `etat/` | 14/09/2026 | complément : les questions ouvertes |
| `diddi-scope-document` — registre `PROD-xxx` | 09/10/2026 | cible produit |
| dépôt `diddi-send` | branche courante | état du code, relu aujourd'hui |
| Jira `diddifree` | 09/10/2026, lecture seule | statuts relevés en direct |
| Confluence espace `DIDDIFREE` | 09/10/2026, lecture seule | pages de lot |

Les parcours Common et DiddiPay, partagés entre les trois services, sont traités dans le
relevé [`DECISIONS_A_PRENDRE_MVP.md`](archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md),
archivé depuis la réorganisation du 09/10 — le MVP DiddiGo actif est porté par
[`DIDDIGO-MVP-FIGE.md`](DIDDIGO-MVP-FIGE.md).

Ce document est un **recueil de questions**, pas un registre de décisions : il n'arbitre rien
et ne définit aucun périmètre. Les réponses, une fois prises, ont leur place dans la référence
produit du service concerné.
