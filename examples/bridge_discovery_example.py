"""
Example script to discover available Philips Hue Bridges on the local network.

Uses the HueBridge class to query the official Hue discovery endpoint and 
prints the IP addresses of any bridges found.
"""

import asyncio
from hueify.bridge import HueBridge

async def main():
    print("🔍 Searching for Hue Bridges...")
    bridges = await HueBridge.discover_bridges()

    if not bridges:
        print("❌ No Hue Bridges found on the network.")
        return

    print(f"✅ Found {len(bridges)} bridge(s):")
    for i, bridge in enumerate(bridges, start=1):
        ip = bridge.get("internalipaddress", "<unknown>")
        print(f"  {i}. IP: {ip}")

if __name__ == "__main__":
    asyncio.run(main())
