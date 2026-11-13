# DiddiGo — raccordement DiddiObserve

Le module expose les signaux sans dépendre de la disponibilité du collecteur. Le déploiement central doit fournir les valeurs réelles, sans les committer dans ce dépôt :

```env
SERVICE_VERSION=<immutable-release-or-git-sha>
DIDDI_DEPLOYMENT_ID=<stable-deployment-id>
SERVICE_INSTANCE_ID=<optional-platform-instance-id>
OBSERVABILITY_METRICS_TOKEN=<rotatable-scrape-secret>
OTEL_EXPORTER_OTLP_ENDPOINT=<central-platform-value>
OTEL_EXPORTER_OTLP_HEADERS=<central-platform-secret-reference-or-value>
OTEL_EXPORT_TIMEOUT_SECONDS=5
OTEL_TRACES_SAMPLER_ARG=0.1
OTEL_MAX_QUEUE_SIZE=2048
OTEL_SCHEDULE_DELAY_MS=5000
```

Prometheus doit scraper `http://diddigo:8000/internal/metrics` avec `Authorization: Bearer <OBSERVABILITY_METRICS_TOKEN>` sur le réseau privé. Sans token, l’endpoint est fermé. Les chemins de routes sont des templates bornés et les durées sont en secondes.

Validation locale : schéma des logs, nettoyage, corrélation W3C, endpoint protégé, métriques HTTP/histogrammes, readiness/liveness, heartbeat worker et absence de blocage métier lorsque l’OTLP est absent ou indisponible. Validation centrale restante : réception OTLP, corrélation inter-services/async, Prometheus/Grafana, stockage, rétention, rotation, alertes et runbooks.
