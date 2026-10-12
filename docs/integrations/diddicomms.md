# Integration DiddiComms

DiddiGo expose le resolver interne :

```http
GET /internal/v1/comms/tasks/ride/{ride_id}
```

DiddiComms utilise un Service Token DiddiFreeID avec l'audience `diddigo`, le
subject `service:diddicomms` et le scope `diddigo:comms-task:read`. DiddiGo
decide les participants et les droits de message/appel. DiddiComms ne connait
pas les tables metier DiddiGo.
