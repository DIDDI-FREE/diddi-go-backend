# Protocole terrain - Partenaires, chauffeurs et vehicules

Date: 2026-09-08

Ce protocole sert a tester le parcours terrain DiddiGo quand un chauffeur est
lie a un partenaire ou une flotte. Il complete le protocole chauffeur classique.

## Objectif

Verifier le flux reel suivant :

```text
admin cree partenaire
-> admin valide KYC partenaire
-> admin rattache ou cree chauffeur
-> admin cree vehicule partenaire
-> admin valide KYV vehicule
-> chauffeur passe en ligne
-> passager cree une course
-> chauffeur recoit/accepte/termine la course
```

## Roles

- Admin DiddiGo : cree et valide les partenaires, KYC, vehicules et KYV.
- Partenaire : entreprise ou proprietaire de flotte, visible en backoffice.
- Chauffeur affilie : utilise un vehicule partenaire.
- Chauffeur solo : reste hors partenaire et garde son propre vehicule.
- Passager : ne voit pas la notion de partenaire.

## Pre-requis

- API DiddiGo staging deployee avec les routes partenaires.
- Token admin valide.
- Token chauffeur valide.
- Token passager valide.
- Au moins 1 partenaire de test.
- Au moins 1 chauffeur de test avec profil DiddiGo cree.
- DiddiFiles disponible pour produire les `file_id` des documents.
- DiddiMap disponible pour search/routing/pricing.
- FCM/WebSocket actifs pour offres de course.

## Donnees a noter

```text
Date:
Testeur:
Version backend:
Version app:
Partner ID:
Driver Profile ID:
Vehicle ID:
Ride ID:
Telephone chauffeur:
Telephone passager:
Zone:
Resultat:
Erreur/code:
Commentaire:
```

## PART-001 - Creation partenaire

Etapes :

1. Admin cree un partenaire avec `partner_type=fleet_owner` ou `company`.
2. Admin ajoute les documents KYC partenaire.
3. Admin valide le KYC partenaire.

Resultat attendu :

- partenaire cree en `pending_verification`;
- apres validation KYC, partenaire en `active`;
- si document obligatoire manque, erreur `INVALID_PARTNER_KYC_DOCUMENTS`.

## PART-002 - Chauffeur affilie

Etapes :

1. Admin prend un chauffeur existant avec profil DiddiGo.
2. Admin affilie le chauffeur au partenaire.
3. Admin liste les chauffeurs du partenaire.

Resultat attendu :

- chauffeur visible dans la liste du partenaire;
- un chauffeur ne peut pas avoir deux partenaires actifs;
- si deja affilie ailleurs, erreur `DRIVER_ALREADY_AFFILIATED`.

## PART-003 - Creation vehicule partenaire

Etapes :

1. Admin cree un vehicule via `POST /v1/admin/partners/{partner_id}/vehicles`.
2. Admin renseigne `driver_id`, plaque, marque, modele, couleur, categorie et confort.
3. Admin ajoute les documents vehicule et les 5 photos.

Photos obligatoires :

```text
avant
arriere
cote gauche
cote droit
interieur
```

Resultat attendu :

- vehicule cree avec `owner_type=partner`;
- `partner_id` est renseigne;
- `driver_id` est renseigne;
- vehicule assigne au chauffeur;
- statut initial `verification_status=pending_verification`.

## PART-004 - Blocage avant KYV vehicule

Etapes :

1. Chauffeur essaie de passer en ligne avant validation KYV.
2. Observer le message dans l'app.

Resultat attendu :

- backend refuse le passage en ligne;
- code attendu `VEHICLE_NOT_VERIFIED`;
- l'app affiche que le vehicule est en verification.

## PART-005 - File admin KYV vehicule

Etapes :

1. Admin ouvre `GET /v1/admin/vehicles/kyv?status=pending_verification`.
2. Admin ouvre le detail `GET /v1/admin/vehicles/{vehicle_id}/kyv`.
3. Admin verifie documents et photos.

Resultat attendu :

- vehicule visible dans la file;
- detail accessible;
- tous les champs documents et photos sont visibles.

## PART-006 - Validation KYV vehicule

Etapes :

1. Admin approuve le vehicule.
2. Chauffeur essaie de passer en ligne.

Resultat attendu :

- vehicule passe en `active`;
- chauffeur peut passer en ligne sauf autre blocage metier documente;
- si wallet/solde bloque, le code doit etre explicite et different de `VEHICLE_NOT_VERIFIED`.

## PART-007 - Course avec chauffeur affilie

Etapes :

1. Chauffeur affilie passe en ligne pres du pickup.
2. Passager cherche destination.
3. Passager cree une course compatible avec categorie/confort du vehicule.
4. Chauffeur recoit l'offre.
5. Chauffeur accepte.
6. Course passe en route, demarree, puis terminee.

Resultat attendu :

- matching ne bloque pas le chauffeur si partenaire actif;
- offre recue via WebSocket/FCM;
- le passager ne voit pas la notion de partenaire;
- la course se termine normalement.

## PART-008 - Partenaire suspendu

Etapes :

1. Admin suspend le partenaire.
2. Chauffeur affilie essaie de passer en ligne.
3. Passager cree une course proche.

Resultat attendu :

- chauffeur bloque avec `PARTNER_SUSPENDED`;
- chauffeur non eligible au matching;
- si le chauffeur est desaffilie, le blocage partenaire ne s'applique plus.

## Verdict

- Pass : le cas fonctionne sans contournement.
- Fail : comportement attendu non respecte.
- Blocked : dependance externe indisponible.
- Needs Review : techniquement OK mais UX confuse.

Severite :

- P0 : bloque test terrain.
- P1 : bloque parcours partenaire/chauffeur majeur.
- P2 : contournement possible.
- P3 : observation UX ou confort.

## Tests Bruno associes

```text
11-Partner-KYV/01 Create Partner
11-Partner-KYV/02 Approve Partner KYC
11-Partner-KYV/03 Create Partner Vehicle
11-Partner-KYV/04 List Vehicle KYV Queue
11-Partner-KYV/04b Get Vehicle KYV Detail
11-Partner-KYV/05 Approve Vehicle KYV
11-Partner-KYV/06 Go Online After KYV
```
