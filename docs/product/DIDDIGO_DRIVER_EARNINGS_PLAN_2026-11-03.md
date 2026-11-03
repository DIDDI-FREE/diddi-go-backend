# Plan d'implémentation - Historique de gains chauffeur

**Date :** 3 novembre 2026
**Statut :** implémenté et validé localement le 3 novembre 2026
**Périmètre :** DiddiGo uniquement

## Objectif

Fournir au chauffeur un tableau de bord de gains fiable par jour, semaine et
mois. Le ledger reste l'historique détaillé des écritures ; il ne devient pas
la source de calcul côté application mobile.

## Décisions figées

- Les périodes utilisent `Africa/Abidjan`.
- Les gains acquis comprennent uniquement les écritures de course confirmées.
- Les commissions sont affichées séparément des gains.
- Les retraits sont affichés séparément des gains.
- Le solde disponible vient du wallet, pas de la somme affichée dans un graphe.
- Une course en attente, échouée ou en litige ne devient pas un gain acquis.
- Les recharges ne sont jamais présentées comme un gain.

## Réponse livrée

La nouvelle lecture devra renvoyer des périodes bornées et explicites, avec au
minimum :

```json
{
  "timezone": "Africa/Abidjan",
  "period": "week",
  "from_date": "2026-11-02",
  "to_date": "2026-11-08",
  "currency": "XOF",
  "summary": {
    "ride_earnings_xof": 0,
    "platform_commissions_xof": 0,
    "withdrawals_succeeded_xof": 0,
    "available_balance_xof": 0,
    "pending_or_disputed_xof": 0
  },
  "buckets": []
}
```

Les dates sont inclusives en calendrier Abidjan. Aucun total ne doit être
inféré par Flutter à partir des pages de ledger.

## Sprint E1 - Contrat et lecture SQL - Terminé

1. Cartographier les écritures existantes : `ride_payout`,
   `platform_commission`, `withdrawal_succeeded`, recharge, ajustement et
   remboursement.
2. Définir précisément les statuts wallet admis dans chaque total. La valeur
   de référence pour un gain acquis est une écriture `confirmed`.
3. Ajouter une méthode de repository agrégée, groupée par jour local Abidjan.
   Elle doit filtrer par chauffeur et ne jamais scanner le ledger d'un autre
   chauffeur.
4. Ajouter les index SQL seulement s'ils sont nécessaires après inspection du
   plan de requête. Aucune nouvelle table n'est prévue par défaut.
5. Écrire le contrat OpenAPI et le guide MkDocs avant d'exposer la route.

**Sortie :** calcul SQL clairement défini, sans ambiguïté entre gain, retrait,
recharge et commission.

## Sprint E2 - API et application - Terminé

1. Exposer une route chauffeur protégée sous le wallet, avec période
   `day`, `week` ou `month` et une date d'ancrage documentée.
2. Obtenir le `driver_id` depuis le JWT, jamais depuis un identifiant choisi
   par l'application.
3. Retourner les totaux, les bornes de période et les buckets nécessaires au
   graphe.
4. Conserver `GET /v1/drivers/me/wallet/ledger` sans changement : il reste la
   vue détaillée et paginée.
5. Documenter la différence entre solde, gain de course, commission et
   retrait dans MkDocs et le brief frontend daté.

**Sortie :** une lecture légère et contractuelle pour le tableau de bord,
sans breaking change sur le ledger existant.

## Sprint E3 - Qualité et recette - Terminé localement

1. Tests unitaires : périodes, fuseau Abidjan, zéro écriture, frontière de
   jour et mois.
2. Tests d'intégration PostgreSQL : mélange de paiements cash et Mobile Money,
   commissions, recharges, retraits et écritures en attente.
3. Tests d'autorisation : un chauffeur ne lit jamais les gains d'un autre.
4. Test de cohérence : le solde disponible correspond au wallet et n'est pas
   confondu avec les gains de la période.
5. Recette staging avec un chauffeur de test et preuves non sensibles dans la
   checklist versionnée.

**Sortie :** données affichables par le frontend et vérifiables par Backoffice
sans recalcul client.

## Hors périmètre

- Tarification par zone.
- Carte de forte demande.
- Gestion autonome d'une flotte par un partenaire.
- Comptabilité et settlement PSP, qui restent la responsabilité de DiddiPay.
