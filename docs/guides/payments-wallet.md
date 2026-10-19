# Paiements et wallet chauffeur

DiddiGo possède le prix métier, les commissions et le grand livre chauffeur.
DiddiPay exécute les paiements numériques, remboursements et retraits.

- Course cash : choix à la création puis confirmation par le chauffeur uniquement.
- Course Mobile Money : choix à la création, puis réseau `orange`, `wave` ou `mtn`
  lors de la préparation. DiddiPay reste le fournisseur technique.
- Course normale : devis figé + attentes + suppléments acceptés.
- Arrêt anticipé : tarif calculé depuis la trace GPS chauffeur réelle.
- Recharge : creation d'un top-up et suivi jusqu'au statut terminal.
- Retrait : destination beneficiaire obligatoire, puis suivi du payout.

## Dette passager

Une dette est creee uniquement lorsqu'une course terminee, initialement choisie
en `mobile_money`, recoit un statut DiddiPay terminal `failed` ou `cancelled`.
Une course cash ne cree jamais automatiquement de dette : DiddiGo ne peut pas
prouver qu'un echange d'especes n'a pas eu lieu.

La dette bloque une nouvelle demande de course, mais pas la connexion,
l'historique ni l'ecran de regularisation. Le passager peut relancer Mobile
Money ou demander un reglement cash confirme ensuite par le chauffeur affecte
a la course. DiddiPay reste la source de verite pour les tentatives, paiements
et remboursements ; DiddiGo garde le statut d'eligibilite metier.

Un top-up chauffeur n'est jamais un paiement de course. Les callbacks doivent
etre idempotents et une reprise ne doit pas crediter deux fois le wallet.
