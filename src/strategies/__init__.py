from strategies.base_strategy import BaseStrategy
from strategies.random_walk import RandomWalk
from strategies.random_walk_with_communication import (
    RandomWalkWithCommunication,
)

# Map names to classes
STRATEGY_MAPPING = {
    "Random Walk": RandomWalk,
    "RandomWalkWithCommunication": RandomWalkWithCommunication,
}

__all__ = [
    "RandomWalk",
    "BaseStrategy",
    "RandomWalkWithCommunication",
    "STRATEGY_MAPPING",
]
