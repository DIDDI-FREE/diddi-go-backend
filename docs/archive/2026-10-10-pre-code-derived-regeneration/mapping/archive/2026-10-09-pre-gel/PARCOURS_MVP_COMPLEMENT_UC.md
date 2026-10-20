# Use cases MVP du périmètre DiddiGo — constats de code au 9 octobre 2026

Relevé du 9 octobre 2026, branche `feat/pilotage-finance-summary-v1`. Complément de
[`PARCOURS_MVP_DIDDIGO.md`](PARCOURS_MVP_DIDDIGO.md).

## À quoi sert ce document

Il part du corpus `management/specs` — 361 use cases — isole les **109 qui relèvent du périmètre
DiddiGo au statut MVP** sur l'axe Back/Infra, et porte pour chacun un **constat de code relevé
aujourd'hui**, pas repris d'une passe antérieure.

Il indique aussi, pour chaque use case, si un **ticket cité par le planning** le porte. C'est une
liste de rattachements, pas de manques : un use case peut être couvert par un ticket que le planning
ne cite pas, ou par un parcours sans passer par un ticket. La liaison `UC-xxx` ↔ `PAR-xxx` reste une
décision à prendre.

## Méthode du constat de code

Le graphe `graphify-out/graph.json` sert à **localiser**, la lecture du fichier à **confirmer** —
jamais l'inverse. Un nœud dans le graphe établit qu'un symbole existe, pas qu'un comportement est
réalisé. Chaque constat porte un `fichier:ligne` ou une route de la surface OpenAPI générée.

La colonne « Constaté dans le code » du corpus, datée du 14 septembre, **n'est pas reprise** : elle
précède les commits sur le moteur de dispatch, l'attente de course, les escales, les suppléments et
les résumés Pilotage, et elle marquait « Absent » des comportements que le code porte aujourd'hui.

### Étiquettes

Elles décrivent **le code seul**. Elles ne disent rien de la conformité à une cible.

| Étiquette | Sens |
| --- | --- |
| **Présent** | le code réalise ce que le use case décrit |
| **Partiel** | une partie est réalisée, le reste est nommé |
| **Absent du code** | rien de correspondant dans `diddi-go` |
| **Hors diddi-go** | le backend appartient à un autre module, code non lu |
| **À vérifier** | présent, mais un point reste à établir par lecture plus fine ou en staging |

Le triplet `UX/Front/Back` vient du classeur et n'a pas été touché. Le corpus précise que le dépôt du
frontend mobile n'est accessible dans aucun environnement : **aucun statut UX ou Front n'est
vérifiable** ici.

## Décompte des constats

| Étiquette | Nombre |
| --- | --- |
| Présent | 52 |
| Partiel | 17 |
| Absent du code | 13 |
| À vérifier | 5 |
| Hors diddi-go | 22 |
| **Total** | **109** |

Pour mémoire, les mêmes 109 use cases au 14 septembre : 33 « Conforme au back », 41 « Partiel »,
26 « Absent », 9 formulations nuancées. L'écart de décompte **mesure l'avancement du code entre les
deux dates**, il ne corrige pas une erreur du corpus.

## DiddiGo / Passager

13 use cases MVP, dont 13 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-009 | Le passager estime le prix d'une course | `P/P/C` | **Présent** | `POST /v1/rides/pricing/estimate` → estimation DiddiMap, barème lu en base sinon défauts de code, décomposition renvoyée (`ride/application/services.py:84-114`). Réponse non persistée : pas d'identifiant de devis ni de date de validité. | `SCRUM-212` Terminé(e) ○ |
| UC-010 | Le passager commande une course | `P/P/C` | **Présent** | `POST /v1/rides` crée la course en `requested` et fige barème, taux de commission et niveau de confort sur la course (`services.py:116-181`, gel ligne 160). | `SCRUM-213` Terminé(e) ○ |
| UC-011 | Le passager suit l'etat de sa course | `P/P/C` | **Présent** | `GET /v1/rides/{id}` et `GET /v1/rides` ; événement WebSocket `ride.status_changed` (`ride/presentation/websocket.py:137`). | `SCRUM-214` Terminé(e) ○ |
| UC-012 | Le passager voit la position du chauffeur | `P/P/P` | **Partiel** | Événement WebSocket `ride.driver_location` (`websocket.py:146`) et poussée `driver.location_push` (ligne 315). La charge utile ne porte pas d'horodatage de fraîcheur ; `last_location_at` n'existe que sur le lien de suivi partagé (`services.py:635`). | `SCRUM-215` À faire ○ |
| UC-013 | Le passager annule une course | `P/P/C` | **Présent** | `POST /v1/rides/{id}/cancel` (`services.py:519-553`) : motif contrôlé contre `VALID_CANCEL_REASONS`, refus sur course terminée, déjà annulée ou `no_driver_found`, arrêt de l'attente si active, statut cible distinct passager/chauffeur, motif persisté. Aucune facturation n'est produite. | `SCRUM-216` Terminé(e) ○ |
| UC-015 | Le passager declenche une alerte d'urgence <br>*note du classeur :* Back ecrit bien un log ride_emergency ; le workflow support reste a faire | `A/P/C` | **Présent** | `POST /v1/rides/{id}/emergency` ; l'alerte **est envoyée** : webhook WhatsApp au support et au contact d'urgence, plus courriel SMTP (`ride/application/emergency_notifications.py:24-96`). Chaque canal non configuré est explicitement tracé en `_skip` avec son motif. | `SCRUM-218` Terminé(e) ○ |
| UC-253 | Le passager est informe qu'aucun chauffeur n'est disponible et peut relancer ou demander a etre notifie <br>*note du classeur :* Cas d'echec du dispatch apres 2 min, absent du backlog | `A/A/A` | **Partiel** | État terminal `no_driver_found` et événement WebSocket `ride.no_driver_found` (`websocket.py:156`), produits à l'épuisement du budget de recherche (`matching_service.py` `_give_up`). Aucune relance côté serveur : le passager crée une nouvelle course. Aucune mise en attente de notification. | `SCRUM-221` À faire ○ |
| UC-254 | Le passager choisit son mode de paiement avant de commander | `P/P/C` | **Présent** | Moyen de paiement porté par la demande de course et conservé sur la course ; `422 INVALID_PAYMENT_METHOD` sur valeur inconnue. | `SCRUM-222` Terminé(e) ○ |
| UC-255 | Le passager voit l'heure de la derniere position connue du chauffeur dans l'application <br>*note du classeur :* L'equivalent existe pour la page publique, pas dans l'app | `A/A/A` | **Partiel** | `last_location_at` est exposé sur le lien de suivi partagé (`services.py:635`). La réponse de `GET /v1/rides/{id}` ne porte pas cet horodatage. | `SCRUM-223` À faire ○ |
| UC-256 | Le passager distingue sa propre perte de connexion de celle du chauffeur <br>*note du classeur :* Deux messages distincts, sinon le chauffeur est accuse a tort | `A/A/A` | **Absent du code** | Aucun signal distinguant la perte de connexion du passager de celle du chauffeur. Les positions portent un TTL Redis, exploité pour l'attente, pas diffusé comme état de santé. | `SCRUM-224` À faire ○ |
| UC-257 | Le passager annule sans frais quand le chauffeur est silencieux au-dela du delai defini avant la prise en charge <br>*note du classeur :* Et sans penalite de points pour le chauffeur : ce n'est pas sa faute | `A/A/A` | **Partiel** | L'annulation est gratuite dans tous les cas (`services.py:519-553`), donc l'effet attendu est atteint. Aucun délai de silence du chauffeur n'est mesuré côté serveur. | `SCRUM-225` À faire ○ |
| UC-258 | Le passager demande un arret et voit le surcout d'attente s'appliquer en direct <br>*note du classeur :* Decision du 14/09 : prix fixe sauf attente et escale | `A/A/A` | **Présent** | `POST /v1/rides/{id}/waiting/start` et `/stop` ; le supplément d'attente entre dans `final_fare = base + waiting_fee + supplements_total` (`services.py:349`). Côté passager, l'attente est déclenchée par le chauffeur, pas demandée par le passager. | `SCRUM-226` À faire ○ |
| UC-259 | Le passager ajoute une escale, voit le surcout et le valide avant qu'il soit applique <br>*note du classeur :* Decision du 14/09 | `A/A/A` | **Présent** | `POST /v1/rides/{id}/stops` (`services.py:454`) et `POST .../supplements` (ligne 478) ; `GET .../supplements` liste les lignes. La validation du surcoût par le passager n'est pas portée par une route dédiée. | `SCRUM-227` À faire ○ |

