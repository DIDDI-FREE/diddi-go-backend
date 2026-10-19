# Dette passager

Date : 2026-10-20
Statut : V1 disponible

## But

Eviter qu'un paiement Mobile Money definitivement echoue soit oublie, sans
bloquer l'acces au compte du passager. DiddiGo cree une dette uniquement pour
une course `completed` qui avait ete choisie en `mobile_money` et dont le
retour DiddiPay est `failed` ou `cancelled`.

Une course initialement cash ne cree jamais une dette automatique. Le serveur
ne peut pas determiner de facon fiable si les especes ont ete remises.

## Effet sur le parcours

```text
Course terminee + Mobile Money failed/expired
  -> dette open
  -> nouvelle demande de course refusee: 409 PASSENGER_DEBT_OUTSTANDING
  -> le passager consulte et regle sa dette
  -> dette settled
  -> nouvelles courses a nouveau autorisees
```

Le passager garde le droit de se connecter, de voir son historique et de voir
sa dette. La suppression globale du compte sera interrogee par DiddiFreeID dans
un lot ulterieur : elle n'est pas appelee par DiddiGo dans cette version.

## API passager

Toutes ces routes utilisent le JWT utilisateur. Le passager connecte est deduit
du token, jamais du corps de requete.

| Action | Route |
| --- | --- |
| Lister ses dettes | `GET /v1/passenger/debts?page=1&page_size=20` |
| Reprendre Mobile Money | `POST /v1/passenger/debts/{debt_id}/mobile-money/prepare` |
| Demander un reglement cash | `POST /v1/passenger/debts/{debt_id}/cash-request` |

Le corps de reprise Mobile Money suit `PaymentPreparationRequest` :

```json
{
  "method": "mobile_money",
  "mobile_money_network": "wave"
}
```

`mobile_money_network` vaut `orange`, `wave` ou `mtn`. L'email DiddiPay vient
du profil lorsque disponible ; sinon DiddiGo derive temporairement
`<telephone>@diddifree.com` pour ce paiement.

## Confirmation cash chauffeur

Le passager demande le cash. Seul le chauffeur affecte a la course d'origine
peut confirmer reception :

```text
POST /v1/passenger/debts/{debt_id}/confirm-cash
```

Cette route exige un profil chauffeur DiddiGo. Une confirmation hors course ou
une dette qui n'attend pas le cash est refusee et journalisee.

## Statuts de dette

| Statut | Signification |
| --- | --- |
| `open` | dette a regler ; reprise Mobile Money ou demande cash possible |
| `mobile_money_pending` | nouvelle tentative Mobile Money en cours |
| `cash_pending_confirmation` | le passager declare regler au chauffeur ; confirmation attendue |
| `settled` | dette reglee ; elle ne bloque plus de nouvelle course |

## Erreurs principales

| HTTP | Code | Traitement frontend |
| --- | --- | --- |
| 409 | `PASSENGER_DEBT_OUTSTANDING` | ouvrir l'ecran de regularisation avant toute nouvelle course |
| 404 | `PASSENGER_DEBT_NOT_FOUND` | rafraichir la liste ; ne pas deviner une dette |
| 409 | `PASSENGER_DEBT_SETTLEMENT_INVALID` | rafraichir la dette ; son statut a change |

## Audit et limites

- DiddiGo ne modifie ni le montant ni l'historique financier source de
  DiddiPay.
- Une dette couvre le montant final complet de la course, supplements acceptes
  inclus. Il n'existe pas de paiement partiel dans ce MVP.
- Les remboursements restent geres par DiddiPay et support ; ils ne sont pas
  une route publique de dette passager.
