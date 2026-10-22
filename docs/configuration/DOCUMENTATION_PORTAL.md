# Portail documentaire MkDocs

## But

Le portail MkDocs publie les contrats, guides et changelogs DiddiGo. Il est un
service statique distinct de l'API : aucune cle, variable d'environnement de
l'application ou donnee metier n'est exposee par ce conteneur.

| Environnement | Adresse | Etat attendu |
| --- | --- | --- |
| Local | `http://localhost:18081` | accessible |
| Staging | `https://docs-go-staging.diddifree.com/` | accessible |
| Production | domaine documentaire eventuel | `404` tant que la publication n'est pas approuvee |

## Lancer localement

Depuis la racine du depot :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml up --build
```

Le port local est configurable avec `DOCS_PORT` et vaut `18081` par defaut.
Arreter avec :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml down
```

## Stack DiddiGo Portainer staging

Le service `docs` fait partie de `docker-compose.portainer.yml`, au meme titre
que `app`, `db` et `redis`. Il est donc deploye depuis la meme branche Git et
la meme stack DiddiGo que le backend.

Renseigner cette variable dans la stack DiddiGo staging :

```ini
DOCS_PUBLIC_ENABLED=true
DOCS_PORT=18081
```

`DOCS_PORT` est un port hote dedie. Choisir une autre valeur libre si `18081`
est deja utilise. Le service API conserve son propre `BACKEND_PORT`.

Dans Nginx Proxy Manager, creer le proxy host staging :

```text
Host: docs-go-staging.diddifree.com
Forward host: meme hote que go-staging.diddifree.com
Forward port: 18081
Websockets: non requis
SSL: certificat habituel du proxy
```

## Protection production

La stack DiddiGo Portainer utilise `DOCS_PUBLIC_ENABLED=false` par defaut. Dans
cet etat, toutes les routes documentaires retournent `404`; seul `/healthz`
reste disponible pour le healthcheck du conteneur.

Ne mettre `DOCS_PUBLIC_ENABLED=true` en production qu'apres une decision de
publication explicite. Si aucun proxy host production n'est cree, le domaine
reste egalement introuvable depuis Internet.

## Verification avant publication

```powershell
# Validation du site statique
C:\Users\Vanauld\Envs\diddigo\Scripts\python.exe -m mkdocs build --strict

# Validation de la stack staging
$env:POSTGRES_PASSWORD = "test-only"
$env:JWT_SECRET = "test-only-32-character-secret-value"
$env:RIDE_START_CODE_SECRET = "test-only-start-code-secret"
docker compose -f docker-compose.portainer.yml config --quiet
```

Apres deploiement staging :

```powershell
curl.exe -I https://docs-go-staging.diddifree.com/
```

La reponse attendue est `200`. Une stack production avec
`DOCS_PUBLIC_ENABLED=false` doit retourner `404` pour `/`.
