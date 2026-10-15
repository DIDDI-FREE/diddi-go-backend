# Compatibilité du contrat WebSocket

Cette page conserve l'ancien chemin documentaire utilisé par certains guides.

Le WebSocket public DiddiGo est disponible sur :

```text
GET /v1/ws?token=<access_token>
```

Un token invalide est refusé pendant le handshake HTTP. Après connexion, le client doit appliquer une reconnexion avec temporisation et relire l'état de la course par HTTP après toute interruption.

Le frontend ne doit pas considérer le WebSocket comme une source de vérité durable : les événements accélèrent l'interface, tandis que les routes HTTP restaurent l'état courant.
