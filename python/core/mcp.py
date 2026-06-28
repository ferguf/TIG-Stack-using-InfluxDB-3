"""
Core Infrastructure: FastMCP Protocol Bridge
File: core/mcp.py

Purpose:
- Preserve original working FastMCP bridge pattern
- Load legacy MCP tools
- Add explicit billing read-only MCP tools
- Expose only billing read-only tools
- Provide /mcp/openapi.json discovery endpoint
- Avoid FastAPI route auto-wrapping
- Avoid leaking Depends(get_db) into MCP schemas
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, MutableMapping, Optional

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from fast_mcp.loader import load_all_mcp_tools

from core.database import get_db
from domains.billing import operations as ops
from domains.billing.operations import (
    BillingValidationError,
    BillingNotFoundError,
    BillingConflictError,
)

logger = logging.getLogger("uvicorn.error")


# =========================================================
# MCP CONFIG
# =========================================================

MCP_SERVER_NAME = "Network-Digital-Twin"
MCP_MOUNT_PATH = "/mcp"
MCP_DISCOVERY_PATH = "/mcp/openapi.json"


ALLOWED_BILLING_READ_TOOLS = {
    "billing_list_models",
    "billing_list_rates",
    "billing_list_providers",
    "billing_get_composite_rate_catalog",
    "billing_get_customer_rates",
    "billing_get_provider_rates",
}


BLOCKED_WRITE_WORDS = (
    "create",
    "update",
    "delete",
    "remove",
    "upsert",
    "seed",
    "apply",
    "register",
    "provision",
    "modify",
)


# =========================================================
# DB SESSION HELPER
# =========================================================

@contextmanager
def billing_db_session():
    """
    Open a DB session for MCP tools.

    MCP tools are not FastAPI endpoints, so FastAPI Depends(get_db)
    does not automatically execute here.
    """
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        yield db
    finally:
        db_gen.close()


# =========================================================
# ERROR HANDLING
# =========================================================

def serialize_error(e: Exception) -> Dict[str, Any]:
    if isinstance(e, BillingNotFoundError):
        return {
            "error": True,
            "status_code": 404,
            "type": "BillingNotFoundError",
            "message": str(e),
        }

    if isinstance(e, BillingValidationError):
        return {
            "error": True,
            "status_code": 422,
            "type": "BillingValidationError",
            "message": str(e),
        }

    if isinstance(e, BillingConflictError):
        return {
            "error": True,
            "status_code": 409,
            "type": "BillingConflictError",
            "message": str(e),
        }

    return {
        "error": True,
        "status_code": 500,
        "type": e.__class__.__name__,
        "message": str(e),
    }


# =========================================================
# EXPLICIT BILLING READ MCP TOOLS
# =========================================================

def register_billing_read_tools(mcp_app: Any) -> None:
    """
    Register explicit billing read-only MCP tools.

    These are intentionally MCP-native functions, not wrapped FastAPI routes.
    That avoids FastAPI Depends(get_db) leaking into the MCP schema.
    """

    @mcp_app.tool(
        name="billing_list_models",
        description=(
            "List all billing models. Use when the user asks what billing "
            "models are available, such as FIXED, ON_DEMAND, or TOKENIZED."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_list_models() -> List[Dict[str, Any]]:
        with billing_db_session() as db:
            try:
                return jsonable_encoder(ops.list_models(db))
            except Exception as e:
                return [serialize_error(e)]

    @mcp_app.tool(
        name="billing_list_rates",
        description=(
            "List all billing rate cards. Use when the user asks for available "
            "billing rates or rate cards."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_list_rates() -> List[Dict[str, Any]]:
        with billing_db_session() as db:
            try:
                return jsonable_encoder(ops.list_rates(db))
            except Exception as e:
                return [serialize_error(e)]

    @mcp_app.tool(
        name="billing_list_providers",
        description=(
            "List all billing providers. Use when the user asks for configured "
            "offnet or wholesale providers."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_list_providers() -> List[Dict[str, Any]]:
        with billing_db_session() as db:
            try:
                return jsonable_encoder(ops.list_providers(db))
            except Exception as e:
                return [serialize_error(e)]

    @mcp_app.tool(
        name="billing_get_composite_rate_catalog",
        description=(
            "Get the composite rate card catalog for a specific rate_id. "
            "Use when the user asks for the full nested billing catalog."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_get_composite_rate_catalog(rate_id: str) -> Dict[str, Any]:
        with billing_db_session() as db:
            try:
                sql = text(
                    """
                    SELECT *
                    FROM v_rate_card_composite
                    WHERE rate_id = CAST(:rate_id AS UUID)
                    """
                )

                result = db.execute(sql, {"rate_id": rate_id}).mappings().first()

                if not result:
                    return {
                        "error": True,
                        "status_code": 404,
                        "message": f"No composite rate catalog found for rate_id={rate_id}",
                    }

                return jsonable_encoder(dict(result))

            except Exception as e:
                return serialize_error(e)

    @mcp_app.tool(
        name="billing_get_customer_rates",
        description=(
            "Get all billing rate cards assigned to a specific customer_id. "
            "Use when the user asks which rate cards apply to a customer."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_get_customer_rates(customer_id: str) -> List[Dict[str, Any]]:
        with billing_db_session() as db:
            try:
                sql = text(
                    """
                    SELECT r.*
                    FROM billing_rate r
                    JOIN customer_rate_cards crc
                        ON r.id = crc.rate_id
                    WHERE crc.customer_id = :customer_id
                    ORDER BY r.effective_start_ts DESC
                    """
                )

                result = db.execute(sql, {"customer_id": customer_id}).mappings().all()
                return jsonable_encoder([dict(row) for row in result])

            except Exception as e:
                return [serialize_error(e)]

    @mcp_app.tool(
        name="billing_get_provider_rates",
        description=(
            "Get all billing rate cards assigned to a specific provider_id. "
            "Use when the user asks which buy-rate cards apply to an offnet "
            "or wholesale provider."
        ),
        meta={"domain": "billing", "read_only": True},
    )
    def billing_get_provider_rates(provider_id: str) -> List[Dict[str, Any]]:
        with billing_db_session() as db:
            try:
                sql = text(
                    """
                    SELECT r.*
                    FROM billing_rate r
                    JOIN provider_rate_cards prc
                        ON r.id = prc.rate_id
                    WHERE prc.provider_id = :provider_id
                    ORDER BY r.effective_start_ts DESC
                    """
                )

                result = db.execute(sql, {"provider_id": provider_id}).mappings().all()
                return jsonable_encoder([dict(row) for row in result])

            except Exception as e:
                return [serialize_error(e)]


# =========================================================
# TOOL MANAGER HELPERS
# =========================================================

def _get_tool_manager(mcp_app: Any) -> Any:
    return getattr(mcp_app, "_tool_manager", None)


def _get_raw_tools(mcp_app: Any) -> Any:
    tool_manager = _get_tool_manager(mcp_app)

    if not tool_manager:
        return {}

    return getattr(
        tool_manager,
        "tools",
        getattr(tool_manager, "_tools", {}),
    )


def _get_tool_meta(tool: Any) -> Dict[str, Any]:
    meta = getattr(tool, "meta", None)

    if isinstance(meta, dict):
        return meta

    private_meta = getattr(tool, "_meta", None)

    if isinstance(private_meta, dict):
        return private_meta

    return {}


def _is_read_only_billing_tool(name: str, tool: Any) -> bool:
    normalized_name = name.lower()

    # Explicit allow-list
    if name in ALLOWED_BILLING_READ_TOOLS:
        return True

    # Defensive mutation block
    if any(word in normalized_name for word in BLOCKED_WRITE_WORDS):
        return False

    # Metadata-based future support
    meta = _get_tool_meta(tool)

    domain = (
        meta.get("domain")
        or getattr(tool, "domain", None)
        or ""
    )

    read_only = (
        meta.get("read_only")
        if "read_only" in meta
        else getattr(tool, "read_only", None)
    )

    if str(domain).lower() == "billing" and read_only is True:
        return True

    return False


def _prune_tools_to_billing_read_only(mcp_app: Any) -> int:
    raw_tools = _get_raw_tools(mcp_app)

    if not isinstance(raw_tools, MutableMapping):
        logger.warning(
            "MCP tool registry is not a mutable dict; cannot prune tools."
        )
        return 0

    original_names = list(raw_tools.keys())
    removed = 0

    for name in original_names:
        tool = raw_tools[name]

        if not _is_read_only_billing_tool(name, tool):
            raw_tools.pop(name, None)
            removed += 1

    return removed


# =========================================================
# TOOL DISCOVERY NORMALIZATION
# =========================================================

def _empty_input_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }


def _normalize_tool(name: str, tool: Any) -> Dict[str, Any]:
    input_schema = (
        getattr(tool, "parameters", None)
        or getattr(tool, "input_schema", None)
        or getattr(tool, "inputSchema", None)
        or _empty_input_schema()
    )

    output_schema = (
        getattr(tool, "output_schema", None)
        or getattr(tool, "outputSchema", None)
    )

    return {
        "name": name,
        "description": getattr(tool, "description", ""),
        "inputSchema": input_schema,
        "outputSchema": output_schema,
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }


def _build_discovery_payload(mcp_app: Any) -> Dict[str, Any]:
    raw_tools = _get_raw_tools(mcp_app)

    tools: List[Dict[str, Any]] = []

    if isinstance(raw_tools, dict):
        for name in sorted(raw_tools.keys()):
            tool = raw_tools[name]

            if _is_read_only_billing_tool(name, tool):
                tools.append(_normalize_tool(name, tool))

    elif isinstance(raw_tools, list):
        for tool in raw_tools:
            name = getattr(tool, "name", "unknown")

            if _is_read_only_billing_tool(name, tool):
                tools.append(_normalize_tool(name, tool))

    return {
        "protocol": "MCP",
        "version": "1.0",
        "info": {
            "title": "Billing Read MCP",
            "version": "1.0.0",
            "scope": "billing-read-only",
        },
        "tools": tools,
    }


# =========================================================
# MCP SETUP
# =========================================================

def setup_mcp(app: FastAPI):
    """
    Initialize and mount FastMCP.

    Correct order in main.py:
        app.include_router(...)
        setup_mcp(app)
    """

    logger.info("MCP SETUP CALLED")

    try:
        from fastmcp import FastMCP

        # -------------------------------------------------
        # 1. Create FastMCP server
        # -------------------------------------------------
        mcp_app = FastMCP(MCP_SERVER_NAME)

        # -------------------------------------------------
        # 2. Preserve original working loader pattern
        # -------------------------------------------------
        load_all_mcp_tools(mcp_app)

        # -------------------------------------------------
        # 3. Add explicit billing read-only tools
        # -------------------------------------------------
        register_billing_read_tools(mcp_app)

        raw_tools = _get_raw_tools(mcp_app)
        total_before = len(raw_tools) if isinstance(raw_tools, (dict, list)) else 0

        # -------------------------------------------------
        # 4. Enforce billing read-only tool surface
        # -------------------------------------------------
        removed = _prune_tools_to_billing_read_only(mcp_app)

        raw_tools_after = _get_raw_tools(mcp_app)
        total_after = len(raw_tools_after) if isinstance(raw_tools_after, (dict, list)) else 0

        logger.info(
            "MCP tools loaded=%s removed=%s exposed=%s",
            total_before,
            removed,
            total_after,
        )

        # -------------------------------------------------
        # 5. Parent-level discovery route
        # -------------------------------------------------
        @app.get(MCP_DISCOVERY_PATH, include_in_schema=False)
        async def get_mcp_schema():
            return JSONResponse(_build_discovery_payload(mcp_app))

        # -------------------------------------------------
        # 6. Mount FastMCP HTTP app
        # -------------------------------------------------
        inner_app = mcp_app.http_app()

        app.mount(MCP_MOUNT_PATH, inner_app, name="mcp_interface")

        logger.info("MCP mounted at %s", MCP_MOUNT_PATH)
        logger.info("MCP discovery available at %s", MCP_DISCOVERY_PATH)

    except Exception as e:
        logger.error("Failed to initialize MCP: %s", e, exc_info=True)
        raise