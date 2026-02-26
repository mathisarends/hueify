import functools
import inspect
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

try:
    from fastmcp import Context, FastMCP
except ImportError as e:
    raise ImportError(
        "MCP support requires 'fastmcp'. Install with: pip install hueify[mcp]"
    ) from e

from hueify import Hueify


@asynccontextmanager
async def lifespan(_: FastMCP) -> AsyncIterator[dict]:
    async with Hueify() as hueify:
        yield {"hueify": hueify}


class HueifyMCP(FastMCP):
    def _namespace_tool(self, namespace: str, **tool_kwargs):
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, ctx: Context, **kwargs):
                hueify: Hueify = ctx.request_context.lifespan_context["hueify"]
                return await func(
                    *args, **{namespace: getattr(hueify, namespace)}, **kwargs
                )

            sig = inspect.signature(func)
            params = [p for p in sig.parameters.values() if p.name != namespace]
            ctx_param = inspect.Parameter(
                "ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context
            )
            wrapper.__signature__ = sig.replace(parameters=[*params, ctx_param])

            return self.tool(**tool_kwargs)(wrapper)

        return decorator

    def light_tool(self, **tool_kwargs):
        return self._namespace_tool("lights", **tool_kwargs)

    def room_tool(self, **tool_kwargs):
        return self._namespace_tool("rooms", **tool_kwargs)

    def zone_tool(self, **tool_kwargs):
        return self._namespace_tool("zones", **tool_kwargs)

    def scene_tool(self, **tool_kwargs):
        return self._namespace_tool("scenes", **tool_kwargs)
