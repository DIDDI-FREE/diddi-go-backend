# Parcours DiddiGo — tels que le produit les a décidés

Date de relevé : 9 octobre 2026.

Catalogue de la cible : fonctionnalités, flux, cas limites, exigences non fonctionnelles. Le pendant côté
code est `PARCOURS_CODE_DIDDIGO.md`, de structure identique.

**Aucun montant ici.** Les valeurs, seuils et plafonds sont dans `PARAMETRES_CONFIGURABLES.md` ; ce
document ne décrit que le comportement et nomme la clé de paramètre quand une valeur intervient. C'est la
règle `PROD-043` : les comportements constituent le périmètre produit, les montants sont centralisés
ailleurs et **ne sont pas figés pour le lancement**.

Sources : `E:\DIDDI AI\diddi-scope-document` — registre de 48 décisions `PROD-xxx`, document des parcours
MVP / V1 / Later, matrice d'alignement de recette, journal des cas particuliers. Rapprochement Jira en
section 6.

Deux avertissements portés par les sources elles-mêmes, qui s'appliquent à tout ce document :

> « Une fonctionnalité incluse dans une phase n'est ni automatiquement développée, ni automatiquement
> validée. Une API présente et un ticket terminé ne remplacent pas une recette sur la version réellement
> déployée. »

> « Les décisions définissent la cible, pas l'état de livraison. »

---

## 1. Inventaire des fonctionnalités

### 1.1 Passager — MVP

| Fonctionnalité | Décision | Jira |
| --- | --- | --- |
| Saisir départ et destination, par texte ou par dictée | `PROD-018` | UC-009 ✅ |
| Vérifier le lieu proposé sur la carte avant de confirmer | parcours Common | — |
| Consulter une estimation avant de confirmer | `PROD-015` | UC-009 ✅ |
| Comparer trois niveaux de confort | `PROD-015` | UC-017 ○ |
| Choisir espèces ou Mobile Money | `PROD-005` | UC-254 ✅ |
| Commander une course | `.docx` §Go | UC-010 ✅ |
| Suivre l'approche du véhicule et l'état de la mission | `PROD-016` | UC-011 ✅ · UC-012 ○ |
| Être informé qu'aucun chauffeur n'est disponible, et pouvoir relancer | `PROD-027` | UC-253 ○ |
| Contacter le chauffeur par appel | `PROD-016` | — |
| Demander un arrêt et voir le surcoût d'attente | `PROD-026` | UC-258 ○ |
| Ajouter une escale, voir le surcoût et le valider | `PROD-026` | UC-259 ○ |
| Annuler une course | `PROD-014` | UC-013 ✅ |
| Annuler sans frais si le chauffeur reste silencieux au-delà du délai | `PROD-014` | UC-257 ○ |
| Partager le suivi de sa course | `.docx` §Go | UC-014 ✅ |
| Signaler une urgence | `PROD-036`, `.docx` §Go | UC-015 ✅ |
| Noter la course, texte facultatif | `PROD-016` | UC-016 ✅ |
| Retrouver la course et son état final dans l'historique | `PROD-011`, `PROD-016` | — |
| Ouvrir l'aide depuis la course et déposer une réclamation | `PROD-017` | — |
| Demander la suppression de son compte | `PROD-010` | — |

### 1.2 Chauffeur — MVP

