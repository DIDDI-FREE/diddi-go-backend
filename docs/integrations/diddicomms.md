# Integration DiddiComms

DiddiGo expose le resolver interne :

```http
GET /internal/v1/comms/tasks/ride/{ride_id}
```

DiddiComms utilise un Service Token DiddiFreeID avec l'audience `diddigo`, le
subject `service:diddicomms` et le scope `diddigo:comms-task:read`. DiddiGo
decide les participants et les droits de message/appel. DiddiComms ne connait
pas les tables metier DiddiGo.

`phone_e164` est fourni uniquement à DiddiComms pour lancer une tentative
d'appel. Il ne doit jamais être exposé au frontend, à DiddiSupport ou aux logs.
DiddiComms reste propriétaire de l'enregistrement et de l'audit des tentatives
d'appel.

Pour une course terminée, les appels sont toujours fermés. Le chat reste ouvert
jusqu'à `closes_at`, calculé avec la variable d'environnement
`RIDE_COMMS_COMPLETED_CHAT_RETENTION_SECONDS`.