## DiddiGo / Chauffeur

17 use cases MVP, dont 12 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-018 | Le chauffeur cree son profil chauffeur <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/drivers/profile` (`driver_service.py:41`). | `SCRUM-183` Terminé(e) ○ |
| UC-019 | Le chauffeur soumet ses documents KYC <br>*note du classeur :* Bug confirme : le verso permis/CNI est capture mais jamais envoye au backend | `P/P/C` | **Présent** | `POST /v1/drivers/kyc/resubmit` (`driver_service.py:107`) ; documents délégués à DiddiFiles, seuls les `file_id` sont conservés. `_ensure_kyc_documents_complete` contrôle la complétude avant approbation. | `SCRUM-184` Terminé(e) ○ |
| UC-020 | Le chauffeur ajoute un vehicule <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/drivers/vehicle` et `PUT /v1/drivers/me/vehicle` (`driver_service.py:234`, `330`). | `SCRUM-185` Terminé(e) ○ |
| UC-021 | Le chauffeur soumet les documents du vehicule <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/drivers/vehicles/{id}/kyv/resubmit` (`driver_service.py:376`). | `SCRUM-186` Terminé(e) ○ |
| UC-022 | Le chauffeur suit l'etat de validation de son profil | `P/P/P` | **À vérifier** | `GET /v1/drivers/me` et `GET /v1/me/capabilities` exposent un état et des `blocking_reasons` (`driver_service.py:499-537`). Les motifs de décision sont persistés — `profile.kyc_review_notes` et `vehicle.review_notes` (lignes 180, 200, 451, 469) — mais leur exposition au chauffeur dans `_profile_payload` reste à confirmer par lecture fine. | `SCRUM-187` Terminé(e) ○ |
| UC-023 | Le chauffeur passe en ligne <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/drivers/online` ; refus par `403 DRIVER_NOT_VERIFIED` ou `409 NO_ACTIVE_VEHICLE` (`driver_service.py:633,647`), contrôles rejoués à l'acceptation (`matching_service.py:222,232`). | `SCRUM-188` Terminé(e) |
| UC-024 | Le chauffeur passe hors ligne <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/drivers/offline`. | `SCRUM-189` Terminé(e) ○ |
| UC-025 | Le chauffeur recoit une proposition de course <br>*note du classeur :* Ecran DriverRideOfferScreen existe ; son/vibration ecran verrouille = priorite absolue, voir bloc Notifications | `P/P/P` | **Partiel** | L'offre part en WebSocket `ride.new_request` (`websocket.py:173`) et par FCM. `push_enabled` est à `false` par défaut (`core/settings.py:99`). `UserDevice` porte `platform` et `push_token` (`notification/domain.py:10-15`) mais **aucun champ de son ni de canal** : rien n'est demandé côté serveur sur ce plan. | `SCRUM-190` Terminé(e) |
| UC-026 | Le chauffeur accepte une course <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/rides/{id}/accept` (`matching_service.py:180`) ; exclusivité par claim Redis `SET NX` doublée d'une contrainte en base ; `409 OFFER_EXPIRED`, `403 OFFER_NOT_YOURS`, `409 RIDE_ALREADY_MATCHED`. | `SCRUM-191` Terminé(e) |
| UC-027 | Le chauffeur refuse une course <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `POST /v1/rides/{id}/decline` (`matching_service.py:290`) réoriente l'offre vers le candidat suivant. Une pénalité **existe** désormais : `-3` points au moteur de priorité sur annulation chauffeur (`core/settings.py:75`), distincte du simple refus. | `SCRUM-192` Terminé(e) ○ |
| UC-028 | Le chauffeur envoie sa position pendant la course <br>*note du classeur :* Format des traces GPS non conforme a ce qu'attend DiddiMap : ecart ouvert | `P/P/C` | **Présent** | `POST /v1/rides/{id}/location-samples` (`services.py:582`) accepte des lots ; positions et vitesses en Redis avec TTL. | `SCRUM-193` Terminé(e) |
| UC-029 | Le chauffeur met a jour les etapes de la course <br>*note du classeur :* Revue code frontend 31/08 : ecran existant mais incomplet, donc P et non A | `P/P/C` | **Présent** | `PATCH /v1/rides/{id}/status` (`services.py:278`) contre `ALLOWED_TRANSITIONS` ; `409 INVALID_STATUS_TRANSITION` hors table ; complétion idempotente. | `SCRUM-194` Terminé(e) |
| UC-030 | Le chauffeur consulte ses gains <br>*note du classeur :* Le detail existe cote backend mais n'est affiche nulle part dans l'app | `A/A/C` | **Présent** | `GET /v1/drivers/me/wallet` et `/ledger` ; la décomposition et le versement estimé sont calculés et exposés (`services.py:349-351`, `_ride_detail_payload`), sous condition de visibilité selon le rôle (`_money_visible`). | `SCRUM-195` Terminé(e) ○ |
| UC-270 | Le chauffeur fournit les photos obligatoires du vehicule : quatre cotes, habitacle avant et arriere, coffre <br>*note du classeur :* Present dans les notes terrain, absent du backlog | `A/A/P` | **Présent** | Les cinq photos existent sur le véhicule : `vehicle_front_photo_file_id`, `_back_`, `_left_`, `_right_` et `vehicle_interior_photo_file_id` (`ride/domain/entities.py:317-322`), plus `photo_url` dans la charge utile. | `SCRUM-204` Terminé(e) ○ |
| UC-271 | Le chauffeur active le mode attente, bloque tant que le vehicule roule <br>*note du classeur :* Sans ce verrou, l'attente est activee aux feux rouges | `A/A/A` | **Présent** | Statut `waiting` dans `ALLOWED_TRANSITIONS` (`entities.py:49-54`) ; `POST /v1/rides/{id}/waiting/start` exige une vitesse GPS (`409 WAITING_TELEMETRY_REQUIRED`) sous le seuil de véhicule arrêté (`409 VEHICLE_NOT_STOPPED`, la réponse porte la vitesse mesurée et le maximum admis) et refuse une télémétrie plus ancienne que son TTL (`services.py:366-395`). | `SCRUM-205` Terminé(e) ○ |
| UC-272 | Le chauffeur enregistre une escale demandee oralement et fait valider le surcout par le passager | `A/A/A` | **Présent** | `POST /v1/rides/{id}/stops` et `/supplements` (`services.py:454`, `478`) ; chaque supplément est une ligne rattachée au prix (`RideSupplement`, `ride/infra/repositories.py`). `422 INVALID_SUPPLEMENT_AMOUNT` sur montant invalide. La validation par le passager n'a pas de route dédiée. | `SCRUM-206` Terminé(e) ○ |
| UC-273 | Le chauffeur annule sans penalite quand le passager est absent apres le delai d'attente sur place | `A/A/A` | **Présent** | Motif `passenger_no_show` dans `CancelReason` (`entities.py:109`) ; l'annulation ne produit aucun frais et ne verse aucune pénalité au chauffeur dans ce cas. Le délai de dix minutes n'est pas mesuré côté serveur. | `SCRUM-207` Terminé(e) ○ |

