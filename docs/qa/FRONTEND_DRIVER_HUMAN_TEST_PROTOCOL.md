# Protocole de test humain - Chauffeurs DiddiGo

Ce document sert aux testeurs terrain pour valider l'experience chauffeur dans
l'application DiddiGo. Il parle en use cases, pas en implementation backend.

## Objectif

Valider qu'un chauffeur peut utiliser DiddiGo de bout en bout :

- creer ou ouvrir son compte;
- completer son dossier chauffeur;
- attendre la validation KYC;
- passer en ligne;
- recevoir une course;
- accepter ou refuser;
- conduire la course;
- terminer la course;
- confirmer le paiement cash;
- recevoir les notifications importantes.

## Perimetre

Inclus dans cette vague :

- application frontend chauffeur;
- API DiddiGo staging;
- DiddiFreeID pour l'authentification;
- DiddiMap pour recherche, route et distance;
- DiddiFiles pour documents KYC si le flux est disponible;
- FCM/WebSocket pour offres et notifications;
- paiement cash.

Non bloquant pour cette vague :

- paiement digital finalise;
- wallet chauffeur;
- retrait chauffeur;
- scoring avance;
- fleet management;
- DiddiSend.

## Comptes et appareils

Preparer au minimum :

- 10 comptes chauffeurs de test;
- 3 comptes passagers de test;
- 1 compte admin ou un moyen backend pour valider le KYC;
- 10 telephones Android si possible;
- au moins 1 telephone iOS si l'application iOS est testable;
- reseaux differents si possible : Wi-Fi, 4G, connexion faible.

Chaque testeur doit noter :

```text
Date:
Nom testeur:
Telephone:
OS/version:
Version app:
Compte utilise:
Zone de test:
Ride ID:
Driver ID:
Resultat:
Capture/log:
Commentaire:
```

## Regles de verdict

Statuts :

- Pass : le use case fonctionne sans contournement.
- Fail : le use case ne fonctionne pas.
- Blocked : le test ne peut pas etre execute a cause d'une dependance.
- Needs Review : le test passe techniquement mais l'experience est confuse.

Severites :

- P0 : bloque le MVP chauffeur.
- P1 : use case majeur casse, test terrain dangereux ou inutilisable.
- P2 : contournement possible mais experience mauvaise.
- P3 : amelioration UX ou observation non bloquante.

## Use Case DRV-001 - Premiere ouverture chauffeur

Objectif :
Verifier que le chauffeur comprend comment entrer dans DiddiGo.

Prerequis :
Application installee, reseau actif.

Etapes :

1. Ouvrir l'application.
2. Choisir le parcours chauffeur si l'application propose un choix.
3. Observer les ecrans d'accueil et permissions demandees.
4. Refuser puis accepter les permissions si le flux le permet.

Resultat attendu :

- le chauffeur comprend clairement quoi faire;
- les permissions GPS/notifications sont demandees avec un texte comprehensible;
- aucun ecran bloquant incomprehensible;
- l'application ne crash pas.

Bloquant si :

- impossible de demarrer;
- permissions indispensables jamais demandees;
- le chauffeur ne peut pas continuer.

## Use Case DRV-002 - Connexion chauffeur via DiddiFreeID

Objectif :
Verifier que le chauffeur peut se connecter avec son numero/email.

Prerequis :
Compte DiddiFreeID disponible ou creation autorisee.

Etapes :

1. Entrer le numero ou l'email.
2. Demander le code OTP.
3. Entrer le code recu.
4. Arriver dans l'application DiddiGo.

Resultat attendu :

- l'OTP est accepte;
- l'utilisateur arrive dans DiddiGo;
- l'application ne demande pas de choisir un role technique;
- le role metier chauffeur depend ensuite du profil/KYC DiddiGo.

Bloquant si :

- OTP impossible a valider;
- boucle de login;
- token expire immediatement;
- l'utilisateur connecte ne peut jamais acceder au parcours chauffeur.

## Use Case DRV-003 - Creation du profil chauffeur

Objectif :
Verifier que le chauffeur peut creer son profil metier DiddiGo.

Prerequis :
Utilisateur connecte.

Etapes :

