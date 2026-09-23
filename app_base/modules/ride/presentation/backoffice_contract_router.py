"""Machine-readable DiddiGo contract for the DiddiFree Backoffice adapter."""

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import require_backoffice_service_token
from app_base.core.service_scopes import OPERATIONS_READ

router = APIRouter(prefix="/internal/backoffice/v1", tags=["internal-backoffice-contract"])
require_manifest_read = require_backoffice_service_token(required_scope=OPERATIONS_READ)


@router.get("/manifest")
async def get_backoffice_command_manifest(
    _claims: dict = Depends(require_manifest_read),
) -> dict:
    return {
        "contract_version": "backoffice.v1",
        "module": "diddigo",
        "actor_header": "X-Backoffice-Actor",
        "legacy_actor_header": "X-User-ID",
        "request_id_header": "X-Request-ID",
        "idempotency_header": "Idempotency-Key",
        "commands": [
            {
                "name": "approve_driver_kyc",
                "permission": "decide",
                "description": "Valider le dossier KYC d'un chauffeur.",
                "method": "POST",
                "path": "/internal/v1/drivers/{driver_id}/kyc/approve",
                "scope": "diddigo:kyc:decide",
                "requires_reason": True,
                "requires_idempotency": True,
                "execution_mode": "interactive",
            },
            {
                "name": "reject_driver_kyc",
                "permission": "decide",
                "description": "Rejeter le dossier KYC d'un chauffeur.",
                "method": "POST",
                "path": "/internal/v1/drivers/{driver_id}/kyc/reject",
                "scope": "diddigo:kyc:decide",
                "requires_reason": True,
                "requires_idempotency": True,
                "execution_mode": "interactive",
            },
            {
                "name": "provision_driver",
                "permission": "create",
                "description": "Creer le profil metier chauffeur pour une identite DiddiFreeID existante.",
                "method": "POST",
                "path": "/internal/v1/drivers/provision",
                "scope": "diddigo:drivers:write",
                "requires_reason": False,
                "requires_idempotency": True,
                "execution_mode": "interactive",
            },
        ],
        "queries": [
            {
                "name": "list_driver_kyc",
                "method": "GET",
                "path": "/internal/v1/drivers/kyc",
                "scope": "diddigo:kyc:read",
            },
            {
                "name": "get_driver_kyc",
                "method": "GET",
                "path": "/internal/v1/drivers/{driver_id}/kyc",
                "scope": "diddigo:kyc:read",
            },
        ],
    }