| Fonctionnalité | Décision | Jira |
| --- | --- | --- |
| Créer son profil métier et fournir ses justificatifs | parcours Common | UC-018 ✅ · UC-019 ✅ |
| Déclarer un véhicule et ses documents | parcours Common | UC-020 ✅ · UC-021 ✅ · UC-270 ✅ |
| Suivre l'état de son dossier, corriger un refus motivé et resoumettre | parcours Common | UC-022 ✅ |
| Renouveler un document arrivé à expiration avant blocage | — | UC-275 ✦ |
| Passer en ligne et hors ligne | `PROD-003` | UC-023 ✅ · UC-024 ✅ |
| Recevoir une offre identifiable avec les informations nécessaires | parcours Common | UC-025 ✅ |
| Accepter ou refuser une offre | `.docx` §Go | UC-026 ✅ · UC-027 ✅ |
| Signaler son arrivée au point de prise en charge | **`PROD-012`** | — |
| Démarrer la course quand le client est à bord | **`PROD-013`** | UC-029 ✅ |
| Utiliser un code de prise en charge quand le GPS est inexploitable | **`PROD-013`** | — |
| Activer le mode attente, bloqué tant que le véhicule roule | `PROD-012` | UC-271 ✅ |
| Enregistrer une escale demandée oralement et faire valider le supplément | `PROD-026` | UC-272 ✅ |
| Annuler sans pénalité quand le passager est absent après le délai | `PROD-027` | UC-273 ✅ |
| Envoyer sa position pendant la course | `.docx` §Go | UC-028 ✅ |
| Signaler une panne, un accident ou un incident | `PROD-036` | — |
| Consulter ses gains et son historique | `PROD-003` | UC-030 ✅ · UC-031 ✅ |
| Recharger son wallet | `PROD-003` | — |
| **Demander un retrait de ses gains dans l'application** | **`PROD-003`, `PROD-032`** | — |
| Voir montant débité, frais exacts et montant reçu avant de confirmer un retrait | `PROD-032` | — |

### 1.3 Opérateur et transverse — MVP

| Fonctionnalité | Décision |
| --- | --- |
| Examiner un dossier relevant de son rôle, valider ou refuser avec motif compréhensible | parcours Common |
| Suspendre un accès de façon visible, motivée et tracée, avec voie de contestation | parcours Common |
| Retrouver l'historique de ses propres actions, chaque action sensible portant acteur, motif, date et résultat | parcours Common, `PROD-037` |
| Décider un remboursement, validé par un administrateur | `PROD-034` |
| Rembourser un paiement cash par voie numérique vers un bénéficiaire vérifié | `PROD-042` |
| Rapprocher les mouvements autorisés, sans les dupliquer | `PROD-037` |
| Accueil conversationnel automatique H24, création et suivi de ticket, reprise humaine avec contexte | `PROD-017` |
| Suivre les indicateurs de base du module | `PROD-010` |
| Exporter la comptabilité vers Odoo | `PROD-010` |

### 1.4 Hors MVP

**V1** — reçu client de paiement (`PROD-045`) ; majoration automatique offre/demande plafonnée
(`PROD-015`) ; tarification différenciée par zone (`PROD-015`) ; score opérationnel avec effets sur
attribution, attente et prix (`PROD-020`) ; partenaires et gestion de flottes (`PROD-001`) ; lieux
favoris et historique de gains détaillé ; messagerie en mission et appels Internet intégrés
(`PROD-016`) ; fidélité, points, bonus et parrainage (`PROD-009`) ; carte bancaire (`PROD-005`) ;
reporting détaillé et ventilé (`PROD-010`) ; renforcement anti-fraude (`PROD-008`).

**Later** — course programmée, masquée au lancement sans supprimer son implémentation (`PROD-016`) ;
carte des zones de demande visible aux passagers et chauffeurs (`PROD-015`) ; initiation d'un retrait par
le Backoffice (`PROD-003`) ; DiddiFund, prêts, financements et score de crédit (`PROD-025`) ; IA
anti-fraude (`PROD-008`).

---

## 2. Flux

### 2.1 Entrée dans le service

Le consommateur saisit son numéro, reçoit un OTP, le confirme, accède à son profil, puis utilise Go, Send
et Food **avec la même identité**. À son retour, la session est conservée ou renouvelée de manière
contrôlée ; si elle n'est plus valide, il se reconnecte **sans perdre l'accès à son historique**.

`PROD-007` — le numéro de téléphone est le mode de connexion prioritaire, par SMS **ou WhatsApp** ;
l'email est uniquement un secours.

Le parcours doit expliquer les échecs : code erroné, code expiré, délai avant un nouvel envoi, numéro
invalide, indisponibilité du prestataire. **Une panne SMS ne doit pas être présentée comme une erreur de
l'utilisateur.** L'authentification consommateur ne remplace pas la vérification professionnelle.

### 2.2 Activation du chauffeur

