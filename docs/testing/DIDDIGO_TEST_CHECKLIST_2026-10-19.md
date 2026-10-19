# DiddiGo - Checklist de campagne de tests

Edition : `2026-10-19`

Version du registre : `1.1`

Derniere mise a jour : `2026-10-19`

Branche de reference : `stage`

Responsable de mise a jour : `non assigne`

Ce fichier est la checklist de campagne figee du 19 octobre 2026. Il ne doit
pas etre regenere en effacant l'historique : chaque execution met a jour les
cases, les preuves et le journal en bas du document.

Toute evolution substantielle du perimetre cree une nouvelle edition datee,
par exemple `DIDDIGO_TEST_CHECKLIST_2026-10-26.md`. L'ancienne checklist reste
consultable avec ses preuves et ses anomalies.

## Legende

- `[ ]` : non execute ou preuve absente.
- `[x]` : execute avec succes et preuve renseignee.
- `[!]` : bloque ; ajouter le blocage dans le journal.
- `[~]` : partiellement valide.
- `UT` : test unitaire, dependances simulees.
- `IT` : test d'integration avec base, Redis ou adaptateur HTTP controle.
- `STG` : test API sur les vrais services de staging.
- `E2E` : parcours complet depuis les applications ou clients reels.

## Regles de suivi

1. Une case n'est cochee que si une preuve reproductible existe : rapport CI,
   sortie Bruno, `request_id`, capture, logs correles ou identifiants metier.
2. Une nouvelle execution ne supprime pas une ancienne preuve. Ajouter une
   ligne au journal et remplacer la preuve courante uniquement si elle est plus
   recente.
3. Un test staging doit indiquer les versions ou commits DiddiGo et des services
   externes impliques.
4. Ne jamais enregistrer de JWT, secret, numero personnel ou URL signee dans ce
   fichier. Utiliser des identifiants techniques non sensibles.
5. Les tests E2E utilisent des comptes et destinations reserves a la recette.
6. Un echec P0 bloque la campagne : il ne peut pas etre masque par une preuve
   positive d'un autre parcours.
7. Les cas `STG` et `E2E` sont executes sur des donnees de recette identifiees,
   jamais sur une course ou un wallet reel.

## Campagne recommandee

La campagne ne consiste pas a lancer tous les tests dans un ordre aleatoire.
Elle se deroule en lots : le lot suivant ne commence que si le precedent est
vert ou si ses blocages sont documentes et acceptes pour la recette.

| Lot | Objectif | Scenarios | Gate |
| --- | --- | --- | --- |
| P0 | Sante et contrats | `STG-00` a `STG-05`, `STG-70` a `STG-74` | Aucun echec d'authentification, contrat ou dependance critique. |
| P1 | Course cash de reference | `STG-10` a `STG-31` | Une course complete sans doublon financier ni perte de temps reel. |
| P2 | Paiements et gains | `STG-40` a `STG-44`, `STG-56` a `STG-57` | Webhook, top-up et retrait idempotents. |
| P3 | Securite et communication | `STG-50` a `STG-55` | Partage, Comms et SOS respectent leurs permissions. |
| P4 | Backoffice et pilotage | `STG-58` a `STG-60`, `STG-80` a `STG-84` | Decisions auditables et totaux coherents. |
| P5 | Experience humaine | `E2E-01` a `E2E-43` | Deux appareils minimum, preuves fonctionnelles et UX. |

### Ordre pratique

1. Executer les tests unitaires et integration du commit a livrer.
2. Executer P0 sur staging et ouvrir une ligne de journal.
3. Executer P1 avec un passager et un chauffeur de recette.
4. Garder les memes identifiants de course pour P2, P3 et P4 lorsque cela est
   pertinent ; ne jamais reemployer une course terminee pour un nouveau test.
5. Executer P5 uniquement lorsque les APIs et le temps reel ont deja ete valides.

### Preuves minimales par campagne

