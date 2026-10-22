# Compatibilité du contrat WebSocket

Cette page conserve l'ancien chemin documentaire utilisé par certains guides.

Le WebSocket public DiddiGo est disponible sur :

```text
GET /v1/ws?token=<access_token>
```

Un token invalide est refuse pendant le handshake HTTP, parfois sous forme de
`403` visible par le navigateur. Apres connexion, le client doit appliquer une
reconnexion avec temporisation et relire l'etat de la course par HTTP apres
toute interruption.

Le backend n'impose pas encore de heartbeat applicatif ni de replay. Le client
peut envoyer periodiquement `{"event":"ping"}` s'il souhaite detecter une
coupure, mais l'absence de reponse ne remplace pas une relecture REST. Apres
reconnexion : renouveler le token si besoin, rouvrir le socket, se reabonner,
puis appeler `GET /v1/rides/active/current` ou `GET /v1/rides/{ride_id}`.

Le frontend ne doit pas considérer le WebSocket comme une source de vérité durable : les événements accélèrent l'interface, tandis que les routes HTTP restaurent l'état courant.
