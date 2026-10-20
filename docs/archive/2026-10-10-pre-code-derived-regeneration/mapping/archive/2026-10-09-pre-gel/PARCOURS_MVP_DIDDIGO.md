# Parcours MVP de DiddiGo — carte du code, de la cible et de l'avancement documenté

Relevé du 9 octobre 2026. Branche `feat/pilotage-finance-summary-v1`.

Ce document **décrit**. Il ne juge pas, ne conclut pas, et ne qualifie aucune différence. Ce qui est
déjà codé fait partie du MVP, au même titre que la décision produit. Quand deux sources disent des
choses différentes, les deux apparaissent et c'est au lecteur de trancher.

## Comment lire

La colonne vertébrale est la taxonomie du planning de lancement : les identifiants `PAR-xxx` de
l'onglet *Parcours sources*, explicitement « distincts des UC historiques Jira ». Le planning fournit
aussi toute la chaîne d'avancement :

```
PAR-xxx  →  tâches liées (P / UX / BE / FE / QT)
         →  onglet Backend : fenêtre, effort, état planning, tickets Jira liés
         →  onglet Jira source : statut au 9 octobre 2026
```

**Les deux colonnes de statut.** Le classeur porte son propre instantané Jira, daté du 9 octobre 2026 ;
le relevé live a été fait le même jour. Les deux colonnes coïncident donc sur les 94 tickets cités —
c'est un fait à conserver, pas une redondance : il établit que l'instantané du planning était exact au
moment où il a été pris. Les écarts apparaîtront aux relevés suivants.

**Périmètre.** Les 23 parcours MVP que traverse réellement un passager puis un chauffeur DiddiGo :
4 parcours DiddiGo, 8 Common, 4 DiddiPay, 4 Support, 3 Pilotage.

**Aucun montant.** Les valeurs, seuils et plafonds sont dans
[`PARAMETRES_CONFIGURABLES.md`](PARAMETRES_CONFIGURABLES.md). Ce document nomme les comportements.

### Les use cases et les décisions, et comment ils sont rattachés

Deux taxonomies coexistent et **aucun lien n'est déclaré entre elles** : les `PAR-xxx` du planning —
qui se présentent comme « distincts des UC historiques Jira » — et les `UC-xxx` du corpus de
spécifications. Les rattachements de ce document sont donc construits, pas lus :

- **Use cases → parcours** : rattachement par lot et par persona. Un use case est porté comme
  *majeur* s'il décrit une étape du parcours nominal, et renvoyé aux *cas limites* s'il décrit une
  défaillance, une concurrence ou une reprise. Les cas limites sont nommés mais traités dans une
  passe séparée.
- **Entrées ouvertes → parcours** : rattachement par le **lot d'origine** que chaque registre déclare.
  Les registres ne nomment aucun parcours. Conséquence à connaître : une entrée du lot
  `diddigo-passager` apparaît sur tous les parcours DiddiGo de ce lot, donc **une même décision peut
  se lire sous plusieurs parcours**, et les décomptes ne s'additionnent pas entre parcours.

La colonne **Code au 09/10** des tables de use cases reprend les constats relevés sur la branche
courante, détaillés dans
[`PARCOURS_MVP_COMPLEMENT_UC.md`](PARCOURS_MVP_COMPLEMENT_UC.md). Étiquettes : *Présent*, *Partiel*,
*Absent du code*, *Hors diddi-go*, *À vérifier* — elles décrivent le code seul et ne disent rien de
la conformité à une cible.

### Légende des statuts

| Statut | Sens |
| --- | --- |
| `Done` / `Terminé(e)` | fermé dans Jira |
| `A tester` | **vaut 85 % indicatif** selon le planning ; un ticket terminé ne suffit pas à déclarer un livrable validé |
| `In Progress` / `En cours`, `In Review` | en cours |
| `Attente de admin` | bloqué sur une action d'administration |
| `To Do` / `À faire` | ouvert |
| `V2` | reclassé hors du périmètre courant |

### Ce que chaque source peut et ne peut pas dire

- Planning, onglet *Vérification code* : « Lecture ciblée locale ; aucune preuve d'exécution ou de
  configuration effective en staging/production. »
- Planning, onglet *Pilotage* : « À tester vaut 85 % indicatif dans Jira source. L'avancement d'un
  livrable intégré reste à renseigner après revue ; un ticket terminé ne suffit pas à le déclarer validé. »
- La colonne **Code** ne porte que sur `diddi-go`. Le code de DiddiPay, DiddiFreeID, DiddiMap,
  DiddiSend, DiddiFood et du Backoffice **n'a pas été lu** ; pour ces parcours, seul ce qui vit dans
  `diddi-go` est rapporté et le module propriétaire est nommé.
- `management/specs/etat/avancement.md` : « Le dépôt du frontend mobile n'est accessible ni sous
  `E:/DIDDI AI`, ni sous `E:/AI DIDDI`. » Aucun statut UX ou Front n'est vérifiable dans cet environnement.

---

## Common — entrer dans le service et devenir professionnel

### PAR-001 — Créer son compte et retrouver sa session

**Persona** Consommateur · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Saisie du numéro → code OTP par SMS → accès au profil. Même identité pour Go, Send et Food. Session conservée ou renouvelée ; sinon reconnexion sans perdre l'historique. Messages clairs : code faux/expiré, délai avant renvoi, numéro invalide, panne SMS (pas présentée comme faute de l'utilisateur).

**Tâches liées.** UX001, BE001, FE001, QT001

**Cible produit.** `PROD-007` connexion par téléphone, SMS ou WhatsApp, email en secours. `PROD-002` Common.

**Code dans `diddi-go`.** `POST /v1/auth/register`, `/otp/request`, `/otp/verify`, `/refresh`, `GET /v1/auth/me`. Vérification RS256 locale des jetons DiddiFreeID via JWKS, `identity_issuer=diddifree-id` ; utilisateur fantôme maintenu dans `auth.users`. Codes OTP consommés conservés pour l'audit. Codes d'erreur distincts : `400 OTP_INVALID`, `410 OTP_EXPIRED`, `409 PHONE_ALREADY_REGISTERED`, `401 TOKEN_MISSING|TOKEN_INVALID|TOKEN_EXPIRED|REFRESH_TOKEN_INVALID`. Envoi du code : `# TODO: replace with real SMS delivery. In dev, the OTP is logged.` (`auth/application/services.py`).

**Confluence.** Lot — DiddiFreeID / Identite (950291)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-001 | L'utilisateur cree un compte DiddiFree avec telephone ou email | MVP | Hors diddi-go | `SCRUM-168` Terminé(e) |
| UC-002 | L'utilisateur demande un OTP pour se connecter | MVP | Hors diddi-go | `SCRUM-169` Terminé(e) |
| UC-003 | L'utilisateur valide son OTP et ouvre une session | MVP | Hors diddi-go | `SCRUM-170` Terminé(e) |
| UC-004 | L'utilisateur consulte son profil global | MVP | Hors diddi-go | `SCRUM-171` Terminé(e) |
| UC-006 | L'utilisateur se deconnecte de son compte | MVP | Hors diddi-go | `SCRUM-173` Terminé(e) |
| UC-008 | Un service verifie l'identite d'un utilisateur via DiddiFreeID | MVP | Hors diddi-go | `SCRUM-175` Terminé(e) |

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **4** · Faits à établir : **6** · Contradictions entre deux sources : **1**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| que se passe-t-il si le canal d'envoi du code est indisponible ? existe-t-il un canal de secours ? | — | Produit |
| quelle est la durée de vie d'un code à usage unique, et combien d'essais avant blocage ? | — | Technique |
| un compte suspendu voit-il le motif de sa suspension ? | UC-007 | Produit |
| un utilisateur peut-il changer le téléphone ou le courriel rattaché à son compte, et selon quelle procédure ? | UC-005 | Produit |

*Faits à établir — portée MVP et entrées structurantes, 6 sur 6.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| la durée de vie de 300 s configurée par défaut est-elle la valeur retenue ? | — | Technique |
| le fournisseur d'envoi est-il surchargé sur l'instance de production ? | — | — |
| le maximum de 5 essais configuré par défaut est-il la valeur retenue ? | — | Technique |
| le sel d'empreinte des codes et le fournisseur d'envoi sont-ils surchargés sur l'instance de production ? | — | Technique |
| les durées et seuils configurés par défaut sont-ils les valeurs retenues ? | — | Technique |
| une déconnexion demandée hors ligne invalide-t-elle réellement le jeton côté serveur au retour du réseau, ou seulement localement ? | — | Technique |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 1 sur 1.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| DiddiFreeID écrit par défaut les codes d'authentification en clair dans les journaux ; cela ne peut pas rester vrai en production | — | Technique |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE001** Inscription, session et premier accès aux modules | 2026-10-14 → 2026-10-16 | 2 j-p | À engager | Élevé |

*BE001 — résultat attendu.* Créer automatiquement le profil consommateur local ; utiliser DiddiFreeID ; traiter OTP expiré et session révoquée.

*BE001 — blocage déclaré.* Contrat/intégration à fermer sur staging ; voir tickets liés.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-169` | Done | Done | UC-002 — L'utilisateur demande un OTP pour se connecter |
| `SCRUM-170` | Done | Done | UC-003 — L'utilisateur valide son OTP et ouvre une session |
| `SCRUM-565` | To Do | To Do | [DiddiGo] /v1/auth/otp/verify émet un jeton HS256 local rejeté par les routes  |
| `SCRUM-566` | To Do | To Do | [DiddiGo] IntegrityError sur POST /v1/rides mal classé en 503 DATABASE_UNAVAIL |
| `SCRUM-567` | To Do | To Do | [Cross-module] Auto-provisionner les comptes consommateur (passager/client) de |

---

### PAR-002 — Devenir chauffeur, coursier ou restaurant

**Persona** Chauffeur, coursier, restaurant · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Création du profil métier, envoi des justificatifs, dossier « en attente ». Contrôle du véhicule (chauffeur/coursier). Refus avec motif, correction, nouvelle soumission. Impossible de travailler ou retirer des gains avant validation. Suspension visible, motivée, tracée, avec contestation possible.

**Tâches liées.** P03, UX002, BE002, FE002, QT002, UX003, BE003, FE003, QT003, I02, S01, S03, S05

**Cible produit.** `PROD-002`. Parcours Common du `.docx` : l'activation n'est pas acquise par la seule création du compte Identity.

**Code dans `diddi-go`.** `POST /v1/drivers/profile`, `/vehicle`, `PUT /v1/drivers/me/vehicle`, `POST /v1/drivers/kyc/resubmit`, `POST /v1/drivers/vehicles/{id}/kyv/resubmit`, `GET /v1/drivers/me`, `GET /v1/me/capabilities`. Documents délégués à DiddiFiles, DiddiGo ne conserve que des `file_id` (`ride/infra/diddifiles_client.py`). Personne et véhicule portent des états de validation séparés. Mise en ligne refusée par `403 DRIVER_NOT_VERIFIED` ou `409 NO_ACTIVE_VEHICLE` ; les deux contrôles sont rejoués à l'acceptation d'une course (`ride/application/matching_service.py:222,232`). Statut d'expiration des documents calculé dans `driver_service.py`. Les capacités sont poussées vers DiddiFreeID par une outbox en base avec version de projection, réessai exponentiel et lettre morte (`ride/infra/capability_projection_repository.py`) : un échec de DiddiFreeID ne bloque pas l'approbation.

**Confluence.** Lot — DiddiFree Pro (1179649) · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprint 1

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-018 | Le chauffeur cree son profil chauffeur | MVP | Présent | `SCRUM-183` Terminé(e) |
| UC-019 | Le chauffeur soumet ses documents KYC | MVP | Présent | `SCRUM-184` Terminé(e) |
| UC-020 | Le chauffeur ajoute un vehicule | MVP | Présent | `SCRUM-185` Terminé(e) |
| UC-021 | Le chauffeur soumet les documents du vehicule | MVP | Présent | `SCRUM-186` Terminé(e) |
| UC-270 | Le chauffeur fournit les photos obligatoires du vehicule : quatre cotes, habitacle avant et arriere, coffre | MVP | Présent | `SCRUM-204` Terminé(e) |
| UC-022 | Le chauffeur suit l'etat de validation de son profil | MVP | À vérifier | `SCRUM-187` Terminé(e) |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-007.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **24** · Faits à établir : **17** · Contradictions entre deux sources : **6**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 20 sur 24.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | — | Produit |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | UC-274 | Produit |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | UC-259 | Produit |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | — | Produit |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | — | Produit |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | — | Technique |
| existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | — | Technique |
| la réputation et les points de priorité (voir UC-274) sont-ils attachés au chauffeur ou au véhicule dans ce cas de partage ? | — | Produit |
| *12 autres entrées de même portée* | | |

*Faits à établir — portée MVP et entrées structurantes, 17 sur 17.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | — | Technique |
| ce cas est-il contrôlé côté serveur ? | — | — |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | — | — |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | — | Technique |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | — | Technique |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | — | Technique |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | — | Technique |
| laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | — | Technique |
| *9 autres entrées de même portée* | | |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 6 sur 6.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | — | Produit |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | — | Technique |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | — | — |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | — | Produit |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | — | Produit |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | — | Produit |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE002** Choix de métier et passage client/pro avec une même identité | 2026-10-14 → 2026-10-16 | 1.5 j-p | À engager | Moyen |
| **BE003** Dossiers chauffeur, coursier, restaurant et véhicule | 2026-10-14 → 2026-10-16 | 2 j-p | À engager | Élevé |

*BE002 — résultat attendu.* Valider les capacités et les statuts métier ; préserver un compte avec plusieurs métiers et les suspensions.

*BE003 — résultat attendu.* Fiabiliser justificatifs et validation ; distinguer personne approuvée et véhicule prêt ; activation assistée tracée.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-430` | A tester | A tester | [DiddiFreeID] Registre de capacités et GET /pro/me |
| `SCRUM-431` | Done | Done | [DiddiGo] Publier operational_status chauffeur vers DiddiFreeID |
| `SCRUM-432` | A tester | A tester | [DiddiSend] Synchroniser operational_status courier avec DiddiFreeID |
| `SCRUM-444` | In Progress | In Progress | [DiddiAdmin] Orchestrer le provisioning métier et l’activation des capabilitie |
| `SCRUM-445` | Done | Done | [DiddiFree Pro] Afficher les capabilities et le workflow métier |
| `SCRUM-496` | Done | Done | [DiddiFree Pro / DiddiSend] Aligner le formulaire livreur sur le workflow d’on |
| `SCRUM-510` | A tester | A tester | [DiddiGo] Fiabiliser la projection diddigo/driver vers DiddiFreeID |
| `SCRUM-513` | A tester | A tester | [DiddiGo] Dead-letter pour la projection capabilities : classer 404 USER_NOT_F |
| `SCRUM-466` | A tester | A tester | [DiddiGo] Valider le contrat d’accès Backoffice et la recette KYC staging |
| `SCRUM-470` | A tester | A tester | [DiddiFiles] Autoriser les purposes KYC livreur DiddiSend |
| `SCRUM-519` | A tester | A tester | [DiddiSend] Approuver la personne au review d'onboarding coursier ; le véhicul |
| `SCRUM-520` | A tester | A tester | [DiddiAdmin][DiddiSend] Onboarding assisté par l'opérateur : création + dossie |
| `SCRUM-558` | Attente de admin | Attente de admin | [DiddiFiles][Backoffice] S2S service-client credentials missing — all document |
| `SCRUM-560` | To Do | To Do | [DiddiFreeID] Provisionner un client aud=diddifiles pour DiddiSend |
| `SCRUM-561` | To Do | To Do | [DiddiSend] Migrer DiddiFilesHttpClient vers le token de service DiddiFreeID |
| `SCRUM-563` | To Do | To Do | [DiddiAdmin] Wire DiddiFilesAdapter to the provisioned service client |

