class HueifyError(Exception):
    """Base class for errors raised by hueify itself rather than by httpx."""


class ResourceNotFoundError(HueifyError):
    """A resource addressed by ID or name does not exist on the bridge."""


class MissingCredentialsError(HueifyError):
    """No bridge IP and application key could be resolved for this client."""


class StreamAuthenticationError(HueifyError):
    """The bridge rejected the application key, so reconnecting cannot help."""


class MissingDependencyError(HueifyError):
    """A feature was used that needs an optional dependency of hueify."""


class EntertainmentError(HueifyError):
    """Streaming to an entertainment area failed."""


class EntertainmentAuthenticationError(EntertainmentError):
    """The bridge rejected the client key, so retrying cannot help."""