## Matching et Priorite

14 use cases MVP, dont 14 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-103 | Le systeme selectionne les chauffeurs eligibles autour du pickup <br>*note du classeur :* Traitement automatique : pas d'ecran, UX/Front sans objet (etait note C dans la V0) | `n.a./n.a./P` | **Présent** | Sélection des chauffeurs éligibles autour du point de prise en charge, par proximité PostGIS puis filtres : vérifié, en ligne, libre, confort compatible, position récente, non déjà sollicité (`matching_service.py` `_next_candidates`). | `SCRUM-283` Terminé(e) ○ |
| UC-104 | Le systeme selectionne les livreurs eligibles autour du pickup <br>*note du classeur :* Traitement automatique : pas d'ecran, UX/Front sans objet (etait note C dans la V0) | `n.a./n.a./P` | **Hors diddi-go** | Livreurs : périmètre DiddiSend, code non lu. | `SCRUM-284` Terminé(e) ○ |
| UC-105 | Le systeme classe les pros selon distance, disponibilite, vehicule et performance <br>*note du classeur :* Traitement automatique : pas d'ecran, UX/Front sans objet (etait note C dans la V0) | `n.a./n.a./P` | **Présent** | Classement en deux temps : tri par distance, puis reclassement d'une liste courte par temps de trajet réel DiddiMap (`matching_eta_ranking_enabled`, `matching_eta_shortlist_size`, `core/settings.py:58-59`), avec bonus de priorité (`priority_service.py`). Si DiddiMap est indisponible, l'ordre de distance est conservé silencieusement (`settings.py:54-57`). | `SCRUM-285` A tester ○ |
| UC-107 | Le systeme evite qu'un pro recoive deux missions incompatibles <br>*note du classeur :* Traitement automatique : pas d'ecran, UX/Front sans objet (etait note C dans la V0) | `n.a./n.a./P` | **Présent** | Un chauffeur déjà sur une course est exclu des offres — invariant couvert par `tests/test_matching.py`. | `SCRUM-287` A tester ○ |
| UC-112 | Le systeme tient la qualite du dispatch a 10 chauffeurs connectes et plus <br>*note du classeur :* Test WebSocket en charge par paliers 5 -> 15 -> 30+ | `n.a./n.a./A` | **Absent du code** | Aucune mesure ni garantie de qualité de dispatch en fonction du nombre de chauffeurs connectés. | `SCRUM-292` Revue en cours ○ |
| UC-278 | Le systeme envoie l'offre a une vague de plusieurs chauffeurs simultanement et passe a la vague suivante en cas de non-reponse <br>*note du classeur :* Vagues recalculees, pas une file figee : les positions changent en quelques secondes | `n.a./n.a./A` | **Présent** | Modèle de vagues d'offres dans `matching_service.py` : `try_match` ouvre une vague, `advance_expired_offer` passe à la suivante à expiration (ligne 320). | `SCRUM-293` A tester ○ |
| UC-279 | Le systeme ferme une offre non repondue apres le delai d'acceptation defini <br>*note du classeur :* Delai a trancher ; au-dela de 20 s le passager attend pour rien | `n.a./n.a./A` | **Présent** | `OFFER_TTL_SECONDS = 15` (`ride/infra/offer_store.py:35`) ; l'offre se ferme par expiration de la clé Redis, et `advance_expired_offer` réoriente. Valeur en **constante de code**. | `SCRUM-294` A tester ○ |
| UC-280 | Le systeme elargit le rayon de recherche a chaque nouvelle vague | `n.a./n.a./A` | **Présent** | `matching_search_radius_step_km` élargit le rayon à chaque vague, borné par `matching_search_radius_max_km` (`core/settings.py:64-65`). Élargissement par pas uniforme, pas par phases nommées. Couvert par `tests/test_matching_wave_dynamics.py`. | `SCRUM-295` Revue en cours ○ |
| UC-281 | Le systeme exclut d'une vague les chauffeurs deja sollicites sur la meme course | `n.a./n.a./A` | **Présent** | Chauffeurs déjà sollicités mémorisés en Redis (`TRIED_KEY_PREFIX`) et exclus des vagues suivantes. | `SCRUM-296` A tester ○ |
| UC-282 | Le systeme abandonne la recherche apres le budget de temps defini et notifie le passager <br>*note du classeur :* 2 minutes decidees le 14/09 | `n.a./n.a./A` | **Présent** | `matching_search_budget_seconds` (`core/settings.py:66`) ; à épuisement, `_give_up` place la course en `no_driver_found` et émet `ride.no_driver_found`. | `SCRUM-297` Revue en cours ○ |
| UC-283 | Le systeme classe les chauffeurs par temps d'arrivee estime pondere par les points de priorite <br>*note du classeur :* La priorite agit sur le tri, pas sur un delai d'envoi | `n.a./n.a./A` | **Présent** | Reclassement par temps d'arrivée estimé combiné aux points de priorité : `matching_eta_ranking_enabled` et `_priority_bonuses` (`matching_service.py`). | `SCRUM-298` Revue en cours ○ |
| UC-284 | Le systeme plafonne l'effet de la priorite pour qu'un chauffeur lointain ne passe jamais devant un chauffeur proche <br>*note du classeur :* C'est ce plafond qui protege l'experience du passager | `n.a./n.a./A` | **Présent** | `matching_priority_cap_seconds` plafonne le bonus pour que la proximité reste dominante (`core/settings.py:72`) ; valeurs d'amorçage d'une configuration stockée en base, éditable par `PUT /internal/v1/admin/dispatch/config`. | `SCRUM-299` Revue en cours ○ |
| UC-286 | Le systeme n'applique aucune penalite aux chauffeurs non retenus d'une vague | `n.a./n.a./A` | **Présent** | Les points de priorité ne sont versés que sur l'issue de la course (`_record_priority_outcome`, `services.py:546`) : `+1` course terminée, `-3` annulation chauffeur. Aucune pénalité n'est appliquée à un chauffeur non retenu d'une vague. | `SCRUM-301` A tester ○ |
| UC-287 | Le systeme ne lance pas de recherche quand aucun chauffeur libre n'est dans le rayon minimal <br>*note du classeur :* Seuil retenu : au moins un chauffeur libre a 3 km | `n.a./n.a./A` | **À vérifier** | Le vivier est calculé avant d'ouvrir une vague et l'absence de candidat conduit à `no_driver_found`. Qu'aucune recherche ne soit *lancée* lorsque le rayon initial est vide reste à établir par lecture de `try_match`. | `SCRUM-302` Revue en cours ○ |

