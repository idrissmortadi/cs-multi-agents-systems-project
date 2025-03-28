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

    def __str__(self):
        return f"Waste(id={self.unique_id}, color={self.waste_color})"

    def __repr__(self):
        return self.__str__()


class Zone(Agent):
    def __init__(self, model, zone_type: Literal[0, 1, 2], is_drop_zone: bool = False):
        super().__init__(model)
        self.zone_type = zone_type
        self.is_drop_zone = is_drop_zone

    def step_agent(self):
        pass

    def __repr__(self):
        return f"Zone({self.zone_type}, drop_zone={self.is_drop_zone})"

    def __str__(self):
        return f"Zone({self.zone_type}, drop_zone={self.is_drop_zone})"
