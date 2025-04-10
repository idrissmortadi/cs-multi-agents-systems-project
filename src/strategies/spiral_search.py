import math
from strategies.base_strategy import BaseStrategy

# Directions map: 0: right, 1: down, 2: left, 3: up
DIRECTION_VECTORS = [(1, 0), (0, 1), (-1, 0), (0, -1)]


class SpiralSearch(BaseStrategy):
    """
    A strategy where the drone moves outwards in a spiral pattern when searching for waste.
    """

    def __init__(self, drone):
        """
        Initialize the SpiralSearch strategy.

        Requires 'spiral_state' and 'search_mode' to be initialized in drone.knowledge:
        knowledge['spiral_state'] = {'center': None, 'leg_length': 1, 'steps_on_leg': 0, 'direction_index': 0, 'legs_completed_of_length': 0}
        knowledge['search_mode'] = False
        """
        super().__init__(name="SpiralSearch", drone=drone)
        # Ensure required knowledge keys exist
        if "spiral_state" not in self.drone.knowledge:
            self.drone.knowledge["spiral_state"] = {
                "center": None,
                "leg_length": 1,
                "steps_on_leg": 0,
                "direction_index": 0,
                "legs_completed_of_length": 0,
            }
        if "search_mode" not in self.drone.knowledge:
            self.drone.knowledge["search_mode"] = False

    def _reset_spiral(self):
        """Resets the spiral state, centering on the current position."""
        self.drone.knowledge["spiral_state"] = {
            "center": self.drone.pos,
            "leg_length": 1,
            "steps_on_leg": 0,
            "direction_index": 0,  # 0: right, 1: down, 2: left, 3: up
            "legs_completed_of_length": 0,
        }
        self.drone.knowledge["search_mode"] = True
        self.drone.logger.info(f"Spiral search initiated/reset at {self.drone.pos}")

    def _get_next_spiral_pos(self):
        """Calculates the next target position in the spiral."""
        state = self.drone.knowledge["spiral_state"]
        if state["center"] is None:
            self._reset_spiral()  # Start spiral if not already started
            state = self.drone.knowledge["spiral_state"]

        dx, dy = DIRECTION_VECTORS[state["direction_index"]]
        next_pos = (self.drone.pos[0] + dx, self.drone.pos[1] + dy)
        return next_pos

    def _update_spiral_state(self):
        """Updates the spiral state after a step is taken."""
        state = self.drone.knowledge["spiral_state"]
        state["steps_on_leg"] += 1

        if state["steps_on_leg"] >= state["leg_length"]:
            state["steps_on_leg"] = 0
            state["direction_index"] = (state["direction_index"] + 1) % 4
            state["legs_completed_of_length"] += 1
            if (
                state["legs_completed_of_length"] >= 2
            ):  # Completed two legs of the same length
                state["legs_completed_of_length"] = 0
                state["leg_length"] += 1

    def execute(self):
        """Execute the Spiral Search strategy."""
        knowledge = self.drone.knowledge
        percepts = self.drone.percepts
        zone_type = knowledge["zone_type"]
        inventory = knowledge["inventory"]

        self.drone.logger.info("============DELIBERATION (SpiralSearch)=============")
        # ... (add logging similar to RandomWalk if desired)

        # === Standard Priorities (similar to RandomWalk) ===
        # Priority 0: Transform
        if len(inventory) == 2 and zone_type < 2:
            knowledge["search_mode"] = False  # Stop searching when transforming
            self.drone.logger.info("Decision: Transform waste")
            return "transform_waste"

        # Priority 1.1: Drop in Transfer Zone
        if (
            knowledge["in_transfer_zone"]
            and inventory
            and any(w.waste_color == zone_type + 1 for w in inventory)
        ):
            knowledge["search_mode"] = False
            self.drone.logger.info("Decision: Drop waste (transfer zone)")
            return "drop_waste"

        # Priority 1.2: Drop in Final Drop Zone (Red Drone)
        if (
            knowledge["in_drop_zone"]
            and inventory
            and zone_type == 2
            and any(w.waste_color == zone_type for w in inventory)
        ):
            knowledge["search_mode"] = False
            self.drone.logger.info("Decision: Drop waste (final drop zone)")
            return "drop_waste"

        # Priority 2: Move East if carrying processed waste (or if red drone carrying anything)
        should_move_east = knowledge.get("should_move_east", False)
        if inventory and (should_move_east or zone_type == 2):
            # Check if we are *already* at the transfer/drop zone before moving east again
            if (knowledge["in_transfer_zone"] and zone_type < 2) or (
                knowledge["in_drop_zone"] and zone_type == 2
            ):
                # Already at destination, don't force move east, let drop logic handle it
                pass
            else:
                knowledge["search_mode"] = False
                self.drone.logger.info(
                    "Decision: Move east (carrying processed/red waste)"
                )
                # Find valid eastward positions
                east_positions = [
                    pos
                    for pos in percepts["neighbors_empty"]
                    if pos[0] > self.drone.pos[0]
                ]
                if east_positions:
                    # NOTE: Ideally, move_east would target a specific valid cell.
                    # If multiple east cells exist, this might need smarter selection.
                    return "move_east"
                else:
                    # Blocked moving east, maybe move randomly or wait?
                    self.drone.logger.info("Blocked moving east, moving randomly")
                    return "move"  # Default move if blocked

        # Priority 3: Pick up compatible waste at current location
        compatible_wastes_here = [
            waste_id
            for waste_id, waste_pos in percepts["neighbor_wastes"]
            if waste_pos == self.drone.pos  # Ensure waste is AT the drone's pos
            and self.drone.model.get_agent_by_id(waste_id).waste_color == zone_type
        ]
        inventory_types = [w.waste_color for w in inventory]
        can_pickup_type = not inventory_types or zone_type in inventory_types

        if (
            compatible_wastes_here
            and len(inventory) < 2
            and knowledge["can_pick"]
            and can_pickup_type
        ):
            knowledge["search_mode"] = False  # Stop searching
            self.drone.logger.info("Decision: Pick waste")
            return "pick_waste"

        # === Spiral Search Logic ===
        if len(inventory) == 0:  # Only search if inventory is empty
            if (
                not knowledge["search_mode"]
                or knowledge["spiral_state"]["center"] is None
            ):
                self._reset_spiral()

            target_pos = self._get_next_spiral_pos()
            self.drone.logger.info(f"Spiral search: Target position {target_pos}")

            # Check if target_pos is valid (within grid and drone's allowed zones)
            grid = self.drone.model.grid
            if not grid.out_of_bounds(target_pos):
                target_zone = self.drone.model._get_zone(target_pos)
                # Allow moving within own zone, lower zones, or into the immediate transfer zone column
                is_valid_target_zone = (
                    target_zone and target_zone.zone_type <= zone_type
                ) or (
                    zone_type < 2
                    and target_pos[0]
                    == (zone_type + 1) * (knowledge["grid_width"] // 3) - 1
                )

                if is_valid_target_zone and target_pos in percepts["neighbors_empty"]:
                    # Update state *before* moving
                    self._update_spiral_state()
                    self.drone.logger.info("Decision: Move (following spiral)")
                    # *** TODO: Implement move_to(target_pos) in Drone/Environment ***
                    # For now, returning "move" relies on luck or Drone.move being modified.
                    return "move"  # Replace with move_to(target_pos) if implemented
                else:
                    # Target blocked or invalid - try to skip or reset spiral?
                    self.drone.logger.info(
                        f"Spiral target {target_pos} blocked/invalid. Skipping step/moving randomly."
                    )
                    # Option 1: Skip spiral step and try next on next tick (might lock)
                    # Option 2: Move randomly
                    knowledge["search_mode"] = False  # Temporarily stop spiral
                    return "move"  # Default random move
            else:
                # Spiral went out of bounds
                self.drone.logger.info("Spiral target out of bounds. Resetting spiral.")
                self._reset_spiral()  # Reset centered on current pos
                return "move"  # Default random move

        # Default Action: If inventory isn't empty but no other action applies, move randomly.
        self.drone.logger.info("Decision: Move (default random)")
        knowledge["search_mode"] = False  # Ensure search mode is off if we default here
        return "move"