## Prix, commissions et penalites

5 use cases MVP, dont 5 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-181 | Le passager voit la decomposition du prix : base, distance, duree <br>*note du classeur :* A faire avant lancement mais non prioritaire (arbitrage 31/08) | `A/A/C` | **Présent** | Décomposition base / distance / durée renvoyée par l'estimation et conservée sur la course (`_pricing_breakdown`, `_pricing_response`, `services.py`). | `SCRUM-325` Terminé(e) ○ |
| UC-182 | Le chauffeur voit sa synthese de gains : taux, frais, bonus, net, cash recu et a reverser | `A/A/C` | **Partiel** | Taux, commission, versement estimé et grand livre du wallet sont exposés (`services.py:349-351`, `/v1/drivers/me/wallet/ledger`). Aucune synthèse agrégée par période, et pas de ligne de cash reçu à reverser — ce compteur appartient à DiddiSend. | `SCRUM-326` Terminé(e) ○ |
| UC-301 | Le systeme ne facture le temps d'attente que lorsque le vehicule est reellement a l'arret | `n.a./n.a./A` | **Présent** | L'attente ne démarre que si la vitesse GPS est sous `waiting_stationary_speed_threshold_kmh` (`409 VEHICLE_NOT_STOPPED`) et si la télémétrie est plus récente que son TTL (`services.py:381-392`). | `SCRUM-333` À faire ○ |
| UC-303 | Le systeme recalcule l'itineraire a l'ajout d'une escale et n'applique un supplement qu'au-dela des seuils de distance et de duree <br>*note du classeur :* Un seuil de distance seul ne suffit pas en circulation dense | `n.a./n.a./A` | **Partiel** | L'escale et le supplément sont enregistrés et entrent dans le total (`services.py:454-504`). Aucun recalcul d'itinéraire DiddiMap à l'ajout d'une escale ; SCRUM-537, reclassé V2, porte ce recalcul. | `SCRUM-335` À faire ○ |
| UC-304 | Le systeme conserve chaque supplement comme une ligne distincte rattachee a la course <br>*note du classeur :* Sans ces lignes, aucun litige de prix n'est arbitrable | `n.a./n.a./A` | **Présent** | `RideSupplement` est une ligne distincte rattachée à la course (`ride/domain/entities.py`, `ride/infra/repositories.py`), cumulée dans `supplements_total`. | `SCRUM-336` À faire ○ |

