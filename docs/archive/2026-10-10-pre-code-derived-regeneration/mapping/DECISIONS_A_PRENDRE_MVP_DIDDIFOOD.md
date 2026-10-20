# DiddiFood — décisions à prendre avant le gel du code du 18 novembre 2026

Relevé du 9 octobre 2026. Même méthode et mêmes consignes de triage que
[`archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md`](archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md), qui couvre Common et DiddiGo.

> **Écart de classification, à signaler avant lecture.** Les 31 use cases DiddiFood portent la phase `Later` sur les quatre axes du backlog du 14/09. Le planning du 09/10 place pourtant PAR-024 à PAR-027 au MVP, avec les livrables BE020 à BE023 en priorité P0 et P1 sur la fenêtre du 14 au 23 octobre, et `PROD-001` énonce que Go, Send et Food lancent leurs parcours essentiels à Abidjan. Ce document suit le planning, source de spécification principale, et ne filtre donc pas sur la phase du backlog. La divergence elle-même est portée en question ci-dessous.

**27 questions** restent à trancher, sur 58 points relevés. Les trois critères
du focus MVP :

1. une contradiction bloquante entre le code existant et le parcours utilisateur ;
2. un comportement métier qui bloque le déroulement d'une commande ou d'une course ;
3. un cas limite qui empêche d'aller au bout d'un parcours principal.

Le reste est fermé : **7** questions de valeur dont le défaut du code fait foi et part
en variable d'environnement, **0** sujets légaux traités par procédure manuelle au
support, **24** hors des trois critères. Tout est listé en fin de document, rien n'est
écarté en silence.

| Axe | Questions |
| --- | --- |
| Décisions produit | 22 |
| Décisions techniques | 5 |
| **Total** | **27** |

| Parcours | Attendu | Questions |
| --- | --- | --- |
| `PAR-024` | Choisir et commander un repas | 9 |
| `PAR-025` | Livrer avec DiddiSend | 12 |
| `PAR-026` | Recevoir ses gains et retirer | 3 |
| `PAR-027` | Litiges Food | 3 |

---

# Décisions produit

## `PAR-024` — Choisir et commander un repas

**Ce que le planning attend.** Trouve un restaurant, voit plats/prix/dispos, panier, adresse, détail plats vs livraison, paiement. Restaurant accepte ou refuse, cuisine suit la préparation et signale « prêt ». Managers gèrent dispos et accès du personnel ; la cuisine n'accède ni aux retraits ni à la finance.

**Décisions produit applicables.** PROD-023 restaurant · PROD-044 disponibilité Food · PROD-005 moyens de paiement visibles

**Livrable backend `BE020` — Restaurants, carte des plats et commande client.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Publier disponibilité, panier, prix plats/livraison, paiement et reprise d’échec sur la même commande.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-25` Terminé(e) · `SCRUM-26` Terminé(e) · `SCRUM-27` Terminé(e) · `SCRUM-28` Terminé(e) · `SCRUM-29` Terminé(e) · `SCRUM-523` Terminé(e) · `SCRUM-528` Terminé(e) · `SCRUM-547` A tester

**Livrable backend `BE021` — Restaurant, cuisine, catalogue et temps de préparation.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Finaliser images publiques catalogue, droits cuisine/manager, filtres commandes, ouvert/fermé et temps de préparation.

Blocage déclaré par le planning : Contrat/intégration à fermer sur staging ; voir tickets liés.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-35` Terminé(e) · `SCRUM-36` Terminé(e) · `SCRUM-37` Terminé(e) · `SCRUM-38` Terminé(e) · `SCRUM-39` Terminé(e) · `SCRUM-468` A tester · `SCRUM-525` À faire · `SCRUM-540` A tester · `SCRUM-541` A tester · `SCRUM-542` À faire · `SCRUM-543` À faire · `SCRUM-544` À faire · `SCRUM-545` À faire · `SCRUM-546` En cours · `SCRUM-551` A tester · `SCRUM-570` À faire

**Confluence.** Lot — DiddiFood / Client (753665) · Lot — DiddiFood / Restaurant (786433) · DiddiFood — Contrat API, proposition (720898)