---

### PAR-003 — Valider et suspendre des dossiers

**Persona** Opérateur Backoffice · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Consulte les dossiers de son rôle, vérifie les pièces, valide ou suspend. Historique de ses actions (qui, motif, date, résultat). Un retry réseau ne répète pas l'action. Droits limités : un coursier ne voit pas les finances d'un restaurant, la cuisine ne demande pas de retrait.

**Tâches liées.** UX003, BE003, FE003, QT003, UX004, BE004, FE004, QT004, S01, S05, Q02

**Cible produit.** `PROD-037` séparation des pouvoirs. Parcours Common : acteur, motif, date et résultat sur chaque action sensible.

**Code dans `diddi-go`.** Surface S2S Backoffice : `/internal/v1/drivers/kyc`, `/{driver_id}/kyc`, `POST .../kyc/approve|reject`, `POST /internal/v1/drivers/provision`, `PATCH /internal/v1/drivers/{id}/profile-photo`, et 15 routes partenaires sous `/internal/v1/admin/partners/*`. Idempotence par réservation Redis (`core/s2s_command_store.py` : `reserve` / `complete` / `release`), TTL 24 h sur KYC et provisioning. Événements d'audit persistés (`audit/domain/entities.py` : `BackofficeAuditEvent`). Visibilité de l'argent conditionnée au rôle de l'appelant (`_money_visible`, `ride/application/services.py`). Un en-tête `X-User-ID` historique reste accepté.

**Confluence.** Lot — DiddiAdmin (1114113)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-128 | L'administrateur valide, suspend ou refuse un partenaire | MVP | Présent | `SCRUM-319` Terminé(e) |
| UC-007 | L'administrateur suspend ou reactive un compte utilisateur | MVP | Hors diddi-go | `SCRUM-174` Terminé(e) |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-201.

**Décisions à prendre et zones ambiguës.**

Aucune entrée ouverte rattachée à ce parcours par les registres.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE003** Dossiers chauffeur, coursier, restaurant et véhicule | 2026-10-14 → 2026-10-16 | 2 j-p | À engager | Élevé |
| **BE004** Validation, suspension et droits des opérateurs | 2026-10-14 → 2026-10-23 | 1.5 j-p | À engager | Moyen |

*BE003 — résultat attendu.* Fiabiliser justificatifs et validation ; distinguer personne approuvée et véhicule prêt ; activation assistée tracée.

*BE004 — résultat attendu.* Fermer les écarts commandes admin, jetons de service, identité opérateur, audit et absence de double action.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-466` | A tester | A tester | [DiddiGo] Valider le contrat d’accès Backoffice et la recette KYC staging |
| `SCRUM-470` | A tester | A tester | [DiddiFiles] Autoriser les purposes KYC livreur DiddiSend |
| `SCRUM-519` | A tester | A tester | [DiddiSend] Approuver la personne au review d'onboarding coursier ; le véhicul |
| `SCRUM-520` | A tester | A tester | [DiddiAdmin][DiddiSend] Onboarding assisté par l'opérateur : création + dossie |
| `SCRUM-558` | Attente de admin | Attente de admin | [DiddiFiles][Backoffice] S2S service-client credentials missing — all document |
| `SCRUM-560` | To Do | To Do | [DiddiFreeID] Provisionner un client aud=diddifiles pour DiddiSend |
| `SCRUM-561` | To Do | To Do | [DiddiSend] Migrer DiddiFilesHttpClient vers le token de service DiddiFreeID |
| `SCRUM-563` | To Do | To Do | [DiddiAdmin] Wire DiddiFilesAdapter to the provisioned service client |
| `SCRUM-434` | A tester | A tester | [DiddiAdmin] Intégrer la vue capacités globale et les statuts propriétaires |
| `SCRUM-467` | A tester | A tester | [DiddiAdmin] Activer et tester l’administration DiddiFood par S2S en staging |
| `SCRUM-515` | A tester | A tester | [DiddiAdmin] queue_command crashe en 500 sur PostgreSQL (cursor.lastrowid inex |
| `SCRUM-516` | A tester | A tester | [DiddiAdmin] Écrans et commandes DiddiSend en échec : JWT opérateur envoyé au  |
| `SCRUM-518` | Attente de admin | Attente de admin | [DiddiAdmin] Identité opérateur UUID, revue d'onboarding coursier et sources r |
| `SCRUM-529` | A tester | A tester | [DiddiAdmin×DiddiGo] Commandes KYC chauffeur & annulation course échouent (X-R |

---

### PAR-004 — Gérer ses données

**Persona** Tout utilisateur · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Contacter le support, demander la suppression du compte. Si mission active, dette ou solde : parcours de résolution explicite.

**Limites que le planning déclare.** Délais et exceptions de suppression à valider ; distinguer fermeture / effacement / conservation des écritures financières.

**Tâches liées.** P05, UX005, BE005, FE005, QT005

**Cible produit.** `PROD-010` suppression de compte au MVP. `PROD-038` conservation et corpus.

**Code dans `diddi-go`.** Aucune route de suppression de compte parmi les 124 routes exposées. `GET`/`PUT`/`DELETE /v1/me/emergency-contact` gère le contact d'urgence. Wallet et grand livre chauffeur exposés (`/v1/drivers/me/wallet`, `/ledger`), donc le solde et la dette sont lisibles, sans parcours de résolution rattaché à une demande de suppression.

**Confluence.** Lot — Compte, donnees personnelles et conformite (1048577)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-196 | L'utilisateur supprime son compte et demande l'effacement de ses donnees | MVP | Absent du code | `SCRUM-113` Terminé(e) |
| UC-197 | L'utilisateur accepte des CGU et une politique de confidentialite versionnees | MVP | Absent du code | `SCRUM-114` Terminé(e) |

3 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-333, UC-334, UC-335.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **15** · Faits à établir : **6** · Contradictions entre deux sources : **1**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 13 sur 15.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| la durée de conservation de chaque type de donnée — réponse partielle du 14/09, voir decisions-actees.md | — | — |
| quelle est la durée de conservation de chaque type de donnée — pièces d'identité, traces brutes, traces agrégées, journaux, pièces comptables ? — réponse partielle du 14/09, voir decisions-actees.md : pièces comptables 10 ans ; anonymisation après 1 an, ou 60 jours sur demande de suppression ; données clients 12 mois ; traces brutes 6 mois ; pièces d'identité tant que le compte est actif, +3 mois après suspension permanente. Traces agrégées et journaux : non répondu, reste ouvert | UC-200, UC-338 | Juridique |
| une déclaration ou une autorisation préalable ARTCI est-elle requise, et laquelle ? | — | Juridique |
| que se passe-t-il si l'anonymisation réussit dans certains services et échoue dans d'autres — retry automatique, état intermédiaire visible, alerte ? | — | Technique |
| quel délai légal s'applique à une demande d'accès ou d'effacement, et à partir de quel événement court-il ? | UC-340 | Juridique |
| quel est le délai de grâce entre la demande de suppression et l'anonymisation définitive ? | UC-335 | Produit |
| quel format de fichier est attendu pour l'export (JSON structuré, PDF lisible, les deux) ? | — | Produit |
| quelles données restent après anonymisation, et sous quelle forme, pour satisfaire la conservation comptable OHADA ? | UC-333 | Juridique |
| *5 autres entrées de même portée* | | |

*Faits à établir — portée MVP et entrées structurantes, 6 sur 6.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| des conditions d'utilisation et une politique de confidentialité existent-elles déjà sous une forme quelconque, prêtes à être versionnées ? | — | Juridique |
| l'analyse de trace existante dans DiddiMap produit-elle déjà une agrégation par segment et tranche horaire, ou un autre type de résultat ? | — | Technique |
| le journal d'audit du back-office enregistre-t-il les lectures de données personnelles, ou seulement les actions de modification ? | — | Technique |
| le texte de justification présenté à l'utilisateur et soumis aux magasins d'applications existe-t-il déjà, ou reste-t-il à rédiger ? | — | Produit |
| quel service porte l'orchestration d'une demande d'export ou d'anonymisation, et comment il connaît la liste des services à interroger | — | Technique |
| quel service porte l'orchestration de cette vérification croisée entre DiddiGo, DiddiSend et DiddiPay ? | — | Technique |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 1 sur 1.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| la décision du 14/09 dit que les traces envoyées à DiddiMap sont anonymisées ; le code de DiddiGo transmet la trace entière, extrémités comprises, et ce use case demande précisément de retirer ces extrémités | — | Juridique |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE005** Suppression de compte et résolution des soldes ou missions | 2026-10-14 → 2026-10-23 | 1.5 j-p | À engager | Moyen |

*BE005 — résultat attendu.* Appliquer fermeture/effacement et conserver les écritures nécessaires ; traiter mission active, dette et solde.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-120` | To Do | To Do | UC-334 — Le système refuse une demande de suppression tant qu'une mission/un s |

---

## Common — chercher, recevoir une offre, garder une trace

### PAR-005 — Trouver une destination par texte ou par voix

**Persona** Client · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Champ de recherche + micro : la voix est transcrite dans le champ, corrigeable. Le client choisit le lieu, vérifie la carte, confirme le devis. La voix ne choisit pas seule entre deux lieux homonymes et ne déclenche aucune commande. Si micro refusé / réseau faible : clavier toujours dispo.

**Limites que le planning déclare.** Langues du lancement et lieux d'Abidjan pour la recette à fixer.

**Tâches liées.** P05, UX006, BE006, FE006, QT006

**Cible produit.** `PROD-018` dictée.

**Code dans `diddi-go`.** `GET /v1/places/search` (`ride/presentation/places_router.py`), couvert par `tests/test_places_search.py`. La transcription vocale est côté application : rien dans `diddi-go` ne reçoit d'audio ni ne transcrit.

**Confluence.** Lot — DiddiMap / Cartographie (1277953)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-144 | Un service recherche un lieu et obtient des suggestions | MVP | Hors diddi-go | `SCRUM-231` Terminé(e) |

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **4** · Faits à établir : **3** · Contradictions entre deux sources : **3**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 3 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le tricycle utilisé par DiddiSend relève-t-il du profil moto ou d'un profil propre ? | UC-148 | Produit |
| que voit le passager quand le temps d'arrivée estimé n'est pas disponible ? | UC-147 | Produit |
| quels critères définissent une position aberrante — vitesse, précision, saut de distance ? | UC-149 | Technique |

