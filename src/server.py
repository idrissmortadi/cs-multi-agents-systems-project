import mesa
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)

from agents import Drone
from model import Environment
from objects import COLORS_MAP, Waste, Zone

print(f"Mesa version: {mesa.__version__}")


def agent_portrayal(agent: mesa.Agent):
    if isinstance(agent, Waste):
        markers = {
            0: "D",  # Diamond
            1: "o",  # Circle
            2: "s",  # Square
        }

        portrayal = {
            "color": "black",
            "marker": markers.get(agent.waste_color, "D"),
            "zorder": 100,
            "size": 70,
        }
    elif isinstance(agent, Drone):
        portrayal = {
            "color": "purple",
            "zorder": 101,
        }
    elif isinstance(agent, Zone):
        return {
            "marker": "s",
            "color": COLORS_MAP[agent.zone_type],
            "zorder": 99,
            "size": 1300,
        }
    return portrayal


model_params = {
    "n": {
        "type": "SliderInt",
        "value": 1,
        "label": "Number of agents:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "num_wastes": {
        "type": "SliderInt",
        "value": 1,
        "label": "Number of wastes:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "width": 9,
    "height": 9,
}
money_model = Environment(n=1, num_wastes=2, width=9, height=9)

SpaceGraph = make_space_component(agent_portrayal)
# GiniEthnicityPlot = make_plot_component(["Gini_Mixed", "Gini_Green", "Gini_Blue"])

page = SolaraViz(
    money_model,
    components=[SpaceGraph],
    model_params=model_params,
    name="Simple",
)
