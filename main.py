import asyncio
from hueify.setup import HueSetupService


async def main():
    print("Hue Bridge API User Setup")
    print("=" * 50)
    print()

    try:
        bridge_ip, user_id = await HueSetupService.discover_and_setup()
        
        print(f"\n✓ Setup complete!")
        print(f"\nAdd these values to your .env file:")
        print(f"HUE_BRIDGE_IP={bridge_ip}")
        print(f"HUE_USER_ID={user_id}")
    except ValueError as e:
        print(f"✗ {e}")
    except ConnectionError as e:
        print(f"✗ {e}")
    except RuntimeError as e:
        print(f"✗ {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
