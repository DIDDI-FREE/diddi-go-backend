# Identite unique et capacites metier

Date: 2026-09-12
Statut: regle d'architecture partagee
Perimetre: modules DiddiFree avec une partie consommateur et une partie metier

## Principe directeur

Une personne doit avoir une seule identite DiddiFreeID.

Les usages metier sont des profils ou capacites actives dans les modules
concernes, pas des comptes separes.

```text
Une personne = un user_id DiddiFreeID
Un service = un profil/capacite metier lie a ce user_id
```

Exemples:

```text
DiddiFreeID user_id
  -> DiddiGo passager
  -> DiddiGo chauffeur
  -> DiddiSend expediteur / destinataire
  -> DiddiSend livreur
  -> DiddiPay utilisateur
  -> partenaire, operateur ou membre de flotte selon module
```

## Regle generale partagee

Pour tous les modules qui ont a la fois une partie consommateur et une partie
professionnelle/metier:

- ne jamais creer deux comptes pour la meme personne;
- utiliser `user_id` DiddiFreeID comme identifiant transversal;
- garder l'authentification, le statut global et la suspension globale dans
  DiddiFreeID;
- garder les profils, statuts, validations et regles metier dans le module
  concerne;
- ne pas mettre les capacites metier fines dans le JWT global;
- exposer l'etat metier via les APIs du module;
- laisser chaque module appliquer ses propres regles d'eligibilite.

## Separation des responsabilites

### DiddiFreeID

DiddiFreeID porte:

- authentification;
- OTP;
- JWT;
- profil global utilisateur;
- statut global du compte;
- suspension globale;
- roles globaux simples, par exemple `user` et `admin`.

DiddiFreeID ne doit pas porter les etats operationnels fins comme:

- chauffeur DiddiGo valide;
- livreur DiddiSend valide;
- vehicule DiddiGo actif;
- disponibilite chauffeur;
- disponibilite livreur;
- statut KYC/KYV local;
- rattachement flotte/partenaire local.

### Modules metier

Chaque module porte ses propres profils metier.

DiddiGo porte par exemple:

- profil chauffeur;
- KYC chauffeur;
- KYV vehicule;
- disponibilite chauffeur;
- rattachement partenaire/flotte DiddiGo;
- courses;
- gains, commissions et wallet chauffeur DiddiGo.

DiddiSend portera par exemple:

- profil livreur;
- KYC/KYV livraison;
- disponibilite livreur;
- rattachement partenaire/flotte DiddiSend;
- livraisons;
- preuves, litiges et gains livreur.

DiddiPay porte les paiements, wallets et statuts financiers selon son propre
contrat.

## Token et roles

Le JWT DiddiFreeID doit rester simple.

Exemple:

```json
{
  "sub": "user-id",
  "role": "user",
  "status": "active"
}
```

La presence d'un profil chauffeur ou livreur ne doit pas exiger:

```text
role=driver
role=courier
```

Ces capacites sont locales aux modules.

Un `admin` global peut appeler les routes admin des modules si la politique du
module l'autorise.

## Capacites exposees par les modules

Chaque module doit pouvoir expliquer au frontend ce que l'utilisateur peut faire
dans ce module.

Format recommande:

```json
{
  "module": "diddigo",
  "user_id": "identity-user-id",
  "consumer_enabled": true,
  "professional_profile": {
    "exists": true,
    "type": "driver",
    "status": "active",
    "verification_status": "approved",
    "can_go_online": true,
    "blocking_reasons": []
  }
}
```

Pour DiddiSend, le meme principe s'applique avec `type=delivery_driver` ou
`courier` selon le vocabulaire retenu.

## Regle pour les frontends

Les frontends ne doivent pas deduire une capacite metier uniquement depuis le
role du token.

Ils doivent:

- se connecter via DiddiFreeID;
- appeler le module concerne avec le bearer token;
- lire l'etat metier retourne par le module;
- afficher les parcours disponibles, en attente ou bloques selon cet etat.