1. Aller dans le parcours chauffeur.
2. Remplir les informations demandees.
3. Ajouter les informations de permis si demande.
4. Sauvegarder.

Resultat attendu :

- profil cree;
- statut visible : en attente, rejete, ou actif;
- message clair si une information manque;
- le frontend ne fait pas semblant que le chauffeur est valide avant validation.

Bloquant si :

- profil impossible a creer;
- erreur 500;
- aucun statut KYC visible.

## Use Case DRV-004 - Upload des documents KYC

Objectif :
Verifier que le chauffeur peut ajouter les justificatifs demandes.

Prerequis :
DiddiFiles disponible, compte connecte.

Etapes :

1. Ajouter permis recto.
2. Ajouter permis verso.
3. Ajouter CNI recto.
4. Ajouter CNI verso.
5. Ajouter selfie si demande.
6. Ajouter document vehicule si demande.
7. Soumettre le dossier.

Resultat attendu :

- chaque fichier affiche un apercu ou un etat upload reussi;
- l'app ne montre jamais une URL technique MinIO;
- en cas d'erreur upload, le message explique quoi refaire;
- le dossier passe en attente de verification.
- l'admin ne peut pas valider le dossier si permis recto/verso, CNI
  recto/verso ou selfie manque.

Bloquant si :

- impossible d'envoyer les documents;
- URL signee invalide;
- le bouton final reste bloque sans explication;
- le dossier n'est pas visible cote admin apres soumission.

## Use Case DRV-005 - Blocage avant validation KYC

Objectif :
Verifier qu'un chauffeur non valide ne peut pas prendre de courses.

Prerequis :
Profil chauffeur cree mais non valide.

Etapes :

1. Essayer de passer en ligne.
2. Observer le message affiche.

Resultat attendu :

- le passage en ligne est bloque;
- l'application affiche un message du type "Dossier en cours de verification";
- le chauffeur sait quoi attendre.

Bloquant si :

- un chauffeur non valide peut passer en ligne;
- l'erreur est incomprehensible;
- l'application reste en chargement infini.

## Use Case DRV-006 - Validation admin et deblocage chauffeur

Objectif :
Verifier que la validation KYC debloque le chauffeur.

Prerequis :
Admin ou backend capable d'approuver le dossier.

Etapes :

1. Faire approuver le chauffeur.
2. Revenir dans l'application chauffeur.
3. Rafraichir le statut si necessaire.
4. Essayer de passer en ligne.

Resultat attendu :

- statut chauffeur actif/valide;
- passage en ligne possible;
- message clair si l'app doit etre relancee ou rafraichie.

Bloquant si :

- chauffeur valide toujours bloque;
- besoin de se deconnecter/reconnecter sans explication;
- incoherence entre admin/backend et frontend.

## Use Case DRV-007 - Vehicule chauffeur

Objectif :
Verifier que le chauffeur peut ajouter et utiliser son vehicule.

Prerequis :
Chauffeur connecte, KYC soumis ou valide selon regle produit.

Etapes :

1. Ajouter plaque.
2. Ajouter type/categorie vehicule.
3. Ajouter comfort level.
4. Sauvegarder.
5. Verifier l'affichage dans le profil.

Resultat attendu :

- vehicule cree;
- plaque et categorie visibles;
- comfort level visible si le frontend chauffeur l'expose;
- erreurs claires si plaque deja utilisee.

Bloquant si :

- aucun vehicule ne peut etre ajoute;
- le matching ignore la categorie vehicule;
- vehicule actif non reconnu au passage en ligne.

## Use Case DRV-008 - Passage en ligne

Objectif :
Verifier que le chauffeur peut devenir disponible.

Prerequis :
Chauffeur valide, vehicule actif, GPS autorise.

Etapes :

1. Appuyer sur "passer en ligne".
2. Verifier la position affichee.
3. Laisser l'application ouverte 2 minutes.
4. Mettre l'application en arriere-plan 2 minutes.
5. Revenir dans l'application.

Resultat attendu :

- statut en ligne visible;
- notification permanente Android si foreground service active;
- l'app ne perd pas silencieusement le statut;
- si la position est perdue, message clair.

Bloquant si :

