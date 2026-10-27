# Référence de configuration

**Sources :** `app_base/core/settings.py`, [`.env.example`](https://github.com/DIDDI-FREE/diddi-go-backend/blob/stage/.env.example), `docker-compose*.yml`.

`.env.example` est le modèle de configuration local. `Settings` charge les variables d'environnement avant le fichier `.env`. Les valeurs sensibles ne doivent jamais être ajoutées à cette documentation, au dépôt ou à un client mobile/web.

## Groupes de variables

| Groupe | Préfixes / variables | Finalité |
|---|---|---|
| Runtime | `APP_*`, `CORS_*`, `LOG_*` | nom, environnement, CORS et logs. |
| Données | `DATABASE_URL`, `REDIS_URL` | PostgreSQL/PostGIS et Redis. |
| Auth locale | `JWT_*`, `OTP_*` | jetons locaux et OTP. |
| DiddiMap | `DIDDIMAP_*` | géocodage, routage et traces. |
| DiddiFreeID | `IDENTITY_*`, `CAPABILITY_PROJECTION_*` | JWT, profils et projection des capacités. |
| DiddiFiles | `DIDDIFILES_*` | fichiers KYC/KYV. |
| DiddiPay | `DIDDIPAY_*`, `DIDDIGO_*`, `PAYMENT_RECONCILIATION_*` | paiement, callbacks, retours et réconciliation. |
| Chauffeur/course | `DRIVER_*`, `WAITING_*`, `MATCHING_*` | éligibilité wallet, attente, dispatch et OTP de retrait. |
| Push/urgence | `PUSH_*`, `FCM_*`, `EMERGENCY_*` | push, contact support et alertes. |
| Pilotage | `RIDE_SUMMARY_*`, `PILOTAGE_*` | endpoints et cache des rapports internes. |
| Portail documentaire | `DOCS_*` | publication MkDocs dans la stack DiddiGo. |

## Déploiement

Les stacks Compose définissent les valeurs de substitution et les valeurs requises. En Portainer, renseigner les secrets exclusivement dans les variables de stack ou un secret manager : `JWT_SECRET`, mots de passe PostgreSQL, clés/callbacks DiddiPay, secrets de clients DiddiFreeID/DiddiMap/DiddiFiles, et identifiants FCM/SMTP/WhatsApp.

Après tout changement de variable, redéployer la stack ; l'application ne fait pas de hot reload de configuration.

## OTP de retrait chauffeur

| Variable | Valeur par défaut | Règle |
|---|---:|---|
| `DRIVER_WITHDRAWAL_OTP_TTL_SECONDS` | `300` | Durée de validité du code de retrait. |
| `DRIVER_WITHDRAWAL_OTP_RETRY_SECONDS` | `60` | Délai minimal avant un nouveau code pour la même demande. |
| `DRIVER_WITHDRAWAL_OTP_MAX_ATTEMPTS` | `5` | Nombre maximal de codes erronés avant verrouillage du challenge. |
| `WITHDRAWAL_OTP_LOG_CODE_FOR_TESTS` | `false` | Affiche le code OTP dans les logs uniquement en `development`, `test` ou `staging`. Ignoré en production. |

Le code est envoyé au téléphone vérifié du profil chauffeur. Il ne doit jamais
être envoyé automatiquement à la destination de retrait choisie.

Chaque demande produit un événement JSON `withdrawal_otp.delivery_accepted`
avec l'identifiant de vérification, le fournisseur, son statut, son identifiant
de message et un téléphone masqué. L'événement `withdrawal_otp.delivery_failed`
indique un échec d'envoi. Ni le code ni le numéro complet ne sont enregistrés
par défaut.

## Contrôle avant déploiement

1. Copier `.env.example` dans un fichier non versionné adapté à l'environnement.
2. Vérifier les URL et audiences des intégrations DiddiFreeID, DiddiMap, DiddiPay et DiddiFiles.
3. Vérifier que les secrets requis ne sont ni vides ni exposés dans les logs.
4. Vérifier `GET /ready` après déploiement.
