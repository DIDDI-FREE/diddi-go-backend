# Paiements et wallet chauffeur

DiddiGo possede le prix metier, les commissions et le grand livre chauffeur.
DiddiPay execute les paiements numeriques, remboursements et retraits.

- Cash : confirmation explicite de la course.
- DiddiPay/Wave : PaymentIntent, action utilisateur eventuelle, webhook puis
  reconciliation.
- Recharge : creation d'un top-up et suivi jusqu'au statut terminal.
- Retrait : destination beneficiaire obligatoire, puis suivi du payout.

Un top-up chauffeur n'est jamais un paiement de course. Les callbacks doivent
etre idempotents et une reprise ne doit pas crediter deux fois le wallet.