**État du code au 09/10, relevé dans `diddi-food`.** **Partiel.** Modules `catalog`, `restaurants`, `ordering`, `payments` présents, 57 opérations exposées : `GET /restaurants`, `/menu`, `/dishes`, `PATCH /dishes/{id}/availability`, `POST /orders`, `GET /orders/{id}/payment`. `food_commission_bps = 1500` et `restaurant_min_withdrawal_xof = 5000` (`app/core/config.py:73,80`) correspondent aux 15 % et aux 5 000 F du planning. `delivery_time_minutes_default = 30` tient lieu de délai affiché faute de source par restaurant. `PlaceOrderIn` ne collecte **aucun courriel client**, que le prestataire de paiement exige : la route de préparation du paiement le réclame donc dans son corps de requête.

### 1. Les use cases DiddiFood sont tous classés `Later` au backlog alors que le planning les met au MVP : quelle classification fait foi pour le gel du 18 novembre ?

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Direction
- **Pourquoi retenue** · Contradiction code / parcours
- **Contexte** · Les 31 use cases Food portent `Later` sur les quatre axes du backlog du 14/09. Le planning du 09/10 place PAR-024 à PAR-027 au MVP avec BE020 à BE023 en priorité P0 et P1, et `PROD-001` dit que Food lance ses parcours essentiels.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 2. Le courriel du client doit-il être collecté à la création de commande, dans le profil, ou rester demandé au moment du paiement ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · `PlaceOrderIn` ne le collecte pas, alors que le prestataire de paiement l'exige pour le paiement en ligne. La route de préparation du paiement le réclame donc dans son corps de requête.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. Les images publiques du catalogue passent-elles par une extension de DiddiFiles, ou DiddiFood les héberge-t-il lui-même en attendant ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Direction
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Contexte** · DiddiFiles n'a pas de capacité d'actif public aujourd'hui. Héberger ailleurs débloque le catalogue mais rompt le principe « aucun module ne détient de fichier brut sauf DiddiFiles ». `SCRUM-540` et `SCRUM-541` sont « A tester », `SCRUM-542` reste « À faire ».
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 4. Quelle est la conséquence d'un refus de commande par un restaurant ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Concerne aussi** · `PAR-027`
- **Rattachement et Jira** · UC-230 Le restaurant reçoit une commande et peut l'accepter ou la refuser → `SCRUM-35` Terminé(e) · phase backlog Later
- **Contexte** · Le rôle cuisine reçoit une nouvelle commande dans sa file et l'accepte ou la refuse dans un délai décidé.
- **Source** · Fiche UC-230 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 5. Quelle est la fenêtre d'annulation d'une commande alimentaire ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-353 Le client annule sa commande dans la fenêtre autorisée → aucun ticket cité par le planning · phase backlog Later
- **Contexte** · Un client food annule sa commande, gratuitement dans une fenêtre autorisée, ou en connaissant le coût au-delà.
- **Source** · Fiche UC-353 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 6. Qui paie un repas annulé après acceptation, et qui paie un plat refusé à la livraison ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-351 Le client paie sa commande alimentaire en espèces à la livraison → aucun ticket cité par le planning · phase backlog Later
- **Contexte** · Un client food choisit de payer en espèces au moment de la livraison plutôt que via DiddiPay.
- **Source** · Fiche UC-351 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 7. Un temps de préparation annoncé engage-t-il le restaurant, et que se passe-t-il s'il est dépassé ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-231 Le restaurant indique un temps de préparation → `SCRUM-36` Terminé(e) · phase backlog Later
- **Contexte** · Le rôle cuisine annonce un temps de préparation, qui alimente l'heure d'arrivée estimée montrée au client.
- **Source** · Fiche UC-231 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 8. À quelle heure exactement un plat basculé en indisponible pour la journée est-il réactivé ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-355 Le poste cuisine bascule un plat en indisponible pour la journée, avec réactivation automatique le lendemain → aucun ticket cité par le planning · phase backlog Later
- **Contexte** · Le rôle cuisine bascule un plat en indisponible pour le reste de la journée, en un geste, sans devoir penser à le réactiver le lendemain.
- **Source** · Fiche UC-355 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-025` — Livrer avec DiddiSend

**Ce que le planning attend.** La commande crée une livraison Send liée à la même référence. Contraintes véhicule et exclusivité. États remontés à Food. Timeout : pas de doublon de mission. Événement tardif ou répété : cohérence conservée. Restaurant fermé, refus, retard, pas de coursier, échec de remise : décision visible puis support / annulation / remboursement.

**Décisions produit applicables.** PROD-022 livraison Food exclusive · PROD-029 engagement Food et incidents

**Livrable backend `BE022` — Livraison repas exclusive, préparation et heure d’arrivée estimée.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Lier commande et livraison unique ; coursier/véhicule compatible ; synchroniser préparation, collecte, remise et estimation.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-44` Terminé(e) · `SCRUM-45` Terminé(e) · `SCRUM-46` Terminé(e) · `SCRUM-47` À faire · `SCRUM-54` À faire · `SCRUM-55` À faire · `SCRUM-404` A tester · `SCRUM-414` A tester · `SCRUM-469` Terminé(e) · `SCRUM-552` A tester

