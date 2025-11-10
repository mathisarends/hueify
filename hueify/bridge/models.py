from pydantic import BaseModel, Field, TypeAdapter

class DisoveredBrigeResponse(BaseModel):
    internalipaddress: str = Field(..., description="Local IP address of the bridge")


BridgeListAdapter = TypeAdapter(list[DisoveredBrigeResponse])