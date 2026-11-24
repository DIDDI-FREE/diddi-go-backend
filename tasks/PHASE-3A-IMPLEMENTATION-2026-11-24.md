# Journal P3-A — Chemin de réconciliation

- État : TERMINÉ
- Constat : les appels HTTP directs de confirmation/correction restent non bloquants ; l’outbox publie les faits indépendamment.
- Décision : ne pas ajouter un second worker HTTP concurrent.
