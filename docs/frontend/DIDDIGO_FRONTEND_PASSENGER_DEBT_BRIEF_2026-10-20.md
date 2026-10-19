# DiddiGo - Brief frontend dette passager

Date : 2026-10-20
Version : V1

## Quand afficher cet ecran

Quand `POST /v1/rides` repond `409 PASSENGER_DEBT_OUTSTANDING`, ne pas afficher
une erreur generique. Ouvrir l'ecran de regularisation, puis appeler :

```text
GET /v1/passenger/debts
```

Le blocage ne concerne que les nouvelles courses. L'utilisateur conserve son
login, l'historique et l'acces a sa dette.

## Parcours Mobile Money

1. Afficher le montant complet et le motif de la dette.
2. L'utilisateur choisit `orange`, `wave` ou `mtn`.
3. Appeler `POST /v1/passenger/debts/{debt_id}/mobile-money/prepare`.
4. Executer `payment.next_action` avec le meme composant que les paiements de
   course normaux.
5. A la reprise de l'application ou au retour checkout, recharger
   `GET /v1/passenger/debts` ; ne pas considerer le paiement reussi seulement
   parce que le navigateur est revenu.

## Parcours especes

1. Le passager appuie sur « Je regle en especes au chauffeur ».
2. Appeler `POST /v1/passenger/debts/{debt_id}/cash-request`.
3. Afficher `cash_pending_confirmation` comme attente de confirmation, pas
   comme paiement deja confirme.
4. Seul le chauffeur de la course d'origine peut confirmer. Le passager ne
   dispose d'aucun bouton de confirmation finale.

## A ne pas faire

- ne pas permettre de paiement partiel ; le montant est celui de la dette ;
- ne pas proposer de dette apres une course initialement cash ;
- ne pas laisser l'utilisateur recréer une course tant qu'une dette non
  `settled` est retournee ;
- ne jamais transmettre `passenger_user_id` ni `driver_id` dans les corps de
  requete : ils viennent des tokens et de la course serveur.

## Vehicule

Les formulaires de creation et de correction vehicule doivent maintenant
obligatoirement collecter `make` et `model`. `color` reste optionnel.
