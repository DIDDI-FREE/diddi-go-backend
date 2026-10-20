# Décisions à prendre et zones ambiguës, par parcours

Relevé du 9 octobre 2026. Annexe de [`PARCOURS_MVP_DIDDIGO.md`](PARCOURS_MVP_DIDDIGO.md).

## Ce que contient ce document

Les entrées ouvertes que les sources déclarent elles-mêmes, rattachées aux parcours par le lot
d'origine. **Rien n'est ajouté, rien n'est arbitré** : chaque ligne est le texte de son registre.

| Registre | Entrées sur le périmètre | Ce que le registre dit de lui-même |
| --- | --- | --- |
| `etat/a-trancher.md` | 208 | « Chaque ligne est une décision manquante. Une décision non prise ne bloque pas une fiche : elle bloque les use cases cités. » |
| `etat/a-verifier.md` | 106 | « Une affirmation qui n'a pas pu être confirmée par la lecture du code, ou un nom technique supposé plutôt que constaté. » |
| `etat/contradictions.md` | 59 | « Chaque ligne oppose deux sources. Une contradiction n'est pas une erreur à corriger silencieusement. Elle appelle un arbitrage. » |

Ces trois registres sont datés du **14 septembre 2026** et produits par `checks/agreger.py`. Leurs
constats de code peuvent donc être dépassés — les constats à jour sont dans
[`PARCOURS_MVP_COMPLEMENT_UC.md`](PARCOURS_MVP_COMPLEMENT_UC.md). Leur valeur ici est la **question
posée**, pas l'état du code qu'elles supposent.

## Comment les entrées sont rattachées aux parcours

**Par le lot d'origine que chaque registre déclare.** Les registres ne nomment aucun parcours, et
aucun lien n'est déclaré entre les `PAR-xxx` du planning et les lots du corpus.

Conséquence à connaître : une entrée du lot `diddigo-passager` apparaît sous **tous** les parcours
DiddiGo rattachés à ce lot. Une même décision peut donc se lire sous plusieurs parcours, et les
décomptes par parcours **ne s'additionnent pas**. Le total réel est celui du tableau ci-dessus.

Un exemple de ce décalage, à garder en tête en lisant : une contradiction du 14/09 énonce
« `services.py` applique un taux de commission de 8 % via la constante `_COMMISSION_RATE`, la décision
du 14/09 fixe la commission DiddiGo à 10 % ». Le registre produit du 9 octobre fixe ce taux à 18 %, et
le code est toujours à 8 %. Trois valeurs, trois dates. On les montre, on ne les réconcilie pas.

## Décisions du planning

Onglet *Décisions*, 9 octobre 2026. Reproduites telles quelles.

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

---

## Common — entrer dans le service et devenir professionnel

### PAR-001 — Créer son compte et retrouver sa session

**Décisions manquantes** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| que se passe-t-il si le canal d'envoi du code est indisponible ? existe-t-il un canal de secours ? | Portée MVP | — | Produit | `diddifreeid-identite` |
| quelle est la durée de vie d'un code à usage unique, et combien d'essais avant blocage ? | Portée MVP | — | Technique | `diddifreeid-identite` |
| un compte suspendu voit-il le motif de sa suspension ? | Portée MVP | UC-007 | Produit | `diddifreeid-identite` |
| un utilisateur peut-il changer le téléphone ou le courriel rattaché à son compte, et selon quelle procédure ? | Portée MVP | UC-005 | Produit | `diddifreeid-identite` |

**Faits à établir** — 6

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la durée de vie de 300 s configurée par défaut est-elle la valeur retenue ? | Portée MVP | — | Technique | `diddifreeid-identite` |
| le fournisseur d'envoi est-il surchargé sur l'instance de production ? | Portée MVP | — | — | `diddifreeid-identite` |
| le maximum de 5 essais configuré par défaut est-il la valeur retenue ? | Portée MVP | — | Technique | `diddifreeid-identite` |
| le sel d'empreinte des codes et le fournisseur d'envoi sont-ils surchargés sur l'instance de production ? | Portée MVP | — | Technique | `diddifreeid-identite` |
| les durées et seuils configurés par défaut sont-ils les valeurs retenues ? | Portée MVP | — | Technique | `diddifreeid-identite` |
| une déconnexion demandée hors ligne invalide-t-elle réellement le jeton côté serveur au retour du réseau, ou seulement localement ? | Portée MVP | — | Technique | `diddifreeid-identite` |

**Contradictions entre deux sources** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| DiddiFreeID écrit par défaut les codes d'authentification en clair dans les journaux ; cela ne peut pas rester vrai en production | Portée MVP | — | Technique | `diddifreeid-identite` |

---

### PAR-002 — Devenir chauffeur, coursier ou restaurant

**Décisions manquantes** — 24

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | Entrées structurantes | — | Produit | `diddigo-chauffeur` |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | Entrées structurantes | UC-274 | Produit | `diddigo-chauffeur` |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | Portée MVP | UC-259 | Produit | `diddigo-chauffeur` |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| la réputation et les points de priorité (voir UC-274) sont-ils attachés au chauffeur ou au véhicule dans ce cas de partage ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| quel est le barème de pénalité pour un refus d'offre, et comment la pénalité doublée sous 1 km s'applique-t-elle ? | Portée MVP | UC-027 | Produit | `diddigo-chauffeur` |
| quel est le barème de pénalité pour une annulation par le pro après acceptation ? | Portée MVP | UC-027, UC-273 | Produit | `diddigo-chauffeur` |
| quelle est la fenêtre de calcul des points — glissante, et sur quelle durée ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| quelle preuve, le cas échéant, le chauffeur doit-il produire pour une annulation pour absence ? | Portée MVP | — | Juridique | `diddigo-chauffeur` |
| quelles photos de véhicule sont obligatoires et lesquelles sont facultatives ? | Portée MVP | UC-270 | Produit | `diddigo-chauffeur` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie — tirage aléatoire à quelle fréquence, quel type de signalement, quelle définition d'un changement d'appareil ? | Portée MVP | — | — | `diddigo-chauffeur` |
| un préjudice matériel donne-t-il lieu à une indemnisation, et selon quelles règles ? | Portée MVP | — | Direction | `diddigo-chauffeur` |
| un véhicule peut-il être associé à plusieurs chauffeurs simultanément, ou un seul à la fois avec bascule explicite ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une annulation pour absence avant le délai est-elle simplement refusée, ou traitée comme une annulation ordinaire avec conséquence ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une déclaration de préjudice se distingue-t-elle d'un signalement de litige ordinaire (UC support-litiges), et si oui par quel circuit de traitement ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence est-elle un filtre strict (aucune offre hors zone) ou une simple priorité (offres hors zone toujours possibles) ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence peut-elle devenir un moyen détourné de refuser des courses sans pénalité de taux d'acceptation ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une validation orale de supplément engage-t-elle le passager en cas de litige ? | Portée V1 | UC-307 | Juridique | `diddigo-chauffeur` |
| combien de fois par jour le mode retour maison peut-il être activé ? | Portée V1 | UC-265 | Produit | `diddigo-chauffeur` |
| combien de temps avant l'expiration d'un document le chauffeur est-il alerté, et à quel moment est-il bloqué ? | Portée V1 | UC-275 | Juridique | `diddigo-chauffeur` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie ? | Portée V1 | UC-268 | Produit | `diddigo-chauffeur` |