**Confluence.** Lot — DiddiFood / Livreur (819201) · Lot — DiddiFood / Systeme (884737)

**État du code au 09/10, relevé dans `diddi-food`.** **Partiel.** Module `delivery` avec l'adaptateur `diddisend_adapter.py`. La charge envoyée est **complète** au regard du schéma de DiddiSend : `recipient_name`, `recipient_phone`, `sender_phone`, `package`, `delivery_mode = door_to_door`, `payment_method`, `quoted_price`, `origin_module = diddifood`, `order_reference`, `idempotency_key`, `ready_at`, `required_vehicle_type = motorcycle`, `exclusive = True`, `financial_breakdown` (`diddisend_adapter.py:69-104`). Deux limites réelles : le déclenchement à l'acceptation est **best-effort**, enveloppé dans un `try/except` pour qu'une panne Send ne transforme pas une acceptation réussie en 503 — l'échec est journalisé `delivery.request_failed_at_acceptance`, `GET /orders/{id}/delivery` renvoie 404 et la reprise est manuelle par `POST /orders/{id}/delivery/request` ; et `delivery_status_sync_enabled` vaut **`False` par défaut** (`app/core/config.py:68`), donc la remontée des états de DiddiSend vers Food ne tourne pas tant qu'elle n'est pas activée.

### 1. Comment le temps d'arrivée estimé total se compose-t-il, et que voit le client si l'un des termes est inconnu ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Use cases que la source dit bloqués** · UC-238
- **Source** · management/specs/etat/a-trancher.md · section « Portée Later » · 14/09/2026

**Réponse :**

> 

### 2. L'engagement de délai d'arrivée du coursier est figé à la commande et jamais recalculé. Est-ce acceptable pour le lancement, ou faut-il un recalcul minimal quand le restaurant met à jour son estimation de préparation ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · Deux défaillances en découlent : une préparation plus longue laisse le coursier attendre à vide, une préparation plus courte laisse le plat prêt avant son arrivée.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. La preuve de remise d'un repas est-elle une photo, comme pour un colis, ou un geste plus léger ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-237 Le livreur livre la commande au client avec confirmation de remise → `SCRUM-46` Terminé(e) · phase backlog Later
- **Contexte** · Le livreur remet la commande au client, avec une preuve, et encaisse en espèces si c'est le mode de paiement choisi.
- **Source** · Fiche UC-237 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Pour un paiement en ligne, l'attribution du coursier attend-elle le succès du paiement, ou part-elle en parallèle avec annulation en cas d'échec ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · L'attribution se déclenche à l'acceptation du restaurant. En ligne, acceptation et création de l'intention de paiement arrivent au même instant : si la recherche démarre et que le paiement échoue, un coursier est en route pour une commande à annuler.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 5. Que fait le livreur d'un repas qu'il n'a pas pu remettre ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-237 Le livreur livre la commande au client avec confirmation de remise → `SCRUM-46` Terminé(e) · phase backlog Later
- **Contexte** · Le livreur remet la commande au client, avec une preuve, et encaisse en espèces si c'est le mode de paiement choisi.
- **Source** · Fiche UC-237 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 6. Que se passe-t-il quand un restaurant est en retard sur son temps annoncé et que le livreur attend ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-236 Le livreur confirme son arrivée au restaurant et la récupération de la commande → `SCRUM-45` Terminé(e) · phase backlog Later
- **Contexte** · Le livreur confirme son arrivée au restaurant, patiente si la commande n'est pas prête, puis confirme la récupération.
- **Source** · Fiche UC-236 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 7. Que se passe-t-il si aucun livreur n'est disponible au moment où la commande est prête ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-239 Le système crée ou réserve une livraison quand la commande est acceptée, ou quand elle approche d'être prête → `SCRUM-55` À faire · phase backlog Later
- **Contexte** · Le système déclenche la création ou la réservation d'une livraison au bon moment, ni trop tôt (coursier immobilisé) ni trop tard (aucun livreur trouvé).
- **Source** · Fiche UC-239 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 8. Une acceptation de commande doit-elle rester valide quand la demande de livraison échoue, ou faut-il la refuser pour éviter une commande sans coursier ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · Le déclenchement est best-effort : une panne DiddiSend ne transforme pas une acceptation réussie en 503. L'échec est journalisé et `GET /orders/{id}/delivery` renvoie 404, avec reprise manuelle.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

