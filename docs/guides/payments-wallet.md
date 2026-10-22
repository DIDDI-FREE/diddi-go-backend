# Paiements et wallet chauffeur

DiddiGo possède le prix métier, les commissions et le grand livre chauffeur.
DiddiPay exécute les paiements numériques, remboursements et retraits.

- Course cash : choix à la création puis confirmation par le chauffeur uniquement.
- Course Mobile Money : choix à la création, puis réseau `orange`, `wave` ou `mtn`
  lors de la préparation. La préparation est autorisée uniquement après
  `status=completed` et après calcul du montant final. DiddiPay reste le
  fournisseur technique.
- Course normale : devis figé + attentes + suppléments acceptés.
- Arrêt anticipé : tarif calculé depuis la trace GPS chauffeur réelle.

Une course terminée normalement et un arrêt anticipé confirmé ont tous deux
`status=completed`. Le champ `completion_reason` explique la fin, mais ne
change pas la règle de paiement.
- Recharge : creation d'un top-up et suivi jusqu'au statut terminal.
- Retrait : destination beneficiaire obligatoire, puis suivi du payout.

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