## Argent des pros

6 use cases MVP, dont 2 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-189 | Le chauffeur recharge son wallet pour continuer a recevoir des courses <br>*note du classeur :* Confirme reel : un solde a deja bouge apres une vraie recharge en staging | `P/P/C` | **Présent** | `POST /v1/drivers/me/wallet/topups` crée un PaymentIntent DiddiPay avec référence métier chauffeur ; `GET .../topups/{id}` suit l'état. | `SCRUM-91` Terminé(e) |
| UC-190 | Le systeme bloque un pro dont le solde passe sous le minimum exige <br>*note du classeur :* Regle commerciale prevue en V2 dans le doc DiddiGo | `A/A/A` | **Présent** | Le contrôle existe — `driver_min_balance` (`core/settings.py:124`) — et est **neutralisé par sa valeur par défaut**, donc aucun blocage ne survient en configuration par défaut. | `SCRUM-92` Terminé(e) |
| UC-192 | Le systeme capture le paiement au moment de la livraison confirmee <br>*note du classeur :* payment.released est declare mais jamais emis aujourd'hui | `n.a./n.a./A` | **Hors diddi-go** | Capture au moment de la livraison confirmée : périmètre DiddiSend et DiddiPay, code non lu. Côté Go, l'équivalent est la complétion de course puis le paiement. | `SCRUM-94` À faire ○ |
| UC-193 | L'administrateur rembourse tout ou partie d'un paiement <br>*note du classeur :* Le remboursement existe cote DiddiPay mais n'est pas branche cote metier | `A/A/P` | **Absent du code** | Aucune route de remboursement dans `diddi-go` ; la décision appartient au Backoffice et l'exécution à DiddiPay. | `SCRUM-95` Terminé(e) ○ |
| UC-309 | Le systeme ne propose pas une course dont la commission estimee depasse le solde du pro <br>*note du classeur :* Un seuil fixe ne protege pas des grosses courses : le controle doit etre par course | `n.a./n.a./A` | **Présent** | Le contrôle existe — `driver_max_estimated_commission` (`core/settings.py:125`) — et est **neutralisé par sa valeur par défaut**. | `SCRUM-98` À faire |
| UC-310 | Le systeme tolere un decouvert borne et bloque le passage en ligne tant qu'il n'est pas comble <br>*note du classeur :* Decision du 14/09 | `A/A/A` | **À vérifier** | Les deux seuils existent et sont neutres par défaut. Qu'un découvert borné soit toléré puis bloquant reste à établir par lecture de `wallet_service.py`. | `SCRUM-99` Terminé(e) |

## DiddiPay

9 use cases MVP, dont 9 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-068 | L'utilisateur consulte le solde de son wallet | `P/P/C` | **Hors diddi-go** | Wallet DiddiPay : module DiddiPay, code non lu. DiddiGo porte son propre wallet chauffeur, distinct. | `SCRUM-13` Terminé(e) ○ |
| UC-069 | L'utilisateur configure son PIN wallet | `P/P/C` | **Hors diddi-go** | PIN wallet : module DiddiPay, code non lu. | `SCRUM-14` Terminé(e) ○ |
| UC-070 | L'utilisateur depose de l'argent | `P/P/C` | **Hors diddi-go** | Dépôt : module DiddiPay, code non lu. Côté Go, la recharge passe par `POST /v1/drivers/me/wallet/topups`. | `SCRUM-15` Terminé(e) ○ |
| UC-071 | L'utilisateur retire de l'argent <br>*note du classeur :* Le payout via le nouvel orchestrateur n'est pas encore disponible | `P/P/P` | **Hors diddi-go** | Retrait : module DiddiPay, code non lu. **Aucune route de retrait dans `diddi-go`.** | `SCRUM-23` Terminé(e) ○ |
| UC-072 | L'utilisateur transfere de l'argent a un autre utilisateur | `P/P/C` | **Hors diddi-go** | Transfert entre utilisateurs : module DiddiPay, code non lu. | `SCRUM-16` Terminé(e) ○ |
| UC-075 | L'utilisateur consulte son historique de transactions | `P/P/C` | **Hors diddi-go** | Historique de transactions DiddiPay : code non lu. Côté Go, `GET /v1/drivers/me/wallet/ledger`. | `SCRUM-19` Terminé(e) ○ |
| UC-076 | Le systeme cree et suit une intention de paiement <br>*note du classeur :* UX sans objet (etait note C dans la V0) | `n.a./P/C` | **Hors diddi-go** | Création et suivi d'une intention de paiement : module DiddiPay, code non lu. Côté Go, `payment/infra/diddipay_client.py` la demande et la relit. | `SCRUM-20` Terminé(e) ○ |
| UC-077 | L'administrateur rapproche une operation de paiement | `P/P/C` | **Hors diddi-go** | Rapprochement d'une opération : module DiddiPay, code non lu. Côté Go, `POST /v1/admin/payments/reconcile` et ses variantes. | `SCRUM-21` Terminé(e) ○ |
| UC-078 | Le systeme recoit et deduplique les webhooks du processeur | `n.a./n.a./C` | **Hors diddi-go** | Déduplication des webhooks du processeur : module DiddiPay, code non lu. Côté Go, le webhook est authentifié par secret de callback et le contexte de retour n'est consommable qu'une fois. | `SCRUM-22` Terminé(e) ○ |

## DiddiFreeID / Identite

