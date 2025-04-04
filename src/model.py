import logging
import os
import shutil
from typing import Optional

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from agents import Drone
from objects import Waste, Zone
from tracker import Tracker


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
        tracker: Optional[Tracker] = None,
    ):
        super().__init__(seed=seed)

        # Add tracker
        self.tracker = tracker

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
                "avg_processing_time": lambda m: m.tracker.metrics[
                    "processing_efficiency"
                ]["avg_processing_time"]
                if m.tracker and "processing_efficiency" in m.tracker.metrics
                else 0,
                "avg_throughput": lambda m: m.tracker.metrics["system_metrics"][
                    "avg_throughput"
                ]
                if m.tracker and "system_metrics" in m.tracker.metrics
                else 0,
                "inventory_utilization": lambda m: sum(
                    [
                        len(a.knowledge["inventory"])
                        for a in m.grid.agents
                        if isinstance(a, Drone)
                    ]
                ),
                "avg_distance_per_agent": lambda m: m.tracker.metrics["agent_behavior"][
                    "avg_distance_per_agent"
                ]
                if m.tracker
                else 0,
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
            # Delete the agents directory completely
            agents_dir = os.path.join(logs_dir, "agents")
            if os.path.exists(agents_dir):
                shutil.rmtree(agents_dir)

            # Delete the environment log file if it exists
            env_log_file = os.path.join(logs_dir, "environment.log")
            if os.path.exists(env_log_file):
                os.remove(env_log_file)

            # Optional: Log to console that logs were cleared
            print("Cleared previous log files.")

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

                # Track initial waste state with tracker
                if self.tracker:
                    self.tracker.track_waste(
                        waste_id=a.unique_id, current_zone=zone_type, status="created"
                    )
                    self.waste_state_changes[a.unique_id] = {
                        "color": zone_type,
                        "last_status": "created",
                        "last_position": pos,
                    }

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
            self.logger.handlers.clear()

        # File handler for environment
        file_handler = logging.FileHandler(os.path.join(logs_dir, "environment.log"))
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def track_waste_changes(self):
        """Track changes in waste status and position"""
        if not self.tracker:
            return

        # Get all waste objects
        waste_objects = [
            agent for agent in self.grid.agents if isinstance(agent, Waste)
        ]

        for waste in waste_objects:
            waste_id = waste.unique_id
            current_zone_agent = self._get_zone(waste.pos)
            current_zone_type = (
                current_zone_agent.zone_type if current_zone_agent else -1
            )

            # Check if waste is in drop zone and is red (completed)
            is_completed = (
                current_zone_agent
                and current_zone_agent.is_drop_zone
                and waste.waste_color == 2
            )

            # Determine current status
            current_status = "completed" if is_completed else "active"

            # Check if waste is new or has changed
            if waste_id not in self.waste_state_changes:
                # New waste that wasn't tracked at initialization
                self.waste_state_changes[waste_id] = {
                    "color": waste.waste_color,
                    "last_status": current_status,
                    "last_position": waste.pos,
                }
                self.tracker.track_waste(
                    waste_id=waste_id,
                    current_zone=current_zone_type,
                    status=current_status,
                )
            else:
                # Existing waste - check for changes
                state = self.waste_state_changes[waste_id]

                # If color changed, waste was transformed
                if waste.waste_color != state["color"]:
                    self.tracker.track_waste(
                        waste_id=waste_id,
                        current_zone=current_zone_type,
                        status="transformed",
                    )
                    state["color"] = waste.waste_color
                    state["last_status"] = "transformed"
                # If status changed to completed
                elif (
                    current_status == "completed"
                    and state["last_status"] != "completed"
                ):
                    self.tracker.track_waste(
                        waste_id=waste_id,
                        current_zone=current_zone_type,
                        status="completed",
                    )
                    state["last_status"] = "completed"
                # If position changed
                elif waste.pos != state["last_position"]:
                    self.tracker.track_waste(
                        waste_id=waste_id,
                        current_zone=current_zone_type,
                        status="moved",
                    )
                    state["last_position"] = waste.pos

    def step(self):
        self.tracker.calculate_metrics()
        self.datacollector.collect(self)

        # self.logger.info("Starting a new step in the environment")
        self.agents.shuffle_do("step_agent")

        # Track waste changes after agents have acted
        self.track_waste_changes()

        # Track metrics for each zone
        if self.tracker:
            step_data = {"step": self.steps}

            # Count wastes by zone
            for zone_type in range(3):
                wastes_in_zone = len(
                    [
                        agent
                        for agent in self.grid.agents
                        if isinstance(agent, Waste)
                        and self._get_zone(agent.pos)
                        and self._get_zone(agent.pos).zone_type == zone_type
                    ]
                )
                step_data[f"{zone_type}_zone_wastes"] = wastes_in_zone

            # Count wastes in drop zone
            wastes_in_drop = len(
                [
                    agent
                    for agent in self.grid.agents
                    if isinstance(agent, Waste)
                    and agent.waste_color == 2
                    and agent.pos[0] == self.grid.width - 1
                ]
            )
            step_data["red_zone_wastes"] = wastes_in_drop

            # Log the step data
            self.tracker.log_result(step_data)

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
        # self.schedule.add(agent)
        self.logger.info(f"Added agent {agent.unique_id} at position {pos}")

    def get_agent_by_id(self, agent_id):
        """Retrieve an agent by its unique ID"""
        return self.agents.select(lambda a: a.unique_id == agent_id)[0]

    @staticmethod
    def do(drone: Drone, action: str) -> dict:
        # Track the action before executing (to get the correct inventory state)
        if drone.model.tracker:
            drone.model.tracker.track_agent_movement(
                agent_id=drone.unique_id,
                position=drone.pos,
                inventory_size=len(drone.knowledge["inventory"]),
                action=action,
            )

        # Execute the action
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
