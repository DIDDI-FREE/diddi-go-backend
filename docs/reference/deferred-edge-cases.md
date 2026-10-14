# Cas limites et sujets différés

Ce registre empêche les cas rares de surcharger le contrat MVP principal.
Ils ne doivent pas bloquer la documentation ni la livraison des parcours
nominaux, sauf lorsqu'une règle de sécurité minimale est indiquée.

## Paiement et prix

### Trace GPS inutilisable

- La trace tarifaire officielle provient uniquement du téléphone du chauffeur.
- Si la trace ne permet pas de calculer un arrêt anticipé, aucun fallback
  silencieux vers le prix estimé ne doit être appliqué.
- Comportement de sécurité retenu pour une évolution ultérieure : course
  terminée opérationnellement, paiement `review_required`, motif
  `gps_trace_unavailable`, sans paiement, commission ni gain chauffeur avant
  revue support.
- Ce workflow de revue complet est différé. Le contrat MVP doit seulement
  signaler l'écart tant qu'il n'est pas livré.

### Adresse e-mail de paiement absente

- DiddiGo récupère normalement l'adresse e-mail depuis DiddiFreeID.
- Si elle est absente, le backend peut construire
  `<telephone>@diddifree.com` uniquement pour initialiser le paiement de la
  course.
- Cette adresse technique ne devient jamais l'adresse du compte, ne doit pas
  recevoir de communication métier et ne doit pas être persistée comme donnée
  de profil.

### Réseaux Mobile Money différés

- Le MVP accepte `orange`, `wave` et `mtn`.
- `moov` reste hors MVP tant que le schéma typé DiddiPay ne l'accepte pas.
- Un futur wallet DiddiPay/DiddiWallet sera un moyen de paiement distinct. Il
  ne doit pas être présenté comme disponible dans le MVP.

## Arrêt anticipé

### Fin unilatérale pour urgence

- Le parcours nominal exige une demande passager puis une confirmation
  chauffeur dans un délai de deux minutes.
- Un chauffeur peut exceptionnellement terminer seul avec un motif contrôlé :
  `safety_risk`, `passenger_incident`, `vehicle_failure`,
  `medical_emergency` ou `other`.
- `other` exige un commentaire.
- La décision est auditée et le paiement passe en revue support.
- L'automatisation complète de cette revue est différée.

## Fonctionnalités exposées hors MVP

- Les routes d'escales déjà exposées restent documentées mais marquées
  `Hors MVP - ne pas intégrer pour le lancement`.
- Elles ne doivent pas être supprimées ni présentées comme prêtes pour le
  parcours de lancement.

## Temps réel

- Un token WebSocket invalide pendant le handshake produit actuellement un
  rejet HTTP `403` avant connexion.
- Le code de fermeture `4401` reste réservé à une connexion déjà établie.
- La récupération d'offres chauffeur manquées après une longue déconnexion
  devra être renforcée après stabilisation du MVP.

## Écarts MVP qui ne sont pas différés

Les éléments suivants restent des travaux de lancement et ne doivent pas être
classés comme simples cas limites :

- connecteur SMS pour le SOS, en complément de WhatsApp ;
- devis persistant valable quinze minutes avec `quote_id` et `expires_at` ;
- arrêt anticipé au prix réel avec demande passager et confirmation chauffeur ;
- nouvelle tentative Mobile Money après paiement échoué ou expiré ;
- documentation et schémas typés des parcours MVP.
