# Journal d'implementation - Cohorte Google Play Review

**Date :** 2 novembre 2026  
**Fonctionnalite :** isolation des comptes Google Play Review dans DiddiGo.

## Objectif

Un passager de revue ne peut etre matche qu'avec un chauffeur de revue. Un
compte ou chauffeur normal ne peut jamais participer a une course de revue.

## Regle

`is_review_account` est une information signee par DiddiFreeID dans le JWT.
Elle est lue par DiddiGo mais jamais acceptee depuis le frontend.

```text
passager review -> chauffeurs review uniquement
passager normal -> chauffeurs normaux uniquement
```

## Etapes

- [x] Ajouter le marqueur aux projections locales utilisateur, chauffeur et course.
- [x] Propager le marqueur JWT DiddiFreeID vers l'utilisateur local.
- [x] Figer le marqueur lors de la creation d'une course.
- [x] Synchroniser le marqueur chauffeur a chaque mise en ligne.
- [x] Filtrer les chauffeurs incompatibles dans le matching et a l'acceptation.
- [x] Exclure les courses Review des agregats de courses Pilotage.
- [x] Identifier la cohorte dans les logs de matching et de mise en ligne.
- [x] Ajouter les tests de non-melange.
- [ ] DiddiPay : accepter le marqueur pour basculer vers un paiement simule.
- [ ] DiddiMap/Pilotage : exclure les traces et courses Review des donnees reelles.
- [ ] DiddiFreeID : emettre le claim JWT `is_review_account` pour les comptes autorises.

## Hors API publique

Le frontend n'envoie ni ne choisit ce marqueur. Les routes existantes restent
identiques. Cette information est reservee aux services et aux operations.
