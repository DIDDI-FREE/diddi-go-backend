# DiddiGo — brief frontend

**Date :** 10 octobre 2026
**But :** intégrer le frontend et les applications mobiles sur le backend réellement disponible, tout en préparant le parcours MVP figé.

## Sources à utiliser

| Besoin | Référence |
|---|---|
| Routes REST, schémas, réponses | [OpenAPI](../api/openapi.json) et [contrat HTTP](../api/HTTP_API_CONTRACT.md) |
| Temps réel | [contrat WebSocket](../realtime/WEBSOCKET_CONTRACT.md) |
| Décisions de parcours MVP | [MVP figé](../product/DIDDIGO-MVP-FIGE.md) |
| Variables et environnements | [référence de configuration](../configuration/CONFIGURATION_REFERENCE.md) |

L'OpenAPI est la source de vérité pour toute route actuellement disponible. Ne pas implémenter une intégration à partir d'anciennes notes ou d'un screenshot.

## Règles d'intégration

- Les routes métier destinées au frontend sont principalement sous `/v1`. Les routes de retour de paiement et les routes internes font exception : toujours prendre le chemin exact dans l'OpenAPI.
- Pour une route protégée, envoyer `Authorization: Bearer <access_token>`.
- Piloter les erreurs par `code`, jamais par le texte français retourné.
- Après une mutation de course, rafraîchir l'état depuis l'API REST si le résultat UI dépend d'un calcul métier, paiement, matching ou état de course.
- Le WebSocket sert à accélérer l'affichage temps réel ; REST reste la source de resynchronisation après reconnexion.

## Parcours à construire sur le contrat actuel

Le frontend doit s'appuyer sur les tags OpenAPI : `auth`, `places`, `ride`, `driver`, `payment`, `driver-wallet`, `partners`, `devices` et leurs tags d'administration/interne lorsque l'application concernée y est autorisée.

Pour une course active :

1. charger la course via REST ;
2. ouvrir `wss://<hôte>/v1/ws?token=<access_token>` ;
3. envoyer `ride.subscribe` pour l'identifiant de course ;
4. afficher `ride.status_changed`, `ride.driver_location`, `ride.waiting_changed` et `ride.no_driver_found` ;
5. après une coupure, reconnecter avec backoff, relire la course puis se réabonner.

L'application chauffeur envoie `driver.location_push` avec latitude/longitude ; lorsqu'une course est affectée, elle ajoute `ride_id`. Les validations de rôle et d'affectation sont serveur : le client ne doit pas les reproduire comme une règle de sécurité.

## Parcours MVP disponibles dans cette version

### Devis et création de course

1. Appeler `POST /v1/rides/pricing/estimate` avec le trajet, la catégorie et le confort.
2. Conserver le `quote_id` et `expires_at` renvoyés.
3. Créer la course avec `POST /v1/rides` en envoyant le `quote_id`, le moyen de paiement et éventuellement `scheduled_at`.
4. Si le backend répond `QUOTE_EXPIRED`, recalculer un devis après confirmation du passager.
5. Ne jamais recalculer localement le prix et ne jamais réutiliser un devis consommé.

### Arrivée et démarrage sécurisé

1. Le chauffeur appelle `POST /v1/rides/{ride_id}/arrive` lorsqu'il est au point de prise en charge. Sa position temps réel doit déjà être publiée.
2. Le backend vérifie que le chauffeur affecté se trouve dans le rayon configuré, passe la course à `arrived` et démarre automatiquement l'attente pré-course. Ne pas appeler `/waiting/start` : cette route concerne uniquement une attente volontaire pendant une course déjà `in_progress`.
3. La réponse de `/arrive` fournit `waiting_started_at`, `free_seconds`, `no_show_after_seconds` et `price_per_minute_xof`. Utiliser ces valeurs serveur plutôt que coder `3 minutes`, `10 minutes` ou `100 XOF` en dur.
4. Le passager voit alors le code à six chiffres et le contenu QR dans `start_authorization` dans le détail de sa course. Le chauffeur ne doit jamais recevoir ni afficher ce code avant saisie/scan par le passager.
5. Le chauffeur appelle `POST /v1/rides/{ride_id}/start` avec le code.
6. Après cinq essais invalides par défaut, afficher le blocage support renvoyé par le backend.
7. Lorsque `no_show_after_seconds` est atteint, le chauffeur peut appeler `POST /v1/rides/{ride_id}/no-show`.

#### Fonctionnement de l'attente pré-course

Le fonctionnement MVP est le suivant :