Le professionnel crée son profil métier, fournit informations et justificatifs, puis voit son dossier en
attente. **Le véhicule est également contrôlé.** Un opérateur autorisé examine les pièces et accepte ou
refuse **avec un motif compréhensible**. Le professionnel peut corriger les éléments refusés et
resoumettre.

Règle structurante : **l'activation ne résulte pas uniquement de la création du compte Identity** — le
module métier conserve ses conditions d'éligibilité. Le professionnel ne peut ni passer en activité ni
retirer des gains avant les validations requises. Une suspension doit être visible, motivée et tracée,
avec une procédure de contestation ou de contact support.

Un seuil d'éligibilité à la mise en ligne existe (`go.online_min_balance`), **distinct** du cash dû et du
minimum de retrait.

### 2.3 Cycle de vie d'une course

```
devis       estimation présentée avant confirmation
            validité bornée (go.quote_validity) ; au-delà, rafraîchissement obligatoire
            demande de devis enregistrée : date, point de prise en charge, confort,
            référence de déduplication, offre disponible, résultat du parcours
            une seule demande comptée par passager dans le voisinage et la fenêtre
            aucune majoration automatique

recherche   trois phases successives, rayon et durée croissants
            les chauffeurs proches devenus libres restent candidats
            à épuisement : nouvelle recherche explicite proposée
            en l'absence de chauffeur : indisponibilité affichée, sans garantie

attribution le chauffeur accepte, l'attribution est confirmée au passager
            une notification retardée ne doit pas permettre d'accepter
            une offre déjà attribuée

approche    le passager suit l'approche et dispose du moyen de contact retenu
            le chauffeur rejoint le point de départ

ARRIVÉE     le chauffeur signale son arrivée
            validée si distance < go.arrival_radius du point de prise en charge
            → démarre l'attente de prise en charge
            → franchise gratuite, puis minutes supplémentaires complètes facturées
            → statut d'arrivée et attente visibles dans le parcours et le prix

départ      démarrage autorisé si proximité, fraîcheur et précision des deux
            positions sont satisfaisantes
            sinon : code de prise en charge à six chiffres, usage unique
            sinon : intervention du support
            le démarrage arrête le compteur d'attente

course      escales : franchise par escale, puis prorata à la seconde
            suppléments visibles, nouveau montant applicable annoncé
            le prix de référence est conservé, hors attente et modifications de trajet

fin         paiement après réalisation de la mission
            cash : le chauffeur encaisse, la commission due est inscrite à son wallet
            numérique : les gains sont crédités au résultat financier confirmé
```

### 2.4 Annulation et fin anticipée

`PROD-014` distingue deux régimes, séparés par le démarrage de la course.

**Avant le démarrage** — c'est une annulation : **aucun frais**, attente acquise comprise.

**Après le démarrage** — c'est une **fin anticipée** : facturer le trajet effectué avec le barème et le
coefficient **acceptés au départ**, puis ajouter seulement attente et suppléments acquis. Si le total
reste sous le seuil `go.early_end_free_threshold`, il est gratuit ; au seuil, il est dû.

Dans les deux cas, le parcours indique **qui** a annulé, **à quelle étape**, et **quelles conséquences**
s'appliquent. L'utilisateur retrouve la course et son état final dans l'historique. Les malus
opérationnels **ne sont pas activés au MVP**.

Après le délai `go.absent_passenger_delay` sans commencement de course, le chauffeur peut déclarer le
client absent et annuler ; l'annulation reste gratuite.

### 2.5 Continuité

`PROD-011` — quitter, fermer ou perdre la connexion **ne met pas fin** à une course. Le passager et le
chauffeur retrouvent la course et poursuivent **depuis son état réel**. La reprise **ne crée pas une
nouvelle mission** et **ne réinitialise pas le compteur d'attente**. La même exigence s'applique aux
livraisons Send et aux commandes Food.

### 2.6 Paiement et régularisation

`PROD-030` — paiement **après** réalisation de la mission ou fin anticipée, y compris en numérique. Ne
pas confondre préparation technique d'un paiement et encaissement. En cas d'échec : afficher *Réessayer*,
permettre un autre moyen, **conserver la somme due**, et **bloquer une nouvelle commande payante** jusqu'à
régularisation — **sans bloquer l'accès au support ni à l'historique**.

