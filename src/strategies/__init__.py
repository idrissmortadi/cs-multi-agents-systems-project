from strategies.base_strategy import BaseStrategy
from strategies.complete_strategy import (
    CompleteStrategy,
)
from strategies.random_walk import RandomWalk

# Map names to classes
STRATEGY_MAPPING = {
    "Random Walk": RandomWalk,
    "Complete Strategy": CompleteStrategy,
}

__all__ = [
    "RandomWalk",
    "BaseStrategy",
    "CompleteStrategy",
    "STRATEGY_MAPPING",
]
