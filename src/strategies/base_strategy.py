class BaseStrategy:
    """
    Base class for all strategies.
    """

    def __init__(self, name: str, drone):
        self.name = name
        self.drone = drone

    def execute(self):
        """
        Execute the strategy.
        """
        raise NotImplementedError("Subclasses must implement this method.")
