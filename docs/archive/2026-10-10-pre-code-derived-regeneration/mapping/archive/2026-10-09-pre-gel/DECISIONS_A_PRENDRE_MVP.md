# Décisions à prendre avant le gel du code du 18 novembre 2026

Périmètre Common et DiddiGo. Relevé du 9 octobre 2026, branche `feat/pilotage-finance-summary-v1`.

**60 questions** restent à trancher. Elles sont les seules à répondre aux trois critères du
focus MVP :

1. une contradiction bloquante entre le code existant et le parcours utilisateur ;
2. un comportement métier qui bloque le déroulement d'une commande ou d'une course ;
3. un cas limite qui empêche d'aller au bout d'un parcours principal.

Sur les 298 points relevés au total, le reste est fermé : **56** questions de valeur dont le défaut du code fait foi et part en configuration, **14** sujets légaux traités par procédure manuelle au support, **151** hors des trois critères, et **17** déjà tranchées avant ce relevé. Les quatre sections correspondantes sont en fin de document.

Un parcours peut apparaître sous plusieurs axes : son préambule — attendu du planning, décisions
produit, tickets Jira du livrable, page Confluence — est répété pour que chaque section se lise seule.

## Répartition

| Axe | Questions |
| --- | --- |
| Décisions produit | 24 |
| Décisions techniques | 30 |
| Décisions non fonctionnelles | 6 |
| **Total** | **60** |

| Parcours | Questions |
| --- | --- |
| `PAR-016` Commander et effectuer une course | 23 |
| `PAR-017` Gérer attente, escales et annulation | 10 |
| `PAR-008` Garder un historique exploitable | 6 |
| `PAR-007` Recevoir une offre et suivre une mission | 5 |
| `PAR-019` Limites du lancement | 5 |
| `PAR-002` Devenir chauffeur, coursier ou restaurant | 4 |
| `PAR-004` Gérer ses données | 2 |
| `PAR-001` Créer son compte et retrouver sa session | 2 |
| `PAR-018` Payer et retrouver ses gains | 2 |
| `PAR-005` Trouver une destination par texte ou par voix | 1 |

---

# Décisions produit

## `PAR-002` — Devenir chauffeur, coursier ou restaurant

**Ce que le planning attend.** Création du profil métier, envoi des justificatifs, dossier « en attente ». Contrôle du véhicule (chauffeur/coursier). Refus avec motif, correction, nouvelle soumission. Impossible de travailler ou retirer des gains avant validation. Suspension visible, motivée, tracée, avec contestation possible.

**Décisions produit applicables.** PROD-002 — l'activation n'est pas acquise par la seule création du compte Identity

**Tickets Jira du livrable backend** — `SCRUM-430` A tester (BE002) · `SCRUM-431` Done (BE002) · `SCRUM-432` A tester (BE002) · `SCRUM-444` In Progress (BE002) · `SCRUM-445` Done (BE002) · `SCRUM-496` Done (BE002) · `SCRUM-510` A tester (BE002) · `SCRUM-513` A tester (BE002) · `SCRUM-466` A tester (BE003) · `SCRUM-470` A tester (BE003) · `SCRUM-519` A tester (BE003) · `SCRUM-520` A tester (BE003) · `SCRUM-558` Attente de admin (BE003) · `SCRUM-560` To Do (BE003)

**Confluence.** Lot — DiddiFree Pro (1179649) · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprint 1

### 1. Le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · lot DiddiGo / Chauffeur → epic `SCRUM-65` —
- **Intitulé** · DiddiGo / Chauffeur
- **Contexte** · Ce lot couvre la vie du chauffeur dans l'application pro : se déclarer, faire valider son identité et son véhicule, se mettre en ligne, recevoir des offres de course, en accepter ou en refuser,…
- **Source** · Fiche de lot « DiddiGo / Chauffeur » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le moteur d'attribution offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · lot DiddiGo / Chauffeur → epic `SCRUM-65` —
- **Intitulé** · DiddiGo / Chauffeur
- **Contexte** · Ce lot couvre la vie du chauffeur dans l'application pro : se déclarer, faire valider son identité et son véhicule, se mettre en ligne, recevoir des offres de course, en accepter ou en refuser,…
- **Source** · Fiche de lot « DiddiGo / Chauffeur » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. UC-270 demande sept photos dont un second angle d'habitacle et le coffre ; le code ne prévoit que six emplacements

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-270 → `SCRUM-204` Terminé(e)
- **Intitulé** · Le chauffeur fournit les photos obligatoires du véhicule : quatre côtés, habitacle avant et arrière, coffre
- **Contexte** · Le chauffeur photographie son véhicule sous tous les angles utiles à sa vérification : les quatre côtés, l'habitacle vu de l'avant et vu de l'arrière, et le coffre.
- **État du code au 09/10** · **Présent** — Les cinq photos existent sur le véhicule : `vehicle_front_photo_file_id`, `_back_`, `_left_`, `_right_` et `vehicle_interior_photo_file_id` (`ride/domain/entities.py:317-322`), plus `photo_url` dans la charge utile.
- **Source** · Fiche UC-270 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-004` — Gérer ses données

**Ce que le planning attend.** Contacter le support, demander la suppression du compte. Si mission active, dette ou solde : parcours de résolution explicite.

**Limite que le planning déclare.** Délais et exceptions de suppression à valider ; distinguer fermeture / effacement / conservation des écritures financières.

**Décisions produit applicables.** PROD-010 suppression de compte · PROD-038 conservation · PROD-028 conversations

**Tickets Jira du livrable backend** — `SCRUM-120` To Do (BE005)

**Confluence.** Lot — Compte, donnees personnelles et conformite (1048577)

### 1. La décision du 14/09 dit que les traces envoyées à DiddiMap sont anonymisées ; le code transmet la trace entière

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Juridique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Compte, donnees personnelles et conformite → aucun ticket rattaché
- **Intitulé** · Compte, donnees personnelles et conformite
- **Contexte** · Ce lot répond à une question simple et à une question difficile. La simple : que peut faire une personne de ses données ?
- **Source** · Fiche de lot « Compte, donnees personnelles et conformite » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Un litige ouvert de faible gravité (ex. objet oublié non réclamé) bloque-t-il la suppression au même titre qu'un litige financier ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-334 → `SCRUM-120` À faire
- **Intitulé** · Le système refuse une demande de suppression tant qu'une mission, un solde ou un litige est ouvert
- **Contexte** · Supprimer un compte au milieu d'une course, avec un solde dû ou un litige en cours, laisserait des obligations non résolues des deux côtés.
- **État du code au 09/10** · **Partiel** — Le solde et la dette du chauffeur sont lisibles (`/v1/drivers/me/wallet`), et les courses actives sont identifiables par leur état. Aucune demande de suppression à refuser, faute de route de suppression.
- **Source** · Fiche UC-334 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-007` — Recevoir une offre et suivre une mission

**Ce que le planning attend.** Offre claire avec infos pour accepter/refuser. Notifications testées (app ouverte, arrière-plan, téléphone verrouillé). Client informé des changements de statut sans recharger. Contact par appel entre parties. Une offre déjà attribuée ne peut plus être acceptée.

**Limite que le planning déclare.** Numéro masqué ou appel direct : à choisir.

**Décisions produit applicables.** PROD-016 appel retenu ; messagerie et appels Internet en V1

**Tickets Jira du livrable backend** — `SCRUM-304` To Do (BE007) · `SCRUM-305` Done (BE007) · `SCRUM-306` To Do (BE007) · `SCRUM-533` Done (BE007) · `SCRUM-534` To Do (BE007) · `SCRUM-552` A tester (BE007)

**Confluence.** Lot — Notifications et canaux (1474561) · Lot — Communication en mission (753685)

### 1. La décision du 01/09 prévoit de s'appeler sans échanger de numéro ; le numéro du chauffeur est transmis au passager

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Communication en mission → aucun ticket rattaché
- **Intitulé** · Communication en mission
- **Contexte** · Ce lot permet aux deux parties d'une mission de se parler sans échanger leurs numéros de téléphone.
- **Source** · Fiche de lot « Communication en mission » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Que se passe-t-il si une partie ne répond pas ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · Communication en mission → aucun ticket rattaché
- **Intitulé** · Communication en mission
- **Contexte** · Ce lot permet aux deux parties d'une mission de se parler sans échanger leurs numéros de téléphone.
- **Source** · Fiche de lot « Communication en mission » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-008` — Garder un historique exploitable

**Ce que le planning attend.** Chaque mission/opération financière laisse une trace (création, attribution, réalisation, annulation, paiement, incident, correction), rejouable sans doublon. Pas de points ni de DiddiScore au MVP.

**Décisions produit applicables.** PROD-008 historique vérifié · PROD-011 reprise · PROD-039 preuves de qualité

**Tickets Jira du livrable backend** — `SCRUM-371` To Do (BE008) · `SCRUM-438` Done (BE008) · `SCRUM-480` A tester (BE008) · `SCRUM-101` In Review (BE026) · `SCRUM-454` In Review (BE026) · `SCRUM-483` Done (BE026) · `SCRUM-487` A tester (BE026) · `SCRUM-492` To Do (BE026)

**Confluence.** Lot — Historique, recus et justificatifs (1409025) · Lot — Reseau degrade et continuite (1572865)

### 1. UC-247 demande de masquer l'identité du chauffeur après la course ; elle reste accessible sans limite

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Historique, recus et justificatifs → aucun ticket rattaché
- **Intitulé** · Historique, recus et justificatifs
- **Contexte** · Ce lot répond à une question qu'on se pose toujours après coup : combien ai-je payé, et pourquoi. Le passager consulte l'historique de ses courses et le détail de chacune.
- **Source** · Fiche de lot « Historique, recus et justificatifs » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-016` — Commander et effectuer une course

**Ce que le planning attend.** Départ + destination (saisie ou voix), estimation, confirmation. Recherche d'un chauffeur éligible, offre, acceptation, suivi de l'approche, arrivée, début, fin. Même mission des deux côtés. Offre expirée, refus, aucun chauffeur, perte de connexion : issue explicite et reprise cohérente.

**Décisions produit applicables.** PROD-015 confort et devis · PROD-027 recherche en trois phases · PROD-013 début de course et secours GPS · PROD-011 reprise

**Tickets Jira du livrable backend** — `SCRUM-188` Done (BE014) · `SCRUM-190` Done (BE014) · `SCRUM-191` Done (BE014) · `SCRUM-193` Done (BE014) · `SCRUM-194` Done (BE014) · `SCRUM-437` Done (BE014) · `SCRUM-438` Done (BE014) · `SCRUM-441` To Do (BE014) · `SCRUM-442` Done (BE014) · `SCRUM-524` A tester (BE014) · `SCRUM-536` To Do (BE014) · `SCRUM-567` To Do (BE014)

**Confluence.** Lot — DiddiGo / Passager (917523), epic SCRUM-64, Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprints 1 et 2 · Lot — Matching et Priorite (1441793)

