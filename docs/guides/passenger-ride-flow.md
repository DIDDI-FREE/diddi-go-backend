# Parcours course passager

```text
Recherche lieu -> estimation -> creation -> matching -> chauffeur assigne
-> approche -> arrivee -> verification code -> course -> paiement -> note
```

## Chauffeurs proches (C3, 13 novembre 2026)

Avant la commande, appeler avec le jeton utilisateur actif :

```http
GET /v1/drivers/nearby?lat=5.36&lng=-4.01&radius_km=5&limit=20&vehicle_category=standard&comfort_level=standard
Authorization: Bearer <access_token>
```

```json
{
  "drivers": [
    {"position": {"lat": 5.36, "lng": -4.008}, "vehicle_category": "standard", "comfort_level": "premium"}
  ],
  "radius_km": 5,
  "approximate": true
}
```

- `lat` et `lng` désignent le départ choisi. Latitude limitée à
  `[-85.05112878, 85.05112878]` (index GEO Redis), longitude à `[-180, 180]`.
- Rayon : strictement positif, maximum 10 km, défaut 5 km. Limite : 1 à 50,
  défaut 20. Catégorie exacte : `standard`, `comfort` ou `van`.
- Confort minimum : `standard`, `comfort` ou `premium`, défaut `standard`.
  Comme dans le matching, un niveau supérieur peut servir un niveau inférieur.
- Les marqueurs sont ordonnés par proximité géographique avant arrondi, sans ETA
  routier. Les coordonnées sont arrondies à trois décimales (environ 100 m).
  Aucune identité, plaque, photo, téléphone ou identifiant durable n'est exposé.
- Présence fraîche et disponibilité Redis requises (présence : 30 s par défaut),
  profil et véhicule validés, aucune course active, partenaire et solde éligibles.
  Les comptes de revue voient uniquement leur cohorte.
- C'est un aperçu borné, pas un inventaire exhaustif : au plus 100 candidats
  disponibles examinés, avec la fenêtre GEO bornée du service de localisation.
  `drivers: []` est une réponse normale, pas une panne ; une dépendance indisponible
  conserve une erreur HTTP et ne se transforme pas en liste vide.
- Remplacer les marqueurs à chaque rafraîchissement, par exemple toutes les 10 s
  lorsque la carte est visible ; arrêter le polling en arrière-plan. Les marqueurs
  peuvent se superposer après arrondi. Réponse `Cache-Control: no-store`.
- Aucun chauffeur n'est réservé ni sollicité par cette consultation. La commande
  garde son matching et revérifie la disponibilité. Aucun nouvel événement WS.
- Les paramètres invalides produisent `422 VALIDATION_ERROR`. Authentification et
  suspension de compte suivent les règles communes des routes utilisateur actives.

## Arrivee et attente pre-course


Quand le chauffeur appelle `POST /v1/rides/{ride_id}/arrive`, la course passe
a `arrived`. Le compteur appartient uniquement a cette arrivee :

- `0..180` secondes : gratuites ;
- au-dela : `100 XOF/minute`, calcule au prorata des secondes ;
- apres `600` secondes : le chauffeur peut declarer `passenger_no_show` ;
- les secondes gratuites inutilisees ne sont jamais reportees.

Le passager suit `ride.status_changed`, mais relit la course apres reconnexion.
La lecture `GET /v1/rides/{ride_id}` expose aussi dans `arrival` les valeurs
contractuelles `free_seconds`, `price_per_minute_xof` et
`no_show_after_seconds` : ne jamais les remplacer par des constantes Flutter.

## Reprise apres interruption

Au retour de l'application ou apres une coupure WebSocket :

1. appeler `GET /v1/rides/active/current` ;
2. si la route retourne 200, afficher cette course et se reabonner au socket ;
3. si elle retourne `404 ACTIVE_RIDE_NOT_FOUND`, revenir a l'ecran d'accueil ;
4. ne jamais deduire une course active depuis le cache seul.

## Supplements

Le chauffeur propose une ligne ; le passager la voit avant facturation et
l'accepte ou la conteste. Seules les lignes acceptees entrent dans le total.

```http
GET /v1/rides/{ride_id}/supplements
POST /v1/rides/{ride_id}/supplements/{supplement_id}/decision
```

```json
{"decision":"accepted"}
```

La valeur alternative est `disputed`. Rejouer la meme decision est
idempotent ; tenter de remplacer une decision terminale retourne
`409 SUPPLEMENT_ALREADY_DECIDED`.

| Type | Tarif |
|---|---:|
| `toll` | 500 XOF |
| `parking` | 200 XOF |
| `baggage_standard` | 500 XOF |
| `baggage_large` | 1 000 XOF |
| `other` | montant propose, maximum 1 000 XOF |

L'attente a `100 XOF/minute` est calculee par le backend et n'est pas une
ligne libre ajoutee par le chauffeur.

## Escales

