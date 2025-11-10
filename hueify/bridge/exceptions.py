class HueBridgeException(Exception):
    pass


class BridgeNotFoundException(HueBridgeException):
    def __init__(self, message: str = "No Hue Bridge found on the network"):
        self.message = message
        super().__init__(self.message)


class BridgeConnectionException(HueBridgeException):
    def __init__(self, message: str = "Failed to connect to Hue Bridge"):
        self.message = message
        super().__init__(self.message)
        