### 1. Le lien de partage de course expire 24 h après sa création dans le code ; la décision du 31/08 dit 20 minutes après la fin de la course

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-165 → `SCRUM-379` À faire
- **Intitulé** · Le lien expire automatiquement : 20 min après la course, à la fin de la livraison
- **Contexte** · Un lien de suivi ne doit pas rester valide indéfiniment : une fois la mission terminée, l'accès à la position ne se justifie plus, et doit s'arrêter automatiquement.
- **État du code au 09/10** · **À vérifier** — Le lien existe ; l'expiration automatique après la course reste à établir par lecture de `create_share_link` et `get_shared_ride`.
- **Source** · Fiche UC-165 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le mode « wave » laisse attendre un paiement par l'application Wave ; il ouvre un formulaire Paystack

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-254 → `SCRUM-222` Terminé(e)
- **Intitulé** · Le passager choisit son mode de paiement avant de commander
- **Contexte** · Le passager décide comment il paiera — en espèces ou par un moyen numérique — avant d'engager la course, et non au moment de descendre du véhicule.
- **État du code au 09/10** · **Présent** — Moyen de paiement porté par la demande de course et conservé sur la course ; `422 INVALID_PAYMENT_METHOD` sur valeur inconnue.
- **Source** · Fiche UC-254 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Le moteur DiddiGo envoie l'offre à un seul chauffeur à la fois, la décision du 14/09 impose des vagues de 5

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · lot Matching et Priorite → epic `SCRUM-66` —
- **Intitulé** · Matching et Priorite
- **Contexte** · Ce lot décide qui reçoit quelle mission, et dans quel ordre.
- **Source** · Fiche de lot « Matching et Priorite » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Le contrôle croisé DiddiGo/DiddiSend doit-il être activé ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-107 → `SCRUM-287` A tester
- **Intitulé** · Le système évite qu'un pro reçoive deux missions incompatibles
- **Contexte** · Un pro qui a accepté une course ou une livraison ne doit pas se retrouver sollicité pour une seconde mission incompatible avant d'avoir terminé la première — cela créerait une double affectation…
- **État du code au 09/10** · **Présent** — Un chauffeur déjà sur une course est exclu des offres — invariant couvert par `tests/test_matching.py`.
- **Source** · Fiche UC-107 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 5. Que fait le système quand un pro accepte alors que la vague suivante est déjà partie ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-278 → `SCRUM-293` A tester
- **Intitulé** · Le système envoie l'offre à une vague de plusieurs chauffeurs simultanément et passe à la vague suivante
- **Contexte** · Proposer une course à plusieurs chauffeurs en même temps réduit le temps d'attente du passager : le premier à répondre l'obtient, au lieu d'attendre le refus ou l'expiration d'un seul chauffeur à la…
- **État du code au 09/10** · **Présent** — Modèle de vagues d'offres dans `matching_service.py` : `try_match` ouvre une vague, `advance_expired_offer` passe à la suivante à expiration (ligne 320).
- **Source** · Fiche UC-278 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 6. Que se passe-t-il quand un passager annonce un paiement en espèces et n'a pas la somme ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Administration
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-254 → `SCRUM-222` Terminé(e)
- **Intitulé** · Le passager choisit son mode de paiement avant de commander
- **Contexte** · Le passager décide comment il paiera — en espèces ou par un moyen numérique — avant d'engager la course, et non au moment de descendre du véhicule.
- **État du code au 09/10** · **Présent** — Moyen de paiement porté par la demande de course et conservé sur la course ; `422 INVALID_PAYMENT_METHOD` sur valeur inconnue.
- **Source** · Fiche UC-254 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 7. Quel est le mode de paiement par défaut d'une course ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-254 → `SCRUM-222` Terminé(e)
- **Intitulé** · Le passager choisit son mode de paiement avant de commander
- **Contexte** · Le passager décide comment il paiera — en espèces ou par un moyen numérique — avant d'engager la course, et non au moment de descendre du véhicule.
- **État du code au 09/10** · **Présent** — Moyen de paiement porté par la demande de course et conservé sur la course ; `422 INVALID_PAYMENT_METHOD` sur valeur inconnue.
- **Source** · Fiche UC-254 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 8. Quel message est affiché à un chauffeur non retenu d'une vague, pour éviter qu'il ne pense avoir refusé ou raté quelque chose ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-286 → `SCRUM-301` A tester
- **Intitulé** · Le système n'applique aucune pénalité aux chauffeurs non retenus d'une vague
- **Contexte** · Un chauffeur sollicité dans une vague mais non retenu n'a rien fait de mal : un autre a simplement été plus rapide ou mieux classé.
- **État du code au 09/10** · **Présent** — Les points de priorité ne sont versés que sur l'issue de la course (`_record_priority_outcome`, `services.py:546`) : `+1` course terminée, `-3` annulation chauffeur. Aucune pénalité n'est appliquée à un chauffeur non retenu d'une vague.
- **Source** · Fiche UC-286 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 9. Une relance crée-t-elle une nouvelle course, ou remet-elle la course existante en recherche ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-253 → `SCRUM-221` À faire
- **Intitulé** · Le passager est informé qu'aucun chauffeur n'est disponible et peut relancer ou demander à être notifié
- **Contexte** · La recherche a échoué. Le passager doit l'apprendre clairement, et pouvoir faire quelque chose : relancer, attendre qu'on le prévienne, ou renoncer.
- **État du code au 09/10** · **Partiel** — État terminal `no_driver_found` et événement WebSocket `ride.no_driver_found` (`websocket.py:156`), produits à l'épuisement du budget de recherche (`matching_service.py` `_give_up`). Aucune relance côté serveur : le passager crée une nouvelle course. Aucune mise en attente de notification.
- **Source** · Fiche UC-253 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 10. Un même pro peut-il être à la fois chauffeur DiddiGo et coursier DiddiSend, et si oui, ce cas est-il réellement rencontré en pratique ?

- **Nature** · Fait à établir
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-107 → `SCRUM-287` A tester
- **Intitulé** · Le système évite qu'un pro reçoive deux missions incompatibles
- **Contexte** · Un pro qui a accepté une course ou une livraison ne doit pas se retrouver sollicité pour une seconde mission incompatible avant d'avoir terminé la première — cela créerait une double affectation…
- **État du code au 09/10** · **Présent** — Un chauffeur déjà sur une course est exclu des offres — invariant couvert par `tests/test_matching.py`.
- **Source** · Fiche UC-107 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-017` — Gérer attente, escales et annulation

**Ce que le planning attend.** Attente facturée et escales : début/fin visibles, supplément, nouveau montant. Pas de double comptage après reconnexion. Annulation : qui, à quelle étape, quelles conséquences. Incident/urgence signalable vers le circuit humain.

**Limite que le planning déclare.** Temps gratuit, tarifs, accord du client à formaliser.

**Décisions produit applicables.** PROD-012 arrivée et attente · PROD-026 escale · PROD-014 annulation et fin anticipée · PROD-036 incident

**Tickets Jira du livrable backend** — `SCRUM-6` Done (BE015) · `SCRUM-7` To Do (BE015) · `SCRUM-524` A tester (BE015) · `SCRUM-537` V2 (BE015)

**Confluence.** Lot — DiddiGo / Passager (917523), Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), Sprint 2 · Lot — Urgence et securite des personnes (393217)

### 1. Aucun parcours complet de réaffectation après accident/panne avec garde du colis, transfert de responsabilité et répartition financière n'a été établi par les recherches ciblées. Ce n'est pas une preuve d'absence dans tout le système.

- **Nature** · Constat à instruire
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · Suspension et accident → aucun ticket rattaché
- **Intitulé** · Suspension et accident
- **Contexte** · Section « Suspension et accident ». Le document précise que ces éléments « restent des propositions » et ne sont pas des règles acquises.
- **Source** · Points à arbitrer · 09/10/2026 · Suspension et accident

**Réponse :**

> 

### 2. Qu'est-ce qui définit le silence d'un chauffeur — absence de position, absence de progression, ou les deux ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-257 → `SCRUM-225` À faire
- **Intitulé** · Le passager annule sans frais quand le chauffeur est silencieux au-delà du délai défini avant la prise en charge
- **Contexte** · Un chauffeur a accepté la course mais ne donne plus signe de vie : il n'avance pas, sa position ne remonte plus. Le passager doit pouvoir partir sans payer, et sans avoir à se justifier.
- **État du code au 09/10** · **Partiel** — L'annulation est gratuite dans tous les cas (`services.py:519-553`), donc l'effet attendu est atteint. Aucun délai de silence du chauffeur n'est mesuré côté serveur.
- **Source** · Fiche UC-257 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Une annulation pour silence du chauffeur a-t-elle un effet sur sa réputation, même sans pénalité ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-257 → `SCRUM-225` À faire
- **Intitulé** · Le passager annule sans frais quand le chauffeur est silencieux au-delà du délai défini avant la prise en charge
- **Contexte** · Un chauffeur a accepté la course mais ne donne plus signe de vie : il n'avance pas, sa position ne remonte plus. Le passager doit pouvoir partir sans payer, et sans avoir à se justifier.
- **État du code au 09/10** · **Partiel** — L'annulation est gratuite dans tous les cas (`services.py:519-553`), donc l'effet attendu est atteint. Aucun délai de silence du chauffeur n'est mesuré côté serveur.
- **Source** · Fiche UC-257 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-019` — Limites du lancement

**Ce que le planning attend.** Chauffeurs indépendants uniquement. Pas de flottes ni de tarifs par zone (un champ « zone » peut être préparé). Stats de base et contrôles anti-abus inclus.

**Décisions produit applicables.** PROD-001 partenaires et flottes en V1 · PROD-015 zones en V1

**Tickets Jira du livrable backend** — `SCRUM-188` Done (BE014) · `SCRUM-190` Done (BE014) · `SCRUM-191` Done (BE014) · `SCRUM-193` Done (BE014) · `SCRUM-194` Done (BE014) · `SCRUM-437` Done (BE014) · `SCRUM-438` Done (BE014) · `SCRUM-441` To Do (BE014) · `SCRUM-442` Done (BE014) · `SCRUM-524` A tester (BE014) · `SCRUM-536` To Do (BE014) · `SCRUM-567` To Do (BE014)

**Confluence.** Lot — Partenaires et Flottes (1376273) · Lot — Zones, couverture et majoration (1146913)

### 1. La commission est calculée sur le prix total majoration comprise ; UC-298 demande le prix de base

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Zones, couverture et majoration → aucun ticket rattaché
- **Intitulé** · Zones, couverture et majoration
- **Contexte** · Ce lot répond à deux questions géographiques. Où travaillons-nous, et combien coûte une course selon l'endroit et le moment.
- **Source** · Fiche de lot « Zones, couverture et majoration » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Les use cases décrivent des actions du partenaire ; toutes les routes correspondantes sont réservées à l'administrateur

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-120 → `SCRUM-311` À faire
- **Intitulé** · Le partenaire crée ou fait créer son organisation
- **Contexte** · Une personne qui possède des véhicules ou emploie des pros doit pouvoir démarrer son organisation partenaire sur la plateforme, comme première étape avant de rattacher des chauffeurs, des coursiers…
- **État du code au 09/10** · **Présent** — `POST /v1/admin/partners` et `POST /internal/v1/admin/partners` ; `Partner` avec `PartnerStatus` et `PartnerType` (`partner/domain/entities.py`).
- **Source** · Fiche UC-120 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. UC-293 et les use cases UC-265 et UC-266 du lot chauffeur décrivent des fonctionnalités qui se recouvrent

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Zones, couverture et majoration → aucun ticket rattaché
- **Intitulé** · Zones, couverture et majoration
- **Contexte** · Ce lot répond à deux questions géographiques. Où travaillons-nous, et combien coûte une course selon l'endroit et le moment.
- **Source** · Fiche de lot « Zones, couverture et majoration » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Décisions techniques

## `PAR-001` — Créer son compte et retrouver sa session

**Ce que le planning attend.** Saisie du numéro → code OTP par SMS → accès au profil. Même identité pour Go, Send et Food. Session conservée ou renouvelée ; sinon reconnexion sans perdre l'historique. Messages clairs : code faux/expiré, délai avant renvoi, numéro invalide, panne SMS (pas présentée comme faute de l'utilisateur).

**Décisions produit applicables.** PROD-007 connexion par téléphone · PROD-002 Common · PROD-046 identité et avantages

**Tickets Jira du livrable backend** — `SCRUM-169` Done (BE001) · `SCRUM-170` Done (BE001) · `SCRUM-565` To Do (BE001) · `SCRUM-566` To Do (BE001) · `SCRUM-567` To Do (BE001)

**Confluence.** Lot — DiddiFreeID / Identite (950291)

### 1. DiddiFreeID écrit par défaut les codes d'authentification en clair dans les journaux

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-002 → `SCRUM-169` Terminé(e)
- **Intitulé** · L'utilisateur demande un OTP pour se connecter
- **Contexte** · Sans mot de passe, l'authentification repose entièrement sur un code à usage unique. L'utilisateur doit pouvoir en demander un, envoyé sur son téléphone ou son courriel.
- **État du code au 09/10** · **Hors diddi-go** — Demande d'OTP : module DiddiFreeID, code non lu. Côté Go, `POST /v1/auth/otp/request` existe, avec un `TODO` : aucun fournisseur SMS branché.
- **Source** · Fiche UC-002 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Une déconnexion demandée hors ligne invalide-t-elle réellement le jeton côté serveur au retour du réseau, ou seulement localement ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-006 → `SCRUM-173` Terminé(e)
- **Intitulé** · L'utilisateur se déconnecte de son compte
- **Contexte** · Un utilisateur doit pouvoir mettre fin à sa session à tout moment, par exemple avant de prêter son téléphone à quelqu'un d'autre.
- **État du code au 09/10** · **Hors diddi-go** — Déconnexion : module DiddiFreeID, code non lu.
- **Source** · Fiche UC-006 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-002` — Devenir chauffeur, coursier ou restaurant

**Ce que le planning attend.** Création du profil métier, envoi des justificatifs, dossier « en attente ». Contrôle du véhicule (chauffeur/coursier). Refus avec motif, correction, nouvelle soumission. Impossible de travailler ou retirer des gains avant validation. Suspension visible, motivée, tracée, avec contestation possible.

**Décisions produit applicables.** PROD-002 — l'activation n'est pas acquise par la seule création du compte Identity

**Tickets Jira du livrable backend** — `SCRUM-430` A tester (BE002) · `SCRUM-431` Done (BE002) · `SCRUM-432` A tester (BE002) · `SCRUM-444` In Progress (BE002) · `SCRUM-445` Done (BE002) · `SCRUM-496` Done (BE002) · `SCRUM-510` A tester (BE002) · `SCRUM-513` A tester (BE002) · `SCRUM-466` A tester (BE003) · `SCRUM-470` A tester (BE003) · `SCRUM-519` A tester (BE003) · `SCRUM-520` A tester (BE003) · `SCRUM-558` Attente de admin (BE003) · `SCRUM-560` To Do (BE003)

**Confluence.** Lot — DiddiFree Pro (1179649) · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprint 1

### 1. La fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-021 → `SCRUM-186` Terminé(e)
- **Intitulé** · Le chauffeur soumet les documents du véhicule
- **Contexte** · Le chauffeur dépose les pièces administratives et les photos de son véhicule, nécessaires à sa vérification.
- **État du code au 09/10** · **Présent** — `POST /v1/drivers/vehicles/{id}/kyv/resubmit` (`driver_service.py:376`).
- **Source** · Fiche UC-021 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-005` — Trouver une destination par texte ou par voix

