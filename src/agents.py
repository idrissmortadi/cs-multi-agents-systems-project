import logging
import os
import random

from mesa import Agent

from objects import Waste

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class Drone(Agent):
    """
    A drone agent that can move around the grid, pick up, transform, and drop waste.
    Each drone is assigned to a specific zone type.
    """

    def __init__(self, model, zone_type):
        """
        Initialize a drone agent.

        Args:
            model: The model instance the drone is part of
            zone_type: The type of zone the drone is assigned to
        """
        super().__init__(model)

        # Setup individual agent logger
        self._setup_logger()

        self.logger.info(
            f"Initializing drone {self.unique_id} with zone type {zone_type}"
        )

        self.percepts = {
            "neighbors_empty": [],  # [(x, y), ...] in correponding zone color
            "neighbor_zones": [],  # [(zone_type, zone_pos), ...]
            "neighbor_drones": [],  # [(drone_id, drone_pos), ...]
            "neighbor_wastes": [],  # [(waste_id, waste_pos), ...]
        }
        self.knowledge = {
            "carried_waste_type": None,
            "carried_waste_amount": 0,
            "can_pick": True,
            "actions": [],
            "percepts": [],
            "grid_width": self.model.grid.width,
            "grid_height": self.model.grid.height,
            "zone_type": zone_type,
            "in_drop_zone": False,  # Whether drone is in a drop zone
        }

    def _setup_logger(self):
        """Set up individual logging for this drone"""
        # Get path to logs directory
        logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        agents_dir = os.path.join(logs_dir, "agents")

        # Create dirs if they don't exist
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        if not os.path.exists(agents_dir):
            os.makedirs(agents_dir)

        # Set up logger for this specific drone
        self.logger = logging.getLogger(f"agent_{self.unique_id}")
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Add file handler
        log_file = os.path.join(agents_dir, f"agent_{self.unique_id}.log")
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def move(self):
        """
        Move the drone to a new position chosen randomly from available empty neighbors.
        If no empty neighbors are available, the drone stays in place.
        Updates the drone's knowledge after moving.
        """
        # Choose a new position from available empty neighbors or stay in place
        new_position = random.choice(
            (
                self.percepts["neighbors_empty"]
                if len(self.percepts["neighbors_empty"]) > 0
                else [self.pos]
            )
        )
        # Move the agent to the new position
        self.model.grid.move_agent(self, new_position)

        # Update knowledge about position
        self.knowledge["actions"].append(f"moved to {new_position}")
        self.logger.info(f"Moved to position {new_position}")

        # Update knowledge about whether position is in drop zone
        is_drop_zone = new_position[0] == (self.knowledge["zone_type"] * 3 + 2)
        self.knowledge["in_drop_zone"] = is_drop_zone
        if is_drop_zone:
            self.logger.info("Entered drop zone")

    def pick_waste(self):
        """
        Pick up waste at the drone's current position if conditions are met.
        Returns:
            bool: True if waste was picked up, False otherwise
        """
        wastes_at_position = [
            (waste_id, waste_pos)
            for waste_id, waste_pos in self.percepts["neighbor_wastes"]
        ]

        if wastes_at_position and self.knowledge["carried_waste_amount"] < 2:
            waste_id, _ = wastes_at_position[0]
            waste = self.model.get_agent_by_id(waste_id)
            self.logger.info(f"Found waste {waste_id}")

            if (
                waste.waste_color == self.knowledge["carried_waste_type"]
                or self.knowledge["carried_waste_type"] is None
            ) and waste.waste_color == self.knowledge["zone_type"]:
                self.knowledge["carried_waste_amount"] += waste.weight
                self.knowledge["carried_waste_type"] = waste.waste_color

                if waste.pos is None:
                    self.logger.warning(
                        f"Waste {waste_id} has no position, cannot pick up"
                    )
                    return False

                self.model.grid.remove_agent(waste)

                self.knowledge["actions"].append(f"picked waste {waste_id}")
                self.logger.info(f"Picked waste {waste.unique_id}")
                self.logger.info(
                    f"Now carrying {self.knowledge['carried_waste_amount']} waste of type {self.knowledge['carried_waste_type']}"
                )
                return True
            else:
                self.knowledge["can_pick"] = False
                self.logger.info(f"Cannot pick waste {waste_id} - incompatible type")

        self.logger.info("Did not pick any waste")
        return False

    def drop_waste(self):
        """
        Drop carried waste at the drone's current position.
        Returns:
            bool: True if waste was dropped, False otherwise
        """
        if self.knowledge["carried_waste_amount"] > 0:
            self.knowledge["carried_waste_amount"] -= 1

            if self.knowledge["carried_waste_amount"] == 0:
                self.knowledge["carried_waste_type"] = None
                self.logger.info("No more waste being carried")
            else:
                self.logger.info(
                    f"Still carrying {self.knowledge['carried_waste_amount']} waste"
                )

            new_waste = Waste(self.model, self.knowledge["zone_type"] + 1)
            self.model.add_agent(new_waste, self.pos)

            self.knowledge["actions"].append("dropped waste")
            self.logger.info(f"Dropped waste at {self.pos}")
            return True

        self.logger.info("No waste to drop")
        return False

    def update(self):
        """
        Update the drone's knowledge based on its current percepts and state.
        This method is called at the beginning of each step.
        """
        # Store current percepts in knowledge history
        self.knowledge["percepts"].append(self.percepts)
        # Reset actions for the new step
        self.knowledge["actions"] = []

        self.logger.info(f"Starting update at position {self.pos}")

        # Log percepts information
        self.logger.debug(f"Empty neighbors: {len(self.percepts['neighbors_empty'])}")
        self.logger.debug(f"Neighboring zones: {len(self.percepts['neighbor_zones'])}")
        self.logger.debug(
            f"Neighboring drones: {len(self.percepts['neighbor_drones'])}"
        )
        self.logger.debug(
            f"Neighboring wastes: {len(self.percepts['neighbor_wastes'])}"
        )

        # Update drop zone status based on current position
        # Check if the drone is in a drop zone (x-coordinate equals zone_type * 3 + 2)
        is_drop_zone = self.pos[0] == (self.knowledge["zone_type"] * 3 + 2)
        self.knowledge["in_drop_zone"] = is_drop_zone
        if is_drop_zone:
            self.logger.info("Currently in drop zone")

    def transform_waste(self):
        """
        Transform carried waste into processed waste.
        Sets the carried waste amount to 1 and updates the waste type.
        """
        prev_type = self.knowledge["carried_waste_type"]
        self.knowledge["carried_waste_amount"] = 1
        self.knowledge["carried_waste_type"] = self.knowledge["zone_type"] + 1
        self.knowledge["actions"].append("transformed waste")
        self.logger.info(
            f"Transformed waste from type {prev_type} to type {self.knowledge['carried_waste_type']}"
        )

    def deliberate(self):
        """
        Decide which action to take based on the drone's current knowledge and state.

        Returns:
            str: The action to take ("transform_waste", "drop_waste", "pick_waste", or "move")
        """
        self.logger.info("Deliberating on next action")

        # Priority 0: Transform waste if carrying maximum capacity
        if self.knowledge["carried_waste_amount"] == 2:
            self.logger.info("Decision: Transform waste (at max capacity)")
            return "transform_waste"

        # Priority 1: Drop waste if in drop zone and carrying waste of the correct type
        if (
            self.knowledge["in_drop_zone"]
            and self.knowledge["carried_waste_amount"] > 0
        ):
            self.logger.info("In drop zone with waste")
            if self.knowledge["carried_waste_type"] == (
                self.knowledge["zone_type"] + 1
            ):
                self.logger.info("Decision: Drop waste (in correct drop zone)")
                return "drop_waste"

        # Priority 2: Pick waste if at same position as compatible waste and has capacity
        filtered_wastes = []
        for waste_id, waste_pos in self.percepts["neighbor_wastes"]:
            waste = self.model.get_agent_by_id(waste_id)
            if (
                waste.waste_color == self.knowledge["carried_waste_type"]
                or self.knowledge["carried_waste_type"] is None
            ) and waste.waste_color == self.knowledge["zone_type"]:
                filtered_wastes.append(waste_id)

        if filtered_wastes:
            self.logger.info(f"Found {len(filtered_wastes)} compatible wastes nearby")

        if (
            filtered_wastes
            and self.knowledge["carried_waste_amount"] < 2
            and self.knowledge["can_pick"]
        ):
            self.logger.info("Decision: Pick waste")
            return "pick_waste"

        # Default action: Move randomly
        self.logger.info("Decision: Move (default action)")
        return "move"

    def step_agent(self):
        """
        Execute one step of the agent's behavior:
        1. Update knowledge
        2. Decide on an action
        3. Execute the action and update percepts
        """
        self.logger.info("Starting step")
        self.update()
        action = self.deliberate()
        self.percepts = self.model.do(self, action)
        self.logger.info("Finished step")
