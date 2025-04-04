from strategies.base_strategy import BaseStrategy


class RandomWalk(BaseStrategy):
    """
    A strategy that implements a random walk for the drone agent.
    Once a drone collects two wastes, it will transform them.
    Then it will move east if it is a green or yellow drone.
    If it is a red drone, it will drop the waste in the drop zone.
    """

    def __init__(self, drone):
        """
        Initialize the strategy.

        :param drone: The drone agent using this strategy.
        """
        super().__init__(name="RandomWalk", drone=drone)

    def execute(self):
        """
        Deliberate on the next action for the drone agent.

        This method checks the current state of the drone and its environment,
        and decides on the next action to take based on a set of priorities.
        """

        # Log deliberation information
        self.drone.logger.info("============DELEBIRATION=============")
        self.drone.logger.info("Deliberating on next action")
        self.drone.logger.info(
            f"Current inventory: {self.drone.knowledge['inventory']}"
        )
        self.drone.logger.info(f"Can pick waste: {self.drone.knowledge['can_pick']}")
        self.drone.logger.info(
            f"Should move east: {self.drone.knowledge['should_move_east']}"
        )
        self.drone.logger.info(
            f"transfer zone status: {self.drone.knowledge['in_transfer_zone']}"
        )
        self.drone.logger.info(
            f"drop zone status: {self.drone.knowledge['in_drop_zone']}"
        )
        self.drone.logger.info(f"Zone type: {self.drone.knowledge['zone_type']}")
        self.drone.logger.info(f"Position: {self.drone.pos}")
        self.drone.logger.info("=====================================")

        # Priority 0: Transform if we are green robot or yellow robot and at max capacity
        if (
            len(self.drone.knowledge["inventory"]) == 2
            and self.drone.knowledge["zone_type"] < 2
        ):
            self.drone.logger.info("At max capacity")
            self.drone.logger.info("Decision: Transform waste (at max capacity)")
            return "transform_waste"
        elif (
            len(self.drone.knowledge["inventory"]) < 2
            and self.drone.knowledge["inventory"]
        ):
            self.drone.logger.info("Not at max capacity")
        elif not self.drone.knowledge["inventory"]:
            self.drone.logger.info("Inventory is empty")
        # ==========================================================================

        # Priority 1.1: Drop waste if in transfer zone and carrying processed waste
        if (
            self.drone.knowledge["in_transfer_zone"]
            and self.drone.knowledge["inventory"]
        ):
            self.drone.logger.info("In transfer zone with waste")

            # Check if waste is of the correct processed type
            if any(
                waste.waste_color == (self.drone.knowledge["zone_type"] + 1)
                for waste in self.drone.knowledge["inventory"]
            ):
                self.drone.logger.info(
                    "Decision: Drop waste (in correct transfer zone)"
                )
                return "drop_waste"
            else:
                self.drone.logger.info("Cannot drop waste")

        # Priority 1.2: if red drone and in drop zone, drop waste
        if (
            self.drone.knowledge["in_drop_zone"]
            and self.drone.knowledge["inventory"]
            and self.drone.knowledge["zone_type"] == 2
        ):
            self.drone.logger.info("In drop zone with waste")

            # Check if waste is of the correct processed type
            if any(
                waste.waste_color == self.drone.knowledge["zone_type"]
                for waste in self.drone.knowledge["inventory"]
            ):
                self.drone.logger.info("Decision: Drop waste (in drop zone)")
                return "drop_waste"
            else:
                self.drone.logger.info("Cannot drop waste")
        # ==========================================================================

        # Priority 1: Move east after transforming waste or if we should move east
        if (
            self.drone.knowledge["should_move_east"]
            and self.drone.knowledge["inventory"]
        ):
            self.drone.logger.info("Decision: Move east (after transformation)")
            return "move_east"
        # ============================================================================

        # Priority 2: Pick waste if at same position as compatible waste and has capacity
        compatible_wastes = []
        inventory_types = [w.waste_color for w in self.drone.knowledge["inventory"]]
        self.drone.logger.info(f"Inventory types: {inventory_types}")
        for waste_id, waste_pos in self.drone.percepts["neighbor_wastes"]:
            waste = self.drone.model.get_agent_by_id(waste_id)

            # Check if waste type is compatible with current inventory
            if (
                (not inventory_types or waste.waste_color in inventory_types)
                and waste.waste_color == self.drone.knowledge["zone_type"]
                and waste_pos[0] != self.drone.knowledge["grid_width"] - 1
            ):
                compatible_wastes.append(waste_id)

        if compatible_wastes:
            self.drone.logger.info(
                f"Found {len(compatible_wastes)} compatible wastes nearby"
            )

        if (
            compatible_wastes
            and len(self.drone.knowledge["inventory"]) < 2
            and self.drone.knowledge["can_pick"]
        ):
            self.drone.logger.info("Decision: Pick waste")
            return "pick_waste"
        elif not self.drone.knowledge["can_pick"]:
            self.drone.logger.info("Cannot pick waste")
        # ==========================================================================

        # If red drone and have any waste in inventory, move east
        if (
            self.drone.knowledge["zone_type"] == 2
            and self.drone.knowledge["inventory"]
            and not self.drone.knowledge["should_move_east"]
        ):
            self.drone.logger.info("Decision: Move east (red drone with waste)")
            return "move_east"

        # Default action: Move randomly
        self.drone.logger.info("Decision: Move (default action)")
        return "move"
