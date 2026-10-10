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
2. Le passager voit alors le code à six chiffres et le contenu QR dans le détail de sa course. Le chauffeur ne doit jamais recevoir ni afficher ce code avant saisie/scan par le passager.
3. Le chauffeur appelle `POST /v1/rides/{ride_id}/start` avec le code.
4. Après cinq essais invalides par défaut, afficher le blocage support renvoyé par le backend.
5. Après dix minutes sans passager, le chauffeur peut appeler `POST /v1/rides/{ride_id}/no-show`.

L'attente pré-course est calculée et persistée par le backend. Le frontend affiche `pre_ride_wait_seconds` et `pre_ride_wait_fee`, sans chronomètre financier autonome.

### KYV véhicule

Les créations et resoumissions de véhicule exigent désormais les six vues : avant, arrière, gauche, droite, intérieur et plaque. Utiliser les champs `*_file_id` publiés dans l'OpenAPI après confirmation DiddiFiles. Les anciens véhicules déjà validés restent compatibles.

## Fonctions encore dépendantes d'un contrat externe

Le retrait chauffeur et le traitement complet d'un impayé numérique restent désactivés tant que le contrat `Payout` et le contrat de litige ne sont pas disponibles dans l'OpenAPI DiddiGo. Le frontend ne doit inventer ni endpoint ni statut pour ces deux fonctions.

## Définition de prêt frontend

- Les requêtes REST sont typées à partir de l'OpenAPI publié.
- Les écrans d'erreur affichent une action compréhensible et conservent le `code` pour le support.
- Les données de position et de course sont effacées de l'état local à la fin de session.
- Les cas de reconnexion WebSocket, token expiré et cache indisponible sont couverts par des tests frontend.
- Les features MVP non encore exposées restent derrière une capacité/feature flag frontend, sans endpoint fictif.
