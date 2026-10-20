# Scoring DiddiGo

Date : 2026-10-20
Statut : V1 disponible

## Objet

Le scoring DiddiGo est un indicateur explicatif de l'activite dans le module
DiddiGo. Il ne constitue pas une preuve de faute, ne declenche aucune
suspension automatique et ne modifie pas le moteur de priorite du matching.

Les plaintes sont traitees par DiddiSupport. Une alerte SOS reste tracee pour
la securite et l'audit, mais ne diminue jamais le score du passager, du
chauffeur ou de la course.

## Endpoints

| Action | Route | Acces |
| --- | --- | --- |
| Consulter ses scores | `GET /v1/me/scores` | utilisateur authentifie |
| Consulter le score d'une course | `GET /v1/rides/{ride_id}/score` | participant ou admin |
| Donner une note | `POST /v1/rides/{ride_id}/rating` | passager ou chauffeur de la course |

La notation utilise le corps suivant :

```json
{
  "rating": 5,
  "comment": "Trajet agreable"
}
```

`rating` est entier, de `1` a `5`. Le serveur derive le role de l'auteur et
ne l'accepte jamais du client.

Les reponses de ces trois routes sont typees dans `openapi.json` par
`MyScoresResponse`, `RideScoreResponse` et `RideRatingResponse`. Le frontend
doit consommer `metrics.eligible_rides` comme taille de l'echantillon utile,
et non deduire cette valeur de `total_rides` ou `rating_count`.

## Notation

Une note est acceptee seulement si :

- la course est `completed` ;
- l'auteur est le passager ou le chauffeur reellement affecte a cette course ;
- il n'existe pas deja une note de ce role pour cette course ;
- la valeur est comprise entre `1` et `5`.

Une note envoyee avant la fin retourne `409 RIDE_NOT_COMPLETED`. Une seconde
note du meme role retourne `409 RATING_ALREADY_SUBMITTED`, y compris lorsque
deux requetes arrivent simultanement : la contrainte est aussi appliquee par
PostgreSQL.

Les notes historiques deposees sur des courses non terminees sont conservees
pour l'audit, mais sont exclues des calculs.

## Population de fiabilite

`total_rides` est une statistique d'activite. Il ne sert pas de denominateur
au calcul. `eligible_rides` est le nombre de courses pertinentes pour le
score :

| Situation | Passager | Chauffeur |
| --- | --- | --- |
| Course `completed` | incluse | incluse |
| Course active | exclue | exclue |
| `no_driver_found` | exclue | exclue |
| `cancelled_by_passenger` | annulation passager incluse | exclue |
| `cancelled_by_driver` | exclue | annulation chauffeur incluse |

Ainsi, l'annulation de l'autre participant, une recherche sans chauffeur et
une course encore active ne degradent pas artificiellement la fiabilite.

## Formule V1

Pour une population eligible non vide :

```text
score =
  moyenne_des_notes_recues * 70 %
  + taux_de_courses_terminees * 5 * 20 %
  + (1 - taux_annulation_propre) * 5 * 10 %
```

Les deux taux sont calcules exclusivement sur `eligible_rides`. Le resultat
est borne entre `1.00` et `5.00`.

Pour un utilisateur sans note recue, la formule garde une valeur interne
neutre de `5.00` pour ce composant, mais l'API expose `rating_avg: null` :
aucune moyenne recue n'est inventee.

Pour un nouvel utilisateur sans activite, l'API retourne :

```json
{
  "score_value": 4.0,
  "score_level": "new",
  "score_status": "insufficient_data",
  "sample_size": 0,
  "metrics": {
    "rating_avg": null
  }
}
```

La valeur `4.00` est un point de depart neutre de compatibilite ; elle ne
signifie pas qu'une reputation de `4/5` a ete etablie. Le score devient
`stable` a partir de cinq courses eligibles. Les seuils de niveau restent :
`excellent` >= 4.70, `good` >= 4.20, `fair` >= 3.50, sinon `risk`.

## Donnees d'urgence

`metrics.emergency_reports` et `metrics.emergency_status` restent des donnees
descriptives pour le support et l'audit. Elles ne participent pas a la formule
et ne produisent aucun `reason_code` negatif.

## Profil public chauffeur

`driver.rating_avg` est la moyenne des notes passager valides de courses
terminees. Il vaut `null` tant que le chauffeur n'a pas recu de note valide ;
un nouveau chauffeur n'est donc plus presente comme note `5.00` par defaut.

## Limites

- Le score ne deduit pas la responsabilite d'un incident, d'un SOS ou d'un
  commentaire libre.
- Les exemptions d'annulation motivees par securite devront etre traitees par
  une future decision Support structuree.
- Le moteur de matching conserve son propre mecanisme de priorite chauffeur.
