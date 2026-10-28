# DiddiGo - Clarifications frontend

Date : 2026-10-28  
Version : V1 - clarifications de contrat

Ce brief complete les briefs dates precedents. Il prime sur leurs passages
contradictoires pour les sujets ci-dessous. Les schemas deployes restent dans
`/openapi.json`; le portail MkDocs publie la copie versionnee dans ce depot.

## Mobile Money

Au moment de payer une course terminee, le passager envoie :

```json
{
  "method": "mobile_money",
  "mobile_money_network": "moov"
}
```

Les valeurs techniquement acceptees par DiddiGo sont `orange`, `wave`, `mtn`
et `moov`. Le frontend doit afficher seulement les reseaux confirmes actifs
par la configuration DiddiPay de l'environnement. L'acceptation de la valeur
par DiddiGo ne prouve pas qu'un reseau est activable en staging ou production.

En cas d'echec, d'annulation ou d'expiration, ne pas creer une nouvelle course
ni une dette automatique. Afficher l'echec, revenir au choix `mobile_money` ou
`cash` pour la meme course `completed`, puis appeler a nouveau la preparation
du paiement si le passager choisit le numerique.

## KYV vehicule

Le vehicule doit etre `active` et avoir `verification_status=active` avant que
le chauffeur puisse passer en ligne.

- Vehicule suspendu mais encore actif : le serveur retourne
  `403 VEHICLE_NOT_VERIFIED`.
- Vehicule desactive : le serveur retourne `409 NO_ACTIVE_VEHICLE`.
- Les valeurs et motifs affiches doivent venir de `GET /v1/me/capabilities`
  et de `GET /v1/drivers/me`, en particulier `blocking_reasons` et
  `document_reviews`.

L'autorisation de transport est facultative. Si elle seule est refusee, son
motif reste visible piece par piece, mais elle ne retire pas a elle seule la
validation d'un vehicule dont les pieces KYV obligatoires sont correctes.

## Lectures de reprise et OpenAPI

Les trois lectures suivantes sont maintenant typees dans OpenAPI :

```text
GET /v1/rides/{ride_id}
GET /v1/rides/active/current?as_role=passenger|driver
GET /v1/pro/metiers
```

`GET /v1/rides/{ride_id}` et la reprise active renvoient le meme modele de
course. Utiliser `payment.ready=true` seulement pour savoir que le montant
final est disponible a la preparation du paiement; ce n'est pas une preuve de
paiement reussi.

`GET /v1/pro/metiers` est une projection **DiddiGo locale**. Il n'agrege pas
DiddiSend, DiddiPay ou d'autres metiers; la vue globale appartient a la future
couche DiddiFree Pro/DiddiFreeID.

## Partage de course

La page publique utilise le token retourne par `POST /v1/rides/{ride_id}/share-link`
puis appelle `GET /v1/rides/shared/{token}`. L'autorisation CORS de son domaine
web est une configuration d'environnement DiddiGo, distincte du token de
partage. Ne jamais mettre ce token dans des logs, analytics ou captures.
