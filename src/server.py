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
        WASTES_COLOR_MAP = {
            0: "#55AF55",
            1: "yellow",
            2: "red",
        }
        WASTES_MARKER_MAP = {
            0: "o",
            1: "s",
            2: "D",
        }

        portrayal = {
            "marker": WASTES_MARKER_MAP.get(agent.waste_color, "circle"),
            "color": WASTES_COLOR_MAP.get(agent.waste_color, "D"),
            "zorder": 101,
            "size": 70,
        }
    elif isinstance(agent, Drone):
        AGENT_COLOR_MAP = {
            0: "#00FF00",
            1: "yellow",
            2: "red",
        }
        portrayal = {
            "color": AGENT_COLOR_MAP.get(agent.zone_type, "purple"),
            "zorder": 100,
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
    "green_agents": {
        "type": "SliderInt",
        "value": 1,
        "label": "Number of green agents",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "yellow_agents": {
        "type": "SliderInt",
        "value": 0,
        "label": "Number of yellow agents",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "red_agents": {
        "type": "SliderInt",
        "value": 0,
        "label": "Number of red agents",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "green_wastes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of green wastes",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "yellow_wastes": {
        "type": "SliderInt",
        "value": 3,
        "label": "Number of yellow wastes",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "red_wastes": {
        "type": "SliderInt",
        "value": 2,
        "label": "Number of red wastes",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "width": {
        "type": "SliderInt",
        "value": 9,
        "label": "Grid width:",
        "min": 9,
        "max": 100,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 9,
        "label": "Grid height:",
        "min": 9,
        "max": 100,
        "step": 1,
    },
}
money_model = Environment(
    green_agents=1,
    yellow_agents=1,
    red_agents=1,
    green_wastes=5,
    yellow_wastes=3,
    red_wastes=2,
    width=9,
    height=9,
)

SpaceGraph = make_space_component(agent_portrayal)
# GiniEthnicityPlot = make_plot_component(["Gini_Mixed", "Gini_Green", "Gini_Blue"])

page = SolaraViz(
    money_model,
    components=[SpaceGraph],
    model_params=model_params,
    name="Simple",
)