## `PAR-026` — Recevoir ses gains et retirer

**Ce que le planning attend.** Commission restaurant 15 % (livraison à part). Voit écritures, montants en attente / disponibles / réservés. Gain numérique dispo après paiement confirmé + collecte confirmée par Send. Cash : régularisation Send confirmée. Retrait : minimum, frais, net, montant réservé pendant le payout ; pas de double dépense du même solde.

**Limite que le planning déclare.** Minimum 5 000 XOF à maintenir ou changer explicitement.

**Décisions produit applicables.** PROD-004 commission restaurant sur les plats · PROD-003 socle financier · PROD-032 retraits

**Livrable backend `BE023` — Wallet restaurant et demande de retrait par le manager.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Vérifier 15 %, minimum 5 000 F, fonds en attente/disponibles/réservés, bénéficiaire et transfert ; cash confirmé avant disponibilité.

Blocage déclaré par le planning : Contrat/intégration à fermer sur staging ; voir tickets liés.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-456` À faire · `SCRUM-471` A tester · `SCRUM-472` À faire · `SCRUM-484` Terminé(e) · `SCRUM-500` A tester · `SCRUM-522` A tester · `SCRUM-525` À faire

**Confluence.** Lot — DiddiFood / Partenaire (950273) · Décision — Wallet restaurant, commission et retraits DiddiFood (5537793)

**État du code au 09/10, relevé dans `diddi-food`.** **Présent.** Modules `wallets` et `payouts` : `/entries`, `/withdrawals`, `/withdrawal-quote`, `/withdrawals/{id}`. Le partage financier est contrôlé par invariant : `courier_earning + send_commission == delivery_fee` et `customer_total == order_total + delivery_fee` (`ordering/domain/entities.py:95-97`). Or `delivery_fee_xof` et `send_commission_bps` valent **0 par défaut** (`app/core/config.py:74,78`) : la livraison d'une commande Food est donc gratuite et le coursier touche zéro tant que ces valeurs ne sont pas posées. `restaurant_advance_limit_xof = 25000`, `restaurant_withdrawal_fee_xof = 0`.

### 1. Le backlog introduit un partenaire alimentaire que le glossaire de la section 3 ne définit pas, et qui ne correspond ni au pro ni au partenaire

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-243 Le partenaire consulte ses ventes, commissions, reversements et performances de préparation → aucun ticket cité par le planning · phase backlog Later
- **Contexte** · Un partenaire alimentaire consulte ses ventes, ses commissions, ses reversements et ses performances de préparation, par point de vente et consolidés.
- **Source** · Fiche UC-243 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le tarif de livraison d'une commande Food est-il porté par DiddiFood ou par le devis de DiddiSend ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · Food impose `courier_earning + send_commission == delivery_fee` et pose `delivery_fee_xof = 0` et `send_commission_bps = 0` par défaut ; DiddiSend calcule de son côté un prix complet et une commission de 10 %. Les deux chemins coexistent sans règle de préséance.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. Qui détient l'argent d'une commande payée en espèces, et par quel mécanisme le restaurant est-il payé ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Contexte** · Le coursier est un coursier DiddiSend, pas un livreur employé par DiddiFood : le modèle cash de DiddiGo ne se transpose pas. Le modèle de données `payments` a besoin de la forme visée avant d'implémenter la confirmation d'encaissement.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

## `PAR-027` — Litiges Food

**Ce que le planning attend.** Plat manquant, erreur, retard, restaurant fermé → support + décision humaine tracée.

**Limite que le planning déclare.** Exclus du MVP : retrait sur place, remplacement de plat, recharge du wallet restaurant.

**Décisions produit applicables.** PROD-029 incidents Food · PROD-034 autorité de remboursement · PROD-017 support

**Livrable backend `BE010` — Reprise humaine et suivi des tickets.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Créer et relier ticket, mission et conversation ; notifier agent ; suivre traitement et réouverture.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-58` V2 · `SCRUM-383` À faire · `SCRUM-385` À faire · `SCRUM-527` En cours · `SCRUM-532` À faire · `SCRUM-535` À faire

