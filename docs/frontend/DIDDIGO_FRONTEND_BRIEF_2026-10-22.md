# Brief frontend DiddiGo - 22 octobre 2026

## Reprise de course

Au lancement ou apres une perte de connexion, appeler `GET /v1/rides/active/current`.
Un `200` restaure la course ; `404 ACTIVE_RIDE_NOT_FOUND` signifie qu'il faut
afficher l'accueil. Se reabonner ensuite au WebSocket de la course.

## Attente avant depart

Lire `arrival.free_seconds`, `arrival.price_per_minute_xof` et
`arrival.no_show_after_seconds` dans `GET /v1/rides/{ride_id}`. Ne jamais
coder les 180 secondes, 100 XOF ou 600 secondes en dur dans l'application.

## Paiement Mobile Money apres course

Un echec, une annulation ou une expiration Mobile Money ne cree pas de dette
et ne bloque pas une nouvelle course. Afficher l'echec, puis revenir au choix
de paiement de la meme course terminee :

1. le client choisit Mobile Money ou especes ;
2. pour Mobile Money, il choisit `orange`, `wave` ou `mtn` ;
3. envoyer un `Idempotency-Key` stable pour un meme clic et ses retries ;
4. utiliser `payment.next_action.url` lorsqu'elle est fournie ;
5. apres retour fournisseur, relire `GET /v1/payments/{ride_id}`.

Le choix especes attend ensuite la confirmation du chauffeur affecte. Les
routes `/v1/passenger/debts/*` sont historiques et ne doivent pas etre integrees
dans ce parcours MVP.

## Supplements et escales

Lire les supplements avec `GET /v1/rides/{ride_id}/supplements`. Afficher
uniquement les lignes `accepted` dans le total final. Une escale est une
modification d'itineraire, pas une attente automatiquement facturee.

## Vue metier locale

`GET /v1/pro/metiers` est disponible pour l'ecran DiddiGo Plus. Son champ
`scope=diddigo_local` est important : il ne contient pas les futurs metiers
DiddiSend ni les autres services. La future vue globale viendra de DiddiFree
Pro/DiddiFreeID.

## Erreurs et temps reel

Utiliser le catalogue d'erreurs de DiddiGo et le contrat WebSocket. Le socket
accelere l'interface ; REST reste la source de verite.

## Acces aux contrats publies

Une fois la stack documentaire staging deployee, lire les guides et les
changelogs sur `https://docs-go-staging.diddifree.com/`. Swagger et
`https://go-staging.diddifree.com/openapi.json` restent la reference des
routes et schemas effectivement deployes.
