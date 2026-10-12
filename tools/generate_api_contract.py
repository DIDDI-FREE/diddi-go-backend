"""Generate the published DiddiGo HTTP contract from FastAPI's OpenAPI schema.

Run with the repository virtual environment:
    .venv\\Scripts\\python.exe tools\\generate_api_contract.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DOCS = ROOT / "docs" / "api"
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_base.main import app  # noqa: E402  # Repository root is inserted just above for direct script execution.


def response_codes(operation: dict[str, object]) -> str:
    responses = operation.get("responses", {})
    if not isinstance(responses, dict):
        return ""
    return ", ".join(sorted(responses, key=lambda code: (not str(code).isdigit(), str(code))))


def render_markdown(schema: dict[str, object]) -> str:
    paths = schema["paths"]
    assert isinstance(paths, dict)
    tags = sorted(
        {
            tag
            for item in paths.values()
            if isinstance(item, dict)
            for operation in item.values()
            if isinstance(operation, dict)
            for tag in operation.get("tags", ["sans-tag"])
        }
    )
    operation_count = sum(
        1
        for item in paths.values()
        if isinstance(item, dict)
        for method in HTTP_METHODS
        if isinstance(item.get(method), dict)
    )
    version = schema.get("info", {}).get("version", "n/a")
    lines = [
        "# Contrat HTTP DiddiGo",
        "",
        "**Source :** `app_base.main:app.openapi()`",
        f"**Généré le :** {date.today().isoformat()}",
        f"**Version applicative :** {version}",
        "",
        "La spécification complète, incluant les schémas de requête et de réponse, est dans "
        "[`openapi.json`](openapi.json). Ce fichier est généré depuis le code ; ne pas le modifier manuellement.",
        "Le temps réel est décrit séparément dans le "
        "[`contrat WebSocket`](../realtime/WEBSOCKET_CONTRACT.md), car OpenAPI ne modélise pas ses messages.",
        "",
        "## Surface",
        "",
        f"- **{len(paths)} chemins**",
        f"- **{operation_count} opérations HTTP**",
        "",
        "## Règles comportementales frontend",
        "",
        "### Démarrage sécurisé d'une course",
        "",
        "- `POST /v1/rides/{ride_id}/start` accepte un code à six chiffres.",
        "- Un code invalide répond `422 INVALID_RIDE_START_CODE` avec `details.attempts` et "
        "`details.maximum_attempts`.",
        "- À la cinquième tentative invalide par défaut, la route répond "
        "`423 RIDE_START_CODE_BLOCKED`. Le blocage est persistant.",
        "",
        "### Reprise d'un paiement numérique",
        "",
        "- `POST /v1/payments/{ride_id}/prepare` réutilise une intention non terminale.",
        "- Si l'intention précédente est `failed`, `cancelled` ou expirée, le même appel crée une "
        "nouvelle intention et retourne ses nouveaux `payment_intent_id` et `next_action`.",
        "- `GET /v1/payments/{ride_id}` reste la source de vérité après retour navigateur.",
        "",
        "### Retrait chauffeur Mobile Money",
        "",
        "- `POST /v1/drivers/me/wallet/withdrawals` exige `quote_id`, "
        "`beneficiary_reference` et `beneficiary_destination`.",
        "- `beneficiary_reference` est une référence métier opaque et stable ; elle ne remplace pas "
        "la destination de paiement.",
        "- `beneficiary_destination.type` vaut `mobile_money`, `phone` est au format E.164 et "
        "`network` identifie le réseau demandé.",
        "- Le frontend ne choisit pas le processeur de paiement. DiddiPay valide la disponibilité "
        "du réseau et exécute le payout.",
        "",
        "### Alerte SOS",
        "",
        "- `POST /v1/rides/{ride_id}/emergency` persiste l'alerte avant les notifications externes.",
        "- La réponse contient `event_id`, `sequence`, `requested_at` et `notifications[]`.",
        "- Chaque notification expose `target`, `channel`, `status` et éventuellement `reason`.",
        "- La limitation répond `429 EMERGENCY_RATE_LIMITED` avec "
        "`details.retry_after_seconds`.",
        "",
    ]
    for tag in tags:
        operations: list[tuple[str, str, str, str, str]] = []
        for path, item in sorted(paths.items()):
            if not isinstance(item, dict):
                continue
            for method in HTTP_METHODS:
                operation = item.get(method)
                if not isinstance(operation, dict) or tag not in operation.get("tags", ["sans-tag"]):
                    continue
                summary = str(operation.get("summary") or operation.get("operationId") or "").replace("|", "\\|")
                security = "oui" if operation.get("security") else "non/documenté"
                operations.append((method.upper(), path, summary, response_codes(operation), security))
        if not operations:
            continue
        lines.extend(
            [
                f"## {tag}",
                "",
                "| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |",
                "|---|---|---|---|---|",
            ]
        )
        lines.extend(
            f"| {method} | `{path}` | {summary} | {codes} | {security} |"
            for method, path, summary, codes, security in operations
        )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    API_DOCS.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    (API_DOCS / "openapi.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (API_DOCS / "HTTP_API_CONTRACT.md").write_text(render_markdown(schema), encoding="utf-8")


if __name__ == "__main__":
    main()
