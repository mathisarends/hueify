from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hueify.models import HueApiError


class HueifyError(Exception):
    """Base class for errors raised by hueify itself rather than by httpx."""


class BridgeError(HueifyError):
    """The bridge returned API errors; the original payloads are in ``errors``."""

    def __init__(self, errors: Iterable[HueApiError]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(error.description for error in self.errors))


class ResourceNotFoundError(HueifyError):
    """A resource addressed by ID or name does not exist on the bridge."""


class AmbiguousResourceError(HueifyError):
    """A name matches several resources; choose a specific ID or group."""


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