Une escale est un waypoint qui modifie l'itineraire complet, et non une pause
facturee automatiquement. Le chauffeur peut actuellement ajouter le point via
`POST /v1/rides/{ride_id}/stops`. La tarification d'une escale doit donc venir
d'un nouveau devis ou d'un ajustement explicite valide par le passager ; elle
ne doit pas etre calculee comme une attente. Les horodatages operationnels par
escale ne sont pas encore exposes et ne doivent pas etre affiches comme acquis.

## Étude C13 : changer la destination pendant la course

**Statut au 13 novembre 2026 : faisable, proposition à valider, non implémentée.**
La fiche C13 vise une course en cours, pas seulement une modification avant
commande. Aucun endpoint de modification de destination n'est actuellement exposé.

### Contraintes vérifiées dans le code

- `RideService.create_quote` crée un devis, puis `request_ride` le consomme et copie
  destination, distance, durée et composantes tarifaires sur la course. Le devis
  d'origine doit rester une preuve ; il ne faut pas le modifier après consommation.
- La fin normale conserve le prix figé et ajoute attentes et suppléments acceptés.
  L'analyse GPS est distincte. Changer `dropoff` seul ne recalcule donc pas le prix.
- Une nouvelle estimation départ initial → nouvelle destination peut ignorer un
  détour déjà parcouru. Une estimation position actuelle → nouvelle destination
  seule oublierait la partie déjà effectuée. Il faut traiter ces deux segments.
- DiddiMap sait estimer un trajet et gérer une trace, mais le port `TraceProvider`
  ne fournit pas de changement de destination de trace. Il faut définir comment
  conserver la trace existante et ses références lors d'une révision de trajet.
- Le partage public, le détail, la reprise de course, l'historique, les montants
  chauffeur et le paiement doivent refléter la même révision appliquée.

### Parcours recommandé (règles proposées, non adoptées)

1. Le passager propriétaire demande une estimation de changement uniquement en
   `in_progress`, sans modifier la course. Refuser après fin/annulation ou pendant
   une confirmation d'arrêt anticipé concurrente.
2. Le backend conserve un instantané de la position chauffeur fraîche, du trajet
   déjà parcouru et de la nouvelle destination géocodée. Il calcule le trajet
   restant avec DiddiMap et affiche nouveau total et différence avec le prix actuel.
3. Le passager confirme ce devis ; le chauffeur affecté accepte ou refuse le
   changement. Tant que l'accord est incomplet ou expiré, destination et prix
   courants restent en vigueur. Refus/expiration doivent être visibles des deux côtés.
4. L'application du changement est atomique et idempotente, avec contrôle de la
   révision et de l'état de course pour empêcher deux changements ou une fin
   concurrente d'écraser le prix. Si le véhicule a trop avancé, refaire le devis.
5. Les deux applications sont notifiées après persistance, relisent la course et
   recalculent la navigation. Après reconnexion, le HTTP restitue la révision et
   toute demande encore en attente. Le partage suit la destination appliquée.

### Impact technique et recette nécessaire

| Zone | Changement à prévoir |
|---|---|
| Données | Migration : demandes/devis de changement, ancienne et nouvelle destination, prix, preuves d'accord, expiration, clé d'idempotence et révision de course. |
| API | Opérations de devis et décision, réponses typées et erreurs métier ; noms à définir au contrat, aucune route proposée ici n'est utilisable. |
| Prix | Séparer trajet effectué et restant, conserver les règles tarifaires convenues ; ne compter la prise en charge, les attentes et suppléments qu'une fois. Recalculer commission et part chauffeur. |
| Concurrence | Verrouillage transactionnel / contrôle de version partagé avec fin, annulation et arrêt anticipé ; conserver l'historique des changements. |
| DiddiMap | Géocodage, itinéraire restant et politique de trace continue ou segmentée ; absence de GPS fiable ou panne : aucun changement appliqué. |
| Temps réel / mobile | Nouveau signal de changement, écran ancien/nouveau prix, confirmation passager, décision chauffeur, navigation et reprise après déconnexion. |
| Paiement / historique | Utiliser le dernier prix accepté ; préserver devis initial, étapes de révision, distance prévue et distance mesurée comme valeurs distinctes. |
| Tests | Hausse/baisse de prix, refus, expiration, double clic, deux demandes concurrentes, fin concurrente, GPS périmé, panne DiddiMap, reconnexion et paiement du montant révisé. |

### Décisions produit à prendre avant implémentation C13

- Valider l'accord du chauffeur en plus de celui du passager (recommandé), et le
  comportement en cas de refus : poursuite du trajet actuel, sans annulation implicite.
- Choisir la formule du segment effectué et les tarifs conservés ; préciser la
  prise en compte d'une destination plus proche et des changements successifs.
- Fixer durée de validité du devis, fraîcheur GPS et seuil de déplacement imposant
  une nouvelle estimation. Ne pas inventer de valeur mobile indépendante du serveur.
- Définir l'interaction avec les escales et un arrêt anticipé. Recommandation :
  une seule demande de modification en attente par course.

C3 est indépendant de ces décisions et peut être livré en premier. C13 exige
un changement explicite de la règle de devis figé avant développement.
