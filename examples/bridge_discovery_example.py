import asyncio
from hueify import HueBridge

async def main():
    print("🔍 Searching for Hue Bridges...")
    bridges = await HueBridge.discover_bridges()

    if not bridges:
        print("❌ No Hue Bridges found on the network.")
        return

    print(f"✅ Found {len(bridges)} bridge(s):")
    for i, bridge in enumerate(bridges, start=1):
        ip = bridge.internalipaddress
        print(f"  {i}. IP: {ip}")


if __name__ == "__main__":
    asyncio.run(main())
