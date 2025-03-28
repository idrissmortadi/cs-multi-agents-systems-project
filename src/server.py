import mesa
from mesa.visualization import SolaraViz, make_plot_component, make_space_component

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
            1: "D",
            2: "*",
        }

        portrayal = {
            "marker": WASTES_MARKER_MAP.get(agent.waste_color, "o"),
            "color": WASTES_COLOR_MAP.get(agent.waste_color, "black"),
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
            "size": 500,
        }
    elif isinstance(agent, Zone):
        if agent.is_drop_zone:
            portrayal = {
                "marker": "s",
                "color": "black",
                "zorder": 99,
                "size": 1000,
            }
        else:
            return {
                "marker": "s",
                "color": COLORS_MAP[agent.zone_type],
                "zorder": 99,
                "size": 1000,
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
        "value": 10,
        "label": "Grid width:",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid height:",
        "min": 10,
        "max": 100,
        "step": 1,
    },
}
model = Environment(
    green_agents=model_params["green_agents"]["value"],
    yellow_agents=model_params["yellow_agents"]["value"],
    red_agents=model_params["red_agents"]["value"],
    green_wastes=model_params["green_wastes"]["value"],
    yellow_wastes=model_params["yellow_wastes"]["value"],
    red_wastes=model_params["red_wastes"]["value"],
    width=model_params["width"]["value"],
    height=model_params["height"]["value"],
)

SpaceGraph = make_space_component(agent_portrayal)
WastesPlot = make_plot_component(["green_wastes", "yellow_wastes", "red_wastes"])

page = SolaraViz(
    model,
    components=[SpaceGraph, WastesPlot],
    model_params=model_params,
    name="Simple",
)
