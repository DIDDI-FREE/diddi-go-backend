# DiddiGo — cartographie Jira au regard du MVP figé

> Source de vérité produit : [`../product/DIDDIGO-MVP-FIGE.md`](../product/DIDDIGO-MVP-FIGE.md).
> État Jira lu et aligné le 10 octobre 2026 via Atlassian Rovo.

## 1. Constat

Jira est historiquement rangé par lots et cas d'usage : `SCRUM-64` (passager), `SCRUM-65` (chauffeur), `SCRUM-69` (DiddiFree Pro), `SCRUM-70` (argent des pros) et `SCRUM-5` (urgence). Cette structure couvre les fonctionnalités, mais ne matérialise pas les parcours de bout en bout W1 à W6. Les tickets récents `SCRUM-585` à `SCRUM-593` commencent à combler les écarts, sans encore respecter toutes les décisions du MVP figé.

Les six workflows de la page MVP deviennent donc les lignes de lecture de Jira. Les lots historiques restent des archives et des liens de traçabilité ; ils ne doivent plus piloter le contenu produit.

## 2. Cartographie par workflow

| Workflow MVP | Couverture Jira existante | État | Décision de triage |
|---|---|---|---|
| W1 — devis, création, matching | `SCRUM-212` estimation (terminé), `SCRUM-213` commande (terminé), `SCRUM-214` suivi (terminé), `SCRUM-221` aucun chauffeur, `SCRUM-592` devis persistant/expiration | `592` à faire ; `221` à faire | `SCRUM-592` est repéré par le label `mvp-w1`. Il conserve la référence à la création depuis `quote_id`, au TTL configurable et au prix initial figé. |
| W2 — arrivée, attente, démarrage, GPS, fin | `SCRUM-588`, `SCRUM-589`, `SCRUM-590`, `SCRUM-205` (attente en course, terminé), `SCRUM-438` (finalisation idempotente, terminé), `SCRUM-442` GPS client (terminé) | cadré, à livrer | `SCRUM-588` facture à la seconde après franchise, et l'annulation client absent est gratuite pour le passager mais le signale. `SCRUM-589` porte le code/QR obligatoire, sans prérequis GPS. |
| W3 — paiement et incident | `SCRUM-222` choix du paiement (terminé), `SCRUM-457` retour paiement contextualisé (à faire), `SCRUM-535` contrat plateforme de réclamations (à faire), `SCRUM-594` incident paiement (à faire) | cadré | `SCRUM-594` porte le fallback, l'incident/litige, la mise en attente du gain et la décision support. Il est relié à `457` et `535`. |
| W4 — gain et retrait | `SCRUM-91` recharge (terminé), `SCRUM-93` demande de payout (terminé), `SCRUM-104` minimum retrait (terminé), `SCRUM-105` suivi payout (terminé), `SCRUM-591` surface DiddiGo (à faire), `SCRUM-406` recette PSP (à tester) | cadré, à livrer | `SCRUM-591` est réécrit : minimum 2 000 XOF configurable, frais chauffeur, bénéficiaire PSP, idempotence, retry/réconciliation/escalade. |
| W5 — urgence | `SCRUM-6` notification SMS/WhatsApp (terminé), `SCRUM-7` événements répétés (à faire), `SCRUM-218` déclenchement (terminé) | cadré, à livrer | `SCRUM-7` conserve chaque événement support, limite les répétitions et notifie le contact une seule fois par course. |
| W6 — KYC/KYV, véhicule, mise en ligne | `SCRUM-184` KYC (terminé), `SCRUM-185` véhicule (terminé), `SCRUM-186` documents véhicule (terminé), `SCRUM-187` suivi validation (terminé), `SCRUM-188` en ligne (terminé), `SCRUM-204` quatre photos (terminé), `SCRUM-466` recette backoffice (à tester), `SCRUM-595` six photos (à faire) | cadré | `SCRUM-595` exige les six vues pour les nouvelles soumissions et conserve les anciens dossiers validés. Il est relié à `204` et `466`. |

