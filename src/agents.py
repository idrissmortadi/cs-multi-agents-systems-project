from mesa import Agent


class Drone(Agent):
    def __init__(self, model):
        super().__init__(model)

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def step_agent(self):
        self.move()
