# Brief frontend DiddiGo - Support et signalements - 27 octobre 2026

## Objet

Ce guide décrit comment l'application passager et DiddiGo Plus doivent traiter
un SOS, un signalement lié à une course et une demande générale d'aide.

## Répartition des responsabilités

| Besoin | Propriétaire | Rôle de DiddiGo |
| --- | --- | --- |
| SOS immédiat | DiddiGo | Enregistre l'urgence et déclenche les notifications. |
| Signalement sur une course | DiddiSupport | Vérifie le lien avec la course puis transmet la création du dossier à DiddiSupport. |
| Demande générale d'aide | DiddiSupport | Aucun traitement DiddiGo requis. |
| Discussion client-agent | DiddiComms | Transporte les messages du dossier support. |

DiddiFreeID fournit l'identité et le jeton. L'application ne choisit jamais un
`user_id`, un rôle métier ou des participants : le backend les déduit du jeton
et de la course.

## 1. SOS immédiat - disponible dans DiddiGo

Afficher le bouton SOS uniquement dans l'écran d'une course accessible à
l'utilisateur. Après confirmation explicite par l'utilisateur, appeler :

```http
POST /v1/rides/{ride_id}/emergency
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "note": "Je ne me sens pas en securite"
}
```

`note` est facultatif et limité à 500 caractères. Ne pas attendre une
conversation ou une réponse humaine avant d'afficher que l'alerte a été prise
en compte. DiddiGo persiste l'événement et tente les canaux configurés
(WhatsApp, SMS et support interne).

En cas d'erreur réseau, afficher un échec explicite et proposer de réessayer.
Ne jamais prétendre que l'urgence a été envoyée sans réponse serveur positive.

## 2. Signaler un problème sur une course - cible d'intégration

Le bouton **Signaler un problème** doit être visible dans le détail d'une
course, active ou terminée. Son objectif est de créer un dossier support, pas
de déclencher le SOS.

Le flux cible est :

```text
Application
  -> API DiddiGo : vérifie que l'utilisateur appartient à la course
  -> DiddiSupport : crée le ticket
  -> DiddiGo : fournit au besoin un contexte de course masqué
  -> DiddiComms : discussion client-agent
```

Le rôle (`passenger` ou `driver`) est déterminé par DiddiGo. Le frontend envoie
uniquement la catégorie choisie et le message saisi.

### État actuel

La route publique de création de ticket côté DiddiSupport et la route publique
DiddiGo de déclenchement contextuel ne sont pas encore contractuellement
publiées. Le frontend ne doit donc pas inventer ni appeler une route telle que
`POST /v1/rides/{ride_id}/support-reports` avant la publication du contrat
DiddiSupport.

Préparer l'écran et le modèle local avec les champs suivants :

```json
{
  "category": "payment_issue",
  "message": "Le paiement est affiche comme echoue alors que j'ai paye.",
  "attachments": []
}
```

Les valeurs définitives de `category`, les pièces jointes et la réponse
`support_ticket_id` seront fournis par le contrat public DiddiSupport.

## 3. Demande générale d'aide

Depuis le menu **Aide et support**, l'application appellera directement
DiddiSupport avec le jeton DiddiFreeID. Cette demande n'a pas besoin de
`ride_id`, ni d'un appel préalable à DiddiGo.

Quand DiddiSupport publiera son contrat, l'application devra proposer :

- le type de problème ;
- un message ;
- la liste et le statut des dossiers déjà créés ;
- l'ouverture de la conversation DiddiComms associée au dossier.

## 4. Ce que le frontend ne doit jamais faire

- Appeler `GET /internal/v1/support/ride/{ride_id}/context` : cette route est
  réservée au service DiddiSupport.
- Construire lui-même les participants, le rôle métier ou les permissions.
- Copier téléphone, position GPS, données KYC/KYV ou détails fournisseur de
  paiement dans une demande support.
- Utiliser le SOS pour un simple litige de prix ou de paiement.

## 5. Référence technique actuelle

DiddiSupport peut déjà lire un contexte DiddiGo redigé avec :

```http
GET /internal/v1/support/ride/{ride_id}/context
```

Cette API est protégée par un jeton de service DiddiFreeID et le scope
`diddigo:support-context:read`. Elle ne fait pas partie de l'API mobile/web.
Voir aussi le guide d'intégration [DiddiSupport](../integrations/diddisupport.md).

## Checklist frontend

- [ ] Bouton SOS distinct du bouton « Signaler un problème ».
- [ ] Confirmation explicite avant SOS.
- [ ] Erreur réseau SOS visible et action de réessai.
- [ ] Écran de signalement contextuel préparé, mais désactivé tant que le
      contrat public DiddiSupport n'est pas publié.
- [ ] Écran « Aide et support » prévu comme intégration directe DiddiSupport.
- [ ] Aucun appel frontend vers une route `/internal/`.