**Ce que le planning attend.** Champ de recherche + micro : la voix est transcrite dans le champ, corrigeable. Le client choisit le lieu, vérifie la carte, confirme le devis. La voix ne choisit pas seule entre deux lieux homonymes et ne déclenche aucune commande. Si micro refusé / réseau faible : clavier toujours dispo.

**Limite que le planning déclare.** Langues du lancement et lieux d'Abidjan pour la recette à fixer.

**Décisions produit applicables.** PROD-018 dictée

**Confluence.** Lot — DiddiMap / Cartographie (1277953)

### 1. DiddiMap valide un profil de véhicule puis construit toujours l'appel avec le profil configuré globalement

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · DiddiMap / Cartographie → aucun ticket rattaché
- **Intitulé** · DiddiMap / Cartographie
- **Contexte** · DiddiMap fournit trois services aux autres modules : trouver un lieu, calculer un itinéraire avec sa distance et sa durée, et recevoir les traces GPS des missions.
- **Source** · Fiche de lot « DiddiMap / Cartographie » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-007` — Recevoir une offre et suivre une mission

**Ce que le planning attend.** Offre claire avec infos pour accepter/refuser. Notifications testées (app ouverte, arrière-plan, téléphone verrouillé). Client informé des changements de statut sans recharger. Contact par appel entre parties. Une offre déjà attribuée ne peut plus être acceptée.

**Limite que le planning déclare.** Numéro masqué ou appel direct : à choisir.

**Décisions produit applicables.** PROD-016 appel retenu ; messagerie et appels Internet en V1

**Tickets Jira du livrable backend** — `SCRUM-304` To Do (BE007) · `SCRUM-305` Done (BE007) · `SCRUM-306` To Do (BE007) · `SCRUM-533` Done (BE007) · `SCRUM-534` To Do (BE007) · `SCRUM-552` A tester (BE007)

**Confluence.** Lot — Notifications et canaux (1474561) · Lot — Communication en mission (753685)

### 1. Un chauffeur peut-il diffuser une position sur une course à laquelle il n'est pas affecté ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-012 → `SCRUM-215` À faire
- **Intitulé** · Le passager voit la position du chauffeur
- **Contexte** · Le passager veut voir où est le chauffeur sur une carte, pour savoir s'il approche et dans combien de temps il sera là.
- **État du code au 09/10** · **Partiel** — Événement WebSocket `ride.driver_location` (`websocket.py:146`) et poussée `driver.location_push` (ligne 315). La charge utile ne porte pas d'horodatage de fraîcheur ; `last_location_at` n'existe que sur le lien de suivi partagé (`services.py:635`).
- **Source** · Fiche UC-012 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-008` — Garder un historique exploitable

**Ce que le planning attend.** Chaque mission/opération financière laisse une trace (création, attribution, réalisation, annulation, paiement, incident, correction), rejouable sans doublon. Pas de points ni de DiddiScore au MVP.

**Décisions produit applicables.** PROD-008 historique vérifié · PROD-011 reprise · PROD-039 preuves de qualité

**Tickets Jira du livrable backend** — `SCRUM-371` To Do (BE008) · `SCRUM-438` Done (BE008) · `SCRUM-480` A tester (BE008) · `SCRUM-101` In Review (BE026) · `SCRUM-454` In Review (BE026) · `SCRUM-483` Done (BE026) · `SCRUM-487` A tester (BE026) · `SCRUM-492` To Do (BE026)

**Confluence.** Lot — Historique, recus et justificatifs (1409025) · Lot — Reseau degrade et continuite (1572865)

### 1. Ce use case est classé partiel ; la liste paginée et filtrée existe

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-245 → `SCRUM-275` Terminé(e)
- **Intitulé** · Le passager consulte l'historique de ses courses
- **Contexte** · Un passager doit retrouver ses courses passées, filtrables, en moins de trois interactions.
- **État du code au 09/10** · **Présent** — `GET /v1/rides` liste l'historique du passager (`services.py:239`).
- **Source** · Fiche UC-245 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Ce use case est classé partiel ; le détail complet existe et est exposé

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-246 → `SCRUM-276` À faire
- **Intitulé** · Le passager consulte le détail d'une course passée : prix, durée réelle, distance, mode de paiement
- **Contexte** · Le détail d'une course passée doit expliquer le montant payé, ligne par ligne, sans que le passager ait à demander.
- **État du code au 09/10** · **Présent** — `GET /v1/rides/{id}` renvoie prix, durée, distance et moyen de paiement, sous condition de visibilité selon le rôle (`_ride_detail_payload`, `_money_visible`).
- **Source** · Fiche UC-246 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Ce use case exige de borner l'horloge du téléphone ; les horodatages envoyés sont acceptés sans contrôle

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-321 → `SCRUM-372` À faire
- **Intitulé** · Le système borne l'horloge du téléphone pour les actions horodatées hors ligne
- **Contexte** · Une action déclarée hors ligne porte l'horodatage du téléphone, pas celui du serveur.
- **État du code au 09/10** · **Partiel** — Le serveur accepte le `recorded_at` fourni par le client et le remplace par l'heure serveur s'il est absent (`services.py:591`). Aucune borne n'est appliquée à une horloge client fausse.
- **Source** · Fiche UC-321 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. UC-245 et UC-246 sont classés partiels ; la liste paginée filtrée et le détail complet existent

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Historique, recus et justificatifs → aucun ticket rattaché
- **Intitulé** · Historique, recus et justificatifs
- **Contexte** · Ce lot répond à une question qu'on se pose toujours après coup : combien ai-je payé, et pourquoi. Le passager consulte l'historique de ses courses et le détail de chacune.
- **Source** · Fiche de lot « Historique, recus et justificatifs » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 5. UC-321 exige de borner l'horloge du téléphone ; les horodatages envoyés sont acceptés sans contrôle

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Reseau degrade et continuite → aucun ticket rattaché
- **Intitulé** · Reseau degrade et continuite
- **Contexte** · Ce lot traite le cas normal à Abidjan : le réseau tombe. Il ne décrit pas une panne, il décrit le régime ordinaire de fonctionnement.
- **Source** · Fiche de lot « Reseau degrade et continuite » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-016` — Commander et effectuer une course

**Ce que le planning attend.** Départ + destination (saisie ou voix), estimation, confirmation. Recherche d'un chauffeur éligible, offre, acceptation, suivi de l'approche, arrivée, début, fin. Même mission des deux côtés. Offre expirée, refus, aucun chauffeur, perte de connexion : issue explicite et reprise cohérente.

**Décisions produit applicables.** PROD-015 confort et devis · PROD-027 recherche en trois phases · PROD-013 début de course et secours GPS · PROD-011 reprise

**Tickets Jira du livrable backend** — `SCRUM-188` Done (BE014) · `SCRUM-190` Done (BE014) · `SCRUM-191` Done (BE014) · `SCRUM-193` Done (BE014) · `SCRUM-194` Done (BE014) · `SCRUM-437` Done (BE014) · `SCRUM-438` Done (BE014) · `SCRUM-441` To Do (BE014) · `SCRUM-442` Done (BE014) · `SCRUM-524` A tester (BE014) · `SCRUM-536` To Do (BE014) · `SCRUM-567` To Do (BE014)

**Confluence.** Lot — DiddiGo / Passager (917523), epic SCRUM-64, Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprints 1 et 2 · Lot — Matching et Priorite (1441793)

### 1. L'instant de mesure de la position est exposé au tiers qui ouvre un lien de partage, mais pas au passager dans son application

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-255 → `SCRUM-223` À faire
- **Intitulé** · Le passager voit l'heure de la dernière position connue du chauffeur dans l'application
- **Contexte** · Le passager doit pouvoir juger si ce qu'il voit sur la carte est vrai maintenant. Un marqueur immobile peut vouloir dire « le chauffeur est arrêté » ou « je ne reçois plus rien depuis trois minutes ».
- **État du code au 09/10** · **Partiel** — `last_location_at` est exposé sur le lien de suivi partagé (`services.py:635`). La réponse de `GET /v1/rides/{id}` ne porte pas cet horodatage.
- **Source** · Fiche UC-255 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le serveur expose-t-il l'instant de la dernière position reçue du chauffeur, ou diffuse-t-il un événement de silence ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-256 → `SCRUM-224` À faire
- **Intitulé** · Le passager distingue sa propre perte de connexion de celle du chauffeur
- **Contexte** · Quand l'information cesse d'arriver, le passager doit savoir de quel côté vient le problème.
- **État du code au 09/10** · **Absent du code** — Aucun signal distinguant la perte de connexion du passager de celle du chauffeur. Les positions portent un TTL Redis, exploité pour l'attente, pas diffusé comme état de santé.
- **Source** · Fiche UC-256 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. Si DiddiMap ne répond pas pour un candidat, ce candidat est-il classé par distance à vol d'oiseau en repli, ou exclu de ce tour ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-283 → `SCRUM-298` Revue en cours
- **Intitulé** · Le système classe les chauffeurs par temps d'arrivée estimé pondéré par les points de priorité
- **Contexte** · Le classement des candidats ne doit pas être une simple distance à vol d'oiseau : le temps d'arrivée réel importe davantage, et les points de priorité d'un chauffeur fiable doivent pouvoir le faire…
- **État du code au 09/10** · **Présent** — Reclassement par temps d'arrivée estimé combiné aux points de priorité : `matching_eta_ranking_enabled` et `_priority_bonuses` (`matching_service.py`).
- **Source** · Fiche UC-283 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Le lien de suivi expire-t-il automatiquement après la course ? La durée et le déclencheur restent à lire dans `create_share_link` et `get_shared_ride`.

- **Nature** · Fait de code à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-165 → `SCRUM-379` À faire · UC-287 → `SCRUM-302` Revue en cours
- **Intitulé** · UC-165 / UC-287
- **Contexte** · Relevé en lisant le code aujourd'hui ; aucun test n'a été exécuté en staging.
- **État du code au 09/10** · **À vérifier** — Le lien existe ; l'expiration automatique après la course reste à établir par lecture de `create_share_link` et `get_shared_ride`.
- **Source** · Constat de code · branche courante au 09/10/2026 · UC-165

**Réponse :**

> 

### 5. Une recherche est-elle lancée lorsque le rayon initial ne contient aucun chauffeur libre, ou l'absence de candidat est-elle détectée avant d'ouvrir une vague ?

- **Nature** · Fait de code à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-165 → `SCRUM-379` À faire · UC-287 → `SCRUM-302` Revue en cours
- **Intitulé** · UC-165 / UC-287
- **Contexte** · Relevé en lisant le code aujourd'hui ; aucun test n'a été exécuté en staging.
- **État du code au 09/10** · **À vérifier** — Le lien existe ; l'expiration automatique après la course reste à établir par lecture de `create_share_link` et `get_shared_ride`.
- **Source** · Constat de code · branche courante au 09/10/2026 · UC-287

**Réponse :**

> 

### 6. Deux appels simultanés à la création de course pour le même passager peuvent-ils créer deux courses ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-010 → `SCRUM-213` Terminé(e)
- **Intitulé** · Le passager commande une course
- **Contexte** · Le passager transforme une estimation en engagement : il demande qu'un chauffeur vienne le chercher, au prix qui vient de lui être annoncé.
- **État du code au 09/10** · **Présent** — `POST /v1/rides` crée la course en `requested` et fige barème, taux de commission et niveau de confort sur la course (`services.py:116-181`, gel ligne 160).
- **Source** · Fiche UC-010 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 7. La déconnexion du canal temps réel est-elle exploitable comme signal de silence, ou un chauffeur peut-il rester connecté sans émettre de position ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-256 → `SCRUM-224` À faire
- **Intitulé** · Le passager distingue sa propre perte de connexion de celle du chauffeur
- **Contexte** · Quand l'information cesse d'arriver, le passager doit savoir de quel côté vient le problème.
- **État du code au 09/10** · **Absent du code** — Aucun signal distinguant la perte de connexion du passager de celle du chauffeur. Les positions portent un TTL Redis, exploité pour l'attente, pas diffusé comme état de santé.
- **Source** · Fiche UC-256 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 8. La route `/api/v1/couriers/{id}/availability` attendue côté DiddiGo par le contrôle croisé DiddiSend existe-t-elle sous un autre nom, ou est-elle à créer ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-107 → `SCRUM-287` A tester
- **Intitulé** · Le système évite qu'un pro reçoive deux missions incompatibles
- **Contexte** · Un pro qui a accepté une course ou une livraison ne doit pas se retrouver sollicité pour une seconde mission incompatible avant d'avoir terminé la première — cela créerait une double affectation…
- **État du code au 09/10** · **Présent** — Un chauffeur déjà sur une course est exclu des offres — invariant couvert par `tests/test_matching.py`.
- **Source** · Fiche UC-107 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 9. Le lien de partage de livraison expire-t-il effectivement à la fin de la livraison ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-165 → `SCRUM-379` À faire
- **Intitulé** · Le lien expire automatiquement : 20 min après la course, à la fin de la livraison
- **Contexte** · Un lien de suivi ne doit pas rester valide indéfiniment : une fois la mission terminée, l'accès à la position ne se justifie plus, et doit s'arrêter automatiquement.
- **État du code au 09/10** · **À vérifier** — Le lien existe ; l'expiration automatique après la course reste à établir par lecture de `create_share_link` et `get_shared_ride`.
- **Source** · Fiche UC-165 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 10. Le passage hors ligne est-il bloqué pendant une course en cours, ou seulement sans effet sur le dispatch pendant ce temps ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-024 → `SCRUM-189` Terminé(e)
- **Intitulé** · Le chauffeur passe hors ligne
- **Contexte** · Le chauffeur cesse de vouloir recevoir des courses. Un geste simple, qui doit rester possible à tout moment où il n'est pas engagé dans une mission.
- **État du code au 09/10** · **Présent** — `POST /v1/drivers/offline`.
- **Source** · Fiche UC-024 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 11. Un chauffeur peut-il émettre une position sur une course à laquelle il n'est pas affecté ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-028 → `SCRUM-193` Terminé(e)
- **Intitulé** · Le chauffeur envoie sa position pendant la course
- **Contexte** · Le chauffeur transmet sa position en continu, pour que le passager le voie approcher et que la distance réelle de la course puisse être calculée à l'arrivée.
- **État du code au 09/10** · **Présent** — `POST /v1/rides/{id}/location-samples` (`services.py:582`) accepte des lots ; positions et vitesses en Redis avec TTL.
- **Source** · Fiche UC-028 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 12. À quel moment exact le paiement d'une course est-il capturé ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-254 → `SCRUM-222` Terminé(e)
- **Intitulé** · Le passager choisit son mode de paiement avant de commander
- **Contexte** · Le passager décide comment il paiera — en espèces ou par un moyen numérique — avant d'engager la course, et non au moment de descendre du véhicule.
- **État du code au 09/10** · **Présent** — Moyen de paiement porté par la demande de course et conservé sur la course ; `422 INVALID_PAYMENT_METHOD` sur valeur inconnue.
- **Source** · Fiche UC-254 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-017` — Gérer attente, escales et annulation

