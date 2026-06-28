import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Import your legacy MCP tool loader
from fast_mcp.loader import load_all_mcp_tools

logger = logging.getLogger("uvicorn.error")

def setup_mcp(app: FastAPI):
    """
    Initializes FastMCP and mounts it to the main FastAPI application.
    """
    try:
        from fastmcp import FastMCP
        
        # 1. Initialize the MCP App
        mcp_app = FastMCP("Network-Digital-Twin") 
        
        # 2. Load your tools
        load_all_mcp_tools(mcp_app) 
        
        # 3. Create the Starlette sub-app
        inner_app = mcp_app.http_app()
        
        # 4. Add the Discovery Route
        @inner_app.route("/openapi.json", methods=["GET"])
        async def get_mcp_schema(request):
            tool_data = []
            tool_manager = getattr(mcp_app, "_tool_manager", None)
            
            if tool_manager:
                raw_tools = getattr(tool_manager, "tools", getattr(tool_manager, "_tools", {}))
                
                if isinstance(raw_tools, dict):
                    for name, t in raw_tools.items():
                        tool_data.append({
                            "name": name,
                            "description": getattr(t, "description", ""),
                            "parameters": getattr(t, "parameters", {})
                        })
                elif isinstance(raw_tools, list):
                    for t in raw_tools:
                        tool_data.append({
                            "name": getattr(t, "name", "unknown"),
                            "description": getattr(t, "description", ""),
                            "parameters": getattr(t, "parameters", {})
                        })
                
                return JSONResponse({
                    "openapi": "3.0.0",
                    "info": {"title": "Network AI Tools", "version": "1.0.0"},
                    "tools": tool_data
                })

        # 5. Mount it to the main FastAPI app
        app.mount("/mcp", inner_app, name="mcp_interface") 
        logger.info("--- SUCCESS: MCP Starlette bridge mounted at /mcp/openapi.json ---")
        
    except Exception as e:
        logger.error(f"Failed to bridge MCP: {e}", exc_info=True)