**Confluence.** Lot — DiddiFood / Support (917505) · Lot — DiddiAdmin (1114113)

**État du code au 09/10, relevé dans `diddi-food`.** **Partiel.** `POST /orders/{id}/refund-requests` puis `POST /admin/refund-requests/{id}/approve|reject` et `GET /admin/refund-requests` : la forme en deux temps est réelle et appliquée. Mais **aucun acteur « support »** n'est autorisé à soumettre — emplacement réservé, en attente d'une capacité support locale ou d'une intégration DiddiAdmin.

### 1. Quelle preuve un client doit-il fournir pour un plat manquant ou impropre ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-242 Le support traite les litiges food : plat manquant, erreur de commande, retard, restaurant fermé → `SCRUM-58` V2 · phase backlog Later
- **Contexte** · Un agent de support traite un litige sur une commande alimentaire (plat manquant, erreur, retard, restaurant fermé), dans la même file qu'un litige de course ou de livraison.
- **Source** · Fiche UC-242 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Qui peut soumettre une demande de remboursement, tant qu'aucun acteur support n'existe dans DiddiFood ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Contexte** · La forme en deux temps — soumission puis approbation — est réelle et appliquée. Seul *qui* est autorisé à soumettre reste un emplacement réservé, en attente d'une capacité support locale ou d'une intégration DiddiAdmin.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. Qui supporte le coût d'un repas non livré, et celui d'un plat refusé à la livraison ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-359 L'administrateur arbitre qui supporte le coût d'un repas non livré ou refusé → aucun ticket cité par le planning · phase backlog Later
- **Contexte** · Un administrateur décide qui supporte le coût d'un repas non livré ou refusé — plateforme, restaurant, livreur ou client — et produit un mouvement d'argent réel.
- **Source** · Fiche UC-359 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Décisions techniques

## `PAR-024` — Choisir et commander un repas

**Ce que le planning attend.** Trouve un restaurant, voit plats/prix/dispos, panier, adresse, détail plats vs livraison, paiement. Restaurant accepte ou refuse, cuisine suit la préparation et signale « prêt ». Managers gèrent dispos et accès du personnel ; la cuisine n'accède ni aux retraits ni à la finance.

**Décisions produit applicables.** PROD-023 restaurant · PROD-044 disponibilité Food · PROD-005 moyens de paiement visibles

**Livrable backend `BE020` — Restaurants, carte des plats et commande client.** Priorité P1, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Publier disponibilité, panier, prix plats/livraison, paiement et reprise d’échec sur la même commande.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-25` Terminé(e) · `SCRUM-26` Terminé(e) · `SCRUM-27` Terminé(e) · `SCRUM-28` Terminé(e) · `SCRUM-29` Terminé(e) · `SCRUM-523` Terminé(e) · `SCRUM-528` Terminé(e) · `SCRUM-547` A tester

**Livrable backend `BE021` — Restaurant, cuisine, catalogue et temps de préparation.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Finaliser images publiques catalogue, droits cuisine/manager, filtres commandes, ouvert/fermé et temps de préparation.

Blocage déclaré par le planning : Contrat/intégration à fermer sur staging ; voir tickets liés.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-35` Terminé(e) · `SCRUM-36` Terminé(e) · `SCRUM-37` Terminé(e) · `SCRUM-38` Terminé(e) · `SCRUM-39` Terminé(e) · `SCRUM-468` A tester · `SCRUM-525` À faire · `SCRUM-540` A tester · `SCRUM-541` A tester · `SCRUM-542` À faire · `SCRUM-543` À faire · `SCRUM-544` À faire · `SCRUM-545` À faire · `SCRUM-546` En cours · `SCRUM-551` A tester · `SCRUM-570` À faire

**Confluence.** Lot — DiddiFood / Client (753665) · Lot — DiddiFood / Restaurant (786433) · DiddiFood — Contrat API, proposition (720898)

