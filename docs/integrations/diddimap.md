# Integration DiddiMap

## Separation des fournisseurs

DiddiGo utilise deux ports distincts :

- `MapProvider` pour la recherche de lieux et les estimations d'itineraire ;
- `TraceProvider` pour le cycle GPS officiel d'une course.

`MAP_PROVIDER=diddimap` est actuellement la seule implementation active. Cette
configuration pourra evoluer vers un autre moteur de recherche ou de routage
sans modifier les use cases DiddiGo.

Les traces GPS ne suivent pas ce choix : elles restent directement gerees par
DiddiMap (`start`, `positions`, `finish`, `analyze`). Il n'existe aucun fallback
silencieux vers un autre fournisseur.

DiddiMap est l'unique fournisseur geographique : recherche, itineraire, ETA et
analyse de trace. Une indisponibilite produit une erreur explicite ; DiddiGo ne
fabrique pas de distance ou d'itineraire de secours silencieux.

DiddiGo collecte la trace de course puis la transmet a DiddiMap pour analyse.
Le prix facture au lancement reste le montant accepte au depart ; les mesures
reelles alimentent l'analyse et l'evolution du pricing.
