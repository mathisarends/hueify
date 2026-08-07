"""Streaming to a Hue entertainment area over its UDP protocol.

The REST API is not built for light shows: every command is an HTTPS request
the bridge queues, and a beat that arrives 300 ms late is not a beat. An
entertainment area is the other path - the bridge takes DTLS datagrams on port
2100 and forwards their colors to the lamps at about 25 Hz, without
acknowledging anything.

Finding and inspecting areas is part of plain hueify. Streaming to them needs
the optional extra, which brings the one dependency the DTLS handshake has::

    pip install "hueify[entertainment]"
"""

from hueify.entertainment.namespace import EntertainmentNamespace
from hueify.entertainment.protocol import (
    MAX_CHANNELS,
    ColorSpace,
    Frame,
    encode_frame,
    frame_length,
)
from hueify.entertainment.source import FrameSource, Renderer, Tick
from hueify.entertainment.stream import (
    DEFAULT_RATE,
    MAX_RATE,
    MIN_RATE,
    EntertainmentStream,
    StreamStats,
)

__all__ = [
    "DEFAULT_RATE",
    "MAX_CHANNELS",
    "MAX_RATE",
    "MIN_RATE",
    "ColorSpace",
    "EntertainmentNamespace",
    "EntertainmentStream",
    "Frame",
    "FrameSource",
    "Renderer",
    "StreamStats",
    "Tick",
    "encode_frame",
    "frame_length",
]