**Ce que le planning attend.** Attente facturée et escales : début/fin visibles, supplément, nouveau montant. Pas de double comptage après reconnexion. Annulation : qui, à quelle étape, quelles conséquences. Incident/urgence signalable vers le circuit humain.

**Limite que le planning déclare.** Temps gratuit, tarifs, accord du client à formaliser.

**Décisions produit applicables.** PROD-012 arrivée et attente · PROD-026 escale · PROD-014 annulation et fin anticipée · PROD-036 incident

**Tickets Jira du livrable backend** — `SCRUM-6` Done (BE015) · `SCRUM-7` To Do (BE015) · `SCRUM-524` A tester (BE015) · `SCRUM-537` V2 (BE015)

**Confluence.** Lot — DiddiGo / Passager (917523), Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), Sprint 2 · Lot — Urgence et securite des personnes (393217)

### 1. Le motif « chauffeur indisponible » fait basculer la course en annulation par le chauffeur même lorsque l'appelant est le passager

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-013 → `SCRUM-216` Terminé(e)
- **Intitulé** · Le passager annule une course
- **Contexte** · Le passager n'a plus besoin de sa course, ou ne veut plus l'attendre. Il l'annule, en sachant avant de confirmer si cela lui coûte quelque chose.
- **État du code au 09/10** · **Présent** — `POST /v1/rides/{id}/cancel` (`services.py:519-553`) : motif contrôlé contre `VALID_CANCEL_REASONS`, refus sur course terminée, déjà annulée ou `no_driver_found`, arrêt de l'attente si active, statut cible distinct passager/chauffeur, motif persisté. Aucune facturation n'est produite.
- **Source** · Fiche UC-013 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Le seul motif proche du silence du chauffeur impute l'annulation au chauffeur, alors que UC-257 demande qu'il ne soit pas mis en cause

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-257 → `SCRUM-225` À faire
- **Intitulé** · Le passager annule sans frais quand le chauffeur est silencieux au-delà du délai défini avant la prise en charge
- **Contexte** · Un chauffeur a accepté la course mais ne donne plus signe de vie : il n'avance pas, sa position ne remonte plus. Le passager doit pouvoir partir sans payer, et sans avoir à se justifier.
- **État du code au 09/10** · **Partiel** — L'annulation est gratuite dans tous les cas (`services.py:519-553`), donc l'effet attendu est atteint. Aucun délai de silence du chauffeur n'est mesuré côté serveur.
- **Source** · Fiche UC-257 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. UC-183 est classé à créer et noté prévu en V2 ; le calcul du prix réel à partir des traces existe et fonctionne

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Prix, commissions et penalites → aucun ticket rattaché
- **Intitulé** · Prix, commissions et penalites
- **Contexte** · Ce lot détient la règle de l'argent : comment un prix se construit, comment il se décompose, ce qui peut s'y ajouter en cours de route, et ce qui se prélève ensuite.
- **Source** · Fiche de lot « Prix, commissions et penalites » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 4. Le chauffeur est-il informé que sa course a été annulée pour silence, et sait-il qu'il n'est pas pénalisé ?

- **Nature** · Fait à établir
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · UC-257 → `SCRUM-225` À faire
- **Intitulé** · Le passager annule sans frais quand le chauffeur est silencieux au-delà du délai défini avant la prise en charge
- **Contexte** · Un chauffeur a accepté la course mais ne donne plus signe de vie : il n'avance pas, sa position ne remonte plus. Le passager doit pouvoir partir sans payer, et sans avoir à se justifier.
- **État du code au 09/10** · **Partiel** — L'annulation est gratuite dans tous les cas (`services.py:519-553`), donc l'effet attendu est atteint. Aucun délai de silence du chauffeur n'est mesuré côté serveur.
- **Source** · Fiche UC-257 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-018` — Payer et retrouver ses gains

**Ce que le planning attend.** Paiement numérique ou cash. Commission Go 18 %. Cash : chauffeur encaisse, commission inscrite dans son wallet. Numérique : gains crédités seulement après confirmation. Chauffeur voit solde, gains, commissions, mouvements ; recharge ; voit pourquoi il est bloqué. Retrait : montant, bénéficiaire, frais, net, confirmation, suivi ; pas de double transfert.

**Limite que le planning déclare.** Assiette et arrondis de la commission à finaliser.

**Décisions produit applicables.** PROD-004 commissions · PROD-030 paiement à la fin · PROD-031 double paiement · PROD-032 retraits · PROD-040 impayés cloisonnés

**Tickets Jira du livrable backend** — `SCRUM-91` Done (BE016) · `SCRUM-92` Done (BE016) · `SCRUM-93` Done (BE016) · `SCRUM-98` To Do (BE016) · `SCRUM-99` Done (BE016) · `SCRUM-103` To Do (BE016) · `SCRUM-104` Done (BE016) · `SCRUM-105` Done (BE016) · `SCRUM-461` Done (BE016) · `SCRUM-514` Done (BE016) · `SCRUM-524` A tester (BE016)

**Confluence.** Lot — Argent des pros (1015809) · Lot — Prix, commissions et penalites (1507329)

### 1. Ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-071 → `SCRUM-23` Terminé(e)
- **Intitulé** · L'utilisateur retire de l'argent
- **Contexte** · Un utilisateur doit pouvoir faire sortir de l'argent de son portefeuille vers son compte mobile money, avec la confirmation par code de sécurité.
- **État du code au 09/10** · **Hors diddi-go** — Retrait : module DiddiPay, code non lu. **Aucune route de retrait dans `diddi-go`.**
- **Source** · Fiche UC-071 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. Comment le remboursement de 50 % après échec de livraison DiddiSend doit-il s'articuler avec le mécanisme de remboursement générique DiddiPay, une fois le wallet coursier construit ?

- **Nature** · Décision à prendre
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Bloque le déroulement d’une commande ou d’une course
- **Rattachement et Jira** · UC-193 → `SCRUM-95` Terminé(e)
- **Intitulé** · L'administrateur rembourse tout ou partie d'un paiement
- **Contexte** · Un paiement doit parfois être remboursé : une livraison échouée, une course annulée après encaissement, un litige tranché en faveur du client.
- **État du code au 09/10** · **Absent du code** — Aucune route de remboursement dans `diddi-go` ; la décision appartient au Backoffice et l'exécution à DiddiPay.
- **Source** · Fiche UC-193 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-019` — Limites du lancement

**Ce que le planning attend.** Chauffeurs indépendants uniquement. Pas de flottes ni de tarifs par zone (un champ « zone » peut être préparé). Stats de base et contrôles anti-abus inclus.

**Décisions produit applicables.** PROD-001 partenaires et flottes en V1 · PROD-015 zones en V1

**Tickets Jira du livrable backend** — `SCRUM-188` Done (BE014) · `SCRUM-190` Done (BE014) · `SCRUM-191` Done (BE014) · `SCRUM-193` Done (BE014) · `SCRUM-194` Done (BE014) · `SCRUM-437` Done (BE014) · `SCRUM-438` Done (BE014) · `SCRUM-441` To Do (BE014) · `SCRUM-442` Done (BE014) · `SCRUM-524` A tester (BE014) · `SCRUM-536` To Do (BE014) · `SCRUM-567` To Do (BE014)

**Confluence.** Lot — Partenaires et Flottes (1376273) · Lot — Zones, couverture et majoration (1146913)

### 1. Ce use case demande un polygone ; DiddiMap implémente un rectangle de configuration non modifiable

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-289 → `SCRUM-392` À faire
- **Intitulé** · L'administrateur définit le polygone de la zone de service d'une ville
- **Contexte** · Un administrateur doit tracer et modifier la zone de service d'une ville par un polygone réel, sans redéploiement — préalable structurant à tout le lot.
- **État du code au 09/10** · **Absent du code** — Aucun polygone ni géométrie de zone. La règle tarifaire est indexée par **ville** et catégorie de véhicule (`PricingRuleRepository.find_active(city, vehicle_category)`), sans géométrie.
- **Source** · Fiche UC-289 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. UC-289 demande un polygone ; DiddiMap implémente un rectangle de configuration non modifiable

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Zones, couverture et majoration → aucun ticket rattaché
- **Intitulé** · Zones, couverture et majoration
- **Contexte** · Ce lot répond à deux questions géographiques. Où travaillons-nous, et combien coûte une course selon l'endroit et le moment.
- **Source** · Fiche de lot « Zones, couverture et majoration » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Décisions non fonctionnelles

## `PAR-007` — Recevoir une offre et suivre une mission

**Ce que le planning attend.** Offre claire avec infos pour accepter/refuser. Notifications testées (app ouverte, arrière-plan, téléphone verrouillé). Client informé des changements de statut sans recharger. Contact par appel entre parties. Une offre déjà attribuée ne peut plus être acceptée.

**Limite que le planning déclare.** Numéro masqué ou appel direct : à choisir.

**Décisions produit applicables.** PROD-016 appel retenu ; messagerie et appels Internet en V1

**Tickets Jira du livrable backend** — `SCRUM-304` To Do (BE007) · `SCRUM-305` Done (BE007) · `SCRUM-306` To Do (BE007) · `SCRUM-533` Done (BE007) · `SCRUM-534` To Do (BE007) · `SCRUM-552` A tester (BE007)

**Confluence.** Lot — Notifications et canaux (1474561) · Lot — Communication en mission (753685)

