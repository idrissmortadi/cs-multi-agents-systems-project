import random

from mesa import Agent


class Drone(Agent):
    def __init__(self, model, zone_type):
        super().__init__(model)
        self.max_weight = 2
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
        }

    def move(self):
        new_position = random.choice(
            (
                self.percepts["neighbors_empty"]
                if len(self.percepts["neighbors_empty"]) > 0
                else [self.pos]
            )
        )

        self.model.grid.move_agent(self, new_position)

        # Check if there is waste in the new position
        # agents_in_position = self.model.grid.get_cell_list_contents([new_position])
        # for agent in agents_in_position:
        #     if isinstance(agent, Waste):
        #         self.pick_waste(agent)
        #     if new_position[0] % (self.model.grid.width // 3) and new_position[0] != 0:
        #         self.drop_waste()
        # if self.model.grid.get_cell_list_contents([new_position]) > 2:
        #    self.pick_waste(self.model.grid.get_cell_list_contents([new_position])[1])

        # if new_position[0] % (self.model.grid.width // 3) and new_position[0] != 0:
        #    self.drop_waste()

        # agents_in_position = self.model.grid.get_cell_list_contents([new_position])
        # for agent in agents_in_position:
        #     if isinstance(agent, Waste):
        #         self.pick_waste(agent)

        # self.model.grid.move_agent(self, new_position)

    def pick_waste(self, waste):
        if self.max_weight >= waste.weight and self.pos == waste.pos:
            self.max_weight -= waste.weight
            self.model.remove_agent(waste)
            print(f"Drone {self.unique_id} picked waste {waste.unique_id}")

    def drop_waste(self):
        self.max_weight = 2

    def update(self):
        self.knowledge["percepts"].append(self.percepts)
        self.knowledge["actions"] = []

    def deleberate(self):
        return "move"

    def step_agent(self):
        self.update()
        action = self.deleberate()
        self.percepts = self.model.do(self, action)
