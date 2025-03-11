from mesa import Model
from mesa.space import MultiGrid

from agents import Drone
from objects import Waste, Zone


class Environment(Model):
    def __init__(self, n=1, num_wastes=10, width=10, height=10, seed=None):
        super().__init__(seed=seed)

        self.num_agents = n
        self.num_wastes = num_wastes

        # No torus, agents cannot move off the grid
        self.grid = MultiGrid(width, height, torus=False)

        # Initialize zones
        for x in range(width):
            for y in range(height):
                zone_color = (
                    "G" if x < width // 3 else "Y" if x < 2 * width // 3 else "R"
                )
                a = Zone(self, zone_color)
                self.grid.place_agent(a, (x, y))

        # Initialize wastes randomly
        for _ in range(self.num_wastes):
            x, y = self.random.randrange(width), self.random.randrange(height)
            waste_color = self._get_zone((x, y)).zone_type

            a = Waste(self, waste_color)
            self.grid.place_agent(a, (x, y))

        # Initialize agents randomly
        for _ in range(self.num_agents):
            x, y = self.random.randrange(width), self.random.randrange(height)
            a = Drone(self)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.agents.shuffle_do("step_agent")

    def _get_zone(self, pos):
        cellmates = self.grid.get_cell_list_contents(pos)
        for agent in cellmates:
            if isinstance(agent, Zone):
                return agent
        return None
