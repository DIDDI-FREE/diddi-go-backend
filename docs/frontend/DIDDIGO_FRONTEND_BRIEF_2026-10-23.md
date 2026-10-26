# Brief frontend DiddiGo - 23 octobre 2026

## Objet

Ce brief complete les contrats precedents. Il decrit uniquement les ajouts de
ce lot ; `openapi.json` staging reste la reference des schemas deployes.

## Reprise de course selon le contexte

Utiliser `GET /v1/rides/active/current?as_role=passenger` dans l'application
passager et `?as_role=driver` dans DiddiGo Plus. Cette distinction est requise
pour une meme personne ayant une course passager et une course chauffeur.

Un `200` renvoie la ressource course complete. Un `404 ACTIVE_RIDE_NOT_FOUND`
signifie qu'il n'existe aucune course active dans le contexte demande.

## Paiement apres course

Dans `GET /v1/rides/{ride_id}`, utiliser `payment.ready=true` seulement comme
indicateur que la course terminee a un montant final payable. Le montant de
reference est `final_fare`. Le frontend continue de preparer un paiement
numerique par `POST /v1/payments/{ride_id}/prepare`, ou attend la confirmation
chauffeur pour les especes.

## Supplements

Avant d'afficher les choix chauffeur, lire :

```http
GET /v1/rides/config/supplements
```

Pour le type `other`, envoyer un montant autorise et un `custom_label` :

```json
{"type":"other","amount":800,"custom_label":"Frais d'acces residence"}
```

La reponse et `GET /v1/rides/{ride_id}/supplements` conservent le type et le
libelle. Ne pas coder les tarifs en dur.

## Retrait chauffeur confirme par OTP

Le chauffeur choisit sa destination Mobile Money, puis demande un code :

```http
POST /v1/drivers/me/wallet/withdrawals/verification/request
```

```json
{
  "beneficiary_destination": {
    "type": "mobile_money",
    "phone": "+2250700000000",
    "network": "wave"
  }
}
```

Le code est envoye au numero deja lie au profil du chauffeur, pas au numero
de destination. La reponse fournit `verification_id`, l'expiration et un
numero masque. L'ecran de saisie envoie ensuite :

```json
{
  "quote_id":"uuid",
  "beneficiary_reference":"driver:uuid",
  "beneficiary_destination":{"type":"mobile_money","phone":"+2250700000000","network":"wave"},
  "verification_id":"uuid",
  "verification_code":"123456"
}
```

La destination ne doit pas changer entre les deux appels. En cas d'expiration,
de mauvais code ou de limite atteinte, l'application revient a la demande de
code et applique le catalogue d'erreurs.

## Push chauffeur

Le backend emet deja le push FCM :

```json
{"event":"ride.new_request","ride_id":"uuid","expires_in_seconds":"15"}
```

L'application doit enregistrer le token FCM et, apres ouverture depuis le
push, restaurer sa session puis relire la course/offre. Le push ne contient
pas le prix ni les adresses completes.
