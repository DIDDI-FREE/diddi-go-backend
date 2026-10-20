# Documentation DiddiGo

## Référence active

[`DIDDIGO-MVP-FIGE.md`](DIDDIGO-MVP-FIGE.md) est l'unique source de vérité produit du MVP DiddiGo. Elle porte le parcours de lancement, les décisions fermées et le découpage initial en epics.

Toute nouvelle epic, user story, ticket backend, frontend, mobile, DevOps ou QA doit la référencer.

## Archives

Les documents de cartographie produits avant le gel ont été conservés dans [`archive/2026-10-09-pre-gel`](archive/2026-10-09-pre-gel). Ils servent de preuves de l'état du code et de l'historique des arbitrages ; ils ne définissent plus le MVP actif.

## Recueils de questions DiddiSend et DiddiFood

Deux documents **de recueil**, pas de décision : ils rassemblent ce qui reste à trancher sur les
autres services avant le gel, avec le contexte, les tickets Jira à leur statut du 09/10, la page
Confluence et l'état du code relu dans chaque dépôt. Ils n'arbitrent rien et ne définissent aucun
périmètre ; les réponses, une fois prises, ont leur place dans la référence produit du service.

| Fichier | Contenu |
| --- | --- |
| [`DECISIONS_A_PRENDRE_MVP_DIDDISEND.md`](DECISIONS_A_PRENDRE_MVP_DIDDISEND.md) | **26 questions**, parcours `PAR-020` à `PAR-023`, sur 41 points relevés — 6 valeurs fermées, 9 hors des trois critères. Écarts relevés dans `diddi-send` : commission de 10 % codée en dur face aux 18 % du planning, plafond de dette cash à 25 000 F face aux 15 000 F de `BE019`, points relais et partenaires exposés alors que `PAR-023` les exclut du lancement. |
| [`DECISIONS_A_PRENDRE_MVP_DIDDIFOOD.md`](DECISIONS_A_PRENDRE_MVP_DIDDIFOOD.md) | **27 questions**, parcours `PAR-024` à `PAR-027`, sur 58 points relevés — 7 valeurs fermées, 24 hors des trois critères. Les 31 use cases Food sont classés `Later` au backlog du 14/09 alors que le planning du 09/10 les met au MVP : la divergence est portée en tête de document. Dans `diddi-food`, la commission de 15 % et le minimum de retrait de 5 000 F sont conformes, mais les frais de livraison et la commission Send valent 0 par défaut et la remontée des états de livraison est désactivée. |

## Règle de maintien

Une décision produit change d'abord dans `DIDDIGO-MVP-FIGE.md`, avec sa date. Les tickets sont ensuite créés ou mis à jour à partir de cette décision. Aucun nouveau registre parallèle de décisions ne doit être créé.
