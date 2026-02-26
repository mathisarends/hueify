from hueify import configure_logging
from hueify.mcp.server import mcp_server

if __name__ == "__main__":
    configure_logging("INFO")
    mcp_server.run(transport="stdio")