7 use cases MVP, dont 5 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-001 | L'utilisateur cree un compte DiddiFree avec telephone ou email | `P/P/C` | **Hors diddi-go** | Création de compte : module DiddiFreeID, code non lu. Côté Go, `POST /v1/auth/register` et un utilisateur fantôme dans `auth.users`. | `SCRUM-168` Terminé(e) ○ |
| UC-002 | L'utilisateur demande un OTP pour se connecter | `P/P/C` | **Hors diddi-go** | Demande d'OTP : module DiddiFreeID, code non lu. Côté Go, `POST /v1/auth/otp/request` existe, avec un `TODO` : aucun fournisseur SMS branché. | `SCRUM-169` Terminé(e) |
| UC-003 | L'utilisateur valide son OTP et ouvre une session | `P/P/C` | **Hors diddi-go** | Validation d'OTP : module DiddiFreeID, code non lu. Côté Go, `POST /v1/auth/otp/verify`. | `SCRUM-170` Terminé(e) |
| UC-004 | L'utilisateur consulte son profil global | `P/P/C` | **Hors diddi-go** | Profil global : module DiddiFreeID, code non lu. Côté Go, `GET /v1/auth/me`. | `SCRUM-171` Terminé(e) ○ |
| UC-006 | L'utilisateur se deconnecte de son compte | `P/P/C` | **Hors diddi-go** | Déconnexion : module DiddiFreeID, code non lu. | `SCRUM-173` Terminé(e) ○ |
| UC-007 | L'administrateur suspend ou reactive un compte utilisateur | `P/P/C` | **Hors diddi-go** | Suspension et réactivation : module DiddiFreeID, code non lu. Côté Go, `403 USER_SUSPENDED` et `403 USER_NOT_VERIFIED` au contrôle d'accès. | `SCRUM-174` Terminé(e) ○ |
| UC-008 | Un service verifie l'identite d'un utilisateur via DiddiFreeID <br>*note du classeur :* Use case machine : pas d'ecran, UX/Front sans objet (etait note C dans la V0) | `n.a./n.a./C` | **Hors diddi-go** | Vérification d'identité par un service : module DiddiFreeID, code non lu. Côté Go, vérification RS256 locale via JWKS, sans rappel synchrone. | `SCRUM-175` Terminé(e) ○ |

## DiddiMap / Cartographie

4 use cases MVP, dont 4 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-144 | Un service recherche un lieu et obtient des suggestions | `n.a./P/C` | **Hors diddi-go** | Recherche de lieu : module DiddiMap, code non lu. Côté Go, `GET /v1/places/search` relaie. | `SCRUM-231` Terminé(e) ○ |
| UC-145 | Un service calcule un itineraire, une distance et une duree | `n.a./P/C` | **Hors diddi-go** | Calcul d'itinéraire : module DiddiMap, code non lu. Côté Go, `ride/infra/routing_client.py` `estimate` l'appelle, avec quatre codes d'erreur distincts. | `SCRUM-232` Terminé(e) ○ |
| UC-146 | Un service envoie ses traces GPS dans le format commun impose par DiddiMap <br>*note du classeur :* Format ecrit par DiddiMap ; ecart DiddiGo confirme, non resolu | `n.a./A/A` | **Présent** | Côté Go, les traces sont envoyées au format DiddiMap : `_ensure_map_trace_started` au démarrage, `append_trace_positions`, puis `analyze_trace` à la complétion (`routing_client.py`). Jeton de service DiddiMap dédié (SCRUM-436, terminé). | `SCRUM-233` À faire ○ |
| UC-147 | Le passager voit un ETA qui se met a jour pendant la course | `P/P/P` | **Absent du code** | Aucun temps d'arrivée estimé réévalué pendant la course n'est diffusé par `diddi-go` ; l'estimation est faite avant la demande. | `SCRUM-234` À faire ○ |

## Urgence et securite des personnes

2 use cases MVP, dont 0 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-169 | Le contact d'urgence choisi est prevenu par SMS ou WhatsApp avec un lien de suivi <br>*note du classeur :* Aujourd'hui le SOS ne notifie que le support interne | `A/A/A` | **Présent** | Le contact d'urgence **est** prévenu : `EmergencyRecipient("emergency_contact", "whatsapp", contact.phone)` et courriel SMTP (`emergency_notifications.py:41-96`). Les canaux sont WhatsApp et courriel, **pas SMS**. Un canal non configuré est tracé en `_skip` avec son motif. | `SCRUM-6` Terminé(e) |
| UC-170 | Un seul declenchement d'urgence est compte par course <br>*note du classeur :* Arbitrage du 31/08 | `n.a./A/A` | **À vérifier** | L'alerte est enregistrée sur la course et journalisée. Qu'un seul déclenchement soit compté par course reste à établir par lecture de `request_emergency` (`services.py:640`). | `SCRUM-7` À faire |

## Notifications et canaux

4 use cases MVP, dont 1 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-156 | Le pro est reveille par un son et une vibration sur une offre, ecran verrouille <br>*note du classeur :* Priorite absolue confirmee le 31/08 ; rien n'existe aujourd'hui dans l'ecran d'offre | `A/A/P` | **Partiel** | L'offre est poussée en WebSocket et par FCM. `UserDevice` ne porte ni champ de son ni canal de notification (`notification/domain.py:10-15`) : rien n'est demandé côté serveur sur le réveil de l'appareil. | `SCRUM-304` À faire |
| UC-157 | L'utilisateur recoit une notification quand l'app est en arriere-plan ou fermee <br>*note du classeur :* Le code n'a que l'enregistrement du token, aucun handler onMessage / onBackgroundMessage | `A/A/P` | **Partiel** | `UserDevice.platform` et `push_token` existent, `POST /v1/devices/register` et `/unregister` les gèrent. `push_enabled` est à `false` par défaut (`core/settings.py:99`), donc rien n'est envoyé en configuration par défaut. | `SCRUM-305` Terminé(e) |
| UC-158 | L'utilisateur recoit une notification sur iPhone <br>*note du classeur :* iOS n'est pas cable du tout | `A/A/P` | **Partiel** | Même constat : la plateforme est portée par `UserDevice`, la livraison dépend de `push_enabled` et d'une configuration FCM. | `SCRUM-306` À faire |
| UC-159 | Le destinataire recoit ses informations et son PIN par SMS ou WhatsApp <br>*note du classeur :* Evolution API deja deployee en staging ; canal partage avec le SOS | `A/A/P` | **Hors diddi-go** | Destinataire de colis et PIN : périmètre DiddiSend, code non lu. | `SCRUM-307` À faire ○ |

