import mesa
from mesa.visualization import SolaraViz, make_plot_component, make_space_component

from model import Environment
from objects import COLORS_MAP

print(f"Mesa version: {mesa.__version__}")
# sns.set_theme(style="whitegrid")


# Update agent_portrayal to use class names instead of isinstance and ensure portrayal is always initialized


def agent_portrayal(agent: mesa.Agent):
    portrayal = {}  # Initialize portrayal to avoid UnboundLocalError

    if agent.__class__.__name__ == "Waste":
        WASTES_COLOR_MAP = {
            0: "#00FF00",
            1: "yellow",
            2: "red",
        }
        WASTES_MARKER_MAP = {
            0: "*",
            1: "*",
            2: "*",
        }

        portrayal = {
            "marker": WASTES_MARKER_MAP.get(agent.waste_color, "o"),
            "color": WASTES_COLOR_MAP.get(agent.waste_color, "black"),
            "zorder": 101,
        }
    elif agent.__class__.__name__ == "Drone":
        AGENT_COLOR_MAP = {
            0: "#00FF00",
            1: "#FFFF00",
            2: "#FF0000",
        }
        portrayal = {
            "color": AGENT_COLOR_MAP.get(agent.zone_type, "purple"),
            "marker": "o",
            "zorder": 100,
        }
    elif agent.__class__.__name__ == "Zone":
        if agent.is_drop_zone:
            portrayal = {
                "marker": "s",
                "color": "#990000",
                "zorder": 99,
            }
        else:
            if (
                agent.pos[0] % (agent.model.grid.width // 3)
                == agent.model.grid.width // 3 - 1
                and agent.pos[0] < agent.model.grid.width // 3 * 2
            ):
                portrayal = {
                    "marker": "s",
                    "color": COLORS_MAP[agent.zone_type],
                    "zorder": 99,
                }
            else:
                portrayal = {
                    "marker": "s",
                    "color": "white",
                    "zorder": 99,
                }

    return portrayal


model_params = {
    "green_agents": {
        "type": "SliderInt",
        "value": 2,
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
        "value": 2,
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
    "agent_implementation": {
        "type": "Select",
        "value": "agents",
        "values": ["agents", "agents_random"],
        "label": "Agent Implementation",
    },
}

selected_agent_module = model_params["agent_implementation"]["value"]
if selected_agent_module == "agents_random":
    pass
else:
    pass

model = Environment(
    green_agents=model_params["green_agents"]["value"],
    yellow_agents=model_params["yellow_agents"]["value"],
    red_agents=model_params["red_agents"]["value"],
    green_wastes=model_params["green_wastes"]["value"],
    yellow_wastes=model_params["yellow_wastes"]["value"],
    red_wastes=model_params["red_wastes"]["value"],
    width=model_params["width"]["value"],
    height=model_params["height"]["value"],
    agent_implementation=model_params["agent_implementation"]["value"],
)


SpaceGraph = make_space_component(agent_portrayal)
WastesPlot = make_plot_component(
    measure=["green_wastes", "yellow_wastes", "red_wastes"],
)
wastes_in_drop_zone = make_plot_component(["wastes_in_drop_zone"])

# Add new plots for metrics
# ProcessingTimePlot = make_plot_component(["avg_processing_time"])
# InventoryUtilizationPlot = make_plot_component(["inventory_utilization"])
# ThroughputPlot = make_plot_component(["avg_throughput"])
# ZoneClearancePlot = make_plot_component(
#     ["zone_0_clearance_rate", "zone_1_clearance_rate", "zone_2_clearance_rate"]
# )
# agents_behaviour = make_plot_component(["avg_distance_per_agent"])

# Update the SolaraViz to include the new plots
page = SolaraViz(
    model,
    components=[
        SpaceGraph,
        WastesPlot,
        wastes_in_drop_zone,
        # ProcessingTimePlot,
        # InventoryUtilizationPlot,
        # ThroughputPlot,
        # agents_behaviour,
        # ZoneClearancePlot,
    ],
    model_params=model_params,
    name="Simple",
)
