# Carte de la cible produit — DiddiGo

Date de relevé : 9 octobre 2026.

Ce document décrit **ce que le produit a décidé**, sans le comparer au code et sans affirmer un état de
livraison. L'état réel du code est dans `CARTE_CODE_DIDDIGO.md` ; la confrontation des deux est dans
`ECARTS_CODE_CIBLE_DIDDIGO.md`.

## Sources d'autorité

| Source | Rôle |
| --- | --- |
| `E:\DIDDI AI\diddi-scope-document\REGISTRE_DECISIONS_PRODUIT_ARCHITECTURE.md` | 48 décisions `PROD-xxx` validées par le porteur, mise à jour du 9 oct. 2026 |
| `…\PARAMETRES_METIER.md` | montants, taux et plafonds ajustables |
| `…\DiddiFree_Parcours_MVP_V1_Later.docx` | parcours utilisateurs par phase |
| `…\MATRICE_ALIGNEMENT_RECETTE.md` | ordre de travail et recettes attendues |
| `…\JOURNAL_CAS_PARTICULIERS.md` | cas limites, 8 entrées `EDGE-xxx` |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx` | jalons et livrables backend |
| Jira `diddifree`, Confluence espace `DIDDIFREE` | état des tickets, lecture seule |

Deux avertissements que ces sources portent elles-mêmes et qui s'appliquent à toute cette carte :

> « Une fonctionnalité incluse dans une phase n'est ni automatiquement développée, ni automatiquement
> validée. Une API présente et un ticket terminé ne remplacent pas une recette sur la version réellement
> déployée. » — `DiddiFree_Parcours_MVP_V1_Later.docx`

> « Les décisions définissent la cible, pas l'état de livraison. » — registre des décisions

---

## 1. Cadre général

`PROD-001` — Go, Send et Food lancent leurs parcours essentiels à **Abidjan**. Le MVP cible les
consommateurs, les chauffeurs et coursiers **indépendants**, et les restaurants. **Partenaires et flottes
sont en V1.**

`PROD-002` — Common regroupe Identity, profils, Backoffice, notifications, Map, support et Pilotage
transverse. Les statistiques propres à chaque métier restent rattachées à leur module.

`PROD-007` — Le **numéro de téléphone est le mode de connexion prioritaire**, par SMS ou WhatsApp.
L'email est uniquement un secours.

`PROD-005` — Au MVP le client choisit **espèces ou Mobile Money** (Wave, MTN, Moov, Orange via le PSP).
La **carte bancaire est en V1**.

`PROD-003` — Le MVP inclut wallets métier, gains, cash, recharges, commissions, dettes, régularisation et
**retraits demandés par le professionnel dans l'application**. L'initiation d'un retrait par le Backoffice
est Later ; la supervision et le traitement des incidents restent au MVP.

`PROD-006` / `PROD-024` — DiddiPay orchestre PaymentIntent, remboursements et payouts ; **les modules
possèdent les soldes métier**. Le wallet public DiddiPay reste distinct et son bouton de paiement est
masqué jusqu'à son ouverture.

`PROD-008` — Historique vérifié et socle anti-fraude avec **revue humaine dès le MVP**. Renforcement en
V1, IA anti-fraude éventuelle Later.

`PROD-010` — Observabilité et statistiques de base par module, aide, **export comptable Odoo** et gestion
de la suppression de compte font partie du MVP. Reporting détaillé et ventilé en V1.

`PROD-043` — Les **comportements** constituent le périmètre produit ; les **montants, taux et plafonds**
sont centralisés dans `PARAMETRES_METIER.md` et **ne sont pas figés pour le lancement**. Les anciens
chiffres de discussion ou de Jira sont des repères historiques, pas des obligations définitives.

---

## 2. Parcours MVP DiddiGo

### 2.1 Commander et effectuer une course

Le passager indique départ et destination, **par saisie ou dictée**. Il vérifie les lieux proposés et
consulte une estimation avant de confirmer. Le système recherche un chauffeur éligible et disponible, lui
présente la demande, puis confirme l'attribution quand le chauffeur accepte.

Le passager suit l'approche du véhicule et dispose du moyen de contact retenu. Le chauffeur rejoint le
point de départ, **signale son arrivée**, commence la course puis la termine. Les écrans des deux parties
reflètent une même mission. Une offre expirée, un refus, une absence de chauffeur ou une perte de
connexion doivent donner **une issue explicite** et permettre une reprise cohérente.

**`PROD-027` Recherche et absence avant départ** — recherche en **trois phases successives** :

```
30 s dans 1 km  →  60 s dans 3 km  →  180 s jusqu'à 5 km
durée maximale totale : 4 min 30 s
```

Continuer à considérer les chauffeurs proches devenus disponibles pendant les phases suivantes. À
épuisement, proposer une **nouvelle recherche explicite**. Les seuils sont des paramètres de lancement,
ajustables après mesure et décision produit.

Après **dix minutes** sans commencement de la course, le chauffeur peut déclarer le client absent et
annuler ; l'annulation reste gratuite (`PROD-014`).

**`PROD-015` Confort, devis et demande** — trois niveaux de confort au MVP. Le devis reste valable
**15 minutes maximum** depuis son émission ; un rafraîchissement produit un nouveau devis, et un devis
expiré doit être rafraîchi avant confirmation. **Le prix de référence est conservé après confirmation**,
hors attente et modifications de trajet.

Au MVP, enregistrer les demandes de devis, dates, points de prise en charge, confort, **références de
déduplication**, offre disponible et résultats du parcours. **Aucune majoration automatique** liée à la
demande. Mesure dans un rayon de 1 km autour de la prise en charge sur les 20 dernières minutes, en
comptant **une seule demande par passager** dans ce voisinage même après rafraîchissement ou comparaison
de conforts. En l'absence de chauffeur, afficher l'indisponibilité sans garantir l'attribution.

**`PROD-013` Début de course et secours GPS** — le chauffeur commence la course lorsque le client est à
bord. Le bouton est autorisé si chauffeur et passager sont à **10 mètres maximum**, avec **deux positions
âgées de 30 secondes maximum** et une **précision annoncée de 10 mètres maximum** chacune. Le démarrage
arrête le compteur d'attente.

Si le GPS est inexploitable, un **code aléatoire de prise en charge à six chiffres** lié à la course
remplace le contrôle de proximité. Le passager le communique une fois à bord. Il est **à usage unique**,
invalidé au démarrage ou à l'annulation. Après **cinq essais incorrects**, bloquer cette tentative de
validation et orienter vers le support. Le recours au code est tracé. Sans GPS exploitable ni code,
intervention du support.

**`PROD-011` Reprise après fermeture** — quitter, fermer ou perdre la connexion **ne met pas fin** à une
course. Le passager et le chauffeur retrouvent la course et poursuivent depuis son état réel. La reprise
**ne crée pas une nouvelle mission** et **ne réinitialise pas le compteur d'attente**. S'applique aussi à
Send et Food.

### 2.2 Attente, escales et annulation

**`PROD-012` Arrivée et attente de prise en charge** — le chauffeur indique son arrivée. Une distance
**strictement inférieure à 50 mètres** du point de prise en charge est requise pour valider l'arrivée et
**démarrer l'attente**. Les **trois premières minutes sont gratuites**. Chaque **minute supplémentaire
complète** est facturée au tarif `go.pickup_wait_rate` :

```
montant = tarif × floor( max(0, t − 180) / 60 )      t en secondes
```

Le statut d'arrivée et l'attente figurent dans le parcours et le prix.

**`PROD-026` Attente en escale** — **une minute gratuite par escale**, puis `go.stop_wait_rate` **au
prorata des secondes, arrondi au franc le plus proche**. Règle distincte de l'attente de prise en charge.

**`PROD-014` Annulation et fin anticipée** — une annulation intervient **avant** le début de course :
**aucun frais**, attente acquise comprise. **Après démarrage il s'agit d'une fin anticipée** : facturer
le trajet effectué avec le barème et le coefficient **acceptés au départ**, puis ajouter seulement attente
et suppléments acquis. Si le total est **strictement inférieur** à `go.early_end_free_threshold`, il est
gratuit ; **au seuil il est dû**. Les **malus opérationnels ne sont pas activés au MVP**.

Le parcours doit rendre les changements visibles : début et fin d'attente, ajout d'escale, supplément,
nouveau montant. L'annulation doit indiquer **qui** l'a demandée, **à quelle étape**, et **quelles
conséquences**. Un incident ou une urgence reste signalable, l'alerte parvenant au circuit humain défini.

### 2.3 Payer et retrouver ses gains

**`PROD-004` Commissions** — Go prélève sa commission **sur le montant total de la prestation encaissée,
attente et suppléments compris**. Taux de référence : `go.commission_rate = 18 %`. Le `.docx` précise
« avec une assiette et des règles d'arrondi à finaliser ».

**`PROD-030` Paiement à la fin** — paiement **après réalisation de la mission ou fin anticipée**, y
compris en numérique. Ne pas confondre préparation technique d'un paiement et encaissement. En cas
d'échec : afficher *Réessayer*, permettre un autre moyen, **conserver la somme due** et **bloquer une
nouvelle commande payante** jusqu'à régularisation — sans bloquer support ni historique.

**`PROD-031` Changement de moyen et double paiement** — le client peut passer du Mobile Money aux
espèces après confirmation. Enregistrer la bascule côté serveur et notifier les deux parties. **Détecter
et signaler automatiquement comme doublon tout succès numérique tardif après encaissement cash**, pour
remboursement administratif — sans dépendre de la seule réclamation client.

**`PROD-032` Retraits sans minimum métier** — tous les professionnels peuvent retirer leur solde
disponible **sans minimum commercial DiddiFree**. Le minimum d'accès à la mise en ligne est un contrôle
**distinct**. Les frais sont supportés par le bénéficiaire et déduits du montant demandé. **Avant
confirmation, afficher montant débité, frais exacts et montant reçu.**

**`PROD-042` Remboursement d'un paiement cash** — rembourser **par voie numérique** vers un bénéficiaire
vérifié, après validation administrative. Ne pas imposer au chauffeur de retrouver physiquement le client
pour restituer des espèces.

**`PROD-034` Autorité de remboursement** — remboursement décidé dans le Backoffice et **validé par un
administrateur**. Les agents support n'obtiennent pas implicitement un droit de remboursement autonome.

**`PROD-040` Impayés cloisonnés** — au lancement, **cloisonner les impayés par module** : une dette Go ne
bloque pas automatiquement Food ou Send. L'accès au support et à l'historique reste disponible. Une fraude
vérifiée peut conduire à une restriction globale **décidée par un humain**.

Dans le parcours cash, le chauffeur encaisse et **la commission due est enregistrée dans son wallet**.
Dans le parcours numérique, **les gains ne sont crédités qu'à partir du résultat financier confirmé**.

### 2.4 Limites du lancement Go

Textuellement : « Le MVP vise les **chauffeurs indépendants**. La gestion de flottes et les **tarifs
différenciés par zone sont en V1**. Préparer un champ de zone ne signifie pas appliquer une tarification
de zone au lancement. Les statistiques de base et les contrôles contre doubles paiements, étapes
incohérentes et abus évidents sont inclus ; les suspicions nécessitent **qualification humaine**. »

---

## 3. Parcours Common qui traversent Go

**Créer son compte** — le consommateur saisit son numéro, reçoit un OTP par SMS, le confirme, accède à
son profil, puis utilise Go, Send et Food **avec la même identité**. Session conservée ou renouvelée de
manière contrôlée. Le parcours doit expliquer les échecs : code erroné ou expiré, délai avant renvoi,
numéro invalide, indisponibilité du prestataire. **Une panne SMS ne doit pas être présentée comme une
erreur de l'utilisateur.** L'authentification consommateur ne remplace pas la vérification
professionnelle.

**Devenir chauffeur** — création du profil métier, justificatifs, dossier en attente ; le **véhicule est
également contrôlé**. Un opérateur autorisé accepte ou refuse **avec un motif compréhensible** ; le
professionnel peut corriger et resoumettre. **L'activation ne résulte pas uniquement de la création du
compte Identity** : le module métier conserve ses conditions d'éligibilité. Pas de mise en activité ni de
retrait de gains avant les validations requises. Une suspension doit être visible, motivée et tracée.

**Administrer sans dépasser ses droits** — chaque action sensible possède acteur, motif, date et
résultat. **Une nouvelle tentative après un problème réseau ne doit pas répéter la mutation.** Les
services utilisent leurs propres identités techniques et des permissions limitées.

**Recherche de destination texte ou voix** — la voix **remplace uniquement la saisie** : elle ne choisit
pas silencieusement entre deux homonymes et **ne déclenche ni commande ni dépense**. Si le micro est
refusé ou la transcription échoue, le clavier reste disponible. `PROD-018` / `PROD-019` encadrent la
dictée et la conservation facultative d'échantillons vocaux, désactivable par l'utilisateur.

**Offre et suivi de mission** — notifications critiques vérifiées application ouverte, en arrière-plan
et téléphone verrouillé. **Une notification retardée ne doit pas permettre d'accepter une offre déjà
attribuée.** Le périmètre retient **l'appel** ; messagerie en mission et appels Internet intégrés sont en
V1.

**Historique exploitable** — chaque mission et opération financière produit un historique vérifiable,
**corrélable et rejouable sans doublon**. Le MVP ne montre ni compteur de points ni DiddiScore.

**Support** — `PROD-017` : accueil conversationnel automatique **H24**, réponse fondée sur une aide
validée, création de ticket, accusé de réception et transmission du contexte. `PROD-037` : l'agent
consulte, explique, documente et propose ; **l'administrateur décide dans sa délégation** ; la finance
exécute et rapproche. L'IA **ne décide pas** d'un remboursement, d'une sanction ou de l'issue d'un litige.
L'accueil H24 **ne signifie pas** qu'un humain est présent H24.

**Pilotage qualité** — indicateurs MVP proposés : volumes, taux d'achèvement et d'échec, montants
encaissés, commissions, retraits en attente, dettes cash, tickets non résolus. **En cas de panne d'un
module, le tableau de bord indique une indisponibilité ou une donnée ancienne plutôt qu'un résultat
artificiellement nul.** Un identifiant de mission doit permettre de retrouver son parcours entre
Identity, le module métier, Send et Pay.

**Conservation** — `PROD-038` : GPS détaillé de mission conservé **30 jours**, puis suppression des
traces précises au profit de statistiques agrégées non identifiantes ; preuves de litige préservées
séparément. Conversations : 90 jours (`PROD-028`). Mise en œuvre soumise à **validation juridique**.

---

## 4. Paramètres métier Go

**Les valeurs ne sont pas ici.** Elles sont dans le registre unique
`docs/mapping/PARAMETRES_CONFIGURABLES.md`, qui rapproche chaque clé documentaire de son implémentation
réelle et de son mécanisme de changement. L'autorité sur les valeurs cible reste
`E:\DIDDI AI\diddi-scope-document\PARAMETRES_METIER.md`.

Raison, posée par `PROD-043` : les comportements constituent le périmètre produit, les montants sont
centralisés et **ne sont pas figés pour le lancement**. Ce document décrit donc les comportements et se
contente de nommer les clés : `go.commission_rate` (assiette : prestation totale encaissée, attente et
suppléments compris), `go.pickup_wait_rate` (minutes supplémentaires complètes après franchise),
`go.stop_wait_rate` (prorata à la seconde après franchise d'escale, arrondi au franc),
`go.early_end_free_threshold` (gratuit sous le seuil, dû au seuil), `go.surge_cap` (V1 uniquement),
`go.online_min_balance` (éligibilité à la mise en ligne, distincte du retrait),
`professional.withdrawal_minimum` (aucun minimum commercial) et `professional.withdrawal_fee` (déduits du
montant demandé, annoncés avant confirmation).

Décisions explicitement **remplacées** (section « Décisions remplacées » du registre) :

- majoration automatique au MVP → **collecte au MVP, activation en V1** ;
- une minute gratuite à la prise en charge → **trois minutes**, seules les minutes supplémentaires
  complètes étant facturées ;
- escale → **franchise distincte d'une minute et prorata à la seconde** ;
- ancien minimum de retrait restaurant de 5 000 F → **absence de minimum métier**.

---

## 5. Découpage MVP / V1 / Later pour Go

| Fonctionnalité | Phase | Référence |
| --- | --- | --- |
| Course de la demande à la fin du trajet | MVP | `.docx` §Go, BE014 |
| Attente facturée, escales, annulation, signalement urgent | MVP | `PROD-012/014/026`, BE015 |
| Wallet chauffeur, commission, recharge, retrait | MVP | `PROD-003/032`, BE016 |
| Trois niveaux de confort | MVP | `PROD-015` |
| Statistiques de base et anti-fraude avec revue humaine | MVP | `PROD-008/010` |
| Recherche de destination texte et voix | MVP | `PROD-018` |
| Appel entre parties en mission | MVP | `PROD-016` |
| Reçu client de paiement | **V1** | `PROD-045` |
| Majoration automatique offre/demande plafonnée | **V1** | `PROD-015` |
| Tarification différenciée par zone | **V1** | `PROD-015`, `.docx` §V1 |
| Score opérationnel avec effets (malus) | **V1** | `PROD-020` |
| Partenaires et gestion de flottes | **V1** | `PROD-001` |
| Lieux favoris, historique de gains détaillé | **V1** | `.docx` §V1 |
| Messagerie en mission, appels Internet intégrés | **V1** | `PROD-016` |
| Fidélité, points, bonus, parrainage | **V1** | `PROD-009` |
| Carte bancaire | **V1** | `PROD-005` |
| Reporting financier détaillé et ventilé | **V1** | `PROD-010` |
| Course programmée | **Later** | `PROD-016` — masquée au lancement sans supprimer son implémentation |
| Carte des zones de demande visible aux utilisateurs | **Later** | `PROD-015` |
| Initiation d'un retrait par le Backoffice | **Later** | `PROD-003` |
| DiddiFund, prêts, financements, score de crédit | **Later** | `PROD-025` |
| IA anti-fraude | **Later** | `PROD-008` |

---

## 6. Planning et état des tickets

### 6.1 Jalons

| Date | Jalon | Équipe pilote | Risque |
| --- | --- | --- | --- |
| 2026-10-30 | Béta interne et TestFlight disponibles | Frontend | Moyen |
| 2026-11-05 | Candidats complets soumis aux stores | Frontend | Moyen |
| 2026-11-17 | Deux applications publiées Play + App Store | Frontend | **Élevé** |
| 2026-11-18 | **Gel du code fonctionnel MVP** | Produit Data | Moyen |
| 2026-12-11 | Pilote terrain terminé dans les trois zones | Support | Moyen |
| 2026-12-16 | Décision finale d'ouverture | Produit Data | Moyen |
| 2026-12-19 | **Ouverture commerciale** Go, Send, Food, Plus | Produit Data | Moyen |

Zones de lancement : Yopougon, Cocody, Plateau.

### 6.2 Livrables backend Go

| ID | Livrable | Phase | Priorité | Fenêtre | Effort restant |
| --- | --- | --- | --- | --- | --- |
| BE014 | Course de la demande à la fin du trajet | MVP | P0 | 14→23 oct | 2 j-p |
| BE015 | Attente facturée, escales, annulation, signalement urgent | MVP | P0 | 14→23 oct | 2 j-p |
| BE016 | Wallet chauffeur, commission, recharge, retrait | MVP | P0 | 14→23 oct | 2 j-p |
| BE026 | Rapprochement quotidien encaissements, gains, espèces | MVP | P1 | 19→23 oct | 1 j-p |
| VBE036 | Tarifs par zone | V1 | P2 | à programmer | non daté |
| VBE037 | Usages enrichis et flottes | V1 | P2 | à programmer | non daté |

Les quatre livrables MVP sont à l'état « **À engager** ».

Arbitrage à échéance **13 octobre**, responsable Finance + Backend, état « à aligner » :
**P02 — seuils et commissions métiers, aligner 0/2 000/25 000 F historiques sur 1 000/15 000 F.**

### 6.3 État Jira des tickets DiddiGo

37 tickets. Règle de lecture posée par le planning : « *À tester* vaut 85 % indicatif ; l'avancement d'un
livrable intégré reste à renseigner après revue ; **un ticket terminé ne suffit pas à le déclarer
validé**. »

**Terminés (12)** — vérificateur de service token scoped (SCRUM-419), endpoint interne ride-summary
(SCRUM-420), publication `operational_status` vers DiddiFreeID (SCRUM-431), auth service DiddiMap pour
les traces (SCRUM-436), non-blocage de fin de course sur `ignore_for_scoring` (SCRUM-437), finalisation
idempotente (SCRUM-438), distinction erreurs métier 409 / indisponibilités 503 DiddiMap (SCRUM-439),
journalisation des traces GPS inutilisables (SCRUM-440), positions GPS continues sans doublons
(SCRUM-442), séparation des retours passager et chauffeur (SCRUM-461), webhook DiddiPay 500 après succès
(SCRUM-514), suivi administrateur des courses (SCRUM-138), demande à devenir chauffeur (SCRUM-159).

**À tester (7)** — contrat d'accès Backoffice et recette KYC staging (SCRUM-466), fiabilisation de la
projection `diddigo/driver` (SCRUM-510), dead-letter `404 USER_NOT_FOUND` terminal (SCRUM-513),
endpoints manquants DiddiGo Pro chauffeur (SCRUM-524), commandes KYC et annulation en échec —
`X-Request-ID` non-UUID et `idempotency_key` manquant (SCRUM-529), blocage E2E recharge et paiements
(SCRUM-549), routes partenaires en S2S Backoffice (SCRUM-569).

**Ouverts, dont des blocages de parcours MVP (11)** :

| Ticket | Sujet | Parcours MVP touché |
| --- | --- | --- |
| SCRUM-565 | `/v1/auth/otp/verify` émet un jeton **HS256 local rejeté** par les routes protégées, alors que l'identité est DiddiFreeID RS256 | Créer son compte et retrouver sa session |
| SCRUM-567 | Auto-provisionner les comptes consommateur depuis DiddiFreeID | Créer son compte |
| SCRUM-564 | Jeton non vérifiable → 500 au lieu de 401 (`PyJWKClientError` non capturé) | Toutes surfaces authentifiées |
| SCRUM-566 | `IntegrityError` sur `POST /v1/rides` mal classé en 503 `DATABASE_UNAVAILABLE` | Commander une course |
| SCRUM-536 | Contrat idempotent DiddiMap non livré → bloque le GPS passager | Suivre l'approche du véhicule |
| SCRUM-568 | Contrat S2S Backoffice pour partenaires et flottes | V1 |
| SCRUM-576 | Migrer les routes traces DiddiGo vers scopes S2S | Traces de course |
| SCRUM-485 | Retirer l'en-tête legacy `X-User-ID` (en revue) | Administration |
| SCRUM-64 / SCRUM-65 | Lots DiddiGo Passager et Chauffeur | épiques de cadrage |
| SCRUM-355 | Code promo cohérent entre modules | V1 fidélité |

**Reclassés V2 (3)** — polling du résumé DiddiGo par Pilotage (SCRUM-422), suppléments tarifaires
automatiques par recalcul DiddiMap (SCRUM-537), photo de profil chauffeur publique (SCRUM-557).

### 6.4 Confluence

*Lot — Pilotage Direction Generale* (page 1441809) : « Organisation interne DIDI GROUP. **Bâti dans le
back-office existant (décision 14/09), pas un service séparé.** » Épique `SCRUM-79`.

*Lot — DiddiFreeID / Identite* (page 950291) : « DiddiFreeID reste le fournisseur d'identité et de
projections globales. **Les profils métier, le KYC, les véhicules, les scores et l'éligibilité
opérationnelle restent propriétaires de DiddiGo**, DiddiSend, DiddiPay et des autres modules. » Contrat
actif : `GET /identity/v1/pro/me`.

---

## 7. Cas limites ouverts touchant Go

Du `JOURNAL_CAS_PARTICULIERS.md` — registre de travail, **aucune entrée n'est une preuve de
fonctionnalité livrée** :

- `EDGE-004` Panne ou retard sans danger immédiat — contact client, signalement, reprise support,
  remontée du ticket. **Pas d'astreinte opérationnelle promise.** Le ticket doit conserver mission,
  acteurs, chronologie, solution convenue et **statut réel du paiement**.
- `EDGE-005` Blessure, agression, danger immédiat — priorité à la sécurité ; le support **n'est pas
  présenté comme un service d'urgence**. Afficher un accès aux secours locaux, permettre un signalement
  après mise en sécurité. **Ne pas bloquer l'accès à l'aide pour impayé** ; ne pas promettre de secours
  dépêchés par DiddiFree.
- `EDGE-006` Téléphone perdu, changement de bénéficiaire — réauthentification et vérification du nouveau
  numéro ; **bénéficiaire d'un retrait lancé non modifiable**. Un OTP sur un nouveau numéro **ne
  transfère pas** un ancien compte.
- `EDGE-007` Identités multiples et bonus — protection anti-fraude requise, bonus en V1, **pas de
  sanction automatique** sur un appareil partagé.

## 8. Recettes attendues côté Go

De la `MATRICE_ALIGNEMENT_RECETTE.md`, ligne « Recherche Go, `PROD-027` », rattachement candidat
`SCRUM-63` :

> Paliers 30/60/180 s jusqu'à 1/3/5 km ; candidat proche nouvellement libre éligible ; fin à 270 s ;
> acceptation tardive concurrente à expiration traitée sans double attribution.

La matrice note comme constat, non comme décision : « défauts code 5 km initial, plafond 15 km, budget
120 s ».

Ordre de travail proposé par la matrice : **1.** paiements, dettes, encours et retraits — sécuriser les
transitions et écritures avant les parcours qui les utilisent ; **2.** Food ; **3.** Send ; **4.** Go,
recherche bornée et reprise sans duplication ; **5.** Common, support, droits, conservation, preuves de
recette et restauration.

Preuve à joindre par scénario : version ou commit, environnement, date, préconditions, identifiants QA,
action, résultat attendu et obtenu, traces expurgées, écritures financières concernées, validateur QA.
**Ne jamais joindre secrets, OTP ou documents personnels à Jira.**
