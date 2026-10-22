# Portail documentaire MkDocs

## But

Le portail MkDocs publie les contrats, guides et changelogs DiddiGo. Il est un
service statique distinct de l'API : aucune cle, variable d'environnement de
l'application ou donnee metier n'est exposee par ce conteneur.

| Environnement | Adresse | Etat attendu |
| --- | --- | --- |
| Local | `http://localhost:18080` | accessible |
| Staging | `https://docs-go-staging.diddifree.com/` | accessible |
| Production | domaine documentaire eventuel | `404` tant que la publication n'est pas approuvee |

## Lancer localement

Depuis la racine du depot :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml up --build
```

Le port local est configurable avec `DOCS_PORT` et vaut `18080` par defaut.
Arreter avec :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml down
```

## Stack Portainer staging

Creer une stack distincte, par exemple `diddi-go-docs-staging`, avec les deux
fichiers Compose dans cet ordre :

```text
docker-compose.docs.yml
docker-compose.docs.portainer.yml
```

Renseigner ces variables dans Portainer :

```ini
DOCS_PUBLIC_ENABLED=true
PORTAINER_PROXY_NETWORK=<nom-du-reseau-externe-de-nginx-proxy-manager>
```

`PORTAINER_PROXY_NETWORK` est le nom exact du reseau Docker deja partage par
Nginx Proxy Manager. Aucun port hote n'est publie par cette stack : le proxy
doit joindre le service `diddigo-docs` sur le port interne `80` via ce reseau.

Dans Nginx Proxy Manager, creer le proxy host staging :

```text
Host: docs-go-staging.diddifree.com
Forward host: diddigo-docs
Forward port: 80
Websockets: non requis
SSL: certificat habituel du proxy
```

## Protection production

L'overlay Portainer utilise `DOCS_PUBLIC_ENABLED=false` par defaut. Dans cet
etat, toutes les routes documentaires retournent `404`; seul `/healthz` reste
interne au reseau Docker pour le healthcheck.

Ne mettre `DOCS_PUBLIC_ENABLED=true` en production qu'apres une decision de
publication explicite. Si aucun proxy host production n'est cree, le domaine
reste egalement introuvable depuis Internet.

## Verification avant publication

```powershell
# Validation du site statique
C:\Users\Vanauld\Envs\diddigo\Scripts\python.exe -m mkdocs build --strict

# Validation de la stack staging (renseigner le reseau reel)
$env:PORTAINER_PROXY_NETWORK = "<reseau-nginx-proxy-manager>"
docker compose -f docker-compose.docs.yml -f docker-compose.docs.portainer.yml config --quiet
```

Apres deploiement staging :

```powershell
curl.exe -I https://docs-go-staging.diddifree.com/
```

La reponse attendue est `200`. Une stack production avec
`DOCS_PUBLIC_ENABLED=false` doit retourner `404` pour `/`.