`PROD-031` — le client peut passer du Mobile Money aux espèces après confirmation. La bascule est
enregistrée côté serveur et les deux parties sont notifiées. Tout succès numérique tardif après un
encaissement cash est **détecté et signalé automatiquement comme doublon**, sans dépendre de la seule
réclamation client ; le remboursement du trop-perçu suit une validation administrative.

`PROD-040` — au lancement, les impayés sont **cloisonnés par module** : une dette Go ne bloque pas
automatiquement Food ou Send. Une fraude vérifiée peut conduire à une restriction globale, **décidée par
un humain**, distincte du blocage automatique pour impayé.

### 2.7 Support

`PROD-017` — accueil conversationnel automatique H24 : écoute, collecte des informations, mission liée,
réponse fondée sur une aide validée et les données autorisées. Notification du support, création du
ticket quand c'est nécessaire, accusé de réception avec référence, puis transmission du contexte aux
humains.

`PROD-037` — l'agent support consulte le nécessaire, explique, documente et **propose**.
L'administrateur support **décide dans sa délégation**. La finance **exécute et rapproche** les mouvements
autorisés. Les rôles ne confèrent pas implicitement tous les droits.

Limites explicites : l'IA **ne décide pas** d'un remboursement, d'une sanction ou de l'issue d'un litige.
Elle ne prétend pas qu'un remboursement est effectué si le système ne le confirme pas. Elle ne révèle
jamais les informations d'un autre utilisateur. **L'accueil automatique H24 ne signifie pas qu'un humain
est présent H24.**

### 2.8 Collecte Pilotage

Le responsable Go retrouve les courses réalisées ou annulées et leurs montants. Le Pilotage transverse
rassemble ces informations **sans remplacer les journaux métier**. Indicateurs proposés au MVP : volumes,
taux d'achèvement et d'échec, montants encaissés, commissions, retraits en attente, dettes cash, tickets
non résolus. Le dictionnaire définit chaque indicateur, sa période, sa source et sa fréquence de mise à
jour **avant la recette**.

Exigence centrale : **en cas de panne d'un module, le tableau de bord indique une indisponibilité ou une
donnée ancienne plutôt qu'un résultat artificiellement nul.** Un identifiant de mission doit permettre de
retrouver son parcours entre Identity, le module métier, Send et Pay.

---

## 3. Cas limites à traiter

### 3.1 Énoncés dans les parcours

| Cas | Comportement attendu |
| --- | --- |
| Code OTP erroné ou expiré | expliqué distinctement, avec le délai avant un nouvel envoi |
| Numéro invalide | expliqué |
| Prestataire SMS indisponible | **jamais présenté comme une erreur de l'utilisateur** |
| Session expirée | reconnexion **sans perte d'accès à l'historique** |
| Offre expirée, refus, absence de chauffeur, perte de connexion | **issue explicite** et reprise cohérente |
| Notification retardée sur une offre déjà attribuée | acceptation impossible |
| Micro refusé, transcription échouée, réseau insuffisant | saisie clavier **reste disponible** |
| Deux lieux homonymes | la voix **ne choisit pas silencieusement** ; le client confirme toujours le lieu |
| Dictée | **ne déclenche ni commande ni dépense** |
| GPS inexploitable au démarrage | code de prise en charge à six chiffres ; au-delà de la limite d'essais, blocage et orientation vers le support |
| Ni GPS exploitable ni code | intervention du support |
| Reconnexion pendant une attente | **pas de double comptage** |
| Rejeu d'une mutation après problème réseau | **la mutation ne doit pas être répétée** |
| Accès aux données d'un autre utilisateur, d'un autre restaurant, d'un service au mauvais scope | refusé — scénario de recette explicite |
| Panne de l'assistant | un **formulaire de signalement** reste utilisable |
| Tentative de manipulation de l'assistant | fait partie de la recette MVP |
| Opération financière incohérente | refusée selon une règle connue, ou transmise à une **revue humaine** |
| Suspicion de fraude | **distincte** d'une fraude confirmée ; un incident isolé ne déclenche pas de sanction dans tous les modules |

