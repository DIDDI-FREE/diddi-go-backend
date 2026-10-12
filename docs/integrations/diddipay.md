# Integration DiddiPay

DiddiGo demande un Service Token DiddiFreeID pour l'audience `diddipay`, puis
appelle les routes de PaymentIntent, top-up et payout. Le mecanisme legacy
peut coexister pendant la migration mais ne constitue pas la cible.

DiddiGo conserve les references metier et le ledger ; DiddiPay reste source de
verite pour l'execution processeur, les frais, settlements et payouts.
