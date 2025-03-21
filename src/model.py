import logging
import os

from mesa import Model
from mesa.space import MultiGrid

from agents import Drone
from objects import Waste, Zone


class Environment(Model):
    def __init__(self, n=1, num_wastes=10, width=9, height=9, seed=None):
        super().__init__(seed=seed)

        # Set up logging for environment
        self._setup_logging()

        self.num_agents = n
        self.num_wastes = num_wastes

        # No torus, agents cannot move off the grid
        self.grid = MultiGrid(width, height, torus=False)
        self.zone_mapping = {"G": 0, "Y": 1, "R": 2}

        self.logger.info(
            "Initializing environment with %d agents, %d wastes, %dx%d grid",
            n,
            num_wastes,
            width,
            height,
        )

        # Initialize zones
        for x in range(width):
            for y in range(height):
                zone_color = 0 if x < width // 3 else 1 if x < 2 * width // 3 else 2
                a = Zone(self, zone_color)
                self.grid.place_agent(a, (x, y))

        # Initialize wastes randomly
        for _ in range(self.num_wastes):
            x, y = self.random.randrange(width), self.random.randrange(height)
            waste_color = self._get_zone((x, y)).zone_type

            a = Waste(self, waste_color)
            self.grid.place_agent(a, (x, y))
            self.logger.info(
                f"Placed waste {a.unique_id} at position ({x}, {y}) with color {waste_color}"
            )

        # Initialize agents randomly
        for _ in range(self.num_agents):
            x, y = self.random.randrange(width), self.random.randrange(height)
            zone_type = self._get_zone((x, y)).zone_type
            a = Drone(self, zone_type)
            self.grid.place_agent(a, (x, y))
            self.logger.info(
                f"Placed drone {a.unique_id} at position ({x}, {y}) in zone type {zone_type}"
            )

    def _setup_logging(self):
        """Set up logging for the environment"""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Create agents directory if it doesn't exist
        agents_dir = os.path.join(logs_dir, "agents")
        if not os.path.exists(agents_dir):
            os.makedirs(agents_dir)

        # Set up environment logger
        self.logger = logging.getLogger("environment")
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()

        # File handler for environment
        file_handler = logging.FileHandler(os.path.join(logs_dir, "environment.log"))
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def step(self):
        self.logger.info("Starting a new step in the environment")
        self.agents.shuffle_do("step_agent")

    def _get_zone(self, pos):
        cellmates = self.grid.get_cell_list_contents(pos)
        for agent in cellmates:
            if isinstance(agent, Zone):
                return agent
        return None

    def remove_agent(self, agent):
        self.grid.remove_agent(agent)
        # self.schedule.remove(agent)
        self.num_agents -= 1
        self.logger.info(f"Removed agent {agent.unique_id} from the environment")

    def add_agent(self, agent, pos):
        self.grid.place_agent(agent, pos)
        self.num_agents += 1
        # self.schedule.add(agent)
        self.logger.info(f"Added agent {agent.unique_id} at position {pos}")

    def get_agent_by_id(self, agent_id):
        """Retrieve an agent by its unique ID"""
        return self.agents.select(lambda a: a.unique_id == agent_id)[0]

    @staticmethod
    def do(drone: Drone, action: str) -> dict:
        getattr(drone, action)()

        # Log the action
        drone.logger.info(f"Executing action: {action}")

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
            if zone_agent and zone_agent.zone_type <= drone_zone_type:
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
