from typing import Literal

from mesa import Agent

COLORS_MAP = {
    "G": "green",
    "Y": "yellow",
    "R": "red",
}


class Waste(Agent):
    def __init__(self, model, waste_color: Literal["G", "Y", "R"]):
        super().__init__(model)
        self.waste_color = waste_color

    def step_agent(self):
        pass


class Zone(Agent):
    def __init__(self, model, zone_type: Literal["G", "Y", "R"]):
        super().__init__(model)
        self.zone_type = zone_type

    def step_agent(self):
        pass
