# Dette passager - flux differe

Date : 2026-10-22
Statut : hors MVP courant

Le mecanisme de dette passager a ete isole pour une decision produit ulterieure.
Un paiement Mobile Money `failed` ou `cancelled` ne cree plus de dette
automatique et ne bloque plus les nouvelles demandes de course.

## Parcours MVP actuel

```text
Course terminee
  -> tentative Mobile Money echoue, expire ou est annulee
  -> l'application affiche l'echec
  -> le passager revient au choix Mobile Money ou especes
  -> nouvelle intention Mobile Money ou confirmation cash chauffeur
```

La nouvelle tentative Mobile Money s'effectue sur la meme course terminee via
`POST /v1/payments/{ride_id}/prepare`. Une tentative precedente reste dans
l'historique DiddiPay ; elle n'est pas masquee ni consideree comme payee.

## Routes historiques

Les routes `/v1/passenger/debts/*` sont conservees pour les donnees deja
enregistrees et leur migration future. Elles ne doivent pas etre integrees dans
les applications passager ou chauffeur pour le MVP actuel.