- impossible de passer en ligne;
- statut en ligne faux;
- GPS non transmis;
- le chauffeur devient indisponible sans message.

## Use Case DRV-009 - Reception d'une course

Objectif :
Verifier que le chauffeur proche recoit une demande.

Prerequis :
Chauffeur en ligne, passager proche, categorie compatible.

Etapes :

1. Garder le chauffeur en ligne.
2. Creer une course avec un passager proche.
3. Observer l'ecran chauffeur.
4. Observer notification sonore/visuelle.

Resultat attendu :

- offre recue rapidement;
- pickup, destination et prix visibles;
- compte a rebours visible si applicable;
- aucune confusion entre plusieurs offres.

Bloquant si :

- aucune offre recue alors que le chauffeur est eligible;
- offre recue par mauvais chauffeur;
- offre sans informations minimales.

## Use Case DRV-010 - Acceptation de course

Objectif :
Verifier que le chauffeur peut accepter une offre.

Prerequis :
Offre recue.

Etapes :

1. Appuyer sur accepter.
2. Observer la confirmation.
3. Verifier que le passager voit le chauffeur.

Resultat attendu :

- course passe en matched/driver_en_route selon UX;
- chauffeur voit l'adresse pickup;
- passager voit le chauffeur;
- aucune double acceptation.

Bloquant si :

- acceptation impossible;
- course deja expiree trop vite sans message;
- passager ne voit jamais le chauffeur.

## Use Case DRV-011 - Refus de course

Objectif :
Verifier qu'un chauffeur peut refuser sans casser le matching.

Prerequis :
Offre recue.

Etapes :

1. Appuyer sur refuser.
2. Observer le retour a l'etat disponible.
3. Verifier avec un autre chauffeur si l'offre est proposee ailleurs.

Resultat attendu :

- refus confirme;
- chauffeur reste en ligne sauf regle contraire;
- course reproposee ou no_driver_found explicite.

Bloquant si :

- refus bloque l'application;
- course reste bloquee sans chauffeur;
- chauffeur devient offline sans explication.

## Use Case DRV-012 - Arrivee au pickup

Objectif :
Verifier que le chauffeur peut avancer le statut de la course.

Prerequis :
Course acceptee.

Etapes :

1. Se deplacer vers le pickup ou simuler le trajet.
2. Appuyer sur "arrive" si ce statut existe.
3. Observer l'application passager.

Resultat attendu :

- statut mis a jour;
- passager notifie;
- position chauffeur visible.

Bloquant si :

- statut impossible a changer;
- passager ne recoit aucun changement;
- mauvais statut affiche.

## Use Case DRV-013 - Demarrage de course

Objectif :
Verifier le passage en course active.

Prerequis :
Chauffeur arrive au pickup.

Etapes :

1. Demarrer la course.
2. Verifier l'ecran trajet.
3. Observer la position live.

Resultat attendu :

- statut in_progress;
- passager voit que la course a demarre;
- les positions GPS continuent.

Bloquant si :

- course impossible a demarrer;
- statut divergent chauffeur/passager;
- trace GPS absente.

## Use Case DRV-014 - Fin de course et prix final

Objectif :
Verifier que le chauffeur peut terminer la course.

Prerequis :
Course in_progress.

Etapes :

1. Arriver a destination.
2. Terminer la course.
3. Observer le prix final.
4. Comparer avec l'estimation initiale.

Resultat attendu :

- course completed;
- prix final affiche;
- si recalcul indisponible, comportement explicite et documente;
- aucun fallback silencieux.

Bloquant si :

- impossible de terminer;
- prix incoherent sans explication;
- l'application reste bloquee sur course active.

## Use Case DRV-015 - Paiement cash

Objectif :
Verifier que le chauffeur peut confirmer l'encaissement cash.

Prerequis :
Course terminee, mode cash.

Etapes :

1. Recevoir le paiement du passager.
2. Appuyer sur confirmer cash.
3. Verifier statut paiement.

Resultat attendu :

- paiement passe en collected/paye;
- chauffeur et passager voient le meme etat;
- recu ou resume visible si disponible.

Bloquant si :

- paiement impossible a confirmer;
- passager et chauffeur voient des statuts differents;
- course terminee mais paiement introuvable.

