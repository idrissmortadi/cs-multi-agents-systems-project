import mesa
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)

from agents import Agent
from model import Environment

print(f"Mesa version: {mesa.__version__}")


def agent_portrayal(agent: Agent):
    portrayal = {
        "color": "red",
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
    "width": 10,
    "height": 10,
}
money_model = Environment(n=50, width=10, height=10)

SpaceGraph = make_space_component(agent_portrayal)
# GiniEthnicityPlot = make_plot_component(["Gini_Mixed", "Gini_Green", "Gini_Blue"])

page = SolaraViz(
    money_model,
    components=[SpaceGraph],
    model_params=model_params,
    name="Simple",
)
