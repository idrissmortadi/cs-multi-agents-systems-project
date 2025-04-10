import random
from strategies.base_strategy import BaseStrategy

# How long to remember waste locations (in steps)
WASTE_MEMORY_DURATION = 20


class MemoryRandomWalk(BaseStrategy):
    """
    A RandomWalk strategy enhanced with memory.
    - Remembers visited cells to avoid redundant exploration.
    - Remembers recently seen waste locations.
    """

    def __init__(self, drone):
        """
        Initialize the MemoryRandomWalk strategy.

        Requires 'visited_cells' and 'waste_memory' in drone.knowledge:
        knowledge['visited_cells'] = set()
        knowledge['waste_memory'] = {} # {pos: timestamp, ...}
        """
        super().__init__(name="MemoryRandomWalk", drone=drone)
        if "visited_cells" not in self.drone.knowledge:
            self.drone.knowledge["visited_cells"] = set()
        if "waste_memory" not in self.drone.knowledge:
            self.drone.knowledge["waste_memory"] = {}  # Stores pos: timestamp

    def _update_memory(self):
        """Updates visited cells and waste memory based on current percepts."""
        knowledge = self.drone.knowledge
        percepts = self.drone.percepts
        current_step = self.drone.model.steps  # Assuming model tracks steps

        # Add current position to visited
        knowledge["visited_cells"].add(self.drone.pos)

        # Prune old waste memory
        expired_waste = [
            pos
            for pos, timestamp in knowledge["waste_memory"].items()
            if current_step - timestamp > WASTE_MEMORY_DURATION
        ]
        for pos in expired_waste:
            del knowledge["waste_memory"][pos]

        # Add newly perceived waste to memory if we can't pick it up now
        can_pickup_now = len(knowledge["inventory"]) < 2 and knowledge["can_pick"]
        if not can_pickup_now:
            for waste_id, waste_pos in percepts["neighbor_wastes"]:
                waste = self.drone.model.get_agent_by_id(waste_id)
                # Only remember compatible waste in our zone
                if waste.waste_color == knowledge["zone_type"]:
                    if waste_pos not in knowledge["waste_memory"]:
                        self.drone.logger.info(f"Remembering waste at {waste_pos}")
                    knowledge["waste_memory"][waste_pos] = current_step

        # If we just picked waste, remove it from memory
        last_action = knowledge.get("actions", [])
        if last_action and last_action[-1].startswith("picked waste"):
            if self.drone.pos in knowledge["waste_memory"]:
                self.drone.logger.info(f"Forgetting picked waste at {self.drone.pos}")
                del knowledge["waste_memory"][self.drone.pos]

    def execute(self):
        """Execute the MemoryRandomWalk strategy."""
        knowledge = self.drone.knowledge
        percepts = self.drone.percepts
        zone_type = knowledge["zone_type"]
        inventory = knowledge["inventory"]

        # Update memory based on current state and percepts
        self._update_memory()

        self.drone.logger.info(
            "============DELIBERATION (MemoryRandomWalk)============="
        )
        self.drone.logger.info(
            f"Visited cells count: {len(knowledge['visited_cells'])}"
        )
        self.drone.logger.info(f"Waste memory count: {len(knowledge['waste_memory'])}")
        # ... (other logging)

        # === Standard Priorities ===
        # (Identical to SpiralSearch's Priority 0, 1.1, 1.2, 2 - Transform, Drop, Move East)
        if len(inventory) == 2 and zone_type < 2:
            return "transform_waste"
        if (
            knowledge["in_transfer_zone"]
            and inventory
            and any(w.waste_color == zone_type + 1 for w in inventory)
        ):
            return "drop_waste"
        if (
            knowledge["in_drop_zone"]
            and inventory
            and zone_type == 2
            and any(w.waste_color == zone_type for w in inventory)
        ):
            return "drop_waste"

        should_move_east = knowledge.get("should_move_east", False)
        if inventory and (should_move_east or zone_type == 2):
            if not (
                (knowledge["in_transfer_zone"] and zone_type < 2)
                or (knowledge["in_drop_zone"] and zone_type == 2)
            ):
                east_positions = [
                    pos
                    for pos in percepts["neighbors_empty"]
                    if pos[0] > self.drone.pos[0]
                ]
                if east_positions:
                    return "move_east"
                else:
                    self.drone.logger.info("Blocked moving east, moving randomly")
                    # Fall through to memory-based move

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
            self.drone.logger.info("Decision: Pick waste")
            return "pick_waste"

        # === Memory-Enhanced Movement ===
        # If not doing a priority action, decide where to move
        empty_neighbors = percepts["neighbors_empty"]
        if not empty_neighbors:
            self.drone.logger.info("No empty neighbors, staying put.")
            return (
                "move"  # Will effectively do nothing if move() requires empty neighbors
            )

        # 1. Prioritize moving towards remembered waste locations nearby
        potential_moves = []
        for pos in empty_neighbors:
            if pos in knowledge["waste_memory"]:
                self.drone.logger.info(
                    f"Prioritizing move towards remembered waste at {pos}"
                )
                potential_moves.append(pos)

        if potential_moves:
            # Move towards one of the remembered locations
            target_pos = random.choice(potential_moves)

            self.drone.logger.info(
                f"Decision: Move towards remembered waste at {target_pos}"
            )
            return ("move_to", target_pos)

        # 2. Prioritize moving towards unvisited neighbors
        unvisited_neighbors = [
            pos for pos in empty_neighbors if pos not in knowledge["visited_cells"]
        ]
        if unvisited_neighbors:
            target_pos = random.choice(unvisited_neighbors)

            self.drone.logger.info(
                f"Decision: Move towards unvisited neighbor {target_pos}"
            )
            return ("move_to", target_pos)

        # 3. If all neighbors visited and no waste memory, move randomly among neighbors
        self.drone.logger.info("All neighbors visited, moving randomly.")
        # target_pos = random.choice(empty_neighbors) # RandomWalk 'move' already does this
        return "move"