### 3.2 Journal des cas particuliers

Du `JOURNAL_CAS_PARTICULIERS.md`. **Registre de travail** : aucune entrée n'est une décision finale ni
une preuve de fonctionnalité livrée. Les quatre entrées qui touchent Go :

| ID | Cas | Décision acquise | Reste à fixer |
| --- | --- | --- | --- |
| `EDGE-004` | Panne ou retard sans danger immédiat | contact client, discussion, signalement, reprise support, remontée du ticket. **Pas d'astreinte opérationnelle promise.** | enregistrer la solution convenue ; accord explicite si le coût ou le trajet change |
| `EDGE-005` | Blessure, agression, danger immédiat | priorité à la sécurité ; le support **n'est pas** un service d'urgence | afficher un accès aux secours locaux, permettre un signalement après mise en sécurité, sans attendre une négociation client. **Ne pas bloquer l'accès à l'aide pour impayé** ; ne pas promettre de secours dépêchés par DiddiFree |
| `EDGE-006` | Téléphone perdu, changement de bénéficiaire | réauthentification et vérification du nouveau numéro ; **bénéficiaire d'un retrait lancé non modifiable** | processus de récupération distinct, preuves adaptées, notification et révocation des sessions compromises. **Un OTP sur un nouveau numéro ne transfère pas un ancien compte** |
| `EDGE-007` | Identités multiples et bonus | protection anti-fraude requise ; bonus en V1 ; **pas de sanction automatique** sur un appareil partagé | conditions de campagne, attribution après prestation et paiement, déduplication, voie de recours |

### 3.3 Recette attendue sur la recherche Go

De la `MATRICE_ALIGNEMENT_RECETTE.md`, ligne `PROD-027`, rattachement candidat `SCRUM-63` :

> Paliers successifs jusqu'au rayon maximal ; candidat proche nouvellement libre éligible ; fin au budget
> total ; **acceptation tardive concurrente à expiration traitée sans double attribution**.

L'état connu y est noté comme constat, non comme décision : « défauts code 5 km initial, plafond 15 km,
budget 120 s ».

### 3.4 Ordre de travail proposé

La matrice ordonne l'analyse ainsi : **1.** paiements, dettes, encours et retraits — sécuriser les
transitions et écritures **avant** les parcours qui les utilisent ; **2.** Food ; **3.** Send ; **4.** Go,
recherche bornée et reprise sans duplication ; **5.** Common — support, droits, conservation, preuves de
recette et restauration.

---

## 4. Exigences non fonctionnelles

### 4.1 Règles d'architecture

`PROD-002` et le guide d'intégration interne posent quatre règles qui ne se négocient pas : chaque service
reste **propriétaire de ses données et de ses règles métier** ; les outils internes **ne lisent jamais la
base d'un autre service** ; **les navigateurs ne reçoivent jamais de credentials de service** ; les
résumés Pilotage **ne retournent jamais de donnée personnelle** ni de dump brut.

Cinquième règle, transverse : **une panne de source ne devient jamais un KPI à zéro** — il faut retourner
ou exposer un état de fraîcheur dégradé.

### 4.2 Traçabilité et auditabilité

Chaque action sensible porte **acteur, motif, date et résultat**. Chaque mission et opération financière
produit un historique vérifiable : création, attribution, réalisation, annulation, paiement, incident,
correction. Les événements doivent pouvoir être **corrélés et rejoués sans doublon**. Le recours au code
de prise en charge est tracé. Un transfert exceptionnel est tracé et vérifié.

### 4.3 Identité et séparation des pouvoirs

Une personne possède **une seule identité DiddiFreeID**, puis des capacités métier locales. Les services
utilisent leurs propres identités techniques et des **permissions limitées**. Les nouvelles intégrations
internes utilisent des jetons service-à-service ; les secrets statiques ne sont tolérés que pendant une
migration ou un secours documenté. Un coursier ne voit pas les finances d'un restaurant ; un membre
cuisine ne demande pas un retrait ; un service ne modifie pas librement les profils d'un autre module.

