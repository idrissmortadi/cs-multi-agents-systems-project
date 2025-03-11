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
            agents_in_position = self.model.grid.get_cell_list_contents([pos])
            occupied = False
            for a in agents_in_position:
                if isinstance(a, Drone):
                    occupied = True
                    break

            if zone_type == self.zone_type and not occupied:
                filtered_steps.append(pos)

        new_position = (
            self.random.choice(filtered_steps) if len(filtered_steps) > 0 else self.pos
        )
        # Check if there is waste in the new position
        agents_in_position = self.model.grid.get_cell_list_contents([new_position])
        for agent in agents_in_position:
            if isinstance(agent, Waste):
                self.pick_waste(agent)
            if new_position[0] % (self.model.grid.width // 3) and new_position[0] != 0:
                self.drop_waste()
        # if self.model.grid.get_cell_list_contents([new_position]) > 2:
        #    self.pick_waste(self.model.grid.get_cell_list_contents([new_position])[1])

        # if new_position[0] % (self.model.grid.width // 3) and new_position[0] != 0:
        #    self.drop_waste()

        agents_in_position = self.model.grid.get_cell_list_contents([new_position])
        for agent in agents_in_position:
            if isinstance(agent, Waste):
                self.pick_waste(agent)

        self.model.grid.move_agent(self, new_position)

    def pick_waste(self, waste):
        if self.max_weight >= waste.weight and self.pos == waste.pos:
            self.max_weight -= waste.weight
            self.model.remove_agent(waste)
            print(f"Drone {self.unique_id} picked waste {waste.unique_id}")

    def drop_waste(self):
        self.max_weight = 2

    def step_agent(self):
        self.move()