**Faits à établir** — 17

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| ce cas est-il contrôlé côté serveur ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | Portée MVP | — | Technique | `diddigo-chauffeur` |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code fixe ce délai à 15 s via la constante OFFER_TTL_SECONDS ; la décision de la section 4 est encore à trancher, entre 60 s, 3 min et une recommandation de 20 s | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe le délai de réponse à une offre à 15 s ; la décision est encore à trancher | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le contrôle « véhicule à l'arrêt » s'appuie-t-il sur la dernière position connue, ou faut-il une confirmation explicite du chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le decoupage en zones utilisé par diddimap-cartographie et zones-couverture-et-majoration est-il réutilisable ici, ou faut-il un découpage propre au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le format brut du motif de rejet, avec l'identifiant technique de l'administrateur, est-il celui affiché au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le lien avec l'alerte d'urgence en cours de course (UC-urgence-et-securite-des-personnes) — une déclaration de préjudice grave doit-elle pouvoir déclencher la même chaîne d'alerte ? | Portée MVP | — | Sécurité | `diddigo-chauffeur` |
| le modèle de données actuel associe-t-il un véhicule à un seul chauffeur, ou la relation est-elle déjà multiple ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le passage hors ligne est-il bloqué pendant une course en cours, ou seulement sans effet sur le dispatch pendant ce temps, laissant la course se dérouler normalement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un chauffeur peut-il émettre une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-chauffeur` |

**Contradictions entre deux sources** — 6

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | Portée MVP | — | Produit | `diddigo-chauffeur` |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | Portée MVP | — | — | `diddigo-chauffeur` |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | Portée MVP | — | Produit | `diddigo-chauffeur` |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | Portée MVP | — | Produit | `diddigo-chauffeur` |

---

### PAR-003 — Valider et suspendre des dossiers

Aucune entrée ouverte rattachée à ce parcours par les registres.

### PAR-004 — Gérer ses données

**Limite déclarée par le planning.** Délais et exceptions de suppression à valider ; distinguer fermeture / effacement / conservation des écritures financières.

**Décisions manquantes** — 15

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la durée de conservation de chaque type de donnée — réponse partielle du 14/09, voir decisions-actees.md | Entrées structurantes | — | — | `compte-donnees-personnelles-et-conformite` |
| quelle est la durée de conservation de chaque type de donnée — pièces d'identité, traces brutes, traces agrégées, journaux, pièces comptables ? — réponse partielle du 14/09, voir decisions-actees.md : pièces comptables 10 ans ; anonymisation après 1 an, ou 60 jours sur demande de suppression ; données clients 12 mois ; traces brutes 6 mois ; pièces d'identité tant que le compte est actif, +3 mois après suspension permanente. Traces agrégées et journaux : non répondu, reste ouvert | Entrées structurantes | UC-200, UC-338 | Juridique | `compte-donnees-personnelles-et-conformite` |
| une déclaration ou une autorisation préalable ARTCI est-elle requise, et laquelle ? | Entrées structurantes | — | Juridique | `compte-donnees-personnelles-et-conformite` |
| que se passe-t-il si l'anonymisation réussit dans certains services et échoue dans d'autres — retry automatique, état intermédiaire visible, alerte ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| quel délai légal s'applique à une demande d'accès ou d'effacement, et à partir de quel événement court-il ? | Portée MVP | UC-340 | Juridique | `compte-donnees-personnelles-et-conformite` |
| quel est le délai de grâce entre la demande de suppression et l'anonymisation définitive ? | Portée MVP | UC-335 | Produit | `compte-donnees-personnelles-et-conformite` |
| quel format de fichier est attendu pour l'export (JSON structuré, PDF lisible, les deux) ? | Portée MVP | — | Produit | `compte-donnees-personnelles-et-conformite` |
| quelles données restent après anonymisation, et sous quelle forme, pour satisfaire la conservation comptable OHADA ? | Portée MVP | UC-333 | Juridique | `compte-donnees-personnelles-et-conformite` |
| un compte en délai de grâce peut-il encore commander une course ou une livraison, ou est-il restreint pendant cette période ? | Portée MVP | — | Produit | `compte-donnees-personnelles-et-conformite` |
| un litige ouvert de faible gravité (ex. objet oublié non réclamé) bloque-t-il la suppression au même titre qu'un litige financier ? | Portée MVP | — | Produit | `compte-donnees-personnelles-et-conformite` |
| un seuil minimal de traces est-il requis avant qu'un agrégat par segment et tranche horaire soit publié ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| une trace brute non encore agrégée est-elle agrégée en urgence avant purge, ou purgée sans agrégation si l'échéance est atteinte en premier ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| une trace trop courte pour un retrait d'extrémités significatif est-elle exclue de l'usage cartographique, ou traitée quand même avec un retrait proportionnel ? | Portée MVP | — | — | `compte-donnees-personnelles-et-conformite` |
| le retrait du consentement cartographique interrompt-il l'envoi des traces, ou seulement leur exploitation ? | Portée V1 | UC-339 | Juridique | `compte-donnees-personnelles-et-conformite` |
| quelle longueur retirer à chaque extrémité d'une trace GPS avant usage cartographique ? | Portée V1 | UC-336 | Technique | `compte-donnees-personnelles-et-conformite` |

**Faits à établir** — 6

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| des conditions d'utilisation et une politique de confidentialité existent-elles déjà sous une forme quelconque, prêtes à être versionnées ? | Portée MVP | — | Juridique | `compte-donnees-personnelles-et-conformite` |
| l'analyse de trace existante dans DiddiMap produit-elle déjà une agrégation par segment et tranche horaire, ou un autre type de résultat ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| le journal d'audit du back-office enregistre-t-il les lectures de données personnelles, ou seulement les actions de modification ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| le texte de justification présenté à l'utilisateur et soumis aux magasins d'applications existe-t-il déjà, ou reste-t-il à rédiger ? | Portée MVP | — | Produit | `compte-donnees-personnelles-et-conformite` |
| quel service porte l'orchestration d'une demande d'export ou d'anonymisation, et comment il connaît la liste des services à interroger | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |
| quel service porte l'orchestration de cette vérification croisée entre DiddiGo, DiddiSend et DiddiPay ? | Portée MVP | — | Technique | `compte-donnees-personnelles-et-conformite` |

**Contradictions entre deux sources** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la décision du 14/09 dit que les traces envoyées à DiddiMap sont anonymisées ; le code de DiddiGo transmet la trace entière, extrémités comprises, et ce use case demande précisément de retirer ces extrémités | Portée MVP | — | Juridique | `compte-donnees-personnelles-et-conformite` |

---

## Common — chercher, recevoir une offre, garder une trace

### PAR-005 — Trouver une destination par texte ou par voix

**Limite déclarée par le planning.** Langues du lancement et lieux d'Abidjan pour la recette à fixer.

**Décisions manquantes** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le tricycle utilisé par DiddiSend relève-t-il du profil moto ou d'un profil propre ? | Portée MVP | UC-148 | Produit | `diddimap-cartographie` |
| que voit le passager quand le temps d'arrivée estimé n'est pas disponible ? | Portée MVP | UC-147 | Produit | `diddimap-cartographie` |
| quels critères définissent une position aberrante — vitesse, précision, saut de distance ? | Portée MVP | UC-149 | Technique | `diddimap-cartographie` |
| quelle est la zone de couverture exacte au lancement ? | Portée V1 | UC-150 | Produit | `diddimap-cartographie` |

**Faits à établir** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| DiddiGo transmet l'identifiant de trace sous forme de chaîne, DiddiMap l'attend sous forme d'entier ; cette conversion est-elle sûre ? | Portée MVP | — | Technique | `diddimap-cartographie` |
| le format des traces correspond dans le code ; un test de bout en bout en staging reste à faire | Portée MVP | — | Technique | `diddimap-cartographie` |
| le format des traces DiddiGo correspond au schéma DiddiMap dans le code, mais l'écart signalé le 31/08 n'a pas été confirmé résolu par un test de bout en bout en staging | Portée MVP | — | — | `diddimap-cartographie` |

**Contradictions entre deux sources** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case décrit un temps d'arrivée estimé qui se met à jour pendant la course ; aucun recalcul n'existe | Portée MVP | — | Technique | `diddimap-cartographie` |
| DiddiMap valide un profil de véhicule à l'entrée du calcul d'itinéraire mais construit toujours l'appel au moteur avec le profil configuré globalement ; un itinéraire moto est en réalité un itinéraire voiture | Portée MVP | — | — | `diddimap-cartographie` |
| DiddiMap valide un profil de véhicule puis construit toujours l'appel avec le profil configuré globalement | Portée MVP | — | Technique | `diddimap-cartographie` |

---

### PAR-006 — Conserver des échantillons vocaux (option)

**Limite déclarée par le planning.** Durée, suppression, hébergement, sous-traitants, sort des anciens échantillons à arbitrer.

Aucune entrée ouverte rattachée à ce parcours par les registres.

### PAR-007 — Recevoir une offre et suivre une mission

**Limite déclarée par le planning.** Numéro masqué ou appel direct : à choisir.

**Décisions manquantes** — 12

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| que fait le système quand aucun appareil n'est enregistré pour un pro à qui une offre est destinée ? | Portée MVP | UC-156 | Produit | `notifications-et-canaux` |
| quel canal est prioritaire pour un code destinataire — SMS ou WhatsApp — et lequel sert de secours ? | Portée MVP | UC-159 | Produit | `notifications-et-canaux` |
| combien de fois un message non délivré est-il retenté, et à quel rythme ? | Portée V1 | UC-160 | Technique | `notifications-et-canaux` |
| combien de temps après la fin de la mission le canal reste-t-il ouvert avant fermeture ? | Portée V1 | UC-154 | Produit | `communication-en-mission` |
| des messages prédéfinis sont-ils proposés, et lesquels ? | Portée V1 | UC-151 | Produit | `communication-en-mission` |
| le chat autorise-t-il l'envoi de photos, ou du texte seulement ? | Portée V1 | UC-151, UC-152 | Produit | `communication-en-mission` |
| pendant combien de temps les échanges sont-ils conservés, et qui peut les lire ? | Portée V1 | UC-155 | Juridique | `communication-en-mission` |
| que se passe-t-il si une partie ne répond pas ? | Portée V1 | UC-151, UC-152 | Produit | `communication-en-mission` |
| quel fournisseur assure le masquage de numéro, et à quel coût par appel ? | Portée V1 | UC-153 | Administration | `communication-en-mission` |
| quelle est la durée de conservation du journal des envois ? | Portée V1 | UC-162 | Juridique | `notifications-et-canaux` |
| quelles notifications l'utilisateur peut-il désactiver, et lesquelles sont obligatoires ? | Portée V1 | UC-161 | Produit | `notifications-et-canaux` |
| un administrateur peut-il lire un échange sans motif, ou seulement sur un litige ouvert ? | Portée V1 | UC-155 | Juridique | `communication-en-mission` |

**Faits à établir** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| est-il prévu de mutualiser l'envoi de notifications entre services, ou chaque service reste-t-il autonome ? | Portée MVP | — | Technique | `notifications-et-canaux` |
| un appareil iPhone est-il enregistré avec un jeton FCM valide, ou l'application iOS n'enregistre-t-elle rien du tout ? | Portée MVP | — | Technique | `notifications-et-canaux` |
| le canal temps réel existant peut-il porter des messages de conversation, ou faut-il un mécanisme distinct pour garantir la livraison et l'ordre ? | Portée V1 | — | Technique | `communication-en-mission` |
| le numéro du chauffeur est-il transmis au passager à tous les états de la course, ou seulement à partir du match ? | Portée V1 | — | Technique | `communication-en-mission` |

**Contradictions entre deux sources** — 2

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est marqué priorité absolue depuis le 31/08 ; ni la charge envoyée par le serveur ni l'écran d'offre ne portent aujourd'hui de son ou de vibration | Portée MVP | — | Technique | `notifications-et-canaux` |
| la décision du 01/09 prévoit de discuter et de s'appeler sans échanger de numéro ; le numéro du chauffeur est aujourd'hui transmis au passager dans la fiche de course | Portée V1 | — | Produit | `communication-en-mission` |

---

### PAR-008 — Garder un historique exploitable

**Décisions manquantes** — 10

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| au bout de combien de temps sans position un véhicule est-il considéré comme silencieux, et l'alerte part-elle vers qui ? — réponse partielle du 14/09, voir decisions-actees.md : seuil retenu : 5 minutes. Destination de l'alerte : proposition Claude dans decisions-actees.md, en attente de validation | Portée MVP | UC-324 | Produit | `reseau-degrade-et-continuite` |
| que fait le système d'une action rejouée dont l'horodatage est hors tolérance — rejet, correction, acceptation signalée ? | Portée MVP | UC-321 | Produit | `reseau-degrade-et-continuite` |
| quel écart maximal est toléré entre l'horloge du téléphone et celle du serveur ? | Portée MVP | UC-321 | Technique | `reseau-degrade-et-continuite` |
| au bout de combien de temps l'identité du chauffeur est-elle masquée dans l'historique — à la fin de la course, ou après un délai ? | Portée V1 | UC-247 | Juridique | `historique-recus-et-justificatifs` |
| pendant combien de temps un utilisateur conserve-t-il l'accès à son historique ? | Portée V1 | — | Juridique | `historique-recus-et-justificatifs` |
| que contient exactement un reçu de course et un reçu de livraison ? | Portée V1 | UC-249 | Produit | `historique-recus-et-justificatifs` |
| que contient exactement un relevé de gains de pro ? | Portée V1 | UC-250, UC-251 | Produit | `historique-recus-et-justificatifs` |
| que contient exactement un relevé de gains de pro, et dans quel format est-il exporté ? | Portée V1 | — | Produit | `historique-recus-et-justificatifs` |
| quel contenu et quelle forme pour la facture mensuelle consolidée ? | Portée V1 | — | Produit | `historique-recus-et-justificatifs` |
| un reçu doit-il porter une mention de TVA distincte, et sous quelle forme ? | Portée V1 | UC-249 | Juridique | `historique-recus-et-justificatifs` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| l'événement de position diffusé par le canal temps réel de DiddiGo porte-t-il l'horodatage de la mesure, ou seulement celui de la diffusion ? | Portée MVP | — | Technique | `reseau-degrade-et-continuite` |

**Contradictions entre deux sources** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case exige de borner l'horloge du téléphone ; les horodatages envoyés par l'application sont acceptés sans aucun contrôle | Portée MVP | — | Technique | `reseau-degrade-et-continuite` |
| ce use case est classé partiel ; la liste paginée et filtrée existe | Portée V1 | — | Technique | `historique-recus-et-justificatifs` |
| ce use case est classé partiel ; le détail complet existe et est exposé | Portée V1 | — | Technique | `historique-recus-et-justificatifs` |
| ce use case est classé partiel sur l'axe back ; la liste paginée, filtrable par rôle, état, date de début et de fin existe et est exposée | Portée V1 | — | — | `historique-recus-et-justificatifs` |
| ce use case est classé partiel sur l'axe back ; le détail complet — décomposition, distance et durée réelles, mode de paiement, quatre horodatages du cycle — existe et est exposé | Portée V1 | — | — | `historique-recus-et-justificatifs` |
| UC-245 et UC-246 sont classés partiels sur l'axe back ; la liste paginée et filtrée et le détail complet d'une course existent et sont exposés | Portée V1 | — | Technique | `historique-recus-et-justificatifs` |
| UC-247 demande de masquer l'identité du chauffeur et l'immatriculation dans l'historique après la course ; la fiche complète du chauffeur reste accessible sans limite de temps | Portée V1 | — | Produit | `historique-recus-et-justificatifs` |

---

## DiddiGo — la course

### PAR-016 — Commander et effectuer une course

**Décisions manquantes** — 96

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel est le barème de points de priorité, sa fenêtre de calcul et le score de départ d'un nouveau pro ? | Entrées structurantes | UC-108, UC-109, UC-283, UC-285 | Produit | `matching-et-priorite` |
| quel est le délai d'acceptation d'une offre ? | Entrées structurantes | UC-278, UC-279, UC-282 | Produit | `matching-et-priorite` |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | Entrées structurantes | — | Produit | `diddigo-chauffeur` |
| quel plafond limite l'effet de la priorité par rapport à la proximité ? — réponse partielle du 14/09, voir decisions-actees.md : réponse reçue porte sur un seuil de suspension de compte à 50 pts, pas sur le plafond de classement demandé ici ; proposition Claude disponible dans decisions-actees.md | Entrées structurantes | UC-284 | Produit | `matching-et-priorite` |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | Entrées structurantes | UC-274 | Produit | `diddigo-chauffeur` |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | Portée MVP | UC-259 | Produit | `diddigo-passager` |
| à partir de quel âge la position affichée est-elle présentée comme ancienne ? | Portée MVP | — | Produit | `suivi-public-hors-application` |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| au bout de combien de temps sans position un véhicule est-il considéré comme silencieux, et l'alerte part-elle vers qui ? — réponse partielle du 14/09, voir decisions-actees.md : seuil retenu : 5 minutes. Destination de l'alerte : proposition Claude dans decisions-actees.md, en attente de validation | Portée MVP | UC-324 | Produit | `reseau-degrade-et-continuite` |
| combien de temps la demande « prévenez-moi » reste-t-elle active ? — réponse partielle du 14/09, voir decisions-actees.md : question non comprise par l'équipe lors de la relecture ; clarification apportée dans decisions-actees.md, reste ouverte | Portée MVP | — | Produit | `diddigo-passager` |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| deux règles de priorité temporaire qui se chevauchent se cumulent-elles, ou la plus favorable l'emporte-t-elle seule ? | Portée MVP | — | Produit | `matching-et-priorite` |
| existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'ancienneté d'une position est-elle présentée en heure absolue ou en durée écoulée ? — proposition Claude en attente de validation : durée écoulée sous 10 min, heure absolue au-delà. Voir decisions-actees.md | Portée MVP | — | Produit | `diddigo-passager` |
| la hausse de priorité liée à une zone s'applique-t-elle uniquement pendant que le pro y est physiquement présent ? | Portée MVP | — | Produit | `matching-et-priorite` |
| la relance sur expiration silencieuse doit-elle être une tâche planifiée périodique, ou une notification Redis (keyspace notification) déclenchée à l'expiration de la clé ? | Portée MVP | — | Technique | `matching-et-priorite` |
| la réputation et les points de priorité (voir UC-274) sont-ils attachés au chauffeur ou au véhicule dans ce cas de partage ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le budget de deux minutes court-il à partir de la création de la course ou de la première vague ? — proposition Claude en attente de validation : à partir de la création de la course. Voir decisions-actees.md | Portée MVP | — | — | `diddigo-passager` |
| le contrôle croisé DiddiGo/DiddiSend doit-il être activé et complété avant le lancement, ou le risque de double affectation entre les deux services est-il jugé négligeable en phase 1 ? | Portée MVP | — | Produit | `matching-et-priorite` |
| le paiement d'une course peut-il être réglé depuis le wallet utilisateur de DiddiPay ? | Portée MVP | — | Produit | `diddigo-passager` |
| le passage d'une aide à la décision administrative à un dispatch automatique de coursiers est-il prévu au même horizon que celui de DiddiGo, ou DiddiSend reste-t-il assisté plus longtemps ? | Portée MVP | — | Produit | `matching-et-priorite` |
| le passager doit-il être informé différemment selon que personne n'était présent ou que tous ont refusé ? | Portée MVP | — | Produit | `diddigo-passager` |
| le plafond est-il exprimé en écart de temps absolu, en pourcentage du temps d'arrivée, ou en rang maximal de dépassement ? | Portée MVP | — | Produit | `matching-et-priorite` |
| le prix d'une course programmée est-il garanti à la réservation, ou recalculé au déclenchement ? | Portée MVP | — | Produit | `diddigo-passager` |
| le serveur expose-t-il l'instant de la dernière position reçue du chauffeur, ou diffuse-t-il un événement de silence ? | Portée MVP | — | Technique | `diddigo-passager` |
| le tricycle utilisé par DiddiSend relève-t-il du profil moto ou d'un profil propre ? | Portée MVP | UC-148 | Produit | `diddimap-cartographie` |
| le verrou d'une seule course active par passager s'applique-t-il aux courses programmées ? | Portée MVP | — | Produit | `diddigo-passager` |
| le voyageur doit-il avoir un compte, ou un nom et un téléphone suffisent-ils ? | Portée MVP | — | Produit | `diddigo-passager` |
| les adresses enregistrées sont-elles visibles par un administrateur, et cette consultation est-elle journalisée ? | Portée MVP | UC-201 | Juridique | `diddigo-passager` |
| pendant combien de temps après la course une note reste-t-elle possible ? | Portée MVP | — | Produit | `diddigo-passager` |
| qu'est-ce qui définit le silence d'un chauffeur — absence de position, absence de progression vers le point de prise en charge, ou les deux ? | Portée MVP | — | Produit | `diddigo-passager` |
| qu'est-ce qui distingue les trois niveaux pour le passager, au-delà du prix ? | Portée MVP | — | Produit | `diddigo-passager` |
| que devient un frais d'annulation dont le prélèvement échoue ? | Portée MVP | — | Administration | `diddigo-passager` |
| que fait le système d'une action rejouée dont l'horodatage est hors tolérance — rejet, correction, acceptation signalée ? | Portée MVP | UC-321 | Produit | `reseau-degrade-et-continuite` |
| que fait le système quand un pro accepte alors que la vague suivante est déjà partie ? | Portée MVP | UC-278, UC-281 | Produit | `matching-et-priorite` |
| que se passe-t-il quand un passager annonce un paiement en espèces et n'a pas la somme ? | Portée MVP | — | Administration | `diddigo-passager` |
| que se passe-t-il si aucun chauffeur n'accepte une course programmée ? | Portée MVP | — | Produit | `diddigo-passager` |
| que voit le passager quand le temps d'arrivée estimé n'est pas disponible ? | Portée MVP | UC-147 | Produit | `diddimap-cartographie` |
| quel critère départage deux candidats strictement à égalité de classement ? | Portée MVP | — | Technique | `matching-et-priorite` |
| quel écart de prix sépare les trois niveaux de confort, et cet écart est-il un multiplicateur ou une grille par niveau ? | Portée MVP | — | Produit | `diddigo-passager` |
| quel écart maximal est toléré entre l'horloge du téléphone et celle du serveur ? | Portée MVP | UC-321 | Technique | `reseau-degrade-et-continuite` |
| quel est le barème de pénalité pour un refus d'offre, et comment la pénalité doublée sous 1 km s'applique-t-elle ? | Portée MVP | UC-027 | Produit | `diddigo-chauffeur` |
| quel est le barème de pénalité pour une annulation par le pro après acceptation ? | Portée MVP | UC-027, UC-273 | Produit | `diddigo-chauffeur` |
| quel est le mode de paiement par défaut d'une course ? | Portée MVP | — | Produit | `diddigo-passager` |
| quel message est affiché à un chauffeur non retenu d'une vague, pour éviter qu'il ne pense avoir refusé ou raté quelque chose ? | Portée MVP | — | Produit | `matching-et-priorite` |
| quel plafond de temps d'attente est facturable sur une même course, et porte-t-il sur une période ou sur le cumul ? | Portée MVP | UC-258 | Produit | `diddigo-passager` |
| quelle densité de chauffeurs libres dans le rayon minimal est réellement nécessaire pour une expérience passager acceptable ? | Portée MVP | — | Produit | `matching-et-priorite` |
| quelle est la conséquence d'annulations répétées par un même passager ? | Portée MVP | — | Produit | `diddigo-passager` |
| quelle est la fenêtre de calcul des points — glissante, et sur quelle durée ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| quelle preuve, le cas échéant, le chauffeur doit-il produire pour une annulation pour absence ? | Portée MVP | — | Juridique | `diddigo-chauffeur` |
| quelles informations la page publique affiche-t-elle — nom du chauffeur, immatriculation, numéro de téléphone ? — réponse partielle du 14/09, voir decisions-actees.md : prénom du chauffeur (pas le nom), immatriculation, modèle et couleur du véhicule, résolus. Numéro de téléphone : proposition Claude dans decisions-actees.md | Portée MVP | UC-163 | Juridique | `diddigo-passager` |
| quelles informations la page publique affiche-t-elle — nom du chauffeur, plaque, numéro de téléphone ? — réponse partielle du 14/09, voir decisions-actees.md : prénom du chauffeur (pas le nom), immatriculation, modèle et couleur du véhicule, résolus. Numéro de téléphone : proposition Claude dans decisions-actees.md | Portée MVP | UC-163, UC-164 | Juridique | `suivi-public-hors-application` |
| quelles informations la page publique affiche-t-elle ? — réponse partielle du 14/09, numéro de téléphone en attente de validation | Portée MVP | — | Juridique | `suivi-public-hors-application` |
| quelles photos de véhicule sont obligatoires et lesquelles sont facultatives ? | Portée MVP | UC-270 | Produit | `diddigo-chauffeur` |
| quelles sont les valeurs successives du rayon de recherche, et combien de vagues au maximum ? | Portée MVP | UC-280 | Produit | `matching-et-priorite` |
| quels critères définissent une position aberrante — vitesse, précision, saut de distance ? | Portée MVP | UC-149 | Technique | `diddimap-cartographie` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie — tirage aléatoire à quelle fréquence, quel type de signalement, quelle définition d'un changement d'appareil ? | Portée MVP | — | — | `diddigo-chauffeur` |
| quels frais s'appliquent à une annulation par le passager, et à partir de quel moment du cycle de la course ? | Portée MVP | UC-013 | Produit | `diddigo-passager` |
| quels motifs d'annulation sont proposés au passager, et lesquels exonèrent de frais ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui décide qu'une zone doit être ciblée pour un renforcement de priorité, et selon quel critère ? | Portée MVP | — | Produit | `matching-et-priorite` |
| qui note le chauffeur, le commanditaire ou le voyageur ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui peut annuler la course une fois le voyageur à bord ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui peut créer une règle de priorité temporaire, et avec quelle durée maximale ? | Portée MVP | — | Produit | `matching-et-priorite` |
| qui peut déclencher une alerte d'urgence, et qui est prévenu — le contact du commanditaire ou celui du voyageur ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui valide un supplément d'escale ou d'attente — le commanditaire, qui paie, ou le voyageur, qui est dans le véhicule ? | Portée MVP | — | Produit | `diddigo-passager` |
| si DiddiMap ne répond pas pour un candidat, ce candidat est-il classé par distance à vol d'oiseau en repli, ou exclu de ce tour ? | Portée MVP | — | Technique | `matching-et-priorite` |
| si le prix recalculé à la commande diffère du prix estimé, la commande est-elle refusée, ou le nouveau prix est-il présenté au passager avant création ? | Portée MVP | — | Produit | `diddigo-passager` |
| sur quelle référence de temps l'âge d'une position est-il calculé, celle du serveur ou celle du téléphone ? | Portée MVP | UC-321 | Technique | `diddigo-passager` |
| un changement de paramètre de dispatch s'applique-t-il immédiatement aux recherches en cours, ou seulement aux nouvelles courses créées après le changement ? | Portée MVP | — | Technique | `matching-et-priorite` |
| un même lien peut-il être ouvert par plusieurs personnes en même temps, et faut-il le limiter ? | Portée MVP | — | Produit | `suivi-public-hors-application` |
| un préjudice matériel donne-t-il lieu à une indemnisation, et selon quelles règles ? | Portée MVP | — | Direction | `diddigo-chauffeur` |
| un pro inactif au-delà de la fenêtre glissante revient-il au score de départ, ou conserve-t-il son dernier score connu ? | Portée MVP | — | Produit | `matching-et-priorite` |
| un supplément validé reste-t-il dû si la course est annulée avant l'escale ? | Portée MVP | — | Produit | `diddigo-passager` |
| un véhicule peut-il être associé à plusieurs chauffeurs simultanément, ou un seul à la fois avec bascule explicite ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une alerte d'urgence doit-elle changer quelque chose à la course elle-même — interruption, verrouillage du paiement, conservation prolongée de la trace ? | Portée MVP | — | Produit | `diddigo-passager` |
| une alerte peut-elle être déclenchée après la fin de la course, et pendant combien de temps ? | Portée MVP | — | Produit | `diddigo-passager` |
| une annulation pour absence avant le délai est-elle simplement refusée, ou traitée comme une annulation ordinaire avec conséquence ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une annulation pour silence du chauffeur a-t-elle un effet sur sa réputation, même sans pénalité ? | Portée MVP | — | Produit | `diddigo-passager` |
| une course doit-elle être terminée pour être notée, ou une course annulée peut-elle l'être aussi ? | Portée MVP | — | Produit | `diddigo-passager` |
| une course programmée peut-elle être annulée sans frais, et jusqu'à quel moment ? | Portée MVP | — | Produit | `diddigo-passager` |
| une déclaration de préjudice se distingue-t-elle d'un signalement de litige ordinaire (UC support-litiges), et si oui par quel circuit de traitement ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une majoration en vigueur au moment du déclenchement s'applique-t-elle à une course réservée avant ? | Portée MVP | — | Produit | `diddigo-passager` |
| une modification d'itinéraire qui raccourcit le trajet donne-t-elle lieu à une réduction, ou le prix annoncé reste-t-il dû ? | Portée MVP | — | Produit | `diddigo-passager` |
| une règle de priorité temporaire est-elle soumise au même régime gouverné que les seuils financiers (UC-350), ou à un régime plus léger ? | Portée MVP | — | Produit | `matching-et-priorite` |
| une relance crée-t-elle une nouvelle course, ou remet-elle la course existante en recherche ? | Portée MVP | — | Produit | `diddigo-passager` |
| une suggestion d'adresses fréquentes, déduite de l'historique, peut-elle remplacer l'enregistrement explicite en première version ? | Portée MVP | — | Produit | `diddigo-passager` |
| une zone de préférence est-elle un filtre strict (aucune offre hors zone) ou une simple priorité (offres hors zone toujours possibles) ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence peut-elle devenir un moyen détourné de refuser des courses sans pénalité de taux d'acceptation ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une validation orale de supplément engage-t-elle le passager en cas de litige ? | Portée V1 | UC-307 | Juridique | `diddigo-chauffeur` |
| au bout de combien de temps sans position un chauffeur est-il considéré comme silencieux ? — réponse partielle du 14/09, voir decisions-actees.md : seuil retenu : 5 minutes. Destination de l'alerte : proposition Claude dans decisions-actees.md, en attente de validation | Portée V1 | UC-324 | Produit | `diddigo-passager` |
| combien de fois par jour le mode retour maison peut-il être activé ? | Portée V1 | UC-265 | Produit | `diddigo-chauffeur` |
| combien de temps avant l'expiration d'un document le chauffeur est-il alerté, et à quel moment est-il bloqué ? | Portée V1 | UC-275 | Juridique | `diddigo-chauffeur` |
| quel seuil de note déclenche une alerte de qualité sur un pro ? | Portée V1 | UC-217 | — | `diddigo-passager` |
| quelle est la zone de couverture exacte au lancement ? | Portée V1 | UC-150 | Produit | `diddimap-cartographie` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie ? | Portée V1 | UC-268 | Produit | `diddigo-chauffeur` |

**Faits à établir** — 65

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un second appel à la route d'alerte doit-il être refusé explicitement plutôt que d'écraser le premier ? | Portée MVP | — | Technique | `diddigo-passager` |
| à quel moment exact le paiement d'une course est-il capturé ? | Portée MVP | — | Technique | `diddigo-passager` |
| ce cas est-il contrôlé côté serveur ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce contrôle doit-il s'exécuter à l'estimation, à la création, ou aux deux moments ? | Portée MVP | — | Technique | `matching-et-priorite` |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | Portée MVP | — | Technique | `diddigo-chauffeur` |
| ce taux d'annulation est-il le même champ que celui déjà utilisé par le score de réputation (`scoring_service.py`), ou un calcul distinct propre à la priorité ? | Portée MVP | — | Technique | `matching-et-priorite` |
| comportement réel d'une course créée avec une valeur scheduled_at dans le futur | Portée MVP | — | Technique | `diddigo-passager` |
| correspondance entre ces noms d'écran et les écrans réels de l'application client | Portée MVP | — | Technique | `diddigo-passager` |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| deux appels simultanés à la création de course pour le même passager peuvent-ils créer deux courses ? | Portée MVP | — | Technique | `diddigo-passager` |
| deux appels successifs à l'estimation peuvent-ils renvoyer deux prix différents pour le même trajet, si la grille ou la majoration change entre les deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| DiddiGo transmet l'identifiant de trace sous forme de chaîne, DiddiMap l'attend sous forme d'entier ; cette conversion est-elle sûre ? | Portée MVP | — | Technique | `diddimap-cartographie` |
| durée de vie du marqueur de disponibilité constatée dans le code, 300 secondes | Portée MVP | — | — | `matching-et-priorite` |
| existe-t-il ailleurs une tâche de fond qui relance une course restée en requested sans offre ouverte ? | Portée MVP | — | Technique | `matching-et-priorite` |
| l'application du chauffeur remonte-t-elle ses positions par le canal temps réel, par la route de lots, ou par les deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'événement de position diffusé par le canal temps réel de DiddiGo porte-t-il l'horodatage de la mesure, ou seulement celui de la diffusion ? | Portée MVP | — | Technique | `reseau-degrade-et-continuite` |
| l'heure de demande d'une course est-elle enregistrée dans le même référentiel de temps que les autres horodatages du cycle ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'horodatage porté par l'événement de changement d'état est-il celui de la transition ou celui de l'envoi ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'ouverture d'un lien de partage par un tiers est-elle journalisée, et permettrait-elle de savoir combien de fois un lien a été consulté ? | Portée MVP | — | Technique | `diddigo-passager` |
| la déconnexion du canal temps réel d'un chauffeur est-elle exploitable comme signal de silence, ou un chauffeur peut-il rester connecté sans émettre de position ? | Portée MVP | — | Technique | `diddigo-passager` |
| la distinction entre catégorie de véhicule et niveau de confort est-elle intentionnelle, et laquelle des deux le passager choisit-il ? | Portée MVP | — | Technique | `diddigo-passager` |
| la liste des motifs d'annulation est-elle filtrée selon que l'appelant est le passager ou le chauffeur ? | Portée MVP | — | Technique | `diddigo-passager` |
| la longueur du commentaire de notation est-elle bornée ? | Portée MVP | — | Technique | `diddigo-passager` |
| la moyenne du chauffeur est-elle recalculée au moment de la notation, ou lue à la volée depuis les notes ? | Portée MVP | — | Technique | `diddigo-passager` |
| la notation d'une course non terminée est-elle possible aujourd'hui ? | Portée MVP | — | Technique | `diddigo-passager` |
| la route `/api/v1/couriers/{id}/availability` attendue côté DiddiGo par le contrôle croisé DiddiSend existe-t-elle sous un autre nom, ou est-elle à créer ? | Portée MVP | — | Technique | `matching-et-priorite` |
| la route de consultation des candidats est-elle appelée par une application, ou seulement testée manuellement à ce jour ? | Portée MVP | — | Technique | `matching-et-priorite` |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le canal WebSocket peut-il notifier simultanément plusieurs chauffeurs pour la même course sans changement de son modèle d'abonnement actuel ? | Portée MVP | — | Technique | `matching-et-priorite` |
| le chauffeur est-il informé que sa course a été annulée pour silence, et sait-il qu'il n'est pas pénalisé ? | Portée MVP | — | Technique | `diddigo-passager` |
| le chauffeur reçoit-il une notification push à l'annulation d'une course qu'il avait acceptée, ou seulement l'événement temps réel ? | Portée MVP | — | Technique | `diddigo-passager` |
| le code fixe ce délai à 15 s via la constante OFFER_TTL_SECONDS ; la décision de la section 4 est encore à trancher, entre 60 s, 3 min et une recommandation de 20 s | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe le délai de réponse à une offre à 15 s ; la décision est encore à trancher | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le contrôle « véhicule à l'arrêt » s'appuie-t-il sur la dernière position connue, ou faut-il une confirmation explicite du chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le decoupage en zones utilisé par diddimap-cartographie et zones-couverture-et-majoration est-il réutilisable ici, ou faut-il un découpage propre au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le format brut du motif de rejet, avec l'identifiant technique de l'administrateur, est-il celui affiché au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le format des traces correspond dans le code ; un test de bout en bout en staging reste à faire | Portée MVP | — | Technique | `diddimap-cartographie` |
| le format des traces DiddiGo correspond au schéma DiddiMap dans le code, mais l'écart signalé le 31/08 n'a pas été confirmé résolu par un test de bout en bout en staging | Portée MVP | — | — | `diddimap-cartographie` |
| le lien avec l'alerte d'urgence en cours de course (UC-urgence-et-securite-des-personnes) — une déclaration de préjudice grave doit-elle pouvoir déclencher la même chaîne d'alerte ? | Portée MVP | — | Sécurité | `diddigo-chauffeur` |
| le lien de partage de livraison expire-t-il effectivement quand la livraison se termine ? | Portée MVP | — | Technique | `suivi-public-hors-application` |
| le mécanisme gouverné de UC-350 (diddiadmin) est-il conçu pour porter des paramètres techniques comme un rayon en kilomètres, ou seulement des seuils financiers ? | Portée MVP | — | Technique | `matching-et-priorite` |
| le modèle de données actuel associe-t-il un véhicule à un seul chauffeur, ou la relation est-elle déjà multiple ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le passage hors ligne est-il bloqué pendant une course en cours, ou seulement sans effet sur le dispatch pendant ce temps, laissant la course se dérouler normalement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le profil transmis à DiddiMap lors d'une estimation de course correspond-il à un profil que DiddiMap connaît, et est-il utilisé par son moteur d'itinéraire ? | Portée MVP | — | Technique | `diddigo-passager` |
| le rayon de recherche et le nombre maximum de candidats sont des constantes du code DiddiGo, respectivement 5 km et 10 candidats ; la décision du 14/09 impose un rayon élargi vague après vague | Portée MVP | — | Technique | `matching-et-priorite` |
| le score de réputation existant (`GET /v1/me/scores`) est-il le même concept que les « points de priorité » attendus ici, ou deux notions distinctes à ne pas confondre ? | Portée MVP | — | Produit | `matching-et-priorite` |
| le support est-il notifié d'une alerte d'urgence par un canal autre que la lecture des journaux ? | Portée MVP | — | Technique | `diddigo-passager` |
| le support est-il notifié d'une alerte par un canal extérieur à DiddiGo — supervision de journaux, alerte d'infrastructure — ou personne n'est prévenu ? | Portée MVP | — | Technique | `diddigo-passager` |
| le taux d'annulation retenu ici distingue-t-il les annulations à l'initiative du pro de celles à l'initiative du passager ? | Portée MVP | — | Produit | `matching-et-priorite` |
| le verrou d'une seule course active par passager s'applique-t-il au commanditaire, au voyageur, ou aux deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| les origines des deux sous-domaines publics sont-elles autorisées dans la configuration d'origines croisées de DiddiGo et de DiddiSend ? | Portée MVP | — | Technique | `suivi-public-hors-application` |
| peut-on savoir, après coup, si une alerte a été déclenchée par le passager ou par le chauffeur ? | Portée MVP | — | Technique | `diddigo-passager` |
| que fait DiddiGo aujourd'hui d'une course créée avec une date de programmation dans le futur ? | Portée MVP | — | Technique | `diddigo-passager` |
| un chauffeur peut-il diffuser une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-passager` |
| un chauffeur peut-il émettre une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un envoi de trace de bout en bout entre DiddiGo et DiddiMap en staging | Portée MVP | — | Technique | `diddigo-passager` |
| un envoi de trace de bout en bout entre DiddiGo et DiddiMap en staging, pour confirmer que l'écart est résorbé et non déplacé sur l'authentification | Portée MVP | — | — | `diddigo-passager` |
| un même pro peut-il être à la fois chauffeur DiddiGo et coursier DiddiSend, et si oui, ce cas est-il réellement rencontré en pratique ? | Portée MVP | — | Produit | `matching-et-priorite` |
| un module de dispatch/matching est-il prévu côté DiddiAdmin, ou ces règles seront-elles gérées ailleurs (fichier de configuration, autre outil) ? | Portée MVP | — | Technique | `matching-et-priorite` |
| un test de charge du canal WebSocket est-il planifié avant le lancement, avec quel outil ? | Portée MVP | — | Technique | `matching-et-priorite` |
| une estimation produit-elle un événement de journal exploitable pour mesurer le taux d'abandon entre estimation et commande ? | Portée MVP | — | Technique | `diddigo-passager` |