## Reseau degrade et continuite

5 use cases MVP, dont 4 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-319 | Le pro continue sa mission hors connexion, ses actions etant mises en file locale sur le telephone <br>*note du classeur :* Option retenue le 14/09 : file locale et rejeu | `A/A/A` | **Partiel** | Côté serveur, `POST /v1/rides/{id}/location-samples` accepte des **lots** de positions avec leur `recorded_at` d'origine (`services.py:582-607`), ce qui permet le vidage d'une file locale. La file elle-même est un travail d'application. | `SCRUM-370` Terminé(e) ○ |
| UC-320 | Le systeme rejoue les actions en attente a la reconnexion sans doublon, par cle d'idempotence | `n.a./A/A` | **Présent** | Trois mécanismes : claim Redis `SET NX` sur l'attribution, réservation de commande S2S (`core/s2s_command_store.py`), et idempotence applicative — complétion rejouable (`ride.completion.retry`), démarrage d'attente rejouable, contexte de retour de paiement consommable une seule fois, projection portant `projection_version` et `event_id`. | `SCRUM-371` À faire |
| UC-321 | Le systeme borne l'horloge du telephone pour les actions horodatees hors ligne <br>*note du classeur :* Une horloge fausse ou manipulee fausse la duree facturee | `n.a./n.a./A` | **Partiel** | Le serveur accepte le `recorded_at` fourni par le client et le remplace par l'heure serveur s'il est absent (`services.py:591`). Aucune borne n'est appliquée à une horloge client fausse. | `SCRUM-372` À faire ○ |
| UC-322 | Le systeme qualifie la fraicheur de la position en paliers et declenche les affichages correspondants <br>*note du classeur :* Position fraiche, tiede, froide : seuils differents avant et pendant la course | `n.a./A/A` | **Partiel** | La fraîcheur des positions est exploitée comme seuil binaire par le TTL Redis, pour autoriser ou refuser l'attente. Aucune qualification en paliers n'est diffusée. | `SCRUM-373` À faire ○ |
| UC-323 | Le systeme fige l'heure d'arrivee estimee au lieu de la faire defiler quand les positions ne rentrent plus <br>*note du classeur :* Un compte a rebours qui ment detruit plus la confiance que le silence | `n.a./A/A` | **Absent du code** | Aucun temps d'arrivée estimé n'est diffusé pendant la course, donc rien à figer. | `SCRUM-374` À faire ○ |

## Historique, recus et justificatifs

2 use cases MVP, dont 2 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-245 | Le passager consulte l'historique de ses courses <br>*note du classeur :* Absent de la matrice V0 : aucun use case d'historique cote passager | `A/A/P` | **Présent** | `GET /v1/rides` liste l'historique du passager (`services.py:239`). | `SCRUM-275` Terminé(e) ○ |
| UC-246 | Le passager consulte le detail d'une course passee : prix, duree reelle, distance, mode de paiement, note | `A/A/P` | **Présent** | `GET /v1/rides/{id}` renvoie prix, durée, distance et moyen de paiement, sous condition de visibilité selon le rôle (`_ride_detail_payload`, `_money_visible`). | `SCRUM-276` À faire ○ |

## Suivi public hors application

6 use cases MVP, dont 6 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-163 | Un proche ouvre le lien de suivi d'une course sans installer l'app <br>*note du classeur :* Sous-domaine diddigo.diddifree.com, non servi par le backend | `A/A/A` | **Présent** | `POST /v1/rides/{id}/share-link` et `GET /v1/rides/shared/{token}` (`services.py:608-639`) ; jeton aléatoire `SHARE_TOKEN_BYTES`, `404 SHARE_LINK_NOT_FOUND` sur jeton inconnu. | `SCRUM-377` Terminé(e) ○ |
| UC-164 | Un proche ouvre le lien de suivi d'une livraison sans installer l'app <br>*note du classeur :* Sous-domaine diddisend.diddifree.com, non indexe | `A/A/A` | **Hors diddi-go** | Lien de suivi d'une livraison : périmètre DiddiSend, code non lu. | `SCRUM-378` Terminé(e) ○ |
| UC-165 | Le lien expire automatiquement : 20 min apres la course, a la fin de la livraison | `n.a./A/A` | **À vérifier** | Le lien existe ; l'expiration automatique après la course reste à établir par lecture de `create_share_link` et `get_shared_ride`. | `SCRUM-379` À faire ○ |
| UC-166 | La page affiche l'ETA et l'heure de la derniere position connue <br>*note du classeur :* Aucun indicateur de fraicheur de position aujourd'hui | `A/A/P` | **Partiel** | `last_location_at` est bien exposé sur la page de suivi (`services.py:635`). Aucun temps d'arrivée estimé n'est diffusé. | `SCRUM-380` À faire ○ |
| UC-167 | Le suivi bascule en interrogation REST periodique si le temps reel tombe <br>*note du classeur :* Arbitrage du 31/08 : polling REST de secours | `n.a./A/A` | **Partiel** | La page de suivi est servie par une route REST (`GET /v1/rides/shared/{token}`), donc interrogeable périodiquement ; aucune bascule automatique depuis le temps réel n'est orchestrée côté serveur. | `SCRUM-381` À faire ○ |
| UC-168 | Les pages de suivi ne sont pas indexees par les moteurs de recherche | `n.a./A/A` | **Absent du code** | Aucune directive d'indexation n'est émise par `diddi-go` ; la route renvoie du JSON, la page est servie ailleurs. | `SCRUM-382` À faire ○ |

## Compte, donnees personnelles et conformite

