import logging
import os

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from agents import Drone
from communication.message.message_service import MessageService
from objects import Waste, Zone


class Environment(Model):
    def __init__(
        self,
        green_agents=1,
        yellow_agents=0,
        red_agents=0,
        green_wastes=5,
        yellow_wastes=3,
        red_wastes=2,
        width=9,
        height=9,
        seed=None,
    ):
        super().__init__(seed=seed)

        if MessageService.get_instance() is None:
            self.message_service = MessageService(self)
            self.message_service.set_instant_delivery(True)
        else:
            self.message_service = MessageService.get_instance()
            self.message_service.set_model(self)

        # Clear old log files before setting up new ones
        self._clear_logs()

        # Set up logging for environment
        self._setup_logging()

        # Set up data collector
        self.datacollector = DataCollector(
            model_reporters={
                "green_wastes": lambda m: len(
                    [
                        a
                        for a in m.grid.agents
                        if isinstance(a, Waste) and a.waste_color == 0
                    ]
                ),
                "yellow_wastes": lambda m: len(
                    [
                        a
                        for a in m.grid.agents
                        if isinstance(a, Waste) and a.waste_color == 1
                    ]
                ),
                "red_wastes": lambda m: len(
                    [
                        a
                        for a in m.grid.agents
                        if isinstance(a, Waste) and a.waste_color == 2
                    ]
                ),
                "wastes_in_drop_zone": lambda m: len(
                    [
                        a
                        for a in m.grid.agents
                        if isinstance(a, Waste)
                        and a.waste_color == 2
                        and m._get_zone(a.pos).is_drop_zone
                    ]
                ),
                "wastes_not_in_drop_zone": lambda m: len(
                    [
                        a
                        for a in m.grid.agents
                        if isinstance(a, Waste) and a.pos[0] != m.grid.width - 1
                    ]
                ),
                "wastes_in_inventories": lambda m: sum(
                    [
                        len(a.knowledge.inventory)
                        for a in m.grid.agents
                        if isinstance(a, Drone) and a.knowledge.inventory
                    ]
                ),
            },
            agent_reporters={},
        )

        # Store number of agents and wastes per zone type
        self.green_agents = green_agents
        self.yellow_agents = yellow_agents
        self.red_agents = red_agents

        self.green_wastes = green_wastes
        self.yellow_wastes = yellow_wastes
        self.red_wastes = red_wastes

        self.num_agents = green_agents + yellow_agents + red_agents
        self.num_wastes = green_wastes + yellow_wastes + red_wastes

        self.waste_state_changes = {}

        # No torus, agents cannot move off the grid
        self.grid = MultiGrid(width, height, torus=False)
        self.zone_mapping = {"G": 0, "Y": 1, "R": 2}

        self.logger.info(
            "Initializing environment with %d agents (%d green, %d yellow, %d red), "
            "%d wastes (%d green, %d yellow, %d red), %dx%d grid",
            self.num_agents,
            green_agents,
            yellow_agents,
            red_agents,
            self.num_wastes,
            green_wastes,
            yellow_wastes,
            red_wastes,
            width,
            height,
        )

        # Initialize zones
        for x in range(width):
            for y in range(height):
                zone_color = 0 if x < width // 3 else 1 if x < 2 * width // 3 else 2
                is_drop_zone = True if x == width - 1 else False
                a = Zone(self, zone_color, is_drop_zone)
                self.grid.place_agent(a, (x, y))
                self.logger.info(
                    f"Placed zone {a.unique_id} at position {(x, y)} with color {zone_color} | "
                    f"Zone type: {zone_color}, Drop zone: {is_drop_zone}"
                )

        # Initialize wastes in each zone type
        self._initialize_wastes_by_zone(0, green_wastes, width, height)  # Green zone
        self._initialize_wastes_by_zone(1, yellow_wastes, width, height)  # Yellow zone
        self._initialize_wastes_by_zone(2, red_wastes, width, height)  # Red zone

        # Initialize agents in each zone type
        self._initialize_drones_by_zone(0, green_agents, width, height)  # Green zone
        self._initialize_drones_by_zone(1, yellow_agents, width, height)  # Yellow zone
        self._initialize_drones_by_zone(2, red_agents, width, height)  # Red zone

    def _clear_logs(self):
        """Clear all existing log files before starting a new simulation"""
        logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )

        if os.path.exists(logs_dir):
            # Shutdown all logging before clearing files
            logging.shutdown()

            # Reset logging manager
            logging.Logger.manager.loggerDict.clear()

            # Remove and recreate agents directory
            agents_dir = os.path.join(logs_dir, "agents")
            if os.path.exists(agents_dir):
                try:
                    for filename in os.listdir(agents_dir):
                        file_path = os.path.join(agents_dir, filename)
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
                except OSError:
                    pass

            os.makedirs(agents_dir, exist_ok=True)

            # Clear environment log
            env_log_file = os.path.join(logs_dir, "environment.log")
            try:
                if os.path.exists(env_log_file):
                    os.remove(env_log_file)
            except OSError:
                pass

    def _initialize_wastes_by_zone(self, zone_type, num_wastes, width, height):
        """Initialize the specified number of wastes in a specific zone type"""
        zone_positions = []

        # Exclude the drop zone for red wastes
        if zone_type == 2:
            width = width - 1

        # Find all positions of the specified zone type
        for x in range(width):
            for y in range(height):
                pos = (x, y)
                zone = self._get_zone(pos)
                if zone and zone.zone_type == zone_type:
                    zone_positions.append(pos)

        # Create wastes in the zone
        for _ in range(num_wastes):
            if zone_positions:
                pos = self.random.choice(zone_positions)
                a = Waste(self, zone_type)
                self.grid.place_agent(a, pos)
                self.logger.info(
                    f"Placed waste {a.unique_id} at position {pos} with color {zone_type}"
                )

    def _initialize_drones_by_zone(self, zone_type, num_drones, width, height):
        """Initialize the specified number of drones in a specific zone type"""
        zone_positions = []

        # Find all positions of the specified zone type
        for x in range(width):
            for y in range(height):
                pos = (x, y)
                zone = self._get_zone(pos)
                if zone and zone.zone_type == zone_type:
                    zone_positions.append(pos)

        # Create drones in the zone
        for _ in range(num_drones):
            if zone_positions:
                pos = self.random.choice(zone_positions)
                a = Drone(self, zone_type)
                self.grid.place_agent(a, pos)
                self.logger.info(
                    f"Placed drone {a.unique_id} at position {pos} in zone type {zone_type}"
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
            for handler in list(self.logger.handlers):
                handler.close()
                self.logger.removeHandler(handler)

        # File handler for environment with mode 'w' to overwrite
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, "environment.log"), mode="w"
        )
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def step(self):
        self.datacollector.collect(self)

        # Shuffle agents and execute their steps
        self.agents.shuffle_do("step_agent")

        # Check grid clean and all wastes treated when stationary
        self._check_grid_clean_and_wastes_treated()

    def _check_grid_clean_and_wastes_treated(self):
        """Check if the grid is clean and all wastes are treated."""
        model_vars = self.datacollector.get_model_vars_dataframe()
        if not model_vars.empty:
            wastes_not_in_drop_zone = model_vars["wastes_not_in_drop_zone"].iloc[-1]
            wastes_in_inventories = model_vars["wastes_in_inventories"].iloc[-1]
            if wastes_not_in_drop_zone == 0:
                self.logger.info("Grid is clean: all wastes are in the drop zone.")
            if wastes_in_inventories == 0:
                self.logger.info(
                    "All wastes have been treated: no wastes in inventories."
                )

    def _get_zone(self, pos):
        cellmates = self.grid.get_cell_list_contents(pos)
        for agent in cellmates:
            if isinstance(agent, Zone):
                return agent
        return None

    def remove_agent(self, agent):
        self.grid.remove_agent(agent)
        self.num_agents -= 1
        self.logger.info(f"Removed agent {agent.unique_id} from the environment")

    def add_agent(self, agent, pos):
        self.grid.place_agent(agent, pos)
        self.num_agents += 1
        self.logger.info(f"Added agent {agent.unique_id} at position {pos}")

    def get_agent_by_id(self, agent_id):
        """Retrieve an agent by its unique ID"""
        return self.agents.select(lambda a: a.unique_id == agent_id)[0]

    @staticmethod
    def do(drone: Drone, action: str) -> dict:
        # Removed call to track_agent_movement (not needed)
        getattr(drone, action)()
        drone.logger.info(f"Executing action: {action}")
        neighbors = drone.model.grid.get_neighborhood(
            drone.pos, moore=False, include_center=True
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
        drone_zone_type = drone.knowledge.zone_type
        valid_neighbors_cells = []
        for pos in neighbors:
            zone_agent = neighbor_zones[neighbors.index(pos)]
            if zone_agent and zone_agent.zone_type <= drone_zone_type:
                valid_neighbors_cells.append(pos)
        neighbors_cells_empty = set(valid_neighbors_cells) - set(
            [a.pos for a in neighbor_drones]
        )
        percepts = {
            "neighbors_empty": list(neighbors_cells_empty),
            "neighbor_zones": [(a.zone_type, a.pos) for a in neighbor_zones],
            "neighbor_drones": [(a.unique_id, a.pos) for a in neighbor_drones],
            "neighbor_wastes": [(a.unique_id, a.pos) for a in neighbor_wastes],
        }
        return percepts
