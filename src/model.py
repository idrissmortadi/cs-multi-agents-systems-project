from mesa import Model
from mesa.space import MultiGrid

from agents import Drone


class Environment(Model):
    def __init__(self, n=10, width=10, height=10, seed=None):
        super().__init__(seed=seed)

        self.num_agents = n

        # No torus, agents cannot move off the grid
        self.grid = MultiGrid(width, height, torus=False)

        for _ in range(self.num_agents):
            x, y = self.random.randrange(width), self.random.randrange(height)
            a = Drone(self)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.agents.shuffle_do("step_agent")