*Faits à établir — portée MVP et entrées structurantes, 3 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| DiddiGo transmet l'identifiant de trace sous forme de chaîne, DiddiMap l'attend sous forme d'entier ; cette conversion est-elle sûre ? | — | Technique |
| le format des traces correspond dans le code ; un test de bout en bout en staging reste à faire | — | Technique |
| le format des traces DiddiGo correspond au schéma DiddiMap dans le code, mais l'écart signalé le 31/08 n'a pas été confirmé résolu par un test de bout en bout en staging | — | — |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 3 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case décrit un temps d'arrivée estimé qui se met à jour pendant la course ; aucun recalcul n'existe | — | Technique |
| DiddiMap valide un profil de véhicule à l'entrée du calcul d'itinéraire mais construit toujours l'appel au moteur avec le profil configuré globalement ; un itinéraire moto est en réalité un itinéraire voiture | — | — |
| DiddiMap valide un profil de véhicule puis construit toujours l'appel avec le profil configuré globalement | — | Technique |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE006** Recherche de destination par texte et dictée | 2026-10-14 → 2026-10-23 | 0.5 j-p | À engager | Moyen |

*BE006 — résultat attendu.* Configurer le service retenu et empêcher la conservation audio non approuvée ; aucun ordre déclenché par la dictée.

Aucun ticket Jira déclaré par le planning pour ce livrable.

---

### PAR-006 — Conserver des échantillons vocaux (option)

**Persona** Client · **Phase source** MVP · **Module** Common · **Traitement planning** Option non activée tant que conservation non arbitrée.

**Attendu, texte du planning.** Option, jamais obligatoire pour réserver. Finalité expliquée avant activation, choix modifiable (opt-out), accès limité. Aucun entraînement de modèle implicite.

**Limites que le planning déclare.** Durée, suppression, hébergement, sous-traitants, sort des anciens échantillons à arbitrer.

**Tâches liées.** P05, UX006, BE006, FE006, QT006

**Cible produit.** `PROD-019` corpus vocal.

**Code dans `diddi-go`.** Aucune surface de conservation d'échantillons vocaux dans `diddi-go`.

**Confluence.** Lot — Compte, donnees personnelles et conformite (1048577)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Aucune entrée ouverte rattachée à ce parcours par les registres.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE006** Recherche de destination par texte et dictée | 2026-10-14 → 2026-10-23 | 0.5 j-p | À engager | Moyen |

*BE006 — résultat attendu.* Configurer le service retenu et empêcher la conservation audio non approuvée ; aucun ordre déclenché par la dictée.

Aucun ticket Jira déclaré par le planning pour ce livrable.

---

### PAR-007 — Recevoir une offre et suivre une mission

**Persona** Professionnel, client · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Offre claire avec infos pour accepter/refuser. Notifications testées (app ouverte, arrière-plan, téléphone verrouillé). Client informé des changements de statut sans recharger. Contact par appel entre parties. Une offre déjà attribuée ne peut plus être acceptée.

**Limites que le planning déclare.** Numéro masqué ou appel direct : à choisir.

**Tâches liées.** P03, P05, UX007, BE007, FE007, QT007

**Cible produit.** `PROD-016` écrans et communication : appel retenu, messagerie et appels Internet en V1.

**Code dans `diddi-go`.** WebSocket `GET /v1/ws` (`ride/presentation/websocket.py`) avec les événements `ride.new_request`, `ride.status_changed`, `ride.driver_location`, `ride.no_driver_found`, `ride.waiting_changed`, `ride.waiting.auto_stopped`, `driver.location_push`. Push FCM derrière `push_enabled`, **à `false` par défaut** (`core/settings.py:99`). Offre déjà attribuée : `409 RIDE_ALREADY_MATCHED` ; offre expirée : `409 OFFER_EXPIRED` ; offre adressée à un autre chauffeur : `403 OFFER_NOT_YOURS`. Aucune route de messagerie ; le contact se fait hors application.

**Confluence.** Lot — Notifications et canaux (1474561) · Lot — Communication en mission (753685)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-025 | Le chauffeur recoit une proposition de course | MVP | Partiel | `SCRUM-190` Terminé(e) |
| UC-156 | Le pro est reveille par un son et une vibration sur une offre, ecran verrouille | MVP | Partiel | `SCRUM-304` À faire |
| UC-157 | L'utilisateur recoit une notification quand l'app est en arriere-plan ou fermee | MVP | Partiel | `SCRUM-305` Terminé(e) |
| UC-158 | L'utilisateur recoit une notification sur iPhone | MVP | Partiel | `SCRUM-306` À faire |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-012.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **12** · Faits à établir : **4** · Contradictions entre deux sources : **2**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 2 sur 12.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| que fait le système quand aucun appareil n'est enregistré pour un pro à qui une offre est destinée ? | UC-156 | Produit |
| quel canal est prioritaire pour un code destinataire — SMS ou WhatsApp — et lequel sert de secours ? | UC-159 | Produit |

*Faits à établir — portée MVP et entrées structurantes, 2 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| est-il prévu de mutualiser l'envoi de notifications entre services, ou chaque service reste-t-il autonome ? | — | Technique |
| un appareil iPhone est-il enregistré avec un jeton FCM valide, ou l'application iOS n'enregistre-t-elle rien du tout ? | — | Technique |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 1 sur 2.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case est marqué priorité absolue depuis le 31/08 ; ni la charge envoyée par le serveur ni l'écran d'offre ne portent aujourd'hui de son ou de vibration | — | Technique |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE007** Notifications, offres et contact en mission | 2026-10-14 → 2026-10-23 | 1.5 j-p | À engager | Moyen |

*BE007 — résultat attendu.* Publier les événements par audience ; livraison Food via Send ; rejet d’offres périmées.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-304` | To Do | To Do | UC-156 — Le pro est réveillé par un son et une vibration sur une offre, écran  |
| `SCRUM-305` | Done | Done | UC-157 — L'utilisateur reçoit une notification quand l'app est en arrière-plan |
| `SCRUM-306` | To Do | To Do | UC-158 — L'utilisateur reçoit une notification sur iPhone |
| `SCRUM-533` | Done | Done | [Plateforme] Convention FCM data-only (réveil app) : valider iOS puis générali |
| `SCRUM-534` | To Do | To Do | [Plateforme] Convention FCM par audience (data-only vs notification) + corrige |
| `SCRUM-552` | A tester | A tester | [Archi DiddiSend/DiddiFood] Décider le canal WS des offres de livraison food a |

---

### PAR-008 — Garder un historique exploitable

**Persona** Support, système · **Phase source** MVP · **Module** Common · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Chaque mission/opération financière laisse une trace (création, attribution, réalisation, annulation, paiement, incident, correction), rejouable sans doublon. Pas de points ni de DiddiScore au MVP.

**Tâches liées.** UX008, BE008, FE008, QT008, BE026, FE026, QT026, Q02

**Cible produit.** `PROD-008` historique vérifié et socle anti-fraude dès le MVP. `PROD-011` reprise après fermeture.

**Code dans `diddi-go`.** Historique des transitions persisté (`RideStatusTransition`, `ride/domain/entities.py:415-423`) avec origine, destination, horodatage et métadonnées. `log_event()` (`core/observability.py`) émet un événement métier JSON depuis 128 points du code. Identifiant de requête propagé (`current_request_id`). `GET /v1/rides` liste l'historique ; `GET /v1/admin/logs/rides/{id}` et `/drivers/{id}` interrogent Loki (`observability/infra/loki.py`). Finalisation de course idempotente, journalisée `ride.completion.retry`. Contextes de retour de paiement consommables une seule fois (`payment/application/return_contexts.py`).

**Confluence.** Lot — Historique, recus et justificatifs (1409025) · Lot — Reseau degrade et continuite (1572865)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-245 | Le passager consulte l'historique de ses courses | MVP | Présent | `SCRUM-275` Terminé(e) |
| UC-246 | Le passager consulte le detail d'une course passee : prix, duree reelle, distance, mode de paiement, note | MVP | Présent | `SCRUM-276` À faire |

3 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-320, UC-319, UC-321.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **10** · Faits à établir : **1** · Contradictions entre deux sources : **7**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 3 sur 10.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| au bout de combien de temps sans position un véhicule est-il considéré comme silencieux, et l'alerte part-elle vers qui ? — réponse partielle du 14/09, voir decisions-actees.md : seuil retenu : 5 minutes. Destination de l'alerte : proposition Claude dans decisions-actees.md, en attente de validation | UC-324 | Produit |
| que fait le système d'une action rejouée dont l'horodatage est hors tolérance — rejet, correction, acceptation signalée ? | UC-321 | Produit |
| quel écart maximal est toléré entre l'horloge du téléphone et celle du serveur ? | UC-321 | Technique |

*Faits à établir — portée MVP et entrées structurantes, 1 sur 1.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| l'événement de position diffusé par le canal temps réel de DiddiGo porte-t-il l'horodatage de la mesure, ou seulement celui de la diffusion ? | — | Technique |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 1 sur 7.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case exige de borner l'horloge du téléphone ; les horodatages envoyés par l'application sont acceptés sans aucun contrôle | — | Technique |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE008** Historique métier, traces et reprise sans doublon | 2026-10-14 → 2026-10-23 | 1.5 j-p | À engager | Moyen |
| **BE026** Rapprochement quotidien des encaissements, gains et espèces | 2026-10-19 → 2026-10-23 | 1 j-p | À engager | Moyen |

*BE008 — résultat attendu.* Corréler mission, paiement et événements ; assurer rejeu sans double mouvement et historique consultable.

*BE026 — résultat attendu.* Fournir journal et extraction minimum des opérations métiers/Pay ; conserver les écarts jusqu’à résolution.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-371` | To Do | To Do | UC-320 — Le système rejoue les actions en attente à la reconnexion sans doublo |
| `SCRUM-438` | Done | Done | DiddiGo: rendre la finalisation de course idempotente lors des retries |
| `SCRUM-480` | A tester | A tester | [DiddiSend][Interne S6] Fraîcheur, recette consommateurs et retrait legacy |
| `SCRUM-101` | Revue en cours | In Review | UC-312 — Un responsable enregistre le reversement d'espèces d'un coursier et s |
| `SCRUM-454` | Revue en cours | In Review | [DiddiSend] Publier le pickup financier et comptabiliser la dette cash Food |
| `SCRUM-483` | Done | Done | [DiddiSend][Interne S5] Exposer finance-summary et health-summary |
| `SCRUM-487` | A tester | A tester | [DiddiPay][UAT] Recette backend DiddiAdmin, Pilotage et wallet legacy |
| `SCRUM-492` | To Do | To Do | [UAT DiddiPay] Vérifier settlement et audit Backoffice |

---

## DiddiGo — la course

### PAR-016 — Commander et effectuer une course

**Persona** Passager, chauffeur · **Phase source** MVP · **Module** DiddiGo · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Départ + destination (saisie ou voix), estimation, confirmation. Recherche d'un chauffeur éligible, offre, acceptation, suivi de l'approche, arrivée, début, fin. Même mission des deux côtés. Offre expirée, refus, aucun chauffeur, perte de connexion : issue explicite et reprise cohérente.

**Tâches liées.** UX014, BE014, FE014, QT014, I02, S03, S05, S07

**Cible produit.** `PROD-015` confort, devis et demande. `PROD-027` recherche en trois phases et absence avant départ. `PROD-013` début de course et secours GPS. `PROD-011` reprise après fermeture. `PROD-016` écrans.

**Code dans `diddi-go`.** `POST /v1/rides/pricing/estimate` (`ride/application/services.py:84-114`) : estimation DiddiMap, barème lu en base sinon défauts de code ; réponse **non persistée**, sans identifiant de devis ni date de validité. `POST /v1/rides` crée la course en `requested` et **fige** barème, taux de commission et niveau de confort sur la course (`services.py:160`). Matching par vagues d'offres : rayon élargi par pas, budget horloge global, reclassement d'une liste courte par temps de trajet DiddiMap qui **retombe sur l'ordre de distance** si DiddiMap est indisponible (`settings.py:54-57`). Attribution exclusive par `SET NX` Redis plus contrainte en base. Machine à états : `requested` → `matched` → `driver_en_route` → `in_progress` → `completed`, avec `waiting` atteignable depuis `in_progress`, et `no_driver_found` terminal (`ride/domain/entities.py:19-66`). Il n'existe pas de statut d'arrivée du chauffeur : `driver_en_route` passe directement à `in_progress`, et ce passage ne vérifie que l'identité de l'acteur puis ouvre la trace DiddiMap (`services.py:316-318`). Positions : `POST /v1/rides/{id}/location-samples`. Partage : `POST /v1/rides/{id}/share-link`, `GET /v1/rides/shared/{token}`. À la fin de course, recalcul réel du trajet ; si DiddiMap échoue, la course se termine avec le tarif verrouillé et le statut d'analyse de trace est marqué en erreur. Quatre codes DiddiMap distincts : `DIDDIMAP_UNAVAILABLE`, `DIDDIMAP_INVALID_RESPONSE`, `DIDDIMAP_AUTHENTICATION_FAILED`, `DIDDIMAP_BUSINESS_ERROR`.

