import random
from strategies.base_strategy import BaseStrategy
# Assuming Waste object has 'waste_color' and 'id' attributes
# Assuming drone.model.get_agent_by_id(id) returns the Waste agent


class EnhancedWalkSpiral(BaseStrategy):  # Renamed for clarity
    """
    An enhanced strategy using spiral search for exploration.
    Drones prioritize tasks: transforming, dropping, picking, and moving purposefully east.
    - Green/Yellow drones collect waste matching their zone type, transform when holding two.
    - After transforming or if Red drone transporting, they move east.
    - When idle (no other task applicable), the drone performs a spiral search pattern
      to explore the area systematically instead of moving randomly.
    - ASSUMES directional move actions ('move_north', 'move_south', etc.) exist.
    """

    def __init__(self, drone):
        """
        Initialize the strategy and spiral search state.

        :param drone: The drone agent using this strategy.
        """
        super().__init__(name="EnhancedWalkSpiral", drone=drone)

        # Spiral Search State Variables
        self.spiral_direction_index = 0  # 0: East, 1: North, 2: West, 3: South
        self.spiral_segment_length = 1  # Current length of the spiral arm
        self.spiral_steps_taken = 0  # Steps taken along the current arm
        self.spiral_turns_in_lap = (
            0  # Turns made in the current 'lap' (length increases after 2 turns)
        )

        # ASSUMPTION: Define the actions corresponding to directions
        # Ensure these action strings match what the environment expects!
        self.directions = ["move_east", "move_north", "move_west", "move_south"]

    def _get_spiral_move(self):
        """
        Determines the next move action based on the spiral search pattern state.
        Updates the spiral state for the next step.
        """
        # Determine the action for the *current* step based on state
        action = self.directions[self.spiral_direction_index]
        self.drone.logger.info(
            f"Decision: Spiral move {action} "
            f"(Step {self.spiral_steps_taken + 1}/{self.spiral_segment_length}, "
            f"Lap Turns {self.spiral_turns_in_lap})"
        )

        # --- Update state for the *next* step ---
        self.spiral_steps_taken += 1

        # Check if the current segment/arm is completed
        if self.spiral_steps_taken >= self.spiral_segment_length:
            self.spiral_steps_taken = 0  # Reset steps for the new segment
            # Turn to the next direction (E -> N -> W -> S -> E ...)
            self.spiral_direction_index = (self.spiral_direction_index + 1) % 4
            self.spiral_turns_in_lap += 1

            # After two turns, increase the segment length for the next lap
            if self.spiral_turns_in_lap >= 2:
                self.spiral_turns_in_lap = 0
                self.spiral_segment_length += 1
                self.drone.logger.info(
                    f"Spiral segment length increased to {self.spiral_segment_length}"
                )

        return action

    def execute(self):
        """
        Deliberate on the next action for the drone agent based on priorities.
        Uses spiral search as the default movement action.
        """
        # Log deliberation information (optional but good for debugging)
        # self.drone.logger.info("--- Deliberation ---")
        # ... add detailed logging if needed ...

        inventory = self.drone.knowledge["inventory"]
        zone_type = self.drone.knowledge["zone_type"]
        in_transfer_zone = self.drone.knowledge["in_transfer_zone"]
        in_drop_zone = self.drone.knowledge["in_drop_zone"]
        can_pick = self.drone.knowledge["can_pick"]
        should_move_east = self.drone.knowledge.get("should_move_east", False)

        # --- Decision Priorities ---

        # Priority 0: Transform waste
        if len(inventory) == 2 and zone_type < 2:
            self.drone.logger.info("Decision: Transform waste (at max capacity)")
            # Reset spiral state? Maybe not, continue spiral after transform/move east/drop cycle?
            # Or reset it so it starts a new spiral from its current location after the task cycle.
            # Let's NOT reset for now, it will resume spiral when idle again.
            return "transform_waste"

        # Priority 1: Drop waste
        if inventory:
            required_waste_type = zone_type + 1 if zone_type < 2 else zone_type
            has_correct_waste_to_drop = any(
                waste.waste_color == required_waste_type for waste in inventory
            )

            if has_correct_waste_to_drop:
                if zone_type < 2 and in_transfer_zone:
                    self.drone.logger.info(
                        f"Decision: Drop waste (Type {required_waste_type} in Transfer Zone)"
                    )
                    return "drop_waste"
                elif zone_type == 2 and in_drop_zone:
                    self.drone.logger.info(
                        f"Decision: Drop waste (Type {required_waste_type} in Drop Zone)"
                    )
                    return "drop_waste"

        # Priority 2: Move East (Purposeful)
        if inventory:
            move_east_needed = False
            log_reason = ""
            if should_move_east:
                move_east_needed = True
                log_reason = "(post-transform flag)"
            elif zone_type == 2 and not in_drop_zone:
                move_east_needed = True
                log_reason = "(Red drone transporting)"
            elif (
                zone_type < 2
                and any(w.waste_color == zone_type + 1 for w in inventory)
                and not in_transfer_zone
            ):
                move_east_needed = True
                log_reason = "(Green/Yellow transporting)"

            if move_east_needed:
                self.drone.logger.info(f"Decision: Move east {log_reason}")
                # When moving east purposefully, we interrupt the spiral.
                # The spiral state remains as is and will resume when idle.
                return "move_east"

        # Priority 3: Pick up compatible waste
        if len(inventory) < 2:
            compatible_wastes_at_location = []
            # Use get() for safer access to percepts
            for waste_id, waste_pos in self.drone.percepts.get("neighbor_wastes", []):
                if (
                    waste_pos == self.drone.pos
                ):  # Check if waste is at the same location
                    try:
                        waste = self.drone.model.get_agent_by_id(waste_id)
                        if waste and waste.waste_color == zone_type:
                            # Check boundary condition for picking (optional, depends on rules)
                            # is_last_column = waste_pos[0] == self.drone.knowledge["grid_width"] - 1
                            # if not is_last_column or zone_type == 2:
                            compatible_wastes_at_location.append(waste_id)
                    except Exception as e:
                        self.drone.logger.warning(
                            f"Could not get agent {waste_id}: {e}"
                        )
                        continue

            # Check can_pick flag from knowledge, assumes it means waste is present AND drone can execute pick
            if compatible_wastes_at_location and can_pick:
                self.drone.logger.info(
                    f"Decision: Pick waste (Type {zone_type} at current location)"
                )
                # Picking interrupts spiral; state is preserved for later.
                return "pick_waste"

        # Priority 4 / Default Action: Perform Spiral Search Move
        # This is executed if no higher priority action was taken
        # self.drone.logger.info("No high-priority action; performing spiral search move.")
        return self._get_spiral_move()