6 use cases MVP, dont 5 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-196 | L'utilisateur supprime son compte et demande l'effacement de ses donnees <br>*note du classeur :* Exigence de publication Apple et Google | `A/A/A` | **Absent du code** | Aucune route de suppression de compte ni d'effacement parmi les 124 routes exposées. | `SCRUM-113` Terminé(e) ○ |
| UC-197 | L'utilisateur accepte des CGU et une politique de confidentialite versionnees | `A/A/A` | **Absent du code** | Aucune notion de conditions générales ni de version de politique de confidentialité dans `diddi-go`. | `SCRUM-114` Terminé(e) ○ |
| UC-201 | Tout acces administrateur a des donnees personnelles est journalise | `P/P/P` | **Partiel** | Les actions sensibles du Backoffice sont journalisées — `BackofficeAuditEvent` et `AuditRepository.record` (`audit/domain/interfaces.py:9`) — et `log_event()` émet un événement métier depuis 128 points. Aucune journalisation spécifique d'un *accès en lecture* à une donnée personnelle. | `SCRUM-118` À faire ○ |
| UC-333 | Le systeme anonymise le compte au lieu de le supprimer et conserve les pieces comptables <br>*note du classeur :* Le droit a l'effacement et la conservation comptable OHADA se contredisent | `n.a./A/A` | **Absent du code** | Aucune anonymisation dans `diddi-go`. | `SCRUM-119` À faire ○ |
| UC-334 | Le systeme refuse une demande de suppression tant qu'une mission, un solde ou un litige est ouvert | `A/A/A` | **Partiel** | Le solde et la dette du chauffeur sont lisibles (`/v1/drivers/me/wallet`), et les courses actives sont identifiables par leur état. Aucune demande de suppression à refuser, faute de route de suppression. | `SCRUM-120` À faire |
| UC-335 | Le systeme applique un delai de grace avant l'anonymisation definitive | `A/A/A` | **Absent du code** | Aucun délai de grâce, faute de parcours de suppression. | `SCRUM-121` À faire ○ |

## Partenaires et Flottes

6 use cases MVP, dont 6 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-120 | Le partenaire cree ou fait creer son organisation | `A/A/P` | **Présent** | `POST /v1/admin/partners` et `POST /internal/v1/admin/partners` ; `Partner` avec `PartnerStatus` et `PartnerType` (`partner/domain/entities.py`). | `SCRUM-311` À faire ○ |
| UC-121 | Le partenaire complete ses informations business | `A/A/P` | **Présent** | `PATCH /v1/admin/partners/{id}` ; `PATCH .../kyc`, `POST .../kyc/approve` et `/reject` pour le dossier. | `SCRUM-312` À faire ○ |
| UC-123 | Le partenaire gere ses chauffeurs ou livreurs rattaches | `A/A/P` | **Présent** | `POST`, `GET` et `DELETE /v1/admin/partners/{id}/drivers` ; `PartnerDriverLink` porte l'affiliation. | `SCRUM-314` À faire ○ |
| UC-124 | Le partenaire gere ses vehicules | `A/A/P` | **Présent** | `POST /v1/admin/partners/{id}/vehicles`. | `SCRUM-315` À faire ○ |
| UC-125 | Le partenaire affecte un vehicule a un operateur terrain | `A/A/P` | **Présent** | `POST .../vehicles/{vehicle_id}/assign` et `/unassign` ; `VehicleAssignment` porte l'affectation. | `SCRUM-316` À faire ○ |
| UC-128 | L'administrateur valide, suspend ou refuse un partenaire | `P/P/C` | **Présent** | `POST /v1/admin/partners/{id}/activate`, `/suspend`, `/reject`, et les routes KYC d'approbation et de rejet. | `SCRUM-319` Terminé(e) ○ |

## Reputation et fraude cote pro

2 use cases MVP, dont 2 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-326 | Le systeme detecte une position GPS simulee et force le passage hors ligne <br>*note du classeur :* L'indicateur systeme existe sur Android : il suffit de le lire | `n.a./A/A` | **Absent du code** | Aucune détection de position simulée dans `diddi-go`. Le seul contrôle de plausibilité est le seuil de vitesse à l'activation de l'attente. | `SCRUM-363` Terminé(e) ○ |
| UC-327 | Le systeme enregistre une empreinte d'appareil a l'inscription et bloque les comptes multiples | `n.a./A/A` | **Absent du code** | Aucune empreinte d'appareil. `UserDevice` porte un jeton de push, pas une empreinte, et n'est pas exploité comme signal anti-fraude. | `SCRUM-364` Terminé(e) ○ |

## Zones, couverture et majoration

1 use cases MVP, dont 1 sans ticket cité par le planning.

| UC | Use case | UX/Front/Back | Code au 09/10 | Constat | Ticket |
| --- | --- | --- | --- | --- | --- |
| UC-289 | L'administrateur definit le polygone de la zone de service d'une ville <br>*note du classeur :* Aucun use case de zone de service dans la matrice V0 | `A/A/A` | **Absent du code** | Aucun polygone ni géométrie de zone. La règle tarifaire est indexée par **ville** et catégorie de véhicule (`PricingRuleRepository.find_active(city, vehicle_category)`), sans géométrie. | `SCRUM-392` À faire ○ |

Légende de la colonne Ticket : `○` signale un use case dont le ticket n'est cité par aucun livrable
backend du planning.

## Use cases du périmètre hors parcours DiddiGo

Ils appartiennent au périmètre par leur lot, mais décrivent un parcours Send ou Food.

| UC | Pourquoi |
| --- | --- |
| UC-104 | Sélection des livreurs éligibles — parcours DiddiSend |
| UC-159 | Destinataire de colis prévenu par SMS avec son PIN — parcours DiddiSend |
| UC-164 | Lien de suivi d'une livraison — parcours DiddiSend |

## Sources

| Source | Date | Rôle |
| --- | --- | --- |
| `diddi-go/app_base/`, `tests/`, surface OpenAPI, `graphify-out/graph.json` | **branche courante** | les constats de code |
| `management/specs/backlog.csv` | — | les 361 use cases, phases et statuts par discipline |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx`, onglets *Backend* et *Jira source* | 09/10/2026 | les tickets que le planning cite |

Rien n'a été écrit dans `management/specs` ni dans le classeur de planning.
