from typing import Any

from pydantic import BaseModel


class ActionResult(BaseModel):
    message: str
    success: bool = True
    clamped: bool = False
    final_value: Any | None = None
