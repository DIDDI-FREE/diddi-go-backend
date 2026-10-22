# SOS et securite

Le SOS est persiste par DiddiGo et journalise pour le support.

Canaux contractuels MVP :

- WhatsApp via Evolution API ;
- SMS ;
- logs et support interne : toujours traces ;
- e-mail : canal additionnel optionnel lorsque SMTP est configure.

Le connecteur SMS est implemente derriere le port `SmsProvider`. Configurer
`SMS_PROVIDER=senndo` ou `SMS_PROVIDER=yellika` avec les secrets et le sender
correspondants dans Portainer. Sans cette configuration, le canal SMS est
retourne comme `skipped` avec le motif `sms_provider_not_configured`.

L'implementation ne prouve pas a elle seule la livraison terrain : une recette
staging doit confirmer la reception WhatsApp et SMS par un vrai contact avant
de declarer le parcours SOS multicanal operationnel.

Chaque livraison retourne `sent`, `failed` ou `skipped` avec son motif. Un
canal non configure ne doit jamais etre presente comme livre.
