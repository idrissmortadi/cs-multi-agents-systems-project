import logging
import os
import random
from dataclasses import dataclass, field
from functools import wraps
from typing import Dict, List, Optional, Set, Tuple

from communication import CommunicatingAgent, MessagePerformative
from objects import Waste

# Set random seed for reproducibility
random.seed(42)

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def cleanup_logger(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get logger name
        logger_name = f"agent_{self.unique_id}"

        # Clean up existing logger if it exists
        if logger_name in logging.Logger.manager.loggerDict:
            existing_logger = logging.getLogger(logger_name)
            # Close and remove all handlers
            for handler in list(existing_logger.handlers):
                handler.close()
                existing_logger.removeHandler(handler)
            # Remove logger from manager
            del logging.Logger.manager.loggerDict[logger_name]

        return func(self, *args, **kwargs)

    return wrapper


@dataclass
class DronePercepts:
    """Represents the percepts of a drone agent."""

    neighbors_empty: List[Tuple[int, int]] = field(default_factory=list)
    neighbor_zones: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    neighbor_drones: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    neighbor_wastes: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)

    def __str__(self):
        return (
            f"Percepts(\n"
            f"\tEmpty: {len(self.neighbors_empty)},\n"
            f"\tZones: {len(self.neighbor_zones)},\n"
            f"\tDrones: {len(self.neighbor_drones)},\n"
            f"\tWastes: {len(self.neighbor_wastes)}\n"
            f")"
        )

    def __repr__(self):
        # Use default dataclass repr for detailed representation
        return self.__str__()


@dataclass
class DroneKnowledge:
    """Represents the knowledge base of a drone agent."""

    inventory: List[Waste] = field(default_factory=list)
    can_pick: bool = True
    should_move_east: bool = False
    actions: List[str] = field(default_factory=list)
    percepts: List[DronePercepts] = field(default_factory=list)
    grid_width: int = 0
    grid_height: int = 0
    zone_type: int = 0
    in_transfer_zone: bool = False
    in_drop_zone: bool = False
    collective_waste_memory: Set[Tuple[int, Tuple[int, int]]] = field(
        default_factory=set
    )
    target_pos: Optional[Tuple[int, int]] = None
    current_state: Optional[str] = None
    visited_positions: Dict[Tuple[int, int], int] = field(default_factory=dict)

    def __str__(self):
        inventory_str = [
            f"Waste(id={w.unique_id}, color={w.waste_color})" for w in self.inventory
        ]
        memory_str = [
            f"Color: {color}, Position: {pos}"
            for color, pos in self.collective_waste_memory
        ]
        return (
            f"Knowledge(\n"
            f"\tZone: {self.zone_type},\n"
            f"\tState: {self.current_state},\n"
            f"\tInventory: {inventory_str},\n"
            f"\tTarget: {self.target_pos},\n"
            f"\tMemory: {memory_str},\n"
            f"\tCanPick: {self.can_pick},\n"
            f"\tMoveEast: {self.should_move_east},\n"
            f"\tInTransferZone: {self.in_transfer_zone},\n"
            f"\tInDropZone: {self.in_drop_zone},\n"
            f"\tActions: {self.actions},\n"
            f"\tVisitedCount: {len(self.visited_positions)}\n"  # Add visited count for brevity
            f")"
        )

    def __repr__(self):
        # Use default dataclass repr or a slightly more detailed one if needed
        # For now, let's make it the same as __str__ for simplicity in logs
        return self.__str__()


