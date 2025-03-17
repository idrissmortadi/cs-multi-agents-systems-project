import random

from mesa import Agent


class Drone(Agent):
    def __init__(self, model, zone_type):
        super().__init__(model)
        self.max_weight = 2
        self.carrying_waste = 0  # Track how much waste the drone is carrying
        self.percepts = {
            "neighbors_empty": [],  # [(x, y), ...] in correponding zone color
            "neighbor_zones": [],  # [(zone_type, zone_pos), ...]
            "neighbor_drones": [],  # [(drone_id, drone_pos), ...]
            "neighbor_wastes": [],  # [(waste_id, waste_pos), ...]
        }
        self.knowledge = {
            "actions": [],
            "percepts": [],
            "grid_width": self.model.grid.width,
            "grid_height": self.model.grid.height,
            "zone_type": zone_type,
            "carrying_waste": 0,  # Track amount of waste being carried
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

        # Check if in drop zone (assuming zone boundaries are at grid_width//3 intervals)
        is_drop_zone = (
            new_position[0] % (self.knowledge["grid_width"] // 3) == 0
            and new_position[0] != 0
        )
        self.knowledge["in_drop_zone"] = is_drop_zone

        # Drop waste if in drop zone and carrying any
        if is_drop_zone and self.knowledge["carrying_waste"] > 0:
            self.drop_waste()
            self.knowledge["actions"].append("dropped waste")

        # Check for waste at new position by examining percepts
        for waste_id, waste_pos in self.percepts["neighbor_wastes"]:
            if waste_pos == self.pos:  # If waste is at current position
                waste = self.model.get_agent_by_id(waste_id)
                if waste and self.max_weight >= waste.weight:
                    self.pick_waste(waste)
                    self.knowledge["actions"].append(f"picked waste {waste_id}")
                    break  # Only pick one waste at a time

    def pick_waste(self, waste):
        if self.max_weight >= waste.weight and self.pos == waste.pos:
            self.max_weight -= waste.weight
            self.knowledge["carrying_waste"] += waste.weight
            self.model.grid.remove_agent(waste)
            print(f"Drone {self.unique_id} picked waste {waste.unique_id}")

    def drop_waste(self):
        self.max_weight = 2
        self.knowledge["carrying_waste"] = 0
        print(f"Drone {self.unique_id} dropped all waste")

    def update(self):
        self.knowledge["percepts"].append(self.percepts)
        self.knowledge["actions"] = []

    def deleberate(self):
        return "move"

    def step_agent(self):
        self.update()
        action = self.deleberate()
        self.percepts = self.model.do(self, action)
