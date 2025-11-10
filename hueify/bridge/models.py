from pydantic import BaseModel, Field, TypeAdapter

class BridgeDiscoveryResponse(BaseModel):
    internalipaddress: str = Field(..., description="Local IP address of the bridge")


BridgeListAdapter = TypeAdapter(list[BridgeDiscoveryResponse])