**Confluence.** Lot — DiddiGo / Passager (917523), epic SCRUM-64, Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), epic SCRUM-65, Sprints 1 et 2 · Lot — Matching et Priorite (1441793)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-009 | Le passager estime le prix d'une course | MVP | Présent | `SCRUM-212` Terminé(e) |
| UC-254 | Le passager choisit son mode de paiement avant de commander | MVP | Présent | `SCRUM-222` Terminé(e) |
| UC-010 | Le passager commande une course | MVP | Présent | `SCRUM-213` Terminé(e) |
| UC-011 | Le passager suit l'etat de sa course | MVP | Présent | `SCRUM-214` Terminé(e) |
| UC-023 | Le chauffeur passe en ligne | MVP | Présent | `SCRUM-188` Terminé(e) |
| UC-024 | Le chauffeur passe hors ligne | MVP | Présent | `SCRUM-189` Terminé(e) |
| UC-025 | Le chauffeur recoit une proposition de course | MVP | Partiel | `SCRUM-190` Terminé(e) |
| UC-026 | Le chauffeur accepte une course | MVP | Présent | `SCRUM-191` Terminé(e) |
| UC-028 | Le chauffeur envoie sa position pendant la course | MVP | Présent | `SCRUM-193` Terminé(e) |
| UC-029 | Le chauffeur met a jour les etapes de la course | MVP | Présent | `SCRUM-194` Terminé(e) |
| UC-103 | Le systeme selectionne les chauffeurs eligibles autour du pickup | MVP | Présent | `SCRUM-283` Terminé(e) |
| UC-105 | Le systeme classe les pros selon distance, disponibilite, vehicule et performance | MVP | Présent | `SCRUM-285` A tester |
| UC-181 | Le passager voit la decomposition du prix : base, distance, duree | MVP | Présent | `SCRUM-325` Terminé(e) |
| UC-145 | Un service calcule un itineraire, une distance et une duree | MVP | Hors diddi-go | `SCRUM-232` Terminé(e) |
| UC-146 | Un service envoie ses traces GPS dans le format commun impose par DiddiMap | MVP | Présent | `SCRUM-233` À faire |

24 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-012, UC-027, UC-107, UC-253, UC-255, UC-256, UC-278, UC-279, UC-280, UC-281, UC-282, UC-283, UC-284, UC-286, UC-287, UC-112, UC-147, UC-322, UC-323, UC-163, UC-165, UC-166, UC-167, UC-168.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **96** · Faits à établir : **65** · Contradictions entre deux sources : **22**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 89 sur 96.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| quel est le barème de points de priorité, sa fenêtre de calcul et le score de départ d'un nouveau pro ? | UC-108, UC-109, UC-283, UC-285 | Produit |
| quel est le délai d'acceptation d'une offre ? | UC-278, UC-279, UC-282 | Produit |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | — | Produit |
| quel plafond limite l'effet de la priorité par rapport à la proximité ? — réponse partielle du 14/09, voir decisions-actees.md : réponse reçue porte sur un seuil de suspension de compte à 50 pts, pas sur le plafond de classement demandé ici ; proposition Claude disponible dans decisions-actees.md | UC-284 | Produit |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | UC-274 | Produit |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | UC-259 | Produit |
| à partir de quel âge la position affichée est-elle présentée comme ancienne ? | — | Produit |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | — | Produit |
| *81 autres entrées de même portée* | | |

*Faits à établir — portée MVP et entrées structurantes, 65 sur 65.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | — | Technique |
| un second appel à la route d'alerte doit-il être refusé explicitement plutôt que d'écraser le premier ? | — | Technique |
| à quel moment exact le paiement d'une course est-il capturé ? | — | Technique |
| ce cas est-il contrôlé côté serveur ? | — | — |
| ce contrôle doit-il s'exécuter à l'estimation, à la création, ou aux deux moments ? | — | Technique |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | — | — |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | — | Technique |
| ce taux d'annulation est-il le même champ que celui déjà utilisé par le score de réputation (`scoring_service.py`), ou un calcul distinct propre à la priorité ? | — | Technique |
| *57 autres entrées de même portée* | | |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 22 sur 22.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| la décision du 31/08 prévoit que le contact d'urgence est prévenu par SMS ou WhatsApp avec un lien ; l'alerte n'envoie aujourd'hui aucun message à personne | — | — |
| la décision du 31/08 prévoit une notification du contact d'urgence ; l'alerte n'envoie aucun message | — | Produit |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | — | Produit |
| ce use case décrit un temps d'arrivée estimé qui se met à jour pendant la course ; aucun recalcul n'existe | — | Technique |
| ce use case exige de borner l'horloge du téléphone ; les horodatages envoyés par l'application sont acceptés sans aucun contrôle | — | Technique |
| DiddiMap valide un profil de véhicule à l'entrée du calcul d'itinéraire mais construit toujours l'appel au moteur avec le profil configuré globalement ; un itinéraire moto est en réalité un itinéraire voiture | — | — |
| DiddiMap valide un profil de véhicule puis construit toujours l'appel avec le profil configuré globalement | — | Technique |
| l'instant de mesure de la position est exposé au tiers qui ouvre un lien de partage public, mais pas au passager dans son application | — | Technique |
| *14 autres entrées de même portée* | | |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE014** Course de la demande à la fin du trajet | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE014 — résultat attendu.* Fiabiliser attribution, position, états, absence de chauffeur et finalisation ; vérifier intégration DiddiMap.