**État du code au 09/10, relevé dans `diddi-food`.** **Partiel.** Modules `catalog`, `restaurants`, `ordering`, `payments` présents, 57 opérations exposées : `GET /restaurants`, `/menu`, `/dishes`, `PATCH /dishes/{id}/availability`, `POST /orders`, `GET /orders/{id}/payment`. `food_commission_bps = 1500` et `restaurant_min_withdrawal_xof = 5000` (`app/core/config.py:73,80`) correspondent aux 15 % et aux 5 000 F du planning. `delivery_time_minutes_default = 30` tient lieu de délai affiché faute de source par restaurant. `PlaceOrderIn` ne collecte **aucun courriel client**, que le prestataire de paiement exige : la route de préparation du paiement le réclame donc dans son corps de requête.

### 1. Le contrat HTTP avec DiddiPay n'a jamais été exercé de bout en bout : qui provisionne la clé de service et quand la recette est-elle planifiée ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Contexte** · `DIDDIPAY_SERVICE_KEY` n'est pas provisionné. Le paiement en ligne, le webhook et le remboursement sont vérifiés avec une passerelle factice contre la vraie base, jamais contre l'environnement de recette de DiddiPay.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

## `PAR-025` — Livrer avec DiddiSend

**Ce que le planning attend.** La commande crée une livraison Send liée à la même référence. Contraintes véhicule et exclusivité. États remontés à Food. Timeout : pas de doublon de mission. Événement tardif ou répété : cohérence conservée. Restaurant fermé, refus, retard, pas de coursier, échec de remise : décision visible puis support / annulation / remboursement.

**Décisions produit applicables.** PROD-022 livraison Food exclusive · PROD-029 engagement Food et incidents

**Livrable backend `BE022` — Livraison repas exclusive, préparation et heure d’arrivée estimée.** Priorité P0, fenêtre 2026-10-14 au 2026-10-23, état planning « À engager ». Lier commande et livraison unique ; coursier/véhicule compatible ; synchroniser préparation, collecte, remise et estimation.

Tickets Jira, statuts relevés en direct le 09/10 — `SCRUM-44` Terminé(e) · `SCRUM-45` Terminé(e) · `SCRUM-46` Terminé(e) · `SCRUM-47` À faire · `SCRUM-54` À faire · `SCRUM-55` À faire · `SCRUM-404` A tester · `SCRUM-414` A tester · `SCRUM-469` Terminé(e) · `SCRUM-552` A tester

**Confluence.** Lot — DiddiFood / Livreur (819201) · Lot — DiddiFood / Systeme (884737)

**État du code au 09/10, relevé dans `diddi-food`.** **Partiel.** Module `delivery` avec l'adaptateur `diddisend_adapter.py`. La charge envoyée est **complète** au regard du schéma de DiddiSend : `recipient_name`, `recipient_phone`, `sender_phone`, `package`, `delivery_mode = door_to_door`, `payment_method`, `quoted_price`, `origin_module = diddifood`, `order_reference`, `idempotency_key`, `ready_at`, `required_vehicle_type = motorcycle`, `exclusive = True`, `financial_breakdown` (`diddisend_adapter.py:69-104`). Deux limites réelles : le déclenchement à l'acceptation est **best-effort**, enveloppé dans un `try/except` pour qu'une panne Send ne transforme pas une acceptation réussie en 503 — l'échec est journalisé `delivery.request_failed_at_acceptance`, `GET /orders/{id}/delivery` renvoie 404 et la reprise est manuelle par `POST /orders/{id}/delivery/request` ; et `delivery_status_sync_enabled` vaut **`False` par défaut** (`app/core/config.py:68`), donc la remontée des états de DiddiSend vers Food ne tourne pas tant qu'elle n'est pas activée.

