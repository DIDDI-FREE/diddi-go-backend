# Questions ouvertes du contrat HTTP et WebSocket

Version : draft.2026-10-15. Décisions et questions maintenues à la main ; seul le bloc des lacunes par opération est généré.

## Questions transversales

| ID | Statut | Question / impact |
|---|---|---|
| Q01 | UNKNOWN | Quel build est servi en staging ? Le 14 octobre à 18:38 UTC : 136 opérations, contre 138 locales. |
| Q02 | UNKNOWN | Quels champs, types, nullabilités et exemples décrivent les réponses HTTP encore ouvertes ? |
| Q03 | UNKNOWN | Quels codes métier et détails exhaustifs s'appliquent à chaque opération et dépendance ? |
| Q04 | UNKNOWN | Quelle matrice exacte rôle/ownership/scope/audience/subject s'applique à chaque opération ? |
| Q05 | DÉCIDÉ PARTIELLEMENT — À VÉRIFIER | Même clé et même demande : retrouver le résultat initial sans doubler l'action ; même clé et détails différents : rejet. Portée, rétention et réponse pendant un traitement encore en cours : UNKNOWN. |
| Q06 | UNKNOWN | Quel corps complet, versionnement, ordre et politique de redélivrance pour DiddiPay ? |
| Q07 | DÉCIDÉ — À VÉRIFIER | Changer le bénéficiaire ou son numéro exige un nouveau devis de retrait ; le même devis ne doit pas permettre cette substitution. |
| Q08 | DÉCIDÉ — À VÉRIFIER | Après reconnexion, récupérer et afficher les offres encore valides pour ce chauffeur ; ne pas réafficher une offre expirée ou devenue indisponible. Mécanisme de récupération non confirmé. |
| Q09 | DÉCIDÉ PARTIELLEMENT — À VÉRIFIER | À expiration de l'accès, renouveler automatiquement via le refresh token et rétablir la connexion sans nouvelle saisie tant que le refresh reste valide ; aucune grâce pour le jeton d'accès expiré. Heartbeat, limites et protocole exact : UNKNOWN. |
| Q10 | DÉCIDÉ — CAS LIMITES À TRAITER | Retenir WebSocket comme signal de changement et relire l'état courant par HTTP ; aucun compteur de révision par course dans le périmètre retenu. Ce choix remplace le tri par heure d'émission comme mécanisme principal de synchronisation. Les cas limites et limites de garantie sont consignés dans API_CONTRACT.md, section Synchronisation retenue. |
| Q11 | UNKNOWN | Quelles transitions et erreurs exhaustives pour les états autres que RideStatus ? Voir les états dans API_CONTRACT.md. |
| Q12 | UNKNOWN | Quels purposes DiddiFiles manquants débloquent les pièces KYC/KYV concernées ? |
| Q13 | DÉCIDÉ — APPLICATION PRODUCTION DIFFÉRÉE | Maintenir les anciennes versions pendant 45 jours, puis exiger la mise à jour ; démarrer lorsque le remplacement est disponible sur Android et iOS avec notification de mise à jour. L'application de cette politique relève du déploiement production, hors du périmètre backend/staging actuel. Politique de compatibilité des changements de sécurité explicitement différée ; aucune garantie ni exception adoptée. |
| Q14 | DÉCIDÉ PARTIELLEMENT — À VÉRIFIER | Rejeter les coordonnées invalides ; si seules vitesse/direction optionnelles sont invalides, conserver les coordonnées valides, écarter ces mesures sans les corriger artificiellement et signaler l'ensemble de la mise à jour comme dégradé. Informer le client sans déconnecter un chauffeur autrement authentifié. Schéma du signalement, bornes et traitement du JSON malformé : UNKNOWN. |
| Q15 | UNKNOWN | Quand distinguer early_stop_requested des notifications de statuts persistés ? |
| Q16 | UNKNOWN | Quelles contraintes conditionnelles encoder, dont réseau requis pour mobile_money ? |

Les exemples sont synthétiques. Aucun DÉFAUT PROPOSÉ n'est adopté comme comportement serveur dans ce contrat.

Les décisions Q05, Q07, Q08, Q09, Q10, Q13 et Q14 ont été recueillies dans la conversation ; les interprétations et propositions sont indiquées explicitement. Elles définissent le comportement cible, pas une preuve de disponibilité dans le code ou en staging. L'audit technique doit confirmer les mécanismes, préciser les schémas et identifier les changements nécessaires ; aucun endpoint, code d'erreur ou délai supplémentaire n'est inventé.



## Écarts MVP et sujets différés

### Bloquant

- **SOS SMS :** WhatsApp est disponible ; le connecteur SMS annoncé par le MVP reste à activer et valider.

### Différé après MVP

- Arrêt anticipé unilatéral d'urgence avec revue support.
- Paiement en revue manuelle lorsque la trace GPS est inutilisable.
- Réseau Moov Money, tant que le contrat DiddiPay typé ne l'accepte pas.
- DiddiWallet comme moyen de paiement passager.
- Activation produit des escales déjà exposées techniquement.

## Lacunes par opération

Les champs détaillés sont dans x-contract de openapi.yaml. Une correction du code ou du générateur actualise le bloc suivant ; les décisions ci-dessus sont préservées.

