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

Un top-up chauffeur n'est jamais un paiement de course. Les callbacks doivent
etre idempotents et une reprise ne doit pas crediter deux fois le wallet.
