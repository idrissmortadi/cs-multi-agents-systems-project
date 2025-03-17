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
            zone_type = self._get_zone((x, y)).zone_type
            a = Drone(self, zone_type)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.agents.shuffle_do("step_agent")

    def _get_zone(self, pos):
        cellmates = self.grid.get_cell_list_contents(pos)
        for agent in cellmates:
            if isinstance(agent, Zone):
                return agent
        return None

    def remove_agent(self, agent):
        self.grid.remove_agent(agent)
        self.schedule.remove(agent)
        self.num_agents -= 1

    def add_agent(self, agent, pos):
        self.grid.place_agent(agent, pos)
        self.num_agents += 1
        self.schedule.add(agent)

    def get_agent_by_id(self, agent_id):
        """Retrieve an agent by its unique ID"""
        return self.agents.select(lambda a: a.unique_id == agent_id)[0]

    @staticmethod
    def do(drone: Drone, action: str) -> dict:
        getattr(drone, action)()

        neighbors = drone.model.grid.get_neighborhood(
            drone.pos, moore=False, include_center=False
        )
        neighbor_zones = [
            a
            for a in drone.model.grid.get_cell_list_contents(neighbors)
            if isinstance(a, Zone)
        ]
        neighbor_drones = [
            a
            for a in drone.model.grid.get_cell_list_contents(neighbors)
            if isinstance(a, Drone)
        ]
        neighbor_wastes = [
            a
            for a in drone.model.grid.get_cell_list_contents(neighbors)
            if isinstance(a, Waste)
        ]

        # Get the drone's current zone type
        drone_zone_type = drone.knowledge["zone_type"]

        # Filter neighbors - only include cells that have the same zone type
        valid_neighbors = []
        for pos in neighbors:
            zone_agent = neighbor_zones[neighbors.index(pos)]
            if zone_agent and zone_agent.zone_type == drone_zone_type:
                valid_neighbors.append(pos)

        # Calculate empty neighbors from the filtered list
        neighbors_empty = set(valid_neighbors) - set([a.pos for a in neighbor_drones])

        percepts = {
            "neighbors_empty": list(neighbors_empty),
            "neighbor_zones": [(a.zone_type, a.pos) for a in neighbor_zones],
            "neighbor_drones": [(a.unique_id, a.pos) for a in neighbor_drones],
            "neighbor_wastes": [(a.unique_id, a.pos) for a in neighbor_wastes],
        }
        return percepts
