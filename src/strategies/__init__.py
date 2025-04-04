from strategies.base_strategy import BaseStrategy
from strategies.random_walk import RandomWalk

# Map names to classes
STRATEGY_MAPPING = {
    "Random Walk": RandomWalk,
}

__all__ = ["RandomWalk", "BaseStrategy", "STRATEGY_MAPPING"]
