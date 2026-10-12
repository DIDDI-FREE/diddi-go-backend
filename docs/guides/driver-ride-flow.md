# Parcours course chauffeur

```text
Profil valide + vehicule valide + solde suffisant -> en ligne
-> offre -> acceptation -> navigation pickup -> arrivee
-> code passager -> course -> fin -> paiement/gain
```

## Arrivee

Le chauffeur publie d'abord une position recente, puis appelle `/arrive`.
L'arrivee est refusee hors du rayon configure avec
`422 DRIVER_TOO_FAR_FROM_PICKUP`.

## Attente pendant la course

`POST /waiting/start` exige une course `in_progress`, une vitesse datant de
moins de 30 secondes et une vitesse inferieure ou egale a 3 km/h.

## Supplements

Le chauffeur choisit un type du catalogue. Il ne fixe pas librement le tarif,
sauf `other`, plafonne a 1 000 XOF. La proposition reste hors prix tant que le
passager ne l'a pas acceptee.

```http
POST /v1/rides/{ride_id}/supplements
```

```json
{"type":"toll"}
```

Pour `other`, le payload contient aussi `amount`. Le champ historique
`reason` reste accepte temporairement comme alias de `type`.