### 1. Le moteur de sélection de DiddiSend est conçu pour grouper les livraisons selon la charge restante ; UC-360 exige une mission repas exclusive et non groupable

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-360 Le livreur reçoit une mission repas exclusive, non groupable → `SCRUM-47` À faire · phase backlog Later
- **Contexte** · Un livreur en mission repas ne reçoit aucune autre offre tant qu'il ne l'a pas terminée — la mission repas ne se groupe pas avec d'autres livraisons.
- **Source** · Fiche UC-360 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. La configuration croisée des jetons de service DiddiFood / DiddiSend est-elle alignée en recette ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Contexte** · `DIDDISEND_SERVICE_TOKEN` doit être égal au `DIDDIFOOD_SERVICE_TOKEN` entrant de DiddiSend, qui doit tourner avec `AUTH_ENABLED=true` et des réglages JWKS DiddiFreeID fonctionnels. Sinon `delivery_gateway()` renvoie `None` et l'appel échoue en `DELIVERY_GATEWAY_NOT_CONFIGURED`.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 3. La remontée des états de livraison vers Food est désactivée par défaut : qui l'active, et avec quel flux Redis ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Contexte** · `delivery_status_sync_enabled` vaut `False` (`app/core/config.py:68`) et conditionne le worker, le démarrage de l'application et le rapport de pilotage. Sans activation, le client ne voit jamais la livraison avancer.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

### 4. Le dépôt DiddiFood écrit qu'un appel de création de livraison « répondra probablement 4xx » : ce constat est-il encore vrai ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Contexte** · La charge de `diddisend_adapter.py:69-104` couvre tous les champs exigés par le `DeliveryCreateRequest` de DiddiSend, et ce dernier dispense même les commandes `diddifood` de l'obligation de courriel payeur. `KNOWN_ISSUES.md` n'a pas été relu depuis.
- **Source** · Relevé dans les dépôts le 09/10/2026

**Réponse :**

> 

---

# Valeurs fermées — à reporter en variable d'environnement

Consigne de lancement : toute question de durée, de seuil, de limite ou de valeur numérique est
fermée. Le défaut actuel du code fait foi et part en variable d'environnement — aucune valeur
modifiable à chaud, pour qu'un changement de comportement passe par un redéploiement traçable.

| Question fermée | Parcours | Source |
| --- | --- | --- |
| Quel taux d'indisponibilité et quel taux de retard font descendre un restaurant, et de combien ? | `PAR-025` | Fiche UC-358 · section « Questions ouvertes » · corpus du 14/09/2026 |
| À quelle fréquence un partenaire alimentaire est-il payé, et selon quel délai après la vente ? | `PAR-026` | Fiche UC-243 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Combien de temps avant la fin de la préparation la mission est-elle proposée à un livreur ? | `PAR-025` | Fiche UC-235 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Quelle est la durée de conservation d'une photo de plat après le retrait du plat du menu ? | `PAR-024` | management/specs/etat/a-trancher.md · section « Portée Later » · 14/09/2026 |
| Pendant combien de temps après la livraison un litige alimentaire est-il recevable ? | `PAR-027` | Fiche de lot « DiddiFood / Support » · section « Questions ouvertes » · corpus du 14/09/2026 |
| Combien de temps un restaurant a-t-il pour accepter ou refuser une commande ? | `PAR-024` | Fiche UC-230 · section « Questions ouvertes » · corpus du 14/09/2026 |
| Minimum 5 000 XOF à maintenir ou changer explicitement. | `PAR-026` | Planning de lancement, onglet « Parcours sources » · 09/10/2026 |

# Fermées — légal et conformité

Non bloquant pour le code MVP. Procédure manuelle au support pour le lancement.

| Question | Parcours | Nature | Décideur |
| --- | --- | --- | --- |
| _aucun sujet légal relevé sur ce périmètre_ | — | — | — |

# Hors des trois critères du focus MVP

24 questions conservées pour après le gel.

