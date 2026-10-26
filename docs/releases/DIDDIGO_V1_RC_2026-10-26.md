# DiddiGo V1 - Release Candidate

**Date :** 26 octobre 2026  
**Statut :** candidate de lancement terrain controle  
**Portee :** Abidjan, applications passager et chauffeur, backoffice et
integrations DiddiFree necessaires au VTC.

Cette note de version decrit la version candidate dans le depot. Elle ne vaut
pas declaration de production : seuls les controles de recette listes ci-dessous
permettent le passage en production limitee.

## Ce qui est livre

### Passager

- Recherche de lieux via DiddiMap, devis persistant et creation de course avec
  `quote_id` encore valide.
- Matching par vagues de chauffeurs eligibles et suivi de course en temps reel.
- Code de demarrage a six chiffres ou QR code.
- Attente avant depart, attente pendant course, client absent et supplements
  proposes par le chauffeur puis acceptes ou contestes par le passager.
- Paiement en especes ou Mobile Money. En cas d'echec Mobile Money, le
  passager revient au choix de paiement pour la meme course terminee.
- Notation mutuelle apres une course terminee, partage de course et alerte SOS.

### Chauffeur et DiddiGo Plus

- Profil chauffeur, KYC, KYV, six photos vehicule, vehicule actif et validation
  administrative avant mise en ligne.
- Reception et acceptation d'offres, navigation vers le passager, arrivee,
  demarrage, positions GPS, attente, supplements, fin de course et encaissement
  cash confirme exclusivement par le chauffeur.
- Wallet, recharges, gains, commission plateforme, retrait et suivi du payout.
- Le retrait est protege par un OTP envoye au numero verifie du profil
  chauffeur. La destination Mobile Money saisie ne recoit pas ce code par
  defaut.

### Systeme et operations

- Integration DiddiMap pour recherche, itineraire, prix estime et traces GPS.
- Integration DiddiPay pour paiement Mobile Money, top-ups et payouts.
- Integration DiddiFiles pour les documents KYC et KYV.
- Integration DiddiComms pour messagerie et appels lies a une course.
- Projection de capacite chauffeur vers DiddiFreeID, endpoints Pilotage,
  observabilite, logs structures et routes de support interne.
- Portail de documentation MkDocs, OpenAPI, AsyncAPI et catalogue d'erreurs.

## Changements inclus dans cette candidate

- `GET /v1/rides/active/current?as_role=passenger|driver` resout le cas d'une
  meme personne avec une course active dans deux roles differents.
- `payment.ready` indique qu'une course terminee a un montant final payable ; il
  ne signifie jamais que le paiement est confirme.
- `GET /v1/rides/config/supplements` expose les montants autorises par le
  serveur. Le supplement `other` exige un `custom_label`.
- Le retrait chauffeur impose une verification OTP transactionnelle liee au
  chauffeur et au beneficiaire choisi.

Les details API sont dans le [contrat HTTP et WebSocket](../api/API_CONTRACT.md)
et le [brief frontend du 23 octobre](../frontend/DIDDIGO_FRONTEND_BRIEF_2026-10-23.md).

## Migrations requises

Avant de deployer cette candidate, appliquer les migrations dans l'ordre normal
Alembic :

```bash
alembic upgrade head
```

La tete attendue est `0a1b2c3d4e5f`. Elle inclut :

| Migration | Effet |
|---|---|
| `f5a6b7c8d9e0` | Stocke le libelle du supplement `other`. |
| `0a1b2c3d4e5f` | Cree les challenges OTP de retrait chauffeur. |

## Configuration de lancement

Les valeurs ne doivent jamais etre stockees dans Git. Elles sont renseignees
dans Portainer ou le gestionnaire de secrets de l'environnement cible.

| Groupe | Variables a verifier |
|---|---|
| Base et cache | `DATABASE_URL`, `REDIS_URL` |
| Identite | `IDENTITY_JWKS_URL`, `IDENTITY_ISSUER`, URLs et credentials S2S requis |
| Cartographie | `DIDDIMAP_BASE_URL`, credentials de service DiddiMap |
| Paiement | `DIDDIPAY_BASE_URL`, credentials S2S, URLs de retour et secret webhook |
| Fichiers | URL DiddiFiles et credentials S2S associes |
| Push | `PUSH_ENABLED`, `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON` |
| SMS et urgence | `SMS_PROVIDER`, credentials fournisseur, sender, `EMERGENCY_SUPPORT_SMS` |
| Retrait OTP | `DRIVER_WITHDRAWAL_OTP_TTL_SECONDS`, `DRIVER_WITHDRAWAL_OTP_RETRY_SECONDS`, `DRIVER_WITHDRAWAL_OTP_MAX_ATTEMPTS` |

Les valeurs de reference et les variables complementaires figurent dans le
fichier `.env.example` du depot et dans la
[reference de configuration](../configuration/CONFIGURATION_REFERENCE.md).

## Go / No-Go staging

Le responsable de release valide ces points avec de vrais comptes avant toute
production limitee :

- [ ] `/health`, `/ready`, `/metrics`, Swagger, OpenAPI et le portail MkDocs repondent.
- [ ] Les migrations atteignent `0a1b2c3d4e5f` sans erreur.
- [ ] Un passager cree une course depuis un devis valide et un chauffeur
  eligible la recoit puis l'accepte.
- [ ] Le parcours arrivee, attente pre-course, code/QR, GPS, fin de course et
  prix final est termine avec deux telephones reels.
- [ ] Un paiement Wave staging revient bien vers DiddiGo ; un echec permet de
  choisir a nouveau Mobile Money ou especes.
- [ ] Une course cash est confirmee une seule fois par le chauffeur et la
  commission/wallet sont coherents.
- [ ] Un retrait OTP envoie le code au numero de profil, refuse un code faux et
  ne cree qu'un seul retrait pour un devis consomme.
- [ ] Une offre chauffeur est recue en application ouverte et par notification
  push lorsque l'application est en arriere-plan.
- [ ] Une alerte SOS est enregistree et les canaux WhatsApp et SMS sont testes
  avec des numeros de recette.
- [ ] Les traces DiddiMap aboutissent a une finalisation sans donnees
  personnelles dans le payload externe.
- [ ] Les erreurs critiques et les identifiants de requete sont exploitables
  dans les logs et les metriques.

Les scenarios detailles sont maintenus dans la
[checklist DiddiGo datee du 19 octobre](../testing/DIDDIGO_TEST_CHECKLIST_2026-10-19.md)
et la [checklist DiddiSupport datee du 20 octobre](../testing/DIDDIGO_DIDDISUPPORT_TEST_CHECKLIST_2026-10-20.md).

## Limites connues et decisions de lancement

- Le WebSocket accelere le temps reel mais ne remplace pas la lecture REST apres
  reconnexion. Les applications relisent la course via
  `GET /v1/rides/{ride_id}`.
- La disponibilite des reseaux Mobile Money est decidee par DiddiPay. Le client
  DiddiGo ne doit afficher que les reseaux confirmes en staging et production.
- Une notification push n'est declaree operationnelle qu'apres test de
  reception sur appareil reel ; la presence des variables FCM ne suffit pas.
- L'incident de paiement est traite par support lorsqu'il n'est pas regle. Les
  routes historiques de dette passager ne sont pas le parcours MVP courant.
- La page web publique d'un lien de partage est une responsabilite frontend ou
  portail ; DiddiGo fournit le token et les donnees publiques autorisees.

## Decision de release

**Production limitee autorisee uniquement si chaque item Go / No-Go est valide
ou fait l'objet d'une derogation datee, approuvee par Produit, Operations et
Direction technique.**
