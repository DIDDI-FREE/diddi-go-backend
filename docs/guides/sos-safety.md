# SOS et securite

Le SOS est persiste par DiddiGo et journalise pour le support.

Canaux contractuels MVP :

- WhatsApp via Evolution API ;
- SMS ;
- logs et support interne : toujours traces ;
- e-mail : canal additionnel optionnel lorsque SMTP est configure.

Le connecteur SMS n'est pas encore implemente dans DiddiGo. Tant qu'il manque,
la reponse doit le signaler comme `skipped` ou absent et le MVP SOS multicanal
ne peut pas etre declare complet.

Chaque livraison retourne `sent`, `failed` ou `skipped` avec son motif. Un
canal non configure ne doit jamais etre presente comme livre.