## 3. Tickets de fondation et dépendances

| Sujet | Tickets | Décision |
|---|---|---|
| Configuration | `SCRUM-584`, `SCRUM-585`, `SCRUM-586`, `SCRUM-587` | Conserver `585` : paramètres tarifaires en environnement et figés sur la course. `586` doit choisir l'option 1 : pas de hot reload. `587` doit distinguer les valeurs globales d'environnement et la matrice tarifaire métier par ville/catégorie, versionnée et auditée ; cette dernière n'est pas une simple variable d'environnement. |
| GPS et DiddiMap | `SCRUM-436` à `SCRUM-440` terminés, `SCRUM-441` à faire, `SCRUM-536` à faire, `SCRUM-576` à faire, `SCRUM-596` confidentialité à faire | `SCRUM-596` limite le payload à `trace_id`, `source_service`, `source_ride_id` et points GPS, sans identifiant personnel. Il est relié à `441` et `576`. |
| DiddiFreeID / Backoffice | `SCRUM-466` à tester, `SCRUM-485` en revue, `SCRUM-510` à tester, `SCRUM-565` et `SCRUM-567` à faire, `SCRUM-568` / `569` à faire ou à tester | Ce sont des dépendances de recette et d'exploitation ; elles ne changent pas le périmètre MVP. Garder les recettes séparées des stories produit. |
| Pilotage et observabilité | `SCRUM-419` / `420` terminés, `SCRUM-422` V2, `SCRUM-593` à faire | `593` est utile à l'exploitation de lancement ; `422` reste V2. |

## 4. Backlog MVP proposé

Ordre de traitement après alignement Jira :

1. **MVP-P0 — W1/W2** : livrer `SCRUM-592`, `SCRUM-588`, `SCRUM-589`; conserver `SCRUM-590` si la règle de fin anticipée du produit est confirmée.
2. **MVP-P0 — W3** : livrer `SCRUM-594`, lié à `SCRUM-457` et `SCRUM-535`.
3. **MVP-P0 — W4** : livrer `SCRUM-591` et vérifier par recette `SCRUM-406`.
4. **MVP-P0 — W5** : livrer `SCRUM-7` et recetter `SCRUM-6` avec SMS, WhatsApp et support.
5. **MVP-P0 — W6** : livrer `SCRUM-595` et achever la recette `SCRUM-466`.
6. **MVP-P0 — intégration** : livrer `SCRUM-596`, finir `SCRUM-441` et `SCRUM-576`, puis faire la recette GPS réelle de `SCRUM-442`.
7. **MVP-P1 — opérations** : `SCRUM-585`, `SCRUM-586`, `SCRUM-587`, `SCRUM-593`.

## 5. Tickets à ne pas compter comme manquants du MVP

- `SCRUM-217`, `SCRUM-219`, `SCRUM-220`, `SCRUM-228` : V1.
- `SCRUM-229`, `SCRUM-230`, `SCRUM-422`, `SCRUM-537`, `SCRUM-557` : V2.
- `SCRUM-485` : migration Backoffice à terminer après les usages legacy, pas un chantier fonctionnel MVP.

## 6. Alignement Jira effectué

1. `SCRUM-588`, `SCRUM-589`, `SCRUM-591` et `SCRUM-7` ont été réécrits selon le MVP et portent respectivement les labels `mvp-w2`, `mvp-w2`, `mvp-w4` et `mvp-w5`.
2. `SCRUM-594` (paiement), `SCRUM-595` (KYV) et `SCRUM-596` (traces DiddiMap) ont été créés avec des critères d'acceptation E2E.
3. `SCRUM-592` porte le label `mvp-w1`. Les nouvelles stories sont reliées à leurs dépendances Jira : `594` ↔ `457`/`535`, `595` ↔ `204`/`466`, `596` ↔ `441`/`576`. Les dépendances opérationnelles sont également reliées : `7` ↔ `6`, `591` ↔ `93`/`105`/`406`.
