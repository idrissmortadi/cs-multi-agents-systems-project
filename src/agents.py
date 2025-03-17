import random

from mesa import Agent


class Drone(Agent):
    def __init__(self, model, zone_type):
        super().__init__(model)
        self.percepts = {
            "neighbors_empty": [],  # [(x, y), ...] in correponding zone color
            "neighbor_zones": [],  # [(zone_type, zone_pos), ...]
            "neighbor_drones": [],  # [(drone_id, drone_pos), ...]
            "neighbor_wastes": [],  # [(waste_id, waste_pos), ...]
        }
        self.knowledge = {
            "carried_waste_type": None,
            "carried_waste_amount": 0,
            "actions": [],
            "percepts": [],
            "grid_width": self.model.grid.width,
            "grid_height": self.model.grid.height,
            "zone_type": zone_type,
            "in_drop_zone": False,  # Whether drone is in a drop zone
        }

    def move(self):
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

        # Update knowledge about whether position is in drop zone
        is_drop_zone = (
            new_position[0] % (self.knowledge["grid_width"] // 3) == 0
            and new_position[0] != 0
        )
        self.knowledge["in_drop_zone"] = is_drop_zone

    def pick_waste(self):
        # Find wastes at current position
        wastes_at_position = [
            (waste_id, waste_pos)
            for waste_id, waste_pos in self.percepts["neighbor_wastes"]
            if waste_pos == self.pos
        ]

        if wastes_at_position and self.knowledge["carried_waste_amount"] < 2:
            waste_id, _ = wastes_at_position[0]  # Get the first waste
            waste = self.model.get_agent_by_id(waste_id)
            if waste:
                self.knowledge["carried_waste_amount"] += waste.weight
                self.model.grid.remove_agent(waste)
                self.knowledge["actions"].append(f"picked waste {waste_id}")
                print(f"Drone {self.unique_id} picked waste {waste.unique_id}")
                return True
        return False

    def drop_waste(self):
        # Only execute if carrying waste
        if self.knowledge["carried_waste_amount"] > 0:
            self.max_weight = 2  # Reset to full capacity
            self.knowledge["carried_waste_amount"] = 0
            self.knowledge["actions"].append("dropped waste")
            print(f"Drone {self.unique_id} dropped all waste")
            return True
        return False

    def update(self):
        self.knowledge["percepts"].append(self.percepts)
        self.knowledge["actions"] = []

        # Update drop zone status based on current position
        is_drop_zone = (
            self.pos[0] % (self.knowledge["grid_width"] // 3) == 0 and self.pos[0] != 0
        )
        self.knowledge["in_drop_zone"] = is_drop_zone

    def transform_waste(self):
        self.knowledge["carried_waste_amount"] = 1
        self.knowledge["carried_waste_type"] = self.knowledge["zone_type"] + 1
        self.knowledge["actions"].append("transformed waste")

    def deleberate(self):
        if self.knowledge["carried_waste_amount"] == 2:
            return "transform_waste"
        # First priority: Drop waste if in drop zone and carrying waste
        if (
            self.knowledge["in_drop_zone"]
            and self.knowledge["carried_waste_amount"] > 0
        ):
            if self.knowledge["carried_waste_type"] == self.knowledge["zone_type"] + 1:
                return "drop_waste"

        # Second priority: Pick waste if at same position as waste and has capacity
        for _, waste_pos in self.percepts["neighbor_wastes"]:
            if waste_pos == self.pos:
                return "pick_waste"

        # Default action: Move
        return "move"

    def step_agent(self):
        self.update()
        action = self.deleberate()
        self.percepts = self.model.do(self, action)
