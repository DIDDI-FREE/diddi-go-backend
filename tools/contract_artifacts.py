"""Build HTTP/WS documentation artifacts without changing application behavior."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = "draft.2026-10-28"
METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
UUID_EXAMPLE = "11111111-1111-4111-8111-111111111111"
AT_EXAMPLE = "2026-10-15T10:00:00Z"


def object_schema(properties: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": properties, "required": required or list(properties)}


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")


def websocket_spec() -> dict:
    identifier = {"type": "string", "format": "uuid"}
    timestamp = {"type": "string", "format": "date-time"}
    text = {"type": "string"}
    integer = {"type": "integer"}
    nullable_text = {"type": ["string", "null"]}
    nullable_time = {"type": ["string", "null"], "format": "date-time"}
    point = object_schema({"lat": {"type": "number"}, "lng": {"type": "number"}})
    pickup = object_schema(
        {
            "lat": {"type": ["number", "null"]},
            "lng": {"type": ["number", "null"]},
            "address": nullable_text,
        }
    )
    waiting = object_schema(
        {
            "active": {"type": "boolean"},
            "started_at": nullable_time,
            "duration_seconds": integer,
            "fee": integer,
            "rate_per_minute": {"type": ["integer", "null"]},
        }
    )
    supplement = object_schema(
        {
            "id": identifier,
            "ride_id": identifier,
            "amount": integer,
            "reason": text,
            "type": text,
            "source": text,
            "status": {"type": "string", "enum": ["pending", "accepted", "disputed"]},
            "created_by_user_id": {"type": ["string", "null"], "format": "uuid"},
            "created_at": nullable_time,
            "decided_by_user_id": {"type": ["string", "null"], "format": "uuid"},
            "decided_at": nullable_time,
        }
    )
    event_schemas = {}
    messages = {}
    operations = {}
    channel_messages = {}

    def add(
        name: str,
        event: str,
        action: str,
        properties: dict,
        example: dict,
        description: str,
        roles: str,
        trigger: str,
        recovery: str,
        required: list[str] | None = None,
    ) -> None:
        payload = object_schema(
            {"event": {"type": "string", "const": event}, **properties},
            ["event", *(required if required is not None else properties)],
        )
        event_schemas[name] = payload
        messages[name] = {
            "name": name,
            "title": event,
            "contentType": "application/json",
            "description": description,
            "payload": {"$ref": f"#/components/schemas/{name}"},
            "examples": [{"name": "exemple", "payload": {"event": event, **example}}],
            "x-contract": {
                "roles": roles,
                "trigger": trigger,
                "recovery": recovery,
                "delivery": "Best effort, sans replay, rétention ni accusé de réception métier serveur→client.",
                "ordering": "Pas de séquence globale ; ne pas déduire un ordre métier de at.",
                "errors": "Messages Error ; aucun ACK d'une notification serveur n'est attendu.",
            },
        }
        channel_messages[name] = {"$ref": f"#/components/messages/{name}"}
        operations[name] = {
            "action": action,
            "channel": {"$ref": "#/channels/session"},
            "messages": [{"$ref": f"#/channels/session/messages/{name}"}],
            "summary": description,
        }

    add(
        "RideSubscribe",
        "ride.subscribe",
        "receive",
        {"ride_id": identifier},
        {"ride_id": UUID_EXAMPLE},
        "Abonner cette connexion à une course.",
        "Passager propriétaire, chauffeur affecté ou admin.",
        "Après connexion ou reconnexion.",
        "Réabonner puis GET /v1/rides/{ride_id} ; répéter ajoute au même ensemble de sockets.",
    )
    add(
        "Ping",
        "ping",
        "receive",
        {},
        {},
        "Heartbeat applicatif de la connexion WebSocket.",
        "Toute connexion authentifiee.",
        "Periodiquement, pour detecter une coupure silencieuse.",
        "Attendre pong ; si absent, reconnecter, se reabonner et relire REST.",
    )
    add(
        "DriverLocationPush",
        "driver.location_push",
        "receive",
        {
            "location": point,
            "heading": {"description": "Valeur transmise sans validation ; forme stricte UNKNOWN."},
            "speed_kmh": {"type": ["number", "string", "null"]},
            "ride_id": {"type": ["string", "null"], "format": "uuid"},
        },
        {"location": {"lat": 5.3601, "lng": -4.009}, "heading": 134, "speed_kmh": 0, "ride_id": UUID_EXAMPLE},
        "Publier la position temps réel ; ne remplace pas les lots GPS durables HTTP.",
        "Rôle driver/admin ou profil chauffeur actif ; avec ride_id : affectation ou admin.",
        "Mise à jour GPS du client ; peut arrêter automatiquement une attente si le véhicule bouge.",
        "Envoyer une position récente ; ne pas rejouer une file de positions anciennes ; GET ride pour état métier.",
        required=["location"],
    )
    add(
        "RideStatusChanged",
        "ride.status_changed",
        "send",
        {"ride_id": identifier, "status": text, "at": timestamp},
        {"ride_id": UUID_EXAMPLE, "status": "arrived", "at": AT_EXAMPLE},
        "Notification d'état ; early_stop_requested est un signal non persisté, pas un RideStatus.",
        "Sockets abonnés à la course.",
        "Changement émis par route/service, y compris demande d'arrêt anticipé.",
        "GET /v1/rides/{ride_id} ; un événement ancien ne doit pas écraser un état REST plus récent.",
    )
    add(
        "RideDriverLocation",
        "ride.driver_location",
        "send",
        {"ride_id": identifier, "location": point, "heading": {}, "at": timestamp},
        {"ride_id": UUID_EXAMPLE, "location": {"lat": 5.3601, "lng": -4.009}, "heading": 134, "at": AT_EXAMPLE},
        "Position chauffeur diffusée aux abonnés après contrôle d'accès.",
        "Sockets abonnés à la course.",
        "driver.location_push contenant un ride_id autorisé.",
        "Attendre une position récente ; ne pas présenter la dernière position comme fraîche sans nouvelle émission.",
    )
    add(
        "RideNoDriverFound",
        "ride.no_driver_found",
        "send",
        {"ride_id": identifier},
        {"ride_id": UUID_EXAMPLE},
        "Fin de recherche sans chauffeur.",
        "Sockets abonnés à la course.",
        "Matching sans chauffeur.",
        "GET /v1/rides/{ride_id} ; pas de timestamp ni d'identifiant d'événement.",
    )
    add(
        "RideNewRequest",
        "ride.new_request",
        "send",
        {
            "ride_id": identifier,
            "pickup": pickup,
            "dropoff_address": nullable_text,
            "vehicle_category": text,
            "comfort_level": text,
            "payment_method": text,
            "expires_in_seconds": integer,
        },
        {
            "ride_id": UUID_EXAMPLE,
            "pickup": {"lat": 5.3601, "lng": -4.009, "address": "Point de départ"},
            "dropoff_address": "Destination",
            "vehicle_category": "standard",
            "comfort_level": "standard",
            "payment_method": "cash",
            "expires_in_seconds": 20,
        },
        "Offre de course adressée à un chauffeur ; la durée de l'exemple n'est pas une constante contractuelle.",
        "Toutes les connexions de l'utilisateur chauffeur ciblé, même sans ride.subscribe.",
        "Vague d'offres de matching.",
        "Aucun endpoint de replay d'offres confirmé : UNKNOWN. Une offre ne garantit pas une affectation.",
    )
    add(
        "RideWaitingChanged",
        "ride.waiting_changed",
        "send",
        {"ride_id": identifier, "status": text, "waiting": waiting, "at": timestamp},
        {
            "ride_id": UUID_EXAMPLE,
            "status": "waiting",
            "waiting": {
                "active": True,
                "started_at": AT_EXAMPLE,
                "duration_seconds": 0,
                "fee": 0,
                "rate_per_minute": 100,
            },
            "at": AT_EXAMPLE,
        },
        "État et montants d'attente en course.",
        "Sockets abonnés à la course.",
        "Début/fin d'attente via HTTP ou arrêt automatique sur mouvement.",
        "GET /v1/rides/{ride_id} ; montant serveur faisant foi.",
    )
    add(
        "RideSupplementChanged",
        "ride.supplement_changed",
        "send",
        {"supplement": supplement, "at": timestamp},
        {
            "supplement": {
                "id": "22222222-2222-4222-8222-222222222222",
                "ride_id": UUID_EXAMPLE,
                "amount": 500,
                "reason": "toll",
                "type": "toll",
                "source": "catalog",
                "status": "pending",
                "created_by_user_id": UUID_EXAMPLE,
                "created_at": AT_EXAMPLE,
                "decided_by_user_id": None,
                "decided_at": None,
            },
            "at": AT_EXAMPLE,
        },
        "Proposition/décision de supplément ; ride_id se trouve dans supplement, pas à la racine.",
        "Sockets abonnés à la course.",
        "Création ou décision du supplément via HTTP.",
        "GET /v1/rides/{ride_id}/supplements ; ne pas ajouter un montant deux fois à réception.",
    )
    add(
        "Ack",
        "ack",
        "send",
        {"received_event": text, "ride_id": identifier},
        {"received_event": "ride.subscribe", "ride_id": UUID_EXAMPLE},
        "Accusé du message client ; ride_id présent pour ride.subscribe, absent pour driver.location_push.",
        "Connexion émettrice.",
        "Traitement réussi d'un message connu.",
        "Pas de correlation_id ; ACK ne garantit ni persistance GPS HTTP ni livraison aux autres clients.",
        required=["received_event"],
    )
    add(
        "Pong",
        "pong",
        "send",
        {"at": timestamp},
        {"at": AT_EXAMPLE},
        "Reponse au heartbeat ping. Ce message ne confirme aucun evenement metier manque.",
        "Connexion emettrice.",
        "Reception d'un ping valide.",
        "En cas d'absence, reconnecter puis relire REST ; aucun replay n'est fourni.",
    )
    add(
        "Error",
        "error",
        "send",
        {
            "code": {
                "type": "string",
                "enum": [
                    "MALFORMED_MESSAGE",
                    "FORBIDDEN_ROLE",
                    "INVALID_LOCATION",
                    "INVALID_RIDE_ID",
                    "RIDE_NOT_OWNED_BY_USER",
                    "CACHE_UNAVAILABLE",
                ],
            },
            "retryable": {"type": "boolean"},
        },
        {"code": "CACHE_UNAVAILABLE", "retryable": True},
        "Erreur applicative du socket ; ce format n'est pas l'enveloppe d'erreur HTTP.",
        "Connexion émettrice.",
        "Validation/droit refusé ou exception Redis.",
        "Corriger le message ; CACHE_UNAVAILABLE ferme ensuite le socket en 1013 et demande reconnexion.",
        required=["code"],
    )
    add(
        "Ignored",
        "ignored",
        "send",
        {"received_event": {}},
        {"received_event": "future.event"},
        "Événement inconnu ignoré ; received_event reprend la valeur reçue, éventuellement null.",
        "Connexion émettrice.",
        "Objet JSON avec événement inconnu ou absent.",
        "Ne pas répéter indéfiniment un événement non supporté.",
    )
    return {
        "asyncapi": "3.0.0",
        "info": {
            "title": "DiddiGo WebSocket",
            "version": VERSION,
            "description": "Contrat du serveur local, directions vues depuis DiddiGo. Exemples synthétiques.",
        },
        "defaultContentType": "application/json",
        "servers": {
            "staging": {
                "host": "go-staging.diddifree.com",
                "protocol": "wss",
                "description": "Adresse connue ; parité du build local avec staging non garantie.",
            }
        },
        "channels": {
            "session": {
                "address": "/v1/ws",
                "messages": channel_messages,
                "servers": [{"$ref": "#/servers/staging"}],
                "bindings": {
                    "ws": {
                        "method": "GET",
                        "query": object_schema({"token": {"type": "string"}}),
                        "bindingVersion": "0.1.0",
                    }
                },
                "description": "Access token query obligatoire ; refus avant accept peut devenir HTTP 403.",
            }
        },
        "operations": operations,
        "components": {"messages": messages, "schemas": event_schemas},
        "x-source": [
            "app_base/modules/ride/presentation/websocket.py",
            "app_base/modules/ride/presentation/router.py",
            "app_base/modules/ride/application/services.py",
        ],
        "x-delivery": {
            "replay": False,
            "retention": "N/A — aucun journal de messages WebSocket.",
            "cross-instance-bus": False,
            "global-order": "UNKNOWN",
            "heartbeat": "UNKNOWN",
        },
    }


def http_contract(raw: dict, sources: dict | None = None) -> tuple[dict, list[str]]:
    spec = deepcopy(raw)
    spec["info"]["description"] = (
        "Contrat documentaire local enrichi ; ne certifie pas le déploiement. "
        "UNKNOWN dans x-contract indique une lacune, pas une valeur de protocole. Voir API_CONTRACT.md."
    )
    spec["x-contract-version"] = VERSION
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    schemas["ApiErrorEnvelope"] = object_schema(
        {
            "error": object_schema(
                {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {},
                    "request_id": {"type": "string"},
                },
                ["code", "message", "details"],
            )
        }
    )
    error_response = {
        "description": "Erreur locale : lire error.code ; liste de codes propre à l'opération non exhaustive.",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ApiErrorEnvelope"},
                "examples": {
                    "validation": {
                        "summary": "Exemple synthétique de validation locale",
                        "value": {
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "La requête est invalide.",
                                "details": {
                                    "violations": [{"loc": ["query", "q"], "msg": "Field required", "type": "missing"}]
                                },
                            },
                        },
                    }
                },
            }
        },
    }
    gaps = []
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method not in METHODS:
                continue
            responses = operation.get("responses", {})
            loose = any(
                status.startswith("2")
                and content.get("schema") is not None
                and not any(key in content["schema"] for key in ("$ref", "properties", "items", "oneOf", "anyOf"))
                for status, response in responses.items()
                for content in response.get("content", {}).values()
            )
            contract = {
                "source": (sources or {}).get((method, path), "app.openapi() ; opération " + operation["operationId"]),
                "purpose": operation.get("summary", "UNKNOWN"),
                "roles": "UNKNOWN — voir dépendances de la route ; security ne définit pas les rôles.",
                "state-before-after": "UNKNOWN — vérifier la précondition et la transition de cette opération.",
                "request": "Paramètres et requestBody ci-dessus ; exemple complet UNKNOWN.",
                "response": "UNKNOWN — champs de succès non spécifiés." if loose else "Schémas ci-dessus.",
                "errors": "Catalogue partiel ; codes/details exhaustifs UNKNOWN.",
                "retry": "UNKNOWN — ne pas supposer une idempotence métier.",
                "side-effects": "UNKNOWN — consulter le parcours dans API_CONTRACT.md.",
                "dependency-failure": "Handlers 500/503 locaux ; comportement spécifique et timeout UNKNOWN.",
            }
            if method == "get":
                contract["state-before-after"] = "N/A pour une lecture simple ; effets des retours navigateur UNKNOWN."
                contract["retry"] = "Lecture à renouveler ; consommation des contextes de retour à vérifier."
            if "early-stop" in path:
                contract["roles"] = "Passager propriétaire pour request ; chauffeur affecté/admin pour confirm."
                contract["state-before-after"] = "in_progress ou waiting ; confirm réussie termine en completed."
                contract["retry"] = "request renouvelle 2 minutes ; confirm après succès retourne 409 ; relire REST."
                contract["side-effects"] = "ride.status_changed ; confirm calcule le prix et libère le chauffeur."
                for status in ("403", "404", "409", "503"):
                    failure = deepcopy(error_response)
                    failure["content"]["application/json"].pop("examples", None)
                    responses.setdefault(status, failure)
            if path.endswith("/location-samples"):
                contract["retry"] = (
                    "Même batch_id + même corps : replay ; corps différent : 409 GPS_BATCH_IDEMPOTENCY_CONFLICT."
                )
            if path.endswith("/supplements/{supplement_id}/decision"):
                contract["retry"] = (
                    "Même décision : idempotent ; changement de décision terminale : 409 SUPPLEMENT_ALREADY_DECIDED."
                )
            if path == "/internal/webhooks/diddipay":
                contract["roles"] = "Émetteur possédant le secret HMAC DiddiPay ; pas de JWT utilisateur/S2S."
                contract["request"] = "UNKNOWN — corps non typé ; HMAC corps brut, header event ID = payload.id."
                contract["retry"] = "Déduplication par event ID : 200 sans corps ; traitement normal : 204 sans corps."
                responses["200"] = {"description": "Événement déjà traité ; réponse sans corps."}
            if path in {"/internal/v1/scores/users/{user_id}", "/internal/v1/scores/rides/{ride_id}"}:
                contract["purpose"] = "Projeter les scores DiddiGo normalisés selon diddi.score.v1."
                contract["roles"] = (
                    "DiddiFree Pro S2S uniquement : aud=diddigo, sub=service:diddifreepro, "
                    "X-Client-ID configuré et scope diddigo:scores:read."
                )
                contract["state-before-after"] = "Lecture seule : aucun état métier, score ou matching n'est modifié."
                contract["request"] = "UUID de sujet dans le chemin ; Bearer S2S, X-Client-ID et X-Request-ID."
                contract["response"] = "Schémas ci-dessus conformes à diddi.score.v1."
                contract["errors"] = (
                    "401 token absent/invalide ; 403 client, scope ou subject ; "
                    "404 RIDE_NOT_FOUND pour une course inconnue."
                )
                contract["retry"] = "Lecture sans mutation ; rejouer avec le même request_id est sûr."
                contract["side-effects"] = "Aucun ; PriorityScore et matching ne sont ni lus ni modifiés."
                contract["dependency-failure"] = "503 SERVICE_JWKS_UNAVAILABLE ou DATABASE_UNAVAILABLE."
            if "422" in responses:
                responses["422"] = deepcopy(error_response)
            operation["x-contract"] = contract
            fields = ", ".join(key for key, value in contract.items() if "UNKNOWN" in value)
            gaps.append(f"| `{method.upper()} {path}` | {fields or 'Aucun UNKNOWN détecté'} |")
    return spec, gaps


def update_generated_section(path: Path, name: str, content: str) -> None:
    start = f"<!-- generated:{name}:start -->"
    end = f"<!-- generated:{name}:end -->"
    original = path.read_text(encoding="utf-8")
    if original.count(start) != 1 or original.count(end) != 1:
        raise ValueError(f"Expected exactly one generated block {name} in {path}")
    before, remainder = original.split(start, 1)
    if end not in remainder:
        raise ValueError(f"Generated block {name} has reversed markers in {path}")
    _, after = remainder.split(end, 1)
    path.write_text(before + start + "\n" + content.rstrip() + "\n" + end + after, encoding="utf-8")


def write_artifacts(raw: dict, sources: dict | None = None) -> None:
    spec, gaps = http_contract(raw, sources)
    api_docs = ROOT / "docs/api"
    write_yaml(api_docs / "openapi.yaml", spec)
    write_yaml(api_docs / "asyncapi.yaml", websocket_spec())
    rows = [
        "| Méthode | Chemin | Opération | Réponses documentées |",
        "|---|---|---|---|",
    ]
    operation_count = 0
    for path, item in sorted(spec["paths"].items()):
        for method, operation in item.items():
            if method not in METHODS:
                continue
            operation_count += 1
            summary = operation.get("summary", operation["operationId"]).replace("|", "\\|")
            codes = ", ".join(sorted(operation.get("responses", {})))
            rows.append(f"| {method.upper()} | `{path}` | {summary} | {codes} |")
    inventory = f"{len(spec['paths'])} chemins ; {operation_count} opérations HTTP.\n\n" + "\n".join(rows)
    update_generated_section(api_docs / "API_CONTRACT.md", "http-inventory", inventory)
    table = "| Opération | Champs encore UNKNOWN |\n|---|---|\n" + "\n".join(gaps)
    update_generated_section(api_docs / "open-questions.md", "operation-gaps", table)