### 4.4 Intégrité financière

Le total des écritures **doit expliquer le solde**. **Aucun rejeu ne doit produire un second mouvement.**
Aucune perte d'écriture financière ni double exécution n'est tolérée. Un remboursement numérique et la
restitution physique d'espèces sont **deux opérations différentes**. La commission Go porte sur le montant
total de la prestation encaissée, attente et suppléments compris (`PROD-004`). Les montants et règles
acceptés pour les opérations déjà engagées sont conservés : **aucune réécriture d'historique**.

### 4.5 Capacité

Proposition du document, **à valider** : produit et exploitation définissent une enveloppe de lancement —
utilisateurs simultanés, professionnels en ligne, nouvelles missions par minute, positions par seconde,
opérations financières par minute — inscrite dans un rapport de charge. « Sans elles, on peut mesurer un
système, mais pas conclure qu'il supportera le lancement attendu. »

Test proposé : une heure au pic prévu, quinze minutes à deux fois ce pic, puis quatre heures d'endurance
au trafic nominal. Objectifs initiaux proposés : moins de 1 % d'erreurs serveur sur requêtes valides ;
p95 sous deux secondes en lecture principale et trois secondes sur les commandes internes, hors attente
explicite du prestataire ou du matching. **Les parcours asynchrones doivent exposer leur attente plutôt
que bloquer silencieusement.** Prévoir des **limites d'admission** plutôt qu'une saturation incontrôlée.
Seuils à ajuster après une première mesure, puis à approuver.

### 4.6 Sauvegarde et restauration

Proposition **à valider** : sauvegarde quotidienne chiffrée, stockée séparément de l'environnement
applicatif, contrôle quotidien du succès, conservation glissante. Pour les bases transactionnelles,
récupération à un instant donné, avec objectifs de perte maximale et de rétablissement **restant à
valider techniquement et financièrement**. Inclure bases, pièces, médias, configuration et procédure de
récupération des secrets.

Restauration isolée **avant le lancement**, puis mensuelle. Contrôler intégrité, droits d'accès, liens
vers les fichiers et rapprochement financier. Point critique : **les opérations prestataire survenues
après le point restauré doivent être réconciliées avant toute reprise des payouts — une restauration
réussie ne suffit pas à autoriser les transferts.**

### 4.7 Astreinte et incidents

Proposition **à valider** : un référent technique principal et un suppléant, contacts testés. Pour les
incidents critiques de sécurité, d'indisponibilité générale ou d'argent : alerte immédiate, accusé de
prise en charge sous quinze minutes, première communication sous trente minutes — **ce n'est pas une
promesse de résolution dans ces délais**. « Si l'équipe ne peut pas couvrir H24, il faut revoir la
promesse d'exploitation ou mobiliser une couverture externe. »

Le support humain conserve des **horaires explicitement annoncés**. L'assistant accuse réception mais
**ne se présente pas comme un service d'urgence**. Chaque incident majeur produit un compte rendu et des
actions préventives suivies.

### 4.8 Conservation des données

`PROD-038` — GPS détaillé de mission conservé une durée bornée, puis suppression des traces précises au
profit de **statistiques agrégées non identifiantes** ; les preuves nécessaires aux litiges sont
préservées séparément. Conversations soumises à leur propre durée (`PROD-028`). Le jeu de données est
préparé et contrôlé avant tout entraînement — **la suppression du nom ne suffit pas à anonymiser une
conversation**. Mise en œuvre **soumise à validation juridique** des finalités, durées et exceptions.

Suppression de compte : une mission active, une dette ou un solde déclenche un **parcours de résolution
explicite**, pas un silence de l'application. La politique finale distingue fermeture du compte,
effacement des données et conservation justifiée des écritures financières.

### 4.9 Qualité et preuve de recette

`PROD-039` — « Exiger des recettes avec preuves, des restaurations réellement testées et un rapprochement
financier. Démontrer les objectifs d'exploitation avant de les promettre aux utilisateurs. **Une
validation produit ne constitue ni une recette réussie ni une preuve de capacité opérationnelle.** »

