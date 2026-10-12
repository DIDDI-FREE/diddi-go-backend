# Statuts de reference

Parcours nominal :

```text
requested -> matching -> matched -> driver_en_route -> arrived
-> in_progress -> completed
```

Etats complementaires : `waiting`, `no_driver_found`,
`cancelled_by_passenger`, `cancelled_by_driver`, `cancelled_by_admin`.

`arrival.arrived_at` non nul implique normalement `status=arrived` ou un etat
ulterieur. Une contradiction doit etre traitee comme un defaut de coherence.
