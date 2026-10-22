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
| Chauffeur/course | `DRIVER_*`, `WAITING_*`, `MATCHING_*` | éligibilité wallet, attente et dispatch. |
| Push/urgence | `PUSH_*`, `FCM_*`, `EMERGENCY_*` | push, contact support et alertes. |
| Pilotage | `RIDE_SUMMARY_*`, `PILOTAGE_*` | endpoints et cache des rapports internes. |
| Portail documentaire | `DOCS_*` | publication MkDocs dans la stack DiddiGo. |

## Déploiement

Les stacks Compose définissent les valeurs de substitution et les valeurs requises. En Portainer, renseigner les secrets exclusivement dans les variables de stack ou un secret manager : `JWT_SECRET`, mots de passe PostgreSQL, clés/callbacks DiddiPay, secrets de clients DiddiFreeID/DiddiMap/DiddiFiles, et identifiants FCM/SMTP/WhatsApp.

Après tout changement de variable, redéployer la stack ; l'application ne fait pas de hot reload de configuration.

## Contrôle avant déploiement

1. Copier `.env.example` dans un fichier non versionné adapté à l'environnement.
2. Vérifier les URL et audiences des intégrations DiddiFreeID, DiddiMap, DiddiPay et DiddiFiles.
3. Vérifier que les secrets requis ne sont ni vides ni exposés dans les logs.
4. Vérifier `GET /ready` après déploiement.
