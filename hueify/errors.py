class HueifyError(Exception):
    """Base class for errors raised by hueify itself rather than by httpx."""


class ResourceNotFoundError(HueifyError):
    """A resource addressed by ID or name does not exist on the bridge."""
