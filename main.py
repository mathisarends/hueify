import asyncio
import httpx
from hueify.bridge import HueBridge


async def create_hue_user(bridge_ip: str) -> str:
    url = f"http://{bridge_ip}/api"
    payload = {"devicetype": "hueify#user"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        data = response.json()

    if isinstance(data, list) and len(data) > 0:
        if "success" in data[0]:
            user_id = data[0]["success"]["username"]
            print(f"✓ API user created!")
            print(f"✓ Username (HUE_USER_ID): {user_id}")
            return user_id
        elif "error" in data[0]:
            print(f"✗ Error: {data[0]['error']['description']}")
            print("→ Press the link button on your Hue Bridge and try again!")
    else:
        print(f"✗ Unexpected response: {data}")

    return None


async def main():
    print("Hue Bridge API User Setup")
    print("=" * 50)

    print("\nDiscovering Hue Bridges...")
    bridges = await HueBridge.discover_bridges()

    if not bridges:
        print("✗ No Hue Bridge found on your network!")
        return

    bridge_ip = bridges[0]["internalipaddress"]
    print(f"✓ Found bridge at: {bridge_ip}")

    print(f"\n⚠ Press the link button on your Hue Bridge NOW!")
    input("Press Enter when you've pressed the button...")

    user_id = await create_hue_user(bridge_ip)

    if user_id:
        print("\nAdd these values to your .env file:")
        print(f"HUE_BRIDGE_IP={bridge_ip}")
        print(f"HUE_USER_ID={user_id}")


if __name__ == "__main__":
    asyncio.run(main())