<!-- generated:operation-gaps:start -->
| Opération | Champs encore UNKNOWN |
|---|---|
| `POST /v1/auth/register` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/auth/otp/request` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/auth/otp/verify` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/auth/refresh` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/auth/me` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/devices/register` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/devices/unregister` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/logs/rides/{ride_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/admin/logs/drivers/{driver_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/me/capabilities` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/me/scores` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /v1/me/emergency-contact` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `PUT /v1/me/emergency-contact` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `DELETE /v1/me/emergency-contact` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/places/search` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /v1/rides/pricing/estimate` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/rides` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/accept` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/decline` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/rides/shared/{token}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/rides/{ride_id}/score` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /v1/rides/{ride_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `PATCH /v1/rides/{ride_id}/status` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/waiting/start` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/early-stop/request` | request, errors, dependency-failure |
| `POST /v1/rides/{ride_id}/early-stop/confirm` | request, errors, dependency-failure |
| `POST /v1/rides/{ride_id}/arrive` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/start` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/no-show` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/waiting/stop` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/stops` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/supplements` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/rides/{ride_id}/supplements` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/supplements/{supplement_id}/decision` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/cancel` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/rating` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/location-samples` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/share-link` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/rides/{ride_id}/emergency` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/ride-summary` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/pilotage/daily-summary` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/pilotage/finance-summary` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /internal/pilotage/breakdown` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/pilotage/health-summary` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/v1/comms/tasks/{task_type}/{task_id}` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /internal/v1/support/ride/{ride_id}/context` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /internal/v1/drivers/provision` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `PATCH /internal/v1/drivers/{driver_id}/profile-photo` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/drivers/kyc` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/v1/drivers/{driver_id}/kyc` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/v1/drivers/vehicles/kyv` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /internal/v1/drivers/vehicles/{vehicle_id}/kyv` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /internal/v1/drivers/{driver_id}/kyc/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/drivers/{driver_id}/kyc/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/drivers/vehicles/{vehicle_id}/kyv/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/drivers/vehicles/{vehicle_id}/kyv/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/dispatch/config` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `PUT /internal/v1/admin/dispatch/config` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/dispatch/priority-rules` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /internal/v1/admin/dispatch/drivers/{driver_id}/priority` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /internal/v1/admin/dispatch/priority-boosts` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/partners` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/partners/{partner_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `PATCH /internal/v1/admin/partners/{partner_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/partners/{partner_id}/members` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/members` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /internal/v1/admin/partners/{partner_id}/drivers` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/drivers` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/activate` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `PATCH /internal/v1/admin/partners/{partner_id}/kyc` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/kyc/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/kyc/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/suspend` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `DELETE /internal/v1/admin/partners/{partner_id}/members/{member_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `DELETE /internal/v1/admin/partners/{partner_id}/drivers/{driver_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/vehicles` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/assign` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /internal/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/unassign` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/profile` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/kyc/resubmit` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/vehicle` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `PATCH /v1/drivers/me/profile-photo` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `PUT /v1/drivers/me/vehicle` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/vehicles/{vehicle_id}/kyv/resubmit` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/drivers/me` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /v1/drivers/kyc` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/drivers/{driver_id}/kyc` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/drivers/{driver_id}/kyc/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/{driver_id}/kyc/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/vehicles/{vehicle_id}/kyv/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/vehicles/{vehicle_id}/kyv/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/online` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/offline` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/vehicles/kyv` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/admin/vehicles/{vehicle_id}/kyv` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/payments/{ride_id}/prepare` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/payments/{ride_id}/confirm-cash` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/payments/{ride_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/passenger/debts` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /v1/passenger/debts/{debt_id}/mobile-money/prepare` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `POST /v1/passenger/debts/{debt_id}/cash-request` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `POST /v1/passenger/debts/{debt_id}/confirm-cash` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `GET /v1/drivers/me/wallet` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/drivers/me/wallet/ledger` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/drivers/me/wallet/topups` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/drivers/me/wallet/topups/{topup_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/drivers/me/wallet/withdrawals/quote` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `POST /v1/drivers/me/wallet/withdrawals` | roles, state-before-after, request, errors, retry, side-effects, dependency-failure |
| `GET /v1/drivers/me/wallet/withdrawals` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/drivers/me/wallet/withdrawals/{withdrawal_id}` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `GET /v1/admin/drivers/{driver_id}/wallet` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/admin/drivers/{driver_id}/wallet/ledger` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/admin/drivers/{driver_id}/wallet/withdrawals` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `POST /v1/admin/payments/reconcile` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/payments/rides/{ride_id}/reconcile` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/payments/topups/{topup_id}/reconcile` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/payments/withdrawals/{withdrawal_id}/reconcile` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/payments/withdrawals/{withdrawal_id}` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /v1/admin/partners` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/partners` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/admin/partners/{partner_id}` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `PATCH /v1/admin/partners/{partner_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/activate` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `PATCH /v1/admin/partners/{partner_id}/kyc` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/kyc/approve` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/kyc/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/suspend` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/reject` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/members` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/partners/{partner_id}/members` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `DELETE /v1/admin/partners/{partner_id}/members/{member_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/drivers` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/admin/partners/{partner_id}/drivers` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `DELETE /v1/admin/partners/{partner_id}/drivers/{driver_id}` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/assign` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/vehicles` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `POST /v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/unassign` | roles, state-before-after, request, response, errors, retry, side-effects, dependency-failure |
| `GET /v1/partners/me` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /v1/ws` | roles, state-before-after, request, errors, side-effects, dependency-failure |
| `POST /internal/webhooks/diddipay` | state-before-after, request, errors, side-effects, dependency-failure |
| `GET /wallet/return` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /payments/return` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /health` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
| `GET /ready` | roles, state-before-after, request, response, errors, side-effects, dependency-failure |
<!-- generated:operation-gaps:end -->