**Contradictions entre deux sources** — 22

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la décision du 31/08 prévoit que le contact d'urgence est prévenu par SMS ou WhatsApp avec un lien ; l'alerte n'envoie aujourd'hui aucun message à personne | Portée MVP | — | — | `diddigo-passager` |
| la décision du 31/08 prévoit une notification du contact d'urgence ; l'alerte n'envoie aucun message | Portée MVP | — | Produit | `diddigo-passager` |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | Portée MVP | — | Produit | `diddigo-passager` |
| ce use case décrit un temps d'arrivée estimé qui se met à jour pendant la course ; aucun recalcul n'existe | Portée MVP | — | Technique | `diddimap-cartographie` |
| ce use case exige de borner l'horloge du téléphone ; les horodatages envoyés par l'application sont acceptés sans aucun contrôle | Portée MVP | — | Technique | `reseau-degrade-et-continuite` |
| DiddiMap valide un profil de véhicule à l'entrée du calcul d'itinéraire mais construit toujours l'appel au moteur avec le profil configuré globalement ; un itinéraire moto est en réalité un itinéraire voiture | Portée MVP | — | — | `diddimap-cartographie` |
| DiddiMap valide un profil de véhicule puis construit toujours l'appel avec le profil configuré globalement | Portée MVP | — | Technique | `diddimap-cartographie` |
| l'instant de mesure de la position est exposé au tiers qui ouvre un lien de partage public, mais pas au passager dans son application | Portée MVP | — | Technique | `diddigo-passager` |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code applique un taux de commission de 8 %, la décision du 14/09 fixe 10 % | Portée MVP | — | Produit | `diddigo-passager` |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe la durée de vie du lien de partage à 24 h via la constante _SHARE_TTL_HOURS, la décision du 31/08 dit 20 minutes après la fin de la course | Portée MVP | — | Produit | `diddigo-passager` |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le document de référence reporte le comparateur de prix entre niveaux de confort en V2 et le liste hors périmètre ; le classeur classe UC-017 en V1 | Portée MVP | — | Produit | `diddigo-passager` |
| le lien de partage de course expire 24 h après sa création dans le code ; la décision du 31/08 dit 20 minutes après la fin de la course | Portée MVP | — | Produit | `suivi-public-hors-application` |
| le mode de paiement « wave » laisse attendre un paiement par l'application Wave ; il ouvre en réalité un formulaire Paystack, comme le mode « diddipay » | Portée MVP | — | Produit | `diddigo-passager` |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le moteur DiddiGo envoie l'offre à un seul chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | Portée MVP | — | Produit | `matching-et-priorite` |
| le motif « chauffeur indisponible » fait basculer la course en annulation par le chauffeur même lorsque l'appelant est le passager ; l'auteur de l'annulation devrait être déterminé par l'identité de l'appelant, pas par le motif qu'il choisit | Portée MVP | — | Technique | `diddigo-passager` |
| le seul motif d'annulation proche du silence du chauffeur est « chauffeur indisponible », qui impute l'annulation au chauffeur ; UC-257 demande explicitement que le chauffeur ne soit pas mis en cause | Portée MVP | — | Technique | `diddigo-passager` |
| UC-253 est classé « à créer » sur l'axe back ; l'état « aucun chauffeur trouvé », sa transition, son journal et son événement temps réel existent et fonctionnent. Le statut juste serait « partiel » | Portée MVP | — | Technique | `diddigo-passager` |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | Portée MVP | — | Produit | `diddigo-chauffeur` |

