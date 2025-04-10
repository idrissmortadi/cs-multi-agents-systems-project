from strategies.base_strategy import BaseStrategy


class GridScan(BaseStrategy):
    """
    A strategy where the drone systematically scans its zone row by row (or column by column).
    This example scans row by row, moving right, then down, then left, etc.
    """

    def __init__(self, drone):
        """
        Initialize the GridScan strategy.

        Requires 'scan_state' and 'search_mode' to be initialized in drone.knowledge:
        knowledge['scan_state'] = {'target_pos': None, 'direction': 'right', 'zone_bounds': None}
        knowledge['search_mode'] = False
        """
        super().__init__(name="GridScan", drone=drone)
        if "scan_state" not in self.drone.knowledge:
            self.drone.knowledge["scan_state"] = {
                "target_pos": None,
                "direction": "right",
                "zone_bounds": None,
            }
        if "search_mode" not in self.drone.knowledge:
            self.drone.knowledge["search_mode"] = False

        # Calculate zone boundaries once
        if self.drone.knowledge["scan_state"]["zone_bounds"] is None:
            zone_type = self.drone.knowledge["zone_type"]
            grid_width = self.drone.knowledge["grid_width"]
            grid_height = self.drone.knowledge["grid_height"]
            zone_width = grid_width // 3
            min_x = zone_type * zone_width
            max_x = (zone_type + 1) * zone_width - 1
            # Red drones should not scan the final drop column initially
            if zone_type == 2:
                max_x = grid_width - 2

            self.drone.knowledge["scan_state"]["zone_bounds"] = {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": 0,
                "max_y": grid_height - 1,
            }
            self.drone.knowledge["scan_state"]["target_pos"] = (
                min_x,
                0,
            )  # Start top-left

    def _get_next_scan_pos(self):
        """Calculates the next target position based on the scan pattern."""
        state = self.drone.knowledge["scan_state"]
        bounds = state["zone_bounds"]
        current_x, current_y = self.drone.pos  # Use current position as reference

        target_x, target_y = state.get("target_pos") or self.drone.pos

        # If drone reached target or no target, find next
        if self.drone.pos == state["target_pos"] or state["target_pos"] is None:
            direction = state["direction"]
            new_target_x, new_target_y = current_x, current_y

            if direction == "right":
                if current_x < bounds["max_x"]:
                    new_target_x += 1
                else:  # Hit right boundary, move down, change direction
                    new_target_y += 1
                    state["direction"] = "left"
            elif direction == "left":
                if current_x > bounds["min_x"]:
                    new_target_x -= 1
                else:  # Hit left boundary, move down, change direction
                    new_target_y += 1
                    state["direction"] = "right"

            # Check if scan finished (moved past bottom boundary)
            if new_target_y > bounds["max_y"]:
                self.drone.logger.info("Grid scan completed zone. Restarting.")
                new_target_x, new_target_y = (
                    bounds["min_x"],
                    bounds["min_y"],
                )  # Restart top-left
                state["direction"] = "right"

            state["target_pos"] = (new_target_x, new_target_y)
            self.drone.logger.info(
                f"New scan target: {state['target_pos']}, Direction: {state['direction']}"
            )
            return state["target_pos"]
        else:
            # Still moving towards the existing target
            return state["target_pos"]

    def execute(self):
        """Execute the GridScan strategy."""
        knowledge = self.drone.knowledge
        percepts = self.drone.percepts
        zone_type = knowledge["zone_type"]
        inventory = knowledge["inventory"]

        self.drone.logger.info("============DELIBERATION (GridScan)=============")
        # ... (logging)

        # === Standard Priorities ===
        # (Identical to SpiralSearch's Priority 0, 1.1, 1.2, 2 - Transform, Drop, Move East)
        if len(inventory) == 2 and zone_type < 2:
            knowledge["search_mode"] = False
            return "transform_waste"
        if (
            knowledge["in_transfer_zone"]
            and inventory
            and any(w.waste_color == zone_type + 1 for w in inventory)
        ):
            knowledge["search_mode"] = False
            return "drop_waste"
        if (
            knowledge["in_drop_zone"]
            and inventory
            and zone_type == 2
            and any(w.waste_color == zone_type for w in inventory)
        ):
            knowledge["search_mode"] = False
            return "drop_waste"

        should_move_east = knowledge.get("should_move_east", False)
        if inventory and (should_move_east or zone_type == 2):
            if not (
                (knowledge["in_transfer_zone"] and zone_type < 2)
                or (knowledge["in_drop_zone"] and zone_type == 2)
            ):
                knowledge["search_mode"] = False
                east_positions = [
                    pos
                    for pos in percepts["neighbors_empty"]
                    if pos[0] > self.drone.pos[0]
                ]
                if east_positions:
                    return "move_east"
                else:
                    self.drone.logger.info("Blocked moving east, moving randomly")
                    return "move"

        # Priority 3: Pick up compatible waste at current location
        compatible_wastes_here = [
            waste_id
            for waste_id, waste_pos in percepts["neighbor_wastes"]
            if waste_pos == self.drone.pos
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

        # === Grid Scan Logic ===
        # Start searching if idle (empty inventory)
        if len(inventory) == 0:
            knowledge["search_mode"] = True
            target_pos = self._get_next_scan_pos()

            if target_pos == self.drone.pos:
                # Already at target, or target calculation failed? Get next immediately.
                target_pos = self._get_next_scan_pos()
                if (
                    target_pos == self.drone.pos
                ):  # Still same? Maybe stuck, move randomly
                    self.drone.logger.warning("Scan seems stuck. Moving randomly.")
                    knowledge["search_mode"] = False
                    return "move"

            # Determine move direction towards target
            dx = target_pos[0] - self.drone.pos[0]
            dy = target_pos[1] - self.drone.pos[1]

            # Prioritize horizontal then vertical movement (or vice versa)
            move_options = []
            if dx > 0:
                move_options.append((self.drone.pos[0] + 1, self.drone.pos[1]))  # Right
            if dx < 0:
                move_options.append((self.drone.pos[0] - 1, self.drone.pos[1]))  # Left
            if dy > 0:
                move_options.append((self.drone.pos[0], self.drone.pos[1] + 1))  # Down
            if dy < 0:
                move_options.append((self.drone.pos[0], self.drone.pos[1] - 1))  # Up

            # Find the first valid move option in the preferred direction
            next_move_pos = None
            for move in move_options:
                if move in percepts["neighbors_empty"]:
                    next_move_pos = move
                    break

            if next_move_pos:
                self.drone.logger.info(
                    f"Decision: Move towards scan target {target_pos}"
                )
                # *** TODO: Implement move_to(next_move_pos) in Drone/Environment ***
                return "move"  # Replace with move_to(next_move_pos) if implemented
            else:
                # Blocked moving towards target
                self.drone.logger.info(
                    f"Blocked moving towards scan target {target_pos}. Moving randomly."
                )
                # Keep target, but move randomly for now
                knowledge["search_mode"] = True  # Stay in search mode, target remains
                return "move"
        else:
            # Not searching (inventory not empty)
            knowledge["search_mode"] = False

        # Default Action:
        self.drone.logger.info("Decision: Move (default random)")
        knowledge["search_mode"] = False
        return "move"
