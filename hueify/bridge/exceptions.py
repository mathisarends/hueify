from hueify.shared.exceptions import HueifyException


class BridgeNotFoundException(HueifyException):
    def __init__(self, message: str = "No Hue Bridge found on the network"):
        self.message = message
        super().__init__(self.message)


class BridgeConnectionException(HueifyException):
    def __init__(self, message: str = "Failed to connect to Hue Bridge"):
        self.message = message
        super().__init__(self.message)