---

### PAR-017 — Gérer attente, escales et annulation

**Limite déclarée par le planning.** Temps gratuit, tarifs, accord du client à formaliser.

**Décisions manquantes** — 78

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | Entrées structurantes | — | Produit | `diddigo-chauffeur` |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | Entrées structurantes | UC-274 | Produit | `diddigo-chauffeur` |
| quel est le tarif du mode attente ? | Entrées structurantes | — | Produit | `prix-commissions-et-penalites` |
| quelle est la grille tarifaire de lancement, par ville et par profil ? | Entrées structurantes | — | Produit | `prix-commissions-et-penalites` |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | Portée MVP | UC-259 | Produit | `diddigo-passager` |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| combien de temps la demande « prévenez-moi » reste-t-elle active ? — réponse partielle du 14/09, voir decisions-actees.md : question non comprise par l'équipe lors de la relecture ; clarification apportée dans decisions-actees.md, reste ouverte | Portée MVP | — | Produit | `diddigo-passager` |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'ancienneté d'une position est-elle présentée en heure absolue ou en durée écoulée ? — proposition Claude en attente de validation : durée écoulée sous 10 min, heure absolue au-delà. Voir decisions-actees.md | Portée MVP | — | Produit | `diddigo-passager` |
| la réputation et les points de priorité (voir UC-274) sont-ils attachés au chauffeur ou au véhicule dans ce cas de partage ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le budget de deux minutes court-il à partir de la création de la course ou de la première vague ? — proposition Claude en attente de validation : à partir de la création de la course. Voir decisions-actees.md | Portée MVP | — | — | `diddigo-passager` |
| le paiement d'une course peut-il être réglé depuis le wallet utilisateur de DiddiPay ? | Portée MVP | — | Produit | `diddigo-passager` |
| le passager doit-il être informé différemment selon que personne n'était présent ou que tous ont refusé ? | Portée MVP | — | Produit | `diddigo-passager` |
| le prix d'une course programmée est-il garanti à la réservation, ou recalculé au déclenchement ? | Portée MVP | — | Produit | `diddigo-passager` |
| le serveur expose-t-il l'instant de la dernière position reçue du chauffeur, ou diffuse-t-il un événement de silence ? | Portée MVP | — | Technique | `diddigo-passager` |
| le verrou d'une seule course active par passager s'applique-t-il aux courses programmées ? | Portée MVP | — | Produit | `diddigo-passager` |
| le voyageur doit-il avoir un compte, ou un nom et un téléphone suffisent-ils ? | Portée MVP | — | Produit | `diddigo-passager` |
| les adresses enregistrées sont-elles visibles par un administrateur, et cette consultation est-elle journalisée ? | Portée MVP | UC-201 | Juridique | `diddigo-passager` |
| pendant combien de temps après la course une note reste-t-elle possible ? | Portée MVP | — | Produit | `diddigo-passager` |
| qu'est-ce qui définit le silence d'un chauffeur — absence de position, absence de progression vers le point de prise en charge, ou les deux ? | Portée MVP | — | Produit | `diddigo-passager` |
| qu'est-ce qui distingue les trois niveaux pour le passager, au-delà du prix ? | Portée MVP | — | Produit | `diddigo-passager` |
| que devient un frais d'annulation dont le prélèvement échoue ? | Portée MVP | — | Administration | `diddigo-passager` |
| que se passe-t-il quand un passager annonce un paiement en espèces et n'a pas la somme ? | Portée MVP | — | Administration | `diddigo-passager` |
| que se passe-t-il si aucun chauffeur n'accepte une course programmée ? | Portée MVP | — | Produit | `diddigo-passager` |
| quel écart de prix sépare les trois niveaux de confort, et cet écart est-il un multiplicateur ou une grille par niveau ? | Portée MVP | — | Produit | `diddigo-passager` |
| quel est le barème de pénalité pour un refus d'offre, et comment la pénalité doublée sous 1 km s'applique-t-elle ? | Portée MVP | UC-027 | Produit | `diddigo-chauffeur` |
| quel est le barème de pénalité pour une annulation par le pro après acceptation ? | Portée MVP | UC-027, UC-273 | Produit | `diddigo-chauffeur` |
| quel est le mode de paiement par défaut d'une course ? | Portée MVP | — | Produit | `diddigo-passager` |
| quel plafond de temps d'attente est facturable sur une même course, et porte-t-il sur une période ou sur le cumul ? | Portée MVP | UC-258 | Produit | `diddigo-passager` |
| quelle est la conséquence d'annulations répétées par un même passager ? | Portée MVP | — | Produit | `diddigo-passager` |
| quelle est la fenêtre de calcul des points — glissante, et sur quelle durée ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| quelle preuve, le cas échéant, le chauffeur doit-il produire pour une annulation pour absence ? | Portée MVP | — | Juridique | `diddigo-chauffeur` |
| quelles informations la page publique affiche-t-elle — nom du chauffeur, immatriculation, numéro de téléphone ? — réponse partielle du 14/09, voir decisions-actees.md : prénom du chauffeur (pas le nom), immatriculation, modèle et couleur du véhicule, résolus. Numéro de téléphone : proposition Claude dans decisions-actees.md | Portée MVP | UC-163 | Juridique | `diddigo-passager` |
| quelles photos de véhicule sont obligatoires et lesquelles sont facultatives ? | Portée MVP | UC-270 | Produit | `diddigo-chauffeur` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie — tirage aléatoire à quelle fréquence, quel type de signalement, quelle définition d'un changement d'appareil ? | Portée MVP | — | — | `diddigo-chauffeur` |
| quels frais s'appliquent à une annulation par le passager, et à partir de quel moment du cycle de la course ? | Portée MVP | UC-013 | Produit | `diddigo-passager` |
| quels motifs d'annulation sont proposés au passager, et lesquels exonèrent de frais ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui note le chauffeur, le commanditaire ou le voyageur ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui peut annuler la course une fois le voyageur à bord ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui peut déclencher une alerte d'urgence, et qui est prévenu — le contact du commanditaire ou celui du voyageur ? | Portée MVP | — | Produit | `diddigo-passager` |
| qui valide un supplément d'escale ou d'attente — le commanditaire, qui paie, ou le voyageur, qui est dans le véhicule ? | Portée MVP | — | Produit | `diddigo-passager` |
| si le prix recalculé à la commande diffère du prix estimé, la commande est-elle refusée, ou le nouveau prix est-il présenté au passager avant création ? | Portée MVP | — | Produit | `diddigo-passager` |
| sur quelle référence de temps l'âge d'une position est-il calculé, celle du serveur ou celle du téléphone ? | Portée MVP | UC-321 | Technique | `diddigo-passager` |
| un préjudice matériel donne-t-il lieu à une indemnisation, et selon quelles règles ? | Portée MVP | — | Direction | `diddigo-chauffeur` |
| un supplément validé reste-t-il dû si la course est annulée avant l'escale ? | Portée MVP | — | Produit | `diddigo-passager` |
| un véhicule peut-il être associé à plusieurs chauffeurs simultanément, ou un seul à la fois avec bascule explicite ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une alerte d'urgence doit-elle changer quelque chose à la course elle-même — interruption, verrouillage du paiement, conservation prolongée de la trace ? | Portée MVP | — | Produit | `diddigo-passager` |
| une alerte peut-elle être déclenchée après la fin de la course, et pendant combien de temps ? | Portée MVP | — | Produit | `diddigo-passager` |
| une annulation pour absence avant le délai est-elle simplement refusée, ou traitée comme une annulation ordinaire avec conséquence ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une annulation pour silence du chauffeur a-t-elle un effet sur sa réputation, même sans pénalité ? | Portée MVP | — | Produit | `diddigo-passager` |
| une course doit-elle être terminée pour être notée, ou une course annulée peut-elle l'être aussi ? | Portée MVP | — | Produit | `diddigo-passager` |
| une course programmée peut-elle être annulée sans frais, et jusqu'à quel moment ? | Portée MVP | — | Produit | `diddigo-passager` |
| une déclaration de préjudice se distingue-t-elle d'un signalement de litige ordinaire (UC support-litiges), et si oui par quel circuit de traitement ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une majoration en vigueur au moment du déclenchement s'applique-t-elle à une course réservée avant ? | Portée MVP | — | Produit | `diddigo-passager` |
| une modification d'itinéraire qui raccourcit le trajet donne-t-elle lieu à une réduction, ou le prix annoncé reste-t-il dû ? | Portée MVP | — | Produit | `diddigo-passager` |
| une relance crée-t-elle une nouvelle course, ou remet-elle la course existante en recherche ? | Portée MVP | — | Produit | `diddigo-passager` |
| une suggestion d'adresses fréquentes, déduite de l'historique, peut-elle remplacer l'enregistrement explicite en première version ? | Portée MVP | — | Produit | `diddigo-passager` |
| une zone de préférence est-elle un filtre strict (aucune offre hors zone) ou une simple priorité (offres hors zone toujours possibles) ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence peut-elle devenir un moyen détourné de refuser des courses sans pénalité de taux d'acceptation ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une validation orale de supplément engage-t-elle le passager en cas de litige ? | Portée V1 | UC-307 | Juridique | `prix-commissions-et-penalites` |
| au bout de combien de temps sans position un chauffeur est-il considéré comme silencieux ? — réponse partielle du 14/09, voir decisions-actees.md : seuil retenu : 5 minutes. Destination de l'alerte : proposition Claude dans decisions-actees.md, en attente de validation | Portée V1 | UC-324 | Produit | `diddigo-passager` |
| combien de fois par jour le mode retour maison peut-il être activé ? | Portée V1 | UC-265 | Produit | `diddigo-chauffeur` |
| combien de temps avant l'expiration d'un document le chauffeur est-il alerté, et à quel moment est-il bloqué ? | Portée V1 | UC-275 | Juridique | `diddigo-chauffeur` |
| le seuil de durée de 3 min recommandé pour le supplément d'escale est-il retenu ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| quel est le barème des pénalités d'annulation, par persona et par moment ? | Portée V1 | UC-184, UC-308 | Produit | `prix-commissions-et-penalites` |
| quel est le pas de monnaie disponible, et l'arrondi se fait-il au bénéfice du client ou du chauffeur ? | Portée V1 | UC-306 | Produit | `prix-commissions-et-penalites` |
| quel est le plafond de temps d'attente facturable sur une même course ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| quel plafond limite la majoration, et comment est-il rendu public au passager ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| quel seuil de note déclenche une alerte de qualité sur un pro ? | Portée V1 | UC-217 | — | `diddigo-passager` |
| quelle est l'assiette des frais de tentative sur une livraison échouée ? | Portée V1 | UC-185 | Produit | `prix-commissions-et-penalites` |
| quelle part de la majoration est versée au pro — recommandé 100 %, non tranché ? | Portée V1 | — | Administration | `prix-commissions-et-penalites` |
| quelles qualifications un agent peut-il donner à une alerte ? | Portée V1 | UC-172 | Produit | `urgence-et-securite-des-personnes` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie ? | Portée V1 | UC-268 | Produit | `diddigo-chauffeur` |
| qui est joignable, et à quelles heures, pour prendre en charge une alerte ? | Portée V1 | UC-172 | Administration | `urgence-et-securite-des-personnes` |
| une alerte déclenchée hors course est-elle possible ? | Portée V1 | — | Produit | `urgence-et-securite-des-personnes` |
| au bout de combien de temps une alerte non prise en charge est-elle escaladée, et vers qui ? | Portée Later | UC-174 | Administration | `urgence-et-securite-des-personnes` |