Exemple:

```text
role user + driver_profile absent      -> proposer onboarding chauffeur
role user + driver_profile pending     -> afficher dossier en verification
role user + driver_profile active      -> afficher mode chauffeur
role user + courier_profile active     -> afficher mode livreur
role admin                             -> afficher outils admin autorises
```

## DiddiFree Pro

`DiddiFree Pro` est une experience commune possible pour les operateurs terrain.

Elle peut afficher:

- courses DiddiGo;
- livraisons DiddiSend;
- disponibilite;
- gains;
- documents;
- vehicules;
- services actives ou en attente.

Cette experience ne signifie pas que DiddiGo et DiddiSend doivent fusionner.

Les moteurs metier restent separes:

- DiddiGo garde les regles de transport de personnes;
- DiddiSend garde les regles de livraison;
- DiddiPay garde les regles de paiement;
- DiddiFiles garde les fichiers;
- DiddiFreeID garde l'identite.

## Roadmap d'adoption

### Phase 1 - Regle d'architecture

Objectif: aligner les equipes.

Livrables:

- documenter cette regle;
- interdire les doubles comptes passager/chauffeur ou client/livreur;
- rappeler que `user_id` DiddiFreeID est la cle de liaison;
- clarifier que les roles metier ne sont pas des roles globaux du token.

### Phase 2 - Capacites DiddiGo explicites

Objectif: rendre l'etat chauffeur lisible sans logique cachee cote frontend.

Livrables DiddiGo:

- endpoint ou payload clair de capacites DiddiGo;
- documentation frontend;
- tests Bruno;
- codes d'erreur coherents pour les blocages.

### Phase 3 - Alignement DiddiSend

Objectif: appliquer le meme modele a DiddiSend.

Livrables attendus cote DiddiSend:

- profil livreur lie au meme `user_id`;
- endpoint de capacites DiddiSend;
- statuts livreur explicites;
- regles KYC/KYV livraison separees de DiddiGo.

### Phase 4 - Aggregation DiddiFree Pro

Objectif: afficher une experience pro commune.

Options:

- frontend appelle chaque module directement;
- DiddiFreeID expose seulement des flags legers;
- futur service `DiddiPro` agrege les capacites si le besoin devient fort.

Decision actuelle:

```text
Ne pas creer DiddiPro maintenant.
Ne pas fusionner DiddiGo et DiddiSend maintenant.
Standardiser les capacites par module d'abord.
```

## Regle anti-duplication

Si une information est globale a la personne, elle appartient a DiddiFreeID.

Si une information depend d'un metier, d'une regle operationnelle ou d'une
validation terrain, elle appartient au module metier.

Exemples:

| Information | Proprietaire |
|---|---|
| Nom public global | DiddiFreeID |
| Avatar global | DiddiFreeID / DiddiFiles |
| Telephone de connexion | DiddiFreeID |
| Suspension globale | DiddiFreeID |
| Profil chauffeur | DiddiGo |
| Statut KYC chauffeur | DiddiGo |
| Vehicule transport passagers | DiddiGo |
| Profil livreur | DiddiSend |
| Vehicule livraison | DiddiSend |
| Fichier brut | DiddiFiles |
| Paiement / wallet | DiddiPay |

## Consequence pour DiddiGo

DiddiGo est deja aligne avec cette strategie si:

- le `driver_profile` reste lie a `user_id`;
- le JWT n'a pas besoin de `role=driver`;
- un passager peut devenir chauffeur avec le meme compte;
- l'admin valide le profil chauffeur cote DiddiGo;
- les partenaires/flottes restent des concepts locaux DiddiGo tant qu'un service
  transversal n'est pas cree.

Le prochain ajustement recommande est d'ajouter un endpoint explicite de
capacites DiddiGo, pour eviter que le frontend assemble lui-meme l'etat a partir
de plusieurs routes.

