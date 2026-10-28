# Paiements et wallet chauffeur

DiddiGo possède le prix métier, les commissions et le grand livre chauffeur.
DiddiPay exécute les paiements numériques, remboursements et retraits.

- Course cash : choix à la création puis confirmation par le chauffeur uniquement.
- Course Mobile Money : choix à la création, puis réseau `orange`, `wave`, `mtn` ou `moov`
  lors de la préparation. La préparation est autorisée uniquement après
  `status=completed` et après calcul du montant final. DiddiPay reste le
  fournisseur technique. L'acceptation par DiddiGo ne garantit pas que le
  réseau est activé chez DiddiPay dans un environnement donné.
- Course normale : devis figé + attentes + suppléments acceptés.
- Arrêt anticipé : tarif calculé depuis la trace GPS chauffeur réelle.

Une course terminée normalement et un arrêt anticipé confirmé ont tous deux
`status=completed`. Le champ `completion_reason` explique la fin, mais ne
change pas la règle de paiement.
- Recharge : creation d'un top-up et suivi jusqu'au statut terminal.
- Retrait : devis serveur, choix de la destination Mobile Money, puis OTP de
  confirmation envoye au numero lie au profil du chauffeur avant le payout.

## Confirmation de retrait

Le chauffeur peut choisir un numero Mobile Money de destination. Ce numero ne
remplace pas le numero connu de son compte : DiddiGo envoie le code de
confirmation au telephone du profil authentifie.

1. Demander `POST /v1/drivers/me/wallet/withdrawals/verification/request`
   avec `beneficiary_destination`.
2. Saisir le code recu au numero de profil.
3. Creer le retrait avec le meme `beneficiary_destination`, le
   `verification_id` et le `verification_code`.

La preuve expire apres cinq minutes, est liee a cette destination et ne peut
etre consommee qu'une fois. Un retry identique d'un retrait deja cree retourne
le retrait existant sans envoyer un second payout.

## Echec Mobile Money

La dette passager est differee : un retour DiddiPay `failed` ou `cancelled`
n'en cree plus automatiquement et ne bloque pas une nouvelle demande de
course. L'application affiche l'echec, puis ramene le passager au choix entre
Mobile Money et especes pour la meme course terminee.

Une nouvelle tentative Mobile Money remplace l'intention echouee sans recreer
la course. Le choix especes utilise ensuite la confirmation du chauffeur.
Les anciennes routes `/v1/passenger/debts/*` restent exposees pour les donnees
historiques, mais ne font pas partie du parcours MVP courant.

Un top-up chauffeur n'est jamais un paiement de course. Les callbacks doivent
etre idempotents et une reprise ne doit pas crediter deux fois le wallet.