```text
arrivée chauffeur
→ attente gratuite pendant free_seconds (180 secondes actuellement)
→ facturation proportionnelle à la seconde au tarif price_per_minute_xof
→ démarrage de la course : durée et frais calculés puis persistés par DiddiGo
```

- La réponse immédiate de `/arrive` utilise les champs plats `waiting_started_at`, `free_seconds`, `no_show_after_seconds` et `price_per_minute_xof`.
- `GET /v1/rides/{ride_id}` expose les données persistées sous `arrival.arrived_at`, `arrival.waiting_started_at`, `arrival.waiting_seconds` et `arrival.waiting_fee`.
- Pendant le statut `arrived`, l'application peut afficher un chronomètre visuel calculé depuis `arrival.waiting_started_at`. Ce chronomètre n'est pas une source financière et ne doit jamais produire le montant à facturer.
- Après `/start`, relire la course par REST. Le backend calcule `arrival.waiting_seconds` et `arrival.waiting_fee`, avec les secondes gratuites déduites, puis utilise ces valeurs dans la tarification finale.
- Un `no-show` autorisé après le délai annule la course sans facturer cette attente au passager : le backend enregistre alors `arrival.waiting_fee` à zéro.
- L'attente pendant la course reste un mécanisme séparé : `/waiting/start` et `/waiting/stop`, statut `waiting`, événement WebSocket `ride.waiting_changed` et facturation par minute commencée.

### KYV véhicule

Les créations et resoumissions de véhicule exigent désormais les six vues : avant, arrière, gauche, droite, intérieur et plaque. Utiliser les champs `*_file_id` publiés dans l'OpenAPI après confirmation DiddiFiles. Les anciens véhicules déjà validés restent compatibles.

### Wallet et retrait chauffeur

1. Charger `GET /v1/drivers/me/wallet`. Utiliser `available_balance` comme montant retirable, `reserved_balance` comme montant immobilisé par les retraits en cours et `total_balance` comme somme des deux. Le champ historique `balance` reste compatible et correspond au solde disponible.
2. Charger l'historique avec `GET /v1/drivers/me/wallet/withdrawals?page=1&page_size=20`. La réponse paginée contient `data`, `page`, `page_size` et `total`.
3. Avant toute confirmation, appeler `POST /v1/drivers/me/wallet/withdrawals/quote` avec `amount`. Le backend contrôle le minimum, le solde disponible et renvoie `quote_id`, `amount`, `fees`, `net_amount`, `currency` et `expires_at`.
4. Afficher au chauffeur le montant débité, les frais et le montant net. Le frontend ne recalcule aucune de ces valeurs.
5. Confirmer avec `POST /v1/drivers/me/wallet/withdrawals` en envoyant `quote_id` et `beneficiary_reference`. Désactiver le bouton pendant la requête ; une répétition réseau du même devis reste idempotente côté backend.
6. Suivre le résultat avec `GET /v1/drivers/me/wallet/withdrawals/{withdrawal_id}` et rafraîchir le wallet.

Statuts à afficher :

| Statut | Comportement frontend |
|---|---|
| `reserved` | Le montant est réservé localement ; afficher un traitement en cours. |
| `processing` | DiddiPay traite le payout ; conserver le suivi et permettre un rafraîchissement. |
| `succeeded` | Le retrait est confirmé. Ne jamais déduire une seconde fois le wallet côté client. |
| `released` | Le payout a échoué ou a été rejeté ; DiddiGo a restitué le montant disponible. Afficher `failure_code`/`failure_message` lorsqu'ils existent. |

Le montant minimum et les frais sont configurés côté backend. La `beneficiary_reference` doit respecter le format accepté par DiddiPay ; ne pas annoncer un canal de payout, notamment Wave, tant qu'il n'est pas confirmé par le contrat DiddiPay déployé.

## Fonction encore dépendante d'un contrat externe

Le traitement complet d'un impayé numérique et de son litige reste dépendant du contrat correspondant. Le frontend ne doit inventer ni endpoint ni statut absent de l'OpenAPI DiddiGo.

## Définition de prêt frontend

- Les requêtes REST sont typées à partir de l'OpenAPI publié.
- Les écrans d'erreur affichent une action compréhensible et conservent le `code` pour le support.
- Les données de position et de course sont effacées de l'état local à la fin de session.
- Les cas de reconnexion WebSocket, token expiré et cache indisponible sont couverts par des tests frontend.
- Les features MVP non encore exposées restent derrière une capacité/feature flag frontend, sans endpoint fictif.
