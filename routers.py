from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from engine.paper_trading_controller import PaperControllerConfig, PaperTradingController

router = APIRouter()


def get_controller() -> PaperTradingController:
    # Gerçek PaperTradingController örneği, ticaret devre dışı bırakılmış olarak oluşturulur
    config = PaperControllerConfig(trading_enabled=False, paper_execution_enabled=False)
    return PaperTradingController(config=config)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "component": "PAPER-002 Stage A Controller"}


@router.get("/preflight")
def preflight_status() -> dict[str, Any]:
    try:
        controller = get_controller()
        result = controller.run_dry_run()
        return {
            "status": "success",
            "trading_enabled": controller.config.trading_enabled,
            "paper_execution_enabled": controller.config.paper_execution_enabled,
            "environment": controller.config.environment,
            "readiness_state": result.readiness_state,
            "block_reason": result.block_reason,
            "message": "Preflight checks evaluated successfully using frozen universe.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remediation/review")
def remediation_stage_a_review() -> dict[str, Any]:
    try:
        controller = get_controller()
        result = controller.run_dry_run()
        return {
            "stage": "A",
            "remediation_status": "verified",
            "audit_log_path": str(controller.config.audit_log_path),
            "incident_log_path": str(controller.config.incident_log_path),
            "broker_audit_log_path": str(controller.config.broker_audit_log_path),
            "safety_manager_initialized": controller.safety is not None,
            "paper_session_id": result.paper_session_id,
            "eligible_count": result.eligible_count,
            "submission_authorized": result.submission_authorized,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