Définition du passage à « À tester » : code et migrations prêts, tests automatisés pertinents qui
passent, contrat consommé documenté, version à tester identifiée, scénario reproductible et limites
connues fournis par le développeur. **« La seule présence d'une route ne suffit pas. »**

Le passage à « Terminé » est une **décision QA** après exécution des critères. « Un écart connu ne
disparaît pas parce qu'il figure dans une note : il reçoit un responsable, une priorité et une décision
explicite. »

Preuve par scénario : identifiant, date, environnement, commit backend et version mobile, préconditions
et données QA, étapes, résultat attendu et obtenu, références de mission, transaction et corrélation.
Captures ou vidéo courte pour l'interface ; logs expurgés et rapprochement des écritures pour l'argent.
**Jamais de secret, d'OTP, de jeton ni de pièce d'identité réelle dans Jira.**

Critère de sortie proposé : tous les parcours MVP critiques passent ; **aucun défaut bloquant de
sécurité, d'argent ou de perte de données n'est ouvert** ; les défauts mineurs restants ont un
contournement acceptable et une acceptation écrite. « **Le nombre de tickets fermés ne sert pas de mesure
de préparation au lancement.** »

En l'absence de QA dédiée, désigner un responsable de recette **différent de l'auteur du changement**.

### 4.10 Mobile et publication

La recette concerne les deux applications, consommateur et professionnelle, avec des versions
identifiées. Android testé sur appareils physiques **modestes et récents**, sur les versions système
retenues, **avec réseau mobile dégradé**. iOS reste un arbitrage explicite : ne pas annoncer une
disponibilité qui n'a pas été construite, testée et acceptée par le store.

Progression proposée : distribution interne, bêta fermée avec pilotes, correction, puis diffusion
graduelle. « Les seuils de passage sont les critères QA du présent document, **pas seulement l'absence de
crash au démarrage**. » Tester aussi l'installation neuve, la mise à jour, la reconnexion, et la
**compatibilité entre une application légèrement ancienne et les API déployées**.

Notifications critiques à vérifier application ouverte, en arrière-plan et **téléphone verrouillé**, sur
appareils physiques représentatifs, avec arrière-plan, batterie limitée et reprise après coupure.

### 4.11 Responsabilités nommées

Les rôles doivent être attribués à des **personnes nommées avant la campagne** — le document précise
qu'ils ne supposent pas que l'équipe possède déjà tous ces postes. Produit valide parcours, règles
tarifaires et exclusions de phase. Backend prépare tests, migrations et diagnostics. Mobile vérifie
écrans, permissions, notifications et reprises réseau. QA coordonne les scénarios, collecte les preuves
et prononce la validation. Finance valide commissions, frais, journaux, rapprochements et exports.
Support valide catégories, réponses de l'assistant, transferts, priorités et moyens de contact.
Exploitation prépare surveillance, sauvegardes, restauration, capacité et retour arrière. La direction
produit décide du lancement. **Le propriétaire de l'environnement reste responsable des déploiements
Portainer.**

---

## 5. Campagne de recette Go

Troisième étape de la campagne de bout en bout, textuellement :

> « Pour Go, réaliser une course numérique et une course cash, puis attente, escale, annulation,
> réclamation et retrait chauffeur. »

Les étapes qui l'encadrent et qui conditionnent Go — première étape, accès et identité professionnelle :
inscription SMS, code erroné ou expiré, reprise de session, changement de permissions ; soumission, refus
motivé, correction, validation d'un dossier ; pièces protégées ; impossibilité d'opérer avant validation ;
effet d'une suspension ; accès d'un autre utilisateur et d'un service au mauvais scope.

Deuxième étape, argent et retraits : montants exacts avant et après opération, arrondis, frais affichés,
historique ; succès, échec définitif, timeout, **callback tardif ou répété**, deux demandes concurrentes,
bénéficiaire invalide. « **Les canaux prestataires réellement prévus pour le lancement doivent être
testés, pas uniquement simulés.** »