**Faits à établir** — 46

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un second appel à la route d'alerte doit-il être refusé explicitement plutôt que d'écraser le premier ? | Portée MVP | — | Technique | `urgence-et-securite-des-personnes` |
| à quel moment exact le paiement d'une course est-il capturé ? | Portée MVP | — | Technique | `diddigo-passager` |
| ce cas est-il contrôlé côté serveur ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | Portée MVP | — | Technique | `diddigo-chauffeur` |
| comportement réel d'une course créée avec une valeur scheduled_at dans le futur | Portée MVP | — | Technique | `diddigo-passager` |
| correspondance entre ces noms d'écran et les écrans réels de l'application client | Portée MVP | — | Technique | `diddigo-passager` |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| deux appels simultanés à la création de course pour le même passager peuvent-ils créer deux courses ? | Portée MVP | — | Technique | `diddigo-passager` |
| deux appels successifs à l'estimation peuvent-ils renvoyer deux prix différents pour le même trajet, si la grille ou la majoration change entre les deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'application du chauffeur remonte-t-elle ses positions par le canal temps réel, par la route de lots, ou par les deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'heure de demande d'une course est-elle enregistrée dans le même référentiel de temps que les autres horodatages du cycle ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'horodatage porté par l'événement de changement d'état est-il celui de la transition ou celui de l'envoi ? | Portée MVP | — | Technique | `diddigo-passager` |
| l'ouverture d'un lien de partage par un tiers est-elle journalisée, et permettrait-elle de savoir combien de fois un lien a été consulté ? | Portée MVP | — | Technique | `diddigo-passager` |
| la déconnexion du canal temps réel d'un chauffeur est-elle exploitable comme signal de silence, ou un chauffeur peut-il rester connecté sans émettre de position ? | Portée MVP | — | Technique | `diddigo-passager` |
| la distinction entre catégorie de véhicule et niveau de confort est-elle intentionnelle, et laquelle des deux le passager choisit-il ? | Portée MVP | — | Technique | `diddigo-passager` |
| la liste des motifs d'annulation est-elle filtrée selon que l'appelant est le passager ou le chauffeur ? | Portée MVP | — | Technique | `diddigo-passager` |
| la longueur du commentaire de notation est-elle bornée ? | Portée MVP | — | Technique | `diddigo-passager` |
| la moyenne du chauffeur est-elle recalculée au moment de la notation, ou lue à la volée depuis les notes ? | Portée MVP | — | Technique | `diddigo-passager` |
| la notation d'une course non terminée est-elle possible aujourd'hui ? | Portée MVP | — | Technique | `diddigo-passager` |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le chauffeur est-il informé que sa course a été annulée pour silence, et sait-il qu'il n'est pas pénalisé ? | Portée MVP | — | Technique | `diddigo-passager` |
| le chauffeur reçoit-il une notification push à l'annulation d'une course qu'il avait acceptée, ou seulement l'événement temps réel ? | Portée MVP | — | Technique | `diddigo-passager` |
| le code fixe ce délai à 15 s via la constante OFFER_TTL_SECONDS ; la décision de la section 4 est encore à trancher, entre 60 s, 3 min et une recommandation de 20 s | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe le délai de réponse à une offre à 15 s ; la décision est encore à trancher | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le contrôle « véhicule à l'arrêt » s'appuie-t-il sur la dernière position connue, ou faut-il une confirmation explicite du chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le decoupage en zones utilisé par diddimap-cartographie et zones-couverture-et-majoration est-il réutilisable ici, ou faut-il un découpage propre au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le format brut du motif de rejet, avec l'identifiant technique de l'administrateur, est-il celui affiché au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le lien avec l'alerte d'urgence en cours de course (UC-urgence-et-securite-des-personnes) — une déclaration de préjudice grave doit-elle pouvoir déclencher la même chaîne d'alerte ? | Portée MVP | — | Sécurité | `diddigo-chauffeur` |
| le modèle de données actuel associe-t-il un véhicule à un seul chauffeur, ou la relation est-elle déjà multiple ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le passage hors ligne est-il bloqué pendant une course en cours, ou seulement sans effet sur le dispatch pendant ce temps, laissant la course se dérouler normalement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le profil transmis à DiddiMap lors d'une estimation de course correspond-il à un profil que DiddiMap connaît, et est-il utilisé par son moteur d'itinéraire ? | Portée MVP | — | Technique | `diddigo-passager` |
| le support est-il notifié d'une alerte d'urgence par un canal autre que la lecture des journaux ? | Portée MVP | — | Technique | `diddigo-passager` |
| le support est-il notifié d'une alerte par un canal extérieur à DiddiGo — supervision de journaux, alerte d'infrastructure — ou personne n'est prévenu ? | Portée MVP | — | Technique | `diddigo-passager` |
| le verrou d'une seule course active par passager s'applique-t-il au commanditaire, au voyageur, ou aux deux ? | Portée MVP | — | Technique | `diddigo-passager` |
| peut-on savoir, après coup, si une alerte a été déclenchée par le passager ou par le chauffeur ? | Portée MVP | — | Technique | `diddigo-passager` |
| que fait DiddiGo aujourd'hui d'une course créée avec une date de programmation dans le futur ? | Portée MVP | — | Technique | `diddigo-passager` |
| un chauffeur peut-il diffuser une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-passager` |
| un chauffeur peut-il émettre une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un envoi de trace de bout en bout entre DiddiGo et DiddiMap en staging | Portée MVP | — | Technique | `diddigo-passager` |
| un envoi de trace de bout en bout entre DiddiGo et DiddiMap en staging, pour confirmer que l'écart est résorbé et non déplacé sur l'authentification | Portée MVP | — | — | `diddigo-passager` |
| une estimation produit-elle un événement de journal exploitable pour mesurer le taux d'abandon entre estimation et commande ? | Portée MVP | — | Technique | `diddigo-passager` |
| le support est-il notifié d'une alerte par un canal extérieur à DiddiGo — supervision des journaux, alerte d'infrastructure — ou personne n'est prévenu ? | Portée V1 | — | Technique | `urgence-et-securite-des-personnes` |

**Contradictions entre deux sources** — 19

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la décision du 31/08 prévoit que le contact d'urgence est prévenu par SMS ou WhatsApp avec un lien ; l'alerte n'envoie aujourd'hui aucun message à personne | Portée MVP | — | — | `urgence-et-securite-des-personnes` |
| la décision du 31/08 prévoit une notification du contact d'urgence ; l'alerte n'envoie aucun message | Portée MVP | — | Produit | `urgence-et-securite-des-personnes` |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | Portée MVP | — | Produit | `diddigo-passager` |
| l'instant de mesure de la position est exposé au tiers qui ouvre un lien de partage public, mais pas au passager dans son application | Portée MVP | — | Technique | `diddigo-passager` |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code applique un taux de commission de 8 %, la décision du 14/09 fixe 10 % | Portée MVP | — | Produit | `diddigo-passager` |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe la durée de vie du lien de partage à 24 h via la constante _SHARE_TTL_HOURS, la décision du 31/08 dit 20 minutes après la fin de la course | Portée MVP | — | Produit | `diddigo-passager` |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le document de référence reporte le comparateur de prix entre niveaux de confort en V2 et le liste hors périmètre ; le classeur classe UC-017 en V1 | Portée MVP | — | Produit | `diddigo-passager` |
| le mode de paiement « wave » laisse attendre un paiement par l'application Wave ; il ouvre en réalité un formulaire Paystack, comme le mode « diddipay » | Portée MVP | — | Produit | `diddigo-passager` |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le motif « chauffeur indisponible » fait basculer la course en annulation par le chauffeur même lorsque l'appelant est le passager ; l'auteur de l'annulation devrait être déterminé par l'identité de l'appelant, pas par le motif qu'il choisit | Portée MVP | — | Technique | `diddigo-passager` |
| le seul motif d'annulation proche du silence du chauffeur est « chauffeur indisponible », qui impute l'annulation au chauffeur ; UC-257 demande explicitement que le chauffeur ne soit pas mis en cause | Portée MVP | — | Technique | `diddigo-passager` |
| UC-171 est classé partiel sur l'axe back ; la route d'alerte accepte déjà le chauffeur assigné au même titre que le passager | Portée MVP | UC-169 | Technique | `urgence-et-securite-des-personnes` |
| UC-253 est classé « à créer » sur l'axe back ; l'état « aucun chauffeur trouvé », sa transition, son journal et son événement temps réel existent et fonctionnent. Le statut juste serait « partiel » | Portée MVP | — | Technique | `diddigo-passager` |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | Portée MVP | — | Produit | `diddigo-chauffeur` |
| ce use case est classé à créer sur l'axe back et noté prévu en V2 dans le cahier des charges DiddiGo ; le calcul du prix réel à partir des traces existe et fonctionne, avec conservation de l'écart | Portée V1 | — | Technique | `prix-commissions-et-penalites` |
| le taux de commission appliqué par DiddiGo dans le code est de 8 %, la décision du 14/09 fixe 10 % | Portée V1 | UC-187, UC-350 | Produit | `prix-commissions-et-penalites` |

---

### PAR-018 — Payer et retrouver ses gains

**Limite déclarée par le planning.** Assiette et arrondis de la commission à finaliser.

**Décisions manquantes** — 61

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel est le délai d'acceptation d'une offre de course DiddiGo ? | Entrées structurantes | — | Produit | `diddigo-chauffeur` |
| quel est le barème de points de priorité et sa fenêtre de calcul ? | Entrées structurantes | UC-274 | Produit | `diddigo-chauffeur` |
| quel est le tarif du mode attente ? | Entrées structurantes | — | Produit | `prix-commissions-et-penalites` |
| quelle est la grille tarifaire de lancement, par ville et par profil ? | Entrées structurantes | — | Produit | `prix-commissions-et-penalites` |
| quel seuil de durée complète le seuil de 200 m pour déclencher le supplément d'escale ? | Portée MVP | UC-259 | Produit | `diddigo-chauffeur` |
| à partir de quel écart la destination est-elle considérée comme hors zone pour ce badge ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| combien de temps le chauffeur a-t-il pour tenter la seconde capture après un premier échec ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| comment le système sait-il, à l'instant d'une course, lequel des deux chauffeurs conduit réellement — déclaration manuelle avant connexion, ou détection automatique ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| existe-t-il un contrôle de qualité de la photo avant acceptation, ou seulement un contrôle de présence ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| la réputation et les points de priorité (voir UC-274) sont-ils attachés au chauffeur ou au véhicule dans ce cas de partage ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| que devient le solde d'un pro qui quitte la plateforme avec un découvert ? | Portée MVP | UC-310 | Juridique | `argent-des-pros` |
| quel est le barème de pénalité pour un refus d'offre, et comment la pénalité doublée sous 1 km s'applique-t-elle ? | Portée MVP | UC-027 | Produit | `diddigo-chauffeur` |
| quel est le barème de pénalité pour une annulation par le pro après acceptation ? | Portée MVP | UC-027, UC-273 | Produit | `diddigo-chauffeur` |
| quelle est la fenêtre de calcul des points — glissante, et sur quelle durée ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| quelle preuve, le cas échéant, le chauffeur doit-il produire pour une annulation pour absence ? | Portée MVP | — | Juridique | `diddigo-chauffeur` |
| quelles photos de véhicule sont obligatoires et lesquelles sont facultatives ? | Portée MVP | UC-270 | Produit | `diddigo-chauffeur` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie — tirage aléatoire à quelle fréquence, quel type de signalement, quelle définition d'un changement d'appareil ? | Portée MVP | — | — | `diddigo-chauffeur` |
| un préjudice matériel donne-t-il lieu à une indemnisation, et selon quelles règles ? | Portée MVP | — | Direction | `diddigo-chauffeur` |
| un véhicule peut-il être associé à plusieurs chauffeurs simultanément, ou un seul à la fois avec bascule explicite ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une annulation pour absence avant le délai est-elle simplement refusée, ou traitée comme une annulation ordinaire avec conséquence ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une déclaration de préjudice se distingue-t-elle d'un signalement de litige ordinaire (UC support-litiges), et si oui par quel circuit de traitement ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence est-elle un filtre strict (aucune offre hors zone) ou une simple priorité (offres hors zone toujours possibles) ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une zone de préférence peut-elle devenir un moyen détourné de refuser des courses sans pénalité de taux d'acceptation ? | Portée MVP | — | Produit | `diddigo-chauffeur` |
| une validation orale de supplément engage-t-elle le passager en cas de litige ? | Portée V1 | UC-307 | Juridique | `prix-commissions-et-penalites` |
| à partir de quelle maturité du processus manuel (UC-313) l'automatisation est-elle jugée sûre à activer ? | Portée V1 | — | Direction | `argent-des-pros` |
| au bout de combien de temps un paiement sans règlement correspondant devient-il une alerte ? | Portée V1 | — | Finance | `argent-des-pros` |
| ce contrôle est-il fait une fois à l'ajout du compte de retrait, ou à chaque demande de versement ? | Portée V1 | — | Produit | `argent-des-pros` |
| ce filtre s'applique-t-il aussi aux courses programmées (UC-262), dont le solde au moment du déclenchement peut différer de celui constaté à la réservation ? | Portée V1 | — | Produit | `argent-des-pros` |
| cet import est-il un fichier déposé manuellement par un administrateur, ou une tâche automatique périodique ? | Portée V1 | — | Technique | `argent-des-pros` |
| combien de fois par jour le mode retour maison peut-il être activé ? | Portée V1 | UC-265 | Produit | `diddigo-chauffeur` |
| combien de temps avant l'expiration d'un document le chauffeur est-il alerté, et à quel moment est-il bloqué ? | Portée V1 | UC-275 | Juridique | `diddigo-chauffeur` |
| comment le remboursement de 50 % après échec de livraison DiddiSend doit-il s'articuler avec le mécanisme de remboursement générique DiddiPay, une fois le wallet coursier construit ? | Portée V1 | — | Technique | `argent-des-pros` |
| le contrôle est-il figé au moment du calcul de l'offre, ou revérifié juste avant l'envoi ? | Portée V1 | — | Technique | `argent-des-pros` |
| le découvert de 2 000 F et le seuil minimum de 1 500 F sont-ils deux réglages distincts à combiner (ex. : blocage si solde < -2 000 F), ou une seule et même valeur mal nommée deux fois ? | Portée V1 | — | Produit | `argent-des-pros` |
| le découvert peut-il être dépassé en cours de course déjà acceptée, avec blocage seulement à la prochaine tentative de mise en ligne, ou la course en cours est-elle elle-même affectée ? | Portée V1 | — | Produit | `argent-des-pros` |
| le paiement d'une livraison DiddiSend transite-t-il par DiddiPay comme une course DiddiGo, ou par un mécanisme propre ? | Portée V1 | — | Technique | `argent-des-pros` |
| le pro est-il notifié et doit-il accepter une recharge initiée par son partenaire ? | Portée V1 | — | Produit | `argent-des-pros` |
| le pro peut-il ajouter un compte de retrait au nom d'un tiers, sous quelles conditions, ou est-ce strictement interdit ? | Portée V1 | — | Juridique | `argent-des-pros` |
| le seuil de 1 500 F et le découvert de 2 000 F sont-ils deux réglages distincts (solde minimum pour accepter, plancher négatif toléré), ou la même valeur exprimée différemment ? | Portée V1 | — | Produit | `argent-des-pros` |
| le seuil de durée de 3 min recommandé pour le supplément d'escale est-il retenu ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| le versement du pro DiddiGo doit-il réutiliser le mécanisme de retrait DiddiPay-Fund existant, ou en construire un propre au wallet chauffeur ? | Portée V1 | — | Technique | `argent-des-pros` |
| quel est le barème des pénalités d'annulation, par persona et par moment ? | Portée V1 | UC-184, UC-308 | Produit | `prix-commissions-et-penalites` |
| quel est le pas de monnaie disponible, et l'arrondi se fait-il au bénéfice du client ou du chauffeur ? | Portée V1 | UC-306 | Produit | `prix-commissions-et-penalites` |
| quel est le plafond de temps d'attente facturable sur une même course ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| quel jour de la semaine les versements sont-ils exécutés ? | Portée V1 | UC-313 | Administration | `argent-des-pros` |
| quel plafond d'espèces un coursier peut-il détenir avant suspension des missions payées en espèces ? | Portée V1 | UC-311 | Produit / Produit / Risque | `argent-des-pros` |
| quel plafond limite la majoration, et comment est-il rendu public au passager ? | Portée V1 | — | Produit | `prix-commissions-et-penalites` |
| quelle est l'assiette des frais de tentative sur une livraison échouée ? | Portée V1 | UC-185 | Produit | `prix-commissions-et-penalites` |
| quelle part de la majoration est versée au pro — recommandé 100 %, non tranché ? | Portée V1 | — | Administration | `prix-commissions-et-penalites` |
| quels déclencheurs autres que l'inactivité de 2 semaines provoquent un contrôle selfie ? | Portée V1 | UC-268 | Produit | `diddigo-chauffeur` |
| qui peut annuler un reversement déjà enregistré, et jusqu'à quand ? | Portée V1 | — | Produit | `argent-des-pros` |
| qui peut être un point agréé — un partenaire, un point relais DiddiSend, une agence dédiée ? | Portée V1 | — | Produit | `argent-des-pros` |
| qui supporte les frais de transfert d'un versement, la plateforme ou le pro ? | Portée V1 | UC-191, UC-315 | Administration | `argent-des-pros` |
| un ajustement direct d'une ligne de grand livre du wallet pro (hors remboursement d'un paiement passager) doit-il exister comme action distincte, avec les mêmes garde-fous (motif, seuil, second approbateur) ? | Portée V1 | — | Produit | `argent-des-pros` |
| un écart de reversement déclenche-t-il un contrôle supplémentaire ou une alerte ? | Portée V1 | — | Finance | `argent-des-pros` |
| un lot marqué envoyé par erreur peut-il être rouvert, et par qui ? | Portée V1 | — | Produit | `argent-des-pros` |
| un palier d'alerte existe-t-il avant le plafond, et à quel niveau ? | Portée V1 | — | Produit | `argent-des-pros` |
| un versement échoué peut-il être relancé directement par le pro, ou doit-il repasser par une nouvelle demande ? | Portée V1 | — | Produit | `argent-des-pros` |
| une recharge en espèces mal saisie peut-elle être corrigée, par qui et jusqu'à quand ? | Portée V1 | — | Produit | `argent-des-pros` |
| une recharge en espèces peut-elle être enregistrée hors ligne puis synchronisée ? | Portée V1 | — | — | `argent-des-pros` |
| une recharge par un partenaire crée-t-elle une créance du pro envers le partenaire (avance), ou est-ce un don sans contrepartie ? | Portée V1 | — | Produit | `argent-des-pros` |

**Faits à établir** — 33

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| l'application du chauffeur transmet-elle systématiquement l'identifiant de course avec sa position pendant une course ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | Portée MVP | — | Technique | `argent-des-pros` |
| ce cas est-il contrôlé côté serveur ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce format brut est-il celui que l'application affiche au chauffeur, ou une mise en forme intervient-elle côté application ? | Portée MVP | — | — | `diddigo-chauffeur` |
| ce que contient exactement la réponse de GET /v1/me/scores, et si elle peut porter les points de priorité | Portée MVP | — | Technique | `diddigo-chauffeur` |
| correspondance entre ces noms d'écran et les écrans réels de l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| l'application fait-elle les deux appels — capabilities et drivers/me — pour construire cet écran, ou l'un des deux suffit-il selon le contexte ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| la route de grand livre accepte-t-elle un filtre par date, ou l'application doit-elle paginer intégralement puis filtrer localement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| laquelle des deux formes, identifiant de fichier ou URL, est la voie officielle pour l'application pro | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code fixe ce délai à 15 s via la constante OFFER_TTL_SECONDS ; la décision de la section 4 est encore à trancher, entre 60 s, 3 min et une recommandation de 20 s | Portée MVP | — | — | `diddigo-chauffeur` |
| le code fixe le délai de réponse à une offre à 15 s ; la décision est encore à trancher | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le contrôle « véhicule à l'arrêt » s'appuie-t-il sur la dernière position connue, ou faut-il une confirmation explicite du chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le decoupage en zones utilisé par diddimap-cartographie et zones-couverture-et-majoration est-il réutilisable ici, ou faut-il un découpage propre au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le format brut du motif de rejet, avec l'identifiant technique de l'administrateur, est-il celui affiché au chauffeur ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le lien avec l'alerte d'urgence en cours de course (UC-urgence-et-securite-des-personnes) — une déclaration de préjudice grave doit-elle pouvoir déclencher la même chaîne d'alerte ? | Portée MVP | — | Sécurité | `diddigo-chauffeur` |
| le modèle de données actuel associe-t-il un véhicule à un seul chauffeur, ou la relation est-elle déjà multiple ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le passage hors ligne est-il bloqué pendant une course en cours, ou seulement sans effet sur le dispatch pendant ce temps, laissant la course se dérouler normalement ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| un chauffeur peut-il émettre une position sur une course à laquelle il n'est pas affecté ? | Portée MVP | — | Technique | `diddigo-chauffeur` |
| correspondance entre ces noms d'écran et les écrans réels des applications pro et d'administration | Portée V1 | — | Technique | `argent-des-pros` |
| l'encours d'espèces coursier partage-t-il le même wallet que le solde de commission (UC-189, UC-190), ou est-ce un compteur distinct ? | Portée V1 | — | Technique | `argent-des-pros` |
| la commission estimée utilisée ici est-elle la même valeur que celle affichée au passager à l'estimation, ou un calcul distinct côté matching ? | Portée V1 | — | Technique | `argent-des-pros` |
| le mécanisme de commande à approbation de DiddiAdmin (UC-193) peut-il porter une commande par lot, ou seulement une commande unitaire par pro ? | Portée V1 | — | Technique | `argent-des-pros` |
| le montant de 5 000 F couvre-t-il confortablement les frais de transfert réels des fournisseurs mobile money utilisés ? | Portée V1 | — | Finance | `argent-des-pros` |
| le rejet actuel du moyen de paiement espèces dans `wallet_service.py` est-il une limitation technique temporaire ou une décision de sécurité délibérée à respecter ? | Portée V1 | — | Technique | `argent-des-pros` |
| le reversement d'espèces est-il rattaché à un point physique précis (agence, hub), ou peut-il être enregistré par n'importe quel responsable habilité ? | Portée V1 | — | Ops | `argent-des-pros` |
| le seuil de 30 000 F constaté dans le code est-il une valeur définitive validée par la direction, ou un réglage provisoire de développement ? | Portée V1 | — | Direction | `argent-des-pros` |
| les fournisseurs mobile money utilisés exposent-ils une vérification de titulaire de compte (name match) via leur API ? | Portée V1 | — | Technique | `argent-des-pros` |
| Paystack fournit-il un rapport de règlement téléchargeable ou une API de settlement exploitable pour cet import ? | Portée V1 | — | Technique | `argent-des-pros` |
| pourquoi `payment_released` a-t-il été ajouté à l'énumération sans jamais être câblé — un développement interrompu, ou une intention encore valide ? | Portée V1 | — | Technique | `argent-des-pros` |
| quels motifs d'échec mobile money sont réellement renvoyés par les fournisseurs utilisés, pour préparer leur traduction en messages clairs ? | Portée V1 | — | Technique | `argent-des-pros` |
| quels moyens mobile money sont réellement actifs en production, au-delà de ceux vus dans le code ? | Portée V1 | — | Technique | `argent-des-pros` |
| settings.driver_min_balance est un réglage global unique ; peut-il différer par ville ou par catégorie de véhicule ? | Portée V1 | — | Produit | `argent-des-pros` |
| un montant minimum ou maximum de recharge est-il imposé, ou tout montant positif est-il accepté ? | Portée V1 | — | Produit | `argent-des-pros` |

**Contradictions entre deux sources** — 9

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| services.py applique un taux de commission de 8 % via la constante _COMMISSION_RATE, la décision du 14/09 fixe la commission DiddiGo à 10 % | Portée MVP | — | Produit | `diddigo-chauffeur` |
| la fiche de lot indique que les six photos de véhicule sont toutes facultatives ; le contrôle d'approbation du dossier exige en réalité quatre des six photos plus l'habitacle, seules la photo générique et l'autorisation de transport restant facultatives | Portée MVP | — | Technique | `diddigo-chauffeur` |
| le code applique un taux de commission de 8 % par constante, la décision du 14/09 fixe la commission DiddiGo à 10 % ; voir la fiche du lot prix-commissions-et-penalites | Portée MVP | — | — | `diddigo-chauffeur` |
| le code prévoit six emplacements de photo de véhicule, tous facultatifs ; UC-270 en exige sept, obligatoires | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le moteur d'attribution de DiddiGo offre la course à un chauffeur à la fois, la décision du 14/09 impose des vagues de 5 pros simultanément | Portée MVP | — | Produit | `diddigo-chauffeur` |
| le solde minimum est configuré à zéro dans tous les fichiers de déploiement lus, la décision du 14/09 fixe 1 500 F | Portée MVP | UC-190 | Technique / Technique / Exploitation | `argent-des-pros` |
| UC-270 demande sept photos, dont l'habitacle avant et arrière et le coffre ; le code ne prévoit que six emplacements, sans distinction de face pour l'habitacle et sans emplacement de coffre | Portée MVP | — | Produit | `diddigo-chauffeur` |
| ce use case est classé à créer sur l'axe back et noté prévu en V2 dans le cahier des charges DiddiGo ; le calcul du prix réel à partir des traces existe et fonctionne, avec conservation de l'écart | Portée V1 | — | Technique | `prix-commissions-et-penalites` |
| le taux de commission appliqué par DiddiGo dans le code est de 8 %, la décision du 14/09 fixe 10 % | Portée V1 | UC-187, UC-350 | Produit | `prix-commissions-et-penalites` |

---

### PAR-019 — Limites du lancement

**Décisions manquantes** — 13

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel est le statut juridique du montage de location-vente de véhicule ? | Portée MVP | UC-124, UC-125 | Juridique | `partenaires-et-flottes` |
| quelle est la part du partenaire de flotte, et sur quelle assiette est-elle calculée ? | Portée MVP | UC-126, UC-127 | Administration | `partenaires-et-flottes` |
| quelles pièces d'entreprise sont exigées d'un partenaire, et lesquelles bloquent l'activation ? | Portée MVP | UC-121 | Juridique | `partenaires-et-flottes` |
| un partenaire peut-il créer son organisation lui-même, ou passe-t-il toujours par un administrateur ? | Portée MVP | UC-120, UC-121 | Produit | `partenaires-et-flottes` |
| un partenaire peut-il rattacher un pro dont le dossier KYC n'est pas encore validé ? | Portée MVP | — | — | `partenaires-et-flottes` |
| un pro peut-il être rattaché à plusieurs partenaires, ou à un seul ? | Portée MVP | UC-123 | Produit | `partenaires-et-flottes` |
| combien de temps dure une majoration exceptionnelle déclenchée manuellement, et qui peut la déclencher ? | Portée V1 | UC-295 | Produit | `zones-couverture-et-majoration` |
| la part du partenaire est-elle prélevée sur la plateforme ou sur le pro ? | Portée V1 | UC-127 | Administration | `partenaires-et-flottes` |
| quel est le montant du supplément de retour à vide, et comment est-il calculé ? | Portée V1 | UC-290, UC-292 | Produit | `zones-couverture-et-majoration` |
| quel rapport demandes/chauffeurs déclenche une majoration, et selon quelle formule ? | Portée V1 | — | Produit | `zones-couverture-et-majoration` |
| quelle distance maximale hors zone est acceptée avant refus d'une course ? | Portée V1 | UC-291 | Produit | `zones-couverture-et-majoration` |
| quelles sont les plages horaires de majoration et leurs coefficients ? | Portée V1 | UC-294 | Produit | `zones-couverture-et-majoration` |
| le périmètre autorisé d'un véhicule est-il la zone de service, ou un périmètre propre au partenaire ? | Portée Later | UC-299 | Produit | `zones-couverture-et-majoration` |

**Faits à établir** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| existe-t-il dans DiddiSend un moyen de rattacher un coursier à un partenaire ? | Portée MVP | — | Technique | `partenaires-et-flottes` |
| la commission de partenaire déclarée sur l'organisation est-elle exploitée ailleurs que dans DiddiGo — par exemple lors d'un versement manuel ? | Portée MVP | — | Technique | `partenaires-et-flottes` |
| la notion de ville de la grille tarifaire de DiddiGo et la couverture de DiddiMap désignent-elles le même périmètre ? | Portée V1 | — | Technique | `zones-couverture-et-majoration` |

**Contradictions entre deux sources** — 10

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case décrit une action du partenaire ; la route correspondante est réservée à l'administrateur | Portée MVP | — | — | `partenaires-et-flottes` |
| les use cases UC-120 à UC-125 décrivent des actions du partenaire ; toutes les routes correspondantes sont réservées à l'administrateur | Portée MVP | — | Produit | `partenaires-et-flottes` |
| ce use case demande un polygone de zone de service ; DiddiMap implémente un rectangle défini par quatre valeurs de configuration, non modifiable sans redéploiement | Portée V1 | — | — | `zones-couverture-et-majoration` |
| ce use case demande un polygone ; DiddiMap implémente un rectangle de configuration non modifiable | Portée V1 | — | Technique | `zones-couverture-et-majoration` |
| la commission est aujourd'hui calculée sur le prix total majoration comprise ; ce use case demande qu'elle soit calculée sur le prix de base et que la majoration revienne intégralement au pro | Portée V1 | — | Produit | `zones-couverture-et-majoration` |
| la commission est calculée sur le prix total majoration comprise ; ce use case demande le prix de base | Portée V1 | — | Produit | `zones-couverture-et-majoration` |
| la direction décide le 14/09 que le plafond de majoration reste interne et non public ; la section 4 du document de référence exige qu'il soit public, « ce qui évite le scandale » — les deux décisions portent la même date et se contredisent | Portée V1 | — | Produit | `zones-couverture-et-majoration` |
| la section 4 du document de référence exige un plafond de majoration public ; la relecture du 14/09 décide que ce plafond reste interne à l'algorithme | Portée V1 | — | Produit | `zones-couverture-et-majoration` |
| UC-293 du lot zones et UC-265 et UC-266 du lot chauffeur décrivent des fonctionnalités qui se recouvrent sans que leur découpage soit explicite | Portée V1 | — | — | `zones-couverture-et-majoration` |
| UC-293 et les use cases UC-265 et UC-266 du lot chauffeur décrivent des fonctionnalités qui se recouvrent | Portée V1 | — | Produit | `zones-couverture-et-majoration` |

---

## DiddiPay — payer, retirer, rapprocher

### PAR-028 — Payer depuis un module

**Décisions manquantes** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | Portée MVP | — | Produit | `diddipay` |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | Portée MVP | UC-072 | Juridique | `diddipay` |
| quelle est la durée de validité d'un code QR de paiement marchand ? | Portée V1 | UC-074 | Produit | `diddipay` |

**Faits à établir** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | Portée MVP | — | Technique | `diddipay` |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | Portée MVP | — | — | `diddipay` |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | Portée MVP | — | Technique | `diddipay` |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | Portée MVP | — | Produit | `diddipay` |

**Contradictions entre deux sources** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | Portée MVP | — | Technique | `diddipay` |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | Portée MVP | — | — | `diddipay` |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | Portée MVP | — | Produit | `diddipay` |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | Portée MVP | — | — | `diddipay` |

---

### PAR-029 — Retirer les gains

**Limite déclarée par le planning.** Vérification du bénéficiaire : capacité du prestataire à confirmer.

**Décisions manquantes** — 31

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | Portée MVP | — | Produit | `diddipay` |
| que devient le solde d'un pro qui quitte la plateforme avec un découvert ? | Portée MVP | UC-310 | Juridique | `argent-des-pros` |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | Portée MVP | UC-072 | Juridique | `diddipay` |
| à partir de quelle maturité du processus manuel (UC-313) l'automatisation est-elle jugée sûre à activer ? | Portée V1 | — | Direction | `argent-des-pros` |
| au bout de combien de temps un paiement sans règlement correspondant devient-il une alerte ? | Portée V1 | — | Finance | `argent-des-pros` |
| ce contrôle est-il fait une fois à l'ajout du compte de retrait, ou à chaque demande de versement ? | Portée V1 | — | Produit | `argent-des-pros` |
| ce filtre s'applique-t-il aussi aux courses programmées (UC-262), dont le solde au moment du déclenchement peut différer de celui constaté à la réservation ? | Portée V1 | — | Produit | `argent-des-pros` |
| cet import est-il un fichier déposé manuellement par un administrateur, ou une tâche automatique périodique ? | Portée V1 | — | Technique | `argent-des-pros` |
| comment le remboursement de 50 % après échec de livraison DiddiSend doit-il s'articuler avec le mécanisme de remboursement générique DiddiPay, une fois le wallet coursier construit ? | Portée V1 | — | Technique | `argent-des-pros` |
| le contrôle est-il figé au moment du calcul de l'offre, ou revérifié juste avant l'envoi ? | Portée V1 | — | Technique | `argent-des-pros` |
| le découvert de 2 000 F et le seuil minimum de 1 500 F sont-ils deux réglages distincts à combiner (ex. : blocage si solde < -2 000 F), ou une seule et même valeur mal nommée deux fois ? | Portée V1 | — | Produit | `argent-des-pros` |
| le découvert peut-il être dépassé en cours de course déjà acceptée, avec blocage seulement à la prochaine tentative de mise en ligne, ou la course en cours est-elle elle-même affectée ? | Portée V1 | — | Produit | `argent-des-pros` |
| le paiement d'une livraison DiddiSend transite-t-il par DiddiPay comme une course DiddiGo, ou par un mécanisme propre ? | Portée V1 | — | Technique | `argent-des-pros` |
| le pro est-il notifié et doit-il accepter une recharge initiée par son partenaire ? | Portée V1 | — | Produit | `argent-des-pros` |
| le pro peut-il ajouter un compte de retrait au nom d'un tiers, sous quelles conditions, ou est-ce strictement interdit ? | Portée V1 | — | Juridique | `argent-des-pros` |
| le seuil de 1 500 F et le découvert de 2 000 F sont-ils deux réglages distincts (solde minimum pour accepter, plancher négatif toléré), ou la même valeur exprimée différemment ? | Portée V1 | — | Produit | `argent-des-pros` |
| le versement du pro DiddiGo doit-il réutiliser le mécanisme de retrait DiddiPay-Fund existant, ou en construire un propre au wallet chauffeur ? | Portée V1 | — | Technique | `argent-des-pros` |
| quel jour de la semaine les versements sont-ils exécutés ? | Portée V1 | UC-313 | Administration | `argent-des-pros` |
| quel plafond d'espèces un coursier peut-il détenir avant suspension des missions payées en espèces ? | Portée V1 | UC-311 | Produit / Produit / Risque | `argent-des-pros` |
| quelle est la durée de validité d'un code QR de paiement marchand ? | Portée V1 | UC-074 | Produit | `diddipay` |
| qui peut annuler un reversement déjà enregistré, et jusqu'à quand ? | Portée V1 | — | Produit | `argent-des-pros` |
| qui peut être un point agréé — un partenaire, un point relais DiddiSend, une agence dédiée ? | Portée V1 | — | Produit | `argent-des-pros` |
| qui supporte les frais de transfert d'un versement, la plateforme ou le pro ? | Portée V1 | UC-191, UC-315 | Administration | `argent-des-pros` |
| un ajustement direct d'une ligne de grand livre du wallet pro (hors remboursement d'un paiement passager) doit-il exister comme action distincte, avec les mêmes garde-fous (motif, seuil, second approbateur) ? | Portée V1 | — | Produit | `argent-des-pros` |
| un écart de reversement déclenche-t-il un contrôle supplémentaire ou une alerte ? | Portée V1 | — | Finance | `argent-des-pros` |
| un lot marqué envoyé par erreur peut-il être rouvert, et par qui ? | Portée V1 | — | Produit | `argent-des-pros` |
| un palier d'alerte existe-t-il avant le plafond, et à quel niveau ? | Portée V1 | — | Produit | `argent-des-pros` |
| un versement échoué peut-il être relancé directement par le pro, ou doit-il repasser par une nouvelle demande ? | Portée V1 | — | Produit | `argent-des-pros` |
| une recharge en espèces mal saisie peut-elle être corrigée, par qui et jusqu'à quand ? | Portée V1 | — | Produit | `argent-des-pros` |
| une recharge en espèces peut-elle être enregistrée hors ligne puis synchronisée ? | Portée V1 | — | — | `argent-des-pros` |
| une recharge par un partenaire crée-t-elle une créance du pro envers le partenaire (avance), ou est-ce un don sans contrepartie ? | Portée V1 | — | Produit | `argent-des-pros` |

**Faits à établir** — 19

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | Portée MVP | — | Technique | `argent-des-pros` |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | Portée MVP | — | — | `diddipay` |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | Portée MVP | — | Technique | `diddipay` |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | Portée MVP | — | Produit | `diddipay` |
| correspondance entre ces noms d'écran et les écrans réels des applications pro et d'administration | Portée V1 | — | Technique | `argent-des-pros` |
| l'encours d'espèces coursier partage-t-il le même wallet que le solde de commission (UC-189, UC-190), ou est-ce un compteur distinct ? | Portée V1 | — | Technique | `argent-des-pros` |
| la commission estimée utilisée ici est-elle la même valeur que celle affichée au passager à l'estimation, ou un calcul distinct côté matching ? | Portée V1 | — | Technique | `argent-des-pros` |
| le mécanisme de commande à approbation de DiddiAdmin (UC-193) peut-il porter une commande par lot, ou seulement une commande unitaire par pro ? | Portée V1 | — | Technique | `argent-des-pros` |
| le montant de 5 000 F couvre-t-il confortablement les frais de transfert réels des fournisseurs mobile money utilisés ? | Portée V1 | — | Finance | `argent-des-pros` |
| le rejet actuel du moyen de paiement espèces dans `wallet_service.py` est-il une limitation technique temporaire ou une décision de sécurité délibérée à respecter ? | Portée V1 | — | Technique | `argent-des-pros` |
| le reversement d'espèces est-il rattaché à un point physique précis (agence, hub), ou peut-il être enregistré par n'importe quel responsable habilité ? | Portée V1 | — | Ops | `argent-des-pros` |
| le seuil de 30 000 F constaté dans le code est-il une valeur définitive validée par la direction, ou un réglage provisoire de développement ? | Portée V1 | — | Direction | `argent-des-pros` |
| les fournisseurs mobile money utilisés exposent-ils une vérification de titulaire de compte (name match) via leur API ? | Portée V1 | — | Technique | `argent-des-pros` |
| Paystack fournit-il un rapport de règlement téléchargeable ou une API de settlement exploitable pour cet import ? | Portée V1 | — | Technique | `argent-des-pros` |
| pourquoi `payment_released` a-t-il été ajouté à l'énumération sans jamais être câblé — un développement interrompu, ou une intention encore valide ? | Portée V1 | — | Technique | `argent-des-pros` |
| quels motifs d'échec mobile money sont réellement renvoyés par les fournisseurs utilisés, pour préparer leur traduction en messages clairs ? | Portée V1 | — | Technique | `argent-des-pros` |
| quels moyens mobile money sont réellement actifs en production, au-delà de ceux vus dans le code ? | Portée V1 | — | Technique | `argent-des-pros` |
| settings.driver_min_balance est un réglage global unique ; peut-il différer par ville ou par catégorie de véhicule ? | Portée V1 | — | Produit | `argent-des-pros` |
| un montant minimum ou maximum de recharge est-il imposé, ou tout montant positif est-il accepté ? | Portée V1 | — | Produit | `argent-des-pros` |

**Contradictions entre deux sources** — 5

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | Portée MVP | — | Technique | `diddipay` |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | Portée MVP | — | — | `diddipay` |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | Portée MVP | — | Produit | `diddipay` |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | Portée MVP | — | — | `diddipay` |
| le solde minimum est configuré à zéro dans tous les fichiers de déploiement lus, la décision du 14/09 fixe 1 500 F | Portée MVP | UC-190 | Technique / Technique / Exploitation | `argent-des-pros` |

---

### PAR-030 — Rembourser et rapprocher

**Limite déclarée par le planning.** Remboursement cash (restitution physique) à définir ; format Odoo à valider par la finance.

**Décisions manquantes** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | Portée MVP | — | Produit | `diddipay` |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | Portée MVP | UC-072 | Juridique | `diddipay` |
| quelle est la durée de validité d'un code QR de paiement marchand ? | Portée V1 | UC-074 | Produit | `diddipay` |

**Faits à établir** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | Portée MVP | — | Technique | `diddipay` |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | Portée MVP | — | — | `diddipay` |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | Portée MVP | — | Technique | `diddipay` |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | Portée MVP | — | Produit | `diddipay` |

**Contradictions entre deux sources** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | Portée MVP | — | Technique | `diddipay` |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | Portée MVP | — | — | `diddipay` |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | Portée MVP | — | Produit | `diddipay` |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | Portée MVP | — | — | `diddipay` |

---

### PAR-031 — Périmètre exact

**Limite déclarée par le planning.** Opérateurs de paiement activés au lancement à confirmer et tester.

**Décisions manquantes** — 3

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le paiement d'une mission peut-il être réglé depuis le wallet utilisateur ? | Portée MVP | — | Produit | `diddipay` |
| quel plafond s'applique à un transfert entre utilisateurs, par opération et par période ? | Portée MVP | UC-072 | Juridique | `diddipay` |
| quelle est la durée de validité d'un code QR de paiement marchand ? | Portée V1 | UC-074 | Produit | `diddipay` |

**Faits à établir** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le retrait Paystack, non implémenté dans le code lu, est-il prévu à court terme, ou le retrait passera-t-il uniquement par Orange Money et Wave ? | Portée MVP | — | Technique | `diddipay` |
| ce barème exact est-il déjà implémenté tel quel dans le code, ou reste-t-il à ajuster pour correspondre à la décision du 14/09 ? | Portée MVP | — | — | `diddipay` |
| le barème de blocage progressif (3+2 tentatives, 10 minutes) est-il déjà implémenté tel quel, ou reste-t-il à ajuster ? | Portée MVP | — | Technique | `diddipay` |
| le parcours de dépôt explique-t-il clairement à l'utilisateur qu'un réseau mobile money choisi (wave, orange, mtn) ouvre en réalité un formulaire Paystack et non l'application du réseau ? | Portée MVP | — | Produit | `diddipay` |

**Contradictions entre deux sources** — 4

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, déclarées à ne plus utiliser | Portée MVP | — | Technique | `diddipay` |
| ce use case est classé MVP et s'appuie sur les routes historiques du portefeuille, que le document de référence déclare à ne plus utiliser pour une nouvelle intégration entre modules | Portée MVP | — | — | `diddipay` |
| le mot wallet désigne deux objets distincts et le glossaire n'en définit qu'un | Portée MVP | — | Produit | `diddipay` |
| le mot wallet désigne deux objets distincts — le compte interne du pro dans DiddiGo et le portefeuille utilisateur de DiddiPay — et le glossaire n'en définit qu'un | Portée MVP | — | — | `diddipay` |

---

## Support — reclamer et faire trancher

### PAR-009 — Faire une réclamation à toute heure

**Décisions manquantes** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| pendant combien de temps après une mission un client peut-il signaler un problème ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| quelle est la durée exacte de la fenêtre de contact pour un objet oublié ? | Portée V1 | UC-347 | Produit | `support-litiges-et-objets-oublies` |
| quels motifs de signalement sont proposés au client ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| qui arbitre une contestation de gain ou de pénalité par un pro, et dans quel délai ? | Portée V1 | UC-179 | Administration | `support-litiges-et-objets-oublies` |
| suite à donner à un colis non livré au-delà du remboursement de 50 % ? | Portée V1 | — | — | `support-litiges-et-objets-oublies` |
| un geste commercial est-il imputé à la plateforme ou au pro fautif ? | Portée V1 | UC-178 | Administration | `support-litiges-et-objets-oublies` |
| un objet oublié non réclamé devient quoi, et au bout de combien de temps ? | Portée V1 | UC-176 | Juridique | `support-litiges-et-objets-oublies` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel rôle du back-office donne accès au remboursement DiddiPay aujourd'hui, et ce rôle est-il attribuable à un agent de support ? | Portée V1 | — | Technique | `support-litiges-et-objets-oublies` |

**Contradictions entre deux sources** — 2

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le chat de mission se ferme à la fin de la mission alors que le canal objet oublié s'ouvre après | Portée V1 | — | Produit | `support-litiges-et-objets-oublies` |
| le chat de mission se ferme à la fin de la mission (`communication-en-mission`, UC-154), alors que ce canal objet oublié s'ouvre après la fin de la mission ; les deux reposent sur le même mécanisme mais avec des fenêtres opposées | Portée V1 | — | — | `support-litiges-et-objets-oublies` |

---

### PAR-010 — Passer à un humain sans perdre le contexte

**Limite déclarée par le planning.** Règles de fermeture/réouverture/délais à valider. Accueil H24 ≠ humain H24.

**Décisions manquantes** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| pendant combien de temps après une mission un client peut-il signaler un problème ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| quelle est la durée exacte de la fenêtre de contact pour un objet oublié ? | Portée V1 | UC-347 | Produit | `support-litiges-et-objets-oublies` |
| quels motifs de signalement sont proposés au client ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| qui arbitre une contestation de gain ou de pénalité par un pro, et dans quel délai ? | Portée V1 | UC-179 | Administration | `support-litiges-et-objets-oublies` |
| suite à donner à un colis non livré au-delà du remboursement de 50 % ? | Portée V1 | — | — | `support-litiges-et-objets-oublies` |
| un geste commercial est-il imputé à la plateforme ou au pro fautif ? | Portée V1 | UC-178 | Administration | `support-litiges-et-objets-oublies` |
| un objet oublié non réclamé devient quoi, et au bout de combien de temps ? | Portée V1 | UC-176 | Juridique | `support-litiges-et-objets-oublies` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel rôle du back-office donne accès au remboursement DiddiPay aujourd'hui, et ce rôle est-il attribuable à un agent de support ? | Portée V1 | — | Technique | `support-litiges-et-objets-oublies` |

**Contradictions entre deux sources** — 2

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le chat de mission se ferme à la fin de la mission alors que le canal objet oublié s'ouvre après | Portée V1 | — | Produit | `support-litiges-et-objets-oublies` |
| le chat de mission se ferme à la fin de la mission (`communication-en-mission`, UC-154), alors que ce canal objet oublié s'ouvre après la fin de la mission ; les deux reposent sur le même mécanisme mais avec des fenêtres opposées | Portée V1 | — | — | `support-litiges-et-objets-oublies` |

---

### PAR-011 — Traiter les litiges de chaque module

**Limite déclarée par le planning.** Plafonds de geste commercial et escalade à définir.

**Décisions manquantes** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| pendant combien de temps après une mission un client peut-il signaler un problème ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| quelle est la durée exacte de la fenêtre de contact pour un objet oublié ? | Portée V1 | UC-347 | Produit | `support-litiges-et-objets-oublies` |
| quels motifs de signalement sont proposés au client ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| qui arbitre une contestation de gain ou de pénalité par un pro, et dans quel délai ? | Portée V1 | UC-179 | Administration | `support-litiges-et-objets-oublies` |
| suite à donner à un colis non livré au-delà du remboursement de 50 % ? | Portée V1 | — | — | `support-litiges-et-objets-oublies` |
| un geste commercial est-il imputé à la plateforme ou au pro fautif ? | Portée V1 | UC-178 | Administration | `support-litiges-et-objets-oublies` |
| un objet oublié non réclamé devient quoi, et au bout de combien de temps ? | Portée V1 | UC-176 | Juridique | `support-litiges-et-objets-oublies` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel rôle du back-office donne accès au remboursement DiddiPay aujourd'hui, et ce rôle est-il attribuable à un agent de support ? | Portée V1 | — | Technique | `support-litiges-et-objets-oublies` |

**Contradictions entre deux sources** — 2

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le chat de mission se ferme à la fin de la mission alors que le canal objet oublié s'ouvre après | Portée V1 | — | Produit | `support-litiges-et-objets-oublies` |
| le chat de mission se ferme à la fin de la mission (`communication-en-mission`, UC-154), alors que ce canal objet oublié s'ouvre après la fin de la mission ; les deux reposent sur le même mécanisme mais avec des fenêtres opposées | Portée V1 | — | — | `support-litiges-et-objets-oublies` |

---

### PAR-012 — Limiter les risques de l'IA

**Décisions manquantes** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| pendant combien de temps après une mission un client peut-il signaler un problème ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| quelle est la durée exacte de la fenêtre de contact pour un objet oublié ? | Portée V1 | UC-347 | Produit | `support-litiges-et-objets-oublies` |
| quels motifs de signalement sont proposés au client ? | Portée V1 | UC-175 | Produit | `support-litiges-et-objets-oublies` |
| qui arbitre une contestation de gain ou de pénalité par un pro, et dans quel délai ? | Portée V1 | UC-179 | Administration | `support-litiges-et-objets-oublies` |
| suite à donner à un colis non livré au-delà du remboursement de 50 % ? | Portée V1 | — | — | `support-litiges-et-objets-oublies` |
| un geste commercial est-il imputé à la plateforme ou au pro fautif ? | Portée V1 | UC-178 | Administration | `support-litiges-et-objets-oublies` |
| un objet oublié non réclamé devient quoi, et au bout de combien de temps ? | Portée V1 | UC-176 | Juridique | `support-litiges-et-objets-oublies` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| quel rôle du back-office donne accès au remboursement DiddiPay aujourd'hui, et ce rôle est-il attribuable à un agent de support ? | Portée V1 | — | Technique | `support-litiges-et-objets-oublies` |

**Contradictions entre deux sources** — 2

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| le chat de mission se ferme à la fin de la mission alors que le canal objet oublié s'ouvre après | Portée V1 | — | Produit | `support-litiges-et-objets-oublies` |
| le chat de mission se ferme à la fin de la mission (`communication-en-mission`, UC-154), alors que ce canal objet oublié s'ouvre après la fin de la mission ; les deux reposent sur le même mécanisme mais avec des fenêtres opposées | Portée V1 | — | — | `support-litiges-et-objets-oublies` |

---

## Pilotage — suivre, proteger, aider

### PAR-013 — Suivre l'activité de chaque module

**Limite déclarée par le planning.** Dictionnaire des indicateurs à écrire avant la recette.

Aucune entrée ouverte rattachée à ce parcours par les registres.

### PAR-014 — Socle anti-fraude

**Limite déclarée par le planning.** Seuils détaillés à définir.

**Décisions manquantes** — 10

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| peut-on refuser un compte au motif que l'appareil a déjà servi, et sur quelle base ? | Portée MVP | UC-327 | Juridique | `reputation-et-fraude-cote-pro` |
| un pro bloqué pour position simulée peut-il faire recours, et auprès de qui ? | Portée MVP | UC-326 | Produit | `reputation-et-fraude-cote-pro` |
| à partir de quelle fréquence deux comptes qui se retrouvent sont-ils signalés ? | Portée V1 | UC-331 | Produit | `reputation-et-fraude-cote-pro` |
| combien de missions payées un filleul doit-il réaliser avant déblocage du bonus de parrainage ? | Portée V1 | UC-328 | Produit | `reputation-et-fraude-cote-pro` |
| que devient un gain gelé dont la fraude est confirmée ? | Portée V1 | UC-330 | Juridique | `reputation-et-fraude-cote-pro` |
| quel délai sépare le calcul d'un bonus de son versement ? | Portée V1 | UC-329 | Produit | `reputation-et-fraude-cote-pro` |
| quel écart entre distance facturée et distance réelle constitue un signalement ? | Portée V1 | UC-332 | Produit | `reputation-et-fraude-cote-pro` |
| quel seuil de note déclenche une alerte de qualité, et sur quelle fenêtre de calcul ? | Portée V1 | UC-217 | Produit | `reputation-et-fraude-cote-pro` |
| quelle est la conséquence pour un pro passé sous le seuil — avertissement, formation, suspension ? | Portée V1 | UC-217 | Administration | `reputation-et-fraude-cote-pro` |
| quels autres déclencheurs, au-delà de 2 semaines d'inactivité, provoquent un contrôle selfie ? | Portée V1 | — | Produit | `reputation-et-fraude-cote-pro` |

**Faits à établir** — 1

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| la réputation d'un pro qui exerce les deux métiers est-elle unifiée, ou reste-t-elle séparée par service ? | Portée V1 | — | Technique | `reputation-et-fraude-cote-pro` |

**Contradictions entre deux sources** — 7

| Entrée | Portée | Use cases cités | Décideur | Lot d'origine |
| --- | --- | --- | --- | --- |
| ce use case est classé à créer ; l'écart de distance est déjà calculé et conservé | Portée V1 | — | Technique | `reputation-et-fraude-cote-pro` |
| ce use case est classé à créer ; l'écart entre prix facturé et prix recalculé sur la trace réelle est déjà calculé et conservé sur chaque course | Portée V1 | UC-183 | — | `reputation-et-fraude-cote-pro` |
| ce use case est classé Later alors que UC-268 et UC-269 du lot diddigo-chauffeur, qui décrivent le même mécanisme de contrôle selfie, sont classés V1 | Portée V1 | — | Produit | `reputation-et-fraude-cote-pro` |
| ce use case est classé partiel ; la notation du passager par le chauffeur est complète | Portée V1 | — | Technique | `reputation-et-fraude-cote-pro` |
| ce use case est classé partiel sur l'axe back ; la notation du passager par le chauffeur est complète, avec contrôle de rôle et interdiction de double note | Portée V1 | — | — | `reputation-et-fraude-cote-pro` |
| UC-218, détection des courses fictives, est classé Later alors que les bonus qui en sont la cible sont classés V1 ; la protection arriverait après le risque | Portée V1 | — | Produit | `reputation-et-fraude-cote-pro` |
| UC-218 est classé Later alors que les bonus qu'il protège sont en V1 | Portée V1 | — | Produit | `reputation-et-fraude-cote-pro` |

---

### PAR-015 — Aide et enquête de satisfaction

**Limite déclarée par le planning.** Fréquence et modalités de l'enquête à préciser.

Aucune entrée ouverte rattachée à ce parcours par les registres.

## Arbitrages du document de périmètre

`diddi-scope-document/POINTS_A_ARBITRER_ET_VERIFICATIONS.md`, 9 octobre 2026. Les entrées `ARB-xxx`
qui touchent le parcours DiddiGo, reproduites telles quelles.

| Réf | Sujet | Question ou proposition à décider |
| --- | --- | --- |
| ARB-004 | Accès professionnel | Montant minimal de mise en ligne par métier ; limites et frais réels à vérifier au contrat PSP. Absence de minimum commercial de retrait déjà validée. |
| ARB-010 | Absence Go | Confirmer le départ des dix minutes à l'arrivée GPS validée ; ne pas importer implicitement le protocole d'absence Food dans Go ou Send. |
| ARB-012 | Organisation support | Calendrier et délais humains à organiser, sans astreinte opérationnelle dédiée selon la dernière décision. Distinguer reprise de ticket et urgence grave. |
| ARB-014 | DiddiScore transmodules V1 | `PROD-040` valide la phase et la portée. Définir signaux, effets, barèmes, durées, récupération, information et contestation avant implémentation ; aucun blocage automatique intermodules pour impayé au MVP. |
| ARB-015 | Remboursement cash numérique | `PROD-042` valide le principe. Spécifier les canaux réellement disponibles, la vérification du bénéficiaire et le traitement d'un client sans moyen numérique compatible. |

## Sources

| Source | Date |
| --- | --- |
| `management/specs/etat/a-trancher.md`, `a-verifier.md`, `contradictions.md` | 14/09/2026 |
| `DIDDIFREE_Planning_Lancement_19_Decembre_2026.xlsx`, onglets *Décisions* et *Parcours sources* | 09/10/2026 |
| `diddi-scope-document/POINTS_A_ARBITRER_ET_VERIFICATIONS.md` | 09/10/2026 |

Rien n'a été écrit dans `management/specs` ni dans le classeur de planning.