- commit ou image DiddiGo deployee ;
- identifiants non sensibles : `request_id`, `ride_id`, `driver_id`,
  `payment_intent_id` ou `withdrawal_id` lorsque disponibles ;
- export Bruno, rapport de tests ou capture d'ecran horodatee ;
- resultat des logs correles par `request_id` ;
- ticket et gravite pour chaque anomalie.

## Etat global

| Niveau | Statut | Derniere execution | Preuve | Responsable |
| --- | --- | --- | --- | --- |
| UT | `[x]` | 2026-10-15 | `pytest: 471 passed` | Codex |
| IT | `[~]` | 2026-10-15 | Suite pytest avec PostgreSQL/Redis et adaptateurs controles | Codex |
| STG | `[ ]` | - | - | - |
| E2E | `[ ]` | - | - | - |

## Matrice des parcours

Mettre a jour cette table apres chaque campagne. Les details executables sont
decrits dans les sections suivantes.

| ID | Parcours | UT | IT | STG | E2E | Preuve courante |
| --- | --- | --- | --- | --- | --- | --- |
| FLOW-01 | Identite DiddiFreeID et shadow user | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_identity_integration.py`, `test_diddiauth_shadow_users.py` |
| FLOW-02 | Capacites et scores utilisateur | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_capabilities_router.py`, `test_scoring_service.py` |
| FLOW-03 | Recherche de lieux | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_places_search.py`, `test_routing_client.py` |
| FLOW-04 | Devis et expiration | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_quote_service.py`, `test_pricing_service.py` |
| FLOW-05 | Creation de course | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_flow.py`, `test_ride_request_validation.py` |
| FLOW-06 | Matching par vagues | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_matching_service.py`, `test_matching_wave_dynamics.py` |
| FLOW-07 | Offre WebSocket et acceptation | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_websocket.py`, `test_matching.py` |
| FLOW-08 | Approche, GPS et arrivee | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_mvp_departure_service.py`, `test_driver_location.py` |
| FLOW-09 | Attente pre-course et no-show | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_mvp_departure_service.py` |
| FLOW-10 | Demarrage par code ou QR | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_mvp_departure_service.py` |
| FLOW-11 | Trace GPS DiddiMap | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_routing_client.py` |
| FLOW-12 | Attente pendant la course | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_waiting_service.py` |
| FLOW-13 | Escales hors MVP | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_flow.py` |
| FLOW-14 | Supplements et decision passager | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_supplements_service.py` |
| FLOW-15 | Fin normale et analyse de trace | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_flow.py`, `test_routing_client.py` |
| FLOW-16 | Arret anticipe | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_flow.py`, `test_pricing_service.py` |
| FLOW-17 | Paiement cash | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_diddipay_integration.py` |
| FLOW-18 | Paiement Mobile Money | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_diddipay_client.py`, `test_diddipay_webhook_route.py` |
| FLOW-19 | Wallet et ledger chauffeur | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_diddipay_integration.py` |
| FLOW-20 | Recharge chauffeur | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_diddipay_integration.py` |
| FLOW-21 | Retrait chauffeur | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_driver_withdrawals.py` |
| FLOW-22 | Annulation | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_authorization_service.py` |
| FLOW-23 | Notation bidirectionnelle | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_scoring_service.py`, `test_ride_flow.py` |
| FLOW-24 | Partage public de course | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_flow.py` |
| FLOW-25 | SOS WhatsApp et SMS | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_emergency_services.py`, `test_sms_providers.py` |
| FLOW-26 | DiddiComms ride resolver | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_comms_task_router.py`, `test_comms_task_resolver.py` |
| FLOW-27 | Notifications FCM | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_notifications.py` |
| FLOW-28 | Profil chauffeur | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_driver_kyc.py` |
| FLOW-29 | KYC chauffeur et DiddiFiles | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_driver_kyc.py`, `test_diddifiles_client.py` |
| FLOW-30 | Vehicule et KYV | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_driver_kyc.py`, `test_partner_service.py` |
| FLOW-31 | Chauffeur en ligne/hors ligne | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_driver_online_eligibility.py` |
| FLOW-32 | Partenaires et flottes | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_partner_service.py`, `test_internal_partner_router.py` |
| FLOW-33 | Backoffice et audit | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_backoffice_access_contract.py`, `test_internal_kyc_router.py` |
| FLOW-34 | Administration paiements | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_payment_reconciliation.py` |
| FLOW-35 | Pilotage et reporting | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_ride_summary_router.py`, `test_ride_breakdown.py` |
| FLOW-36 | Observabilite operationnelle | `[x]` | `[x]` | `[ ]` | `[ ]` | `test_observability.py`, `test_operational_log_search.py` |

## A. Checklist unitaire

Commande de reference :

```bash
uv run pytest -m unit -q
```

- [x] `UT-01` JWT utilisateur valide : verification issuer, signature et shadow user.
- [x] `UT-02` Capacites : passager actif et chauffeur eligible exposes correctement.
- [x] `UT-03` Recherche : biais et limite sont transmis au `MapProvider`.
- [x] `UT-04` Devis : base, distance, duree, confort, surge et commission sont calcules.
- [x] `UT-05` Devis : `quote_id` et expiration a 15 minutes sont produits.
- [x] `UT-06` Creation : un devis valide cree une course avec le paiement choisi.
- [x] `UT-07` Matching : les chauffeurs eligibles sont classes et repartis par vagues de cinq.
- [x] `UT-08` Matching : categorie, confort, zone, partenaire, score et wallet sont appliques.
- [x] `UT-09` Offre : acceptation assigne exactement un chauffeur et ferme les autres offres.
- [x] `UT-10` Arrivee : rayon valide, heure d'arrivee et attente pre-course sont initialises.
- [x] `UT-11` Attente pre-course : trois minutes gratuites puis calcul a la seconde.
- [x] `UT-12` No-show : le chauffeur peut cloturer apres dix minutes.
- [x] `UT-13` Demarrage : code correct demarre la course et debloque le prix chauffeur.
- [x] `UT-14` GPS : lots valides, ordre temporel et idempotence sont respectes.
- [x] `UT-15` Attente en course : vitesse stationnaire, debut, fin et tarif sont calcules.
- [x] `UT-16` Supplements : tarifs forfaitaires et decision passager sont appliques.
- [x] `UT-17` Fin normale : devis fige, attentes et supplements composent le montant.
- [x] `UT-18` Early stop : demande, montant provisoire, confirmation et prix reel fonctionnent.
- [x] `UT-19` Cash : seule la confirmation chauffeur credite le ledger.
- [x] `UT-20` Mobile Money : reseau, nouvelle tentative et webhook idempotent fonctionnent.
- [x] `UT-21` Wallet : solde et ledger refletent les ecritures financieres.
- [x] `UT-22` Top-up : succes DiddiPay credite une seule fois.
- [x] `UT-23` Retrait : devis, frais, destination et reservation du solde fonctionnent.
- [x] `UT-24` Annulation : etat terminal, motif et fermeture des offres sont coherents.
- [x] `UT-25` Notation : chauffeur et passager alimentent leurs scores respectifs.
- [x] `UT-26` Partage : token public temporaire expose uniquement les donnees autorisees.
- [x] `UT-27` SOS : evenement persiste, limite de frequence et notification unique du contact.
- [x] `UT-28` SMS : adaptateurs Senndo/Yellika et idempotence valides.
- [x] `UT-29` DiddiComms : participants et permissions suivent l'etat de la course.
- [x] `UT-30` FCM : enregistrement, envoi d'offre et desinscription d'appareil.
- [x] `UT-31` KYC/KYV : dossier complet, approbation, rejet et nouvelle soumission.
- [x] `UT-32` Disponibilite : profil, vehicule, partenaire et solde sont controles.
- [x] `UT-33` Partenaire : KYC, membres, chauffeurs, vehicules et affectation.
- [x] `UT-34` Backoffice : scopes S2S, acteur humain, audit et idempotence.
- [x] `UT-35` Pilotage : resume, finance, ventilation et sante sont agreges.
- [x] `UT-36` Observabilite : request ID, logs structures et metriques sont emis.

## B. Checklist integration locale/CI

Prerequis : PostgreSQL/PostGIS, Redis, migrations a jour et fournisseurs HTTP
simules ou sandbox. Ne pas utiliser de fournisseur de production.

- [ ] `IT-01` Demarrer PostgreSQL et Redis puis appliquer `alembic upgrade head`.
- [ ] `IT-02` Executer toute la suite `uv run pytest -q` sur une base vide.
- [ ] `IT-03` Reexecuter la suite sans recreer la base pour detecter les fuites d'etat.
- [ ] `IT-04` Valider DiddiFreeID JWKS puis creation du shadow user en base.
- [ ] `IT-05` Valider recherche et devis via le mock DiddiMap sans fallback local.
- [ ] `IT-06` Creer cinq chauffeurs eligibles, ouvrir une vague et accepter avec un seul.
- [ ] `IT-07` Laisser expirer une vague puis verifier l'ouverture automatique de la suivante.
- [ ] `IT-08` Executer arrivee, attente gratuite, attente payante, code et demarrage.
- [ ] `IT-09` Envoyer plusieurs lots GPS, fermer et analyser la trace DiddiMap simulee.
- [ ] `IT-10` Executer une course cash jusqu'au credit du ledger chauffeur.
- [ ] `IT-11` Executer Mobile Money avec webhook signe puis rejouer le webhook.
- [ ] `IT-12` Executer top-up puis retrait avec destination beneficiaire.
- [ ] `IT-13` Executer KYC et KYV avec URLs signees DiddiFiles simulees.
- [ ] `IT-14` Executer le resolver DiddiComms avant et apres cloture de la course.
- [ ] `IT-15` Executer SOS avec Evolution simule, Senndo sandbox et Yellika simule.
- [ ] `IT-16` Executer la projection chauffeur, interrompre le reseau puis reconciler.
- [ ] `IT-17` Executer les routes Pilotage avec un JWT S2S conforme.
- [ ] `IT-18` Verifier metriques Prometheus et correlation des logs par `request_id`.
- [ ] `IT-19` Construire les images Docker backend et documentation.
- [ ] `IT-20` Valider `docker compose config` local et Portainer.

## C. Checklist staging API

### Preflight

- [ ] `STG-00` Noter le commit DiddiGo deploye : `________________`.
- [ ] `STG-01` Noter les versions DiddiMap, DiddiPay, DiddiFiles, DiddiFreeID et DiddiComms.
- [ ] `STG-02` Creer un passager, deux chauffeurs, un admin et un client Pilotage de recette.
- [ ] `STG-03` Verifier `/health`, disponibilite PostgreSQL, Redis et migrations.
- [ ] `STG-04` Verifier les variables SMS, FCM, DiddiMap, DiddiPay et DiddiFiles sans afficher les secrets.
- [ ] `STG-05` Demarrer une collecte de logs avec `request_id`, `ride_id` et `driver_id`.

### Contrats et securite P0

- [ ] `STG-70` Verifier que `GET /openapi.json` expose les routes frontend
  attendues et que Swagger charge sans erreur.
- [ ] `STG-71` Verifier le contrat WebSocket : connexion avec JWT valide,
  rejet handshake `403` sans JWT ou avec JWT invalide.
- [ ] `STG-72` Verifier qu'un utilisateur ne lit ni ne modifie la course d'un
  autre utilisateur.
- [ ] `STG-73` Verifier les erreurs contractuelles critiques : devis expire,
  offre expiree, course deja active, chauffeur non eligible et paiement invalide.
- [ ] `STG-74` Verifier qu'aucun token, secret, telephone complet ou URL signee
  ne sort dans les logs applicatifs, reponses API ou preuves de recette.

### Onboarding et disponibilite

- [ ] `STG-10` Authentifier le passager via DiddiFreeID et lire ses capacites.
- [ ] `STG-11` Creer le profil chauffeur puis televerser les documents dans DiddiFiles.
- [ ] `STG-12` Soumettre et approuver le KYC chauffeur depuis le Backoffice.
- [ ] `STG-13` Creer le vehicule, envoyer les six photos et approuver le KYV.
- [ ] `STG-14` Financer le wallet si necessaire puis passer le chauffeur en ligne.
- [ ] `STG-15` Enregistrer un appareil FCM et ouvrir le WebSocket chauffeur.

### Course cash nominale

- [ ] `STG-20` Rechercher pickup/dropoff avec biais geographique.
- [ ] `STG-21` Creer un devis standard et verifier prix, commission, expiration et `quote_id`.
- [ ] `STG-22` Creer une course cash avec le devis exact.
- [ ] `STG-23` Recevoir l'offre WebSocket/FCM puis l'accepter avec le chauffeur eligible.
- [ ] `STG-24` Envoyer les positions d'approche et declarer l'arrivee dans le rayon.
- [ ] `STG-25` Verifier l'attente gratuite puis une courte attente facturable.
- [ ] `STG-26` Demarrer par code ou QR et verifier l'affichage du prix chauffeur.
- [ ] `STG-27` Envoyer des positions GPS pendant toute la course.
- [ ] `STG-28` Ajouter un supplement bagage et le faire accepter par le passager.
- [ ] `STG-29` Terminer la course et verifier les metriques reelles DiddiMap.
- [ ] `STG-30` Confirmer le cash puis verifier paiement, commission, gain et ledger.
- [ ] `STG-31` Noter la course dans les deux sens et verifier les scores.

### Course Mobile Money nominale

- [ ] `STG-40` Creer et terminer une nouvelle course `mobile_money`.
- [ ] `STG-41` Preparer le paiement avec un reseau supporte.
- [ ] `STG-42` Executer la `next_action` DiddiPay et recevoir le webhook final.
- [ ] `STG-43` Verifier paiement reussi et credit unique du chauffeur.
- [ ] `STG-44` Verifier qu'une relecture/reconciliation ne double aucune ecriture.

### Autres parcours nominaux

- [ ] `STG-50` Demander puis confirmer un arret anticipe avec prix reel.
- [ ] `STG-51` Generer un lien partage et suivre la position sans compte.
- [ ] `STG-52` Creer une conversation DiddiComms pendant la course.
- [ ] `STG-53` Terminer/annuler la course puis verifier la fermeture des nouveaux messages.
- [ ] `STG-54` Enregistrer un contact d'urgence puis declencher le SOS.
- [ ] `STG-55` Verifier livraison WhatsApp Evolution et SMS du fournisseur selectionne.
- [ ] `STG-56` Creer une recharge chauffeur et verifier son credit.
- [ ] `STG-57` Creer un devis de retrait puis un retrait avec destination beneficiaire.
- [ ] `STG-58` Creer un partenaire, approuver son KYC et affecter vehicule/chauffeur.
- [ ] `STG-59` Lire les resumes Pilotage et verifier les totaux avec les courses creees.
- [ ] `STG-60` Retrouver la campagne complete dans les logs et metriques.

### Regression et resilence P4

- [ ] `STG-80` Rejouer la confirmation cash et le webhook Mobile Money : aucun
  second credit de wallet, gain ou mouvement de ledger ne doit apparaitre.
- [ ] `STG-81` Couper puis restaurer le WebSocket pendant une course : la
  relecture REST reconcilie l'etat sans dupliquer une action.
- [ ] `STG-82` Refuser une piece KYC et une piece KYV depuis DiddiAdmin, puis
  renvoyer seulement les pieces refusees et verifier le retour a
  `pending_verification`.
- [ ] `STG-83` Rejouer la meme decision Backoffice avec la meme cle
  d'idempotence, puis avec une payload differente : la premiere est rejouee et
  la seconde est refusee.
- [ ] `STG-84` Verifier les totaux Pilotage : nombre de courses, paiement cash,
  paiement numerique, commission et gain chauffeur correspondent exactement a
  la campagne.

## D. Checklist E2E applications et humains

Utiliser deux telephones physiques minimum. Pour le comportement en arriere-plan,
ajouter un Android avec optimisation batterie active ; ajouter un iPhone des que
l'application iOS est disponible.

### Passager et chauffeur

- [ ] `E2E-01` Le passager se connecte et arrive sur la recherche sans configuration technique.
- [ ] `E2E-02` Les suggestions de lieux apparaissent pendant la saisie et restent pertinentes autour de lui.
- [ ] `E2E-03` Le passager choisit confort et paiement puis comprend le prix et sa duree de validite.
- [ ] `E2E-04` Le chauffeur valide et en ligne recoit l'offre au premier plan.
- [ ] `E2E-05` Le chauffeur recoit aussi la notification lorsque l'application est en arriere-plan.
- [ ] `E2E-06` Le passager suit l'approche et voit l'arrivee sans rafraichissement manuel.
- [ ] `E2E-07` Le compteur d'attente affiche gratuitement les trois premieres minutes puis le montant.
- [ ] `E2E-08` Le QR ou code demarre la course et le prix devient visible au chauffeur.
- [ ] `E2E-09` Les deux utilisateurs voient les changements d'etat en temps reel.
- [ ] `E2E-10` Le passager voit et accepte un supplement avant facturation.
- [ ] `E2E-11` La fin cash est comprise par les deux parties et confirmee uniquement par le chauffeur.
- [ ] `E2E-12` Le paiement Mobile Money ouvre le bon operateur et revient dans l'application.
- [ ] `E2E-13` Le passager et le chauffeur peuvent se noter apres la course.

### Securite et communication

- [ ] `E2E-20` Le proche ouvre le lien partage dans un navigateur sans application ni compte.
- [ ] `E2E-21` La messagerie et l'appel sont disponibles seulement pendant la fenetre autorisee.
- [ ] `E2E-22` Le bouton SOS confirme visuellement l'alerte sans exposer de details techniques.
- [ ] `E2E-23` Le contact recoit WhatsApp et SMS avec la reference utile de la course.
- [ ] `E2E-24` Le support retrouve immediatement l'alerte et ses logs correles.

### Chauffeur professionnel

- [ ] `E2E-30` Le chauffeur photographie et soumet tous ses documents KYC/KYV.
- [ ] `E2E-31` L'application affiche correctement l'attente de validation admin.
- [ ] `E2E-32` Apres approbation, le chauffeur peut passer en ligne sans recreer son compte.
- [ ] `E2E-33` Le wallet affiche solde, gains, top-ups et retraits de facon comprehensible.
- [ ] `E2E-34` Le retrait affiche frais, destination et statut jusqu'a son traitement.

### Backoffice et Pilotage

- [ ] `E2E-40` L'agent retrouve et approuve un dossier KYC/KYV avec URLs signees valides.
- [ ] `E2E-41` L'agent gere partenaire, chauffeur et vehicule sans acces direct a la base.
- [ ] `E2E-42` Le support reconcilie un paiement depuis le Backoffice sans doublon financier.
- [ ] `E2E-43` Pilotage affiche les totaux et ventilations correspondant a la campagne.

## E. Criteres de sortie happy path

Une version est candidate a la production limitee seulement si :

- [ ] Tous les `UT` et `IT` obligatoires sont verts dans la CI du meme commit.
- [ ] Tous les scenarios `STG-10` a `STG-60` applicables sont coches.
- [ ] Le parcours cash et le parcours Mobile Money ont chacun une preuve complete.
- [ ] Le parcours SOS a une preuve WhatsApp et une preuve SMS.
- [ ] Le parcours DiddiComms se ferme correctement apres un etat terminal.
- [ ] Aucun doublon financier n'apparait dans paiement, top-up ou retrait.
- [ ] Les totaux Pilotage correspondent aux donnees metier de la campagne.
- [ ] Aucun secret ou PII n'apparait dans les preuves et logs partages.
- [ ] Tous les blocages restants ont un ticket, un responsable et une decision de lancement.

## F. Scenarios de regression obligatoires

Ces cas ne remplacent pas les happy paths. Ils protegent les risques les plus
couteux avant une livraison.

| ID | Risque | Resultat attendu |
| --- | --- | --- |
| REG-01 | Devis de plus de 15 minutes | `QUOTE_EXPIRED`, aucune course creee. |
| REG-02 | Deux demandes de course du meme passager | Une seule course active ; rejet explicite de la seconde. |
| REG-03 | Deux chauffeurs acceptent la meme offre | Un seul chauffeur assigne ; l'autre recoit un conflit explicite. |
| REG-04 | Chauffeur hors zone, hors ligne ou solde insuffisant | Pas d'offre ; raison metier visible dans les logs. |
| REG-05 | Position GPS invalide | Rejet `422`, jamais un timeout ou un `503`. |
| REG-06 | DiddiMap indisponible | Erreur explicite ; aucun fallback silencieux de prix ou trace. |
| REG-07 | Paiement ou webhook rejoue | Une seule ecriture financiere. |
| REG-08 | Paiement Mobile Money expire | Nouvelle tentative possible, historique de l'ancienne conserve. |
| REG-09 | Message Comms apres annulation/fin | Lecture historique autorisee selon contrat ; nouvel envoi refuse. |
| REG-10 | SOS repete | Limitation appliquee sans supprimer l'alerte initiale. |
| REG-11 | KYC/KYV refuse | Motif, piece concernee et correction attendue visibles au chauffeur. |
| REG-12 | Token expire ou scope S2S insuffisant | `401` ou `403` contractuel ; aucune action partielle. |
| REG-13 | Redemarrage entre evenement et projection | Rejeu idempotent, projection chauffeur reconciliee. |
| REG-14 | Annulation pendant attente active | Action autorisee au bon acteur et attente cloturee proprement. |
| REG-15 | Documents DiddiFiles non accessibles | Le dossier n'est pas approuve et l'erreur est exploitable par le Backoffice. |

## G. Journal des executions

Ajouter une ligne par campagne, meme si elle echoue.

| Date/heure | Environnement | Commit/version | Perimetre | Resultat | Preuve/rapport | Execute par | Blocage/ticket |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-19 | local | arbre de travail `stage` | Suite unitaire (`pytest -m unit -q`) | PASS, 312 tests | sortie terminal locale | Codex | avertissement deprecation Starlette/TestClient, non bloquant |
| 2026-10-15 | local | `4ab8fb6` | Suite pytest complete | PASS, 471 tests | sortie terminal locale | Codex | aucun |
| - | staging | - | - | NON EXECUTE | - | - | - |

## H. Anomalies ouvertes pendant la recette

Ne pas supprimer une ligne resolue ; mettre son statut a `RESOLU` et ajouter le
commit ou ticket de correction.

| ID | Date | Scenario | Gravite | Description | Request/Ride ID | Ticket | Statut |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-PLACEHOLDER | - | - | - | Remplacer cette ligne par la premiere anomalie | - | - | EXEMPLE |

## I. Prochaine execution

- Environnement : `staging`
- Perimetre recommande : `P0`, `P1`, puis `P2` a `P4` selon les integrations disponibles.
- Comptes de recette : `a renseigner sans inscrire les tokens`.
- Fenetre : `a planifier`.
- Responsable : `a assigner`.