*BE014 — blocage déclaré.* Contrat/intégration à fermer sur staging ; voir tickets liés.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-188` | Done | Done | UC-023 — Le chauffeur passe en ligne |
| `SCRUM-190` | Done | Done | UC-025 — Le chauffeur reçoit une offre de course |
| `SCRUM-191` | Done | Done | UC-026 — Le chauffeur accepte une course |
| `SCRUM-193` | Done | Done | UC-028 — Le chauffeur envoie sa position pendant la course |
| `SCRUM-194` | Done | Done | UC-029 — Le chauffeur met à jour les étapes de la course |
| `SCRUM-437` | Done | Done | DiddiGo: ne pas bloquer la fin de course si DiddiMap retourne ignore_for_scori |
| `SCRUM-438` | Done | Done | DiddiGo: rendre la finalisation de course idempotente lors des retries |
| `SCRUM-441` | To Do | To Do | DiddiMap: publier un contrat idempotent pour finish/analyze des traces service |
| `SCRUM-442` | Done | Done | Frontend: envoyer les positions GPS de course en continu et sans doublons |
| `SCRUM-524` | A tester | A tester | Backend requis — Endpoints manquants DiddiGo Pro chauffeur (3 tickets frontend |
| `SCRUM-536` | To Do | To Do | [DiddiGo Frontend Consumer] Blocage backend — SCRUM-441 (DiddiMap contrat idem |
| `SCRUM-567` | To Do | To Do | [Cross-module] Auto-provisionner les comptes consommateur (passager/client) de |

---

### PAR-017 — Gérer attente, escales et annulation

**Persona** Passager, chauffeur · **Phase source** MVP · **Module** DiddiGo · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Attente facturée et escales : début/fin visibles, supplément, nouveau montant. Pas de double comptage après reconnexion. Annulation : qui, à quelle étape, quelles conséquences. Incident/urgence signalable vers le circuit humain.

**Limites que le planning déclare.** Temps gratuit, tarifs, accord du client à formaliser.

**Tâches liées.** UX015, BE015, FE015, QT015

**Cible produit.** `PROD-012` arrivée et attente de prise en charge. `PROD-026` attente en escale. `PROD-014` annulation et fin anticipée. `PROD-036` panne, accident et remplacement.

**Code dans `diddi-go`.** `POST /v1/rides/{id}/waiting/start` et `/stop` (`services.py:366-453`) : réservé au chauffeur assigné ou à un admin, exige `in_progress` (`409 WAITING_INVALID_RIDE_STATUS`), exige une vitesse GPS (`409 WAITING_TELEMETRY_REQUIRED`) sous le seuil de véhicule arrêté (`409 VEHICLE_NOT_STOPPED`, la réponse porte la vitesse mesurée et le maximum admis), refuse une télémétrie plus ancienne que son TTL Redis, et est idempotent si l'attente est déjà active. La facturation part de `waiting_started_at` au tarif par minute, **sans franchise gratuite** dans ce chemin. Reprise de course : `PATCH /status` vers `in_progress` est refusé (`409 WAITING_STOP_ENDPOINT_REQUIRED`) ; `waiting` → `completed` arrête l'attente automatiquement. Événement `ride.waiting.auto_stopped`. `POST /v1/rides/{id}/stops` et `/supplements` ajoutent escales et suppléments (`422 INVALID_SUPPLEMENT_AMOUNT`), chaque supplément étant une ligne rattachée au prix (`RideStop`, `RideSupplement`, `ride/infra/repositories.py`). `POST /v1/rides/{id}/cancel` : motif dans `VALID_CANCEL_REASONS` sinon `422`, refus sur course terminée, déjà annulée ou sans chauffeur trouvé, arrêt de l'attente si active, statut cible distinct passager/chauffeur, motif persisté, issue versée au moteur de priorité. **Aucune facturation n'est produite par une annulation**, quel que soit l'état de départ ; il n'existe pas de notion de fin anticipée. `POST /v1/rides/{id}/emergency` et le contact d'urgence (`/v1/me/emergency-contact`).

**Confluence.** Lot — DiddiGo / Passager (917523), Sprint 3 · Lot — DiddiGo / Chauffeur (1245185), Sprint 2 · Lot — Urgence et securite des personnes (393217)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-271 | Le chauffeur active le mode attente, bloque tant que le vehicule roule | MVP | Présent | `SCRUM-205` Terminé(e) |
| UC-272 | Le chauffeur enregistre une escale demandee oralement et fait valider le surcout par le passager | MVP | Présent | `SCRUM-206` Terminé(e) |
| UC-258 | Le passager demande un arret et voit le surcout d'attente s'appliquer en direct | MVP | Présent | `SCRUM-226` À faire |
| UC-259 | Le passager ajoute une escale, voit le surcout et le valide avant qu'il soit applique | MVP | Présent | `SCRUM-227` À faire |
| UC-301 | Le systeme ne facture le temps d'attente que lorsque le vehicule est reellement a l'arret | MVP | Présent | `SCRUM-333` À faire |
| UC-304 | Le systeme conserve chaque supplement comme une ligne distincte rattachee a la course | MVP | Présent | `SCRUM-336` À faire |
| UC-013 | Le passager annule une course | MVP | Présent | `SCRUM-216` Terminé(e) |
| UC-015 | Le passager declenche une alerte d'urgence | MVP | Présent | `SCRUM-218` Terminé(e) |
| UC-169 | Le contact d'urgence choisi est prevenu par SMS ou WhatsApp avec un lien de suivi | MVP | Présent | `SCRUM-6` Terminé(e) |

4 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-257, UC-273, UC-303, UC-170.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **78** · Faits à établir : **46** · Contradictions entre deux sources : **19**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 61 sur 78.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | — | Produit |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | UC-274 | Produit |
| quel est le tarif du mode attente ? | — | Produit |
| quelle est la grille tarifaire de lancement, par ville et par profil ? | — | Produit |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | UC-259 | Produit |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | — | Produit |
| combien de temps la demande « prévenez-moi » reste-t-elle active ? — réponse partielle du 14/09, voir decisions-actees.md : question non comprise par l'équipe lors de la relecture ; clarification apportée dans decisions-actees.md, reste ouverte | — | Produit |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | — | Produit |
| *53 autres entrées de même portée* | | |

*Faits à établir — portée MVP et entrées structurantes, 45 sur 46.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | — | Technique |
| un second appel à la route d'alerte doit-il être refusé explicitement plutôt que d'écraser le premier ? | — | Technique |
| à quel moment exact le paiement d'une course est-il capturé ? | — | Technique |
| ce cas est-il contrôlé côté serveur ? | — | — |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | — | — |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | — | Technique |
| comportement réel d'une course créée avec une valeur scheduled_at dans le futur | — | Technique |
| correspondance entre ces noms d'écran et les écrans réels de l'application client | — | Technique |
| *37 autres entrées de même portée* | | |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 17 sur 19.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| la décision du 31/08 prévoit que le contact d'urgence est prévenu par SMS ou WhatsApp avec un lien ; l'alerte n'envoie aujourd'hui aucun message à personne | — | — |
| la décision du 31/08 prévoit une notification du contact d'urgence ; l'alerte n'envoie aucun message | — | Produit |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | — | Produit |
| l'instant de mesure de la position est exposé au tiers qui ouvre un lien de partage public, mais pas au passager dans son application | — | Technique |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | — | Technique |
| le code applique un taux de commission de 8 %, la décision du 14/09 fixe 10 % | — | Produit |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | — | — |
| le code fixe la durée de vie du lien de partage à 24 h via la constante _SHARE_TTL_HOURS, la décision du 31/08 dit 20 minutes après la fin de la course | — | Produit |
| *9 autres entrées de même portée* | | |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE015** Attente facturée, escales, annulation et signalement urgent | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE015 — résultat attendu.* Livrer attente et escales MVP avec tarif décidé ; éviter double comptage ; traiter annulation et alerte.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-6` | Done | Done | UC-169 — Notifier le contact d'urgence par SMS/WhatsApp avec lien de suivi |
| `SCRUM-7` | To Do | To Do | UC-170 — Un seul déclenchement d'urgence compté par course |
| `SCRUM-524` | A tester | A tester | Backend requis — Endpoints manquants DiddiGo Pro chauffeur (3 tickets frontend |
| `SCRUM-537` | V2 | V2 | [DiddiGo] Suppléments tarifaires automatiques (recalcul route DiddiMap) — évol |

---

### PAR-018 — Payer et retrouver ses gains

**Persona** Passager, chauffeur · **Phase source** MVP · **Module** DiddiGo · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Paiement numérique ou cash. Commission Go 18 %. Cash : chauffeur encaisse, commission inscrite dans son wallet. Numérique : gains crédités seulement après confirmation. Chauffeur voit solde, gains, commissions, mouvements ; recharge ; voit pourquoi il est bloqué. Retrait : montant, bénéficiaire, frais, net, confirmation, suivi ; pas de double transfert.

**Limites que le planning déclare.** Assiette et arrondis de la commission à finaliser.

**Tâches liées.** P02, UX016, BE016, FE016, QT016

**Cible produit.** `PROD-004` commissions. `PROD-005` moyens visibles. `PROD-030` paiement à la fin. `PROD-031` changement de moyen et double paiement. `PROD-032` retraits sans minimum métier. `PROD-040` impayés cloisonnés par module. `PROD-003` socle financier.

**Code dans `diddi-go`.** `final_fare = base + waiting_fee + supplements_total`, puis `platform_commission = final_fare × commission_rate` et `driver_payout_estimate = final_fare − platform_commission` (`services.py:349-351`). Le taux est figé sur la course à sa création, donc un changement de valeur n'affecte que les courses postérieures. `POST /v1/payments/{ride_id}/prepare` (PaymentIntent DiddiPay), `POST /v1/payments/{ride_id}/confirm-cash`, `GET /v1/payments/{ride_id}`. Wallet : `GET /v1/drivers/me/wallet`, `/ledger`, `POST /v1/drivers/me/wallet/topups`, `GET .../topups/{id}` ; côté opérateur `GET /v1/admin/drivers/{id}/wallet` et `/ledger`. Webhook `POST /internal/webhooks/diddipay` protégé par secret de callback ; réconciliation périodique relisant l'intent (`settings.py:146-156`) pour qu'un webhook perdu se répare seul. `POST /v1/admin/payments/reconcile` et ses variantes par course et par recharge. Éligibilité : deux contrôles existent, solde minimum et plafond de commission estimée (`settings.py:124-125`), **neutralisés par leurs valeurs par défaut**. `422 AMOUNT_MISMATCH`, `422 INVALID_PAYMENT_METHOD`. **Aucune route de retrait** parmi les 124 routes exposées.

**Confluence.** Lot — Argent des pros (1015809) · Lot — Prix, commissions et penalites (1507329)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-030 | Le chauffeur consulte ses gains | MVP | Présent | `SCRUM-195` Terminé(e) |
| UC-182 | Le chauffeur voit sa synthese de gains : taux, frais, bonus, net, cash recu et a reverser | MVP | Partiel | `SCRUM-326` Terminé(e) |
| UC-189 | Le chauffeur recharge son wallet pour continuer a recevoir des courses | MVP | Présent | `SCRUM-91` Terminé(e) |
| UC-071 | L'utilisateur retire de l'argent | MVP | Hors diddi-go | `SCRUM-23` Terminé(e) |

4 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-190, UC-309, UC-310, UC-193.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **61** · Faits à établir : **33** · Contradictions entre deux sources : **9**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 23 sur 61.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | — | Produit |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | UC-274 | Produit |
| quel est le tarif du mode attente ? | — | Produit |
| quelle est la grille tarifaire de lancement, par ville et par profil ? | — | Produit |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | UC-259 | Produit |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | — | Produit |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | — | Produit |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | — | Technique |
| *15 autres entrées de même portée* | | |

*Faits à établir — portée MVP et entrées structurantes, 18 sur 33.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | — | Technique |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | — | Technique |
| ce cas est-il contrôlé côté serveur ? | — | — |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | — | — |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | — | Technique |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | — | Technique |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | — | Technique |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | — | Technique |
| *10 autres entrées de même portée* | | |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 7 sur 9.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | — | Produit |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | — | Technique |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | — | — |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | — | Produit |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | — | Produit |
| le solde minimum est configuré à zéro dans tous les fichiers de déploiement lus, la décision du 14/09 fixe 1 500 F | UC-190 | Technique / Technique / Exploitation |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | — | Produit |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE016** Wallet chauffeur, commission, recharge et retrait | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE016 — résultat attendu.* Appliquer 18 %, seuil 1 000 F à l’offre/acceptation ; recharge PaymentIntent ; confirmer réserve et retrait métier.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-91` | Done | Done | UC-189 — Le chauffeur recharge son wallet pour continuer à recevoir des course |
| `SCRUM-92` | Done | Done | UC-190 — Le système bloque un pro dont le solde passe sous le minimum exigé |
| `SCRUM-93` | Done | Done | UC-191 — Le pro demande le versement de ses gains |
| `SCRUM-98` | To Do | To Do | UC-309 — Le système ne propose pas une course dont la commission estimée dépas |
| `SCRUM-99` | Done | Done | UC-310 — Le système tolère un découvert borné et bloque le passage en ligne au |
| `SCRUM-103` | To Do | To Do | UC-314 — Le système vérifie que le compte mobile money de retrait correspond a |
| `SCRUM-104` | Done | Done | UC-315 — Le système applique un montant minimum de retrait |
| `SCRUM-105` | Done | Done | UC-316 — Le pro suit l'état de son retrait et voit la raison d'un échec |
| `SCRUM-461` | Done | Done | [DiddiGo] Séparer et sécuriser les retours passager et chauffeur |
| `SCRUM-514` | Done | Done | [DiddiGo] Webhook DiddiPay répond 500 après traitement réussi (status_code Non |
| `SCRUM-524` | A tester | A tester | Backend requis — Endpoints manquants DiddiGo Pro chauffeur (3 tickets frontend |

---

### PAR-019 — Limites du lancement

**Persona** Chauffeur · **Phase source** MVP · **Module** DiddiGo · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Chauffeurs indépendants uniquement. Pas de flottes ni de tarifs par zone (un champ « zone » peut être préparé). Stats de base et contrôles anti-abus inclus.

**Tâches liées.** P01, UX014, BE014, FE014, QT014

**Cible produit.** `PROD-001` partenaires et flottes en V1. `PROD-015` tarification par zone en V1. `PROD-008` et `PROD-010`.

**Code dans `diddi-go`.** Module `partner` complet et exposé : `Partner`, `PartnerMember`, `PartnerDriverLink`, `VehicleAssignment`, 15 routes en `/v1/admin/partners/*` et autant en `/internal/v1/admin/partners/*` (`partner/presentation/router.py`, `internal_router.py`). Un champ de ville existe côté tarification via la règle par ville et catégorie (`PricingRuleRepository.find_active(city, vehicle_category)`), sans logique de zone. Un multiplicateur de majoration est lu en base et borné par un plafond de code, sans calcul offre/demande. Statistiques de base : les cinq routes Pilotage. Contrôles anti-abus : voir PAR-014.

**Confluence.** Lot — Partenaires et Flottes (1376273) · Lot — Zones, couverture et majoration (1146913)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-120 | Le partenaire cree ou fait creer son organisation | MVP | Présent | `SCRUM-311` À faire |
| UC-121 | Le partenaire complete ses informations business | MVP | Présent | `SCRUM-312` À faire |
| UC-123 | Le partenaire gere ses chauffeurs ou livreurs rattaches | MVP | Présent | `SCRUM-314` À faire |
| UC-124 | Le partenaire gere ses vehicules | MVP | Présent | `SCRUM-315` À faire |
| UC-125 | Le partenaire affecte un vehicule a un operateur terrain | MVP | Présent | `SCRUM-316` À faire |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-289.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **13** · Faits à établir : **3** · Contradictions entre deux sources : **10**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 6 sur 13.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| quel est le statut juridique du montage de location-vente de véhicule ? | UC-124, UC-125 | Juridique |
| quelle est la part du partenaire de flotte, et sur quelle assiette est-elle calculée ? | UC-126, UC-127 | Administration |
| quelles pièces d'entreprise sont exigées d'un partenaire, et lesquelles bloquent l'activation ? | UC-121 | Juridique |
| un partenaire peut-il créer son organisation lui-même, ou passe-t-il toujours par un administrateur ? | UC-120, UC-121 | Produit |
| un partenaire peut-il rattacher un pro dont le dossier KYC n'est pas encore validé ? | — | — |
| un pro peut-il être rattaché à plusieurs partenaires, ou à un seul ? | UC-123 | Produit |

*Faits à établir — portée MVP et entrées structurantes, 2 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| existe-t-il dans DiddiSend un moyen de rattacher un coursier à un partenaire ? | — | Technique |
| la commission de partenaire déclarée sur l'organisation est-elle exploitée ailleurs que dans DiddiGo — par exemple lors d'un versement manuel ? | — | Technique |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 2 sur 10.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case décrit une action du partenaire ; la route correspondante est réservée à l'administrateur | — | — |
| les use cases UC-120 à UC-125 décrivent des actions du partenaire ; toutes les routes correspondantes sont réservées à l'administrateur | — | Produit |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE014** Course de la demande à la fin du trajet | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE014 — résultat attendu.* Fiabiliser attribution, position, états, absence de chauffeur et finalisation ; vérifier intégration DiddiMap.

*BE014 — blocage déclaré.* Contrat/intégration à fermer sur staging ; voir tickets liés.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-188` | Done | Done | UC-023 — Le chauffeur passe en ligne |
| `SCRUM-190` | Done | Done | UC-025 — Le chauffeur reçoit une offre de course |
| `SCRUM-191` | Done | Done | UC-026 — Le chauffeur accepte une course |
| `SCRUM-193` | Done | Done | UC-028 — Le chauffeur envoie sa position pendant la course |
| `SCRUM-194` | Done | Done | UC-029 — Le chauffeur met à jour les étapes de la course |
| `SCRUM-437` | Done | Done | DiddiGo: ne pas bloquer la fin de course si DiddiMap retourne ignore_for_scori |
| `SCRUM-438` | Done | Done | DiddiGo: rendre la finalisation de course idempotente lors des retries |
| `SCRUM-441` | To Do | To Do | DiddiMap: publier un contrat idempotent pour finish/analyze des traces service |
| `SCRUM-442` | Done | Done | Frontend: envoyer les positions GPS de course en continu et sans doublons |
| `SCRUM-524` | A tester | A tester | Backend requis — Endpoints manquants DiddiGo Pro chauffeur (3 tickets frontend |
| `SCRUM-536` | To Do | To Do | [DiddiGo Frontend Consumer] Blocage backend — SCRUM-441 (DiddiMap contrat idem |
| `SCRUM-567` | To Do | To Do | [Cross-module] Auto-provisionner les comptes consommateur (passager/client) de |

---

## DiddiPay — payer, retirer, rapprocher

### PAR-028 — Payer depuis un module

**Persona** Client · **Phase source** MVP · **Module** DiddiPay · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Le module demande un PaymentIntent (intention de paiement) à DiddiPay, le client passe par le prestataire de paiement. Résultat affiché seulement selon la confirmation reçue. Confirmation tardive gérée ; notification authentifiée et rapprochée (montant, devise, référence) ; callback répété ne recrédite pas.

**Tâches liées.** P06, UX024, BE024, FE024, QT024

**Cible produit.** `PROD-006` DiddiPay orchestre. `PROD-024` orchestration. `PROD-005` moyens visibles.

**Code dans `diddi-go`.** `payment/infra/diddipay_client.py` crée et relit les PaymentIntent (`diddipay_base_url`, `diddipay_client_id=diddigo`). Retours applicatifs séparés passager et professionnel (`diddigo_consumer_return_url`, `diddigo_pro_return_url`), contexte de retour consommable **une seule fois** (`payment/application/return_contexts.py`), TTL 15 min. `GET /payments/return` et `GET /wallet/return` non authentifiées. Webhook authentifié par `diddipay_callback_secret`. Réconciliation périodique entre un âge minimal — grâce laissée au payeur encore sur la page de paiement — et un âge maximal au-delà duquel DiddiPay a expiré l'intent. Six codes `500` refusent de publier une allocation incohérente.

**Confluence.** Lot — DiddiPay (557057) · DiddiPay — Wallet legacy vs PaymentIntent (5406721)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-076 | Le systeme cree et suit une intention de paiement | MVP | Hors diddi-go | `SCRUM-20` Terminé(e) |
| UC-070 | L'utilisateur depose de l'argent | MVP | Hors diddi-go | `SCRUM-15` Terminé(e) |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-078.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **3** · Faits à établir : **4** · Contradictions entre deux sources : **4**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 2 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | — | Produit |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | UC-072 | Juridique |

*Faits à établir — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | — | Technique |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | — | — |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | — | Technique |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | — | Produit |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | — | Technique |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | — | — |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | — | Produit |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | — | — |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE024** Paiement et recharge via PaymentIntent depuis les métiers | 2026-10-14 → 2026-10-16 | 2.5 j-p | À engager | Élevé |

*BE024 — résultat attendu.* Valider vrai prestataire, retour sécurisé, montant/devise/référence et callback ; sans wallet grand public.

*BE024 — blocage déclaré.* Contrat/intégration à fermer sur staging ; voir tickets liés.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-406` | A tester | A tester | Vérifier le retrait DiddiPay de bout en bout sur un vrai rail PSP test |
| `SCRUM-426` | A tester | A tester | DiddiPay : la réconciliation d'un paiement réussi n'émet pas payment.succeeded |
| `SCRUM-457` | To Do | To Do | [Paiements] Orchestrer le retour applicatif contextuel par service |
| `SCRUM-462` | A tester | A tester | [DiddiPay] Restreindre et auditer les URL de retour fournies par les services |
| `SCRUM-503` | To Do | To Do | [DiddiPay][Production Readiness] Fermer les écarts backend avant production |
| `SCRUM-504` | To Do | To Do | [DiddiPay][Prod] Sprint 1 — Migrer PaymentIntent/Payout vers les jetons S2S Di |
| `SCRUM-505` | To Do | To Do | [DiddiPay][Prod] Sprint 2 — Sécuriser le retour checkout par destinations enre |
| `SCRUM-506` | To Do | To Do | [DiddiPay][Prod] Sprint 3 — Ajouter les garde-fous Paystack test/live et la re |
| `SCRUM-511` | A tester | A tester | [DiddiPay][Docker UAT] Worker unhealthy and PaymentIntent provider initializat |
| `SCRUM-549` | A tester | A tester | [DiddiPay][Frontend] Blocage E2E — SCRUM-511 non résolu bloque Recharge + paie |

---

### PAR-029 — Retirer les gains

**Persona** Chauffeur, coursier, manager restaurant · **Phase source** MVP · **Module** DiddiPay · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Le module métier vérifie droits et fonds, réserve le montant, appelle le payout DiddiPay. Frais et net affichés avant confirmation. Succès : réserve clôturée. Échec définitif : réserve rendue. Résultat inconnu : réconciliation, ni libération ni 2e transfert.

**Limites que le planning déclare.** Vérification du bénéficiaire : capacité du prestataire à confirmer.

**Tâches liées.** P06, UX025, BE025, FE025, QT025

**Cible produit.** `PROD-032` retraits sans minimum métier. `PROD-003` retrait demandé dans l'application au MVP.

**Code dans `diddi-go`.** Aucune route de retrait dans `diddi-go`. Le wallet et le grand livre chauffeur existent, donc le solde qui serait réservé est lisible, mais ni la demande, ni la réservation, ni l'appel de payout ne sont exposés.

**Confluence.** Lot — Argent des pros (1015809) · PawaPay — Integration passerelle wallet (7897089)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-071 | L'utilisateur retire de l'argent | MVP | Hors diddi-go | `SCRUM-23` Terminé(e) |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-192.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **31** · Faits à établir : **19** · Contradictions entre deux sources : **5**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 3 sur 31.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | — | Produit |
| que devient le solde d'un pro qui quitte la plateforme avec un découvert ? | UC-310 | Juridique |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | UC-072 | Juridique |

*Faits à établir — portée MVP et entrées structurantes, 4 sur 19.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | — | Technique |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | — | — |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | — | Technique |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | — | Produit |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 5 sur 5.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | — | Technique |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | — | — |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | — | Produit |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | — | — |
| le solde minimum est configuré à zéro dans tous les fichiers de déploiement lus, la décision du 14/09 fixe 1 500 F | UC-190 | Technique / Technique / Exploitation |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE025** Exécution des retraits demandés aux wallets métiers | 2026-10-14 → 2026-10-23 | 2.5 j-p | À engager | Élevé |

*BE025 — résultat attendu.* Déclencher le transfert depuis la réserve métier ; garder référence unique et réconcilier résultat inconnu sans doubler le versement.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-93` | Done | Done | UC-191 — Le pro demande le versement de ses gains |
| `SCRUM-103` | To Do | To Do | UC-314 — Le système vérifie que le compte mobile money de retrait correspond a |
| `SCRUM-406` | A tester | A tester | Vérifier le retrait DiddiPay de bout en bout sur un vrai rail PSP test |
| `SCRUM-456` | To Do | To Do | [DiddiPay] Exécuter le payout restaurant idempotent et le rapprochement |
| `SCRUM-471` | A tester | A tester | [DiddiFood][Sprint 1] Traiter et réconcilier les statuts payout DiddiPay |
| `SCRUM-487` | A tester | A tester | [DiddiPay][UAT] Recette backend DiddiAdmin, Pilotage et wallet legacy |
| `SCRUM-500` | A tester | A tester | [DiddiFood][Sprint 2/4] Sécuriser et auditer le bénéficiaire DiddiPay du walle |
| `SCRUM-504` | To Do | To Do | [DiddiPay][Prod] Sprint 1 — Migrer PaymentIntent/Payout vers les jetons S2S Di |
| `SCRUM-509` | To Do | To Do | [DiddiPay][Prod] Sprint 6 — Clôture backend, recette QA et go/no-go production |

---

### PAR-030 — Rembourser et rapprocher

**Persona** Opérateur finance, client · **Phase source** MVP · **Module** DiddiPay · **Traitement planning** Scindé : rapprochement métiers MVP ; automatisation remboursements/reporting Pay V1, confirmation DEC-11.

**Attendu, texte du planning.** Remboursement sur décision métier autorisée (montant remboursable, droits, historique). Statut compréhensible pour le client. Rapprochement modules / Pay / prestataire, écarts visibles jusqu'à résolution. Synthèse comptable et export Odoo.

**Limites que le planning déclare.** Remboursement cash (restitution physique) à définir ; format Odoo à valider par la finance.

**Tâches liées.** P04, BE026, FE026, QT026, S02, VUX030, VBE030

**Cible produit.** `PROD-034` autorité de remboursement. `PROD-042` remboursement d'un paiement cash. `PROD-010` export comptable Odoo au MVP.

**Code dans `diddi-go`.** Côté Go : `POST /v1/admin/payments/reconcile`, `/rides/{ride_id}/reconcile`, `/topups/{topup_id}/reconcile` (`tests/test_payment_reconciliation.py`). `/internal/pilotage/finance-summary` expose 16 métriques et trois contrôles comptables bloquants ; le contrat précise que DiddiPay reste autorité sur les captures, remboursements partiels exacts, frais processeur, règlements et payouts, et que Pilotage/Odoo doivent réconcilier les deux sources. Aucune route de remboursement ni client Odoo dans `diddi-go`.

**Confluence.** Lot — DiddiPay (557057) · DiddiPay — Plan de recette backend DiddiAdmin et Pilotage (5668865)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-077 | L'administrateur rapproche une operation de paiement | MVP | Hors diddi-go | `SCRUM-21` Terminé(e) |
| UC-193 | L'administrateur rembourse tout ou partie d'un paiement | MVP | Absent du code | `SCRUM-95` Terminé(e) |

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **3** · Faits à établir : **4** · Contradictions entre deux sources : **4**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 2 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | — | Produit |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | UC-072 | Juridique |

*Faits à établir — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | — | Technique |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | — | — |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | — | Technique |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | — | Produit |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | — | Technique |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | — | — |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | — | Produit |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | — | — |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE026** Rapprochement quotidien des encaissements, gains et espèces | 2026-10-19 → 2026-10-23 | 1 j-p | À engager | Moyen |

*BE026 — résultat attendu.* Fournir journal et extraction minimum des opérations métiers/Pay ; conserver les écarts jusqu’à résolution.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-101` | Revue en cours | In Review | UC-312 — Un responsable enregistre le reversement d'espèces d'un coursier et s |
| `SCRUM-454` | Revue en cours | In Review | [DiddiSend] Publier le pickup financier et comptabiliser la dette cash Food |
| `SCRUM-483` | Done | Done | [DiddiSend][Interne S5] Exposer finance-summary et health-summary |
| `SCRUM-487` | A tester | A tester | [DiddiPay][UAT] Recette backend DiddiAdmin, Pilotage et wallet legacy |
| `SCRUM-492` | To Do | To Do | [UAT DiddiPay] Vérifier settlement et audit Backoffice |

---

### PAR-031 — Périmètre exact

**Persona** Direction · **Phase source** MVP · **Module** DiddiPay · **Traitement planning** Socle PaymentIntent et transferts métiers MVP ; wallet Pay public/P2P exclu.

**Attendu, texte du planning.** Pay = orchestrateur financier, pas un wallet grand public. Les wallets appartiennent à Go, Send, Food. Interfaces legacy conservées tant que soldes/consommateurs non inventoriés.

**Limites que le planning déclare.** Opérateurs de paiement activés au lancement à confirmer et tester.

**Tâches liées.** P01, P06, UX024, BE024, FE024, QT024

**Cible produit.** `PROD-006`, `PROD-024`, `PROD-025` extensions financières hors lancement.

**Code dans `diddi-go`.** DiddiGo possède ses propres soldes métier : `DriverWallet`, `DriverTopup`, `Transaction` (`payment/domain/entities.py`) et son grand livre. Il appelle DiddiPay pour les PaymentIntent et les recharges, sans jamais exposer de wallet grand public. Aucune lecture de la base d'un autre module : la règle de non-lecture croisée est tenue par construction, les échanges passant par les clients `infra/*_client.py`.

**Confluence.** Lot — DiddiPay (557057) · DiddiPay — Wallet legacy vs PaymentIntent (5406721)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-068 | L'utilisateur consulte le solde de son wallet | MVP | Hors diddi-go | `SCRUM-13` Terminé(e) |
| UC-069 | L'utilisateur configure son PIN wallet | MVP | Hors diddi-go | `SCRUM-14` Terminé(e) |
| UC-072 | L'utilisateur transfere de l'argent a un autre utilisateur | MVP | Hors diddi-go | `SCRUM-16` Terminé(e) |
| UC-075 | L'utilisateur consulte son historique de transactions | MVP | Hors diddi-go | `SCRUM-19` Terminé(e) |

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **3** · Faits à établir : **4** · Contradictions entre deux sources : **4**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 2 sur 3.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | — | Produit |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | UC-072 | Juridique |

*Faits à établir — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | — | Technique |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | — | — |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | — | Technique |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | — | Produit |

*Contradictions entre deux sources — portée MVP et entrées structurantes, 4 sur 4.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | — | Technique |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | — | — |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | — | Produit |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | — | — |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE024** Paiement et recharge via PaymentIntent depuis les métiers | 2026-10-14 → 2026-10-16 | 2.5 j-p | À engager | Élevé |

*BE024 — résultat attendu.* Valider vrai prestataire, retour sécurisé, montant/devise/référence et callback ; sans wallet grand public.

*BE024 — blocage déclaré.* Contrat/intégration à fermer sur staging ; voir tickets liés.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-406` | A tester | A tester | Vérifier le retrait DiddiPay de bout en bout sur un vrai rail PSP test |
| `SCRUM-426` | A tester | A tester | DiddiPay : la réconciliation d'un paiement réussi n'émet pas payment.succeeded |
| `SCRUM-457` | To Do | To Do | [Paiements] Orchestrer le retour applicatif contextuel par service |
| `SCRUM-462` | A tester | A tester | [DiddiPay] Restreindre et auditer les URL de retour fournies par les services |
| `SCRUM-503` | To Do | To Do | [DiddiPay][Production Readiness] Fermer les écarts backend avant production |
| `SCRUM-504` | To Do | To Do | [DiddiPay][Prod] Sprint 1 — Migrer PaymentIntent/Payout vers les jetons S2S Di |
| `SCRUM-505` | To Do | To Do | [DiddiPay][Prod] Sprint 2 — Sécuriser le retour checkout par destinations enre |
| `SCRUM-506` | To Do | To Do | [DiddiPay][Prod] Sprint 3 — Ajouter les garde-fous Paystack test/live et la re |
| `SCRUM-511` | A tester | A tester | [DiddiPay][Docker UAT] Worker unhealthy and PaymentIntent provider initializat |
| `SCRUM-549` | A tester | A tester | [DiddiPay][Frontend] Blocage E2E — SCRUM-511 non résolu bloque Recharge + paie |

---

## Support — reclamer et faire trancher

### PAR-009 — Faire une réclamation à toute heure

**Persona** Client, professionnel · **Phase source** MVP · **Module** Support · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Depuis une course/livraison/commande/transaction, ouvre l'aide. L'agent conversationnel (IA) recueille le problème, retrouve la mission, ne demande que ce qui manque. Peut identifier un gain, retrait ou pénalité contesté. Explique statuts et procédures. Ne promet jamais un remboursement non confirmé ; ne révèle rien d'un autre utilisateur.

**Tâches liées.** P04, UX009, BE009, FE009, QT009, I03, S02

**Cible produit.** `PROD-017` accueil et traitement.

**Code dans `diddi-go`.** Aucune surface de support, d'assistant conversationnel ni de ticket dans `diddi-go`. `POST /v1/rides/{id}/emergency` émet une alerte vers un webhook WhatsApp et un envoi SMTP (`ride/application/emergency_notifications.py`), avec un délai d'expiration propre.

**Confluence.** Lot — Support, litiges et objets oublies (1605633)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **7** · Faits à établir : **1** · Contradictions entre deux sources : **2**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

Aucune entrée de portée MVP ni structurante ; les entrées rattachées sont de portée V1 ou Later.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE009** Accueil conversationnel et réclamation H24 | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE009 — résultat attendu.* Raccorder assistant au dossier autorisé et à l’aide validée ; interdire décision de remboursement ou sanction autonome.

Aucun ticket Jira déclaré par le planning pour ce livrable.

---

### PAR-010 — Passer à un humain sans perdre le contexte

**Persona** Agent support · **Phase source** MVP · **Module** Support · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Notifié, reprend l'échange. Si l'IA ne sait pas : ticket + référence au client + contexte transmis. Si l'IA est en panne : formulaire de signalement. Statuts proposés : reçu, en traitement, en attente d'infos, résolu, fermé.

**Limites que le planning déclare.** Règles de fermeture/réouverture/délais à valider. Accueil H24 ≠ humain H24.

**Tâches liées.** P04, UX010, BE010, FE010, QT010, I03, S02

**Cible produit.** `PROD-017`.

**Code dans `diddi-go`.** Aucune surface de ticket ni de reprise humaine dans `diddi-go`.

**Confluence.** Lot — Support, litiges et objets oublies (1605633)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **7** · Faits à établir : **1** · Contradictions entre deux sources : **2**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

Aucune entrée de portée MVP ni structurante ; les entrées rattachées sont de portée V1 ou Later.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE010** Reprise humaine et suivi des tickets | 2026-10-14 → 2026-10-23 | 2.5 j-p | À engager | Élevé |

*BE010 — résultat attendu.* Créer et relier ticket, mission et conversation ; notifier agent ; suivre traitement et réouverture.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-58` | V2 | V2 | UC-242 — Traiter les litiges food (plat manquant, erreur, retard, restaurant f |
| `SCRUM-383` | To Do | To Do | UC-175 — Le client signale un problème sur une course ou une livraison terminé |
| `SCRUM-385` | To Do | To Do | UC-177 — Un agent ouvre, traite et clôture un ticket rattaché à une mission |
| `SCRUM-527` | In Progress | In Progress | DiddiSend — exposer POST /deliveries/{id}/complaints (route manquante, bloque  |
| `SCRUM-532` | To Do | To Do | [DiddiSend + Backoffice] Exposer et gérer les réclamations livraison dans le b |
| `SCRUM-535` | To Do | To Do | [Plateforme] Concevoir un contrat de réclamation partagé réutilisable par tous |

---

### PAR-011 — Traiter les litiges de chaque module

**Persona** Agent support · **Phase source** MVP · **Module** Support · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Go : course non conforme, attente contestée, incident sécurité, écart de prix. Send : collecte impossible, livraison échouée, preuve contestée, colis abîmé. Food : plat manquant, erreur, retard, restaurant fermé. Pay : paiement/retrait en attente, échoué, contesté. L'humain vérifie, décide, remboursement via le circuit financier avec trace.

**Limites que le planning déclare.** Plafonds de geste commercial et escalade à définir.

**Tâches liées.** P04, UX010, BE010, FE010, QT010, I03, S02

**Cible produit.** `PROD-017`, `PROD-034` autorité de remboursement, `PROD-037` séparation des pouvoirs.

**Code dans `diddi-go`.** Côté Go, les éléments qu'un litige exploite existent : historique des transitions, journal métier, recherche de logs par course, détail de course avec visibilité selon le rôle, montants et décomposition tarifaire. Le traitement du litige lui-même n'a pas de surface ici.

**Confluence.** Lot — Support, litiges et objets oublies (1605633)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **7** · Faits à établir : **1** · Contradictions entre deux sources : **2**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

Aucune entrée de portée MVP ni structurante ; les entrées rattachées sont de portée V1 ou Later.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE010** Reprise humaine et suivi des tickets | 2026-10-14 → 2026-10-23 | 2.5 j-p | À engager | Élevé |

*BE010 — résultat attendu.* Créer et relier ticket, mission et conversation ; notifier agent ; suivre traitement et réouverture.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-58` | V2 | V2 | UC-242 — Traiter les litiges food (plat manquant, erreur, retard, restaurant f |
| `SCRUM-383` | To Do | To Do | UC-175 — Le client signale un problème sur une course ou une livraison terminé |
| `SCRUM-385` | To Do | To Do | UC-177 — Un agent ouvre, traite et clôture un ticket rattaché à une mission |
| `SCRUM-527` | In Progress | In Progress | DiddiSend — exposer POST /deliveries/{id}/complaints (route manquante, bloque  |
| `SCRUM-532` | To Do | To Do | [DiddiSend + Backoffice] Exposer et gérer les réclamations livraison dans le b |
| `SCRUM-535` | To Do | To Do | [Plateforme] Concevoir un contrat de réclamation partagé réutilisable par tous |

---

### PAR-012 — Limiter les risques de l'IA

**Persona** Direction, support · **Phase source** MVP · **Module** Support · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** L'IA ne décide pas seule d'un remboursement, sanction ou litige. Signalements sécurité prioritaires, sans promesse d'intervention immédiate hors couverture réelle. Tests de manipulation de l'assistant, isolation des comptes et reprise humaine dans la recette.

**Tâches liées.** P04, UX009, BE009, FE009, QT009, I03, S02

**Cible produit.** `PROD-017`. `PROD-008` : IA anti-fraude éventuelle en Later.

**Code dans `diddi-go`.** Aucun composant d'IA dans `diddi-go`.

**Confluence.** Lot — Support, litiges et objets oublies (1605633)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **7** · Faits à établir : **1** · Contradictions entre deux sources : **2**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

Aucune entrée de portée MVP ni structurante ; les entrées rattachées sont de portée V1 ou Later.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE009** Accueil conversationnel et réclamation H24 | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |

*BE009 — résultat attendu.* Raccorder assistant au dossier autorisé et à l’aide validée ; interdire décision de remboursement ou sanction autonome.

Aucun ticket Jira déclaré par le planning pour ce livrable.

---

## Pilotage — suivre, proteger, aider

### PAR-013 — Suivre l'activité de chaque module

**Persona** Responsables Go/Send/Food, restaurant, exploitation · **Phase source** MVP · **Module** Pilotage · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Go : courses réalisées/annulées + montants. Send : livraisons, échecs, cash en attente. Food : commandes, gains, retraits. Pay : opérations confirmées / échouées / incertaines. Indicateurs : volumes, taux d'achèvement/échec, montants encaissés, commissions, retraits en attente, dettes cash, tickets non résolus. État des services, alertes, et « donnée indisponible » plutôt qu'un faux zéro.

**Limites que le planning déclare.** Dictionnaire des indicateurs à écrire avant la recette.

**Tâches liées.** P07, UX011, BE011, FE011, QT011, D05

**Cible produit.** `PROD-010` observabilité et statistiques de base au MVP, reporting détaillé en V1.

**Code dans `diddi-go`.** Cinq routes internes derrière une même garde (`ride/presentation/summary_router.py:16-20` : audience `diddigo`, scope `diddigo:ride-summary:read`, sujet `service:pilotage`) : `/internal/v1/ride-summary`, `/internal/pilotage/daily-summary`, `/finance-summary`, `/breakdown`, `/health-summary`. `finance-summary` est typé (`summary_schemas.py:39-48`, 16 métriques) et applique trois contrôles comptables bloquants. `breakdown` ventile par heure, moyen de paiement, type de service et statut final, avec cache. Fenêtre interrogeable bornée. `health-summary` publie `freshness_window_seconds` ; `finance-summary`, `daily-summary` et `breakdown` ne portent pas de bloc `freshness`. Six codes `500` dédiés aux incohérences d'allocation (`FARE_ALLOCATION_MISMATCH`, `PAYMENT_ALLOCATION_MISMATCH`, `DRIVER_PAYMENT_MISMATCH`, `INVALID_FINANCE_AMOUNT`, `INVALID_RIDE_FARE`) ; `503 RIDE_SUMMARY_UNAVAILABLE` et `503 LOG_SEARCH_UNAVAILABLE` quand la source est indisponible.

**Confluence.** Lot — Pilotage Direction Generale (1441809), epic SCRUM-79 — « bati dans le back-office existant, pas un service separe »

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Aucune entrée ouverte rattachée à ce parcours par les registres.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE011** Indicateurs métiers de base et qualité des données | 2026-10-19 → 2026-10-23 | 1.5 j-p | À engager | Moyen |

*BE011 — résultat attendu.* Exposer volumes, gains, encours et retraits selon droits ; fraîcheur et indisponibilité explicites.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-420` | Done | Done | [S2] DiddiGo: endpoint interne ride-summary |
| `SCRUM-435` | A tester | A tester | [Pilotage/Reporting] Valider la séparation avec la projection /pro/me |
| `SCRUM-481` | Done | Done | [DiddiSend][Interne S4] Exposer daily-summary Pilotage v1 |
| `SCRUM-483` | Done | Done | [DiddiSend][Interne S5] Exposer finance-summary et health-summary |
| `SCRUM-501` | A tester | A tester | [DiddiFood][Sprint 3/4] Exposer les synthèses Pilotage métier, finance et sant |
| `SCRUM-550` | A tester | A tester | [DiddiFood] Exposer GET /restaurants/{id}/daily-summary en accès gérant (stats |
| `SCRUM-571` | To Do | To Do | [DiddiFood] Créer l'endpoint GET /restaurants/{id}/daily-summary |

---

### PAR-014 — Socle anti-fraude

**Persona** Opérateur, système · **Phase source** MVP · **Module** Pilotage · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Common : limite les abus d'OTP. Go : contrôle des étapes de course et paiements. Send : preuves, dettes, reversements. Food : isolation des restaurants, rapprochement commande/livraison/gains. Pay : authentifie les notifications, bloque les doubles opérations. Suspicion ≠ fraude confirmée ; décision tracée.

**Limites que le planning déclare.** Seuils détaillés à définir.

**Tâches liées.** P07, UX012, BE012, FE012, QT012, BE026, FE026, QT026, Q02

**Cible produit.** `PROD-008` socle anti-fraude avec revue humaine dès le MVP. `PROD-046` identité et avantages.

**Code dans `diddi-go`.** Limite de renvoi d'OTP et durée de vie du code (`core/settings.py:43-44`). Exclusivité d'attribution par `SET NX` Redis doublée d'une contrainte en base. Réservation Redis des commandes S2S. Machine à états fermée : toute transition hors `ALLOWED_TRANSITIONS` lève `409 INVALID_STATUS_TRANSITION`. Vérification du sujet attendu en plus du scope sur les jetons de service. Secret de callback sur le webhook DiddiPay. Réconciliation paiements périodique. Fenêtre de rapport bornée pour qu'un appelant de service ne balaye pas la base.

**Confluence.** Lot — Reputation et fraude cote pro (1540097)

**Tâches et use cases majeurs.**

| UC | Action | Phase | Code au 09/10 | Ticket |
| --- | --- | --- | --- | --- |
| UC-326 | Le systeme detecte une position GPS simulee et force le passage hors ligne | MVP | Absent du code | `SCRUM-363` Terminé(e) |
| UC-327 | Le systeme enregistre une empreinte d'appareil a l'inscription et bloque les comptes multiples | MVP | Absent du code | `SCRUM-364` Terminé(e) |

1 cas limites rattachés à ce parcours — défaillance, concurrence ou reprise — traités dans une passe séparée : UC-201.

**Décisions à prendre et zones ambiguës.**

Décisions manquantes : **10** · Faits à établir : **1** · Contradictions entre deux sources : **7**. Liste intégrale dans [`PARCOURS_MVP_DECISIONS.md`](PARCOURS_MVP_DECISIONS.md).

*Décisions manquantes — portée MVP et entrées structurantes, 2 sur 10.*

| Entrée | Use cases cités | Décideur |
| --- | --- | --- |
| peut-on refuser un compte au motif que l'appareil a déjà servi, et sur quelle base ? | UC-327 | Juridique |
| un pro bloqué pour position simulée peut-il faire recours, et auprès de qui ? | UC-326 | Produit |

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE012** Contrôles anti-abus et décisions humaines tracées | 2026-10-14 → 2026-10-23 | 2 j-p | À engager | Élevé |
| **BE026** Rapprochement quotidien des encaissements, gains et espèces | 2026-10-19 → 2026-10-23 | 1 j-p | À engager | Moyen |

*BE012 — résultat attendu.* Vérifier acteur, droits, montants, signatures et transitions ; empêcher doubles actions et accès entre comptes.

*BE026 — résultat attendu.* Fournir journal et extraction minimum des opérations métiers/Pay ; conserver les écarts jusqu’à résolution.

| Ticket | Statut au 09/10 (classeur) | Statut live (09/10) | Résumé |
| --- | --- | --- | --- |
| `SCRUM-448` | Done | Done | [DiddiSend] Des endpoints admin acceptent des tokens non-admin |
| `SCRUM-559` | To Do | To Do | Durcir l'authentification S2S DiddiFiles (JWT aud+scope, retrait des backdoors |
| `SCRUM-562` | To Do | To Do | [DiddiFiles] Retirer le mécanisme service legacy (SERVICE_KEY implicite) et re |
| `SCRUM-564` | To Do | To Do | [DiddiGo] Jeton non vérifiable → 500 au lieu de 401 (PyJWKClientError non capt |
| `SCRUM-101` | Revue en cours | In Review | UC-312 — Un responsable enregistre le reversement d'espèces d'un coursier et s |
| `SCRUM-454` | Revue en cours | In Review | [DiddiSend] Publier le pickup financier et comptabiliser la dette cash Food |
| `SCRUM-483` | Done | Done | [DiddiSend][Interne S5] Exposer finance-summary et health-summary |
| `SCRUM-487` | A tester | A tester | [DiddiPay][UAT] Recette backend DiddiAdmin, Pilotage et wallet legacy |
| `SCRUM-492` | To Do | To Do | [UAT DiddiPay] Vérifier settlement et audit Backoffice |

---

### PAR-015 — Aide et enquête de satisfaction

**Persona** Utilisateur · **Phase source** MVP · **Module** Pilotage · **Traitement planning** MVP à livrer et valider.

**Attendu, texte du planning.** Aide accessible depuis le parcours ; enquête de satisfaction après usage (ne remplace pas un ticket). Réponses validées de l'aide alimentent l'assistant, avec un responsable de mise à jour.

**Limites que le planning déclare.** Fréquence et modalités de l'enquête à préciser.

**Tâches liées.** P07, UX013, BE013, FE013, QT013, I03

**Cible produit.** `PROD-017`.

**Code dans `diddi-go`.** Aucune surface d'aide ni d'enquête de satisfaction dans `diddi-go`. `POST /v1/rides/{id}/rating` enregistre une note de course, avec `409 RATING_ALREADY_SUBMITTED` et `422 RATING_OUT_OF_RANGE`.

**Confluence.** Lot — Support, litiges et objets oublies (1605633)

**Tâches et use cases majeurs.**

Aucun use case du corpus ne décrit l'étape nominale de ce parcours. Le périmètre est porté par le livrable backend et les décisions produit.

**Décisions à prendre et zones ambiguës.**

Aucune entrée ouverte rattachée à ce parcours par les registres.

| Livrable backend | Fenêtre | Effort restant | État planning | Risque |
| --- | --- | --- | --- | --- |
| **BE013** Aide validée et retour de satisfaction | 2026-10-19 → 2026-10-23 | 0.5 j-p | À engager | Moyen |

*BE013 — résultat attendu.* Stocker avis de satisfaction distincts des tickets ; relier aide versionnée à l’assistant.

Aucun ticket Jira déclaré par le planning pour ce livrable.

---

## Annexe A — constats de code du planning

Onglet *Vérification code*, daté du 09/10/2026. Reproduits tels quels. Le planning précise :
« Lecture ciblée locale ; aucune preuve d'exécution ou de configuration effective en staging/production. »

| Réf | Module | Sujet | Source précise | Constat | Conséquence planning | Tâches |
| --- | --- | --- | --- | --- | --- | --- |
| CODE-01 | Go | Wallet chauffeur et recharge métiers | `diddi-go/app_base/modules/payment/application/wallet_service.py:122` | La recharge crée un PaymentIntent avec référence métier chauffeur. | Conserver interface wallet Go ; ne pas l’assimiler au wallet Pay P2P. | BE016 / BE024 |
| CODE-02 | Go | Minimum par défaut | `diddi-go/app_base/core/settings.py:124` | driver_min_balance = 0 dans le code local. | Configurer 1 000 F et vérifier offre/acceptation ; valeur déployée non inspectée. | BE016 |
| CODE-03 | Send | Politique cash locale | `diddi-send/config/diddisend.toml:40` | max_amount_to_remit = 25000. | Aligner à 15 000 F ; pas de conclusion sur valeur staging effective. | BE019 |
| CODE-04 | Send | Contrôle d’éligibilité | `diddi-send/app/modules/delivery/application/eligibility.py:152` | Contrôle de dette actuelle, nombre de missions et échéance ; exclusivité Food présente. | Vérifier dette projetée et seuil 1 000 F ; garde de solde non trouvée dans cette fonction. | BE019 / BE022 |
| CODE-05 | Food | Wallet restaurant | `diddi-food/app/modules/wallets/application/use_cases.py:35` | Crédit pickup ; régularisation cash ; soldes pending/available/reserved ; retrait réservé. | Valider bout en bout avec Send et le transfert Pay ; pas de wallet livreur Food ici. | BE023 / QT023 |
| CODE-06 | Food | Taux et minimum retrait | `diddi-food/app/core/config.py:73` | food_commission_bps 1500 ; minimum retrait 5000 à la ligne 80. | Conforme aux valeurs décidées dans les défauts locaux ; vérifier configuration et recette. | BE023 |
| CODE-07 | Pay | Mécanisme de transfert | `diddipay-fund/payfund_app/modules/payments/presentation/payout_router.py:89` | create_payout et lecture de statut, séparés du module wallet legacy. | Retraits métiers à conserver sans lancement du wallet Pay grand public. | BE025 |
| CODE-08 | Jira frontend | Ancien seuil et wallet livreur Food | `https://diddifree.atlassian.net/browse/SCRUM-553` | Description mentionnant 2 000 F ; SCRUM-572 indique retrait désactivé. | Aligner contrat et interface sur 1 000 F ; état frontend local non audité. | FE019 / P03 |
| CODE-09 | Méthode | Portée des constats | `Graphify + lecture ciblée des sources locales au 09/10/2026` | Graphify a orienté vers les services financiers ; sources relues pour les valeurs. | Analyse locale, sans exécution de tests ni preuve de déploiement ; les étapes QA restent nécessaires. | Q01 |

## Annexe B — décisions et points à résoudre du planning

Onglet *Décisions*. Reproduits tels quels.

| Réf | État | Sujet | Décision ou point à résoudre | Responsable | Date cible |
| --- | --- | --- | --- | --- | --- |
| DEC-01 | Validé | Dates | Gel fonctionnel 18/11/2026 ; lancement 19/12/2026. | Direction | 2026-10-09 |
| DEC-02 | Validé | Ouverture | Go, Send, Food et Plus obligatoires ensemble ; seul Pay public peut être partiel. | Direction | 2026-10-09 |
| DEC-03 | Validé | Paiements | PaymentIntent pour paiements/recharges métiers ; wallets Go/Send/Food ; aucun wallet Pay P2P au MVP. | Finance + Backend | 2026-10-09 |
| DEC-04 | Constat code | Retraits | Le transfert de retrait utilise Payout ; ce mécanisme ne crée pas de wallet Pay grand public. | Backend | 2026-10-13 |
| DEC-05 | Validé | Commissions | Go 18 % ; Send/livraison Food 18 % ; restaurant Food 15 %. | Finance | 2026-10-13 |
| DEC-06 | À décider | Assiettes et frais | Fixer base, arrondi, suppléments, annulations, frais et minimums de retrait Go/Send. | Finance | 2026-10-13 |
| DEC-07 | Validé | Solde minimum | 1 000 XOF pour chauffeur Go et livreur Send/Food ; pas un seuil de wallet restaurant. | Finance | 2026-10-13 |
| DEC-08 | Validé | Encours cash | Dette cash livreur maximale 15 000 XOF ; cash MVP ; pas de plafond général client ou restaurant ajouté. | Finance | 2026-10-13 |
| DEC-09 | À décider | Encours projeté | Préciser cas de commande qui ferait dépasser 15 000 F ; proposition : refuser cette mission cash avant acceptation ; arbitrer ancien plafond de 3 missions/24 h. | Finance + Produit | 2026-10-13 |
| DEC-10 | Validé | Restaurant | Minimum retrait 5 000 XOF ; recharge restaurant hors MVP ; manager autorisé à demander son retrait. | Référent Food | 2026-10-13 |
| DEC-11 | À confirmer | Restitutions | Remboursement automatisé Pay reporté en V1 ; au MVP conserver traitement humain traçable des litiges et des restitutions. | Finance + Support | 2026-10-14 |
| DEC-12 | Proposition | Livreur Food | DiddiSend possède missions et wallet livreur Food ; DiddiFood possède commande et wallet restaurant. Confirmer le contrat et dédupliquer le suivi. | Backend | 2026-10-13 |
| DEC-13 | Validé | Métiers | Chauffeur, coursier Send/Food, restaurant/cuisine/manager et admin/support MVP. Relais, flottes V1 ; marchés/supermarchés Later. | Produit | 2026-10-12 |
| DEC-14 | Hypothèse | Zones et ouverture | Conserver Yopougon, Cocody, Plateau ; téléchargement public avant 18/11, commandes ouvertes au public le 19/12. | Direction | 2026-10-13 |
| DEC-15 | Objectif externe | Stores | Soumission 05/11, publication cible 17/11 ; disponibilité dépend de la revue effective Google/Apple. | Frontend | 2026-11-17 |
| DEC-16 | Validé | UI UX | MVP puis conception V1 ; aucun travail Later. | Responsable UI UX | 2026-10-12 |
| DEC-17 | À décider | Audio | Langues, prestataire et politique ; conservation optionnelle audio désactivée jusqu’à décision explicite. | Produit | 2026-10-14 |
| DEC-18 | À décider | Support | Horaires humains, circuit urgence, droits financiers et montants autorisés ; IA H24 ne signifie pas agents H24. | Support + Direction | 2026-10-14 |
| DEC-19 | À décider | Production | Valider budget et trafic attendu ; ne pas attendre la fin complète du staging pour provisionner la production. | DevOps + Direction | 2026-10-14 |
| DEC-20 | Proposition | Sauvegardes | Quotidiennes chiffrées, 30 jours ; perte de données max 15 min, reprise 4 h ; restauration prouvée. | DevOps | 2026-10-16 |
| DEC-21 | Proposition | Performance | Pic 60 min, double pic 15 min, endurance 4 h ; erreurs <1 %, 95 % lectures <2 s et commandes <3 s hors attente prestataire. | DevOps + QA | 2026-10-16 |
| DEC-22 | À nommer | Responsables | 1 Flutter, 1 Backend, 1 DevOps, 1 QA, 1 UI UX, 2 Support, 1 Produit/Data, 1 IA disponibles ; affectations nominatives à compléter. | Direction | 2026-10-12 |
| DEC-23 | Proposition | Capacité | 5 jours/semaine ; 70 % du temps alloué aux tâches planifiées ; jours fériés non fournis ; charge distribuée sur chaque fenêtre. | Direction | 2026-10-14 |
| DEC-24 | Proposition | Gel du code | Après le 18/11 : exploitation/formation/recette ; correction bloquante seulement sur décision explicite, nouvelle validation et resoumission mobile si nécessaire. | Produit + QA | 2026-11-18 |
| DEC-25 | À faire ensuite | Checklist QA | Ajouter la checklist détaillée après validation du planning ; campagnes et efforts QA sont déjà inclus. | Responsable QA | 2026-10-16 |
| DEC-26 | Proposition | V1 | Conception UI UX après le gel MVP ; dates d’implémentation V1 et Later non engagées ; P2P reste conditionnel/hors MVP. | Produit | 2026-11-23 |
| DEC-27 | Proposition | Estimations | Efforts restants de planification, pas des temps Jira ; revue humaine incluse ; aucune promesse de gain IA chiffrée sans mesure. | Responsables équipes | 2026-10-14 |

## Annexe C — parcours DiddiGo hors MVP

Pour situer la trajectoire, sans détail.

| PAR | Phase | Parcours | Traitement planning |
| --- | --- | --- | --- |
| PAR-036 | V1 | Tarifs par zone | Conception UI UX après MVP ; réalisation non datée |
| PAR-037 | V1 | Usages enrichis et flottes | Conception UI UX après MVP ; réalisation non datée |
| PAR-045 | Later | Course programmée, pour un tiers, modes spéciaux | Hors planning daté et hors UI UX |

## Sources

| Source | Date | Rôle |
| --- | --- | --- |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx` — *Parcours sources*, *Backend*, *Jira source*, *Vérification code*, *Décisions* | 09/10/2026 | **spécification principale** |
| `diddi-scope-document/` — registre des 48 décisions `PROD-xxx`, parcours MVP/V1/Later, paramètres | 09/10/2026 | cible produit |
| `diddi-go/app_base/`, `tests/`, surface OpenAPI générée | branche courante | le code |
| Jira `diddifree`, lecture seule | 09/10/2026 | statut live |
| Confluence espace `DIDDIFREE`, pages « Lot — », lecture seule | 15/09 et 08/10/2026 | epics, sprints, répartition |
| `management/specs/` — `backlog.csv`, `ASSEMBLAGE.md`, `lots/`, `etat/` | 14/09/2026 | complément, voir `PARCOURS_MVP_COMPLEMENT_UC.md` |

Documents voisins : [`PARCOURS_CODE_DIDDIGO.md`](PARCOURS_CODE_DIDDIGO.md) et
[`PARCOURS_CIBLE_DIDDIGO.md`](PARCOURS_CIBLE_DIDDIGO.md) détaillent chaque côté séparément ;
[`PARAMETRES_CONFIGURABLES.md`](PARAMETRES_CONFIGURABLES.md) porte toutes les valeurs.
