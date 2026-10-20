# 20 octobre 2026 - Scoring equitable

## Correction

- Les alertes SOS ne diminuent plus le score passager, chauffeur ou course.
  Les incidents restent conserves pour l'audit et le support.
- Les courses actives, `no_driver_found` et les annulations faites par l'autre
  participant ne sont plus utilisees dans le denominateur de fiabilite.
- Une note est maintenant refusee tant que la course n'est pas `completed`.
- Les notes historiques rattachees a une course non terminee restent en base
  mais ne comptent plus dans les moyennes.
- La contrainte PostgreSQL protege aussi les doublons de note concurrents.
- Un nouveau chauffeur affiche `rating_avg: null`, au lieu d'une fausse note
  `5.00`.
- Les reponses scoring et notation sont maintenant typees dans OpenAPI.

## Compatibilite

Les endpoints existants sont conserves. Les scores peuvent evoluer apres le
deploiement, car les populations et moyennes sont recalculees selon les regles
ci-dessus. Un nouvel utilisateur garde le score neutre `4.00` avec
`score_status=insufficient_data` et `score_level=new`.

## Validation

Les tests couvrent la formule, le SOS, la notation avant fin, les doublons et
les aggregations PostgreSQL reelles.