### 1. Ce use case est marqué priorité absolue depuis le 31/08 ; ni la charge serveur ni l'écran d'offre ne portent de son ou de vibration

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-156 → `SCRUM-304` À faire
- **Intitulé** · Le pro est réveillé par un son et une vibration sur une offre, écran verrouillé
- **Contexte** · Un chauffeur qui a le téléphone verrouillé dans sa poche doit être réveillé par un son et une vibration quand une offre de course arrive — sans quoi l'offre expire sans qu'il ne l'ait jamais vue, le…
- **État du code au 09/10** · **Partiel** — L'offre est poussée en WebSocket et par FCM. `UserDevice` ne porte ni champ de son ni canal de notification (`notification/domain.py:10-15`) : rien n'est demandé côté serveur sur le réveil de l'appareil.
- **Source** · Fiche UC-156 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 2. UC-156 est marqué priorité absolue ; ni la charge serveur ni l'écran d'offre ne portent de son ou de vibration

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Notifications et canaux → aucun ticket rattaché
- **Intitulé** · Notifications et canaux
- **Contexte** · Ce lot décide si un message atteint la personne visée. Il couvre quatre canaux : les notifications push Android, les notifications push iPhone, le SMS et WhatsApp.
- **Source** · Fiche de lot « Notifications et canaux » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-016` — Commander et effectuer une course

**Ce que le planning attend.** Départ + destination (saisie ou voix), estimation, confirmation. Recherche d'un chauffeur éligible, offre, acceptation, suivi de l'approche, arrivée, début, fin. Même mission des deux côtés. Offre expirée, refus, aucun chauffeur, perte de connexion : issue explicite et reprise cohérente.

**Décisions produit applicables.** PROD-015 confort et devis · PROD-027 recherche en trois phases · PROD-013 début de course et secours GPS · PROD-011 reprise

**Tickets Jira du livrable backend** — `SCRUM-188` Done (BE014) · `SCRUM-190` Done (BE014) · `SCRUM-191` Done (BE014) · `SCRUM-193` Done (BE014) · `SCRUM-194` Done (BE014) · `SCRUM-437` Done (BE014) · `SCRUM-438` Done (BE014) · `SCRUM-441` To Do (BE014) · `SCRUM-442` Done (BE014) · `SCRUM-524` A tester (BE014) · `SCRUM-536` To Do (BE014) · `SCRUM-567` To Do (BE014)

**Confluence.** Lot — DiddiGo / Passager (917523), epic SCRUM-64, Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprints 1 et 2 · Lot — Matching et Priorite (1441793)

### 1. UC-253 est classé à créer sur l'axe back ; l'état, sa transition, son journal et son événement existent

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-253 → `SCRUM-221` À faire
- **Intitulé** · Le passager est informé qu'aucun chauffeur n'est disponible et peut relancer ou demander à être notifié
- **Contexte** · La recherche a échoué. Le passager doit l'apprendre clairement, et pouvoir faire quelque chose : relancer, attendre qu'on le prévienne, ou renoncer.
- **État du code au 09/10** · **Partiel** — État terminal `no_driver_found` et événement WebSocket `ride.no_driver_found` (`websocket.py:156`), produits à l'épuisement du budget de recherche (`matching_service.py` `_give_up`). Aucune relance côté serveur : le passager crée une nouvelle course. Aucune mise en attente de notification.
- **Source** · Fiche UC-253 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

## `PAR-017` — Gérer attente, escales et annulation

**Ce que le planning attend.** Attente facturée et escales : début/fin visibles, supplément, nouveau montant. Pas de double comptage après reconnexion. Annulation : qui, à quelle étape, quelles conséquences. Incident/urgence signalable vers le circuit humain.

**Limite que le planning déclare.** Temps gratuit, tarifs, accord du client à formaliser.

**Décisions produit applicables.** PROD-012 arrivée et attente · PROD-026 escale · PROD-014 annulation et fin anticipée · PROD-036 incident

**Tickets Jira du livrable backend** — `SCRUM-6` Done (BE015) · `SCRUM-7` To Do (BE015) · `SCRUM-524` A tester (BE015) · `SCRUM-537` V2 (BE015)

**Confluence.** Lot — DiddiGo / Passager (917523), Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), Sprint 2 · Lot — Urgence et securite des personnes (393217)

### 1. Panne ou retard sans danger immédiat — Enregistrer la solution convenue ; accord explicite si coût ou trajet change.

- **Nature** · Cas limite à fermer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Empêche d’aller au bout d’un parcours principal
- **Rattachement et Jira** · EDGE-004 → aucun ticket rattaché
- **Intitulé** · EDGE-004
- **Contexte** · Décision déjà acquise : PROD-017/036 : contact client, discussion, signalement, reprise support et remontée du ticket. Pas d'astreinte opérationnelle promise.
- **Source** · Journal des cas particuliers · 09/10/2026 · EDGE-004

**Réponse :**

> 

### 2. La décision du 31/08 prévoit une notification du contact d'urgence ; l'alerte n'envoie aucun message

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Produit
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · UC-015 → `SCRUM-218` Terminé(e)
- **Intitulé** · Le passager déclenche une alerte d'urgence
- **Contexte** · Le passager se sent en danger pendant sa course. Il déclenche une alerte en un geste, sans avoir à expliquer, et quelqu'un est prévenu.
- **État du code au 09/10** · **Présent** — `POST /v1/rides/{id}/emergency` ; l'alerte **est envoyée** : webhook WhatsApp au support et au contact d'urgence, plus courriel SMTP (`ride/application/emergency_notifications.py:24-96`). Chaque canal non configuré est explicitement tracé en `_skip` avec son motif.
- **Source** · Fiche UC-015 · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

### 3. UC-171 est classé partiel ; la route d'alerte accepte déjà le chauffeur assigné

- **Nature** · Contradiction à arbitrer
- **Décideur désigné** · Technique
- **Pourquoi retenue** · Contradiction code / parcours
- **Rattachement et Jira** · Urgence et securite des personnes → aucun ticket rattaché
- **Intitulé** · Urgence et securite des personnes
- **Contexte** · Ce lot est court et il n'est pas comme les autres. Six use cases, et le seul du corpus dont l'échec peut mettre quelqu'un en danger.
- **Source** · Fiche de lot « Urgence et securite des personnes » · section « Questions ouvertes » · corpus du 14/09/2026

**Réponse :**

> 

---

# Valeurs fermées — à reporter en configuration

Consigne de lancement : toute question de durée, de seuil, de limite ou de valeur numérique est
fermée. Le défaut actuel du code fait foi pour le lancement et part en variable d'environnement.

| Question fermée | Parcours | Variable | Défaut actuel | Emplacement |
| --- | --- | --- | --- | --- |
| Combien de fois par jour le mode retour maison peut-il être activé ? | `PAR-002` | à sortir en .env | non implémenté | à ajouter |
| Combien de temps avant l'expiration d'un document le chauffeur est-il alerté, et à quel moment est-il bloqué ? | `PAR-002` | à sortir en .env — un statut d'expiration existe | calculé sans seuil d'alerte | ride/application/driver_service.py |
| Le code fixe le délai de réponse à une offre à 15 s ; la décision est encore à trancher | `PAR-002` | OFFER_TTL_SECONDS — aujourd'hui constante de code, à sortir en .env | 15 s | ride/infra/offer_store.py:35 |
| Quel est le barème de pénalité pour un refus d'offre ? | `PAR-002` | à identifier | à relever dans le code |  |
| Quel est le barème de pénalité pour une annulation par le pro après acceptation ? | `PAR-002` | à identifier | à relever dans le code |  |
| Quel délai légal s'applique à une demande d'accès ou d'effacement, et à partir de quel événement ? | `PAR-004` | à sortir en .env | non implémenté | à ajouter |
| Quel est le délai de grâce entre la demande de suppression et l'anonymisation définitive ? | `PAR-004` | à sortir en .env | non implémenté | à ajouter |
| Un compte en délai de grâce peut-il encore commander une course ou une livraison, ou est-il restreint pendant cette période ? | `PAR-004` | à sortir en .env | non implémenté | à ajouter |
| Combien de temps après la fin de la mission le canal reste-t-il ouvert ? | `PAR-007` | à identifier | à relever dans le code |  |
| Pendant combien de temps les échanges sont-ils conservés, et qui peut les lire ? | `PAR-007` | à identifier | à relever dans le code |  |
| Quel est le délai d'acceptation d'une offre de course DiddiGo ? | `PAR-007` | OFFER_TTL_SECONDS — aujourd'hui constante de code, à sortir en .env | 15 s | ride/infra/offer_store.py:35 |
| Au bout de combien de temps l'identité du chauffeur est-elle masquée dans l'historique ? | `PAR-008` | à identifier | à relever dans le code |  |
| Pendant combien de temps un utilisateur conserve-t-il l'accès à son historique ? | `PAR-008` | à identifier | à relever dans le code |  |
| Combien de temps la demande « prévenez-moi » reste-t-elle active ? | `PAR-016` | à créer — aucune mise en attente de notification | absent | à ajouter |
| L'ancienneté d'une position est-elle présentée en heure absolue ou en durée écoulée ? — proposition Claude en attente de validation : durée écoulée sous 10 min, heure absolue au-delà. Voir decisions-actees.md | `PAR-016` | WAITING_TELEMETRY_TTL_SECONDS | 30 s | core/settings.py:131 |
| Le code applique un taux de commission de 8 %, la décision du 14/09 fixe 10 % | `PAR-016` | à sortir en .env — aujourd'hui constante de code | 0,08 soit 8 % | ride/application/services.py:51 |
| Le code fixe la durée de vie du lien de partage à 24 h, la décision du 31/08 dit 20 minutes après la fin de la course | `PAR-016` | à sortir en .env — aujourd'hui en dur | 24 h dans le code, 20 min décidé le 31/08 | ride/application/services.py |
| Quel plafond de temps d'attente est facturable sur une course ? | `PAR-016` | WAITING_PRICE_PER_MINUTE_XOF | 100 XOF/min, sans franchise | core/settings.py:129 |
| Quel plafond limite l'effet de la priorité par rapport à la proximité ? | `PAR-016` | MATCHING_PRIORITY_CAP_SECONDS / _SECONDS_PER_POINT / _POINTS_* | plafond 120 s, 10 s par point, +1 course terminée, −3 annulation chauffeur | core/settings.py:71-75 |
| Quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | `PAR-016` | à créer — aucune franchise d'escale dans le code | absent | à ajouter |
| Quelles sont les valeurs successives du rayon de recherche, et combien de vagues au maximum ? | `PAR-016` | MATCHING_SEARCH_RADIUS_STEP_KM / _MAX_KM | 2 km par vague, plafond 15 km | core/settings.py:64-65 |
| Si le prix recalculé à la commande diffère du prix estimé, la commande est-elle refusée ou le nouveau prix présenté avant création ? | `PAR-016` | côté application mobile | 30 s décidé le 14/09 | hors diddi-go |
| Un même lien peut-il être ouvert par plusieurs personnes en même temps, et faut-il le limiter ? | `PAR-016` | à sortir en .env | non implémenté | à ajouter |
| Le seuil de durée de 3 min recommandé pour le supplément d'escale est-il retenu ? | `PAR-017` | à créer — aucune franchise d'escale dans le code | absent | à ajouter |
| Le taux de commission appliqué par DiddiGo est de 8 %, la décision du 14/09 fixe 10 % | `PAR-017` | à sortir en .env — aujourd'hui constante de code | 0,08 soit 8 % | ride/application/services.py:51 |
| Quel est le barème des pénalités d'annulation, par persona et par moment ? | `PAR-017` | à identifier | à relever dans le code |  |
| Quel plafond de temps d'attente est facturable sur une même course, et porte-t-il sur une période ou sur le cumul ? | `PAR-017` | WAITING_PRICE_PER_MINUTE_XOF | 100 XOF/min, sans franchise | core/settings.py:129 |
| Environ 3 % évoqués seulement à titre indicatif (Cotation PSP) ? | `PAR-018` | à identifier | à relever dans le code |  |
| La commission Go 8 % et la majoration plafond 1,60 constatées lors de la lecture précédente ne correspondent pas aux décisions 18 % et 1,50 en V1. Aucun changement backend n'a été fait pendant cette revue. | `PAR-018` | à sortir en .env — aujourd'hui constante de code | 0,08 soit 8 % | ride/application/services.py:51 |
| Le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % | `PAR-018` | à sortir en .env — aujourd'hui constante de code | 0,08 soit 8 % | ride/application/services.py:51 |
| Le découvert de 2 000 F et le seuil minimum de 1 500 F sont-ils deux réglages distincts à combiner (ex. : blocage si solde < -2 000 F), ou une seule et même valeur mal nommée deux fois ? | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Le découvert peut-il être dépassé en cours de course déjà acceptée, avec blocage seulement à la prochaine tentative de mise en ligne, ou la course en cours est-elle elle-même affectée ? | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Le seuil de 1 500 F et le découvert de 2 000 F sont-ils deux réglages distincts (solde minimum pour accepter, plancher négatif toléré), ou la même valeur exprimée différemment ? | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Que devient le solde d'un pro qui quitte la plateforme avec un découvert ? | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Quel plafond d'espèces un coursier peut-il détenir avant suspension des missions payées en espèces ? | `PAR-018` | à identifier | à relever dans le code |  |
| Quelle valeur retenir pour « go.online_min_balance » ? Repère actuel : Non fixé (XOF). | `PAR-018` | à identifier | à relever dans le code |  |
| Quelle valeur retenir pour « professional.withdrawal_fee » ? Repère actuel : Frais réels ? | `PAR-018` | à identifier | à relever dans le code |  |
| Quelle valeur retenir pour « professional.withdrawal_minimum » ? Repère actuel : Aucun minimum commercial selon règle validée (XOF). | `PAR-018` | à identifier | à relever dans le code |  |
| Combien de temps dure une majoration exceptionnelle, et qui peut la déclencher ? | `PAR-019` | à identifier | à relever dans le code |  |
| La direction décide le 14/09 que le plafond de majoration reste interne et non public ; la section 4 du document de référence exige qu'il soit public, « ce qui évite le scandale » — les deux décisions portent la même date et se contredisent | `PAR-019` | à sortir en .env — aujourd'hui constante de code | 1,60 | ride/application/services.py:50 |
| Quel est le montant du supplément de retour à vide, et comment est-il calculé ? | `PAR-019` | à identifier | à relever dans le code |  |
| L'intervalle de 60 s configuré par défaut est-il la valeur retenue ? | `PAR-001` | OTP_RATE_LIMIT_SECONDS | 60 s | core/settings.py:43 |
| La durée de 15 min configurée par défaut est-elle la valeur retenue ? | `PAR-001` | JWT_ACCESS_LIFETIME_MINUTES | 15 min | core/settings.py:40 |
| La durée de vie de 300 s configurée par défaut est-elle la valeur retenue ? | `PAR-001` | OTP_CODE_LIFETIME_SECONDS | 300 s | core/settings.py:44 |
| Le maximum de 5 essais configuré par défaut est-il la valeur retenue ? | `PAR-001` | à créer — aucun compteur d'essais côté serveur | absent | à ajouter |
| UC-147 décrit un temps d'arrivée estimé qui se met à jour ; aucun recalcul n'existe | `PAR-005` | côté application mobile | 30 s décidé le 14/09 | hors diddi-go |
| Combien de fois un message non délivré est-il retenté, et à quel rythme ? | `PAR-007` | à identifier | à relever dans le code |  |
| Ce use case décrit un temps d'arrivée estimé qui se met à jour ; aucun recalcul n'existe | `PAR-016` | côté application mobile | 30 s décidé le 14/09 | hors diddi-go |
| Sur quelle référence de temps l'âge d'une position est-il calculé, celle du serveur ou celle du téléphone ? | `PAR-016` | WAITING_TELEMETRY_TTL_SECONDS | 30 s | core/settings.py:131 |
| Le contrôle « véhicule à l'arrêt » s'appuie-t-il sur la dernière position connue, ou faut-il une confirmation explicite du chauffeur ? | `PAR-017` | WAITING_STATIONARY_SPEED_THRESHOLD_KMH | 3,0 km/h | core/settings.py:130 |
| Le solde minimum est configuré à zéro dans tous les fichiers de déploiement lus, la décision du 14/09 fixe 1 500 F | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Un découvert borné est-il toléré puis bloquant ? Les deux seuils existent (`driver_min_balance`, `driver_max_estimated_commission`) et sont neutres par défaut ; le comportement de `wallet_service.py` reste à lire. | `PAR-018` | DRIVER_MIN_BALANCE | 0, donc contrôle neutre | core/settings.py:124 |
| Quelle est la durée de conservation de chaque type de donnée ? | `PAR-004` | à identifier | à relever dans le code |  |
| Quelle est la durée de conservation du journal des envois ? | `PAR-007` | à identifier | à relever dans le code |  |
| Au bout de combien de temps une alerte non prise en charge est-elle escaladée, et vers qui ? | `PAR-017` | à identifier | à relever dans le code |  |
| Une alerte peut-elle être déclenchée après la fin de la course, et pendant combien de temps ? | `PAR-017` | à identifier | à relever dans le code |  |

Trois de ces valeurs sont aujourd'hui des **constantes de code** : les reporter en configuration
demande donc un changement de code, couvert par `SCRUM-585`. Il s'agit du taux de commission
(`services.py:51`), du plafond de majoration (`services.py:50`) et du TTL d'offre
(`offer_store.py:35`).

Quatre lignes n'ont **aucun défaut à reporter** parce que rien n'existe dans le code : le compteur
d'essais OTP côté serveur, la franchise d'escale, la mise en attente de notification « prévenez-moi »,
et le seuil d'alerte avant expiration d'un document.

# Fermées — légal et conformité

Consigne de lancement : non bloquant pour le code MVP. Purges automatiques complexes et processus
OHADA / ARTCI traités par procédure manuelle au support pour le lancement.

| Question | Parcours | Nature | Décideur |
| --- | --- | --- | --- |
| Une déclaration ou une autorisation préalable ARTCI est-elle requise, et laquelle ? | `PAR-003` | Décision à prendre | Juridique |
| Des conditions d'utilisation et une politique de confidentialité existent-elles déjà sous une forme quelconque, prêtes à être versionnées ? | `PAR-004` | Fait à établir | Juridique |
| Le retrait du consentement cartographique interrompt-il l'envoi des traces, ou seulement leur exploitation ? | `PAR-004` | Décision à prendre | Juridique |
| Quel est le statut juridique du montage de location-vente de véhicule ? | `PAR-019` | Décision à prendre | Juridique |
| Le journal d'audit du back-office enregistre-t-il les lectures de données personnelles, ou seulement les actions de modification ? | `PAR-003` | Fait à établir | Technique |
| Chat et support — 90 jours décidés ; proposition de départ : fin de mission pour le chat, clôture du dossier pour le support. Le porteur doit confirmer ces déclencheurs. | `PAR-004` | Proposition à approuver | Juridique |
| Conservation, PROD-028 / 038 — état connu : Cible, pas preuve de purge implémentée. | `PAR-004` | Constat à instruire | Produit |
| Contrôle du corpus avant entraînement. Les conversations restent à 90 jours. Les autres paramètres détaillés ci-dessous, non repris dans le comparatif approuvé, restent des propositions. Aucune durée n'est présentée comme obligation légale. Vérifier dispositif ? | `PAR-004` | Proposition à approuver | Juridique |
| Exceptions avec le responsable conformité avant activation ? | `PAR-004` | Proposition à approuver | Juridique |
| Le journal d'audit enregistre-t-il les lectures de données personnelles, ou seulement les modifications ? | `PAR-004` | Fait à établir | Technique |
| PROD-038 valide GPS détaillé 30 jours puis agrégats, preuves de litige séparées ? | `PAR-004` | Proposition à approuver | Juridique |
| Que se passe-t-il si l'anonymisation réussit dans certains services et échoue dans d'autres ? | `PAR-004` | Décision à prendre | Technique |
| Quel service porte l'orchestration d'une demande d'export ou d'anonymisation, et comment il connaît la liste des services à interroger ? | `PAR-004` | Fait à établir | Technique |
| Durée de conservation, suppression, hébergement ? | `PAR-006` | Point flou à fermer | Produit |

# Déjà tranchées avant ce relevé

Relevées dans `management/specs/etat/decisions-actees.md` du 14/09 et dans le registre des décisions
produit du 09/10. Elles ne sont plus à poser.

**Que se passe-t-il si le canal d'envoi du code est indisponible ? existe-t-il un canal de secours ?**

- *Réponse partielle* · Courriel et WhatsApp sont confirmés pour le lancement. Le SMS n'est pas encore confirmé — c'est donc le point à fermer, pas l'existence d'un canal de secours.
- Source · decisions-actees.md · actée équipe 14/09

**Que se passe-t-il si le canal d'envoi est indisponible ? existe-t-il un canal de secours ?**

- *Réponse partielle* · Courriel et WhatsApp sont confirmés pour le lancement. Le SMS n'est pas encore confirmé — c'est donc le point à fermer, pas l'existence d'un canal de secours.
- Source · decisions-actees.md · actée équipe 14/09

**Quelle est la durée de vie d'un code à usage unique, et combien d'essais avant blocage ?**

- *Décision actée* · Durée de session sans réauthentification : jusqu'à 1 mois, avec réauthentification forcée si l'application n'a pas été ouverte depuis 2 semaines. Pour le code de confirmation DiddiPay : 3 tentatives puis blocage de 10 minutes, puis 2 tentatives et blocage définitif.
- Source · decisions-actees.md · actée équipe 14/09

**Quel est le barème de points de priorité et sa fenêtre de calcul ?**

- *Décision actée* · Plafond de base 150 points, jusqu'à 175 avec les bonus cumulés, jamais au-delà. Score de départ d'un nouveau chauffeur : 80 points. Sous 50 points, le compte est suspendu.
- Source · decisions-actees.md · actée équipe 14/09

**Quelles données restent après anonymisation, et sous quelle forme, pour satisfaire la conservation comptable OHADA ?**

- *Réponse partielle* · Les durées sont actées — 10 ans pour les pièces comptables, 12 mois pour les données clients, anonymisation sous 1 an ou sous 60 jours sur demande. Ce qui reste ouvert est la liste exacte des champs conservés sous forme anonymisée et leur format.
- Source · decisions-actees.md · actée équipe 14/09, liste des champs non arrêtée

**Quelles données restent après anonymisation pour satisfaire la conservation comptable OHADA ?**

- *Réponse partielle* · Les durées sont actées — 10 ans pour les pièces comptables, 12 mois pour les données clients, anonymisation sous 1 an ou sous 60 jours sur demande. Ce qui reste ouvert est la liste exacte des champs conservés sous forme anonymisée et leur format.
- Source · decisions-actees.md · actée équipe 14/09, liste des champs non arrêtée

**Au bout de combien de temps sans position un véhicule est-il considéré comme silencieux, et l'alerte part vers qui ?**

- *Décision actée* · 5 minutes sans position déclenchent une alerte. Le destinataire de cette alerte reste une proposition non validée : la file de support en niveau urgent, avec escalade vers le SOS au-delà de 15 minutes sans réponse.
- Source · decisions-actees.md · actée équipe 14/09

**Quelles informations la page publique affiche-t-elle ?**

- *Décision actée* · Prénom du chauffeur — pas le nom de famille —, immatriculation, modèle et couleur du véhicule. Le numéro de téléphone reste une proposition non validée : ne jamais l'afficher, et proposer un appel masqué quand le masquage sera disponible.
- Source · decisions-actees.md · actée équipe 14/09

**À partir de quel âge la position affichée est-elle présentée comme ancienne ?**

- *Décision actée* · 3 minutes sans coordonnées GPS reçues du chauffeur dans l'application passager ; 5 minutes sur la page publique de suivi.
- Source · decisions-actees.md · actée équipe 14/09

**Au bout de combien de temps sans position un chauffeur est-il considéré comme silencieux ?**

- *Décision actée* · 5 minutes sans position déclenchent une alerte. Le destinataire de cette alerte reste une proposition non validée : la file de support en niveau urgent, avec escalade vers le SOS au-delà de 15 minutes sans réponse.
- Source · decisions-actees.md · actée équipe 14/09

**Quel est le délai d'acceptation d'une offre ?**

- *Réponse partielle* · Pour la livraison DiddiSend : 1 minute pour accepter, 3 minutes d'attente sur place, annulation sans pénalité passé 5 minutes au total. Le livreur dispose de 2 minutes de plus que le chauffeur DiddiGo — mais le délai propre à la course DiddiGo reste explicitement à trancher.
- Source · decisions-actees.md · actée équipe 14/09

**Quel est le barème de points de priorité, sa fenêtre de calcul et le score de départ d'un nouveau pro ?**

- *Décision actée* · Plafond de base 150 points, jusqu'à 175 avec les bonus cumulés, jamais au-delà. Score de départ d'un nouveau chauffeur : 80 points. Sous 50 points, le compte est suspendu.
- Source · decisions-actees.md · actée équipe 14/09

**Quelles informations la page publique affiche-t-elle — nom du chauffeur, plaque, numéro de téléphone ?**

- *Décision actée* · Prénom du chauffeur — pas le nom de famille —, immatriculation, modèle et couleur du véhicule. Le numéro de téléphone reste une proposition non validée : ne jamais l'afficher, et proposer un appel masqué quand le masquage sera disponible.
- Source · decisions-actees.md · actée équipe 14/09

**Quels frais s'appliquent à une annulation par le passager, et à partir de quel moment ?**

- *Décision actée* · Avant le début de course : aucun frais, attente acquise comprise. Après démarrage, c'est une fin anticipée : le trajet effectué est facturé au barème accepté au départ, et le total est gratuit s'il reste sous le seuil configuré.
- Source · PROD-014 · registre du 09/10

**Quels frais s'appliquent à une annulation par le passager, et à partir de quel moment du cycle ?**

- *Décision actée* · Avant le début de course : aucun frais, attente acquise comprise. Après démarrage, c'est une fin anticipée : le trajet effectué est facturé au barème accepté au départ, et le total est gratuit s'il reste sous le seuil configuré.
- Source · PROD-014 · registre du 09/10

**Quel est le tarif du mode attente ?**

- *Décision actée* · 100 F par minute, identique au tarif normal, comptabilisé dès l'activation. La part revenant au chauffeur est identique à sa part sur le prix de base.
- Source · decisions-actees.md · actée équipe 14/09

**Quelle est la grille tarifaire de lancement, par ville et par profil ?**

- *Décision actée* · Facturation à la minute : 100 F par minute de trajet estimée, tenant compte de la zone et du profil. Prix minimum d'une course : 500 F quelle que soit la distance. Aucune distance minimale : la course n'est jamais refusée pour ce motif.
- Source · decisions-actees.md · actée équipe 14/09

# Hors des trois critères du focus MVP

151 questions conservées pour après le gel : ni contradiction code / parcours, ni blocage du
déroulement, ni cas limite empêchant d'aller au bout d'un parcours principal.

| Question | Parcours | Axe | Nature | Décideur |
| --- | --- | --- | --- | --- |
| Ancien téléphone perdu, changement bénéficiaire — Processus de récupération distinct, preuves adaptées, notification et révocation des sessions compromises ; protocole à approuver. | `PAR-001` | Produit | Cas limite à fermer | Produit |
| Identités multiples et bonus — Conditions de campagne, attribution après prestation/paiement, déduplication et recours à définir. | `PAR-001` | Produit | Cas limite à fermer | Produit |
| Récupération de compte : expliquer le cas de perte du moyen actuel. OTP du nouveau numéro = preuve de contrôle de ce numéro, pas preuve de propriété de l'ancien compte. Distinguer récupération du compte et validation d'un nouveau bénéficiaire ; protocole exact à approuver. | `PAR-001` | Produit | Précision à fermer | Produit |
| Un compte suspendu voit-il le motif de sa suspension ? | `PAR-001` | Produit | Décision à prendre | Produit |
| Un utilisateur peut-il changer le téléphone ou le courriel rattaché à son compte ? | `PAR-001` | Produit | Décision à prendre | Produit |
| Comment la pénalité doublée sous 1 km s'applique-t-elle ? | `PAR-002` | Produit | Décision à prendre | Produit |
| Quelles photos de véhicule sont obligatoires et lesquelles sont facultatives ? | `PAR-002` | Produit | Décision à prendre | Produit |
| Quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie ? | `PAR-002` | Produit | Décision à prendre | Produit |
| Approuvez-vous le parcours de suppression de compte proposé, en cinq étapes ? | `PAR-004` | Produit | Proposition à approuver | Produit |
| Approuvez-vous le socle anti-fraude d'identité proposé pour le MVP ? | `PAR-004` | Produit | Proposition à approuver | Produit |
| Les règles d'éligibilité aux bonus prévues en V1 ? | `PAR-004` | Produit | Proposition à approuver | Produit |
| Le tricycle de DiddiSend relève-t-il du profil moto ou d'un profil propre ? | `PAR-005` | Produit | Décision à prendre | Produit |
| Que voit le passager quand le temps d'arrivée estimé n'est pas disponible ? | `PAR-005` | Produit | Décision à prendre | Produit |
| Quelle est la zone de couverture exacte au lancement ? | `PAR-005` | Produit | Décision à prendre | Produit |
| Éventuels sous-traitants restent à arbitrer ? | `PAR-006` | Produit | Point flou à fermer | Produit |
| Des messages prédéfinis sont-ils proposés, et lesquels ? | `PAR-007` | Produit | Décision à prendre | Produit |
| Le chat autorise-t-il l'envoi de photos, ou du texte seulement ? | `PAR-007` | Produit | Décision à prendre | Produit |
| Le périmètre retient l'appel ; le choix entre numéro masqué et appel direct reste à fixer. | `PAR-007` | Produit | Point flou à fermer | Produit |
| Que fait le système quand aucun appareil n'est enregistré pour un pro à qui une offre est destinée ? | `PAR-007` | Produit | Décision à prendre | Produit |
| Quel canal est prioritaire pour un code destinataire, et lequel sert de secours ? | `PAR-007` | Produit | Décision à prendre | Produit |
| Quel fournisseur assure le masquage de numéro, et à quel coût par appel ? | `PAR-007` | Produit | Décision à prendre | Administration |
| Quelles notifications l'utilisateur peut-il désactiver, et lesquelles sont obligatoires ? | `PAR-007` | Produit | Décision à prendre | Produit |
| Un administrateur peut-il lire un échange sans motif, ou seulement sur un litige ouvert ? | `PAR-007` | Produit | Décision à prendre | Juridique |
| Exploitation, PROD-039 — état connu : Preuves à produire. | `PAR-008` | Produit | Constat à instruire | Produit |
| Que contient exactement un relevé de gains de pro ? | `PAR-008` | Produit | Décision à prendre | Produit |
| Que contient exactement un reçu de course et un reçu de livraison ? | `PAR-008` | Produit | Décision à prendre | Produit |
| Que fait le système d'une action rejouée dont l'horodatage est hors tolérance ? | `PAR-008` | Produit | Décision à prendre | Produit |
| Que fait le système d'une action rejouée dont l'horodatage est hors tolérance — rejet, correction, acceptation signalée ? | `PAR-008` | Produit | Décision à prendre | Produit |
| Un reçu doit-il porter une mention de TVA distincte, et sous quelle forme ? | `PAR-008` | Produit | Décision à prendre | Juridique |
| Absence Go — Confirmer le départ des dix minutes à l'arrivée GPS validée ? | `PAR-016` | Produit | Arbitrage produit ouvert | Produit |
| Complété avant le lancement, ou le risque de double affectation entre les deux services est-il jugé négligeable en phase 1 ? | `PAR-016` | Produit | Décision à prendre | Produit |
| Il vérifie les lieux proposés et consulte une estimation avant de confirmer. | `PAR-016` | Produit | Point flou à fermer | Produit |
| Le paiement d'une course peut-il être réglé depuis le wallet utilisateur de DiddiPay ? | `PAR-016` | Produit | Décision à prendre | Produit |
| Le passager doit-il être informé différemment selon que personne n'était présent ou que tous ont refusé ? | `PAR-016` | Produit | Décision à prendre | Produit |
| Le plafond est-il exprimé en écart de temps absolu, en pourcentage du temps d'arrivée, ou en rang maximal de dépassement ? | `PAR-016` | Produit | Proposition à valider | Produit |
| Le score de réputation existant (`GET /v1/me/scores`) est-il le même concept que les « points de priorité » attendus ici, ou deux notions distinctes à ne pas confondre ? | `PAR-016` | Produit | Fait à établir | Produit |
| Ne pas importer implicitement le protocole d'absence Food dans Go ou Send ? | `PAR-016` | Produit | Arbitrage produit ouvert | Produit |
| Quelle densité de chauffeurs libres dans le rayon minimal est réellement nécessaire pour une expérience passager acceptable ? | `PAR-016` | Produit | Décision à prendre | Produit |
| Recherche Go, PROD-027 — état connu : SCRUM-63 ; défauts code 5 km initial, plafond 15 km, budget 120 s. | `PAR-016` | Produit | Constat à instruire | Produit |
| Admin expose aussi des changements de statut Identity. Ces briques ne prouvent pas la chaîne complète notification au pro, motif visible, contestation et décision de réactivation. | `PAR-017` | Produit | Constat à instruire | Produit |
| Blessure, agression, danger immédiat — Afficher un accès aux secours locaux appropriés et permettre un signalement après mise en sécurité, sans attendre une négociation client ou réponse support. Références locales à vérifier avant publication. | `PAR-017` | Produit | Cas limite à fermer | Produit |
| Décision PROD-036 : incident, priorité sécurité, intervention humaine, réattribution tracée lorsque possible et absence de double facturation. La répartition détaillée entre professionnels et la garde en cas de transfert restent à concevoir. | `PAR-017` | Produit | Constat à instruire | Produit |
| Food app/modules/restaurants/application/backoffice.py:26 : transitions suspend et reactivate explicites, avec contexte Backoffice. | `PAR-017` | Produit | Constat à instruire | Produit |
| Go possède statut suspended et notes de revue ; Send possède statut suspended, état de readiness bloquant et projection de capability correspondante. | `PAR-017` | Produit | Constat à instruire | Produit |
| Les acteurs autorisés, le temps gratuit éventuel, les tarifs ? | `PAR-017` | Produit | Point flou à fermer | Produit |
| Les règles d'accord du client restent à formaliser ? | `PAR-017` | Produit | Point flou à fermer | Produit |
| Que devient un frais d'annulation dont le prélèvement échoue ? | `PAR-017` | Produit | Décision à prendre | Administration |
| Quel est le pas de monnaie disponible, et l'arrondi se fait-il au bénéfice du client ou du chauffeur ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Quelle est l'assiette des frais de tentative sur une livraison échouée ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Quelle est la conséquence d'annulations répétées par un même passager ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Quels motifs d'annulation sont proposés au passager, et lesquels exonèrent de frais ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Un supplément validé reste-t-il dû si la course est annulée avant l'escale ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Une modification d'itinéraire qui raccourcit le trajet donne-t-elle lieu à une réduction ? | `PAR-017` | Produit | Décision à prendre | Produit |
| Une validation orale de supplément engage-t-elle le passager en cas de litige ? | `PAR-017` | Produit | Décision à prendre | Juridique |
| Attention : paiement à la fin, dette client et coût plateforme sont trois faits différents. Aucun gain ne doit être inventé par un simple changement de statut de mission. | `PAR-018` | Produit | Constat à instruire | Produit |
| Bascule et doublon, PROD-031 — état connu : Nouvelle règle cible ; couverture actuelle à inspecter. | `PAR-018` | Produit | Constat à instruire | Produit |
| Ce filtre s'applique-t-il aussi aux courses programmées (UC-262), dont le solde au moment du déclenchement peut différer de celui constaté à la réservation ? | `PAR-018` | Produit | Décision à prendre | Produit |
| DiddiScore transmodules V1 — PROD-040 valide la phase et la portée. Définir signaux, effets, barèmes, durées, récupération, information et contestation avant implémentation ; aucun blocage automatique intermodules pour impayé au MVP. | `PAR-018` | Produit | Arbitrage produit ouvert | Produit |
| Food app/core/config.py:80 et app/modules/wallets/application/use_cases.py:293 : minimum restaurant 5 000 F par défaut et contrôle minimum. La nouvelle décision supprime ce minimum métier ; la configuration exige actuellement une valeur strictement positive. | `PAR-018` | Produit | Constat à instruire | Produit |
| Le traitement d'un client sans moyen numérique compatible, sans imposer une restitution physique par le professionnel ? | `PAR-018` | Produit | Arbitrage produit ouvert | Produit |
| Paiement en fin de service et dette, PROD-030 — état connu : Send exige encore paiement confirmé pour delivered. Contrat à aligner ; ne pas supposer un ticket existant couvrant l'ensemble. | `PAR-018` | Produit | Constat à instruire | Produit |
| Peut-il différer par ville ou par catégorie de véhicule ? | `PAR-018` | Produit | Fait à établir | Produit |
| Quel jour de la semaine les versements sont-ils exécutés ? | `PAR-018` | Produit | Décision à prendre | Administration |
| Qui supporte les frais de transfert d'un versement, la plateforme ou le pro ? | `PAR-018` | Produit | Décision à prendre | Administration |
| Remboursement cash numérique — PROD-042 valide le principe. Spécifier les canaux réellement disponibles, la vérification du bénéficiaire ? | `PAR-018` | Produit | Arbitrage produit ouvert | Produit |
| Retrait, PROD-032 — état connu : Minimum commercial encore présent dans la lecture Food ; SCRUM-484 à réconcilier. | `PAR-018` | Produit | Constat à instruire | Produit |
| SCRUM-484 prévoit encore refus sous 5 000 F et disponibilité des gains numériques après paiement confirmé et pickup. Le paiement à la fin décale la disponibilité effective des gains, sans permettre de créditer de l'argent non confirmé. | `PAR-018` | Produit | Constat à instruire | Produit |
| Send app/modules/delivery/application/delivery_service.py:420 : paiement cash collected ou numérique paid exigé avant transition delivered. L'issue « mission remise mais dette client » nécessite un contrat explicite séparant état métier et paiement. | `PAR-018` | Produit | Constat à instruire | Produit |
| Settings.driver_min_balance est un réglage global unique ? | `PAR-018` | Produit | Fait à établir | Produit |
| Un ajustement direct d'une ligne de grand livre du wallet pro (hors remboursement d'un paiement passager) doit-il exister comme action distincte, avec les mêmes garde-fous (motif, seuil, second approbateur) ? | `PAR-018` | Produit | Décision à prendre | Produit |
| Un montant minimum ou maximum de recharge est-il imposé, ou tout montant positif est-il accepté ? | `PAR-018` | Produit | Fait à établir | Produit |
| La part du partenaire est-elle prélevée sur la plateforme ou sur le pro ? | `PAR-019` | Produit | Décision à prendre | Administration |
| Le périmètre autorisé d'un véhicule est-il la zone de service, ou un périmètre propre au partenaire ? | `PAR-019` | Produit | Décision à prendre | Produit |
| Quelle distance maximale hors zone est acceptée avant refus ? | `PAR-019` | Produit | Décision à prendre | Produit |
| Quelle est la part du partenaire de flotte, et sur quelle assiette ? | `PAR-019` | Produit | Décision à prendre | Administration |
| Quelles pièces d'entreprise sont exigées d'un partenaire, et lesquelles bloquent l'activation ? | `PAR-019` | Produit | Décision à prendre | Juridique |
| Quelles pièces d'entreprise sont exigées, et lesquelles bloquent l'activation ? | `PAR-019` | Produit | Décision à prendre | Juridique |
| Quelles sont les plages horaires de majoration et leurs coefficients ? | `PAR-019` | Produit | Décision à prendre | Produit |
| Un partenaire peut-il créer son organisation lui-même, ou passe-t-il toujours par un administrateur ? | `PAR-019` | Produit | Décision à prendre | Produit |
| Un pro peut-il être rattaché à plusieurs partenaires, ou à un seul ? | `PAR-019` | Produit | Décision à prendre | Produit |
| Le sel d'empreinte des codes et le fournisseur d'envoi sont-ils surchargés en production ? | `PAR-001` | Technique | Fait à établir | Technique |
| Les durées et seuils configurés par défaut sont-ils les valeurs retenues ? | `PAR-001` | Technique | Fait à établir | Technique |
| Drivers/me — pour construire l'écran de suivi ? | `PAR-002` | Technique | Fait à établir | Technique |
| Existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | `PAR-002` | Technique | Décision à prendre | Technique |
| L'application fait-elle les deux appels — capabilities ? | `PAR-002` | Technique | Fait à établir | Technique |
| Laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | `PAR-002` | Technique | Fait à établir | Technique |
| Le format brut du motif de rejet, avec l'identifiant technique de l'administrateur, est-il celui affiché au chauffeur ? | `PAR-002` | Technique | Fait à établir | Technique |
| Les motifs de décision KYC sont-ils exposés au chauffeur ? `profile.kyc_review_notes` ? | `PAR-002` | Technique | Fait de code à établir | Technique |
| `vehicle.review_notes` sont persistés à l'approbation comme au rejet ? | `PAR-002` | Technique | Fait de code à établir | Technique |
| Quel service porte l'orchestration d'une demande d'export ou d'anonymisation ? | `PAR-004` | Technique | Fait à établir | Technique |
| Quel service porte l'orchestration de cette vérification croisée entre DiddiGo, DiddiSend et DiddiPay ? | `PAR-004` | Technique | Fait à établir | Technique |
| Quelle longueur retirer à chaque extrémité d'une trace GPS avant usage cartographique ? | `PAR-004` | Technique | Décision à prendre | Technique |
| Le format des traces correspond dans le code ? | `PAR-005` | Technique | Fait à établir | Technique |
| Quels critères définissent une position aberrante ? | `PAR-005` | Technique | Décision à prendre | Technique |
| Un test de bout en bout en staging reste à faire ? | `PAR-005` | Technique | Fait à établir | Technique |
| Est-il prévu de mutualiser l'envoi de notifications entre services ? | `PAR-007` | Technique | Fait à établir | Technique |
| Est-il prévu de mutualiser l'envoi de notifications entre services, ou chaque service reste-t-il autonome ? | `PAR-007` | Technique | Fait à établir | Technique |
| L'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position ? | `PAR-007` | Technique | Fait à établir | Technique |
| Le canal temps réel existant peut-il porter des messages, ou faut-il un mécanisme distinct ? | `PAR-007` | Technique | Fait à établir | Technique |
| Le numéro du chauffeur est-il transmis à tous les états de la course, ou seulement à partir du match ? | `PAR-007` | Technique | Fait à établir | Technique |
| Un appareil iPhone est-il enregistré avec un jeton FCM valide, ou l'application iOS n'enregistre-t-elle rien ? | `PAR-007` | Technique | Fait à établir | Technique |
| Un appareil iPhone est-il enregistré avec un jeton FCM valide, ou l'application iOS n'enregistre-t-elle rien du tout ? | `PAR-007` | Technique | Fait à établir | Technique |
| L'événement de position du canal temps réel porte-t-il l'horodatage de la mesure ou celui de la diffusion ? | `PAR-008` | Technique | Fait à établir | Technique |
| Quel écart maximal est toléré entre l'horloge du téléphone et celle du serveur ? | `PAR-008` | Technique | Décision à prendre | Technique |
| Ce contrôle doit-il s'exécuter à l'estimation, à la création, ou aux deux moments ? | `PAR-016` | Technique | Fait à établir | Technique |
| Deux appels successifs à l'estimation peuvent-ils renvoyer deux prix différents pour le même trajet ? | `PAR-016` | Technique | Fait à établir | Technique |
| Existe-t-il ailleurs une tâche de fond qui relance une course restée en requested sans offre ouverte ? | `PAR-016` | Technique | Fait à établir | Technique |
| L'application du chauffeur remonte-t-elle ses positions par le canal temps réel, par la route de lots, ou par les deux ? | `PAR-016` | Technique | Fait à établir | Technique |
| L'heure de demande est-elle enregistrée dans le même référentiel de temps que les autres horodatages du cycle ? | `PAR-016` | Technique | Fait à établir | Technique |
| L'horodatage porté par l'événement de changement d'état est-il celui de la transition ou celui de l'envoi ? | `PAR-016` | Technique | Fait à établir | Technique |
| L'événement de position diffusé par le canal temps réel porte-t-il l'horodatage de la mesure ou celui de la diffusion ? | `PAR-016` | Technique | Fait à établir | Technique |
| La relance sur expiration silencieuse doit-elle être une tâche planifiée périodique, ou une notification Redis (keyspace notification) déclenchée à l'expiration de la clé ? | `PAR-016` | Technique | Décision à prendre | Technique |
| Le canal WebSocket peut-il notifier simultanément plusieurs chauffeurs pour la même course sans changement de son modèle d'abonnement actuel ? | `PAR-016` | Technique | Fait à établir | Technique |
| Le profil transmis à DiddiMap correspond-il à un profil qu'il connaît, et est-il utilisé par son moteur d'itinéraire ? | `PAR-016` | Technique | Fait à établir | Technique |
| Les origines des deux sous-domaines publics sont-elles autorisées dans la configuration d'origines croisées ? | `PAR-016` | Technique | Fait à établir | Technique |
| Les origines du sous-domaine public sont-elles autorisées dans la configuration d'origines croisées de DiddiGo ? | `PAR-016` | Technique | Fait à établir | Technique |
| Quel critère départage deux candidats strictement à égalité de classement ? | `PAR-016` | Technique | Décision à prendre | Technique |
| La liste des motifs d'annulation est-elle filtrée selon que l'appelant est le passager ou le chauffeur ? | `PAR-017` | Technique | Fait à établir | Technique |
| Le chauffeur reçoit-il une notification push à l'annulation d'une course qu'il avait acceptée ? | `PAR-017` | Technique | Fait à établir | Technique |
| La commission estimée utilisée ici est-elle la même valeur que celle affichée au passager à l'estimation, ou un calcul distinct côté matching ? | `PAR-018` | Technique | Fait à établir | Technique |
| Le contrôle est-il figé au moment du calcul de l'offre, ou revérifié juste avant l'envoi ? | `PAR-018` | Technique | Décision à prendre | Technique |
| Le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | `PAR-018` | Technique | Fait à établir | Technique |
| Quels moyens mobile money sont réellement actifs en production, au-delà de ceux vus dans le code ? | `PAR-018` | Technique | Fait à établir | Technique |
| Existe-t-il dans DiddiSend un moyen de rattacher un coursier à un partenaire ? | `PAR-019` | Technique | Fait à établir | Technique |
| La commission de partenaire déclarée est-elle exploitée ailleurs que dans DiddiGo ? | `PAR-019` | Technique | Fait à établir | Technique |
| La couverture de DiddiMap désignent-elles le même périmètre ? | `PAR-019` | Technique | Fait à établir | Technique |
| La notion de ville de la grille tarifaire de DiddiGo ? | `PAR-019` | Technique | Fait à établir | Technique |
| Leur présence dans la charge utile de `GET /v1/drivers/me` reste à confirmer ? | `PAR-002` | Non fonctionnel | Fait de code à établir | Technique |
| Approuvez-vous la matrice de rôles Backoffice proposée ? | `PAR-003` | Non fonctionnel | Proposition à approuver | Produit |
| L'authentification renforcée avec interdiction de valider son propre remboursement ? | `PAR-003` | Non fonctionnel | Proposition à approuver | Produit |
| Organisation support — Calendrier et délais humains à organiser, sans astreinte opérationnelle dédiée selon la dernière décision. Distinguer reprise de ticket et urgence grave ; voir journal des cas particuliers. | `PAR-004` | Non fonctionnel | Arbitrage produit ouvert | Produit |
| Support et droits, PROD-017 / 037 — état connu : Briques existantes, chaîne complète non prouvée. | `PAR-004` | Non fonctionnel | Constat à instruire | Produit |
| Approuvez-vous la liste d'indicateurs MVP proposée par module, et l'exigence que chacun définisse son unité, sa période, sa source et la distinction zéro / indisponible ? | `PAR-008` | Non fonctionnel | Proposition à approuver | Produit |
| Approuvez-vous les objectifs d'exploitation proposés — charge, sauvegarde, restauration, astreinte, publication mobile — ou faut-il revoir la promesse ? | `PAR-008` | Non fonctionnel | Proposition à approuver | Direction |
| Le support est-il notifié d'une alerte d'urgence par un canal autre que la lecture des journaux ? | `PAR-016` | Non fonctionnel | Fait à établir | Technique |
| Un test de charge du canal WebSocket est-il planifié avant le lancement, avec quel outil ? | `PAR-016` | Non fonctionnel | Fait à établir | Technique |
| Une estimation produit-elle un événement de journal exploitable pour mesurer l'abandon entre estimation et commande ? | `PAR-016` | Non fonctionnel | Fait à établir | Technique |
| Le support est-il notifié d'une alerte par un canal extérieur à DiddiGo, ou personne n'est prévenu ? | `PAR-017` | Non fonctionnel | Fait à établir | Technique |
| Le support est-il notifié par un canal extérieur à DiddiGo, ou personne n'est prévenu ? | `PAR-017` | Non fonctionnel | Fait à établir | Technique |
| Peut-on savoir après coup si une alerte a été déclenchée par le passager ou par le chauffeur ? | `PAR-017` | Non fonctionnel | Fait à établir | Technique |
| Quelle preuve, le cas échéant, le chauffeur doit-il produire pour une annulation pour absence ? | `PAR-017` | Non fonctionnel | Décision à prendre | Juridique |
| Quelles qualifications un agent peut-il donner à une alerte ? | `PAR-017` | Non fonctionnel | Décision à prendre | Produit |
| Qui est joignable, et à quelles heures, pour prendre en charge une alerte ? | `PAR-017` | Non fonctionnel | Décision à prendre | Administration |
| Un second appel à la route d'alerte d'urgence est-il refusé explicitement, ou écrase-t-il le premier ? | `PAR-017` | Non fonctionnel | Fait de code à établir | Technique |
| Un second appel à la route d'alerte doit-il être refusé explicitement plutôt que d'écraser le premier ? | `PAR-017` | Non fonctionnel | Fait à établir | Technique |
| Un second appel à la route d'alerte doit-il être refusé plutôt que d'écraser le premier ? | `PAR-017` | Non fonctionnel | Fait à établir | Technique |
| Une alerte doit-elle changer quelque chose à la course elle-même ? | `PAR-017` | Non fonctionnel | Décision à prendre | Produit |
| Une alerte déclenchée hors course est-elle possible ? | `PAR-017` | Non fonctionnel | Décision à prendre | Produit |
| Une annulation pour absence avant le délai est-elle simplement refusée, ou traitée comme une annulation ordinaire ? | `PAR-017` | Non fonctionnel | Décision à prendre | Produit |
| Cash, PROD-033 — état connu : Comportement validé ; plafond et alerte configurables selon PARAMETRES_METIER.md. | `PAR-018` | Non fonctionnel | Constat à instruire | Produit |
| Le seuil de 30 000 F constaté dans le code est-il une valeur définitive validée par la direction, ou un réglage provisoire de développement ? | `PAR-018` | Non fonctionnel | Fait à établir | Direction |

# Sources

| Source | Date | Rôle |
| --- | --- | --- |
| `management/specs` — fiches de use case et de lot, sections « Questions ouvertes » | 14/09/2026 | les questions |
| `management/specs/etat/decisions-actees.md` | 14/09/2026 | les réponses déjà données, en trois statuts |
| `diddi-scope-document` — registre `PROD-xxx`, points à arbitrer, paramètres métier, journal des cas particuliers | 09/10/2026 | cible produit et points restés flous |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx` | 09/10/2026 | parcours, livrables, tickets, instantané Jira |
| `diddi-go/app_base/`, surface OpenAPI, `graphify-out/graph.json` | branche courante | état du code |
| Jira `diddifree` · Confluence espace `DIDDIFREE` | 09/10/2026, lecture seule | tickets et pages de lot |

Documents voisins : [`PARCOURS_MVP_DIDDIGO.md`](PARCOURS_MVP_DIDDIGO.md) pour la carte des parcours,
[`PARCOURS_MVP_COMPLEMENT_UC.md`](PARCOURS_MVP_COMPLEMENT_UC.md) pour les constats de code use case
par use case, [`PARAMETRES_CONFIGURABLES.md`](PARAMETRES_CONFIGURABLES.md) pour le registre des
valeurs.