| Question | Parcours | Axe | Nature | Décideur |
| --- | --- | --- | --- | --- |
| DiddiFiles peut-il servir des fichiers publics de façon durable, ou son modèle d'adresse temporaire impose-t-il un autre dispositif pour les photos de catalogue ? | `PAR-024` | Technique | Fait à établir | Technique |
| Le cloisonnement entre rôle gérant et rôle cuisine sera-t-il porté par DiddiFood, ou l'identité évoluera-t-elle pour porter des rôles par ressource ? | `PAR-024` | Technique | Fait à établir | Technique |
| Le partenaire alimentaire doit-il être un type supplémentaire du partenaire DiddiSend, ou un objet propre à DiddiFood ? | `PAR-026` | Technique | Fait à établir | Technique |
| Une photo de plat est-elle publique, ou passe-t-elle par une adresse temporaire comme les pièces sensibles ? | `PAR-024` | Technique | Décision à prendre | Technique |
| Quelles finalités de fichier DiddiFood déclare-t-il — photo de plat, logo, document de restaurant, autre ? | `PAR-024` | Technique | Décision à prendre | Technique |
| Un remboursement alimentaire est-il imputé au restaurant, au livreur ou à la plateforme, selon le motif ? | `PAR-027` | Produit | Décision à prendre | Administration |
| Le partenaire alimentaire relève-t-il du même objet partenaire que la flotte, ou d'un objet distinct ? | `PAR-026` | Produit | Décision à prendre | Produit |
| Existe-t-il un montant minimum de commande, et des frais de livraison distincts du prix des plats ? | `PAR-024` | Produit | Décision à prendre | Produit |
| Quelles performances de préparation sont mesurées, et lesquelles sont exposées au partenaire ? | `PAR-026` | Produit | Décision à prendre | Produit |
| Le client food est-il le même compte que le passager et l'expéditeur, ou un persona distinct ? | `PAR-024` | Produit | Fait à établir | Produit |
| UC-242 et UC-359 décrivent-ils deux étapes d'un même processus, ou deux processus distincts ? | `PAR-027` | Produit | Fait à établir | Produit |
| Quelles exigences de qualité s'appliquent à une photo de plat — dimensions, cadrage, poids ? | `PAR-024` | Produit | Décision à prendre | Produit |
| Un partenaire alimentaire peut-il exploiter plusieurs points de vente sous un même compte ? | `PAR-026` | Produit | Décision à prendre | Produit |
| Quelles sont les règles de remboursement d'une commande alimentaire, par type de litige ? | `PAR-027` | Produit | Décision à prendre | Administration |
| Exclus du MVP : retrait sur place, remplacement de plat, recharge du wallet restaurant. | `PAR-027` | Produit | Point flou à fermer | Produit |
| Quelles pièces et quelles conditions un restaurant doit-il réunir pour être validé ? | `PAR-027` | Produit | Décision à prendre | Juridique |
| L'absence de contrôle d'authentification relevée sur DiddiFiles est-elle résolue ? | `PAR-024` | Technique | Fait à établir | Technique |
| Un restaurant est-il informé de son rang et de ce qui le fait varier ? | `PAR-025` | Produit | Décision à prendre | Produit |
| Le menu d'un restaurant est-il validé avant publication, et par qui ? | `PAR-024` | Produit | Décision à prendre | Produit |
| Quelle capacité opérationnelle minimale est exigée d'un restaurant ? | `PAR-027` | Produit | Décision à prendre | Administration |
| Combien de restaurants l'équipe peut-elle intégrer par semaine ? | `PAR-027` | Produit | Décision à prendre | Administration |
| Quels indicateurs composent le suivi des commandes food ? | `PAR-027` | Produit | Décision à prendre | Produit |
| Le retrait sur place fait-il partie du périmètre ? | `PAR-024` | Produit | Décision à prendre | Produit |
| Qui valide une photo de plat avant publication ? | `PAR-024` | Produit | Décision à prendre | Produit |

# Sources

| Source | Date | Rôle |
| --- | --- | --- |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx` | 09/10/2026 | source de spécification principale : parcours, livrables, tickets |
| `management/specs` — fiches de use case et de lot, registres `etat/` | 14/09/2026 | complément : les questions ouvertes |
| `diddi-scope-document` — registre `PROD-xxx` | 09/10/2026 | cible produit |
| dépôt `diddi-food` | branche courante | état du code, relu aujourd'hui |
| Jira `diddifree` | 09/10/2026, lecture seule | statuts relevés en direct |
| Confluence espace `DIDDIFREE` | 09/10/2026, lecture seule | pages de lot |

Les parcours Common et DiddiPay, partagés entre les trois services, sont traités dans le
relevé [`DECISIONS_A_PRENDRE_MVP.md`](archive/2026-10-09-pre-gel/DECISIONS_A_PRENDRE_MVP.md),
archivé depuis la réorganisation du 09/10 — le MVP DiddiGo actif est porté par
[`DIDDIGO-MVP-FIGE.md`](DIDDIGO-MVP-FIGE.md).

Ce document est un **recueil de questions**, pas un registre de décisions : il n'arbitre rien
et ne définit aucun périmètre. Les réponses, une fois prises, ont leur place dans la référence
produit du service concerné.
