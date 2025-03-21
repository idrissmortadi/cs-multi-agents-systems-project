from typing import Literal

from mesa import Agent

COLORS_MAP = {
    0: "#008800",
    1: "#CCCC00",
    2: "#880000",
}


class Waste(Agent):
    def __init__(self, model, waste_color: Literal[0, 1, 2]):
        super().__init__(model)
        self.weight = 1
        self.waste_color = waste_color

    def step_agent(self):
        pass


class Zone(Agent):
    def __init__(self, model, zone_type: Literal[0, 1, 2]):
        super().__init__(model)
        self.zone_type = zone_type

    def step_agent(self):
        pass