class Drone(CommunicatingAgent):
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
        super().__init__(model, name=f"Drone_{id(self)}_{zone_type}")
        self.zone_type = zone_type  # Keep zone_type directly accessible if needed

        # Setup individual agent logger
        self._setup_logger()

        self.logger.info(
            f"Initializing drone {self.unique_id} with zone type {zone_type}"
        )

        # Initialize percepts using the dataclass
        self.percepts = DronePercepts()

        # Initialize knowledge using the dataclass
        self.knowledge = DroneKnowledge(
            grid_width=self.model.grid.width,
            grid_height=self.model.grid.height,
            zone_type=zone_type,
        )

    @cleanup_logger
    def _setup_logger(self):
        """Set up individual logging for this drone"""
        logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        agents_dir = os.path.join(logs_dir, "agents")
        os.makedirs(agents_dir, exist_ok=True)

        self.logger = logging.getLogger(f"agent_{self.unique_id}")
        self.logger.setLevel(logging.INFO)

        # Create new file handler
        log_file = os.path.join(agents_dir, f"agent_{self.unique_id}.log")
        file_handler = logging.FileHandler(log_file, mode="w")
        formatter = logging.Formatter(
            "[%(asctime)s] [AGENT %(name)s] [%(levelname)s] [ZONE %(zone_type)s] %(message)s",
            defaults={"zone_type": self.zone_type},
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def move_randomly(self):
        """
        Move the drone to a new position chosen randomly from available empty neighbors.
        If no empty neighbors are available, the drone stays in place.
        Updates the drone's knowledge after moving.
        """
        # Choose a new position randomly from available empty neighbors or stay in place
        new_position = self.pos  # Default to staying in place

        if not self.percepts.neighbors_empty:
            self.logger.info("MOVEMENT: No empty neighbors available, staying in place")
            return

        # Get visit counts for neighbors, default to 0 if not visited
        neighbor_visits = {
            n_pos: self.knowledge.visited_positions.get(n_pos, 0)
            for n_pos in self.percepts.neighbors_empty
        }

        # Find the minimum visit count
        min_visits = min(neighbor_visits.values())

        # Get all neighbors with the minimum visit count
        least_visited_neighbors = [
            n_pos for n_pos, visits in neighbor_visits.items() if visits == min_visits
        ]

        self.logger.info(
            f"MOVEMENT: Found {len(least_visited_neighbors)} least visited neighbors (visit count: {min_visits})"
        )

        # Choose randomly among the least visited neighbors
        new_position = random.choice(least_visited_neighbors)

        if new_position != self.pos:
            # Reset can_pick when moving to a new position
            self.knowledge.can_pick = True
            self.logger.info("SEARCH: Reset can_pick flag after moving")
            self.logger.info(f"MOVEMENT: Moving from {self.pos} to {new_position}")
        else:
            self.logger.info("MOVEMENT: Staying in current position")

        # Move the agent to the new position
        self.model.grid.move_agent(self, new_position)

        # Update visit count for the new position
        previous_visits = self.knowledge.visited_positions.get(self.pos, 0)
        self.knowledge.visited_positions[self.pos] = previous_visits + 1

        # Update knowledge about position
        self.knowledge.actions.append(f"moved to {new_position}")
        self.logger.info(
            f"SEARCH: Position {self.pos} now visited {self.knowledge.visited_positions[self.pos]} time(s)"
        )

    def move_east(self):
        """
        Move the drone to the east (increasing x-coordinate).
        If no empty positions to the east are available, the drone stays in place.
        Updates the drone's knowledge after moving.
        """
        # Look for empty positions to the east
        east_positions = [
            pos for pos in self.percepts.neighbors_empty if pos[0] > self.pos[0]
        ]

        # If there are positions to the east, move to the first one; otherwise, stay in place
        if east_positions:
            new_position = east_positions[0]
        else:
            new_position = self.pos
            self.logger.info("No east positions available, staying in place")

        # If drone is actually moving to a new position (not staying in place)
        if new_position != self.pos:
            # Reset can_pick when moving to a new position
            self.knowledge.can_pick = True
            self.logger.info("Reset can_pick flag after moving east")

        # Move the agent to the new position
        self.model.grid.move_agent(self, new_position)

        # Update visit count for the new position
        self.knowledge.visited_positions[self.pos] = (
            self.knowledge.visited_positions.get(self.pos, 0) + 1
        )
        # Update knowledge about position
        self.knowledge.actions.append(f"moved east to {new_position}")
        self.logger.info(f"Moved east to position {new_position}")

    def step_towards_target(self):
        """
        Take a step towards the target position, prioritizing movement in the x direction first.
        """
        target_pos = self.knowledge.target_pos
        target_x, target_y = target_pos

        neighbor_positions = self.percepts.neighbors_empty

        if len(neighbor_positions) == 0:
            self.logger.info(
                "MOVEMENT: No empty neighbors available to move towards target"
            )
            return

        # Prioritize movement in the x direction first
        if self.pos[0] != target_x:
            # Filter neighbors with the closest x-coordinate to the target
            closest_x_neighbors = [
                pos for pos in neighbor_positions if pos[0] == target_x
            ]
            if closest_x_neighbors:
                self.logger.info("TARGETING: Aligning x-coordinate with target")
                new_position = min(
                    closest_x_neighbors,
                    key=lambda pos: abs(pos[1] - target_y),
                )
            else:
                # If no neighbors match the target x, move closer in x direction
                self.logger.info("TARGETING: Moving closer in x-direction")
                new_position = min(
                    neighbor_positions,
                    key=lambda pos: abs(pos[0] - target_x),
                )
        else:
            # If x-coordinate is aligned, move in the y direction
            self.logger.info("TARGETING: X-coordinate aligned, moving in y-direction")
            new_position = min(
                neighbor_positions,
                key=lambda pos: abs(pos[1] - target_y),
            )

        # Calculate Manhattan distance to target before and after move
        current_distance = abs(self.pos[0] - target_x) + abs(self.pos[1] - target_y)
        new_distance = abs(new_position[0] - target_x) + abs(new_position[1] - target_y)

        self.logger.info(f"TARGETING: Moving towards target {target_pos}")
        self.logger.info(f"MOVEMENT: From {self.pos} to {new_position}")
        self.logger.info(
            f"TARGETING: Distance to target: {current_distance} → {new_distance}"
        )

        # Execute the move
        self.model.grid.move_agent(self, new_position)

        # Update visit count for the new position
        self.knowledge.visited_positions[self.pos] = (
            self.knowledge.visited_positions.get(self.pos, 0) + 1
        )

        self.knowledge.actions.append(f"moved towards target {target_pos}")

    def pick_waste(self):
        """
        Pick up waste at the drone's current position if conditions are met.
        Sends a broadcast message upon successful pickup.
        Returns:
            bool: True if waste was picked up, False otherwise
        """
        wastes_at_position = [
            (waste_id, waste_pos)
            for waste_id, waste_pos in self.percepts.neighbor_wastes
            # if waste_pos == self.pos  # Ensure waste is at the current position
        ]

        if not wastes_at_position:
            self.logger.info("COLLECTION: No waste found at current position")
            return False

        if len(self.knowledge.inventory) >= 2:
            self.logger.info("COLLECTION: Inventory full, cannot pick waste")
            return False

        # At this point we have waste nearby and inventory space
        self.logger.info(
            f"COLLECTION: Found {len(wastes_at_position)} waste(s) nearby, checking compatibility"
        )

        # Look for compatible waste
        for waste_id, waste_pos in wastes_at_position:
            waste = self.model.get_agent_by_id(waste_id)
            inventory_types = [w.waste_color for w in self.knowledge.inventory]

            self.logger.info(
                f"COLLECTION: Checking waste {waste_id} (color {waste.waste_color}) at {waste_pos}"
            )
            self.logger.info(f"COLLECTION: Current inventory types: {inventory_types}")

            # Check if waste type is compatible with current inventory and drone's zone
            if waste.waste_color == self.knowledge.zone_type and (
                not inventory_types or waste.waste_color in inventory_types
            ):
                if waste.pos is not None:  # Ensure waste is actually on the grid
                    original_waste_color = waste.waste_color
                    waste_to_pick = waste.pos
                    self.logger.info(
                        f"COLLECTION: Waste {waste_id} is compatible, picking up"
                    )

                    self.model.grid.remove_agent(waste)  # Remove waste from grid
                    self.knowledge.inventory.append(waste)

                    self.knowledge.actions.append(f"picked waste {waste_id}")

                    # Memory management
                    self.logger.info(
                        f"COMMUNICATION: Broadcasting removal of waste {waste_id} at {waste_pos}"
                    )
                    self.send_broadcast_message(
                        MessagePerformative.INFORM_WASTE_POS_REMOVE_REF,
                        (original_waste_color, waste_to_pick),
                    )

                    # Remove from own collective memory
                    self.knowledge.collective_waste_memory.discard(
                        (original_waste_color, waste_to_pick)
                    )
                    self.logger.info(
                        f"MEMORY: Removed waste (color {original_waste_color}) at {waste_to_pick}"
                    )

                    # If this was a target waste, reset target
                    if self.knowledge.target_pos == waste_to_pick:
                        self.knowledge.target_pos = None
                        self.logger.info(
                            "TARGETING: Reset target position after pickup"
                        )

                    # Reset can_pick state
                    self.knowledge.can_pick = True

                    self.logger.info(
                        f"INVENTORY: Now carrying {len(self.knowledge.inventory)} item(s)"
                    )
                    return True
                else:
                    self.logger.warning(
                        f"COLLECTION: Waste {waste_id} has no position, cannot pick up"
                    )
            else:
                self.logger.info(
                    f"COLLECTION: Waste {waste_id} is incompatible (color {waste.waste_color} != zone {self.knowledge.zone_type})"
                )
                self.knowledge.can_pick = False  # Cannot pick this specific waste

        # If we got here, we didn't find any compatible waste to pick
        self.logger.info("COLLECTION: No compatible waste found to pick up")
        return False

    def drop_waste(self):
        """
        Drop a waste item from inventory at the drone's current position.
        Returns:
            bool: True if waste was dropped, False otherwise
        """
        # Get the processed waste type from inventory
        processed_waste = self.knowledge.inventory.pop(0)

        # Log waste info before dropping
        self.logger.info(
            f"DELIVERY: Dropping waste (ID: {processed_waste.unique_id}, color: {processed_waste.waste_color}) at {self.pos}"
        )

        # Processed waste should be of the same type as the zone type + 1 or 2
        assert (
            processed_waste.waste_color == self.knowledge.zone_type + 1
            or processed_waste.waste_color == 2
        ), (
            f"Processed waste type {processed_waste.waste_color} does not match zone type {self.knowledge.zone_type + 1}"
        )

        # Create a new waste object with the same type
        self.model.grid.place_agent(processed_waste, self.pos)

        # Broadcast to other agents
        self.logger.info(
            f"COMMUNICATION: Broadcasting new waste (ID: {processed_waste.unique_id}, color: {processed_waste.waste_color}) at {self.pos}"
        )
        self.send_broadcast_message(
            MessagePerformative.INFORM_WASTE_POS_ADD_REF,
            (processed_waste.waste_color, self.pos),
        )

        # Update knowledge
        self.knowledge.actions.append("dropped waste")

        # Update movement flags
        self.knowledge.should_move_east = False
        self.logger.info(
            "MOVEMENT: Setting should_move_east=False after dropping waste"
        )

        # Final status update
        self.logger.info(
            f"INVENTORY: Now carrying {len(self.knowledge.inventory)} items"
        )

        return True

    def update(self):
        """
        Update the drone's knowledge based on its current percepts and state.
        This method is called at the beginning of each step.
        """
        # Initialize current position info
        self.logger.info(f"Current position: {self.pos}")

        # Process mailbox messages
        new_messages = self.get_new_messages()
        if new_messages:
            self.logger.info(f"MAILBOX: Received {len(new_messages)} messages")
        else:
            self.logger.info("MAILBOX: No new messages")

        # Process and broadcast nearby wastes
        waste_count = len(self.percepts.neighbor_wastes)
        if waste_count > 0:
            self.logger.info(f"PERCEPTION: Detected {waste_count} waste(s) nearby")
            for waste_id, waste_pos in self.percepts.neighbor_wastes:
                waste = self.model.get_agent_by_id(waste_id)
                self.logger.info(
                    f"COMMUNICATION: Broadcasting waste {waste_id} (color {waste.waste_color}) at {waste_pos}"
                )
                self.send_broadcast_message(
                    MessagePerformative.INFORM_WASTE_POS_ADD_REF,
                    (waste.waste_color, waste_pos),
                )
                # Add to own collective memory if not already present
                self.knowledge.collective_waste_memory.add(
                    (waste.waste_color, waste_pos)
                )
        else:
            self.logger.info("PERCEPTION: No waste detected nearby")

        # Process received messages by type
        add_waste_messages = [
            m
            for m in new_messages
            if m.get_performative() == MessagePerformative.INFORM_WASTE_POS_ADD_REF
        ]
        delete_waste_messages = [
            m
            for m in new_messages
            if m.get_performative() == MessagePerformative.INFORM_WASTE_POS_REMOVE_REF
        ]

        # Update collective memory from ADD messages
        if add_waste_messages:
            self.logger.info(
                f"MEMORY: Processing {len(add_waste_messages)} ADD_WASTE messages"
            )
            for message in add_waste_messages:
                waste_color, waste_pos = message.get_content()
                self.knowledge.collective_waste_memory.add((waste_color, waste_pos))
                self.logger.info(
                    f"MEMORY: Added waste (color {waste_color}) at {waste_pos}"
                )

        # Update collective memory from DELETE messages
        if delete_waste_messages:
            self.logger.info(
                f"MEMORY: Processing {len(delete_waste_messages)} DELETE_WASTE messages"
            )
            for message in delete_waste_messages:
                waste_color, waste_pos = message.get_content()
                self.knowledge.collective_waste_memory.discard((waste_color, waste_pos))
                self.logger.info(
                    f"MEMORY: Removed waste (color {waste_color}) at {waste_pos}"
                )

        # Target assignment logic
        compatible_wastes = [
            wp
            for wp in self.knowledge.collective_waste_memory
            if wp[0] == self.zone_type and not self.in_drop_zone(wp[1])
        ]

        self.logger.info(f"MEMORY: Known compatible wastes: {len(compatible_wastes)}")

        if compatible_wastes and not self.knowledge.target_pos:
            # Assign closest waste as target
            closest_waste = min(
                compatible_wastes,
                key=lambda wp: (
                    abs(wp[1][0] - self.pos[0]) + abs(wp[1][1] - self.pos[1])
                ),
            )
            self.knowledge.target_pos = closest_waste[1]
            self.logger.info(
                f"TARGETING: Assigned new target at {self.knowledge.target_pos} (color {closest_waste[0]})"
            )
        elif not self.knowledge.collective_waste_memory:
            self.logger.info("TARGETING: No waste in memory, entering search mode")
            self.knowledge.target_pos = None
            self.knowledge.current_state = "searching"
        elif self.knowledge.target_pos:
            self.logger.info(
                f"TARGETING: Maintaining current target at {self.knowledge.target_pos}"
            )

        # Store percepts in history
        self.knowledge.percepts.append(self.percepts)

        # Zone position checks
        is_transfer_zone = (
            self.pos[0]
            == (self.knowledge.zone_type + 1) * (self.knowledge.grid_width // 3) - 1
            and self.pos[0] != self.knowledge.grid_width - 1
            and self.knowledge.zone_type < 2
        )
        is_drop_zone = (
            self.pos[0] == self.knowledge.grid_width - 1
            and self.knowledge.zone_type == 2
        )

        # Update zone knowledge
        self.knowledge.in_transfer_zone = is_transfer_zone
        self.knowledge.in_drop_zone = is_drop_zone

        if is_transfer_zone:
            self.logger.info("POSITION: Currently in transfer zone")
        if is_drop_zone:
            self.logger.info("POSITION: Currently in drop zone")

        # Special movement rules
        if self.knowledge.in_transfer_zone or self.knowledge.in_drop_zone:
            self.knowledge.should_move_east = False
            self.logger.info(
                "MOVEMENT: In special zone, setting should_move_east=False"
            )
        elif self.knowledge.zone_type == 2 and len(self.knowledge.inventory) > 0:
            self.knowledge.should_move_east = True
            self.logger.info(
                "MOVEMENT: Red zone drone with inventory, setting should_move_east=True"
            )

        # Log inventory state
        if self.knowledge.inventory:
            inventory_types = [w.waste_color for w in self.knowledge.inventory]
            self.logger.info(
                f"INVENTORY: Carrying {len(self.knowledge.inventory)} item(s) of type(s) {inventory_types}"
            )
        else:
            self.logger.info("INVENTORY: Empty")

        # Final memory state summary
        self.logger.info(
            f"MEMORY: Total items in collective memory: {len(self.knowledge.collective_waste_memory)}"
        )

    def transform_waste(self):
        """
        Transform all waste in the inventory into a single processed waste item.
        The processed waste type is one level higher than the zone type.
        """
        # Store information about what we're transforming for logging
        inventory_count = len(self.knowledge.inventory)
        waste_types = [w.waste_color for w in self.knowledge.inventory]
        waste_ids = [w.unique_id for w in self.knowledge.inventory]

        self.logger.info(
            f"TRANSFORM: Processing {inventory_count} waste items (IDs: {waste_ids}, types: {waste_types})"
        )

        # Clear the inventory and delete old wastes
        for waste in self.knowledge.inventory:
            del waste
        self.knowledge.inventory = []

        # Create one processed waste item and add it to inventory
        processed_waste = Waste(self.model, self.knowledge.zone_type + 1)
        self.knowledge.inventory.append(processed_waste)

        self.logger.info(
            f"TRANSFORM: Created new waste (ID: {processed_waste.unique_id}, type: {processed_waste.waste_color})"
        )

        # Move east after transforming
        self.knowledge.should_move_east = True
        self.logger.info(
            "MOVEMENT: Set should_move_east flag to True after transforming"
        )

        # Log the transformation action
        self.knowledge.actions.append("transformed waste")
        self.logger.info(
            f"ACTION: Transformed {inventory_count} waste items into type {processed_waste.waste_color}"
        )
        self.logger.info(
            f"INVENTORY: Now carrying 1 item of type {processed_waste.waste_color}"
        )

    def deliberate(self):
        """
        Deliberate on the next action for the drone agent based on the flowchart logic.
        This implements a stage-based decision-making process with the following priority:
        1. Drop waste if in appropriate zone
        2. Transform waste if inventory full
        3. Deliver waste by moving east if needed
        4. Pick waste if nearby
        5. Move to targeted waste
        6. Search by moving randomly
        """
        # Log knowledge information
        self.logger.info("============DELIBERATION STEP=============")
        self.logger.info(f"\tKnowledge: {self.knowledge}")
        self.logger.info(f"\tPosition: {self.pos}")
        self.logger.info("==========================================")

        # PRIORITY 1: DELIVERY - Check if we can drop waste in transfer zone or drop zone
        can_drop = (
            self.knowledge.in_transfer_zone
            and self.knowledge.zone_type < 2
            and self.knowledge.inventory
            and any(
                waste.waste_color == self.knowledge.zone_type + 1
                for waste in self.knowledge.inventory
            )
        ) or (
            self.knowledge.in_drop_zone
            and self.knowledge.inventory
            and all(waste.waste_color == 2 for waste in self.knowledge.inventory)
        )

        if can_drop:
            self.logger.info(
                f"DELIVERY STAGE: Dropping waste in {'transfer' if self.knowledge.in_transfer_zone else 'drop'} zone"
            )
            return "drop_waste"

        # PRIORITY 2: PROCESSING - Transform collected waste when inventory is full
        if (
            self.knowledge.inventory
            and len(self.knowledge.inventory) == 2
            and self.knowledge.zone_type < 2
        ):
            self.logger.info(
                "PROCESSING STAGE: Have 2 wastes in inventory, need to transform"
            )
            return "transform_waste"

        # PRIORITY 3: DELIVERY MOVEMENT - Move east with processed waste
        if self.knowledge.should_move_east and self.knowledge.inventory:
            self.logger.info("DELIVERY STAGE: Moving east with processed waste")
            return "move_east"

        # PRIORITY 4: COLLECTION - Pick waste if nearby and compatible
        can_pick = (
            len(self.knowledge.inventory) < 2
            and self.percepts.neighbor_wastes
            and self.knowledge.can_pick
            and any(
                not self.in_drop_zone(waste_pos)
                for _, waste_pos in self.percepts.neighbor_wastes
            )
        )

        if can_pick:
            # Check for compatible wastes nearby
            for waste_id, waste_pos in self.percepts.neighbor_wastes:
                waste = self.model.get_agent_by_id(waste_id)
                inventory_types = [w.waste_color for w in self.knowledge.inventory]

                # Check if waste is compatible with current inventory and drone type
                if waste.waste_color == self.knowledge.zone_type and (
                    not inventory_types or waste.waste_color in inventory_types
                ):
                    self.logger.info(
                        f"COLLECTION STAGE: Found compatible waste nearby at {waste_pos}"
                    )
                    return "pick_waste"

        # PRIORITY 5: TARGETED COLLECTION - Move towards target waste
        if self.knowledge.target_pos:
            # Check if we've reached our target
            if (
                abs(self.pos[0] - self.knowledge.target_pos[0]) == 0
                and abs(self.pos[1] - self.knowledge.target_pos[1]) == 0
            ):
                self.logger.info("COLLECTION STAGE: Reached target waste position")
                self.knowledge.target_pos = None

                # Discard from collective memory
                self.knowledge.collective_waste_memory.discard(
                    (self.knowledge.zone_type, self.pos)
                )
                self.logger.info(
                    f"Removed target waste {self.knowledge.zone_type} at {self.pos} from collective memory"
                )

                # Check if we can pick waste here (reuse logic from above)
                if can_pick:
                    return "pick_waste"
            else:
                # Verify target still exists in collective memory
                target_exists = any(
                    waste_pos == self.knowledge.target_pos
                    for _, waste_pos in self.knowledge.collective_waste_memory
                )

                if not target_exists:
                    self.logger.info(
                        "COLLECTION STAGE: Target waste no longer exists in memory, resetting target"
                    )
                    self.knowledge.target_pos = None
                else:
                    self.logger.info(
                        f"COLLECTION STAGE: Moving towards target at {self.knowledge.target_pos}"
                    )
                    return "step_towards_target"

        # PRIORITY 6: SEARCH - No specific task, search by moving randomly
        self.logger.info(
            "SEARCH STAGE: No waste found or targeted, moving randomly to search"
        )
        return "move_randomly"

    def step_agent(self):
        """
        Execute one step of the agent's behavior:
        1. Update knowledge
        2. Decide on an action
        3. Execute the action and update percepts
        """
        self.logger.info("======== STEP BEGIN ========")
        self.logger.info(
            f"Position: {self.pos} | Inventory: {len(self.knowledge.inventory)} items"
        )

        # Update phase
        self.logger.info("--- UPDATE PHASE ---")
        self.update()

        # Deliberation phase
        self.logger.info("--- DELIBERATION PHASE ---")
        action = self.deliberate()

        # Action phase
        self.logger.info(f"--- ACTION PHASE: {action.upper()} ---")
        percept_dict = self.model.do(self, action)
        self.percepts = DronePercepts(**percept_dict)

        self.logger.info(
            f"Step complete | Position: {self.pos} | Inventory: {len(self.knowledge.inventory)} items"
        )
        self.logger.info("======== STEP END ========\n")

    def in_drop_zone(self, pos):
        """Check if the position is in the drop zone."""
        if pos[0] == self.knowledge.grid_width - 1:
            return True
        return False

    def in_transfer_zone(self, pos):
        """Check if the position is in the transfer zone."""
        if (
            pos[0]
            == (self.knowledge.zone_type + 1) * (self.knowledge.grid_width // 3) - 1
            and pos[0] != self.knowledge.grid_width - 1
        ):
            return True
        return False
