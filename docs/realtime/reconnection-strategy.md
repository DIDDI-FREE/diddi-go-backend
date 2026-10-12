# Strategie de reconnexion temps reel

1. Reconnexion avec backoff progressif et jitter.
2. Relecture de la course active via HTTP.
3. Reprise de l'abonnement a la course.
4. Deduplication par type, `ride_id`, statut et horodatage.
5. Polling temporaire toutes les 15 secondes pendant l'approche si le socket
   est indisponible.

Le gestionnaire WebSocket actuel est local au processus. Une exploitation
multi-replicas exige un bus Redis pour diffuser les evenements entre instances.
