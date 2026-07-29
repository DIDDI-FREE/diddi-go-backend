# Message pour les RH — état d'avancement DiddiGo

> À copier/coller (email ou Teams). Adaptez la formule d'appel et la signature.

---

Bonjour,

Voici un point d'avancement sur le backend de DiddiGo, l'application de VTC.

**Où nous en sommes**

Le cœur du service fonctionne de bout en bout. Concrètement, aujourd'hui :

- un passager peut créer un compte, se connecter par code SMS, voir le prix
  estimé de son trajet et commander une course ;
- l'application trouve automatiquement le chauffeur disponible le plus proche
  et lui propose la course ; s'il refuse ou ne répond pas dans les 15 secondes,
  elle passe au suivant ;
- un chauffeur peut s'inscrire, enregistrer son véhicule, se mettre en ligne,
  accepter ou refuser une demande, puis suivre le déroulé de la course jusqu'à
  son terme ;
- le passager suit son chauffeur en direct sur la carte et voit son nom, sa
  note et les détails du véhicule ;
- le paiement en espèces est enregistré en fin de course, et chacun peut noter
  l'autre.

Ce parcours complet a été testé, du premier écran d'inscription jusqu'au
paiement.

**Notre niveau de confiance**

Le code est couvert par **128 tests automatiques** qui s'exécutent à chaque
modification et vérifient l'ensemble des parcours. Ils tournent sur une vraie
base de données, pas sur une simulation — c'est ce qui nous permet de repérer
les problèmes avant qu'ils n'atteignent les utilisateurs.

Ces tests ont d'ailleurs déjà prouvé leur utilité : ils ont mis au jour
plusieurs anomalies sérieuses, dont une qui empêchait purement et simplement
un passager d'annuler sa course, et une autre qui rejetait certains
utilisateurs pourtant correctement connectés. Toutes ont été corrigées.

**Ce qui reste à faire**

Trois chantiers avant une mise en service réelle :

1. **L'envoi des SMS.** Les codes de connexion sont bien générés, mais pas
   encore envoyés par SMS — il faut souscrire à un service d'envoi et le
   raccorder. C'est une intégration courte, mais elle nécessite un prestataire
   et un budget.
2. **L'espace d'administration.** Il n'existe aujourd'hui aucun écran interne
   pour valider les dossiers des chauffeurs. En conséquence, tout chauffeur
   qui renseigne un numéro de permis est accepté automatiquement. C'est
   volontaire pour la phase de test, mais **cela doit impérativement être
   fermé avant l'ouverture au public**.
3. **Le paiement mobile.** Seul l'espèce est géré. Le paiement par mobile
   money a été anticipé dans la conception, mais reste à développer.

**La suite immédiate**

Les équipes mobile peuvent démarrer : un document de cadrage technique leur a
été remis, décrivant ce qui est disponible, ce qui ne l'est pas encore, et les
points d'attention. Elles ne sont pas bloquées par les trois chantiers
ci-dessus.

Quelques décisions produit restent à trancher de votre côté ou de celui du
métier — par exemple le délai au bout duquel on cesse de chercher un chauffeur,
ou l'existence de frais d'annulation. Je peux préparer une courte note sur ces
points si c'est utile.

Je reste disponible pour en discuter.

Bien cordialement,
[Votre nom]

---

## Notes d'usage (à ne pas envoyer)

**Ton retenu :** factuel, sans jargon. Aucune mention de FastAPI, Redis,
PostgreSQL, WebSocket, JWT — ces termes ne parlent pas aux RH et diluent le
message.

**Le point à ne pas retirer :** l'approbation automatique des chauffeurs
(point 2). C'est un risque de conformité, pas un détail technique. Il vaut
mieux qu'il soit écrit et daté, plutôt que découvert plus tard.

**Si on vous demande un délai :** le message n'en donne aucun volontairement,
car les trois chantiers dépendent de décisions externes (prestataire SMS,
priorité du back-office, partenaire mobile money). Si une date est exigée,
demandez d'abord ces arbitrages.

**Variante courte** — si vous préférez trois lignes en message instantané :

> Point DiddiGo : le parcours complet fonctionne côté serveur — inscription,
> commande, attribution automatique au chauffeur le plus proche, suivi en
> direct, paiement espèces et notation. 128 tests automatiques couvrent
> l'ensemble. Restent trois chantiers avant ouverture : l'envoi réel des SMS,
> l'espace de validation des chauffeurs (aujourd'hui ils sont approuvés
> automatiquement — à fermer avant le public), et le paiement mobile. Les
> équipes mobile peuvent démarrer, elles ont le cadrage.