Cinquième étape, exploitation : rapprocher une journée contrôlée entre missions, wallets, Pay, prestataire
et reporting ; vérifier source indisponible, alertes, export Odoo, suppression de compte, restauration et
retour arrière. « Les tests dangereux se déroulent dans un environnement isolé, jamais contre des fonds ou
données réels sans protocole spécifique autorisé. »

---

## 6. Rapprochement Jira

### 6.1 Couverture des parcours cible par des tickets

Les deux lots DiddiGo (`SCRUM-64` passager, `SCRUM-65` chauffeur) portent **48 tickets de cas d'usage**
qui couvrent la quasi-totalité des parcours MVP décrits ci-dessus — à **trois exceptions notables** :

| Parcours cible MVP | Décision | Ticket |
| --- | --- | --- |
| Le chauffeur **signale son arrivée**, validée par la proximité, et déclenche l'attente de prise en charge | `PROD-012` | **aucun ticket identifié** |
| **Code de prise en charge à six chiffres** en secours GPS, usage unique, limite d'essais | `PROD-013` | **aucun ticket identifié** |
| Le professionnel **demande un retrait** dans l'application, avec montant débité, frais et net affichés | `PROD-003`, `PROD-032` | **aucun ticket DiddiGo identifié** |

Ces trois lignes correspondent au livrable **BE015** (« Attente facturée, escales, annulation et
signalement urgent », MVP P0, 14→23 oct, *à engager*) et **BE016** (« Wallet chauffeur, commission,
recharge et retrait », MVP P0, même fenêtre, *à engager*). Le périmètre produit existe, le planning
existe, mais le découpage en tickets reste à faire.

La fin anticipée facturée (`PROD-014`) n'a pas non plus de ticket identifié — seul UC-273 couvre
l'annulation sans pénalité pour passager absent.

### 6.2 Parcours cible V1 déjà ticketés

UC-260 adresses favorites · UC-263 carte de chaleur · UC-264 badge sortie de zone · UC-265 mode retour
maison · UC-266 mode ma destination · UC-274 points de priorité consultables · UC-268 et UC-269 contrôle
selfie d'inactivité. Reclassés V2 : UC-261 commander pour autrui · UC-262 course programmée · UC-267
zones de préférence · UC-276 déclaration de préjudice · UC-277 chauffeur remplaçant.

Ces tickets anticipent des parcours que le document place en V1 ou Later. Leur présence au backlog n'est
pas un engagement de phase.

### 6.3 Décisions du 9 octobre non encore ticketées

Les compléments `PROD-035` à `PROD-048` ont été validés le 9 octobre — le jour de ce relevé. Pour Go, les
décisions suivantes n'ont pas de ticket identifié : `PROD-040` cloisonnement des impayés par module,
`PROD-042` remboursement d'un paiement cash par voie numérique, `PROD-043` séparation comportement et
paramètres, `PROD-045` reçu client (V1), `PROD-046` identité et avantages, `PROD-048` tenue du journal
des cas particuliers.

C'est attendu : la matrice d'alignement précise que les références Jira y sont « des rattachements
candidats, pas des tickets modifiés », et demande de « rapprocher cette matrice des tickets existants
**avant toute création de ticket** ».

### 6.4 Tickets de cadrage transverses

`SCRUM-79` Lot Pilotage Direction Générale — bâti dans le back-office existant, décision du 14/09, **pas
un service séparé**. `SCRUM-405` standardiser le protocole S2S entre backends. `SCRUM-415` et `SCRUM-425`
ADR du contrat JWT service-à-service. `SCRUM-435` valider la séparation avec la projection des capacités.
`SCRUM-424` secrets, observabilité et runbook Pilotage. `SCRUM-423` sécurité, rotation et révocation des
jetons de service.

### 6.5 Règle de lecture des états Jira

Posée par le planning de lancement : « *À tester* vaut 85 % indicatif dans Jira source. L'avancement d'un
livrable intégré reste à renseigner après revue ; **un ticket terminé ne suffit pas à le déclarer
validé**. » Et par le registre : « Jira donne l'état réel des tickets ; le document définit le
périmètre ; les arbitrages du 09/10 complètent les règles. »

**Légende** — ✅ terminé · ✦ à tester · ○ ouvert ou en revue
