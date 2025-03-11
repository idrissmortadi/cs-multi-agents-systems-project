from mesa import Agent


class Waste(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.weight = 1


class Drone(Agent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.max_weight = 2
        self.zone_type = self.model._get_zone(pos).zone_type

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )

        filtered_steps = []
        for pos in possible_steps:
            zone_type = self.model._get_zone(pos).zone_type
            if zone_type == self.zone_type:
                filtered_steps.append(pos)

        new_position = self.random.choice(filtered_steps)
        self.model.grid.move_agent(self, new_position)
        # Check if there is waste in the new position
        # if self.model.grid.get_cell_list_contents([new_position]) > 1:
        #     self.pick_waste(self.model.grid.get_cell_list_contents([new_position])[1])

        # if new_position[0] % (self.model.grid.width // 3) and new_position[0] != 0:
        #     self.drop_waste()

    def pick_waste(self, waste):
        if self.max_weight >= waste.weight and self.pos == waste.pos:
            self.max_weight -= waste.weight
            return True
        return False

    def drop_waste(self):
        self.max_weight = 2

    def step_agent(self):
        self.move()