## Use Case DRV-016 - Perte de connexion

Objectif :
Verifier que l'app gere les mauvaises connexions.

Prerequis :
Chauffeur en ligne ou en course.

Etapes :

1. Couper internet 30 secondes.
2. Remettre internet.
3. Observer l'etat chauffeur.

Resultat attendu :

- message de connexion perdu;
- tentative de reconnexion;
- pas de crash;
- etat resynchronise apres retour reseau.

Bloquant si :

- course perdue;
- chauffeur reste dans un etat faux;
- impossible de recuperer sans reinstall.

## Use Case DRV-017 - Application en arriere-plan

Objectif :
Verifier les limites connues du WebSocket et du foreground service.

Prerequis :
Chauffeur en ligne, Android recommande.

Etapes :

1. Passer en ligne.
2. Mettre l'app en arriere-plan.
3. Attendre une demande de course.
4. Observer notification/retour app.

Resultat attendu :

- Android garde le service actif si foreground service active;
- notification visible;
- offre recue si OS ne tue pas l'app;
- limite iOS/app tuee documentee.

Bloquant si :

- aucune notification alors que l'app est au premier plan ou service actif;
- l'application pretend etre fiable fermee de force.

## Use Case DRV-018 - Notifications push

Objectif :
Verifier que le chauffeur recoit les notifications essentielles.

Prerequis :
FCM configure, token device enregistre.

Etapes :

1. Autoriser les notifications.
2. Passer en ligne.
3. Creer une course proche.
4. Mettre l'application en arriere-plan.

Resultat attendu :

- notification d'offre recue;
- tap sur notification ouvre la course;
- pas de doublons excessifs;
- message utile.

Bloquant si :

- aucune notification d'offre;
- notification ouvre mauvais ecran;
- token device non enregistre.

## Use Case DRV-019 - Urgence pendant course

Objectif :
Verifier que le chauffeur peut signaler une urgence.

Prerequis :
Course active.

Etapes :

1. Ouvrir action urgence/SOS.
2. Confirmer l'action.
3. Observer l'accuse de reception.

Resultat attendu :

- urgence enregistree;
- message de confirmation visible;
- ride ID associe;
- pas de fausse promesse si support humain non disponible.

Bloquant si :

- bouton urgence absent en course;
- aucune confirmation;
- erreur 500.

## Use Case DRV-020 - Fin de journee chauffeur

Objectif :
Verifier que le chauffeur peut sortir proprement du service.

Prerequis :
Chauffeur en ligne, aucune course active.

Etapes :

1. Appuyer sur passer hors ligne.
2. Fermer l'application.
3. Rouvrir l'application.

Resultat attendu :

- statut hors ligne conserve;
- le chauffeur ne recoit plus d'offre;
- reprise claire au prochain lancement.

Bloquant si :

- impossible de passer hors ligne;
- chauffeur recoit encore des courses;
- statut incorrect au redemarrage.

## Test terrain 10 chauffeurs

Scenario recommande :

```text
10 chauffeurs valides autour d'une zone.
3 passagers creent 10 courses courtes.
Chaque chauffeur doit recevoir au moins une offre si eligible.
Chaque passager doit completer au moins une course cash.
Au moins une course doit etre refusee pour tester la reproposition.
Au moins une course doit tester partage de course.
Au moins une course doit tester urgence.
```

Mesures a noter :

- temps entre creation course et reception offre;
- chauffeur qui recoit l'offre;
- distance chauffeur-pickup;
- categorie vehicule;
- comfort level choisi par le passager;
- statut final;
- raison si no_driver_found;
- notification recue ou non;
- difference prix estime / prix final;
- bugs UX observes.

## Sortie de vague 1 chauffeur

La vague 1 chauffeur est acceptable si :

- un chauffeur non valide est bloque proprement;
- un chauffeur valide peut passer en ligne;
- un chauffeur proche recoit une offre;
- acceptation/refus fonctionnent;
- une course cash peut etre terminee;
- notifications et WebSocket fonctionnent au premier plan;
- les limites arriere-plan sont connues et expliquees;
- aucune erreur 500 non documentee sur les use cases critiques.
