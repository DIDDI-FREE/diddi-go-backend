# Contrat WebSocket DiddiGo

Source : `app_base/modules/ride/presentation/websocket.py`. Ce contrat complete
l'OpenAPI, qui ne represente pas les messages WebSocket.

## Connexion

```text
wss://<hote-diddigo>/v1/ws?token=<access_token>
```

Le token doit etre un JWT d'acces, jamais un refresh token.

| Situation | Comportement serveur |
|---|---|
| Token absent, invalide ou refresh token | fermeture `4401` |
| Redis indisponible pour une operation dependante du cache | `CACHE_UNAVAILABLE`, fermeture `1013` |
| Evenement client inconnu | reponse `ignored`, socket conserve |

## Messages client vers serveur

Abonnement :

```json
{"event":"ride.subscribe","ride_id":"<uuid-course>"}
```

Position chauffeur :

```json
{
  "event":"driver.location_push",
  "location":{"lat":5.3601,"lng":-4.0090},
  "heading":134,
  "speed_kmh":22.5,
  "ride_id":"<uuid-course-optionnel>"
}
```

## Messages serveur vers client

| Evenement | Destinataire | Charge utile principale |
|---|---|---|
| `ride.status_changed` | abonnes de la course | `ride_id`, `status`, `at` |
| `ride.driver_location` | abonnes de la course | `ride_id`, `location`, `heading`, `at` |
| `ride.no_driver_found` | abonnes de la course | `ride_id` |
| `ride.new_request` | chauffeur cible | offre de course et expiration |
| `ride.waiting_changed` | abonnes de la course | etat et prix de l'attente |
| `ride.supplement_changed` | abonnes de la course | proposition ou decision |
| `ack` | socket emetteur | evenement confirme |
| `error` | socket emetteur | `code`, informations de reprise |

`ride.status_changed` est emis pour `arrived`, `in_progress`, `completed` et
les annulations. Un evenement est une notification, pas la source de verite.

## Regles frontend

1. Ouvrir le socket apres obtention d'un access token valide.
2. Apres reconnexion, relire la course REST puis refaire `ride.subscribe`.
3. Ignorer proprement les evenements futurs inconnus.
4. Ne pas afficher une position appartenant a une autre course.
5. Sur `4401`, renouveler la session ; sur `1013`, appliquer un backoff.
